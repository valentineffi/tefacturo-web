#!/usr/bin/env python3
"""Genera docs/ (sitio estático para GitHub Pages) a partir de la captura de Wix en source/.

Entrada:  source/wix-dom.html, wix-css.json, wix-features.json, wix-media-sizes.json  (tools/capture_wix.mjs)
          src/site.js (runtime propio que reemplaza al JS de Wix)
Salida:   docs/index.html + docs/assets/{css,js,img,video,fonts,docs}
Caché:    .cache/ (originales bajados de Wix; no se versiona)
"""
import datetime, hashlib, html, json, os, re, shutil, subprocess, sys, unicodedata, urllib.request
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pages  # noqa: E402  (páginas de contenido propias: src/pages/)
import landing  # noqa: E402  (landing de performance: src/landing/)

Image.MAX_IMAGE_PIXELS = None
ROOT = Path(__file__).resolve().parent.parent
SRC, OUT, CACHE = ROOT / 'source', ROOT / 'docs', ROOT / '.cache'
A = OUT / 'assets'

SITE_URL = 'https://valentineffi.github.io/tefacturo-web/'   # se ajusta al pasar a tefacturo.com.ar
TITLE = 'TeFacturo | Sistema de facturación electrónica simple'
DESCRIPTION = ('Sistema de facturación electrónica simple para pequeños y medianos comercios de Argentina: '
               'software fácil de usar y equipo POS para facturar con ARCA en segundos.')

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
    'f172e0': 'Facturación electrónica', '7e6ec9': 'Gestión de productos', '9af791': 'Reportes',
    '51305e': 'Impresión térmica y PDF',
    '2b000d': 'WhatsApp', 'd9ad68': 'Instagram', 'e99f41': 'Facebook',
}

