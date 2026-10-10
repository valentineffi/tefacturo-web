#!/usr/bin/env python3
"""Genera docs/ (sitio estático para GitHub Pages) a partir de la captura de Wix en source/.

Entrada:  source/wix-dom.html, wix-css.json, wix-features.json, wix-media-sizes.json  (tools/capture_wix.mjs)
          src/site.js (runtime propio que reemplaza al JS de Wix)
Salida:   docs/index.html + docs/assets/{css,js,img,video,fonts,docs}
Caché:    .cache/ (originales bajados de Wix; no se versiona)
"""
import hashlib, html, json, os, re, shutil, subprocess, sys, unicodedata, urllib.request
from pathlib import Path
from PIL import Image

Image.MAX_IMAGE_PIXELS = None
ROOT = Path(__file__).resolve().parent.parent
SRC, OUT, CACHE = ROOT / 'source', ROOT / 'docs', ROOT / '.cache'
A = OUT / 'assets'

SITE_URL = 'https://valentineffi.github.io/tefacturo-web/'   # se ajusta al pasar a tefacturo.com.ar
TITLE = 'TeFacturo | Sistema de facturación electrónica simple'
DESCRIPTION = ('TeFacturo es un sistema de facturación electrónica simple pensado para pequeños y medianos '
               'comercios: software fácil de usar con un equipo POS dedicado para facturar en segundos.')

# Secciones (ids de Wix) a las que apuntan las anclas — de wix-features.json > scrollToAnchor
ANCHORS = json.loads((SRC / 'wix-features.json').read_text())['props']['scrollToAnchor']['anchorDataIdToCompIdMap']

# Texto alternativo por imagen (en Wix casi todas dicen "Pink Poppy Flowers"). '' = decorativa.
ALTS = {
    '78ccf8': 'TeFacturo', 'aed2c1': 'TeFacturo', '9e2f55': '', '0852d4': 'Ágil, simple & sin vueltas.',
    '974e21': 'Comerciante emitiendo una factura en un equipo POS TeFacturo',
    '185ebe': 'Comerciante usando una tablet en su local', '30a583': 'Comerciante sonriendo en su local',
    '277cc5': '', '4a4118': '', '544b8b': '', '80167c': '', 'dbfdcd': '',
    '6cb375': 'Preguntas frecuentes', 'e89585': 'Aprendé sobre el sistema. Empezar es fácil',
    '4d8e0b': '¿Más dudas? Contactanos por WhatsApp', '506553': 'Quiero mi TeFacturo',
    'cccfaa': 'Descubrí todas las funciones del sistema',
    'f172e0': 'Facturación electrónica', '9a64fe': 'Facturación electrónica AFIP/ARCA: emití Facturas A, B y C con CAE automático. Notas de crédito y débito.',
    '7e6ec9': 'Gestión de productos', 'eba5b1': 'Gestión de productos: alta masiva por CSV/Excel. Variantes, categorías jerárquicas y departamentos con impuestos internos.',
    '9af791': 'Reportes', '4da3fa': 'Reportes: KPIs de ventas, gráficos de tendencias, filtros por fecha, punto de venta, vendedor y cliente.',
    '51305e': 'Impresión térmica y PDF', 'ef238a': 'Impresión térmica y PDF: tickets de venta, notas de crédito, etiquetas de góndola. Detección automática de impresoras en red.',
    '2b000d': 'WhatsApp', 'd9ad68': 'Instagram', 'e99f41': 'Facebook',
}

# Desvíos deliberados respecto del Wix (ver CLAUDE.md > "Diferencias con Wix")
WHATSAPP_URL = 'https://wa.me/5492926508200'
PDF_NAME = 'Funcionalidades-Principales-TeFacturo.pdf'


def fetch(url, dest):
    dest = Path(dest)
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        dest.write_bytes(urllib.request.urlopen(req, timeout=120).read())
    return dest


def slug(s):
    s = re.sub(r'\.(png|jpe?g|webp)$', '', html.unescape(s), flags=re.I)
    s = s.replace('_3x', '').replace('@3x', '')
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
    s = re.sub(r'[^a-zA-Z0-9]+', '-', s).strip('-').lower()[:48].strip('-')
    return s or 'img'


