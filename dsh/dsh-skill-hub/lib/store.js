/**
 * Persistent configuration and installed-skill state for dsh-skill-hub.
 *
 * Layout under the DSH home directory (default `~/.dsh`):
 *   skill-hub/config.json      user configuration: the configured repositories
 *   skill-hub/state.json       scan results and installed-skill records
 *   skill-hub/cache/<id>/<sha> extracted repository snapshots, keyed by commit
 *   skill-hub/skills/<id>/...  installed skill directories
 *
 * @module dsh-skill-hub/store
 */
import { existsSync, mkdirSync, readFileSync, renameSync, rmSync, writeFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { dirname, join } from 'node:path';

/** Environment variable that overrides the DSH home directory. */
const DSH_HOME_ENV = 'DSH_HOME';

/**
 * Resolve the DSH home directory: `$DSH_HOME` when set, else `~/.dsh`.
 * @returns the absolute DSH home path.
 */
export function dshHome() {
  const configured = process.env[DSH_HOME_ENV];
  if (typeof configured === 'string' && configured.trim() !== '') return configured.trim();
  return join(homedir(), '.dsh');
}

/**
 * Resolve a path inside this plugin's data directory.
 * @param segments - path segments appended to `$DSH_HOME/skill-hub`.
 * @returns the absolute path.
 */
export function dataPath(...segments) {
  return join(dshHome(), 'skill-hub', ...segments);
}

/** Create a directory (and parents) when missing. */
function ensureDir(path) {
  mkdirSync(path, { recursive: true });
}

/**
 * Read a JSON document, returning `fallback` when it is absent or unreadable.
 * @param path - absolute file path.
 * @param fallback - value returned when the file does not hold valid JSON.
 * @returns the parsed document or the fallback.
 */
function readJson(path, fallback) {
  if (!existsSync(path)) return fallback;
  try {
    const parsed = JSON.parse(readFileSync(path, 'utf8'));
    return parsed ?? fallback;
  } catch {
    return fallback;
  }
}

/**
 * Write a JSON document atomically (temp file + rename) with owner-only mode.
 * @param path - absolute destination path.
 * @param value - the JSON-serializable value to persist.
 */
function writeJson(path, value) {
  ensureDir(dirname(path));
  const temp = `${path}.tmp-${process.pid}-${Date.now()}`;
  writeFileSync(temp, `${JSON.stringify(value, null, 2)}\n`, { mode: 0o600 });
  renameSync(temp, path);
}

/** The default empty configuration document. */
function emptyConfig() {
  return { version: 1, repos: [] };
}

/** The default empty state document. */
function emptyState() {
  return { version: 1, repos: {}, installed: {} };
}

/**
 * Normalize an `owner/repo` slug or GitHub URL into `owner/repo`.
 * @param input - raw user input, e.g. `liustack/modlens` or a full GitHub URL.
 * @returns the normalized slug, or `undefined` when it cannot be understood.
 */
export function normalizeRepoSlug(input) {
  const raw = String(input ?? '').trim();
  if (raw === '') return undefined;
  let candidate = raw;
  const url = /^(?:https?:\/\/)?(?:www\.)?github\.com\/(.+)$/i.exec(raw);
  if (url !== null) candidate = url[1];
  candidate = candidate.replace(/\.git$/i, '').replace(/^\/+|\/+$/g, '');
  const parts = candidate.split('/').filter((part) => part !== '');
  if (parts.length < 2) return undefined;
  const [owner, repo] = parts;
  if (!/^[\w.-]+$/.test(owner) || !/^[\w.-]+$/.test(repo)) return undefined;
  return `${owner}/${repo}`;
}

/** Stable identifier for a configured repository row. */
function repoId(slug) {
  return slug.replace('/', '__').toLowerCase();
}

/**
 * Configuration store backed by `skill-hub/config.json`.
 */
export class ConfigStore {
  /** Absolute path of the configuration document. */
  file = dataPath('config.json');

  /**
   * Read the configuration, repairing unknown shapes.
   * @returns the configuration document.
   */
  read() {
    const document = readJson(this.file, emptyConfig());
    const repos = Array.isArray(document.repos) ? document.repos : [];
    return {
      version: 1,
      repos: repos
        .filter((row) => row !== null && typeof row === 'object')
        .map((row) => ({
          id: typeof row.id === 'string' && row.id !== '' ? row.id : repoId(String(row.repo ?? '')),
          repo: String(row.repo ?? ''),
          ref: typeof row.ref === 'string' ? row.ref : '',
          label: typeof row.label === 'string' ? row.label : '',
          enabled: row.enabled !== false,
        }))
        .filter((row) => row.repo !== ''),
    };
  }

  /**
   * Replace the whole configuration document.
   * @param document - the configuration to persist.
   * @returns the persisted configuration.
   */
  write(document) {
    const next = { version: 1, repos: Array.isArray(document?.repos) ? document.repos : [] };
    writeJson(this.file, next);
    return next;
  }

  /**
   * Add a repository when it is not configured yet.
   * @param input - `owner/repo` slug or GitHub URL.
   * @param options - optional branch/tag ref and display label.
   * @returns the created row, or `undefined` for an unparsable slug.
   */
  addRepo(input, options = {}) {
    const slug = normalizeRepoSlug(input);
    if (slug === undefined) return undefined;
    const document = this.read();
    const id = repoId(slug);
    const existing = document.repos.find((row) => row.id === id);
    if (existing !== undefined) {
      existing.ref = typeof options.ref === 'string' ? options.ref : existing.ref;
      existing.label = typeof options.label === 'string' ? options.label : existing.label;
      existing.enabled = true;
      this.write(document);
      return existing;
    }
    const row = {
      id,
      repo: slug,
      ref: typeof options.ref === 'string' ? options.ref : '',
      label: typeof options.label === 'string' ? options.label : '',
      enabled: true,
    };
    document.repos.push(row);
    this.write(document);
    return row;
  }

  /**
   * Remove a repository row.
   * @param id - the row identifier.
   * @returns true when a row was removed.
   */
  removeRepo(id) {
    const document = this.read();
    const before = document.repos.length;
    document.repos = document.repos.filter((row) => row.id !== id);
    this.write(document);
    return document.repos.length !== before;
  }
}

/**
 * State store backed by `skill-hub/state.json`.
 */
export class StateStore {
  /** Absolute path of the state document. */
  file = dataPath('state.json');

  /** @returns the state document. */
  read() {
    const document = readJson(this.file, emptyState());
    return {
      version: 1,
      repos: document.repos !== null && typeof document.repos === 'object' ? document.repos : {},
      installed: document.installed !== null && typeof document.installed === 'object' ? document.installed : {},
    };
  }

  /**
   * Merge a per-repository scan result into the state.
   * @param id - the repository row identifier.
   * @param entry - the scan result to store.
   */
  setRepoScan(id, entry) {
    const document = this.read();
    document.repos[id] = entry;
    writeJson(this.file, document);
  }

  /**
   * Merge installed-skill records into the state.
   * @param records - keyed records to upsert.
   */
  setInstalled(records) {
    const document = this.read();
    Object.assign(document.installed, records);
    writeJson(this.file, document);
  }

  /**
   * Drop installed-skill records.
   * @param keys - state keys to delete.
   */
  clearInstalled(keys) {
    const document = this.read();
    for (const key of keys) delete document.installed[key];
    writeJson(this.file, document);
  }
}

/**
 * Prepare the data directories this plugin writes into.
 * @returns the created directory paths.
 */
export function ensureDataDirs() {
  const paths = {
    root: dataPath(),
    cache: dataPath('cache'),
    skills: dataPath('skills'),
  };
  for (const path of Object.values(paths)) ensureDir(path);
  return paths;
}

/**
 * Delete a directory tree, ignoring a missing path.
 * @param path - the directory to remove.
 */
export function removeTree(path) {
  rmSync(path, { recursive: true, force: true });
}

export { ensureDir, repoId };
