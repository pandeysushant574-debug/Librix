/* ============================================================
   theme.js — appearance settings (glass on/off, light/night mode, UI colour).
   Loaded in <head> of EVERY page so the saved look is applied before first paint.
   Settings live in localStorage ('librix.settings') so they persist per browser.
   Public API:  window.LibrixTheme.get() / .set(patch) / .reset() / .PRESETS
   ============================================================ */
(function () {
  'use strict';
  const KEY = 'librix.settings';
  const DEFAULTS = { glass: true, mode: 'light', color: null };   // color null = original Librix palette

  const PRESETS = [
    { name: 'Original', color: null },
    { name: 'Ocean',    color: '#2563eb' },
    { name: 'Emerald',  color: '#059669' },
    { name: 'Teal',     color: '#0d9488' },
    { name: 'Violet',   color: '#7c3aed' },
    { name: 'Rose',     color: '#e11d48' },
    { name: 'Sunset',   color: '#ea580c' },
    { name: 'Gold',     color: '#ca8a04' },
    { name: 'Slate',    color: '#475569' },
  ];

  function load() {
    try {
      const raw = JSON.parse(localStorage.getItem(KEY) || 'null');
      if (raw && typeof raw === 'object') {
        return {
          glass: raw.glass !== false,
          mode: raw.mode === 'dark' ? 'dark' : 'light',
          color: /^#[0-9a-fA-F]{6}$/.test(raw.color || '') ? raw.color.toLowerCase() : null,
        };
      }
    } catch (e) { /* ignore corrupt value */ }
    return Object.assign({}, DEFAULTS);
  }

  function save(s) { try { localStorage.setItem(KEY, JSON.stringify(s)); } catch (e) { /* storage blocked */ } }

  /* ---- colour helpers ---- */
  function hexToHsl(hex) {
    const r = parseInt(hex.slice(1, 3), 16) / 255, g = parseInt(hex.slice(3, 5), 16) / 255, b = parseInt(hex.slice(5, 7), 16) / 255;
    const max = Math.max(r, g, b), min = Math.min(r, g, b), d = max - min;
    let h = 0, s = 0; const l = (max + min) / 2;
    if (d) {
      s = d / (1 - Math.abs(2 * l - 1));
      if (max === r) h = ((g - b) / d) % 6; else if (max === g) h = (b - r) / d + 2; else h = (r - g) / d + 4;
      h = Math.round(h * 60); if (h < 0) h += 360;
    }
    return { h, s: Math.round(s * 100), l: Math.round(l * 100) };
  }
  function luminance(hex) {
    const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
    return 0.2126 * f(parseInt(hex.slice(1, 3), 16)) + 0.7152 * f(parseInt(hex.slice(3, 5), 16)) + 0.0722 * f(parseInt(hex.slice(5, 7), 16));
  }
  const hsl = (h, s, l, a) => `hsl(${((h % 360) + 360) % 360} ${Math.max(0, Math.min(100, s))}% ${Math.max(0, Math.min(100, l))}%${a != null ? ' / ' + a : ''})`;

  /* ---- build the CSS variable set for the chosen colour + mode ---- */
  function buildVars(s) {
    const dark = s.mode === 'dark';
    const v = {};

    // Base hue: custom colour, or the original purple/orange family for "Original" in night mode.
    let base = null;
    if (s.color) base = hexToHsl(s.color);
    else if (dark) base = { h: 272, s: 55, l: 50 };
    if (!base) return v;                                  // Original + light mode → untouched stylesheet

    const h = base.h, sat = Math.max(35, Math.min(85, base.s));

    if (dark) {
      v['--bg-gradient'] =
        `radial-gradient(circle at 15% 20%, ${hsl(h, sat, 30, 0.55)}, transparent 45%),` +
        `radial-gradient(circle at 85% 10%, ${hsl(h + 40, sat, 26, 0.5)}, transparent 50%),` +
        `radial-gradient(circle at 75% 75%, ${hsl(h - 40, sat, 28, 0.5)}, transparent 55%),` +
        `linear-gradient(135deg, ${hsl(h, 40, 7)} 0%, ${hsl(h + 15, 38, 11)} 45%, ${hsl(h + 35, 40, 16)} 100%)`;
      v['--orb1'] = hsl(h, sat, 45, 0.38);       v['--orb2'] = hsl(h + 40, sat, 42, 0.32);
      v['--orb3'] = hsl(h - 40, sat, 42, 0.34);  v['--orb4'] = hsl(h + 80, sat, 40, 0.28);
      v['--sidebar-bg'] =
        `linear-gradient(180deg, ${hsl(h, sat - 5, 24, 0.7)} 0%, ${hsl(h + 25, sat - 10, 18, 0.7)} 55%, ${hsl(h + 50, sat - 10, 14, 0.75)} 100%)`;
    } else {
      v['--bg-gradient'] =
        `radial-gradient(circle at 15% 20%, ${hsl(h + 25, 90, 82, 0.8)}, transparent 45%),` +
        `radial-gradient(circle at 85% 10%, ${hsl(h - 25, 90, 80, 0.7)}, transparent 50%),` +
        `radial-gradient(circle at 75% 75%, ${hsl(h + 55, 85, 78, 0.7)}, transparent 55%),` +
        `linear-gradient(135deg, ${hsl(h, sat, 66)} 0%, ${hsl(h + 25, sat, 72)} 50%, ${hsl(h + 55, sat, 78)} 100%)`;
      v['--orb1'] = hsl(h + 20, 95, 80, 0.55);   v['--orb2'] = hsl(h - 20, 95, 78, 0.5);
      v['--orb3'] = hsl(h + 60, 90, 76, 0.5);    v['--orb4'] = hsl(h + 100, 90, 78, 0.45);
      v['--sidebar-bg'] =
        `linear-gradient(180deg, ${hsl(h, sat, 58, 0.62)} 0%, ${hsl(h + 25, sat, 62, 0.58)} 55%, ${hsl(h + 50, sat, 66, 0.6)} 100%)`;
    }

    // Accent only when the user actually picked a colour (keeps original green buttons otherwise).
    if (s.color) {
      const a = s.color;
      const hh = base.h, ss = Math.max(40, base.s);
      v['--accent'] = a;
      v['--accent-strong'] = hsl(hh, ss, Math.max(18, base.l - 12));
      v['--accent-soft'] = hsl(hh, ss, base.l, 0.35);
      v['--on-accent'] = luminance(a) > 0.42 ? '#000000' : '#ffffff';
    }
    return v;
  }

  const MANAGED = ['--bg-gradient', '--orb1', '--orb2', '--orb3', '--orb4', '--sidebar-bg',
    '--accent', '--accent-strong', '--accent-soft', '--on-accent'];

  function apply(s) {
    const root = document.documentElement;
    root.setAttribute('data-theme', 'librix');
    root.setAttribute('data-glass', s.glass ? 'on' : 'off');
    root.setAttribute('data-mode', s.mode);
    if (s.color) root.setAttribute('data-accent', 'custom'); else root.removeAttribute('data-accent');
    MANAGED.forEach((k) => root.style.removeProperty(k));
    const vars = buildVars(s);
    Object.keys(vars).forEach((k) => root.style.setProperty(k, vars[k]));
    root.style.colorScheme = s.mode === 'dark' ? 'dark' : 'light';
    // keep the mobile browser chrome in step
    let meta = document.querySelector('meta[name="theme-color"]');
    if (!meta && document.head) { meta = document.createElement('meta'); meta.name = 'theme-color'; document.head.appendChild(meta); }
    if (meta) meta.content = s.mode === 'dark' ? '#14101f' : (s.color || '#4a2e4f');
  }

  let state = load();
  apply(state);

  window.LibrixTheme = {
    PRESETS,
    get: () => Object.assign({}, state),
    set(patch) { state = Object.assign({}, state, patch); save(state); apply(state); return this.get(); },
    reset() { state = Object.assign({}, DEFAULTS); save(state); apply(state); return this.get(); },
  };

  // keep several open tabs in sync
  window.addEventListener('storage', (e) => { if (e.key === KEY) { state = load(); apply(state); window.dispatchEvent(new Event('librix-theme-sync')); } });
})();