# Dorso de las tarjetas de "Funcionalidades" (id de la imagen de Wix -> título, texto). En Wix era una imagen con
# el texto escrito; acá es texto (aprobado por el usuario, 2026-10-19: así se corrige sin rehacer imágenes y lo leen
# los buscadores), con el fondo, la tipografía y las medidas de la imagen original de 746 px (FEATURE_CSS).
FEATURE_CARDS = {
    '9a64fe': ('Facturación electrónica ARCA (ex AFIP)', 'Emití Facturas A, B y C con CAE automático y notas de crédito.'),
    'eba5b1': ('Gestión de productos', 'Alta masiva por CSV/Excel. Variantes, categorías jerárquicas y departamentos con impuestos internos.'),
    '4da3fa': ('Reportes', 'KPIs de ventas, gráficos de tendencias, filtros por fecha, punto de venta, vendedor y cliente.'),
    'ef238a': ('Impresión térmica y PDF', 'Tickets de venta, notas de crédito, etiquetas de góndola. Detección automática de impresoras en red.'),
}
# Medidas en cqw del ancho de la tarjeta: 746 px -> letra de 51,1 px, interlineado de 64 px, texto desde (66, 96) px
FEATURE_CSS = '''
.tf-feat{container-type:inline-size;width:100%;aspect-ratio:1;background:#041212}
.tf-feat-in{box-sizing:border-box;height:100%;padding:12.87cqw 8.85cqw 0;color:#fff;font-family:inter,sans-serif;font-size:6.85cqw;line-height:1.25}
.tf-feat-in h3,.tf-feat-in p{margin:0;font:inherit;color:inherit;letter-spacing:normal}
.tf-feat-in h3{font-weight:600}
.tf-feat-in p{font-weight:300}
.tf-login{position:absolute;z-index:3;top:50%;right:230px;transform:translateY(-50%);display:inline-flex;align-items:center;box-sizing:border-box;
  height:46px;padding:0 1.5em;border:1px solid #010A0A;border-radius:999px;background:transparent;color:#010A0A;font:600 14px/1 inter,sans-serif;
  text-decoration:none;white-space:nowrap;visibility:hidden;transition:background-color .2s,color .2s}
.tf-login.is-placed{visibility:visible}
.tf-login svg{width:1.25em;height:1.25em;margin-right:.5em;flex:none}
.tf-login.is-text{height:auto;padding:0;border:0;border-radius:0;right:auto}
.tf-login.is-text svg{width:1em;height:1em;margin-right:.4em}
.tf-login.is-text:hover{background:transparent;color:#FF5B04!important}
.tf-login.is-compact{width:var(--tf-login-h,46px);padding:0;justify-content:center}
.tf-login.is-compact svg{margin:0}
.tf-login.is-compact span{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}
.tf-login:hover{background:#010A0A;color:#fff}
.tf-login:focus-visible{outline:2px solid #FF5B04;outline-offset:2px}
/* Planes y Descargas: filas 9 y 10 de la grilla de secciones; preguntas frecuentes y contacto bajan dos */
#planes{grid-area:9/1/10/2}
#descargas{grid-area:10/1/11/2}
#comp-mo3g1cca{grid-area:11/1/12/2}
#comp-lxu94j0k{grid-area:12/1/13/2}
.tf-plans{background:#F6F6F6;color:#010A0A;font-family:inter,sans-serif;padding:72px 7.5vw 88px}
.tf-plans h2{margin:0;color:#075056;font-weight:600;font-size:clamp(32px,3.7vw,52px);line-height:1.05;letter-spacing:-.01em}
.tf-plans-lead{margin:16px 0 0;max-width:34em;font-size:clamp(15px,1.25vw,18px);line-height:1.5;color:#3A4545}
.tf-period{display:inline-flex;gap:4px;margin-top:28px;padding:4px;border-radius:999px;background:#E6EBEB}
.tf-period[hidden]{display:none}
.tf-period button{border:0;border-radius:999px;padding:10px 18px;background:transparent;color:#010A0A;font:500 14px/1 inter,sans-serif;cursor:pointer}
.tf-period button[aria-checked="true"]{background:#fff;box-shadow:0 1px 3px rgba(1,10,10,.12)}
.tf-period button:focus-visible{outline:2px solid #FF5B04;outline-offset:2px}
.tf-save{color:#FF5B04;font-weight:600}
.tf-plans-grid{display:grid;gap:20px;margin-top:28px;grid-template-columns:1fr}
@media (min-width:750px){.tf-plans-grid{grid-template-columns:repeat(auto-fit,minmax(260px,1fr))}}
.tf-plans-msg{margin:0;font-size:16px;color:#3A4545}
.tf-plans-msg a{color:#075056;font-weight:600;text-decoration:underline}
.tf-plan{display:flex;flex-direction:column;background:#fff;border-radius:24px;padding:28px 26px 26px;box-shadow:0 1px 2px rgba(1,10,10,.06)}
.tf-plan h3{margin:0;font-weight:600;font-size:22px}
.tf-plan-desc{margin:6px 0 0;font-size:14px;line-height:1.45;color:#5B6666}
.tf-price{margin:22px 0 0;display:flex;align-items:baseline;gap:6px}
.tf-price b{font-weight:600;font-size:40px;letter-spacing:-.02em;font-variant-numeric:tabular-nums}
.tf-price span{font-size:15px;color:#5B6666}
.tf-price-note{margin:4px 0 0;min-height:1.4em;font-size:13px;color:#5B6666}
.tf-limits{list-style:none;margin:20px 0 0;padding:14px 0 0;border-top:1px solid #E6EBEB}
.tf-limits li{display:flex;justify-content:space-between;gap:12px;padding:5px 0;font-size:14px}
.tf-limits b{font-weight:600;font-variant-numeric:tabular-nums;text-align:right}
.tf-feat-t{margin:18px 0 0;font-weight:600;font-size:14px}
.tf-feats{list-style:none;margin:8px 0 0;padding:0}
.tf-feats li{position:relative;padding:4px 0 4px 22px;font-size:14px;line-height:1.4;color:#2A3333}
.tf-feats li::before{content:"";position:absolute;left:2px;top:.62em;width:10px;height:6px;border-left:2px solid #FF5B04;border-bottom:2px solid #FF5B04;transform:rotate(-45deg)}
.tf-more summary{margin-top:6px;cursor:pointer;font-size:14px;font-weight:500;color:#075056}
.tf-plan-cta{display:flex;align-items:center;justify-content:center;height:48px;border-radius:999px;
  background:linear-gradient(90deg,#FF5B04 0%,#E3520A 45%,#8A3608 100%);color:#fff;font:600 15px/1 inter,sans-serif;text-decoration:none}
.tf-plan-cta-wrap{margin-top:auto;padding-top:24px}
.tf-plan-cta:focus-visible{outline:2px solid #010A0A;outline-offset:2px}
@media (max-width:749px){.tf-plans{padding:56px 20px 64px}}
.tf-downloads{background:#fff;padding-top:72px}
.tf-dl-grid{display:grid;gap:16px;margin-top:28px;grid-template-columns:1fr}
@media (min-width:750px){.tf-dl-grid{grid-template-columns:repeat(2,1fr)}}
@media (min-width:1100px){.tf-dl-grid{grid-template-columns:repeat(4,1fr)}}
.tf-dl{display:flex;flex-direction:column;border:1px solid #E6EBEB;border-radius:20px;padding:24px 22px 22px;background:#F6F6F6}
.tf-dl-icon{width:40px;height:40px;color:#075056}
.tf-dl h3{margin:14px 0 0;font-weight:600;font-size:20px}
.tf-dl-meta{margin:4px 0 0;min-height:1.4em;font-size:13px;color:#5B6666;font-variant-numeric:tabular-nums}
.tf-dl-hint{margin:12px 0 0;font-size:14px;line-height:1.45;color:#2A3333}
.tf-dl-actions{margin-top:auto;padding-top:20px}
.tf-dl-btn{display:flex;align-items:center;justify-content:center;gap:8px;height:46px;border-radius:999px;background:#010A0A;color:#fff;
  font:600 15px/1 inter,sans-serif;text-decoration:none}
.tf-dl-btn svg{width:18px;height:18px}
.tf-dl-btn.is-web{background:transparent;color:#010A0A;border:1px solid #010A0A}
.tf-dl-btn[aria-disabled="true"]{background:#E6EBEB;color:#5B6666;pointer-events:none}
.tf-dl-btn:focus-visible{outline:2px solid #FF5B04;outline-offset:2px}
.tf-dl-alt{margin:8px 0 0;font-size:13px;color:#5B6666}
.tf-dl-alt a{color:#075056;text-decoration:underline}
'''

