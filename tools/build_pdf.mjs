// Genera el PDF "Funcionalidades principales" desde src/pdf/funcionalidades.html -> src/pdf/<nombre>.pdf
// (build_site.py lo copia a docs/assets/docs/). Inter sale de las fuentes locales del sitio: correr después de un
// build_site.py, que deja docs/assets/fonts y site.css.
// Uso: node tools/build_pdf.mjs   (playwright global, como capture_wix.mjs; CHROME=<ruta> usa ese navegador)
import { createRequire } from 'module';
import { execSync } from 'child_process';
import { fileURLToPath, pathToFileURL } from 'url';
import fs from 'fs';
import path from 'path';

const require = createRequire(import.meta.url);
const { chromium } = require(path.join(execSync('npm root -g').toString().trim(), 'playwright'));
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const SRC = path.join(ROOT, 'src', 'pdf', 'funcionalidades.html');
const OUT = path.join(ROOT, 'src', 'pdf', 'Funcionalidades-Principales-TeFacturo.pdf');
const FONTS = path.join(ROOT, 'docs', 'assets', 'fonts');

const css = fs.readFileSync(path.join(ROOT, 'docs', 'assets', 'css', 'site.css'), 'utf8');
const fonts = (css.match(/@font-face\s*\{[^}]*\}/g) || [])
  .filter(f => /font-family:\s*['"]?inter['"]?\s*;/.test(f))
  .map(f => f.replace(/url\((['"]?)\.\.\/fonts\/([^'")]+)\1\)/g, (_, q, name) => `url(${pathToFileURL(path.join(FONTS, name))})`))
  .join('\n');
if (!fonts) throw new Error('No encontré Inter en docs/assets/css/site.css: correr antes python3 tools/build_site.py');
const logo = fs.readFileSync(path.join(ROOT, 'brand', 'logos', 'svg', 'tefacturo-isologo-naranja.svg'), 'utf8')
  .replace(/^[\s\S]*?<svg[^>]*>/, '').replace(/<\/svg>\s*$/, '');

const html = fs.readFileSync(SRC, 'utf8').replace('{{FONTS}}', fonts).replace('{{LOGO}}', logo);
const tmp = path.join(path.dirname(SRC), '.funcionalidades.tmp.html');
fs.writeFileSync(tmp, html);
const browser = await chromium.launch(process.env.CHROME ? { executablePath: process.env.CHROME } : {});
try {
  const page = await browser.newPage();
  await page.goto(pathToFileURL(tmp).href, { waitUntil: 'load' });
  await page.evaluate(() => document.fonts.ready);
  // body mide una hoja A4: si el contenido lo desborda, el PDF saldría con una segunda hoja
  const overflow = await page.evaluate(() => document.body.scrollHeight > document.body.clientHeight + 1);
  if (overflow) throw new Error('El contenido no entra en una hoja A4: ajustar row-gap o el texto');
  await page.pdf({ path: OUT, format: 'A4', printBackground: true, margin: { top: 0, right: 0, bottom: 0, left: 0 } });
  console.log('pdf:', path.relative(ROOT, OUT), Math.round(fs.statSync(OUT).size / 1024), 'KB');
} finally {
  await browser.close();
  fs.rmSync(tmp, { force: true });
}
