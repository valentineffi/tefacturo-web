/* TeFacturo — runtime que reemplaza al JS de Wix.
 * Lee window.TF_CONFIG (triggersAndReactions de Wix, generado por tools/build_site.py) y reproduce:
 * animaciones de entrada, estados hover/click, menú hamburguesa, tabs de FAQ y scroll a anclas. */
(function () {
  'use strict';
  var CFG = window.TF_CONFIG || { triggers: {}, viewport: {}, repeaters: {}, anchors: {} };
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var root = document.documentElement;

  function inRange(bp) {
    var w = window.innerWidth;
    return (bp.min == null || w >= bp.min) && (bp.max == null || w <= bp.max);
  }
  function targets(id) {
    var el = document.getElementById(id);
    return (el ? [el] : []).concat($$('[id^="' + id + '__"]'));
  }

  /* ---------- barra de scroll (Wix la descuenta en sus cálculos de escala) ---------- */
  function scrollbar() {
    root.style.setProperty('--scrollbar-width', (window.innerWidth - root.clientWidth) + 'px');
  }
  scrollbar();
  window.addEventListener('resize', scrollbar);

  /* ---------- animaciones de entrada (viewport-enter → Play) ---------- */
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var pending = [];

  function done(el) {
    el.setAttribute('data-motion-enter', 'done');
    el.style.removeProperty('animation-play-state');
  }
  function measure(els) {
    // Posición sin la animación aplicada (Wix usa --motion-left/top para glide/arc)
    els.forEach(function (el) { el.setAttribute('data-motion-enter', 'done'); });
    var r = els.map(function (el) { return el.getBoundingClientRect(); });
    els.forEach(function (el, i) {
      el.removeAttribute('data-motion-enter');
      el.style.setProperty('--motion-left', r[i].left + 'px');
      el.style.setProperty('--motion-top', (r[i].top + window.scrollY) + 'px');
      el.style.setProperty('--motion-width', r[i].width + 'px');
      el.style.setProperty('--motion-height', r[i].height + 'px');
    });
  }
  function play(el) {
    var cs = getComputedStyle(el);
    if (cs.animationName === 'none') return done(el);
    var n = cs.animationName.split(',').length, ended = 0;
    var total = Math.max.apply(null, cs.animationDuration.split(',').map(function (d, i) {
      return parseFloat(d) * 1000 + parseFloat(cs.animationDelay.split(',')[i] || '0') * 1000;
    }));
    var finish = function () { if (el.getAttribute('data-motion-enter') !== 'done') done(el); };
    el.addEventListener('animationend', function h(e) {
      if (e.target !== el) return;
      if (++ended >= n) { el.removeEventListener('animationend', h); finish(); }
    });
    setTimeout(finish, total + 250);
    el.style.setProperty('animation-play-state', 'running');
  }

  Object.keys(CFG.triggers).forEach(function (id) {
    var ve = CFG.triggers[id]['viewport-enter'];
    if (!ve) return;
    var active = Object.keys(ve).some(function (k) {
      return ve[k].some(function (t) { return inRange(t.triggerBpRange || {}); });
    });
    targets(id).forEach(function (el) { pending.push({ el: el, id: id, active: active }); });
  });

  if (reduce || !('IntersectionObserver' in window)) {
    pending.forEach(function (p) { done(p.el); });
  } else {
    measure(pending.map(function (p) { return p.el; }));
    pending.forEach(function (p) {
      if (!p.active) return done(p.el);
      var prm = CFG.viewport[p.id] || {};
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting) { io.disconnect(); play(e.target); }
        });
      }, { threshold: prm.threshold != null ? prm.threshold : 0.15 });
      io.observe(p.el);
    });
  }
  // Cualquier animación pausada que no tenga disparador en este breakpoint queda en su estado final
  $$('[id^="comp-"]').forEach(function (el) {
    if (pending.some(function (p) { return p.el === el && p.active; })) return;
    var cs = getComputedStyle(el);
    if (cs.animationName !== 'none' && cs.animationPlayState.indexOf('paused') > -1) done(el);
  });

  /* ---------- estados (hover → AddState, click/keydown → ToggleState) ---------- */
  Object.keys(CFG.triggers).forEach(function (id) {
    var evs = CFG.triggers[id];
    ['hover', 'click', 'keydown'].forEach(function (ev) {
      if (!evs[ev]) return;
      Object.keys(evs[ev]).forEach(function (src) {
        var list = evs[ev][src];
        targets(src).forEach(function (el) {
          var apply = function (mode) {
            list.forEach(function (t) {
              if (!inRange(t.triggerBpRange || {})) return;
              t.reactions.forEach(function (r) {
                var name = r.reactionData && r.reactionData.name;
                if (!name) return;
                targets(id).forEach(function (tg) {
                  if (mode === 'add') tg.classList.add(name);
                  else if (mode === 'remove') tg.classList.remove(name);
                  else tg.classList.toggle(name);
                });
              });
            });
          };
          if (ev === 'hover') {
            el.addEventListener('mouseenter', function () { apply('add'); });
            el.addEventListener('mouseleave', function () { apply('remove'); });
          } else if (ev === 'click') {
            el.classList.add('has-click-trigger');
            el.addEventListener('click', function () { apply('toggle'); });
          } else {
            el.addEventListener('keydown', function (e) {
              if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); apply('toggle'); }
            });
          }
        });
      });
    });
  });

  /* ---------- scroll a secciones ---------- */
  function scrollToId(id) {
    var el = id && document.getElementById(id);
    var y = el ? el.getBoundingClientRect().top + window.scrollY : 0;
    window.scrollTo({ top: y, behavior: reduce ? 'auto' : 'smooth' });
  }
  document.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('a[href^="#"]');
    if (!a) return;
    e.preventDefault();
    closeMenu();
    var id = a.getAttribute('href').slice(1);
    scrollToId(id);
    if (id) history.replaceState(null, '', '#' + id); else history.replaceState(null, '', location.pathname);
  });

  // Menú de escritorio: en Wix son textos sin link; acá llevan a su sección.
  var NAV = {
    'sobre nosotros': 'anchors-mnhrlr5d', 'por qué elegirnos': 'anchors-mnhrlyvi', 'modo de uso': 'anchors-mnhrn2bf',
    'funciones': 'anchors-mpcom8jf', 'contacto': 'anchors-mnhrn58c', 'quiero mi tefacturo': 'anchors-mnhrn58c'
  };
  var navItems = [];  // los textos del menú de escritorio, para sumarles "Ingresar" (ver placeLogin)
  $$('header [id^="comp-kbgakxea_r_comp-"]').forEach(function (el) {
    if (el.closest('nav, [role="dialog"]')) return;
    var key = (el.getAttribute('aria-label') || el.textContent || '').trim().toLowerCase();
    var anchor = NAV[key];
    if (!anchor || el.querySelector('[id^="comp-"]')) return;
    if (key !== 'quiero mi tefacturo') navItems.push(el);
    el.classList.add('has-click-trigger');
    el.addEventListener('click', function () { scrollToId(CFG.anchors[anchor]); });
  });
  var logo = document.getElementById('comp-kbgakxea_r_comp-mndbqcp6');
  if (logo) logo.addEventListener('click', function () { scrollToId(null); });

  /* ---------- menú hamburguesa ---------- */
  var menuRoot = document.getElementById('comp-kbgakxea_r_comp-mnhluyru');
  var menuBtn = menuRoot && $('button[aria-label="Menu"]', menuRoot);
  var overlay = document.getElementById('comp-kbgakxea_r_comp-mnhluyuq');
  var menuHome = document.getElementById('comp-kbgakxea_r_comp-mnhluyru-menu-content');
  var menuSlot = document.getElementById('comp-kbgakxea_r_comp-mnhluyv71');
  var site = document.getElementById('SITE_CONTAINER');
  var OPEN = 'HamburgerOverlay547129737--isMenuOpen', savedY = 0;

  function openMenu() {
    if (!overlay || overlay.getAttribute('data-visible') === 'true') return;
    var nav = menuHome && $('nav', menuHome);
    if (nav && menuSlot) menuSlot.appendChild(nav);
    savedY = window.scrollY;
    if (site) site.style.marginTop = 'calc(' + (-savedY) + 'px)';
    document.body.classList.add('siteScrollingBlocked');
    overlay.classList.add(OPEN);
    overlay.setAttribute('data-visible', 'true');
    menuBtn.setAttribute('aria-expanded', 'true');
    overlay.focus();
  }
  function closeMenu() {
    if (!overlay || overlay.getAttribute('data-visible') !== 'true') return;
    var nav = menuSlot && $('nav', menuSlot);
    if (nav && menuHome) menuHome.insertBefore(nav, menuHome.firstChild);
    overlay.classList.remove(OPEN);
    overlay.setAttribute('data-visible', 'false');
    menuBtn.setAttribute('aria-expanded', 'false');
    document.body.classList.remove('siteScrollingBlocked');
    if (site) site.style.marginTop = '';
    window.scrollTo(0, savedY);
    menuBtn.focus();
  }
  if (menuBtn && overlay) {
    menuBtn.addEventListener('click', function () {
      overlay.getAttribute('data-visible') === 'true' ? closeMenu() : openMenu();
    });
    var closeBtn = $('#comp-kbgakxea_r_comp-mnhluyv91 button', overlay) || document.getElementById('comp-kbgakxea_r_comp-mnhluyv91');
    if (closeBtn) closeBtn.addEventListener('click', closeMenu);
    var bg = $('[data-hook="hamburger-overlay-dialog"]', overlay);
    if (bg) bg.addEventListener('click', closeMenu);
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeMenu(); });
    window.addEventListener('resize', function () { if (menuRoot.offsetParent === null) closeMenu(); });
  }

  /* ---------- tabs (Preguntas frecuentes) ---------- */
  $$('[role="tablist"]').forEach(function (list) {
    var tabs = $$('[role="tab"]', list);
    var P = 'Tabscomponent1176390459';
    var scroller = list;
    var comp = list.closest('[id^="comp-"]');
    var back = comp && $('[data-hook="BackwardScrollBtn"]', comp);
    var fwd = comp && $('[data-hook="ForwardScrollBtn"]', comp);
    var VIS = 'TabsScrollButton1157534303--isVisible';

    function setPhase(el, enter) {
      if (!el) return;
      el.className = el.className.replace(/\s*\S+---phase-\d+-(?:enter|exit)-(?:done|active)/g, '') +
        ' ' + P + (enter ? '---phase-10-enter-done' : '---phase-9-exit-done');
    }
    function select(tab, focus) {
      tabs.forEach(function (t) {
        var on = t === tab;
        t.classList.toggle('TabsList2027980309--current', on);
        t.setAttribute('aria-selected', on ? 'true' : 'false');
        t.setAttribute('tabindex', on ? '0' : '-1');
        t.setAttribute('data-testid', on ? 'ActiveTabItem' : 'false');
        var panel = $('[data-hook="TabPanel"][aria-labelledby="' + t.id + '"]');
        if (panel) {
          panel.classList.toggle(P + '--isVisible', on);
          panel.setAttribute('aria-hidden', on ? 'false' : 'true');
          setPhase(panel, on);
          setPhase(panel.closest('.' + P + '__animationWrapper'), on);
        }
      });
      if (focus) tab.focus();
      var lr = list.getBoundingClientRect(), tr = tab.getBoundingClientRect();
      if (tr.left < lr.left || tr.right > lr.right) scroller.scrollBy({ left: tr.left - lr.left - 20, behavior: 'smooth' });
    }
    tabs.forEach(function (t, i) {
      t.addEventListener('click', function () { select(t); });
      t.addEventListener('keydown', function (e) {
        var k = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0;
        if (k) { e.preventDefault(); select(tabs[(i + k + tabs.length) % tabs.length], true); }
      });
    });
    function arrows() {
      var max = scroller.scrollWidth - scroller.clientWidth - 1;
      if (back) back.classList.toggle(VIS, scroller.scrollLeft > 1);
      if (fwd) fwd.classList.toggle(VIS, scroller.scrollLeft < max);
    }
    if (back) back.addEventListener('click', function () { scroller.scrollBy({ left: -scroller.clientWidth * 0.6, behavior: 'smooth' }); });
    if (fwd) fwd.addEventListener('click', function () { scroller.scrollBy({ left: scroller.clientWidth * 0.6, behavior: 'smooth' }); });
    scroller.addEventListener('scroll', arrows, { passive: true });
    window.addEventListener('resize', arrows);
    arrows();
  });

  /* ---------- "Ingresar": en escritorio, un ítem más del menú; en el celular, ícono al lado del menú ---------- */
  var login = $('header .tf-login');
  // Lo que ocupan las letras (el bloque de Wix suele ser más ancho que el texto)
  function textBox(el) {
    var walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT), node, l = Infinity, r = -Infinity, t = Infinity, b = -Infinity;
    while ((node = walker.nextNode())) {
      if (!node.nodeValue.trim()) continue;
      var range = document.createRange();
      range.selectNodeContents(node);
      Array.prototype.forEach.call(range.getClientRects(), function (q) {
        if (!q.width) return;
        l = Math.min(l, q.left); r = Math.max(r, q.right); t = Math.min(t, q.top); b = Math.max(b, q.bottom);
      });
    }
    return r > l ? { left: l, right: r, top: t, bottom: b, width: r - l, height: b - t } : el.getBoundingClientRect();
  }
  function textStyle(el) {
    var walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, { acceptNode: function (n) { return n.nodeValue.trim() ? 1 : 3; } });
    var node = walker.nextNode();
    return getComputedStyle(node ? node.parentElement : el);
  }
  // Escritorio: los ítems se redistribuyen con el mismo espacio entre todos, "Ingresar" incluido
  function placeInMenu(cta, h) {
    var items = navItems.map(function (el) { return { el: el, b: textBox(el) }; })
      .filter(function (it) { return it.b.width; })
      .sort(function (a, b) { return a.b.left - b.b.left; });
    if (!items.length) return false;
    var st = textStyle(items[0].el);
    login.classList.add('is-text');
    login.style.fontFamily = st.fontFamily;
    login.style.fontSize = st.fontSize;
    login.style.fontWeight = st.fontWeight;
    login.style.color = st.color;
    var w = login.getBoundingClientRect().width;
    var widths = items.reduce(function (sum, it) { return sum + it.b.width; }, w);
    var c = cta.getBoundingClientRect(), start = items[0].b.left;
    var gap = (c.left - start - widths) / (items.length + 1);
    if (gap < 18) { login.classList.remove('is-text'); login.removeAttribute('style'); return false; }
    var x = start;
    items.forEach(function (it) { it.el.style.transform = 'translateX(' + Math.round(x - it.b.left) + 'px)'; x += it.b.width + gap; });
    login.style.left = Math.round(x - h.left) + 'px';
    login.style.top = Math.round(items[0].b.top - h.top + items[0].b.height / 2) + 'px';
    return true;
  }
  // Celular (o un menú sin lugar): círculo con el ícono, centrado en el hueco a la izquierda de ref
  function placeBeside(ref, h) {
    var r = ref.getBoundingClientRect(), left = h.left;
    $$('header [id^="comp-kbgakxea_r_comp-"]').forEach(function (el) {
      if (el === ref || el.contains(ref) || ref.contains(el) || el.closest('nav, [role="dialog"]')) return;
      var b = el.getBoundingClientRect();
      if (b.width && b.right <= r.left && b.bottom > r.top && b.top < r.bottom) left = Math.max(left, b.right);
    });
    var size = Math.max(28, Math.min(Math.round(r.height), Math.round(r.left - left - 16)));
    login.classList.add('is-compact');
    login.style.height = size + 'px';
    login.style.setProperty('--tf-login-h', size + 'px');
    login.style.top = Math.round(r.top - h.top + r.height / 2) + 'px';
    login.style.right = Math.round(h.right - r.left + (r.left - left - size) / 2) + 'px';
  }
  function placeLogin() {
    var header = login.parentNode, h = header.getBoundingClientRect();
    var cta = document.getElementById('comp-kbgakxea_r_comp-mndcac9l');
    navItems.forEach(function (el) { el.style.transform = ''; });
    login.className = 'tf-login';
    login.removeAttribute('style');
    var desktop = cta && cta.getBoundingClientRect().width;
    if (!(desktop && placeInMenu(cta, h))) {
      var ref = desktop ? cta : menuBtn;
      if (!ref || !ref.getBoundingClientRect().width) return;
      placeBeside(ref, h);
    }
    login.classList.add('is-placed');
  }
  if (login) {
    placeLogin();
    window.addEventListener('resize', placeLogin);
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(placeLogin);
  }

  /* ---------- "Ingresar" pregunta a qué sistema: el nuevo o el anterior (CFG.login) ---------- */
  if (login && CFG.login && CFG.login.options && CFG.login.options.length > 1) {
    var loginMenu = document.createElement('div');
    loginMenu.className = 'tf-login-menu';
    loginMenu.id = 'tf-login-menu';
    loginMenu.hidden = true;
    var loginTitle = document.createElement('p');
    loginTitle.textContent = CFG.login.title;
    loginMenu.appendChild(loginTitle);
    CFG.login.options.forEach(function (o) {
      var a = document.createElement('a'), b = document.createElement('b'), d = document.createElement('span');
      a.href = o.url;
      b.textContent = o.name;
      d.textContent = o.detail;
      a.appendChild(b);
      a.appendChild(d);
      loginMenu.appendChild(a);
    });
    // En el <body>, fuera del DOM de Wix: así ningún contenedor del header lo recorta ni le cambia la referencia del fixed
    document.body.appendChild(loginMenu);
    login.setAttribute('aria-haspopup', 'true');
    login.setAttribute('aria-expanded', 'false');
    login.setAttribute('aria-controls', loginMenu.id);
    var placeLoginMenu = function () {
      var r = login.getBoundingClientRect(), w = loginMenu.offsetWidth, vw = root.clientWidth;
      loginMenu.style.top = Math.round(r.bottom + 10) + 'px';
      // Alineado al borde derecho del botón si no entra hacia la derecha (el ícono del celular está pegado al menú)
      var left = r.left + w > vw - 16 ? r.right - w : r.left;
      loginMenu.style.left = Math.round(Math.max(16, Math.min(left, vw - 16 - w))) + 'px';
    };
    var closeLoginMenu = function (focusBack) {
      if (loginMenu.hidden) return;
      if (focusBack) login.focus();  // antes de ocultarlo: con el foco adentro, ocultarlo lo manda al <body>
      loginMenu.hidden = true;
      login.setAttribute('aria-expanded', 'false');
    };
    login.addEventListener('click', function (e) {
      e.preventDefault();
      if (!loginMenu.hidden) { closeLoginMenu(false); return; }
      loginMenu.hidden = false;
      login.setAttribute('aria-expanded', 'true');
      placeLoginMenu();
      if (e.detail === 0) $('a', loginMenu).focus();  // abierto con el teclado: el foco pasa a la primera opción
    });
    document.addEventListener('click', function (e) {
      if (!loginMenu.contains(e.target) && !login.contains(e.target)) closeLoginMenu(false);
    });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeLoginMenu(true); });
    window.addEventListener('resize', function () { if (!loginMenu.hidden) placeLoginMenu(); });
    window.addEventListener('scroll', function () { if (!loginMenu.hidden) placeLoginMenu(); }, { passive: true });
  }

  /* ---------- planes: precios de la API (GET /api/public/plans), no del HTML ---------- */
  var plansEl = document.getElementById('planes');
  if (plansEl && CFG.plans && window.fetch) loadPlans(plansEl, CFG.plans);

  function loadPlans(section, cfg) {
    var grid = $('.tf-plans-grid', section), toggle = $('.tf-period', section), period = 'monthly', plans = [];
    var VISIBLE = 6;
    function esc(t) { return String(t).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
    function pesos(cents) { return '$ ' + Math.round(cents / 100).toLocaleString('es-AR'); }
    function fail() {
      grid.innerHTML = '<p class="tf-plans-msg">No pudimos cargar los planes. Consultanos por <a href="' + esc(cfg.whatsapp) + '" rel="noopener">WhatsApp</a>.</p>';
    }
    // Sólo las de cfg.features, en ese orden y con ese nombre (PLANS_FEATURES en build_site.py)
    function features(plan) {
      var keys = plan.capabilities.map(function (c) { return c.key; });
      return cfg.features.filter(function (f) { return keys.indexOf(f.key) >= 0; });
    }
    function list(items) { return items.map(function (f) { return '<li>' + esc(f.label) + '</li>'; }).join(''); }
    function card(plan, prev) {
      var p = plan.periods.filter(function (x) { return x.period === period; })[0] || plan.periods[0];
      var note = p.period === 'monthly' ? 'Pagando mes a mes' : pesos(p.priceCents) + ' por ' + (p.months === 12 ? 'año' : p.months + ' meses');
      var limits = cfg.limits.map(function (key) {
        var l = plan.limits.filter(function (x) { return x.key === key; })[0];
        return l ? '<li><span>' + esc(l.name) + '</span><b>' + (l.value === null ? 'Sin límite' : l.value.toLocaleString('es-AR')) + '</b></li>' : '';
      }).join('');
      var feats = features(plan), title = 'Incluye';
      if (prev) {
        var had = features(prev).map(function (c) { return c.key; });
        feats = feats.filter(function (c) { return had.indexOf(c.key) < 0; });
        title = 'Todo lo del plan ' + esc(prev.name) + (feats.length ? ', más:' : '');
      }
      var more = feats.length > VISIBLE + 1
        ? '<details class="tf-more"><summary>Ver ' + (feats.length - VISIBLE) + ' más</summary><ul class="tf-feats">' + list(feats.slice(VISIBLE)) + '</ul></details>'
        : '';
      var shown = more ? feats.slice(0, VISIBLE) : feats;
      var wa = cfg.whatsapp + '?text=' + encodeURIComponent('Hola, quiero el plan ' + plan.name + ' de TeFacturo.');
      return '<article class="tf-plan" aria-labelledby="plan-' + esc(plan.code) + '">' +
        '<h3 id="plan-' + esc(plan.code) + '">' + esc(plan.name) + '</h3>' +
        (plan.description ? '<p class="tf-plan-desc">' + esc(plan.description) + '</p>' : '') +
        '<p class="tf-price"><b>' + pesos(p.monthlyPriceCents) + '</b><span>/mes</span></p>' +
        '<p class="tf-price-note">' + note + '</p>' +
        (limits ? '<ul class="tf-limits">' + limits + '</ul>' : '') +
        '<p class="tf-feat-t">' + title + '</p>' +
        (shown.length ? '<ul class="tf-feats">' + list(shown) + '</ul>' : '') + more +
        '<div class="tf-plan-cta-wrap"><a class="tf-plan-cta" href="' + esc(wa) + '" rel="noopener">Quiero el plan ' + esc(plan.name) + '</a></div>' +
        '</article>';
    }
    function render() { grid.innerHTML = plans.map(function (plan, i) { return card(plan, plans[i - 1]); }).join(''); }

    var ctrl = window.AbortController ? new AbortController() : null;
    var timeout = setTimeout(function () { if (ctrl) ctrl.abort(); }, 8000);
    fetch(cfg.api, { signal: ctrl ? ctrl.signal : undefined, credentials: 'omit' })
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (body) {
        clearTimeout(timeout);
        plans = (body && body.data && body.data.items || []).filter(function (x) { return x.periods && x.periods.length; });
        if (!plans.length) return fail();
        // El selector sólo si todos los planes se pueden pagar por año
        var annual = plans.every(function (x) { return x.periods.some(function (y) { return y.period === 'annual'; }); });
        if (annual) {
          var save = Math.max.apply(null, plans.map(function (x) {
            return x.periods.filter(function (y) { return y.period === 'annual'; })[0].discountBps;
          }));
          $('.tf-save', toggle).textContent = save > 0 ? '· ahorrá ' + Math.round(save / 100) + ' %' : '';
          toggle.hidden = false;
          $$('button', toggle).forEach(function (b) {
            b.addEventListener('click', function () {
              period = b.getAttribute('data-period');
              $$('button', toggle).forEach(function (x) { x.setAttribute('aria-checked', x === b ? 'true' : 'false'); });
              render();
            });
          });
        }
        render();
      })
      .catch(function () { clearTimeout(timeout); fail(); });
  }

  /* ---------- descargas: la última versión publicada de cada plataforma (GET /api/app-releases/latest) ---------- */
  function latestRelease(platform, arch) {
    return fetch(CFG.downloads.api + '?platform=' + encodeURIComponent(platform) + '&arch=' + encodeURIComponent(arch), { credentials: 'omit' })
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (body) { return body && body.data && body.data.release; });
  }
  if (CFG.downloads && window.fetch) $$('#descargas .tf-dl[data-platform]').forEach(function (card) {
    var platform = card.getAttribute('data-platform');
    function latest(arch) { return latestRelease(platform, arch); }
    latest(card.getAttribute('data-arch')).then(function (rel) {
      if (!rel || !rel.url) return;
      var btn = $('.tf-dl-btn', card);
      btn.removeAttribute('aria-disabled');
      btn.href = rel.url;
      btn.setAttribute('download', '');
      btn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M12 4v11M7 10l5 5 5-5M5 20h14"/></svg>Descargar';
      var mb = rel.sizeBytes ? ' · ' + Math.round(rel.sizeBytes / 1048576) + ' MB' : '';
      $('.tf-dl-meta', card).textContent = 'Versión ' + rel.version + mb;
      (CFG.downloads.alt[platform] || []).forEach(function (alt) {
        latest(alt.arch).then(function (other) {
          if (!other || !other.url) return;
          var p = document.createElement('p');
          p.className = 'tf-dl-alt';
          var link = document.createElement('a');
          link.href = other.url;
          link.setAttribute('download', '');
          link.textContent = alt.label;
          p.appendChild(link);
          card.insertBefore(p, $('.tf-dl-actions', card));  // arriba del botón: los botones quedan alineados
        }).catch(function () {});
      });
    }).catch(function () {});
  });
  // Enlaces de texto debajo de las tarjetas (el launcher): cada uno aparece sólo si tiene versión publicada
  if (CFG.downloads && window.fetch) $$('#descargas .tf-dl-link[data-platform]').forEach(function (link) {
    latestRelease(link.getAttribute('data-platform'), link.getAttribute('data-arch')).then(function (rel) {
      if (!rel || !rel.url) return;
      link.href = rel.url;
      link.setAttribute('download', '');
      link.title = 'Versión ' + rel.version + (rel.sizeBytes ? ' · ' + Math.round(rel.sizeBytes / 1048576) + ' MB' : '');
      link.hidden = false;
      link.parentNode.hidden = false;
    }).catch(function () {});
  });

  /* ---------- videos: bajar y reproducir sólo cuando se ven ---------- */
  if ('IntersectionObserver' in window) {
    var vio = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        var v = e.target;
        if (e.isIntersecting) { var p = v.play(); if (p && p.catch) p.catch(function () {}); } else v.pause();
      });
    });  // preload="none" en el HTML: el video se baja recién al verse (mientras tanto, el póster)
    $$('video').forEach(function (v) { v.muted = true; vio.observe(v); });
  }

  /* ---------- años de experiencia: se cuentan hasta el año en curso (el build los deja con el año en que se generó) ---------- */
  $$('[data-tf-since]').forEach(function (el) {
    el.textContent = new Date().getFullYear() - Number(el.getAttribute('data-tf-since'));
  });

  if (location.hash.length > 1) setTimeout(function () { scrollToId(location.hash.slice(1)); }, 50);
})();
