// Compara docs/ (servido local) contra las capturas de referencia de Wix en source/reference.
// Uso: node tools/compare.mjs [anchos separados por coma]   (TF_URL=https://... para comparar el sitio publicado)   -> escribe .cache/compare/*.png y un resumen
import { createRequire } from 'module';
import { execSync, spawn } from 'child_process';
import { fileURLToPath } from 'url';
import fs from 'fs';
import path from 'path';

const require = createRequire(import.meta.url);
const { chromium } = require(path.join(execSync('npm root -g').toString().trim(), 'playwright'));
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const OUT = path.join(ROOT, '.cache', 'compare');
fs.mkdirSync(OUT, { recursive: true });
const widths = (process.argv[2] || '1440,1920,1024,900,768,390').split(',').map(Number);
const WIX_BANNER = 30; // alto del banner "Creado con Wix" en la referencia

const server = spawn('python3', ['-m', 'http.server', '8765', '-d', path.join(ROOT, 'docs')], { stdio: 'ignore' });
await new Promise(r => setTimeout(r, 800));
const browser = await chromium.launch();
try {
  for (const w of widths) {
    const p = await browser.newPage({ viewport: { width: w, height: 900 } });
    await p.goto(process.env.TF_URL || 'http://localhost:8765/', { waitUntil: 'load' });
    await p.evaluate(() => document.fonts.ready);
    const H = await p.evaluate(() => document.documentElement.scrollHeight);
    for (let y = 0; y < H; y += 300) { await p.evaluate(y => scrollTo(0, y), y); await p.waitForTimeout(60); }
    await p.waitForTimeout(2500);
    await p.evaluate(() => scrollTo(0, 0)); await p.waitForTimeout(500);
    const file = path.join(OUT, `clone-${w}.png`);
    await p.screenshot({ path: file, fullPage: true });
    await p.close();
    const out = execSync(`python3 "${path.join(ROOT, 'tools', 'diff_images.py')}" "${path.join(ROOT, 'source', 'reference', `full-${w}.png`)}" "${file}" "${path.join(OUT, `diff-${w}.png`)}" ${WIX_BANNER}`).toString();
    console.log(w, out.trim());
  }
} finally {
  await browser.close();
  server.kill();
}
