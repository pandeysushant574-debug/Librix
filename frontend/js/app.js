/* ============================================================
   app.js — shared shell logic loaded on every authenticated page:
   sidebar highlight, live clock, user chip, toasts, modal helpers.
   ============================================================ */

const NAV_ITEMS = [
  { group: 'Library', items: [
    { href: 'dashboard.html', icon: '🏠', label: 'Dashboard' },
    { href: 'books.html', icon: '📚', label: 'Books' },
    { href: 'members.html', icon: '🧑‍🤝‍🧑', label: 'Members' },
    { href: 'issue-return.html', icon: '🔁', label: 'Issue / Return' },
    { href: 'search.html', icon: '🔎', label: 'Search' },
    { href: 'fines.html', icon: '💲', label: 'Fines' },
    { href: 'reports.html', icon: '📊', label: 'Reports' },
  ]},
  { group: 'Quality (Q16)', items: [
    { href: 'quality.html', icon: '✅', label: 'Quality Overview' },
    { href: 'unit-tests.html', icon: '🧪', label: 'Unit Test Cases' },
    { href: 'bug-matrix.html', icon: '🐞', label: 'Bug Matrix' },
    { href: 'input-bounds.html', icon: '📐', label: 'Input Bounds' },
    { href: 'system-logs.html', icon: '🗒️', label: 'System Logs' },
  ]},
  { group: 'System', items: [
    { href: 'admin.html', icon: '🛡️', label: 'Admin' },
    { href: 'settings.html', icon: '⚙️', label: 'Settings' },
  ]},
];

function renderSidebar() {
  const mount = document.getElementById('sidebar-mount');
  if (!mount) return;
  const current = window.location.pathname.split('/').pop() || 'dashboard.html';

  let html = `<div class="brand"><span class="l1">L</span><span class="l2">i</span><span class="l3">b</span><span class="l4">r</span><span class="l5">i</span><span class="l6">x</span></div>`;

  NAV_ITEMS.forEach(group => {
    html += `<div class="nav-group"><div class="nav-label">${group.group}</div>`;
    group.items.forEach(item => {
      const active = current === item.href ? 'active' : '';
      html += `<a class="nav-item ${active}" href="${item.href}"><span class="ic">${item.icon}</span><span class="label">${item.label}</span></a>`;
    });
    html += `</div>`;
  });

  html += `<div class="sidebar-footer"><a href="settings.html" title="Settings" style="text-decoration:none;">⚙️</a><span>🌐</span></div>`;
  mount.innerHTML = html;
  setupNavIndicator(mount);
}

/* ---- sliding glass pill behind the active menu item (animates from the previous page's item) ---- */
const NAV_KEY = 'librix.nav';

function navRect(sidebar, item) {
  const sb = sidebar.getBoundingClientRect();
  const r = item.getBoundingClientRect();
  return { top: r.top - sb.top + sidebar.scrollTop, left: r.left - sb.left + sidebar.scrollLeft, width: r.width, height: r.height };
}

function placeNavIndicator(ind, rect) {
  ind.style.top = rect.top + 'px';
  ind.style.left = rect.left + 'px';
  ind.style.width = rect.width + 'px';
  ind.style.height = rect.height + 'px';
}

function setupNavIndicator(sidebar) {
  const active = sidebar.querySelector('.nav-item.active');
  if (!active) return;
  let ind = sidebar.querySelector('.nav-indicator');
  if (!ind) {
    ind = document.createElement('div');
    ind.className = 'nav-indicator no-anim';
    sidebar.insertBefore(ind, sidebar.firstChild);
  }
  sidebar.classList.add('has-indicator');
  let prev = null;
  try { prev = JSON.parse(sessionStorage.getItem(NAV_KEY) || 'null'); } catch (e) { /* ignore */ }
  const now = navRect(sidebar, active);
  if (prev && prev.href !== active.getAttribute('href') && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    placeNavIndicator(ind, prev.rect);          // start where the last page's pill was...
    void ind.offsetWidth;                       // ...commit that position...
    ind.classList.remove('no-anim');
    requestAnimationFrame(() => placeNavIndicator(ind, now));   // ...then glide to the new item
  } else {
    placeNavIndicator(ind, now);
    requestAnimationFrame(() => ind.classList.remove('no-anim'));
  }
  try { sessionStorage.setItem(NAV_KEY, JSON.stringify({ href: active.getAttribute('href'), rect: now })); } catch (e) { /* ignore */ }
}

