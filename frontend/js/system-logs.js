/* ============================================================
   system-logs.js — Quality > System Logs screen
   ============================================================ */

const LEVEL_BADGE = { INFO: 'badge-blue', WARNING: 'badge-orange', ERROR: 'badge-red', DEBUG: 'badge-gray' };
let logSearchDebounce;

function kpiLog(label, value) {
  return `<div class="kpi-card glass"><div class="kpi-label">${label}</div><div class="kpi-value">${value}</div></div>`;
}

async function loadLogCounters() {
  try {
    const c = await Api.get('/logs', { counters: 1 });
    document.getElementById('log-counters').innerHTML = [
      kpiLog('Today', c.today), kpiLog('Warnings', c.warnings), kpiLog('Errors', c.errors), kpiLog('Debug', c.debug),
    ].join('');
  } catch (e) { /* non-fatal */ }
}

async function loadLogs() {
  const q = document.getElementById('log-search').value.trim();
  const level = document.getElementById('log-level-filter').value;
  try {
    const rows = await Api.get('/logs', { q, level });
    document.getElementById('logs-tbody').innerHTML = rows.length ? rows.map(l => `
      <tr>
        <td>${escapeHtml(l.timestamp)}</td>
        <td><span class="badge ${LEVEL_BADGE[l.level] || 'badge-gray'}">${l.level}</span></td>
        <td>${escapeHtml(l.module)}</td>
        <td>${escapeHtml(l.action)}</td>
        <td>${escapeHtml(l.username || '—')}</td>
        <td style="max-width:320px;white-space:normal;">${escapeHtml(l.message)}</td>
        <td>${escapeHtml(l.result || '—')}</td>
      </tr>`).join('') : '<tr><td colspan="7" class="empty-state">No logs match your filters.</td></tr>';
  } catch (err) {
    showToast(err.message || 'Failed to load logs.', 'error');
  }
}

async function viewAuditLogs() {
  try {
    const rows = await Api.get('/logs', { audit: 1 });
    const html = `
      <div class="modal-header"><h3>📜 Audit Logs</h3><button class="modal-close" onclick="closeModal()">✕</button></div>
      <div class="table-wrap glass"><div class="table-scroll" style="max-height:60vh;">
      <table class="data-table">
        <thead><tr><th>Time</th><th>User</th><th>Action</th><th>Entity</th><th>Old</th><th>New</th></tr></thead>
        <tbody>${rows.length ? rows.map(a => `
          <tr>
            <td>${escapeHtml(a.timestamp)}</td>
            <td>${escapeHtml(a.username || '—')}</td>
            <td>${escapeHtml(a.action)}</td>
            <td>${escapeHtml(a.entity_type)} #${a.entity_id ?? '—'}</td>
            <td style="max-width:180px;white-space:normal;">${escapeHtml(a.old_value || '—')}</td>
            <td style="max-width:180px;white-space:normal;">${escapeHtml(a.new_value || '—')}</td>
          </tr>`).join('') : '<tr><td colspan="6" class="empty-state">No audit records.</td></tr>'}
        </tbody>
      </table></div></div>`;
    openModal(html);
  } catch (err) {
    showToast(err.message || 'Failed to load audit logs.', 'error');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  loadLogCounters(); loadLogs();
  document.getElementById('log-search').addEventListener('input', () => {
    clearTimeout(logSearchDebounce);
    logSearchDebounce = setTimeout(loadLogs, 300);
  });
  document.getElementById('log-level-filter').addEventListener('change', loadLogs);
  document.getElementById('view-audit-btn').addEventListener('click', viewAuditLogs);
});
