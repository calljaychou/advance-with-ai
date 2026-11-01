/**
 * The dsh-skill-hub service: repository configuration, scanning, installing,
 * updating, and runtime skill registration.
 *
 * @module dsh-skill-hub/service
 */
import { existsSync, readdirSync, rmSync } from 'node:fs';
import { join } from 'node:path';

import { ConfigStore, StateStore, dataPath, ensureDataDirs, normalizeRepoSlug } from './store.js';
import { GitHubError, materializeSnapshot, resolveRepo, resolveSha } from './github.js';
import { discoverSkills, installSkillDir, readInstalledSkill, registerInstalledSkills, skillKey } from './skills.js';

/** How many installations are recorded per repository before pruning is offered. */
const MAX_INSTALL_LOG = 200;

/**
 * Owns all skill-hub state for one host plugin instance.
 */
export class SkillHubService {
  /**
   * @param registry - the `ctx.skills` registry used for runtime registration.
   * @param logger - a cordis logger.
   */
  constructor(registry, logger) {
    this.registry = registry;
    this.logger = logger;
    this.config = new ConfigStore();
    this.state = new StateStore();
    /** Disposers for currently registered runtime skills. */
    this.disposers = [];
    /** Failures recorded by the last registration pass. */
    this.registrationFailures = [];
    /** Last action result, surfaced in the UI. */
    this.lastResult = undefined;
    ensureDataDirs();
    this.refreshRegistrations();
  }

  /**
   * Re-register every installed skill, replacing the previous generation.
   * @returns the number of skills registered and any failures.
   */
  refreshRegistrations() {
    for (const dispose of this.disposers) {
      try {
        dispose();
      } catch (error) {
        this.logger?.warn?.(`skill-hub: 释放旧技能注册失败：${error?.message ?? String(error)}`);
      }
    }
    this.disposers = [];
    const records = Object.values(this.state.read().installed);
    const { disposers, failures } = registerInstalledSkills(this.registry, records, this.logger);
    this.disposers = disposers;
    this.registrationFailures = failures;
    return { registered: disposers.length, failures };
  }

  /**
   * Ask the live skill registry which skills it currently exposes.
   *
   * This is the authoritative answer to "did registration work?", as opposed to
   * counting our own disposers.
   *
   * @returns skill summaries, or an empty list when the registry is unreadable.
   */
  async catalog() {
    try {
      const summaries = await this.registry.list({ cwd: process.cwd() });
      if (!Array.isArray(summaries)) return [];
      return summaries.map((summary) => ({
        name: summary.name,
        description: summary.description,
        provider: summary.provider,
        source: summary.source,
        ...(summary.whenToUse === undefined ? {} : { whenToUse: summary.whenToUse }),
      }));
    } catch (error) {
      this.logger?.warn?.(`skill-hub: 读取技能清单失败：${error?.message ?? String(error)}`);
      return [];
    }
  }

  /**
   * The snapshot enriched with the live registry catalog.
   * @returns the view payload served to the settings UI.
   */
  async view() {
    const state = this.snapshot();
    state.catalog = await this.catalog();
    return state;
  }

  /** Release every registration owned by this plugin instance. */
  dispose() {
    for (const dispose of this.disposers) {
      try {
        dispose();
      } catch {
        // Disposal is best effort: the host is shutting down either way.
      }
    }
    this.disposers = [];
  }

  /**
   * Build the payload the settings UI renders.
   * @returns configuration, scan results, install status, and registration state.
   */
  snapshot() {
    const config = this.config.read();
    const state = this.state.read();
    const repos = config.repos.map((row) => {
      const scan = state.repos[row.id];
      const skills = Array.isArray(scan?.skills) ? scan.skills : [];
      const installedForRepo = Object.values(state.installed).filter((record) => record.repoId === row.id);
      const installedNames = new Set(installedForRepo.map((record) => record.name));
      const scannedNames = new Set(skills.map((skill) => skill.name));
      const detailed = skills.map((skill) => {
        const record = state.installed[skillKey(row.id, skill.name)];
        const status = record === undefined ? 'new' : record.sha === scan?.sha ? 'current' : 'stale';
        return { ...skill, status, installedSha: record?.sha, installedAt: record?.installedAt };
      });
      const removed = installedForRepo
        .filter((record) => !scannedNames.has(record.name))
        .map((record) => ({ name: record.name, status: 'removed', description: record.description, installedAt: record.installedAt }));
      return {
        id: row.id,
        repo: row.repo,
        ref: row.ref,
        label: row.label,
        enabled: row.enabled,
        sha: scan?.sha,
        resolvedRef: scan?.resolvedRef,
        scannedAt: scan?.scannedAt,
        skills: [...detailed, ...removed],
        skipped: Array.isArray(scan?.skipped) ? scan.skipped : [],
        counts: {
          new: detailed.filter((skill) => skill.status === 'new').length,
          stale: detailed.filter((skill) => skill.status === 'stale').length,
          current: detailed.filter((skill) => skill.status === 'current').length,
          installed: installedForRepo.length,
        },
      };
    });

    return {
      dataDir: dataPath(),
      skillsDir: dataPath('skills'),
      repos,
      installed: Object.values(state.installed).map((record) => ({
        key: skillKey(record.repoId, record.name),
        name: record.name,
        repo: record.repo,
        repoId: record.repoId,
        sha: record.sha,
        installedAt: record.installedAt,
        path: record.path,
      })),
      registered: this.disposers.length,
      registrationFailures: this.registrationFailures,
      lastResult: this.lastResult,
    };
  }

