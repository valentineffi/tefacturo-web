// Reproduce las mismas interacciones en Wix y en el clon y guarda capturas lado a lado en .cache/compare/ix-*.png
// Uso: node tools/compare_interactions.mjs
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
const SITES = { wix: 'https://ailen4403.wixstudio.com/tfacturo', clone: 'http://localhost:8765/' };

const CASES = [
  { name: 'card-hover', w: 1440, run: async p => {
      await p.evaluate(() => document.getElementById('comp-mpcom3xk').scrollIntoView()); await p.waitForTimeout(2500);
      const r = await p.evaluate(() => document.getElementById('comp-mpcom3xv4').getBoundingClientRect().toJSON());
      await p.mouse.move(r.x + r.width / 2, r.y + r.height / 2); await p.waitForTimeout(900);
    } },
  { name: 'tab-3', w: 1440, run: async p => {
      await p.evaluate(() => document.getElementById('comp-mo3g1cca').scrollIntoView()); await p.waitForTimeout(2500);
      await p.click('#tab-comp-mo3gaczk'); await p.waitForTimeout(800);
    } },
  { name: 'burger-open', w: 390, h: 844, run: async p => {
      await p.click('#comp-kbgakxea_r_comp-mnhluyru button[aria-label="Menu"]'); await p.waitForTimeout(1200);
    } },
  { name: 'burger-link', w: 390, h: 844, run: async p => {
      await p.click('#comp-kbgakxea_r_comp-mnhluyru button[aria-label="Menu"]'); await p.waitForTimeout(1200);
      await p.click('text=Contacto >> visible=true'); await p.waitForTimeout(2500);
      console.log('   scrollY', await p.evaluate(() => Math.round(scrollY)));
    } },
  { name: 'cta-hover', w: 1440, run: async p => {
      await p.hover('#comp-kbgakxea_r_comp-mndcac9l'); await p.waitForTimeout(700);
    } },
];

const server = spawn('python3', ['-m', 'http.server', '8765', '-d', path.join(ROOT, 'docs')], { stdio: 'ignore' });
await new Promise(r => setTimeout(r, 800));
const browser = await chromium.launch();
try {
  for (const c of CASES) {
    const shots = [];
    for (const [k, url] of Object.entries(SITES)) {
      const p = await browser.newPage({ viewport: { width: c.w, height: c.h || 900 } });
      await p.goto(url, { waitUntil: 'load' }); await p.waitForTimeout(3500);
      console.log(c.name, k);
      try { await c.run(p); } catch (e) { console.log('   ERROR', e.message.split('\n')[0]); }
      const f = path.join(OUT, `ix-${c.name}-${k}.png`); await p.screenshot({ path: f }); shots.push(f);
      await p.close();
    }
    execSync(`python3 -c "
from PIL import Image
a,b=[Image.open(x) for x in ['${shots[0]}','${shots[1]}']]
s=Image.new('RGB',(a.width*2+10,a.height),(255,0,255)); s.paste(a,(0,0)); s.paste(b,(a.width+10,0)); s.save('${path.join(OUT, `ix-${c.name}.png`)}')"`);
  }
} finally { await browser.close(); server.kill(); }
