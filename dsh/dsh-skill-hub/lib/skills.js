/**
 * Skill discovery, installation, and runtime registration for dsh-skill-hub.
 *
 * A "skill" here is a directory containing `SKILL.md` whose YAML frontmatter
 * declares at least a `name` and a `description`, matching the layout the
 * built-in filesystem provider understands. Remote skills are installed into
 * `$DSH_HOME/skill-hub/skills/<repo>/<skill>/` and then registered into the
 * running harness with `ctx.skills.register()`, so they work even where the
 * filesystem skill provider is disabled.
 *
 * @module dsh-skill-hub/skills
 */
import { cpSync, existsSync, readFileSync, readdirSync, rmSync } from 'node:fs';
import { basename, dirname, join, relative } from 'node:path';
import yaml from 'js-yaml';

/** The file that marks a directory as a skill. */
export const SKILL_FILE = 'SKILL.md';

/** Kebab-case constraint the harness applies to skill names. */
const SKILL_NAME = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

/** Directories never searched for skills. */
const SKIP_DIRS = new Set([
  '.git',
  'node_modules',
  'vendor',
  'dist',
  'build',
  'out',
  'target',
  '__pycache__',
  '.venv',
  'venv',
  '.next',
  '.cache',
]);

/** Maximum directory depth searched below a snapshot root. */
const MAX_DEPTH = 6;

/**
 * Split a `SKILL.md` document into YAML frontmatter and body.
 * @param text - the raw file contents.
 * @returns the parsed attributes and the body that follows the frontmatter.
 */
export function parseSkillDocument(text) {
  const normalized = String(text ?? '').replace(/^\uFEFF/, '');
  const match = /^---\r?\n([\s\S]*?)\r?\n---\r?\n?/.exec(normalized);
  if (match === null) return { attributes: {}, body: normalized.trim() };
  let attributes = {};
  try {
    const parsed = yaml.load(match[1]);
    if (parsed !== null && typeof parsed === 'object' && !Array.isArray(parsed)) attributes = parsed;
  } catch {
    attributes = {};
  }
  return { attributes, body: normalized.slice(match[0].length).trim() };
}

/**
 * Coerce frontmatter invocation flags into the harness shape.
 * @param value - the raw `invocation` frontmatter value.
 * @returns a validated invocation object, or `undefined` when unusable.
 */
function normalizeInvocation(value) {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) return undefined;
  const result = {};
  if (typeof value.modelInvocable === 'boolean') result.modelInvocable = value.modelInvocable;
  if (typeof value.userInvocable === 'boolean') result.userInvocable = value.userInvocable;
  return Object.keys(result).length === 0 ? undefined : result;
}

/**
 * Find every skill in a materialized repository snapshot.
 * @param snapshotRoot - the extracted repository root.
 * @returns discovered skills plus the entries skipped and why.
 */
export function discoverSkills(snapshotRoot) {
  const skills = [];
  const skipped = [];
  const seen = new Set();

  const walk = (dir, depth) => {
    if (depth > MAX_DEPTH) return;
    let entries;
    try {
      entries = readdirSync(dir, { withFileTypes: true });
    } catch {
      return;
    }
    const hasSkillFile = entries.some((entry) => entry.isFile() && entry.name === SKILL_FILE);
    if (hasSkillFile) {
      const skillFile = join(dir, SKILL_FILE);
      const record = readSkillFile(skillFile);
      if (record.ok) {
        const relDir = relative(snapshotRoot, dir) || '.';
        if (seen.has(record.name)) {
          skipped.push({ path: relDir, reason: `技能名 "${record.name}" 重复，已跳过` });
        } else {
          seen.add(record.name);
          skills.push({ ...record, relDir, absDir: dir, skillFile });
        }
      } else {
        skipped.push({ path: relative(snapshotRoot, dir) || '.', reason: record.reason });
      }
      return;
    }
    for (const entry of entries) {
      if (!entry.isDirectory()) continue;
      if (entry.name.startsWith('.') || SKIP_DIRS.has(entry.name)) continue;
      walk(join(dir, entry.name), depth + 1);
    }
  };

  walk(snapshotRoot, 0);
  skills.sort((left, right) => left.name.localeCompare(right.name));
  return { skills, skipped };
}