# Desvíos deliberados respecto del Wix (ver CLAUDE.md > "Diferencias con Wix")
WHATSAPP_URL = 'https://wa.me/5492926508200'
# El sistema (front web de producción) y la API de la que la sección de planes lee los precios
APP_URL = 'https://web.tefacturo.ar/'
PLANS_API_URL = 'https://api.tefacturo.ar/api/public/plans'
# Sección "Descargas": la última versión de cada plataforma sale del canal de actualización (público)
RELEASES_API_URL = 'https://api.tefacturo.ar/api/app-releases/latest'
DOWNLOADS = [
    {'platform': 'android', 'arch': 'arm64-v8a', 'name': 'Android', 'icon': 'phone',
     'hint': 'Para celulares, tablets y equipos POS. Android te va a pedir permiso para instalar apps de este origen.',
     'alt': [{'arch': 'armeabi-v7a', 'label': 'Equipos de 32 bits'}]},
    {'platform': 'windows', 'arch': 'x64', 'name': 'Windows', 'icon': 'desktop',
     'hint': 'Para la computadora del mostrador o de la oficina.'},
    {'platform': 'linux', 'arch': 'x86_64', 'name': 'Linux', 'icon': 'desktop',
     'hint': 'AppImage: dale permiso de ejecución y abrila, sin instalar nada.'},
]
# Sección "Planes" (propia, no está en Wix): los precios se leen de PLANS_API_URL al cargar la página.
# Funciones que no se anuncian aunque un plan las incluya (decisión del usuario, 2026-10-19: Mercado Pago
# hasta validarlo con un comercio real) y los topes que se muestran en cada tarjeta, en orden.
PLANS_HIDDEN_CAPABILITIES = ['cap.mercadopago.collections.enabled']
PLANS_KEY_LIMITS = ['limit.users.max', 'limit.sales_points.max', 'meter.afip.invoices.authorized.count.month', 'limit.products.max']
LOGIN_ICON = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" '
              'aria-hidden="true"><path d="M15 3h3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-3"/><path d="M10 17l5-5-5-5"/><path d="M15 12H4"/></svg>')
PDF_NAME = 'Funcionalidades-Principales-TeFacturo.pdf'

