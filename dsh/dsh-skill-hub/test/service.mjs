/**
 * End-to-end test of the skill-hub service using a fake skill registry, so the
 * scan → install → register → update-detection path runs without a live harness.
 *
 * Usage: node test/service.mjs [owner/repo]
 */
import { existsSync, readFileSync } from 'node:fs';

import { useTempHome } from './helpers.mjs';
import { SkillHubService } from '../lib/service.js';
import { skillKey } from '../lib/skills.js';
import { dataPath } from '../lib/store.js';

// Isolate this suite: configuration and state live in a throwaway home.
useTempHome();

const slug = process.argv[2] ?? 'liustack/modlens';
const logger = { info: () => {}, warn: (message) => console.log(`  [warn] ${message}`) };

/** Fake `ctx.skills` capturing registrations. */
function createRegistry() {
  const registered = new Map();
  return {
    registered,
    register(skill) {
      if (registered.has(skill.name)) throw new Error(`duplicate runtime skill "${skill.name}"`);
      registered.set(skill.name, skill);
      return () => registered.delete(skill.name);
    },
  };
}

const checks = [];
/**
 * Record one assertion.
 * @param label - what is being checked.
 * @param condition - the assertion result.
 */
function check(label, condition) {
  checks.push({ label, ok: Boolean(condition) });
  console.log(`  ${condition ? 'PASS' : 'FAIL'}  ${label}`);
}

const registry = createRegistry();
const service = new SkillHubService(registry, logger);
const id = slug.replace('/', '__').toLowerCase();

console.log(`\n=== 1. 添加并扫描 ${slug} ===`);
const scan = await service.addRepo(slug);
check('扫描返回 commit SHA', typeof scan.sha === 'string' && scan.sha.length === 40);
check('发现至少一个技能', scan.skills.length > 0);
console.log(`  sha=${scan.sha.slice(0, 7)} 技能=${scan.skills.map((skill) => skill.name).join(', ') || '(无)'}`);

console.log('\n=== 2. 安装前状态 ===');
let snapshot = service.snapshot();
let row = snapshot.repos.find((repo) => repo.id === id);
check('配置里有该仓库', row !== undefined);
check('技能状态为 new', row.skills.every((skill) => skill.status === 'new'));
check('尚未注册任何技能', registry.registered.size === 0);

console.log('\n=== 3. 一键安装 ===');
const outcomes = await service.installRepo(id);
check('安装动作成功', outcomes.every((outcome) => outcome.action === 'installed' || outcome.action === 'unchanged'));
check('运行时有注册技能', registry.registered.size > 0);
for (const [name, skill] of registry.registered) {
  check(`技能 ${name} 有正文内容`, typeof skill.content === 'string' && skill.content.length > 50);
  check(`技能 ${name} 有描述`, typeof skill.description === 'string' && skill.description.length > 0);
  check(`技能 ${name} resourceBase 指向存在的目录`, existsSync(skill.resourceBase?.path ?? ''));
  check(`技能 ${name} source 标注来源`, typeof skill.source === 'string' && skill.source.startsWith('skill-hub:'));
}

console.log('\n=== 4. 落盘校验 ===');
const installedRecord = Object.values(service.state.read().installed).find((record) => record.repoId === id);
check('state 记录了安装', installedRecord !== undefined);
check('SKILL.md 已写入数据目录', installedRecord !== undefined && existsSync(`${installedRecord.path}/SKILL.md`));
if (installedRecord !== undefined) {
  const body = readFileSync(`${installedRecord.path}/SKILL.md`, 'utf8');
  check('落盘内容与仓库一致', body.length > 50);
  check('安装目录位于 skill-hub/skills 下', installedRecord.path.startsWith(dataPath('skills')));
}

console.log('\n=== 5. 重复安装应为 unchanged ===');
const again = await service.installRepo(id);
check('重复安装判定为 unchanged', again.every((outcome) => outcome.action === 'unchanged'));
check('重复安装未重复注册', registry.registered.size === outcomes.filter((outcome) => outcome.action === 'installed').length);

console.log('\n=== 6. 状态快照 ===');
snapshot = service.snapshot();
row = snapshot.repos.find((repo) => repo.id === id);
check('技能状态变为 current', row.skills.every((skill) => skill.status === 'current' || skill.status === 'removed'));
check('lastResult 报告成功', snapshot.lastResult?.ok === true);
console.log(`  ${snapshot.lastResult?.message ?? '(无)'}`);

console.log('\n=== 7. 单技能安装 / 更新 ===');
const target = scan.skills[0].name;
service.uninstallSkill(id, target);
check('卸载后该技能未注册', !registry.registered.has(target));
const single = await service.installSkill(id, target);
check('单技能安装返回 installed', single.action === 'installed');
check('单技能安装后已注册', registry.registered.has(target));
check(
  '单技能安装未影响同仓库其它技能',
  scan.skills.every((skill) => registry.registered.has(skill.name)) && registry.registered.size === scan.skills.length,
);

// 伪造一个落后的 SHA，用来验证单技能更新判定不依赖真实的新 commit。
const targetKey = skillKey(id, target);
service.state.setInstalled({ [targetKey]: { ...service.state.read().installed[targetKey], sha: '0'.repeat(40) } });
const updated = await service.installSkill(id, target);
check('单技能更新返回 updated', updated.action === 'updated');
const refreshed = service.snapshot().repos.find((repo) => repo.id === id).skills.find((skill) => skill.name === target);
check('更新后该技能状态为 current', refreshed?.status === 'current');
const singleMessage = String(service.snapshot().lastResult?.message ?? '');
check('lastResult 指明技能名与来源', singleMessage.includes(target) && singleMessage.includes(row.repo));
const repeated = await service.installSkill(id, target);
check('已最新时返回 unchanged', repeated.action === 'unchanged');
let unknownRejected = false;
try {
  await service.installSkill(id, 'definitely-not-scanned');
} catch {
  unknownRejected = true;
}
check('未扫描到的技能名被拒绝', unknownRejected);
console.log(`  ${service.snapshot().lastResult?.message ?? '(无)'}`);

console.log('\n=== 8. 卸载与清理 ===');
const victim = [...registry.registered.keys()][0];
if (victim !== undefined) {
  const before = registry.registered.size;
  service.uninstallSkill(id, victim);
  check('卸载后运行时注销', registry.registered.size === before - 1);
  check('卸载后目录被删除', !existsSync(dataPath('skills', id, victim)));
}

const failed = checks.filter((item) => !item.ok);
console.log(`\n结果：${checks.length - failed.length}/${checks.length} 通过`);
if (failed.length > 0) {
  for (const item of failed) console.log(`  失败: ${item.label}`);
}
process.exit(failed.length === 0 ? 0 : 1);
