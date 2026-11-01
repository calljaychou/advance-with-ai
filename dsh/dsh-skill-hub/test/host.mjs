/**
 * Host-plugin load test: mounts the real plugin with a fake cordis context and
 * drives the real HTTP handler end-to-end (config → scan → install → register),
 * so everything except browser rendering is verified without a live harness.
 *
 * Usage: node test/host.mjs [owner/repo]
 */
import { existsSync } from 'node:fs';

import { useTempHome } from './helpers.mjs';
import { API_PATH } from '../lib/api.js';
import { apply, inject, name } from '../lib/index.js';

// Isolate this suite: configuration and state live in a throwaway home.
useTempHome();

const slug = process.argv[2] ?? 'liustack/modlens';

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

const registered = new Map();
const routes = [];
const disposers = [];

/** A fake cordis context exposing exactly what the plugin injects. */
const ctx = {
  logger: () => ({ info: () => {}, warn: (message) => console.log(`  [warn] ${message}`) }),
  skills: {
    register(skill) {
      registered.set(skill.name, skill);
      return () => registered.delete(skill.name);
    },
    async list() {
      return [...registered.values()].map((skill) => ({
        name: skill.name,
        description: skill.description,
        provider: 'runtime',
        source: skill.source,
      }));
    },
  },
  webServer: {
    register(route) {
      routes.push(route);
    },
  },
  effect(callback) {
    const disposer = callback();
    if (typeof disposer === 'function') disposers.push(disposer);
    return disposer;
  },
};

/**
 * Build a fake request.
 * @param options - method, headers, and optional JSON body.
 * @returns a minimal request object.
 */
function makeRequest({ method = 'GET', headers = { host: '127.0.0.1:3080' }, body } = {}) {
  const chunks = body === undefined ? [] : [Buffer.from(typeof body === 'string' ? body : JSON.stringify(body))];
  return {
    method,
    headers,
    async *[Symbol.asyncIterator]() {
      for (const chunk of chunks) yield chunk;
    },
  };
}

/**
 * Build a fake response capturing status and body.
 * @returns the response plus a captured-state reader.
 */
function makeResponse() {
  const captured = { status: 0, body: '' };
  return {
    captured,
    writeHead(status) {
      captured.status = status;
    },
    end(chunk) {
      captured.body = chunk === undefined ? '' : String(chunk);
    },
  };
}

console.log('\n=== 1. 插件装载 ===');
check('name 为 skill-hub', name === 'skill-hub');
check('inject 声明 skills 与 webServer', Array.isArray(inject) && inject.includes('skills') && inject.includes('webServer'));
apply(ctx);
check('注册了一个 HTTP 路由', routes.length === 1);
check('路由路径与类型正确', routes[0]?.path === API_PATH && routes[0]?.kind === 'exact');
check('路由带 handler', typeof routes[0]?.handler === 'function');
check('装载时未注册任何技能（未安装）', registered.size === 0);

const route = routes[0];
/**
 * Send one request through the real handler.
 * @param request - the fake request.
 * @returns status and parsed body.
 */
async function invoke(request) {
  const response = makeResponse();
  await route.handler(request, response);
  let parsed;
  try {
    parsed = JSON.parse(response.captured.body);
  } catch {
    parsed = undefined;
  }
  return { status: response.captured.status, parsed };
}

console.log('\n=== 2. 状态查询 ===');
const initial = await invoke(makeRequest());
check('GET 返回 200', initial.status === 200 && initial.parsed?.ok === true);
check('初始没有配置仓库', (initial.parsed?.value?.state?.repos?.length ?? -1) === 0);

console.log('\n=== 3. 添加仓库并扫描（走真实 HTTP 路径）===');
const added = await invoke(makeRequest({ method: 'POST', body: { action: 'addRepo', repo: slug } }));
check('addRepo 返回 200', added.status === 200 && added.parsed?.ok === true);
const repoRow = added.parsed?.value?.state?.repos?.[0];
check('状态里出现仓库行', repoRow !== undefined && repoRow.repo.toLowerCase() === slug.toLowerCase());
check('扫描到技能', (repoRow?.skills?.length ?? 0) > 0);
console.log(`  ${repoRow?.repo} @${String(repoRow?.sha).slice(0, 7)} 技能: ${(repoRow?.skills ?? []).map((skill) => `${skill.name}(${skill.status})`).join(', ')}`);

console.log('\n=== 4. 一键安装 ===');
const installed = await invoke(makeRequest({ method: 'POST', body: { action: 'install', id: repoRow.id } }));
check('install 返回 200', installed.status === 200 && installed.parsed?.ok === true);
check('运行时已注册技能', registered.size > 0);
check('状态标记为 current', (installed.parsed?.value?.state?.repos?.[0]?.skills ?? []).every((skill) => skill.status === 'current'));
const installedRow = installed.parsed?.value?.state?.installed?.[0];
check('state 记录安装路径', typeof installedRow?.path === 'string' && existsSync(installedRow.path));
const catalog = installed.parsed?.value?.state?.catalog ?? [];
check('技能注册表列出了该技能（provider=runtime）', catalog.some((skill) => skill.name === 'modlens' && skill.provider === 'runtime'));
check('技能注册表带来源标记', catalog.some((skill) => String(skill.source ?? '').startsWith('skill-hub:')));
console.log(`  ${installed.parsed?.value?.state?.lastResult?.message ?? ''}`);
for (const [skillName, skill] of registered) {
  console.log(`  注册: ${skillName} ← ${skill.source}（正文 ${skill.content.length} 字符）`);
}

console.log('\n=== 5. 单技能安装 / 更新（真实 HTTP 路径）===');
const targetName = (repoRow.skills ?? [])[0]?.name;
check('扫描结果含可操作技能', typeof targetName === 'string' && targetName !== '');
const dropped = await invoke(makeRequest({ method: 'POST', body: { action: 'uninstall', id: repoRow.id, name: targetName } }));
check('卸载目标技能成功', dropped.status === 200 && !registered.has(targetName));
const reinstalled = await invoke(makeRequest({ method: 'POST', body: { action: 'installSkill', id: repoRow.id, name: targetName } }));
check('installSkill 返回 200', reinstalled.status === 200 && reinstalled.parsed?.ok === true);
check('单技能重新注册成功', registered.has(targetName));
check(
  'lastResult 指明技能名',
  String(reinstalled.parsed?.value?.state?.lastResult?.message ?? '').includes(targetName),
);
console.log(`  ${reinstalled.parsed?.value?.state?.lastResult?.message ?? ''}`);

console.log('\n=== 6. 围栏与会话清理 ===');
const blocked = await invoke(makeRequest({ method: 'POST', headers: { host: 'evil.example.com' }, body: { action: 'addRepo', repo: slug } }));
check('外部 host 被拒绝', blocked.status === 403);
const removed = await invoke(makeRequest({ method: 'POST', body: { action: 'removeRepo', id: repoRow.id, uninstall: true } }));
check('移除仓库成功', removed.status === 200 && removed.parsed?.ok === true);
check('移除后技能已注销', registered.size === 0);
for (const dispose of disposers) dispose();
check('effect 注册了释放函数', disposers.length === 1);

const failed = checks.filter((item) => !item.ok);
console.log(`\n结果：${checks.length - failed.length}/${checks.length} 通过`);
if (failed.length > 0) for (const item of failed) console.log(`  失败: ${item.label}`);
process.exit(failed.length === 0 ? 0 : 1);
