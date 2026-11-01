/**
 * Client-bundle contract test.
 *
 * Loads `client/client.js` in a simulated `window.__ModuleLoader__` environment
 * with a fake React, then checks:
 *   1. the bundle registers under the expected id,
 *   2. the factory returns a valid cordis client plugin (name / inject / apply),
 *   3. apply() injects the settings section with the right slot options,
 *   4. the panel component actually renders — both the loading branch and a
 *      populated branch — catching undefined access in the render path.
 *
 * Usage: node test/client.mjs
 */
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';

const here = dirname(fileURLToPath(import.meta.url));
const bundlePath = join(here, '..', 'client', 'client.js');

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

/**
 * Build a fake React whose hook state is fed from a fixed sequence.
 * @param values - one entry per `useState` call, in call order.
 * @returns the fake React module plus captured effects.
 */
function createFakeReact(values) {
  const effects = [];
  let index = 0;
  return {
    effects,
    module: {
      Fragment: Symbol('Fragment'),
      createElement(type, props, ...children) {
        return { type, props: props ?? {}, children: children.flat(Infinity) };
      },
      useState(initial) {
        const provided = values[index];
        index += 1;
        return [provided === undefined ? initial : provided, () => {}];
      },
      useCallback(fn) {
        return fn;
      },
      useEffect(fn) {
        effects.push(fn);
      },
    },
  };
}

/**
 * Collect every string rendered in an element tree, expanding function components.
 * @param node - an element, string, number, null, or array.
 * @param out - accumulator for rendered text.
 * @param seen - guard against runaway recursion.
 */
function collectText(node, out = [], seen = { depth: 0 }) {
  if (node === null || node === undefined || node === false) return out;
  if (typeof node === 'string' || typeof node === 'number') {
    out.push(String(node));
    return out;
  }
  if (Array.isArray(node)) {
    for (const child of node) collectText(child, out, seen);
    return out;
  }
  if (typeof node !== 'object') return out;
  if (typeof node.type === 'function') {
    if (seen.depth > 50) return out;
    seen.depth += 1;
    collectText(node.type(node.props), out, seen);
    seen.depth -= 1;
    return out;
  }
  for (const child of node.children ?? []) collectText(child, out, seen);
  return out;
}

/**
 * Collect every `button` element in a tree, expanding function components.
 * @param node - an element, string, number, null, or array.
 * @param out - accumulator for `{ label, element }` entries.
 * @returns the buttons in render order.
 */
function collectButtons(node, out = []) {
  if (node === null || node === undefined || typeof node !== 'object') return out;
  if (Array.isArray(node)) {
    for (const child of node) collectButtons(child, out);
    return out;
  }
  if (typeof node.type === 'function') {
    collectButtons(node.type(node.props), out);
    return out;
  }
  if (node.type === 'button') {
    const labels = [];
    for (const child of node.children ?? []) collectText(child, labels);
    out.push({ label: labels.join(''), element: node });
  }
  for (const child of node.children ?? []) collectButtons(child, out);
  return out;
}

/**
 * Load the bundle and return its registration plus the plugin factory result.
 * @param values - hook state sequence for the panel render.
 * @param fetchImpl - optional fetch replacement used to capture panel requests.
 * @returns the registration and plugin exports.
 */
function loadBundle(values, fetchImpl) {
  const registrations = [];
  const fake = createFakeReact(values);
  const sandbox = {
    console,
    window: { __ModuleLoader__: { load: (registration) => registrations.push(registration) } },
    fetch:
      fetchImpl ??
      (async () => {
        throw new Error('network disabled in test');
      }),
  };
  sandbox.globalThis = sandbox;
  vm.createContext(sandbox);
  vm.runInContext(readFileSync(bundlePath, 'utf8'), sandbox, { filename: bundlePath });
  const registration = registrations[0];
  const require = (id) => {
    if (id === 'react') return fake.module;
    throw new Error(`unexpected require("${id}")`);
  };
  return { registration, plugin: registration?.factory(require), fake };
}

console.log('\n=== 1. bundle 注册 ===');
const { registration, plugin } = loadBundle([]);
check('调用 __ModuleLoader__.load 一次', registration !== undefined);
check('注册 id 为 dsh-skill-hub', registration?.id === 'dsh-skill-hub');
check('factory 为函数', typeof registration?.factory === 'function');

console.log('\n=== 2. 客户端插件契约 ===');
check('导出 name', plugin?.name === 'dsh-skill-hub');
check('inject 包含 slots', Array.isArray(plugin?.inject) && plugin.inject.includes('slots'));
check('导出 apply 函数', typeof plugin?.apply === 'function');

