/**
 * Offline smoke test for the GitHub layer: resolve a public repository, pin a
 * commit, materialize the snapshot, and list candidate skill directories.
 *
 * Usage: node test/smoke.mjs [owner/repo ...]
 */
import { readdirSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';

import { materializeSnapshot, resolveRepo, resolveSha } from '../lib/github.js';

const DEFAULT_REPOS = ['liustack/modlens'];

/**
 * Recursively collect `SKILL.md` paths, skipping heavy or irrelevant folders.
 * @param root - snapshot root directory.
 * @returns relative paths of every SKILL.md found.
 */
function findSkillFiles(root) {
  const skip = new Set(['.git', 'node_modules', 'vendor', 'dist', 'build', '.next', '__pycache__']);
  const found = [];
  const walk = (dir, depth) => {
    if (depth > 6) return;
    for (const entry of readdirSync(dir, { withFileTypes: true })) {
      if (entry.name.startsWith('.') && entry.name !== '.') continue;
      const full = join(dir, entry.name);
      if (entry.isDirectory()) {
        if (skip.has(entry.name)) continue;
        walk(full, depth + 1);
      } else if (entry.name === 'SKILL.md') {
        found.push(relative(root, full));
      }
    }
  };
  walk(root, 0);
  return found.sort();
}

const repos = process.argv.slice(2).length > 0 ? process.argv.slice(2) : DEFAULT_REPOS;
let failures = 0;

for (const slug of repos) {
  try {
    const repo = await resolveRepo(slug);
    const { sha, ref } = await resolveSha(slug, '', repo.defaultBranch);
    const started = Date.now();
    const root = await materializeSnapshot(slug, sha);
    const skills = findSkillFiles(root);
    const cachedRoot = await materializeSnapshot(slug, sha);
    console.log(`\n=== ${slug} ===`);
    console.log(`  默认分支 : ${repo.defaultBranch} (${ref})`);
    console.log(`  commit   : ${sha}`);
    console.log(`  描述     : ${repo.description || '(无)'}  ★${repo.stars}`);
    console.log(`  快照根   : ${root}`);
    console.log(`  耗时     : ${Date.now() - started}ms（第二次命中缓存: ${cachedRoot === root}）`);
    console.log(`  发现 skill: ${skills.length}`);
    for (const path of skills) console.log(`    - ${path}`);
    if (!statSync(root).isDirectory()) throw new Error('snapshot root is not a directory');
  } catch (error) {
    failures += 1;
    console.log(`\n=== ${slug} ===`);
    console.log(`  失败: ${error.name}: ${error.message}`);
  }
}

console.log(`\n完成：${repos.length - failures}/${repos.length} 成功`);
process.exit(failures === 0 ? 0 : 1);