# Cifras de "Nuestra trayectoria", que repiten las páginas de contenido y la landing de anuncios
SINCE_YEAR = 2018        # los años de experiencia se cuentan desde acá; el runtime los lleva al año en curso
ACTIVE_COMMERCES = 140   # «140+»: 141 comercios activos al 2026-10-19

# Correcciones de texto aprobadas por el cliente (typos y un dato erróneo del Wix)
TEXT_FIXES = [
    ('Sí, uestro sistema', 'Sí, nuestro sistema'),
    ('ARCA (Administración Federal de Ingresos Públicos)', 'ARCA (Agencia de Recaudación y Control Aduanero, ex AFIP)'),
    ('>Sí! TeFacturo', '>¡Sí! TeFacturo'),
    ('Solo necesitas completar un formulario con tus datos fiscales, Nosotros',
     'Solo necesitás completar un formulario con tus datos fiscales, nosotros'),
    ('Por qué elegrinos', 'Por qué elegirnos'),
]


def years_since():
    return datetime.date.today().year - SINCE_YEAR


def site_cfg():
    """Config que reciben pages.py y landing.py. `years` lleva data-tf-since para que el runtime lo actualice."""
    return {'site': SITE_URL, 'whatsapp': WHATSAPP_URL, 'active': str(ACTIVE_COMMERCES),
            'years': '<span data-tf-since="%d">%d</span>' % (SINCE_YEAR, years_since())}


# Cambios de contenido de "Nuestra trayectoria" aprobados por el usuario (2026-10-19): años contados desde
# SINCE_YEAR, comercios activos reales, y «3 Plataformas» y «Validado por ARCA» en lugar de «80 % Mayor eficiencia»
# y «100 % Clientes satisfechos» (ninguno de los dos estaba medido)
_NUM = '<span style="color:rgb(1, 10, 10);" class="wixui-rich-text__text"%s>%s</span>+'
# Preguntas frecuentes coherentes con lo que el sistema ofrece hoy (aprobado por el usuario, 2026-10-19): sin notas
# de débito ni facturación de servicios (no están implementadas), sin Google Play (todavía no está publicada) y los
# usuarios adicionales tienen costo
FAQ_FIXES = [
    ('Descargá la app desde Google Play en tu celular o tablet.', 'Instalá la app en tu celular o tablet.'),
    ('(Facturas A, B, C, Notas de Crédito/Débito, etc.)', '(Facturas A, B y C y notas de crédito)'),
    ('un kiosco, ferretería, tienda online o servicio profesional,', 'un kiosco, almacén, ferretería o tienda,'),
    ('Sin costos por factura emitida, sin cargos por usuario adicional en el plan básico, y sin sorpresas. '
     'Si necesitás funcionalidades avanzadas, te lo avisamos antes.',
     'Sin costos por factura emitida y sin sorpresas. Si necesitás más usuarios o funcionalidades avanzadas, '
     'tienen un costo adicional que te informamos antes de sumarlos.'),
]

TRAJECTORY = [
    ('<span class="wixui-rich-text__text">80<span class="color_12 wixui-rich-text__text">%</span></span>',
     '<span class="wixui-rich-text__text">3</span>'),
    ('<span class="wixui-rich-text__text">Mayor eficiencia</span>', '<span class="wixui-rich-text__text">Plataformas</span>'),
    ('Reducí el tiempo de facturación y olvidate de los sistemas lentos o caídos.',
     'Android, computadora y web: facturá desde el mostrador, la oficina o el celular.'),
    (_NUM % ('', '8'), _NUM % (' data-tf-since="%d"' % SINCE_YEAR, years_since())),
    (_NUM % ('', '60'), _NUM % ('', ACTIVE_COMMERCES)),
    ('<span class="wixui-rich-text__text">Clientes satisfechos</span>', '<span class="wixui-rich-text__text">Validado por ARCA</span>'),
    ('Comercios de todos los rubros ya confían en nuestro servicio</p>\n\n<p class="font_8 wixui-rich-text__text">y soporte.</p>',
     'Cada comprobante sale con su CAE de ARCA, conectado directo al web service oficial.</p>'),
]


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
    css += FEATURE_CSS
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
        # Todos están debajo del primer pantallazo: no se bajan hasta que el runtime los ve (data-autoplay)
        tag = tag.replace(' preload="auto"', ' preload="none"').replace(' autoplay=""', ' data-autoplay=""')
        return tag.replace(' crossorigin="anonymous"', '')
    dom = re.sub(r'<video\b[^>]*src="https://video\.wixstatic\.com/video/(63393a_[0-9a-f]{32})/[^"]*"[^>]*>', fix, dom)
    # Póster de fondo que Wix pone detrás de cada video (opacity 0, pero se bajaba de wixstatic con prioridad alta)
    def poster_img(m):
        tag = re.sub(r'\ssrc="[^"]*"', ' src="assets/video/%s.webp"' % m.group(1)[7:19], m.group(0))
        return re.sub(r'\sfetchpriority="[^"]*"', '', tag)[:-1] + ' loading="lazy" decoding="async">'
    return re.sub(r'<img src="https://static\.wixstatic\.com/media/(63393a_[0-9a-f]{32})f000\.jpg[^"]*"[^>]*>', poster_img, dom)


