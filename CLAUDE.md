# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Objetivo

Réplica **pixel-perfect** (idéntica, no "parecida") del sitio de TeFacturo hecho en Wix Studio, publicada en GitHub Pages (`docs/`). Fuente de verdad: https://ailen4403.wixstudio.com/tfacturo (one-page). Más adelante pasa al dominio tefacturo.com.ar (cambiar `SITE_URL` en `tools/build_site.py` y agregar `docs/CNAME`).

Para contenido nuevo se puede leer https://tefacturo.com.ar/ (misión, qué hace), pero **siempre consultar con el usuario antes de agregar o cambiar contenido**.

## Cómo funciona (pipeline)

No es un sitio escrito a mano: es el DOM + CSS renderizado de Wix, sin el JS de Wix, con assets locales y un runtime propio chico. Eso es lo que garantiza el pixel-perfect (incluidos los degradés).

1. `tools/capture_wix.mjs` → `source/`: DOM renderizado (`wix-dom.html`), **todo** el CSS en orden incluido el inyectado en runtime (`wix-css.json`), config de páginas/interacciones de Wix (`wix-features.json`), overlay del menú mobile abierto (`wix-menu-open.json`), tamaño renderizado de cada imagen por ancho (`wix-media-sizes.json`) y screenshots de referencia (`source/reference/`).
2. `tools/build_site.py` → `docs/`: baja originales de Wix a `.cache/` (imágenes, videos, fuentes, PDF), genera WebP responsive (`srcset` + `sizes` calculados de las medidas reales), recomprime videos (540p H.264), reescribe URLs, saca scripts/banner de Wix y elementos sobrantes del template, inyecta `head` (SEO/OG/favicon) y `window.TF_CONFIG`.
3. `src/site.js` (runtime, se copia a `docs/assets/js/`): reimplementa lo que hacía el JS de Wix leyendo **la misma config de Wix** (`triggersAndReactions`): animaciones de entrada (IntersectionObserver + `animation-play-state`, marca `data-motion-enter="done"` al terminar), estados hover/click (clases `variants-*`), menú hamburguesa (mueve el `<nav>` al overlay), tabs de FAQ, scroll a anclas, `--scrollbar-width`.

4. `tools/pages.py` → páginas de contenido propias para SEO (no son Wix): `src/pages/<slug>.html` (cabecera JSON `<!--page {...} -->` + cuerpo HTML) con `src/pages/_layout.html` y `_pages.css` → `docs/<slug>/index.html`, más `/recursos/` (índice), `404.html`, y entradas en `sitemap.xml` y `llms.txt`. Para agregar una página: crear el `.html` en `src/pages/` y correr el build. La home lleva al pie una banda "Guías y recursos" (`pages.home_footer()`, agregado propio debajo de todo el contenido de Wix: el clon mide ~300 px más que la referencia y `compare.mjs` compara hasta el alto de la referencia). Contenido nuevo: solo datos que estén en el sitio o sean normativa verificable de ARCA (nada de precios, testimonios ni cifras inventadas) y consultar con el usuario.

5. `tools/landing.py` → landing de performance para anuncios (`src/landing/empezar.html` → `docs/empezar/index.html`): autocontenida (CSS/JS inline, ~37 KB), `noindex` y fuera del sitemap, única conversión = WhatsApp (con eventos `whatsapp_click` en dataLayer, `fbq Contact`, `gtag generate_lead`). IDs de Meta Pixel / Google Tag y la referencia de campaña en el mensaje se configuran arriba de `tools/landing.py`. El copy y la fuente de cada dato están en `src/landing/COPY.md`: cambiar el copy ahí primero. La pantalla del equipo son capturas reales de la app (`src/landing/app/`, copiadas a `docs/empezar/app/`): sacarlas de nuevo si cambia la pantalla de venta, con productos ficticios sin marca y sin datos del emisor.

6. `tools/build_pdf.mjs` → PDF "Funcionalidades principales" (`src/pdf/funcionalidades.html` → `src/pdf/Funcionalidades-Principales-TeFacturo.pdf`, que `build_site.py` copia a `docs/assets/docs/`). Réplica del original de Illustrator con el contenido corregido; usa la Inter de `docs/assets/fonts`, así que va después de un `build_site.py`, y falla si el contenido no entra en una hoja A4. Una función nueva es un `<section class="f">` más. Después de regenerarlo, correr `build_site.py` otra vez para publicarlo.

**Nunca editar `docs/` a mano**: se regenera. Los cambios van en `src/site.js`, `tools/build_site.py` o se re-captura de Wix.

## Comandos

```bash
node tools/capture_wix.mjs            # re-capturar Wix (necesita playwright global: npm i -g playwright)
python3 tools/build_site.py           # generar docs/ (python3 + Pillow, ffmpeg)
python3 -m http.server 8765 -d docs   # ver local
node tools/compare.mjs [1440,390]     # diff píxel vs referencia de Wix → .cache/compare/diff-<w>.png (TF_URL=<url> para el publicado)
node tools/compare_interactions.mjs   # hover tarjeta, tab FAQ, menú mobile, hover CTA: Wix vs clon lado a lado
node tools/build_pdf.mjs              # regenerar el PDF de funcionalidades (CHROME=<ruta> para usar otro Chrome)
python3 tools/diff_bands.py ref.png clone.png out.png 30 y0:y1 ...   # ver franjas concretas (ref|clon|diff)
tools/build_logos.sh                  # regenerar brand/logos y brand/favicon desde el manual (pág. 7)
```

Estado de referencia de `compare.mjs`: misma altura en todos los anchos (30 px menos = banner de Wix eliminado; el footer de guías queda fuera de la comparación) y ~1,3–1,8 % de píxeles distintos, todo en bordes de imágenes rasterizadas (Wix sirve AVIF con unsharp mask) y frames de video. Si sube de eso, algo se rompió.

