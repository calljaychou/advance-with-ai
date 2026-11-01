/**
 * GitHub access for dsh-skill-hub: resolve a repository and a commit SHA, then
 * download and extract that exact snapshot once.
 *
 * Only public repositories are supported, so every request is unauthenticated
 * and the request count per scan is deliberately tiny: one repository lookup,
 * one commit lookup, and one tarball download (plus a cache hit afterwards).
 *
 * @module dsh-skill-hub/github
 */
import { existsSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
/** `tar` v7 publishes named exports only, so the extractor is imported by name. */
import { x as tarExtract } from 'tar';

import { dataPath, ensureDir, removeTree } from './store.js';

/** GitHub REST endpoint. */
const API_BASE = 'https://api.github.com';

/** Requests carry a descriptive agent so GitHub can attribute traffic. */
const USER_AGENT = 'dsh-skill-hub';

/** Failure carrying a machine-readable code alongside a user-facing message. */
export class GitHubError extends Error {
  /**
   * @param code - stable error code consumed by the UI.
   * @param message - user-facing message.
   */
  constructor(code, message) {
    super(message);
    this.name = 'GitHubError';
    this.code = code;
  }
}

/**
 * Perform an authenticated-free GitHub API request.
 * @param path - API path beginning with `/`.
 * @param options - `raw` returns the response body instead of parsed JSON.
 * @returns the parsed JSON body, or the raw response when `raw` is set.
 */
async function githubRequest(path, options = {}) {
  const { raw = false, accept = 'application/vnd.github+json' } = options;
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      headers: { accept, 'user-agent': USER_AGENT, 'x-github-api-version': '2022-11-28' },
      redirect: 'follow',
    });
  } catch (error) {
    throw new GitHubError('network', `无法访问 GitHub：${error?.message ?? String(error)}`);
  }
  if (response.status === 404) {
    throw new GitHubError('not-found', '仓库不存在，或它是私有仓库（当前仅支持公开仓库）');
  }
  if (response.status === 403 || response.status === 429) {
    const remaining = response.headers.get('x-ratelimit-remaining');
    const reset = response.headers.get('x-ratelimit-reset');
    const when = reset === null ? '' : `，配额重置于 ${new Date(Number(reset) * 1000).toLocaleTimeString()}`;
    throw new GitHubError(
      'rate-limited',
      `GitHub 接口限流（未认证请求每小时 60 次，剩余 ${remaining ?? '0'}）${when}。稍后重试即可。`,
    );
  }
  if (!response.ok) {
    throw new GitHubError('http', `GitHub 返回 ${response.status} ${response.statusText}`);
  }
  if (raw) return response;
  return response.json();
}

/**
 * Resolve a repository's default branch and canonical name.
 * @param slug - `owner/repo`.
 * @returns the resolved repository facts.
 */
export async function resolveRepo(slug) {
  const payload = await githubRequest(`/repos/${slug}`);
  return {
    fullName: typeof payload?.full_name === 'string' ? payload.full_name : slug,
    defaultBranch: typeof payload?.default_branch === 'string' ? payload.default_branch : 'main',
    description: typeof payload?.description === 'string' ? payload.description : '',
    stars: typeof payload?.stargazers_count === 'number' ? payload.stargazers_count : 0,
    pushedAt: typeof payload?.pushed_at === 'string' ? payload.pushed_at : '',
  };
}

/**
 * Resolve the commit SHA a ref points at.
 * @param slug - `owner/repo`.
 * @param ref - branch, tag, or commit; empty selects the default branch.
 * @param defaultBranch - fallback ref when `ref` is empty.
 * @returns the resolved commit SHA.
 */
export async function resolveSha(slug, ref, defaultBranch) {
  const target = ref === undefined || ref === null || String(ref).trim() === '' ? defaultBranch : String(ref).trim();
  const payload = await githubRequest(`/repos/${slug}/commits/${encodeURIComponent(target)}`);
  const sha = payload?.sha;
  if (typeof sha !== 'string' || sha === '') {
    throw new GitHubError('bad-response', `无法解析 ${slug}@${target} 的 commit`);
  }
  return { sha, ref: target };
}

/**
 * Download and extract a repository snapshot, reusing an existing extraction.
 * @param slug - `owner/repo`.
 * @param sha - the exact commit to materialize.
 * @returns the directory containing the extracted tree (its single root entry).
 */
export async function materializeSnapshot(slug, sha) {
  const target = dataPath('cache', slug.replace('/', '__').toLowerCase(), sha);
  const marker = join(target, '.dsh-skill-hub-ok');

  if (existsSync(marker)) {
    const root = snapshotRoot(target);
    if (root !== undefined) return root;
  }

  removeTree(target);
  ensureDir(target);

  const response = await githubRequest(`/repos/${slug}/tarball/${sha}`, { raw: true });
  const bytes = Buffer.from(await response.arrayBuffer());
  if (bytes.length === 0) throw new GitHubError('empty-tarball', `${slug}@${sha} 的压缩包为空`);

  // Extract the in-memory tarball: gzip is handled by tar itself.
  const { Readable } = await import('node:stream');
  const { pipeline } = await import('node:stream/promises');
  await pipeline(Readable.from(bytes), tarExtract({ cwd: target }));

  const root = snapshotRoot(target);
  if (root === undefined) throw new GitHubError('empty-tarball', `${slug}@${sha} 解压后为空`);
  const { writeFileSync } = await import('node:fs');
  writeFileSync(marker, `${new Date().toISOString()}\n`, { mode: 0o600 });
  return root;
}

/**
 * Find the single top-level directory of an extracted GitHub tarball.
 * @param dir - the extraction directory.
 * @returns the absolute snapshot root, or `undefined` when it is missing.
 */
function snapshotRoot(dir) {
  let entries;
  try {
    entries = readdirSync(dir, { withFileTypes: true });
  } catch {
    return undefined;
  }
  const directories = entries.filter((entry) => entry.isDirectory() && !entry.name.startsWith('.'));
  if (directories.length === 1) return join(dir, directories[0].name);
  return dir;
}
