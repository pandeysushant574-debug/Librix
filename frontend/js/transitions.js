/* ============================================================
   transitions.js — smooth page-to-page navigation, click ripples, cursor light
   Works with css/glass.css. Plain JS, no libraries.
   ============================================================ */
(function () {
  'use strict';
  const LEAVE_MS = 260;
  const reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  let leaving = false;

  /** Fade the current page out, then go to `url`. Used for links, login and logout. */
  function pageGo(url) {
    if (leaving) return;
    leaving = true;
    document.body.classList.add('page-leaving');
    setTimeout(() => { window.location.href = url; }, reduce ? 0 : LEAVE_MS);
  }
  window.pageGo = pageGo;

  // The browser's back/forward cache can restore a page frozen in its "leaving" state.
  window.addEventListener('pageshow', () => {
    leaving = false;
    document.body.classList.remove('page-leaving');
  });

  // Intercept same-site link clicks so every page change animates.
  document.addEventListener('click', (e) => {
    if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    const a = e.target.closest && e.target.closest('a[href]');
    if (!a || a.target === '_blank' || a.hasAttribute('download')) return;
    const href = a.getAttribute('href');
    if (!href || href.startsWith('#') || /^(mailto:|tel:|javascript:)/i.test(href)) return;
    const url = new URL(a.href, window.location.href);
    if (url.origin !== window.location.origin) return;
    if (url.pathname === window.location.pathname && url.search === window.location.search) { e.preventDefault(); return; }
    e.preventDefault();
    a.classList.add('leaving-target');
    pageGo(url.href);
  });

  // Click ripple on buttons.
  document.addEventListener('pointerdown', (e) => {
    if (reduce) return;
    const el = e.target.closest && e.target.closest('.btn, .btn-icon');
    if (!el || el.disabled) return;
    const r = el.getBoundingClientRect();
    const size = Math.max(r.width, r.height) * 2.2;
    const dot = document.createElement('span');
    dot.className = 'ripple';
    dot.style.width = dot.style.height = size + 'px';
    dot.style.left = (e.clientX - r.left - size / 2) + 'px';
    dot.style.top = (e.clientY - r.top - size / 2) + 'px';
    if (getComputedStyle(el).position === 'static') el.style.position = 'relative';
    el.appendChild(dot);
    setTimeout(() => dot.remove(), 700);
  }, { passive: true });

  // Soft light that follows the cursor across glass surfaces.
  let raf = null;
  document.addEventListener('pointermove', (e) => {
    if (reduce || raf) return;
    raf = requestAnimationFrame(() => {
      raf = null;
      const el = e.target.closest && e.target.closest('.glass-panel, .kpi-card, .quality-card, .loop-step, .btn, .nav-item');
      if (!el) return;
      const r = el.getBoundingClientRect();
      el.style.setProperty('--mx', (e.clientX - r.left) + 'px');
      el.style.setProperty('--my', (e.clientY - r.top) + 'px');
    });
  }, { passive: true });
})();