  /**
   * Add a repository row and immediately scan it.
   * @param input - `owner/repo` slug or GitHub URL.
   * @param options - optional ref and label.
   * @returns the scan outcome for the new row.
   */
  async addRepo(input, options = {}) {
    const slug = normalizeRepoSlug(input);
    if (slug === undefined) {
      throw new GitHubError('bad-repo', '仓库格式应为 owner/repo 或 GitHub 链接');
    }
    const row = this.config.addRepo(slug, options);
    this.lastResult = { ok: true, message: `已添加 ${row.repo}` };
    return this.scanRepo(row.id);
  }

  /**
   * Remove a repository row. Installed skills are kept unless `uninstall`.
   * @param id - the row identifier.
   * @param uninstall - also delete that repository's installed skills.
   * @returns a summary of what was removed.
   */
  removeRepo(id, uninstall = false) {
    const row = this.config.read().repos.find((candidate) => candidate.id === id);
    if (row === undefined) throw new GitHubError('not-found', `未配置仓库 ${id}`);
    let removedSkills = 0;
    if (uninstall) {
      const state = this.state.read();
      const records = Object.entries(state.installed).filter(([, record]) => record.repoId === id);
      for (const [, record] of records) {
        rmSync(record.path, { recursive: true, force: true });
        removedSkills += 1;
      }
      this.state.clearInstalled(records.map(([key]) => key));
    }
    this.config.removeRepo(id);
    rmSync(dataPath('skills', id), { recursive: true, force: true });
    this.refreshRegistrations();
    this.lastResult = { ok: true, message: `已移除 ${row.repo}${uninstall ? `，并删除 ${removedSkills} 个技能` : ''}` };
    return { removedSkills };
  }

  /**
   * Resolve a repository's HEAD commit, download it, and list its skills.
   * @param id - the row identifier.
   * @returns the stored scan result.
   */
  async scanRepo(id) {
    const row = this.config.read().repos.find((candidate) => candidate.id === id);
    if (row === undefined) throw new GitHubError('not-found', `未配置仓库 ${id}`);

    const repo = await resolveRepo(row.repo);
    const { sha, ref } = await resolveSha(row.repo, row.ref, repo.defaultBranch);
    const root = await materializeSnapshot(row.repo, sha);
    const { skills, skipped } = discoverSkills(root);

    const entry = {
      sha,
      resolvedRef: ref,
      defaultBranch: repo.defaultBranch,
      description: repo.description,
      stars: repo.stars,
      pushedAt: repo.pushedAt,
      scannedAt: new Date().toISOString(),
      skills: skills.map((skill) => ({
        name: skill.name,
        description: skill.description,
        ...(skill.whenToUse === undefined ? {} : { whenToUse: skill.whenToUse }),
        relDir: skill.relDir,
      })),
      skipped,
    };
    this.state.setRepoScan(id, entry);
    this.lastResult = {
      ok: true,
      message: `${row.repo}@${sha.slice(0, 7)} 扫描完成：发现 ${skills.length} 个技能${skipped.length > 0 ? `，跳过 ${skipped.length} 个` : ''}`,
    };
    return entry;
  }

  /**
   * Scan every enabled repository, collecting per-repository failures.
   * @returns the scan outcomes.
   */
  async scanAll() {
    const rows = this.config.read().repos.filter((row) => row.enabled);
    const results = [];
    for (const row of rows) {
      try {
        const entry = await this.scanRepo(row.id);
        results.push({ id: row.id, repo: row.repo, ok: true, sha: entry.sha, skills: entry.skills.length });
      } catch (error) {
        results.push({ id: row.id, repo: row.repo, ok: false, message: error?.message ?? String(error) });
        this.logger?.warn?.(`skill-hub: 扫描 ${row.repo} 失败：${error?.message ?? String(error)}`);
      }
    }
    const failed = results.filter((result) => !result.ok);
    this.lastResult = {
      ok: failed.length === 0,
      message:
        failed.length === 0
          ? `全部扫描完成：${results.length} 个仓库，共 ${results.reduce((sum, item) => sum + (item.skills ?? 0), 0)} 个技能`
          : `扫描完成，${failed.length} 个仓库失败：${failed.map((item) => `${item.repo}（${item.message}）`).join('；')}`,
    };
    return results;
  }

