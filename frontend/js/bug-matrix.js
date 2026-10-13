/* ============================================================
   bug-matrix.js — Quality > Bug Log Matrix screen
   ============================================================ */

let allBugs = [];
const BUG_BADGE = { Open: 'badge-orange', 'In Progress': 'badge-blue', Fixed: 'badge-blue', Retest: 'badge-yellow', Closed: 'badge-green' };
const SEVERITY_BADGE = { Critical: 'badge-red', High: 'badge-orange', Medium: 'badge-yellow', Low: 'badge-gray' };
const NEXT_STATUS = { Open: 'In Progress', 'In Progress': 'Fixed', Fixed: 'Retest', Retest: 'Closed' };

function kpiSmall(label, value) {
  return `<div class="kpi-card glass"><div class="kpi-label">${label}</div><div class="kpi-value">${value}</div></div>`;
}

async function loadCounters() {
  try {
    const c = await Api.get('/bugs', { counters: 1 });
    document.getElementById('bug-counters').innerHTML = [
      kpiSmall('Total Bugs', c.total), kpiSmall('Open', c.open_count), kpiSmall('Critical', c.critical_count),
      kpiSmall('High Priority', c.high_priority_count), kpiSmall('Fixed', c.fixed_count),
      kpiSmall('Retest', c.retest_count), kpiSmall('Closed', c.closed_count),
    ].join('');
  } catch (err) { /* non-fatal */ }
}

async function loadBugs() {
  const status = document.getElementById('bug-status-filter').value;
  const severity = document.getElementById('bug-severity-filter').value;
  try {
    allBugs = await Api.get('/bugs', { status, severity });
    renderBugsTable();
  } catch (err) {
    showToast(err.message || 'Failed to load bugs.', 'error');
  }
}

function renderBugsTable() {
  document.getElementById('bugs-tbody').innerHTML = allBugs.length ? allBugs.map(b => `
    <tr>
      <td><b>${escapeHtml(b.bug_code)}</b></td>
      <td>${escapeHtml(b.reported_date)}</td>
      <td>${escapeHtml(b.module)}</td>
      <td>${escapeHtml(b.title)}</td>
      <td><span class="badge ${SEVERITY_BADGE[b.severity]}">${b.severity}</span></td>
      <td>${escapeHtml(b.priority)}</td>
      <td><span class="badge ${BUG_BADGE[b.status]}">${b.status}</span></td>
      <td>${escapeHtml(b.closed_date || '—')}</td>
      <td><div class="row-actions">
        ${NEXT_STATUS[b.status] ? `<button class="btn-icon" title="Advance to ${NEXT_STATUS[b.status]}" onclick="advanceBug(${b.bug_id}, '${NEXT_STATUS[b.status]}')">➡️</button>` : ''}
        ${b.status === 'Retest' ? `<button class="btn-icon" title="Failed retest — back to In Progress" onclick="advanceBug(${b.bug_id}, 'In Progress')">↩️</button>` : ''}
        <button class="btn-icon" title="Edit" onclick="editBug(${b.bug_id})">✏️</button>
        <button class="btn-icon" title="Delete" onclick="deleteBug(${b.bug_id})">🗑️</button>
      </div></td>
    </tr>`).join('') : '<tr><td colspan="9" class="empty-state">No bugs found.</td></tr>';
}

async function advanceBug(id, newStatus) {
  try {
    await Api.put('/bugs/' + id, { status: newStatus });
    showToast('Bug moved to ' + newStatus + '.', 'success');
    loadBugs(); loadCounters();
  } catch (err) {
    showToast(err.message || 'Update failed.', 'error');
  }
}

async function deleteBug(id) {
  if (!confirm('Delete this bug record?')) return;
  try {
    await Api.del('/bugs/' + id);
    showToast('Bug deleted.', 'success');
    loadBugs(); loadCounters();
  } catch (err) {
    showToast(err.message || 'Delete failed.', 'error');
  }
}