# ---------------------------------------------------------------- Semántica (sin cambios visuales)
H1_TEXT = 'TeFacturo: facturación electrónica ágil, simple y sin vueltas'
# Textos que en Wix son <h2>/<h6> pero no son títulos (datos de contacto, subtítulos, menú) -> <p> con la misma clase
NOT_HEADINGS = ['Por qué elegirnos', 'Sobre Nosotros', 'Modo de Uso', 'Funciones', 'Contacto',
                'Si tenés alguna duda', 'Mitre 1058', 'Dirección', '+54 9 2926', 'Teléfono', 'Mail',
                'contacto@tefacturo', 'ariel.tallerpd', 'Diseñadas para cubrir']


def semantics(dom):
    def demote(m):
        text = html.unescape(re.sub(r'<[^>]+>', '', m.group(3))).strip()
        if not any(text.startswith(t) for t in NOT_HEADINGS):
            return m.group(0)
        return '<p%s>%s</p>' % (m.group(2), m.group(3))
    dom, n = re.subn(r'<(h[26])(\b[^>]*)>(.*?)</\1>', demote, dom, flags=re.S)
    # La portada es una imagen-título: un <h1> solo para lectores de pantalla y buscadores
    h1 = '<h1 style="position:absolute;width:1px;height:1px;margin:-1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap">%s</h1>' % html.escape(H1_TEXT)
    dom = re.sub(r'(<main\b[^>]*>)', r'\1' + h1, dom, count=1)
    # Imágenes de la portada (LCP): prioridad alta
    first = re.compile(r'<section id="(comp-[^"]+)".*?</section>', re.S).search(dom, dom.find('<main'))
    if first:
        sec = re.sub(r'<img\b(?![^>]*fetchpriority)', '<img fetchpriority="high"', first.group(0))
        dom = dom[:first.start()] + sec + dom[first.end():]
    print('  semantics: %d headings revisados, h1 + LCP en %s' % (n, first and first.group(1)))
    return dom


def feature_cards(dom):
    """Cambia la imagen del dorso de cada tarjeta de FEATURE_CARDS por su texto (antes de procesar las imágenes,
    así la imagen vieja ni se baja)."""
    for media_id, (title, body) in FEATURE_CARDS.items():
        pat = r'<wow-image\b(?:(?!</wow-image>).)*?63393a_%s(?:(?!</wow-image>).)*?</wow-image>' % media_id
        card = '<div class="tf-feat"><div class="tf-feat-in"><h3>%s</h3><p>%s</p></div></div>' % (html.escape(title), html.escape(body))
        dom, n = re.subn(pat, lambda m: card, dom, count=1, flags=re.S)
        if not n:
            print('  OJO: no encontré la tarjeta de funcionalidades', media_id)
    return dom


