// Runs every H-<nn>-<tool>.mjs repro in its own process and prints one line each.
// H01_DEPS=/tmp/h01deps TZ=America/Los_Angeles node _build/review/H-01/run_all.mjs [filter]
// "bug" means the repro failed (the bug is there); "fixed" means it passed. Exit 1 if any bug is still there.
import fs from 'fs';
import path from 'path';
import { spawnSync } from 'child_process';
import { fileURLToPath } from 'url';
const here = path.dirname(fileURLToPath(import.meta.url));
const files = fs.readdirSync(here).filter((f) => /^H-\d\d-[a-z0-9]+\.mjs$/.test(f) && f.includes(process.argv[2] || '')).sort();
let bugs = 0;
for (const f of files) {
  const t = Date.now();
  const r = spawnSync(process.execPath, [path.join(here, f)], { encoding: 'utf8', env: process.env, timeout: 300000 });
  const last = ((r.stdout || '') + (r.stderr || '')).trim().split('\n').pop() || '';
  const state = r.status === 1 ? 'bug  ' : r.status === 0 ? 'fixed' : 'error';
  if (r.status !== 0) bugs++;
  console.log(state + ' ' + f + ' (' + Math.round((Date.now() - t) / 1000) + ' s) ' + last.slice(0, 200));
}
console.log(files.length + ' repros, ' + bugs + ' still failing');
process.exit(bugs ? 1 : 0);
