"""Landing de performance (destino de anuncios): src/landing/empezar.html -> docs/empezar/index.html.

Página propia (no Wix), autocontenida: CSS y JS inline, una sola fuente, sin librerías. Una conversión:
abrir WhatsApp. `noindex` y fuera del sitemap. Copy y fuentes de cada dato: src/landing/COPY.md.

Corre sola (`python3 tools/landing.py`) o desde build_site.py.
"""
import glob, html, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'src' / 'landing' / 'empezar.html'
SLUG = 'empezar'

# Medición: completar con los IDs del cliente. Vacíos = no se carga ningún script de terceros.
META_PIXEL_ID = ''
GTAG_ID = ''          # GA4 (G-...) o Google Ads (AW-...)
# Agrega "(ref: <utm_campaign>)" al mensaje de WhatsApp para atribuir conversaciones (pendiente 4 de COPY.md)
WA_REF = True

PHOTO_ID = '974e21'   # comerciante emitiendo en un equipo POS (home de Wix)
PHOTO_ALT = 'Comerciante emitiendo una factura en un equipo POS TeFacturo'


def photo(out_dir):
    files = []
    for f in glob.glob(str(Path(out_dir) / 'assets' / 'img' / ('*-%s-*l.webp' % PHOTO_ID))):
        m = re.search(r'-(\d+)l\.webp$', f)
        files.append((int(m.group(1)), Path(f).name))
    if not files:
        return ''
    files.sort()
    srcset = ', '.join('../assets/img/%s %dw' % (n, w) for w, n in files)
    mid = next((n for w, n in files if w >= 800), files[-1][1])
    return ('<img src="../assets/img/%s" srcset="%s" sizes="(min-width: 1000px) 560px, calc(100vw - 32px)" '
            'width="1200" height="800" alt="%s" loading="lazy" decoding="async">' % (mid, srcset, html.escape(PHOTO_ALT)))


def tracking():
    head, body = [], []
    if META_PIXEL_ID:
        head.append("<script>!function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?n.callMethod.apply(n,arguments)"
                    ":n.queue.push(arguments)};if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);"
                    "t.async=!0;t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}(window,document,'script',"
                    "'https://connect.facebook.net/en_US/fbevents.js');fbq('init','%s');fbq('track','PageView');</script>" % META_PIXEL_ID)
    if GTAG_ID:
        head.append('<script async src="https://www.googletagmanager.com/gtag/js?id=%s"></script>'
                    "<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments)}"
                    "gtag('js',new Date());gtag('config','%s');</script>" % (GTAG_ID, GTAG_ID))
    return '\n'.join(head), '\n'.join(body)


def build(out_dir, cfg):
    out_dir = Path(out_dir)
    url = cfg['site'] + SLUG + '/'
    head, body = tracking()
    vals = {'URL': url, 'SITE': cfg['site'], 'WA': cfg['whatsapp'], 'WA_BASE': cfg['whatsapp'],
            'WA_REF': json.dumps(WA_REF), 'PHOTO': photo(out_dir), 'TRACKING_HEAD': head, 'TRACKING_BODY': body,
            'YEARS': cfg['years'], 'ACTIVE': cfg['active']}
    out = SRC.read_text(encoding='utf-8')
    for k, v in vals.items():
        out = out.replace('{{%s}}' % k, v)
    assert '{{' not in out, re.findall(r'\{\{\w+\}\}', out)
    (out_dir / SLUG).mkdir(parents=True, exist_ok=True)
    (out_dir / SLUG / 'index.html').write_text(out, encoding='utf-8')
    print('  landing: /%s/ (%d KB)' % (SLUG, len(out.encode()) // 1024))


if __name__ == '__main__':
    import sys
    sys.path.insert(0, str(ROOT / 'tools'))
    from build_site import OUT, site_cfg
    build(OUT, site_cfg())