  /**
   * Install or update skills from a repository's most recent scan.
   * @param id - the row identifier.
   * @param selected - skill names to act on; all scanned skills when omitted.
   * @param options - `rescan` forces a fresh scan before installing.
   * @returns per-skill installation outcomes.
   */
  async installRepo(id, selected, options = {}) {
    const row = this.config.read().repos.find((candidate) => candidate.id === id);
    if (row === undefined) throw new GitHubError('not-found', `未配置仓库 ${id}`);

    let scan = this.state.read().repos[id];
    if (options.rescan === true || scan === undefined || typeof scan.sha !== 'string') {
      scan = await this.scanRepo(id);
    }

    const wanted = Array.isArray(selected) && selected.length > 0 ? new Set(selected) : undefined;
    const targets = scan.skills.filter((skill) => wanted === undefined || wanted.has(skill.name));
    if (targets.length === 0) {
      this.lastResult = { ok: true, message: `${row.repo} 没有需要安装的技能` };
      return [];
    }

    const root = await materializeSnapshot(row.repo, scan.sha);
    const discovered = discoverSkills(root).skills;
    const byName = new Map(discovered.map((skill) => [skill.name, skill]));
    const outcomes = [];
    const records = {};

    for (const target of targets) {
      const skill = byName.get(target.name);
      if (skill === undefined) {
        outcomes.push({ name: target.name, action: 'skipped', message: '该 commit 中已找不到此技能' });
        continue;
      }
      const destDir = dataPath('skills', id, skill.name);
      const previous = this.state.read().installed[skillKey(id, skill.name)];
      const action = previous === undefined ? 'installed' : previous.sha === scan.sha ? 'unchanged' : 'updated';
      try {
        installSkillDir(skill.absDir, destDir);
        records[skillKey(id, skill.name)] = {
          repoId: id,
          repo: row.repo,
          name: skill.name,
          description: skill.description,
          sha: scan.sha,
          resolvedRef: scan.resolvedRef,
          installedAt: new Date().toISOString(),
          path: destDir,
          relDir: skill.relDir,
        };
        outcomes.push({ name: skill.name, action });
      } catch (error) {
        outcomes.push({ name: skill.name, action: 'failed', message: error?.message ?? String(error) });
      }
    }

    if (Object.keys(records).length > 0) {
      this.state.setInstalled(records);
      const { registered, failures } = this.refreshRegistrations();
      const installedCount = outcomes.filter((outcome) => outcome.action === 'installed').length;
      const updatedCount = outcomes.filter((outcome) => outcome.action === 'updated').length;
      const failedCount = outcomes.filter((outcome) => outcome.action === 'failed').length;
      this.lastResult = {
        ok: failedCount === 0 && failures.length === 0,
        message:
          `${row.repo}：新装 ${installedCount}、更新 ${updatedCount}` +
          `${outcomes.filter((outcome) => outcome.action === 'unchanged').length > 0 ? `、已最新 ${outcomes.filter((outcome) => outcome.action === 'unchanged').length}` : ''}` +
          `${failedCount > 0 ? `、失败 ${failedCount}` : ''}；当前运行时注册 ${registered} 个技能` +
          `${failures.length > 0 ? `（${failures.length} 个未注册）` : ''}`,
      };
    }

    this.pruneInstallLog();
    return outcomes;
  }