## Detalles que no son obvios

- Wix responsive: un solo DOM, breakpoints en CSS (desktop >1000px, tablet 750–1000, mobile 320–750). El escalado es CSS puro (`--scaling-factor`).
- El banner "Creado con Wix" reserva 30 px vía `--wix-ads-height` **y** `--sticky-offset`; ambos se fuerzan a 0 al final del CSS.
- Las URLs de imágenes de Wix llevan el recorte en el path (`/v1/crop/x_..,y_..,w_..,h_../fill/...`) con comas adentro: no cortar la URL en comas.
- Imágenes con transparencia (degradés, curvas, títulos-imagen) se exportan en WebP **sin pérdida** para que los degradés no tengan banding; fotos en WebP q90.
- Muchos títulos/botones son imágenes en Wix ("Ágil, simple…", "Empezar es fácil", "Preguntas frecuentes", CTAs). Se mantienen como imagen para ser idénticos; los `alt` descriptivos están en `ALTS` (build_site.py).
- Las tarjetas de "Funcionalidades" son imagen frente (ícono) + dorso; el hover pone opacity 0 al frente (clase `variants-*`, transición 0.4s). En Wix el dorso es una imagen con el texto escrito; acá es texto (`FEATURE_CARDS` + `FEATURE_CSS` en build_site.py, aprobado por el usuario, 2026-10-19), con el fondo `#041212`, Inter 600/300 y las medidas de la imagen de 746 px expresadas en `cqw` para que escale igual. `compare.mjs` puede marcar diferencias de antialiasing en esa franja.
- SEO sin cambios visuales (`semantics()` en build_site.py): `<h1>` oculto (`H1_TEXT`, la portada es una imagen-título), los `<h2>/<h6>` que no son títulos (menú, datos de contacto, subtítulos; lista `NOT_HEADINGS`) pasan a `<p>` con la misma clase (el CSS de Wix estiliza por clase `font_X`, no por etiqueta), y `fetchpriority="high"` en las imágenes de la primera sección. Schema JSON-LD en `schema()`, `llms.txt` en `llms_txt()`.
- Videos: `preload="none"` y sin `autoplay`; el runtime los baja y reproduce al entrar en pantalla. No agregar `rootMargin` a ese observer: los videos arrancan antes y `compare.mjs` captura otro frame (sube el diff en 390 sin que haya un cambio real).
- Hay un diálogo sobrante del template (`comp-kd5px9q0`, "SECURE YOUR BUSINESS TODAY / INFO@MYSITE.COM") que el build elimina.
- macOS es case-insensitive: no crear `assets/` en la raíz (choca con `Assets/`).

## Diferencias deliberadas con Wix

En Wix estos links no funcionan o son placeholders; acá se resolvieron así (confirmar con el usuario si cambia algo):
- Menú de escritorio y CTA "Quiero mi TeFacturo" del header: en Wix no navegan; acá scrollean a su sección (CTA → Contacto). Ver `NAV` en `src/site.js`.
- "¿Más dudas? Contactanos": en Wix va a `web.whatsapp.com`; acá a `WHATSAPP_URL` (wa.me con el teléfono del sitio).
- PDF "Descubrí todas las funciones" se sirve local (`docs/assets/docs/`) y ya no es el de Wix: lo genera `tools/build_pdf.mjs` (desde 2026-10-19).
- Íconos de WhatsApp/Instagram/Facebook del contacto: sin link (igual que en Wix) hasta tener las URLs.
- Typos y un dato erróneo del Wix (FAQ: "uestro", ARCA ≠ "Administración Federal…", menú: "elegrinos") se corrigen en el build con `TEXT_FIXES` (aprobado por el usuario, 2026-10-13). Si el build avisa "no encontré el texto a corregir", el Wix cambió.
- "Nuestra trayectoria" (`TRAJECTORY` en build_site.py, aprobado por el usuario, 2026-10-19): los años de experiencia se cuentan desde `SINCE_YEAR` (2018) y el runtime los lleva al año en curso (`data-tf-since`, también en las páginas y en `/empezar/`, con `{{YEARS}}`); los comercios activos salen de `ACTIVE_COMMERCES` (`{{ACTIVE}}` en páginas y landing), «80 % Mayor eficiencia» y «100 % Clientes satisfechos» (no medidos) pasaron a «3 Plataformas» y «100 % Validado por ARCA». `compare.mjs` va a marcar esa franja como distinta de la referencia: es a propósito.
- Funcionalidades coherentes con el sistema (`FAQ_FIXES`, páginas, `llms.txt`, schema y PDF; aprobado por el usuario, 2026-10-19): sin notas de débito ni facturación de servicios hasta que el sistema las emita, sin "Google Play" hasta que la app esté publicada ahí, y los usuarios adicionales tienen costo. Antes de afirmar una función, verificarla contra el sistema (repos `bussiness-api` y `tefacturo`). Presupuestos, remitos y cuentas corrientes se sumaron el 2026-10-19 (PDF, guías, `llms.txt`, schema); **Mercado Pago (QR/Point) no se anuncia** hasta validarlo con un comercio real (decisión del usuario).

## Assets y marca

- `Assets/`: material original del cliente (no versionado: pesado y privado). No modificar.
- `brand/`: logos exportados como vectores exactos del manual de marca (el `.af` de Affinity no se puede exportar por CLI), favicons, `og-image.png`.
- Marca: naranja `#FF5B04`, claro `#F6F6F6`, gris `#D7DDDD`, casi negro `#010A0A`, acento `#075056`. Tipografía Inter (SemiBold títulos, Regular destacados, Light texto). El Wix también usa Sora en algunos textos.
