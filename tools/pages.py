"""Páginas de contenido (SEO) escritas a mano: src/pages/*.html -> docs/<slug>/index.html.

A diferencia de la home (réplica de Wix), estas páginas son propias: template + CSS en src/pages/,
con la marca de TeFacturo. Cada archivo de contenido empieza con un comentario JSON:

    <!--page {"title": ..., "description": ..., "h1": ..., "kicker": ..., "type": "guide"|"service",
              "lead": ..., "related": [slugs], "updated": "AAAA-MM-DD"} -->

`type: guide` publica schema Article; `service`, WebPage. También genera /recursos/ (índice) y 404.html.
"""
import html, json, re, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = ROOT / 'src' / 'pages'


def load():
    out = []
    for f in sorted(PAGES.glob('*.html')):
        if f.name.startswith('_'):
            continue
        raw = f.read_text(encoding='utf-8')
        m = re.match(r'\s*<!--page\s+(\{.*?\})\s*-->\s*', raw, re.S)
        meta = json.loads(m.group(1))
        meta['slug'], meta['body'] = f.stem, raw[m.end():]
        out.append(meta)
    return sorted(out, key=lambda p: p.get('order', 99))


def schema(p, cfg, url):
    org = cfg['site'] + '#organization'
    crumbs = [('Inicio', cfg['site']), ('Recursos', cfg['site'] + 'recursos/')]
    if p['slug'] != 'recursos':
        crumbs.append((p['h1'], url))
    graph = [{'@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': u} for i, (n, u) in enumerate(crumbs)]}]
    page = {'@type': 'Article' if p.get('type') == 'guide' else 'WebPage', '@id': url + '#main', 'url': url,
            'name': p['title'], 'headline': p['h1'], 'description': p['description'], 'inLanguage': 'es-AR',
            'isPartOf': {'@id': cfg['site'] + '#website'}, 'publisher': {'@id': org},
            'image': cfg['site'] + 'assets/img/og-image.png'}
    if p.get('type') == 'guide':
        page.update({'author': {'@id': org}, 'datePublished': p['updated'], 'dateModified': p['updated']})
    graph.append(page)
    return json.dumps({'@context': 'https://schema.org', '@graph': graph}, ensure_ascii=False)


def card(p, pre):
    return ('<a class="card" href="%s%s/"><span class="card-kicker">%s</span><span class="card-title">%s</span>'
            '<span class="card-text">%s</span></a>' % (pre, p['slug'], html.escape(p['kicker']), html.escape(p['h1']),
                                                       html.escape(p['description'])))


def render(p, all_pages, cfg, tpl, pre='../'):
    url = cfg['site'] + (p['slug'] + '/' if p['slug'] else '')
    by_slug = {q['slug']: q for q in all_pages}
    related = [by_slug[s] for s in p.get('related', []) if s in by_slug]
    rel_html = ('<section class="related wrap" aria-labelledby="rel-t"><h2 id="rel-t">Seguí leyendo</h2>'
                '<div class="cards">%s</div></section>' % ''.join(card(q, pre) for q in related)) if related else ''
    footer_links = ''.join('<li><a href="%s%s/">%s</a></li>' % (pre, q['slug'], html.escape(q['h1'])) for q in all_pages)
    body = (p['body'].replace('{{WHATSAPP}}', cfg['whatsapp']).replace('{{PRE}}', pre)
            .replace('{{YEARS}}', cfg['years']).replace('{{ACTIVE}}', cfg['active']))
    vals = {
        'TITLE': html.escape(p['title']), 'DESCRIPTION': html.escape(p['description']), 'URL': url,
        'OG_IMAGE': cfg['site'] + 'assets/img/og-image.png', 'PRE': pre, 'H1': html.escape(p['h1']),
        'KICKER': html.escape(p['kicker']), 'LEAD': p.get('lead', ''), 'BODY': body, 'RELATED': rel_html,
        'FOOTER_LINKS': footer_links, 'WHATSAPP': cfg['whatsapp'], 'SCHEMA': schema(p, cfg, url),
        'ROBOTS': p.get('robots', 'index, follow'), 'CRUMB': ('<span aria-current="page">Recursos</span>' if p['slug'] == 'recursos' else
                  '<a href="%srecursos/">Recursos</a><span aria-hidden="true">/</span><span aria-current="page">%s</span>'
                  % (pre, html.escape(p.get('crumb', p['kicker'])))),
        'UPDATED': ('<p class="updated">Actualizado: %s</p>' % fecha(p['updated'])) if p.get('type') == 'guide' else '',
    }
    out = tpl
    for k, v in vals.items():
        out = out.replace('{{%s}}' % k, v)
    assert '{{' not in out, re.findall(r'\{\{\w+\}\}', out)
    return out


MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre',
         'noviembre', 'diciembre']