  /**
   * Install or update exactly one skill from a repository's latest scan.
   *
   * This is the per-skill counterpart of {@link installRepo}: the settings panel
   * renders one 安装 / 更新 / 重装 button per scanned skill row and calls this
   * method, so a single skill can be handled without touching its siblings.
   *
   * The action installs the commit pinned by the repository's current scan,
   * exactly like the bulk action does; run `scanRepo` first to move that pin.
   *
   * @param id - the repository row identifier.
   * @param name - the skill name as reported by the scan.
   * @param options - `rescan` forces a fresh scan before installing.
   * @returns the single installation outcome.
   */
  async installSkill(id, name, options = {}) {
    const skillName = String(name ?? '').trim();
    if (skillName === '') throw new GitHubError('bad-skill', '缺少技能名');
    const row = this.config.read().repos.find((candidate) => candidate.id === id);
    if (row === undefined) throw new GitHubError('not-found', `未配置仓库 ${id}`);

    let scan = this.state.read().repos[id];
    if (options.rescan === true || scan === undefined || typeof scan.sha !== 'string' || !Array.isArray(scan.skills)) {
      scan = await this.scanRepo(id);
    }
    if (!scan.skills.some((skill) => skill.name === skillName)) {
      throw new GitHubError('not-found', `${row.repo} 的最新扫描中不存在技能 ${skillName}，请先重新扫描`);
    }

    const [outcome] = await this.installRepo(id, [skillName]);
    const result = outcome ?? { name: skillName, action: 'skipped', message: '没有需要处理的技能' };
    const labels = { installed: '已安装', updated: '已更新', unchanged: '已是最新', skipped: '已跳过', failed: '处理失败' };
    const label = labels[result.action] ?? String(result.action);
    const short = typeof scan.sha === 'string' ? scan.sha.slice(0, 7) : '';
    this.lastResult = {
      ok: result.action !== 'failed' && result.action !== 'skipped',
      message: `${skillName} ${label}${short === '' ? '' : `（${row.repo}@${short}）`}${result.message === undefined ? '' : `：${result.message}`}`,
    };
    return result;
  }

  /**
   * Scan and install every enabled repository in one action.
   * @returns per-repository outcomes.
   */
  async installAll() {
    const rows = this.config.read().repos.filter((row) => row.enabled);
    const summary = [];
    for (const row of rows) {
      try {
        const outcomes = await this.installRepo(row.id, undefined, { rescan: true });
        summary.push({ id: row.id, repo: row.repo, ok: true, outcomes });
      } catch (error) {
        summary.push({ id: row.id, repo: row.repo, ok: false, message: error?.message ?? String(error) });
      }
    }
    const failed = summary.filter((item) => !item.ok);
    const installed = summary.reduce(
      (sum, item) => sum + (item.outcomes ?? []).filter((outcome) => outcome.action === 'installed').length,
      0,
    );
    const updated = summary.reduce(
      (sum, item) => sum + (item.outcomes ?? []).filter((outcome) => outcome.action === 'updated').length,
      0,
    );
    this.lastResult = {
      ok: failed.length === 0,
      message:
        `一键安装/更新完成：新装 ${installed}、更新 ${updated}，当前注册 ${this.disposers.length} 个技能` +
        `${failed.length > 0 ? `；${failed.length} 个仓库失败` : ''}`,
    };
    return summary;
  }

  /**
   * Delete one installed skill and drop its registration.
   * @param id - the repository row identifier.
   * @param name - the skill name.
   * @returns a summary of the removal.
   */
  uninstallSkill(id, name) {
    const key = skillKey(id, name);
    const state = this.state.read();
    const record = state.installed[key];
    if (record === undefined) throw new GitHubError('not-found', `未安装技能 ${name}`);
    rmSync(record.path, { recursive: true, force: true });
    this.state.clearInstalled([key]);
    this.refreshRegistrations();
    this.lastResult = { ok: true, message: `已卸载 ${name}` };
    return { name };
  }

  /**
   * List the skill directories currently installed for a repository.
   * @param id - the repository row identifier.
   * @returns the installed directories that still exist on disk.
   */
  listInstalledDirs(id) {
    const dir = dataPath('skills', id);
    if (!existsSync(dir)) return [];
    return readdirSync(dir, { withFileTypes: true })
      .filter((entry) => entry.isDirectory())
      .map((entry) => join(dir, entry.name));
  }

  /** Keep the state document from growing without bound. */
  pruneInstallLog() {
    const state = this.state.read();
    const entries = Object.entries(state.installed);
    if (entries.length <= MAX_INSTALL_LOG) return;
    entries.sort((left, right) => String(left[1].installedAt).localeCompare(String(right[1].installedAt)));
    const drop = entries.slice(0, entries.length - MAX_INSTALL_LOG);
    this.state.clearInstalled(drop.map(([key]) => key));
  }

  /**
   * Re-read installed skills from disk and re-register them.
   * @returns the registration summary.
   */
  reload() {
    const result = this.refreshRegistrations();
    this.lastResult = {
      ok: result.failures.length === 0,
      message: `已重新加载：注册 ${result.registered} 个技能${result.failures.length > 0 ? `，${result.failures.length} 个失败` : ''}`,
    };
    return result;
  }

  /**
   * Report the installed skills that are currently readable from disk.
   * @returns one entry per installed skill with its resolved metadata.
   */
  inspectInstalled() {
    return Object.values(this.state.read().installed).map((record) => {
      const parsed = readInstalledSkill(record.path);
      return {
        name: record.name,
        repo: record.repo,
        path: record.path,
        ok: parsed.ok,
        reason: parsed.ok ? undefined : parsed.reason,
        description: parsed.ok ? parsed.description : record.description,
      };
    });
  }
}