function bugFormHtml(b) {
  const x = b || {};
  return `
    <div class="modal-header"><h3>${b ? 'Edit Bug' : 'Log Bug'}</h3><button class="modal-close" onclick="closeModal()">✕</button></div>
    <form id="bug-form">
      <div class="form-grid">
        <div class="field"><label>Module <span class="req">*</span></label><input type="text" id="b-module" value="${escapeHtml(x.module || '')}" required></div>
        <div class="field"><label>Reported Date <span class="req">*</span></label><input type="date" id="b-date" value="${x.reported_date || new Date().toISOString().slice(0,10)}" required></div>
        <div class="field span-2"><label>Title <span class="req">*</span></label><input type="text" id="b-title" value="${escapeHtml(x.title || '')}" required></div>
        <div class="field span-2"><label>Description <span class="req">*</span></label><textarea id="b-description" required>${escapeHtml(x.description || '')}</textarea></div>
        <div class="field"><label>Severity <span class="req">*</span></label>
          <select id="b-severity"><option ${x.severity === 'Critical' ? 'selected' : ''}>Critical</option><option ${x.severity === 'High' ? 'selected' : ''}>High</option><option ${x.severity === 'Medium' || !x.severity ? 'selected' : ''}>Medium</option><option ${x.severity === 'Low' ? 'selected' : ''}>Low</option></select></div>
        <div class="field"><label>Priority <span class="req">*</span></label>
          <select id="b-priority"><option ${x.priority === 'High' ? 'selected' : ''}>High</option><option ${x.priority === 'Medium' || !x.priority ? 'selected' : ''}>Medium</option><option ${x.priority === 'Low' ? 'selected' : ''}>Low</option></select></div>
        <div class="field span-2"><label>Root Cause</label><textarea id="b-root">${escapeHtml(x.root_cause || '')}</textarea></div>
        <div class="field span-2"><label>Fix Action</label><textarea id="b-fix">${escapeHtml(x.fix_action || '')}</textarea></div>
        <div class="field span-2"><label>Retest Result</label><textarea id="b-retest">${escapeHtml(x.retest_result || '')}</textarea></div>
      </div>
      <div id="bug-form-error" class="field-error"></div>
      <div class="form-actions">
        <button type="button" class="btn" onclick="closeModal()">Cancel</button>
        <button type="submit" class="btn btn-primary">${b ? 'Save Changes' : 'Log Bug'}</button>
      </div>
    </form>`;
}

function openBugModal(b) {
  openModal(bugFormHtml(b));
  document.getElementById('bug-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      module: document.getElementById('b-module').value.trim(),
      reported_date: document.getElementById('b-date').value,
      title: document.getElementById('b-title').value.trim(),
      description: document.getElementById('b-description').value.trim(),
      severity: document.getElementById('b-severity').value,
      priority: document.getElementById('b-priority').value,
      root_cause: document.getElementById('b-root').value.trim(),
      fix_action: document.getElementById('b-fix').value.trim(),
      retest_result: document.getElementById('b-retest').value.trim(),
    };
    try {
      if (b) { await Api.put('/bugs/' + b.bug_id, payload); showToast('Bug updated.', 'success'); }
      else { await Api.post('/bugs', payload); showToast('Bug logged.', 'success'); }
      closeModal();
      loadBugs(); loadCounters();
    } catch (err) {
      document.getElementById('bug-form-error').textContent = (err.errors && err.errors.join(' ')) || err.message;
    }
  });
}

function editBug(id) {
  const b = allBugs.find(x => x.bug_id === id);
  if (b) openBugModal(b);
}

function exportBugsCsv() {
  const header = ['Code', 'Date', 'Module', 'Title', 'Severity', 'Priority', 'Status', 'Closed'];
  const lines = [header.join(',')].concat(allBugs.map(b =>
    [b.bug_code, b.reported_date, b.module, b.title, b.severity, b.priority, b.status, b.closed_date]
      .map(v => `"${(v ?? '').toString().replace(/"/g, '""')}"`).join(',')
  ));
  downloadCsv(lines.join('\n'), 'bug-matrix.csv');
}

document.addEventListener('DOMContentLoaded', () => {
  loadCounters(); loadBugs();
  document.getElementById('bug-status-filter').addEventListener('change', loadBugs);
  document.getElementById('bug-severity-filter').addEventListener('change', loadBugs);
  document.getElementById('add-bug-btn').addEventListener('click', () => openBugModal());
  document.getElementById('export-bugs-btn').addEventListener('click', exportBugsCsv);
});