/* items can be hidden by role after login info loads, and the layout changes on resize */
function refreshNavIndicator() {
  const sidebar = document.getElementById('sidebar-mount');
  const active = sidebar && sidebar.querySelector('.nav-item.active');
  const ind = sidebar && sidebar.querySelector('.nav-indicator');
  if (!active || !ind) return;
  ind.classList.add('no-anim');
  const rect = navRect(sidebar, active);
  placeNavIndicator(ind, rect);
  void ind.offsetWidth;
  ind.classList.remove('no-anim');
  try { sessionStorage.setItem(NAV_KEY, JSON.stringify({ href: active.getAttribute('href'), rect })); } catch (e) { /* ignore */ }
}
window.addEventListener('resize', refreshNavIndicator);

function renderTopbarClock() {
  const el = document.getElementById('topbar-clock');
  if (!el) return;
  function tick() {
    const now = new Date();
    const month = now.toLocaleString('en-US', { month: 'short' }).toUpperCase();
    const day = now.getDate();
    const dateStr = now.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
    const timeStr = now.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
    el.innerHTML = `<div><div style="font-size:10px;font-weight:800;opacity:.8">${month}</div><div class="date-num">${day}</div></div>
      <div><div>${dateStr}</div><div style="color:var(--text-muted)">${timeStr}</div></div>`;
  }
  tick();
  setInterval(tick, 30000);
}

async function renderUserChip() {
  const el = document.getElementById('user-chip');
  if (!el) return;
  try {
    const user = await Api.get('/auth/me');
    const initials = (user.name || user.username).split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();
    el.innerHTML = `<div class="user-avatar">${initials}</div>
      <div class="user-meta"><div class="name">${escapeHtml(user.name || user.username)}</div><div class="role">${escapeHtml(user.role)}</div></div>`;
    window.CURRENT_USER = user;
    applyRoleVisibility(user.role);
  } catch (e) {
    window.location.href = 'login.html';
  }
}

function applyRoleVisibility(role) {
  // Assistant: search, issue/return, limited reports. Librarian: no Admin. Admin: everything.
  const restrictedForAssistant = ['books.html', 'members.html', 'admin.html'];
  const restrictedForLibrarian = ['admin.html'];
  document.querySelectorAll('.nav-item').forEach(a => {
    const href = a.getAttribute('href');
    if (role === 'Assistant' && restrictedForAssistant.includes(href)) a.style.display = 'none';
    if (role === 'Librarian' && restrictedForLibrarian.includes(href)) a.style.display = 'none';
  });
  refreshNavIndicator();
}

function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

function showToast(message, type = 'success') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => toast.classList.add('out'), 3600);
  setTimeout(() => toast.remove(), 4000);
}

function openModal(html) {
  closeModal(true);
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay';
  overlay.id = 'active-modal';
  overlay.innerHTML = `<div class="modal-box glass-panel">${html}</div>`;
  overlay.addEventListener('click', (e) => { if (e.target === overlay) closeModal(); });
  document.body.appendChild(overlay);
}

function closeModal(immediate = false) {
  const existing = document.getElementById('active-modal');
  if (!existing) return;
  existing.id = 'closing-modal';            // frees the id so a new modal can open right away
  if (immediate) { existing.remove(); return; }
  existing.classList.add('closing');        // play the fade-out, then remove
  setTimeout(() => existing.remove(), 200);
}

function downloadCsv(content, filename) {
  const blob = new Blob([content], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename;
  document.body.appendChild(a); a.click(); a.remove();
  URL.revokeObjectURL(url);
}

async function handleLogout() {
  try { await Api.post('/auth/logout'); } catch (e) { /* ignore */ }
  try { sessionStorage.removeItem(NAV_KEY); } catch (e) { /* ignore */ }
  (window.pageGo || ((u) => { window.location.href = u; }))('login.html');
}

function initShell() {
  renderSidebar();
  renderTopbarClock();
  renderUserChip();
  const logoutBtn = document.getElementById('logout-btn');
  if (logoutBtn) logoutBtn.addEventListener('click', handleLogout);
}

document.addEventListener('DOMContentLoaded', initShell);
