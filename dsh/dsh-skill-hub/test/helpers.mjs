/**
 * Shared test helpers.
 *
 * Every test that touches the data directory redirects `DSH_HOME` to a fresh
 * temporary directory, so tests are order-independent and never write into the
 * developer's real `~/.dsh`. The repository cache is seeded from the real home
 * when present, keeping scans offline-fast.
 *
 * @module dsh-skill-hub/test/helpers
 */
import { cpSync, existsSync, mkdtempSync, rmSync } from 'node:fs';
import { homedir, tmpdir } from 'node:os';
import { join } from 'node:path';

/**
 * Point `DSH_HOME` at a throwaway directory for the current process.
 * @returns the temporary home directory.
 */
export function useTempHome() {
  const home = mkdtempSync(join(tmpdir(), 'dsh-skill-hub-test-'));
  process.env.DSH_HOME = home;
  const realCache = join(homedir(), '.dsh', 'skill-hub', 'cache');
  if (existsSync(realCache)) {
    try {
      cpSync(realCache, join(home, 'skill-hub', 'cache'), { recursive: true });
    } catch {
      // A cache miss only costs a download; it must never fail the test run.
    }
  }
  process.on('exit', () => {
    try {
      rmSync(home, { recursive: true, force: true });
    } catch {
      // Best effort: the OS cleans up temporary directories anyway.
    }
  });
  return home;
}

/**
 * Assertion recorder shared by the tests.
 * @returns a `check(label, condition)` function plus the collected results.
 */
export function createChecker() {
  const checks = [];
  /**
   * Record one assertion.
   * @param label - what is being checked.
   * @param condition - the assertion result.
   */
  const check = (label, condition) => {
    checks.push({ label, ok: Boolean(condition) });
    console.log(`  ${condition ? 'PASS' : 'FAIL'}  ${label}`);
  };
  check.checks = checks;
  return check;
}

/**
 * Print the summary and exit with a failing status when anything failed.
 * @param checks - the collected assertion results.
 * @param label - the suite name used in the header.
 */
export function finish(checks, label = '结果') {
  const failed = checks.filter((item) => !item.ok);
  console.log(`\n${label}：${checks.length - failed.length}/${checks.length} 通过`);
  if (failed.length > 0) for (const item of failed) console.log(`  失败: ${item.label}`);
  process.exit(failed.length === 0 ? 0 : 1);
}