# ---------------------------------------------------------------- Limpieza del DOM
def plans_section():
    """Planes con sus precios. El HTML trae el título y el aviso de carga; site.js arma las tarjetas con
    PLANS_API_URL. Sin JS o si la API no contesta, queda el link a WhatsApp."""
    return '''<section id="planes" class="tf-plans" aria-labelledby="planes-t">
<h2 id="planes-t">Planes</h2>
<p class="tf-plans-lead">Elegí el plan para tu comercio. Sin costo por factura y sin permanencia.</p>
<div class="tf-period" role="radiogroup" aria-label="Forma de pago" hidden>
<button type="button" role="radio" aria-checked="true" data-period="monthly">Mensual</button>
<button type="button" role="radio" aria-checked="false" data-period="annual">Anual <span class="tf-save"></span></button>
</div>
<div class="tf-plans-grid" aria-live="polite"><p class="tf-plans-msg">Cargando planes…</p></div>
<noscript><p class="tf-plans-msg">Consultanos los planes por <a href="%s" rel="noopener">WhatsApp</a>.</p></noscript>
</section>''' % WHATSAPP_URL


DL_ICONS = {
    'phone': '<rect x="7" y="2.5" width="10" height="19" rx="2"/><path d="M11 18.5h2"/>',
    'desktop': '<rect x="3" y="4" width="18" height="12" rx="1.5"/><path d="M9 20h6M12 16v4"/>',
    'web': '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 2.6 3.8 5.6 3.8 9s-1.3 6.4-3.8 9c-2.5-2.6-3.8-5.6-3.8-9S9.5 5.6 12 3z"/>',
}


def dl_icon(name):
    return ('<svg class="tf-dl-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" '
            'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">%s</svg>' % DL_ICONS[name])


def downloads_section():
    """Descargas. Una tarjeta por plataforma de DOWNLOADS más la web; site.js completa versión, tamaño y link
    con RELEASES_API_URL. Sin JS (o si la plataforma no tiene versión publicada) el botón queda deshabilitado."""
    cards = ''.join('''<article class="tf-dl" data-platform="%s" data-arch="%s">%s<h3>%s</h3><p class="tf-dl-meta"></p>
<p class="tf-dl-hint">%s</p><div class="tf-dl-actions"><a class="tf-dl-btn" aria-disabled="true">Próximamente</a></div></article>'''
                    % (d['platform'], d['arch'], dl_icon(d['icon']), html.escape(d['name']), html.escape(d['hint'])) for d in DOWNLOADS)
    web = '''<article class="tf-dl">%s<h3>Web</h3><p class="tf-dl-meta">Siempre la última versión</p>
<p class="tf-dl-hint">Desde el navegador de cualquier computadora, sin instalar nada.</p>
<div class="tf-dl-actions"><a class="tf-dl-btn is-web" href="%s">Abrir TeFacturo web</a></div></article>''' % (dl_icon('web'), APP_URL)
    return '''<section id="descargas" class="tf-plans tf-downloads" aria-labelledby="descargas-t">
<h2 id="descargas-t">Descargá TeFacturo</h2>
<p class="tf-plans-lead">Instalala en tu celular, tablet, equipo POS o computadora, o usala desde el navegador.</p>
<div class="tf-dl-grid">%s%s</div>
</section>''' % (cards, web)


