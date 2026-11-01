/**
 * Unit test for the HTTP surface: the loopback/same-origin fence, method
 * handling, and action dispatch — exercised without a live harness.
 *
 * Usage: node test/api.mjs
 */
import { API_PATH, createApiHandler, isTrustedRequest } from '../lib/api.js';

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

/** A service stub recording the actions it receives. */
function createService() {
  const seen = [];
  return {
    seen,
    snapshot: () => ({ dataDir: '/tmp/skill-hub', repos: [], registered: seen.length }),
    view: async () => ({ dataDir: '/tmp/skill-hub', repos: [], registered: seen.length, catalog: [] }),
    addRepo: async (repo) => seen.push(`addRepo:${repo}`),
    scanRepo: async (id) => seen.push(`scan:${id}`),
    installRepo: async (id) => seen.push(`install:${id}`),
    installSkill: async (id, name) => seen.push(`installSkill:${id}:${name}`),
  };
}

/**
 * Build a fake request.
 * @param options - method, headers, and optional JSON body.
 * @returns a minimal request object usable by the handler.
 */
function makeRequest({ method = 'GET', headers = {}, body } = {}) {
  const payload = body === undefined ? [] : [Buffer.from(typeof body === 'string' ? body : JSON.stringify(body))];
  return {
    method,
    headers,
    async *[Symbol.asyncIterator]() {
      for (const chunk of payload) yield chunk;
    },
  };
}

/**
 * Build a fake response capturing the status and body.
 * @returns the response object plus a reader for what was written.
 */
function makeResponse() {
  const captured = { status: 0, headers: {}, body: '' };
  return {
    captured,
    writeHead(status, headers) {
      captured.status = status;
      captured.headers = headers ?? {};
    },
    end(chunk) {
      captured.body = chunk === undefined ? '' : String(chunk);
    },
  };
}

const serviceStub = createService();
const handler = createApiHandler(serviceStub, { warn: () => {} });

/**
 * Invoke the handler once.
 * @param request - the fake request.
 * @returns the captured status and parsed body.
 */
async function invoke(request) {
  const response = makeResponse();
  await handler(request, response);
  let parsed;
  try {
    parsed = JSON.parse(response.captured.body);
  } catch {
    parsed = undefined;
  }
  return { status: response.captured.status, parsed };
}

console.log('\n=== 1. 同源/本机围栏 ===');
check('本机 host 通过', isTrustedRequest({ headers: { host: '127.0.0.1:3080' } }) === true);
check('localhost 通过', isTrustedRequest({ headers: { host: 'localhost:3080' } }) === true);
check('[::1] 通过', isTrustedRequest({ headers: { host: '[::1]:3080' } }) === true);
check('外部 host 拒绝', isTrustedRequest({ headers: { host: 'evil.example.com' } }) === false);
check('缺少 host 拒绝', isTrustedRequest({ headers: {} }) === false);
check('cross-site 拒绝', isTrustedRequest({ headers: { host: '127.0.0.1:3080', 'sec-fetch-site': 'cross-site' } }) === false);
check('跨源 origin 拒绝', isTrustedRequest({ headers: { host: '127.0.0.1:3080', origin: 'http://evil.example.com' } }) === false);
check('同源 origin 通过', isTrustedRequest({ headers: { host: '127.0.0.1:3080', origin: 'http://127.0.0.1:3080' } }) === true);

console.log('\n=== 2. HTTP 行为 ===');
const forbidden = await invoke(makeRequest({ headers: { host: 'evil.example.com' } }));
check('外部 host 收到 403', forbidden.status === 403 && forbidden.parsed?.ok === false);

const get = await invoke(makeRequest({ headers: { host: '127.0.0.1:3080' } }));
check('GET 返回 200 与状态', get.status === 200 && get.parsed?.ok === true && typeof get.parsed.value.state === 'object');

const created = await invoke(
  makeRequest({ method: 'POST', headers: { host: '127.0.0.1:3080' }, body: { action: 'addRepo', repo: 'liustack/modlens' } }),
);
check('POST addRepo 成功', created.status === 200 && created.parsed?.ok === true);

const singleInstall = await invoke(
  makeRequest({
    method: 'POST',
    headers: { host: '127.0.0.1:3080' },
    body: { action: 'installSkill', id: 'liustack__modlens', name: 'modlens' },
  }),
);
check(
  'POST installSkill 分发到服务并带上技能名',
  singleInstall.status === 200 &&
    singleInstall.parsed?.ok === true &&
    serviceStub.seen.includes('installSkill:liustack__modlens:modlens'),
);

const unknown = await invoke(
  makeRequest({ method: 'POST', headers: { host: '127.0.0.1:3080' }, body: { action: 'nope' } }),
);
check('未知 action 返回 400', unknown.status === 400 && unknown.parsed?.error?.code === 'bad-action');

const brokenJson = await invoke(
  makeRequest({ method: 'POST', headers: { host: '127.0.0.1:3080' }, body: '{not json' }),
);
check('非法 JSON 返回 400', brokenJson.status === 400 && brokenJson.parsed?.error?.code === 'bad-json');

const wrongMethod = await invoke(makeRequest({ method: 'DELETE', headers: { host: '127.0.0.1:3080' } }));
check('DELETE 返回 405', wrongMethod.status === 405);

console.log('\n=== 3. 路由常量 ===');
check('路由路径固定', API_PATH === '/skill-hub/api');

const failed = checks.filter((item) => !item.ok);
console.log(`\n结果：${checks.length - failed.length}/${checks.length} 通过`);
process.exit(failed.length === 0 ? 0 : 1);