console.log('\n=== 3. 设置页槽位注册 ===');
const slotCalls = [];
const registrationsSeen = [];
const fakeCtx = {
  slots: {
    inject(slotName, callback) {
      slotCalls.push(slotName);
      const result = callback();
      return result;
    },
    register(options, component) {
      registrationsSeen.push({ options, component });
      return () => {};
    },
  },
};
plugin.apply(fakeCtx);
check('注入 settings.section 槽位', slotCalls.length === 1 && slotCalls[0] === 'settings.section');
const entry = registrationsSeen[0];
check('注册了一个组件', registrationsSeen.length === 1 && typeof entry?.component === 'function');
check('槽位选项 name 正确', entry?.options?.name === 'settings.section');
check('槽位选项 id 正确', entry?.options?.id === 'dsh-skill-hub');
check('label 返回中文标题', typeof entry?.options?.label === 'function' && entry.options.label() === '技能仓库');
check('声明了 order', typeof entry?.options?.order === 'number');
check('inject 返回对象', typeof entry?.options?.inject === 'function' && typeof entry.options.inject() === 'object');

console.log('\n=== 4. 加载态渲染 ===');
const loading = loadBundle([]);
let loadingPanel;
const loadingCtx = {
  slots: {
    inject: (_slot, callback) => callback(),
    register: (_options, component) => {
      loadingPanel = component({});
      return component;
    },
  },
};
loading.plugin.apply(loadingCtx);
let loadingText = [];
let loadingError;
try {
  loadingText = collectText(loadingPanel);
} catch (error) {
  loadingError = error;
}
check('加载态渲染不抛异常', loadingError === undefined);
if (loadingError !== undefined) console.log(`  渲染错误: ${loadingError.message}`);
check('加载态显示提示文案', loadingText.join(' | ').includes('正在加载技能仓库配置'));

console.log('\n=== 5. 有数据渲染 ===');
const populatedState = {
  dataDir: '/Users/mac-z/.dsh/skill-hub',
  skillsDir: '/Users/mac-z/.dsh/skill-hub/skills',
  registered: 1,
  repos: [
    {
      id: 'liustack__modlens',
      repo: 'liustack/modlens',
      ref: '',
      label: '',
      enabled: true,
      sha: 'a1923d016c2b617ccd1d6ef3f9e9368622841e67',
      resolvedRef: 'main',
      scannedAt: '2026-09-18T03:30:00.000Z',
      skills: [
        { name: 'modlens', description: '视觉识别技能', status: 'new' },
        { name: 'modsearch', description: '联网搜索技能', status: 'stale', installedSha: 'deadbeef' },
        { name: 'stable', description: '已最新技能', status: 'current', installedSha: 'a1923d0' },
        { name: 'legacy', description: '已移除的技能', status: 'removed' },
      ],
      skipped: [{ path: 'tools/bad', reason: '技能名不是 kebab-case' }],
      counts: { new: 1, stale: 1, current: 1, installed: 3 },
    },
    {
      id: 'big__repo',
      repo: 'big/repo',
      ref: '',
      label: '',
      enabled: true,
      sha: 'b'.repeat(40),
      resolvedRef: 'main',
      scannedAt: '2026-09-18T03:30:00.000Z',
      skills: Array.from({ length: 12 }, (_, index) => ({
        name: `skill-${index}`,
        description: `批量技能 ${index}`,
        status: 'new',
      })),
      skipped: [],
      counts: { new: 12, stale: 0, current: 0, installed: 0 },
    },
  ],
  installed: [{ key: 'liustack__modlens:modlens', name: 'modlens', repo: 'liustack/modlens', repoId: 'liustack__modlens', sha: 'a1923d0', installedAt: '2026-09-18T03:31:00.000Z', path: '/tmp' }],
  registrationFailures: [{ name: 'dup-skill', reason: '技能名与仓库 X 冲突' }],
  catalog: [
    { name: 'modlens', description: '视觉识别技能', provider: 'runtime', source: 'skill-hub:liustack/modlens' },
    { name: 'builtin-helper', description: '内置技能', provider: 'filesystem', source: 'user-dsh' },
  ],
  lastResult: { ok: true, message: 'liustack/modlens：新装 1、更新 0' },
};
const fetchCalls = [];
const populated = loadBundle([populatedState, '', '', '', ''], async (url, options) => {
  fetchCalls.push({ url, options });
  return { status: 200, json: async () => ({ ok: true, value: { state: populatedState } }) };
});
let panelElement;
const populatedCtx = {
  slots: {
    inject: (_slot, callback) => callback(),
    register: (_options, component) => {
      panelElement = component({});
      return component;
    },
  },
};
populated.plugin.apply(populatedCtx);
let populatedText = [];
let renderError;
try {
  populatedText = collectText(panelElement);
} catch (error) {
  renderError = error;
}
check('有数据渲染不抛异常', renderError === undefined);
if (renderError !== undefined) console.log(`  渲染错误: ${renderError.message}`);
const joined = populatedText.join(' | ');
check('渲染出仓库名', joined.includes('liustack/modlens'));
check('渲染出技能名', joined.includes('modlens') && joined.includes('modsearch'));
check('渲染出状态标签', joined.includes('未安装') && joined.includes('可更新') && joined.includes('仓库中已移除'));
check('渲染出一键按钮', joined.includes('一键安装 / 更新全部') || joined.includes('一键安装 / 更新'));
check('渲染出跳过原因', joined.includes('技能名不是 kebab-case'));
check('渲染出未注册技能区块', joined.includes('未注册的技能') && joined.includes('dup-skill'));
check('渲染出去重后的短 SHA', joined.includes('@a1923d0') || joined.includes('a1923d0'));
check('渲染出数据目录', joined.includes('/Users/mac-z/.dsh/skill-hub'));
check('渲染出注册表统计', joined.includes('Harness 技能注册表') && joined.includes('本插件注册 1 个'));
check('文本节点数量合理', populatedText.length > 20);