def insert_after_element(dom, start_pat, html_block):
    """Inserta html_block justo después del elemento que abre en start_pat (mismo balanceo que remove_element)."""
    m = re.search(start_pat, dom)
    assert m, 'no encontré ' + start_pat
    tag = re.match(r'<(\w[\w-]*)', m.group(0)).group(1)
    depth = 0
    for t in re.finditer(r'<(/?)%s\b[^>]*?(/?)>' % tag, dom[m.start():]):
        if t.group(2):
            continue
        depth += -1 if t.group(1) else 1
        if depth == 0:
            end = m.start() + t.end()
            return dom[:end] + html_block + dom[end:]
    raise AssertionError('no encontré el cierre de ' + start_pat)


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
        # El PDF ya no es el de Wix: lo genera tools/build_pdf.mjs desde src/pdf/ (contenido corregido, 2026-10-19)
        shutil.copy(ROOT / 'src' / 'pdf' / PDF_NAME, A / 'docs' / PDF_NAME)
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
<meta property="og:site_name" content="TeFacturo">
<meta property="og:image" content="{u}assets/img/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="TeFacturo, sistema de facturación electrónica">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{t}">
<meta name="twitter:description" content="{d}">
<meta name="theme-color" content="#FF5B04">
<link rel="icon" href="assets/favicon/favicon.svg" type="image/svg+xml">
<link rel="icon" href="assets/favicon/favicon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="assets/favicon/apple-touch-icon.png">
<link rel="stylesheet" href="assets/css/site.css">
<noscript><style>[id^="comp-"]{{animation:none!important}}</style></noscript>
<script type="application/ld+json">{ld}</script>
'''.format(t=html.escape(TITLE), d=html.escape(DESCRIPTION), u=SITE_URL, ld=json.dumps(schema(), ensure_ascii=False))


def schema():
    org = SITE_URL + '#organization'
    return {'@context': 'https://schema.org', '@graph': [
        {'@type': 'Organization', '@id': org, 'name': 'TeFacturo', 'url': SITE_URL,
         'logo': SITE_URL + 'assets/favicon/icon-512.png', 'image': SITE_URL + 'assets/img/og-image.png',
         'description': DESCRIPTION, 'email': 'contacto@tefacturo.com.ar', 'telephone': '+54 9 2926 508200',
         'address': {'@type': 'PostalAddress', 'streetAddress': 'Mitre 1058', 'addressLocality': 'Coronel Suárez',
                     'addressRegion': 'Buenos Aires', 'addressCountry': 'AR'},
         'areaServed': {'@type': 'Country', 'name': 'Argentina'},
         'contactPoint': {'@type': 'ContactPoint', 'contactType': 'customer support', 'telephone': '+54 9 2926 508200',
                          'email': 'contacto@tefacturo.com.ar', 'availableLanguage': 'es'}},
        {'@type': 'WebSite', '@id': SITE_URL + '#website', 'url': SITE_URL, 'name': 'TeFacturo',
         'inLanguage': 'es-AR', 'publisher': {'@id': org}},
        {'@type': 'SoftwareApplication', 'name': 'TeFacturo', 'url': SITE_URL,
         'applicationCategory': 'BusinessApplication', 'operatingSystem': 'Android, Windows, Linux',
         'description': DESCRIPTION, 'publisher': {'@id': org}, 'inLanguage': 'es-AR',
         'featureList': [
             'Facturación electrónica ARCA (ex AFIP): Facturas A, B y C con CAE automático',
             'Notas de crédito',
             'Gestión de productos con alta masiva por CSV/Excel, variantes y categorías',
             'Cuentas corrientes: ventas a cuenta, cobros parciales y deudores',
             'Presupuestos y remitos que pasan a venta sin volver a cargarlos',
             'Reportes de ventas con KPIs y filtros por fecha, punto de venta, vendedor y cliente',
             'Impresión térmica y PDF: tickets, notas de crédito y etiquetas de góndola',
             'Equipos POS, impresoras térmicas y tablets preconfigurados']},
    ]}


def llms_txt(extra=()):
    """Resumen en Markdown para buscadores con IA (llmstxt.org), armado solo con contenido que ya está en el sitio."""
    return '''# TeFacturo

> {d}

TeFacturo combina software fácil de usar con un equipo POS dedicado para que cualquier negocio pueda emitir
facturas de manera rápida y sin complicaciones: prender el equipo, facturar en segundos e imprimir el comprobante,
sin conocimientos técnicos. Reemplaza los sistemas complejos o el uso directo de ARCA (ex AFIP).

## Funcionalidades

- Facturación electrónica ARCA: Facturas A, B y C con CAE automático y notas de crédito.
- Gestión de productos: alta masiva por CSV/Excel, variantes, categorías jerárquicas y departamentos con impuestos internos.
- Cuentas corrientes: ventas a cuenta, cobros parciales, listado de deudores y estado de cuenta de cada cliente.
- Presupuestos: con el logo del comercio; al aceptarlo reserva el stock y pasa a venta o remito sin volver a cargarlo.
- Remitos: reservan el stock y se facturan después, completos o en partes.
- Reportes: KPIs de ventas, gráficos de tendencias, filtros por fecha, punto de venta, vendedor y cliente.
- Impresión térmica y PDF: tickets de venta, notas de crédito, etiquetas de góndola; detección automática de impresoras en red.
- Aplicación nativa para Android y PC (Windows y Linux).
- Equipos opcionales listos para usar: impresoras térmicas, terminales POS, tablets y kits completos, con el software ya instalado.

## Cómo empezar

