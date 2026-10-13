/* ============================================================
   unit-tests.js — Quality > Unit Test Cases screen
   ============================================================ */

let allTests = [];

function testStatusBadge(status) {
  if (!status) return '<span class="badge badge-gray">Not Run</span>';
  const map = { PASS: 'badge-green', FAIL: 'badge-red', ERROR: 'badge-red' };
  return `<span class="badge ${map[status] || 'badge-gray'}">${status}</span>`;
}

async function loadTests() {
  try {
    allTests = await Api.get('/tests');
    renderTestsTable();
  } catch (err) {
    showToast(err.message || 'Failed to load test cases.', 'error');
  }
}

function renderTestsTable() {
  document.getElementById('tests-tbody').innerHTML = allTests.length ? allTests.map(t => `
    <tr>
      <td>${t.test_case_id}</td>
      <td><b>${escapeHtml(t.test_code)}</b></td>
      <td>${escapeHtml(t.module)}</td>
      <td>${escapeHtml(t.title)}</td>
      <td style="max-width:220px;white-space:normal;">${escapeHtml(t.expected_result)}</td>
      <td style="max-width:220px;white-space:normal;">${escapeHtml(t.last_actual || '—')}</td>
      <td>${testStatusBadge(t.last_status)}</td>
      <td>${escapeHtml((t.last_executed_at || '—'))}</td>
      <td><div class="row-actions">
        <button class="btn-icon" title="Run Test" onclick="runTest(${t.test_case_id})">▶</button>
        <button class="btn-icon" title="Edit" onclick="editTest(${t.test_case_id})">✏️</button>
        <button class="btn-icon" title="Delete" onclick="deleteTest(${t.test_case_id})">🗑️</button>
      </div></td>
    </tr>`).join('') : '<tr><td colspan="9" class="empty-state">No test cases yet.</td></tr>';
}

async function runTest(id) {
  try {
    const result = await Api.post('/tests/run/' + id);
    showToast(`${result.test_code}: ${result.status}`, result.status === 'PASS' ? 'success' : 'error');
    loadTests();
  } catch (err) {
    showToast(err.message || 'Test run failed.', 'error');
  }
}

async function runAllTests() {
  try {
    const results = await Api.post('/tests/run-all');
    const passed = results.filter(r => r.status === 'PASS').length;
    showToast(`Ran ${results.length} tests — ${passed} passed, ${results.length - passed} failed/error.`, passed === results.length ? 'success' : 'warning');
    loadTests();
  } catch (err) {
    showToast(err.message || 'Run all failed.', 'error');
  }
}

async function deleteTest(id) {
  if (!confirm('Delete this test case and its history?')) return;
  try {
    await Api.del('/tests/' + id);
    showToast('Test case deleted.', 'success');
    loadTests();
  } catch (err) {
    showToast(err.message || 'Delete failed.', 'error');
  }
}

function testFormHtml(t) {
  const x = t || {};
  return `
    <div class="modal-header"><h3>${t ? 'Edit Test Case' : 'Add Test Case'}</h3><button class="modal-close" onclick="closeModal()">✕</button></div>
    <form id="test-form">
      <div class="form-grid">
        <div class="field"><label>Module <span class="req">*</span></label><input type="text" id="t-module" value="${escapeHtml(x.module || '')}" required></div>
        <div class="field"><label>Test Type</label>
          <select id="t-type"><option ${x.test_type === 'Unit' || !x.test_type ? 'selected' : ''}>Unit</option><option ${x.test_type === 'Functional' ? 'selected' : ''}>Functional</option><option ${x.test_type === 'Regression' ? 'selected' : ''}>Regression</option></select></div>
        <div class="field span-2"><label>Title <span class="req">*</span></label><input type="text" id="t-title" value="${escapeHtml(x.title || '')}" required></div>
        <div class="field span-2"><label>Description</label><textarea id="t-description">${escapeHtml(x.description || '')}</textarea></div>
        <div class="field span-2"><label>Input Data</label><textarea id="t-input">${escapeHtml(x.input_data || '')}</textarea></div>
        <div class="field span-2"><label>Expected Result <span class="req">*</span></label><textarea id="t-expected" required>${escapeHtml(x.expected_result || '')}</textarea></div>
        <div class="field"><label>Priority</label>
          <select id="t-priority"><option ${x.priority === 'High' ? 'selected' : ''}>High</option><option ${x.priority === 'Medium' || !x.priority ? 'selected' : ''}>Medium</option><option ${x.priority === 'Low' ? 'selected' : ''}>Low</option></select></div>
      </div>
      <div id="test-form-error" class="field-error"></div>
      <div class="form-actions">
        <button type="button" class="btn" onclick="closeModal()">Cancel</button>
        <button type="submit" class="btn btn-primary">${t ? 'Save Changes' : 'Add Test Case'}</button>
      </div>
    </form>`;
}

function openTestModal(t) {
  openModal(testFormHtml(t));
  document.getElementById('test-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      module: document.getElementById('t-module').value.trim(),
      test_type: document.getElementById('t-type').value,
      title: document.getElementById('t-title').value.trim(),
      description: document.getElementById('t-description').value.trim(),
      input_data: document.getElementById('t-input').value.trim(),
      expected_result: document.getElementById('t-expected').value.trim(),
      priority: document.getElementById('t-priority').value,
    };
    try {
      if (t) { await Api.put('/tests/' + t.test_case_id, payload); showToast('Test case updated.', 'success'); }
      else { await Api.post('/tests', payload); showToast('Test case added.', 'success'); }
      closeModal();
      loadTests();
    } catch (err) {
      document.getElementById('test-form-error').textContent = (err.errors && err.errors.join(' ')) || err.message;
    }
  });
}

function editTest(id) {
  const t = allTests.find(x => x.test_case_id === id);
  if (t) openTestModal(t);
}

function exportTestsCsv() {
  const header = ['Code', 'Module', 'Title', 'Expected', 'Actual', 'Status', 'Executed At'];
  const lines = [header.join(',')].concat(allTests.map(t =>
    [t.test_code, t.module, t.title, t.expected_result, t.last_actual, t.last_status, t.last_executed_at]
      .map(v => `"${(v ?? '').toString().replace(/"/g, '""')}"`).join(',')
  ));
  downloadCsv(lines.join('\n'), 'unit-test-cases.csv');
}

document.addEventListener('DOMContentLoaded', () => {
  loadTests();
  document.getElementById('run-all-btn').addEventListener('click', runAllTests);
  document.getElementById('add-test-btn').addEventListener('click', () => openTestModal());
  document.getElementById('export-tests-btn').addEventListener('click', exportTestsCsv);
});
