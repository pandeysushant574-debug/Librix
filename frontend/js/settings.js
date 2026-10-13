/* ============================================================
   settings.js — Settings page: glass on/off, light/night mode, UI colour.
   All changes apply instantly through window.LibrixTheme (js/theme.js).
   ============================================================ */
(function () {
  'use strict';
  const T = window.LibrixTheme;
  const glassToggle = document.getElementById('glass-toggle');
  const modeSeg = document.getElementById('mode-seg');
  const swatchBox = document.getElementById('swatches');
  const colorInput = document.getElementById('custom-color-input');
  const hexLabel = document.getElementById('custom-hex');

  function renderSwatches() {
    const s = T.get();
    swatchBox.innerHTML = '';
    T.PRESETS.forEach((p) => {
      const wrap = document.createElement('div');
      wrap.className = 'swatch-wrap';
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'swatch' + (p.color ? '' : ' original') + (s.color === p.color ? ' active' : '');
      if (p.color) b.style.background = p.color;
      b.title = p.name;
      b.setAttribute('aria-label', p.name + ' colour');
      b.addEventListener('click', () => { T.set({ color: p.color }); sync(); });
      const label = document.createElement('span');
      label.textContent = p.name;
      wrap.appendChild(b); wrap.appendChild(label);
      swatchBox.appendChild(wrap);
    });
  }

  function sync() {
    const s = T.get();
    glassToggle.classList.toggle('on', s.glass);
    glassToggle.setAttribute('aria-checked', String(s.glass));
    modeSeg.querySelectorAll('button').forEach((b) => b.classList.toggle('active', b.dataset.mode === s.mode));
    renderSwatches();
    hexLabel.textContent = s.color ? s.color.toUpperCase() : 'Original palette';
    if (s.color) colorInput.value = s.color;
  }

  function toggleGlass() {
    const on = !T.get().glass;
    T.set({ glass: on });
    sync();
    if (window.showToast) showToast(on ? 'Glass effect on' : 'Glass effect off');
  }
  glassToggle.addEventListener('click', toggleGlass);
  glassToggle.addEventListener('keydown', (e) => { if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); toggleGlass(); } });

  modeSeg.addEventListener('click', (e) => {
    const b = e.target.closest('button[data-mode]');
    if (!b) return;
    T.set({ mode: b.dataset.mode });
    sync();
  });

  // live-update while dragging the picker, save on every change
  colorInput.addEventListener('input', () => { T.set({ color: colorInput.value }); sync(); });

  document.getElementById('reset-btn').addEventListener('click', () => {
    T.reset(); sync();
    if (window.showToast) showToast('Appearance reset to defaults');
  });

  window.addEventListener('librix-theme-sync', sync);   // another tab changed the settings
  sync();
})();
