/* ============================================================
   search.js — debounced live search against GET /api/books?q=
   ============================================================ */

let searchDebounce;

function statusBadge2(status) {
  const map = { Available: 'badge-green', Unavailable: 'badge-orange', Inactive: 'badge-gray' };
  return `<span class="badge ${map[status] || 'badge-gray'}">${status}</span>`;
}

async function runSearch(q) {
  const tbody = document.getElementById('search-tbody');
  if (!q) {
    tbody.innerHTML = '<tr><td colspan="6" class="empty-state">Type to search the catalog…</td></tr>';
    return;
  }
  tbody.innerHTML = '<tr><td colspan="6" class="empty-state">Searching…</td></tr>';
  try {
    const results = await Api.get('/books', { q });
    tbody.innerHTML = results.length ? results.map(b => `
      <tr>
        <td>${escapeHtml(b.title)}</td>
        <td>${escapeHtml(b.author)}</td>
        <td>${escapeHtml(b.category || '—')}</td>
        <td>${escapeHtml(b.isbn || '—')}</td>
        <td>${b.available_qty}</td>
        <td>${statusBadge2(b.status)}</td>
      </tr>`).join('') : '<tr><td colspan="6" class="empty-state">No matches found.</td></tr>';
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="6" class="empty-state">${escapeHtml(err.message || 'Search failed.')}</td></tr>`;
  }
}

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('global-search').addEventListener('input', (e) => {
    clearTimeout(searchDebounce);
    const q = e.target.value.trim();
    searchDebounce = setTimeout(() => runSearch(q), 300);
  });
});
