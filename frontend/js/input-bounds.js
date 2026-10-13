/* ============================================================
   input-bounds.js — Quality > Input Bounds Testing screen
   ============================================================ */

async function loadBoundaryTests() {
  try {
    const rows = await Api.get('/boundary-tests');
    renderBoundaryTable(rows);
  } catch (err) {
    showToast(err.message || 'Failed to load boundary tests.', 'error');
  }
}

function renderBoundaryTable(rows) {
  document.getElementById('boundary-tbody').innerHTML = rows.length ? rows.map(r => `
    <tr>
      <td><b>${escapeHtml(r.test_code)}</b></td>
      <td>${escapeHtml(r.module)}</td>
      <td>${escapeHtml(r.field_name)}</td>
      <td style="max-width:260px;white-space:normal;">${escapeHtml(r.expected_behavior)}</td>
      <td style="max-width:260px;white-space:normal;">${escapeHtml(r.actual_behavior || '—')}</td>
      <td><span class="badge ${r.status === 'PASS' ? 'badge-green' : r.status === 'FAIL' ? 'badge-red' : 'badge-gray'}">${r.status || 'Not Run'}</span></td>
      <td>${escapeHtml(r.executed_at || '—')}</td>
    </tr>`).join('') : '<tr><td colspan="7" class="empty-state">No boundary tests run yet. Click "Run All Boundary Tests".</td></tr>';
}

async function runBoundaryTests() {
  try {
    const results = await Api.post('/boundary-tests/run');
    const passed = results.filter(r => r.status === 'PASS').length;
    showToast(`Ran ${results.length} boundary tests — ${passed} passed.`, passed === results.length ? 'success' : 'warning');
    loadBoundaryTests();
  } catch (err) {
    showToast(err.message || 'Run failed.', 'error');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  loadBoundaryTests();
  document.getElementById('run-boundary-btn').addEventListener('click', runBoundaryTests);
});