1. Contanos sobre tu negocio: completás un formulario con tus datos fiscales.
2. Asesoramiento y configuración: te guiamos en ARCA, configuramos el sistema y hacemos la puesta en marcha.
3. Recibís tu sistema listo para facturar (acceso a tu cuenta o el dispositivo físico).
4. Emitís tu primera factura.

## Contacto

- Web: {u}
- WhatsApp: {w}
- Email: contacto@tefacturo.com.ar
- Dirección: Mitre 1058, Coronel Suárez, Buenos Aires, Argentina
- [Funcionalidades principales (PDF)]({u}assets/docs/{p})
'''.format(d=DESCRIPTION, u=SITE_URL, w=WHATSAPP_URL, p=PDF_NAME) + (
        '\n## Guías y páginas\n\n' + ''.join('- [%s](%s): %s\n' % (t, u, d) for u, _, t, d in extra) if extra else '')


def runtime_config():
    t = json.loads((SRC / 'wix-features.json').read_text())['props']['triggersAndReactions']
    return {'triggers': t['compsToTriggers'], 'viewport': t['viewportTriggerCompsToParams'],
            'repeaters': t['repeaterDescendantToRepeaterMapper'], 'anchors': ANCHORS,
            'downloads': {'api': RELEASES_API_URL, 'alt': {d['platform']: d.get('alt', []) for d in DOWNLOADS}},
            'plans': {'api': PLANS_API_URL, 'whatsapp': WHATSAPP_URL, 'hidden': PLANS_HIDDEN_CAPABILITIES,
                      'limits': PLANS_KEY_LIMITS}}


def main():
    for d in ['css', 'js', 'img', 'video', 'fonts', 'docs', 'favicon']:
        (A / d).mkdir(parents=True, exist_ok=True)
    dom = (SRC / 'wix-dom.html').read_text(encoding='utf-8')
    build_css(dom)
    dom = clean(dom)
    dom = feature_cards(dom)
    dom = Images().rewrite(dom)
    dom = rewrite_videos(dom)
    dom = rewrite_links(dom)
    dom = semantics(dom)
    # "Ingresar" al sistema: en Wix no existía. site.js lo ubica al lado del botón del encabezado.
    dom = insert_after_element(dom, r'<section id="comp-mpcom3xk"', plans_section() + downloads_section())
    dom = re.sub(r'(<header id="comp-kbgakxea"[^>]*>)', r'\1<a class="tf-login" href="%s" title="Ingresar al sistema">%s<span>Ingresar</span></a>' % (APP_URL, LOGIN_ICON), dom, count=1)
    for a, b in TEXT_FIXES + TRAJECTORY + FAQ_FIXES:
        if a not in dom:
            print('  OJO: no encontré el texto a corregir:', a)
        dom = dom.replace(a, b)
    dom = re.sub(r'<html[^>]*>', '<html lang="es-AR">', dom, count=1)
    dom = re.sub(r'<head>', '<head>\n' + head(), dom, count=1)
    cfg = '<script>window.TF_CONFIG=%s</script>\n<script src="assets/js/site.js" defer></script>\n' % json.dumps(runtime_config(), separators=(',', ':'))
    dom = dom.replace('</body>', pages.home_footer() + cfg + '</body>')
    (OUT / 'index.html').write_text('<!DOCTYPE html>\n' + re.sub(r'^\s*<!DOCTYPE html>\s*', '', dom, flags=re.I), encoding='utf-8')
    shutil.copy(ROOT / 'src' / 'site.js', A / 'js' / 'site.js')
    for f in (ROOT / 'brand' / 'favicon').iterdir():
        shutil.copy(f, A / 'favicon' / f.name)
    (OUT / '.nojekyll').write_text('')
    (OUT / 'robots.txt').write_text('User-agent: *\nAllow: /\n\nSitemap: %ssitemap.xml\n' % SITE_URL)
    extra = pages.build(OUT, site_cfg())
    landing.build(OUT, site_cfg())  # noindex, fuera del sitemap
    urls = [(SITE_URL, datetime.date.today().isoformat())] + [(u, d) for u, d, _, _ in extra]
    (OUT / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                     + ''.join('  <url><loc>%s</loc><lastmod>%s</lastmod></url>\n' % u for u in urls)
                                     + '</urlset>\n')
    (OUT / 'llms.txt').write_text(llms_txt(extra), encoding='utf-8')
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
