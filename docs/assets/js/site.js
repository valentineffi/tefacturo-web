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
  $$('header [id^="comp-kbgakxea_r_comp-"]').forEach(function (el) {
    if (el.closest('nav, [role="dialog"]')) return;
    var key = (el.getAttribute('aria-label') || el.textContent || '').trim().toLowerCase();
    var anchor = NAV[key];
    if (!anchor || el.querySelector('[id^="comp-"]')) return;
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

  /* ---------- videos: reproducir sólo cuando se ven ---------- */
  if ('IntersectionObserver' in window) {
    var vio = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        var v = e.target;
        if (e.isIntersecting) { var p = v.play(); if (p && p.catch) p.catch(function () {}); } else v.pause();
      });
    });
    $$('video').forEach(function (v) { v.muted = true; vio.observe(v); });
  }

  if (location.hash.length > 1) setTimeout(function () { scrollToId(location.hash.slice(1)); }, 50);
})();
