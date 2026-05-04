// Content purity check — fails if banned phrases reappear in source.
// Runs in <100ms; no browser needed. Use as the first PR gate.

import { execSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const REPO_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');

const BANNED = [
  // Stripped per changes.md item #1 + #13 (rohit's call: strip everywhere).
  /AI[- ]augmented/i,
  /TradingAgents/i,
];

const PATHS = ['content', 'layouts', 'hugo.toml', 'assets'];

function rg(pattern, paths) {
  try {
    const out = execSync(
      `rg -nI --no-heading -e ${JSON.stringify(pattern)} ${paths.map(p => JSON.stringify(p)).join(' ')}`,
      { encoding: 'utf8', cwd: REPO_ROOT }
    );
    return out.split('\n').filter(Boolean);
  } catch (e) {
    // rg exits 1 when no matches; that's what we want.
    if (e.status === 1) return [];
    throw e;
  }
}

let failed = 0;
for (const re of BANNED) {
  const pattern = re.source;
  const flag = re.ignoreCase ? '(?i)' : '';
  const hits = rg(`${flag}${pattern}`, PATHS);
  if (hits.length) {
    failed += 1;
    console.log(`FAIL: banned phrase /${re.source}/${re.flags} reappeared:`);
    hits.slice(0, 20).forEach(h => console.log(`  ${h}`));
    if (hits.length > 20) console.log(`  …and ${hits.length - 20} more`);
  } else {
    console.log(`PASS: no /${re.source}/${re.flags} in ${PATHS.join(' ')}`);
  }
}

if (failed) process.exit(1);
console.log('\nOK: content purity check passed');