console.log('\n=== 6. 每个技能的单独安装 / 更新按钮 ===');
const buttonNodes = collectButtons(panelElement);
const buttonLabels = buttonNodes.map((item) => item.label);
check('未安装技能显示「安装」', buttonLabels.filter((label) => label === '安装').length === 1);
check('可更新技能显示「更新」', buttonLabels.filter((label) => label === '更新').length === 1);
check('已最新技能显示「重装」', buttonLabels.filter((label) => label === '重装').length === 1);
check('每个已安装技能都有「卸载」', buttonLabels.filter((label) => label === '卸载').length === 3);
check('仓库级按钮仍然存在', buttonLabels.includes('一键安装 / 更新') || buttonLabels.includes('一键安装 / 更新全部'));

const installButton = buttonNodes.find((item) => item.label === '安装');
check('找到单技能安装按钮', installButton !== undefined);
if (installButton !== undefined) {
  installButton.element.props.onClick();
  await new Promise((resolve) => setImmediate(resolve));
  const request = fetchCalls[fetchCalls.length - 1];
  const payload = JSON.parse(String(request?.options?.body ?? '{}'));
  check(
    '单技能按钮提交 installSkill 与该技能名',
    payload.action === 'installSkill' && payload.id === 'liustack__modlens' && payload.name === 'modlens',
  );
}

console.log('\n=== 7. 技能列表折叠 ===');
check('长技能列表默认折叠', buttonLabels.includes('展开技能（12）') && !buttonLabels.includes('折叠技能（12）'));
check('短技能列表默认展开', buttonLabels.includes('折叠技能（4）'));
check('折叠后不渲染该仓库的技能行', !joined.includes('skill-11'));
check('折叠后显示摘要行', joined.includes('技能列表已折叠'));
check('提供全部折叠 / 展开按钮', buttonLabels.includes('全部折叠') && buttonLabels.includes('全部展开'));

// 显式覆盖：把长列表强制展开，验证折叠状态可被按钮翻转。
const expanded = loadBundle([populatedState, '', '', '', '', { 'big__repo': false }]);
let expandedPanel;
expanded.plugin.apply({
  slots: {
    inject: (_slot, callback) => callback(),
    register: (_options, component) => {
      expandedPanel = component({});
      return component;
    },
  },
});
const expandedText = collectText(expandedPanel).join(' | ');
const expandedLabels = collectButtons(expandedPanel).map((item) => item.label);
check('显式展开后渲染长列表技能', expandedText.includes('skill-11'));
check('显式展开后按钮切换为折叠', expandedLabels.includes('折叠技能（12）'));
check('显式展开后仍保留短列表展开状态', expandedLabels.includes('折叠技能（4）'));

const failed = checks.filter((item) => !item.ok);
console.log(`\n结果：${checks.length - failed.length}/${checks.length} 通过`);
if (failed.length > 0) for (const item of failed) console.log(`  失败: ${item.label}`);
process.exit(failed.length === 0 ? 0 : 1);