/**
 * Read and validate one `SKILL.md`.
 * @param skillFile - absolute path of the skill document.
 * @returns the parsed record, or a failure with a human-readable reason.
 */
export function readSkillFile(skillFile) {
  let text;
  try {
    text = readFileSync(skillFile, 'utf8');
  } catch (error) {
    return { ok: false, reason: `无法读取 SKILL.md：${error?.message ?? String(error)}` };
  }
  const { attributes, body } = parseSkillDocument(text);
  const fallbackName = basename(dirname(skillFile));
  const rawName = typeof attributes.name === 'string' && attributes.name.trim() !== '' ? attributes.name.trim() : fallbackName;
  const name = rawName.toLowerCase();
  if (!SKILL_NAME.test(name)) {
    return { ok: false, reason: `技能名 "${rawName}" 不是 kebab-case（只允许小写字母、数字、连字符）` };
  }
  const description =
    typeof attributes.description === 'string' && attributes.description.trim() !== ''
      ? attributes.description.trim()
      : '';
  if (description === '') return { ok: false, reason: `技能 "${name}" 缺少 description` };
  const whenToUse = typeof attributes.whenToUse === 'string' && attributes.whenToUse.trim() !== '' ? attributes.whenToUse.trim() : undefined;
  const invocation = normalizeInvocation(attributes.invocation);
  return { ok: true, name, description, whenToUse, invocation, content: body };
}

/**
 * Read an installed skill directory back from disk.
 * @param dir - the installed skill directory.
 * @returns the parsed record, or a failure describing what is wrong.
 */
export function readInstalledSkill(dir) {
  const skillFile = join(dir, SKILL_FILE);
  if (!existsSync(skillFile)) return { ok: false, reason: `缺少 ${SKILL_FILE}` };
  return readSkillFile(skillFile);
}

/**
 * Copy a skill directory into place, replacing any previous copy.
 * @param sourceDir - the skill directory inside a snapshot.
 * @param destDir - the destination directory to (re)create.
 * @returns the destination path.
 */
export function installSkillDir(sourceDir, destDir) {
  rmSync(destDir, { recursive: true, force: true });
  cpSync(sourceDir, destDir, { recursive: true, verbatimSymlinks: true });
  return destDir;
}

/**
 * Stable identifier for one installed skill.
 * @param repoId - the repository row identifier.
 * @param name - the skill name.
 * @returns the key used in the state document.
 */
export function skillKey(repoId, name) {
  return `${repoId}:${name}`;
}

/**
 * Register every installed skill into the running harness.
 * @param registry - the `ctx.skills` registry.
 * @param records - installed-skill records from the state document.
 * @param logger - a diagnostic sink.
 * @returns disposers for the registrations, plus per-skill failures.
 */
export function registerInstalledSkills(registry, records, logger) {
  const disposers = [];
  const failures = [];
  const claimed = new Map();

  for (const record of records) {
    if (!existsSync(record.path)) {
      failures.push({ name: record.name, reason: '安装目录已不存在' });
      continue;
    }
    const parsed = readInstalledSkill(record.path);
    if (!parsed.ok) {
      failures.push({ name: record.name, reason: parsed.reason });
      continue;
    }
    const owner = claimed.get(parsed.name);
    if (owner !== undefined && owner !== record.repoId) {
      failures.push({ name: parsed.name, reason: `技能名与仓库 ${owner} 冲突，保持先注册者生效` });
      continue;
    }
    try {
      const dispose = registry.register({
        name: parsed.name,
        description: parsed.description,
        ...(parsed.whenToUse === undefined ? {} : { whenToUse: parsed.whenToUse }),
        ...(parsed.invocation === undefined ? {} : { invocation: parsed.invocation }),
        content: parsed.content,
        source: `skill-hub:${record.repo}`,
        path: join(record.path, SKILL_FILE),
        resourceBase: { kind: 'directory', path: record.path },
      });
      if (typeof dispose === 'function') disposers.push(dispose);
      claimed.set(parsed.name, record.repoId);
    } catch (error) {
      failures.push({ name: parsed.name, reason: error?.message ?? String(error) });
      logger?.warn?.(`skill-hub: 注册技能 ${parsed.name} 失败：${error?.message ?? String(error)}`);
    }
  }

  return { disposers, failures };
}