# ---------------------------------------------------------------- CSS
def build_css(dom):
    sheets = json.loads((SRC / 'wix-css.json').read_text())
    parts = []
    for s in sheets:
        name = s['href'] or s['id'] or ''
        if 'FreemiumBanner' in name:
            continue
        t = s['text']
        if s['media'] and s['media'] not in ('all', ''):
            t = '@media %s{%s}' % (s['media'], t)
        parts.append('/* %s */\n%s' % (name.rsplit('/', 1)[-1][:80], t))
    css = '\n'.join(parts)
    css = re.sub(r'/\*# sourceMappingURL=[^*]*\*/', '', css)

    # Fuentes -> locales
    fonts = {}
    def font_url(m):
        url = m.group(2)
        full = 'https:' + url if url.startswith('//') else url
        ext = re.search(r'\.(woff2?|ttf|otf|eot)(?:\?|$)', full)
        ext = ext.group(1) if ext else 'woff2'
        name = hashlib.sha1(full.encode()).hexdigest()[:16] + '.' + ext
        fonts[name] = full
        return 'url(%s../fonts/%s%s)' % (m.group(1), name, m.group(1))
    css = re.sub(r'url\(([\'"]?)((?:https?:)?//static\.parastorage\.com/[^\'")]+)\1\)', font_url, css)
    for name, url in fonts.items():
        try:
            shutil.copy(fetch(url, CACHE / 'fonts' / name), A / 'fonts' / name)
        except Exception as e:  # algunas variantes (eot/cyrillic) pueden no existir: el navegador sigue con la siguiente
            print('  font fail', url[-60:], e)

    # Sin banner de Wix: el alto reservado pasa a 0
    css += '\n:root,:host,.spxThemeOverride{--wix-ads-height:0px!important;--sticky-offset:0px!important}\n'
    (A / 'css' / 'site.css').write_text(css)
    print('css', len(css) // 1024, 'KB,', len(fonts), 'fuentes')


# ---------------------------------------------------------------- Imágenes
MEDIA_RE = re.compile(r'https://static\.wixstatic\.com/media/(63393a_[0-9a-f]{32}~mv2\.(?:png|jpe?g))(/v1/[^"\s]*)?')
WIDTHS = [160, 320, 480, 640, 800, 1024, 1280, 1600, 1920, 2400, 3000, 3840]


def media_sizes():
    data = json.loads((SRC / 'wix-media-sizes.json').read_text())
    out = {}  # (comp, src) -> {vw: width}
    for vw, items in data.items():
        for it in items:
            if it['tag'] == 'IMG':
                out.setdefault((it['comp'], it['src']), {})[int(vw)] = it['w']
    return out


class Images:
    def __init__(self):
        self.sizes = media_sizes()
        self.done = {}

    def original(self, media_id):
        return fetch('https://static.wixstatic.com/media/' + media_id, CACHE / 'media' / media_id)

    def rendition_set(self, media_id, transform, alt, max_w):
        crop = re.search(r'/crop/x_(\d+),y_(\d+),w_(\d+),h_(\d+)', transform or '')
        key = (media_id, crop.groups() if crop else None)
        if key in self.done:
            return self.done[key]
        im = Image.open(self.original(media_id))
        im = im.convert('RGBA') if im.mode in ('RGBA', 'LA', 'P') else im.convert('RGB')
        if crop:
            x, y, w, h = map(int, crop.groups())
            im = im.crop((x, y, x + w, y + h))
        # Gráficos con transparencia (degradés, curvas, títulos) -> WebP sin pérdida: nada de banding
        lossless = im.mode == 'RGBA' and im.getchannel('A').getextrema()[0] < 255
        base = slug(alt) + '-' + media_id[7:13] + ('-c' + hashlib.sha1(str(key[1]).encode()).hexdigest()[:5] if crop else '')
        cap = min(im.width, max(320, int(max_w * 2)))       # hasta 2x del mayor tamaño mostrado
        widths = sorted({w for w in WIDTHS if w < cap} | {cap})
        files = []
        for w in widths:
            fn = '%s-%d%s.webp' % (base, w, 'l' if lossless else '')
            dst = A / 'img' / fn
            if not dst.exists():
                h = round(im.height * w / im.width)
                r = im.resize((w, h), Image.LANCZOS)
                if lossless:
                    r.save(dst, 'WEBP', lossless=True, quality=100, method=6)
                else:
                    r.save(dst, 'WEBP', quality=90, method=6)
            files.append((fn, w))
        self.done[key] = (files, im.width, im.height)
        return self.done[key]

    def sizes_attr(self, comp, src_name):
        m = self.sizes.get((comp, src_name)) or {}
        if not m:
            return '100vw', 1920
        def vw(v):
            w = m.get(v, 0)
            return '%.2fvw' % (100.0 * w / v) if w else '1px'
        return '(max-width: 750px) %s, (max-width: 1000px) %s, %s' % (vw(390), vw(900), vw(1440)), max(m.values())

    def rewrite(self, dom):
        # Cada <wow-image id="img-comp-X"> envuelve <picture><source ...><img ...></picture>
        def fix_block(mb):
            block = mb.group(0)
            comp = mb.group(1)
            def one(m, attr):
                media_id, tr = m.group(1), m.group(2)
                alt = ALTS.get(media_id[7:13])
                if not alt:
                    a = re.search(r'alt="([^"]*)"', block)
                    alt = 'decorativo' if alt == '' else (a.group(1) if a else media_id)
                sizes, max_w = self.sizes_attr(comp, media_id)
                files, W, H = self.rendition_set(media_id, tr, alt, max_w)
                srcset = ', '.join('assets/img/%s %dw' % (f, w) for f, w in files)
                return srcset, sizes, files
            def src_tag(mt):
                tag = mt.group(0)
                m = MEDIA_RE.search(tag)
                if not m:
                    return tag
                srcset, sizes, files = one(m, 'srcset')
                tag = re.sub(r'\ssrcset="[^"]*"', '', tag)
                return tag[:-1].rstrip('/') + ' srcset="%s" sizes="%s">' % (srcset, sizes)
            def img_tag(mt):
                tag = mt.group(0)
                m = MEDIA_RE.search(tag)
                if not m:
                    return tag
                srcset, sizes, files = one(m, 'src')
                mid = files[min(len(files) - 1, len(files) // 2)][0]
                tag = re.sub(r'\ssrcset="[^"]*"', '', tag)
                tag = re.sub(r'\ssrc="[^"]*"', ' src="assets/img/%s" srcset="%s" sizes="%s"' % (mid, srcset, sizes), tag)
                tag = re.sub(r'\sfetchpriority="[^"]*"', '', tag)
                if m.group(1)[7:13] in ALTS:
                    tag = re.sub(r'\salt="[^"]*"', ' alt="%s"' % html.escape(ALTS[m.group(1)[7:13]]), tag)
                return tag
            block = re.sub(r'<source\b[^>]*>', src_tag, block)
            block = re.sub(r'<img\b[^>]*>', img_tag, block)
            return block
        dom = re.sub(r'<wow-image id="img-(comp-[^"]+)".*?</wow-image>', fix_block, dom, flags=re.S)
        # Atributo con JSON de Wix: ya no hace falta
        dom = re.sub(r'\sdata-image-info="[^"]*"', '', dom)
        left = MEDIA_RE.findall(dom)
        if left:
            print('  OJO: quedan URLs de wixstatic:', len(left))
        return dom


# ---------------------------------------------------------------- Videos
def rewrite_videos(dom):
    def fix(m):
        tag, vid = m.group(0), m.group(1)
        src = fetch('https://video.wixstatic.com/video/%s/1080p/mp4/file.mp4' % vid, CACHE / 'video' / (vid + '.mp4'))
        poster_src = fetch('https://static.wixstatic.com/media/%sf000.jpg' % vid, CACHE / 'video' / (vid + '.jpg'))
        out = A / 'video' / (vid[7:19] + '-540.mp4')
        poster = A / 'video' / (vid[7:19] + '.webp')
        if not out.exists():
            subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', str(src), '-an', '-vf', 'scale=540:-2',
                            '-c:v', 'libx264', '-preset', 'slow', '-crf', '26', '-pix_fmt', 'yuv420p',
                            '-movflags', '+faststart', str(out)], check=True)
        if not poster.exists():
            Image.open(poster_src).convert('RGB').resize((720, 720), Image.LANCZOS).save(poster, 'WEBP', quality=82)
        tag = re.sub(r'\ssrc="[^"]*"', ' src="assets/video/%s" poster="assets/video/%s"' % (out.name, poster.name), tag)
        return tag.replace(' crossorigin="anonymous"', '')
    return re.sub(r'<video\b[^>]*src="https://video\.wixstatic\.com/video/(63393a_[0-9a-f]{32})/[^"]*"[^>]*>', fix, dom)


# ---------------------------------------------------------------- Limpieza del DOM
def remove_element(dom, start_pat):
    """Borra el elemento que abre en start_pat (regex) con todo su contenido (balanceando <div>/<tag>)."""
    m = re.search(start_pat, dom)
    if not m:
        return dom, False
    tag = re.match(r'<(\w[\w-]*)', m.group(0)).group(1)
    depth, i = 0, m.start()
    for t in re.finditer(r'<(/?)%s\b[^>]*?(/?)>' % tag, dom[i:]):
        if t.group(2):
            continue
        depth += -1 if t.group(1) else 1
        if depth == 0:
            return dom[:i] + dom[i + t.end():], True
    return dom, False


def clean(dom):
    dom = re.sub(r'<script\b[^>]*>.*?</script>', '', dom, flags=re.S)
    dom = re.sub(r'<noscript\b[^>]*>.*?</noscript>', '', dom, flags=re.S)
    dom = re.sub(r'<style\b[^>]*>.*?</style>', '', dom, flags=re.S)
    dom = re.sub(r'<link\b[^>]*>', '', dom)
    dom = re.sub(r'<meta\b[^>]*>', '', dom)
    dom = re.sub(r'<title>.*?</title>', '', dom, flags=re.S)
    dom = re.sub(r'<!--.*?-->', '', dom, flags=re.S)
    # Banner "Creado con Wix" y diálogo sobrante del template (oculto, con textos de ejemplo)
    for pat in [r'<div id="WIX_ADS"[^>]*>', r'<div id="comp-kd5px9q0"[^>]*>']:
        dom, ok = remove_element(dom, pat)
        print('  remove', pat[9:30], ok)
    # Overlay del menú hamburguesa: Wix crea el contenedor del <nav> recién al abrir. Usamos el overlay
    # capturado abierto, en estado cerrado y con el contenedor vacío (el runtime mueve el <nav> ahí).
    portal = json.loads((SRC / 'wix-menu-open.json').read_text())['portalOpen']
    portal, _ = remove_element(portal, r'<nav\b[^>]*>')
    portal = portal.replace(' HamburgerOverlay547129737--isMenuOpen', '').replace('data-visible="true"', 'data-visible="false"')
    pm = re.search(r'<div id="portal-comp-kbgakxea_r_comp-mnhluyru">', dom)
    dom, ok = remove_element(dom, r'<div id="portal-comp-kbgakxea_r_comp-mnhluyru">')
    dom = dom[:pm.start()] + portal + dom[pm.start():]
    print('  menu overlay', ok, 'slot' if 'comp-kbgakxea_r_comp-mnhluyv71' in portal else 'SIN SLOT')
    # Estado de animaciones: arrancan pausadas hasta que el runtime las dispare
    dom = dom.replace(' data-motion-enter="done"', '')
    dom = re.sub(r' style="(?:--motion-[a-z]+: [^;"]+;\s*)+"', '', dom)
    dom = re.sub(r'\n{3,}', '\n', dom)
    return dom


def rewrite_links(dom):
    page = 'https://ailen4403.wixstudio.com/tfacturo'
    def anchor(m):
        tag = m.group(0)
        a = re.search(r'data-anchor="(anchors-[a-z0-9]+)"', tag)
        target = '#' + ANCHORS[a.group(1)] if a and a.group(1) in ANCHORS else '#'
        return tag.replace('href="%s"' % page, 'href="%s"' % target)
    dom = re.sub(r'<a\b[^>]*href="%s"[^>]*>' % re.escape(page), anchor, dom)
    pdf = re.search(r'https://[0-9a-f-]+\.filesusr\.com/ugd/(63393a_[0-9a-f]+\.pdf)', dom)
    if pdf:
        shutil.copy(fetch(pdf.group(0), CACHE / 'docs' / pdf.group(1)), A / 'docs' / PDF_NAME)
        dom = dom.replace(pdf.group(0), 'assets/docs/' + PDF_NAME)
    dom = dom.replace('href="https://web.whatsapp.com/"', 'href="%s"' % WHATSAPP_URL)
    return dom


def head():
    return '''<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{t}</title>
<meta name="description" content="{d}">
<link rel="canonical" href="{u}">
<meta property="og:type" content="website">
<meta property="og:locale" content="es_AR">
<meta property="og:title" content="{t}">
<meta property="og:description" content="{d}">
<meta property="og:url" content="{u}">
<meta property="og:image" content="{u}assets/img/og-image.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#FF5B04">
<link rel="icon" href="assets/favicon/favicon.svg" type="image/svg+xml">
<link rel="icon" href="assets/favicon/favicon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="assets/favicon/apple-touch-icon.png">
<link rel="stylesheet" href="assets/css/site.css">
<noscript><style>[id^="comp-"]{{animation:none!important}}</style></noscript>
<script type="application/ld+json">{ld}</script>
'''.format(t=html.escape(TITLE), d=html.escape(DESCRIPTION), u=SITE_URL, ld=json.dumps({
        '@context': 'https://schema.org', '@type': 'Organization', 'name': 'TeFacturo', 'url': SITE_URL,
        'logo': SITE_URL + 'assets/favicon/icon-512.png', 'email': 'contacto@tefacturo.com.ar',
        'telephone': '+54 9 2926 508200',
        'address': {'@type': 'PostalAddress', 'streetAddress': 'Mitre 1058', 'addressLocality': 'Coronel Suárez',
                    'addressRegion': 'Buenos Aires', 'addressCountry': 'AR'}}, ensure_ascii=False))


def runtime_config():
    t = json.loads((SRC / 'wix-features.json').read_text())['props']['triggersAndReactions']
    return {'triggers': t['compsToTriggers'], 'viewport': t['viewportTriggerCompsToParams'],
            'repeaters': t['repeaterDescendantToRepeaterMapper'], 'anchors': ANCHORS}


def main():
    for d in ['css', 'js', 'img', 'video', 'fonts', 'docs', 'favicon']:
        (A / d).mkdir(parents=True, exist_ok=True)
    dom = (SRC / 'wix-dom.html').read_text(encoding='utf-8')
    build_css(dom)
    dom = clean(dom)
    dom = Images().rewrite(dom)
    dom = rewrite_videos(dom)
    dom = rewrite_links(dom)
    dom = re.sub(r'<html[^>]*>', '<html lang="es-AR">', dom, count=1)
    dom = re.sub(r'<head>', '<head>\n' + head(), dom, count=1)
    cfg = '<script>window.TF_CONFIG=%s</script>\n<script src="assets/js/site.js" defer></script>\n' % json.dumps(runtime_config(), separators=(',', ':'))
    dom = dom.replace('</body>', cfg + '</body>')
    (OUT / 'index.html').write_text('<!DOCTYPE html>\n' + re.sub(r'^\s*<!DOCTYPE html>\s*', '', dom, flags=re.I), encoding='utf-8')
    shutil.copy(ROOT / 'src' / 'site.js', A / 'js' / 'site.js')
    for f in (ROOT / 'brand' / 'favicon').iterdir():
        shutil.copy(f, A / 'favicon' / f.name)
    (OUT / '.nojekyll').write_text('')
    (OUT / 'robots.txt').write_text('User-agent: *\nAllow: /\n\nSitemap: %ssitemap.xml\n' % SITE_URL)
    (OUT / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                     '  <url><loc>%s</loc></url>\n</urlset>\n' % SITE_URL)
    og = ROOT / 'brand' / 'og-image.png'
    if og.exists():
        shutil.copy(og, A / 'img' / 'og-image.png')
    # Limpieza: assets generados que ya no referencia el HTML
    used = set(re.findall(r'assets/(?:img|video)/([^\s"\',)]+)', (OUT / 'index.html').read_text(encoding='utf-8')))
    for d in ['img', 'video']:
        for f in (A / d).iterdir():
            if f.name not in used and f.name != 'og-image.png':
                f.unlink()
    print('index.html', (OUT / 'index.html').stat().st_size // 1024, 'KB')


if __name__ == '__main__':
    main()