def fecha(iso):
    y, m, d = iso.split('-')
    return '%d de %s de %s' % (int(d), MESES[int(m) - 1], y)


def build(out_dir, cfg):
    """Genera las páginas en out_dir. Devuelve [(url, lastmod, título, descripción)] para sitemap y llms.txt."""
    out_dir = Path(out_dir)
    tpl = (PAGES / '_layout.html').read_text(encoding='utf-8')
    (out_dir / 'assets' / 'css').mkdir(parents=True, exist_ok=True)
    shutil.copy(PAGES / '_pages.css', out_dir / 'assets' / 'css' / 'pages.css')
    (out_dir / 'assets' / 'brand').mkdir(parents=True, exist_ok=True)
    for name in ['tefacturo-isologotipo-horizontal-negro.svg', 'tefacturo-isologotipo-horizontal-blanco.svg']:
        shutil.copy(ROOT / 'brand' / 'logos' / 'svg' / name, out_dir / 'assets' / 'brand' / name)
    pages = load()
    listed = []
    for p in pages:
        d = out_dir / p['slug']
        d.mkdir(parents=True, exist_ok=True)
        (d / 'index.html').write_text(render(p, pages, cfg, tpl), encoding='utf-8')
        listed.append((cfg['site'] + p['slug'] + '/', p['updated'], p['h1'], p['description']))
    # Índice /recursos/
    newest = max(p['updated'] for p in pages)
    hub = {'slug': 'recursos', 'title': 'Guías de facturación electrónica | TeFacturo',
           'description': 'Guías prácticas sobre facturación electrónica con ARCA para comercios y monotributistas: '
                          'tipos de factura, puntos de venta, notas de crédito y más.',
           'h1': 'Guías y recursos de facturación electrónica', 'kicker': 'Recursos', 'crumb': 'Recursos',
           'lead': '<p class="lead">Todo lo que necesitás saber para facturar con ARCA sin vueltas, explicado simple.</p>',
           'body': '<div class="cards cards-hub">%s</div>' % ''.join(card(p, '../') for p in pages), 'updated': newest}
    (out_dir / 'recursos').mkdir(exist_ok=True)
    (out_dir / 'recursos' / 'index.html').write_text(render(hub, pages, cfg, tpl), encoding='utf-8')
    listed.insert(0, (cfg['site'] + 'recursos/', newest, hub['h1'], hub['description']))
    # 404 (GitHub Pages la sirve en cualquier ruta: rutas absolutas al sitio)
    nf = {'slug': '', 'title': 'Página no encontrada | TeFacturo', 'description': 'La página que buscás no existe.',
          'h1': 'No encontramos esta página', 'kicker': 'Error 404', 'crumb': '404', 'robots': 'noindex',
          'lead': '<p class="lead">Puede que el link esté mal escrito o que la página se haya movido.</p>',
          'body': '<p><a class="btn" href="%s">Ir al inicio</a></p><h2>Quizás te sirva</h2><div class="cards">%s</div>'
                  % (cfg['site'], ''.join(card(p, cfg['site']) for p in pages[:3])), 'updated': newest}
    (out_dir / '404.html').write_text(render(nf, pages, cfg, tpl, pre=cfg['site']), encoding='utf-8')
    print('  páginas:', len(pages), '+ recursos + 404')
    return listed


def home_footer():
    """Banda de links a las páginas de contenido, al pie de la home (debajo de todo el contenido de Wix)."""
    links = ''.join('<li><a href="%s/">%s</a></li>' % (p['slug'], html.escape(p['h1'])) for p in load())
    return '''<style>
.tf-foot{background:#010A0A;color:#D7DDDD;font:300 15px/1.6 inter,system-ui,sans-serif;padding:48px 16px 40px}
.tf-foot-in{max-width:1120px;margin:0 auto}
.tf-foot-t{display:flex;flex-wrap:wrap;align-items:baseline;justify-content:space-between;gap:8px 24px;margin:0 0 18px}
.tf-foot h2{margin:0;color:#fff;font:600 20px/1.3 inter,system-ui,sans-serif;letter-spacing:-.01em}
.tf-foot a{color:#fff;text-decoration:none}
.tf-foot a:hover,.tf-foot a:focus-visible{color:#FF5B04}
.tf-foot-all{color:#FF5B04!important;font-weight:400}
.tf-foot ul{list-style:none;margin:0;padding:0;columns:1;column-gap:32px}
.tf-foot li{margin:0 0 10px;break-inside:avoid}
@media (min-width:750px){.tf-foot{padding:56px 32px 48px}.tf-foot ul{columns:2}}
@media (min-width:1000px){.tf-foot ul{columns:3}}
</style>
<footer class="tf-foot"><div class="tf-foot-in">
<div class="tf-foot-t"><h2>Guías y recursos</h2><a class="tf-foot-all" href="recursos/">Ver todas las guías →</a></div>
<ul>%s</ul>
</div></footer>
''' % links
