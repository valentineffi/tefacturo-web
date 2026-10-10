// Captura el sitio Wix renderizado: DOM, CSS completo (incluido el inyectado en runtime),
// el menú hamburguesa abierto, config de interacciones y screenshots de referencia.
// Uso: node tools/capture_wix.mjs   (requiere playwright instalado global: npm i -g playwright)
import { createRequire } from 'module';
import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const require = createRequire(import.meta.url);
const { chromium } = require(path.join(execSync('npm root -g').toString().trim(), 'playwright'));

const SITE = 'https://ailen4403.wixstudio.com/tfacturo';
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const OUT = path.join(ROOT, 'source');
fs.mkdirSync(path.join(OUT, 'reference'), { recursive: true });

const browser = await chromium.launch();

async function open(width, height = 900) {
  const page = await browser.newPage({ viewport: { width, height } });
  await page.goto(SITE, { waitUntil: 'load', timeout: 60000 });
  await page.waitForTimeout(4000);
  const H = await page.evaluate(() => document.documentElement.scrollHeight);
  for (let y = 0; y < H; y += 400) { await page.evaluate(y => scrollTo(0, y), y); await page.waitForTimeout(120); }
  await page.evaluate(() => scrollTo(0, 0));
  await page.waitForTimeout(2500);
  return page;
}

// Texto de cada hoja en orden. <style> con texto -> texto crudo; hojas <link> -> se bajan crudas;
// hojas construidas con insertRule (texto vacío) -> se serializa el CSSOM.
async function collectCss(page) {
  const sheets = await page.evaluate(() => [...document.styleSheets].map(s => {
    const n = s.ownerNode;
    const raw = n && n.tagName === 'STYLE' ? n.textContent : '';
    let cssom = '';
    try { cssom = [...s.cssRules].map(r => r.cssText).join('\n'); } catch (e) {}
    return { href: s.href, id: n && (n.id || n.dataset.url || n.dataset.href) || null, media: s.media.mediaText, raw, cssom };
  }));
  for (const s of sheets) {
    if (s.href) { try { s.raw = await (await page.request.get(s.href)).text(); } catch (e) {} }
    s.text = s.raw && s.raw.trim() ? s.raw : s.cssom;
    delete s.raw; delete s.cssom;
  }
  return sheets;
}

// 1) Desktop: DOM + CSS + features JSON
const page = await open(1440);
fs.writeFileSync(path.join(OUT, 'wix-dom.html'), await page.content());
const desktopCss = await collectCss(page);
const featuresHref = await page.evaluate(() => document.getElementById('features_c1dmp')?.href);
if (featuresHref) fs.writeFileSync(path.join(OUT, 'wix-features.json'), await (await page.request.get(featuresHref)).text());
await page.close();

// 2) Mobile: abrir hamburguesa, capturar el diálogo y el CSS que se cargó al abrir
const m = await open(390, 844);
const MENU = '#comp-kbgakxea_r_comp-mnhluyru';
const menuClosed = await m.evaluate(s => document.querySelector(s).outerHTML, MENU);
await m.click(MENU + ' button[aria-label="Menu"]');
await m.waitForTimeout(1500);
const PORTAL = '#portal-comp-kbgakxea_r_comp-mnhluyru';
const menuHtml = { closed: menuClosed, open: await m.evaluate(s => document.querySelector(s).outerHTML, MENU),
  portalOpen: await m.evaluate(s => document.querySelector(s)?.outerHTML, PORTAL),
  htmlClass: await m.evaluate(() => document.documentElement.className + ' | body: ' + document.body.className) };
fs.writeFileSync(path.join(OUT, 'wix-menu-open.json'), JSON.stringify(menuHtml));
await m.screenshot({ path: path.join(OUT, 'reference', 'menu-open-390.png') });
const mobileCss = await collectCss(m);
await m.close();

// Unión de hojas: orden desktop + las nuevas de mobile al final (por href/id/texto)
const key = s => s.href || s.id || s.text.slice(0, 200);
const seen = new Set(desktopCss.map(key));
const allCss = desktopCss.concat(mobileCss.filter(s => !seen.has(key(s))));
fs.writeFileSync(path.join(OUT, 'wix-css.json'), JSON.stringify(allCss));

// 3) Screenshots de referencia
// y tamaño renderizado de cada imagen/video (para srcset/sizes)
const sizes = {};
for (const w of [1440, 1920, 1024, 900, 768, 390]) {
  const p = await open(w);
  await p.screenshot({ path: path.join(OUT, 'reference', `full-${w}.png`), fullPage: true });
  sizes[w] = await p.evaluate(() => [...document.querySelectorAll('img, video')].map(e => {
    const c = e.closest('[id^="comp-"]'); const r = e.getBoundingClientRect();
    return { comp: c ? c.id : null, tag: e.tagName, src: (e.currentSrc || e.src || '').split('/v1/')[0].split('/').pop(), w: Math.round(r.width), h: Math.round(r.height) };
  }));
  await p.close();
}
fs.writeFileSync(path.join(OUT, 'wix-media-sizes.json'), JSON.stringify(sizes));
await browser.close();
console.log('ok', allCss.length, 'stylesheets; menu:', !!menuHtml.dialog);
