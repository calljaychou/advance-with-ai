/**
 * HTTP surface of dsh-skill-hub, mounted on the DSH web server.
 *
 * The route is loopback- and same-origin-fenced on purpose: every action here
 * downloads code from GitHub and writes into the harness data directory, so it
 * must not be reachable from another origin or another machine.
 *
 * @module dsh-skill-hub/api
 */
import { GitHubError } from './github.js';

/** Absolute path of the plugin's JSON endpoint. */
export const API_PATH = '/skill-hub/api';

/** Largest accepted request body. */
const MAX_BODY_BYTES = 64 * 1024;

/**
 * Whether a hostname names the local machine.
 * @param hostname - a `URL.hostname` value.
 * @returns true for loopback names and addresses.
 */
function isLoopbackHost(hostname) {
  const host = String(hostname).replace(/^\[|\]$/g, '').toLowerCase();
  if (host === 'localhost' || host === '::1') return true;
  return /^127\.\d{1,3}\.\d{1,3}\.\d{1,3}$/.test(host);
}

/**
 * Reject cross-site and non-loopback callers, mirroring the built-in routes.
 * @param req - the incoming request.
 * @returns true when the request may be served.
 */
export function isTrustedRequest(req) {
  const host = req?.headers?.host;
  if (typeof host !== 'string' || host === '') return false;
  let hostUrl;
  try {
    hostUrl = new URL(`http://${host}`);
  } catch {
    return false;
  }
  if (!isLoopbackHost(hostUrl.hostname)) return false;
  if (req.headers['sec-fetch-site'] === 'cross-site') return false;
  const origin = req.headers.origin;
  if (origin === undefined) return true;
  try {
    return new URL(origin).host === hostUrl.host;
  } catch {
    return false;
  }
}

/**
 * Read and parse a bounded JSON request body.
 * @param req - the incoming request.
 * @returns the parsed body, or an empty object when absent.
 */
async function readJsonBody(req) {
  const chunks = [];
  let size = 0;
  for await (const chunk of req) {
    size += chunk.length;
    if (size > MAX_BODY_BYTES) throw new GitHubError('payload-too-large', '请求体过大');
    chunks.push(chunk);
  }
  if (chunks.length === 0) return {};
  try {
    const parsed = JSON.parse(Buffer.concat(chunks).toString('utf8'));
    return parsed !== null && typeof parsed === 'object' ? parsed : {};
  } catch {
    throw new GitHubError('bad-json', '请求体不是合法 JSON');
  }
}

/** A successful envelope. */
function ok(value) {
  return { ok: true, value };
}

/** A failed envelope. */
function fail(code, message) {
  return { ok: false, error: { code, message } };
}

/**
 * Build the request handler bound to one service instance.
 * @param service - the skill-hub service.
 * @param logger - a diagnostic sink.
 * @returns an async `(req, res)` handler.
 */
export function createApiHandler(service, logger) {
  /**
   * Dispatch one action.
   * @param action - the requested action name.
   * @param body - the request payload.
   * @returns the action result, always accompanied by the fresh snapshot.
   */
  const dispatch = async (action, body) => {
    /** Every successful action answers with the freshly enriched view. */
    const view = async () => ({ state: await service.view() });
    switch (action) {
      case 'getState':
        return view();
      case 'addRepo':
        await service.addRepo(body.repo, { ref: body.ref, label: body.label });
        return view();
      case 'removeRepo':
        service.removeRepo(String(body.id ?? ''), body.uninstall === true);
        return view();
      case 'scan':
        await service.scanRepo(String(body.id ?? ''));
        return view();
      case 'scanAll':
        await service.scanAll();
        return view();
      case 'install':
        await service.installRepo(String(body.id ?? ''), Array.isArray(body.skills) ? body.skills : undefined, {
          rescan: body.rescan === true,
        });
        return view();
      case 'installSkill':
        await service.installSkill(String(body.id ?? ''), String(body.name ?? ''), { rescan: body.rescan === true });
        return view();
      case 'installAll':
        await service.installAll();
        return view();
      case 'uninstall':
        service.uninstallSkill(String(body.id ?? ''), String(body.name ?? ''));
        return view();
      case 'reload':
        service.reload();
        return view();
      default:
        throw new GitHubError('bad-action', `未知操作 "${action}"`);
    }
  };

  return async function handleApi(req, res) {
    /**
     * Write one JSON response.
     * @param status - the HTTP status code.
     * @param body - the envelope to serialize.
     */
    const send = (status, body) => {
      res.writeHead(status, { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' });
      res.end(JSON.stringify(body));
    };

    if (!isTrustedRequest(req)) {
      send(403, fail('forbidden', '该接口仅接受本机同源请求'));
      return;
    }

    try {
      if (req.method === 'GET') {
        send(200, ok({ state: await service.view() }));
        return;
      }
      if (req.method !== 'POST') {
        send(405, fail('method-not-allowed', '仅支持 GET 与 POST'));
        return;
      }
      const body = await readJsonBody(req);
      const action = typeof body.action === 'string' ? body.action : '';
      const value = await dispatch(action, body);
      send(200, ok(value));
    } catch (error) {
      const known = error instanceof GitHubError;
      const code = known ? error.code : 'internal';
      const message = error?.message ?? String(error);
      logger?.warn?.(`skill-hub: 接口失败 [${code}] ${message}`);
      send(known ? 400 : 500, fail(code, message));
    }
  };
}
