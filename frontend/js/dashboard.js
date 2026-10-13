/* ============================================================
   dashboard.js — pulls GET /api/reports/dashboard (real SQL data)
   ============================================================ */

function kpi(label, value, sub = '') {
  return `<div class="kpi-card glass"><div class="kpi-label">${label}</div><div class="kpi-value">${value}</div>${sub ? `<div class="kpi-sub">${sub}</div>` : ''}</div>`;
}

function recentRow(title, sub, badge) {
  return `<div class="recent-item"><div><div class="ri-title">${escapeHtml(title)}</div><div class="ri-sub">${escapeHtml(sub)}</div></div>${badge || ''}</div>`;
}

async function loadDashboard() {
  try {
    const d = await Api.get('/reports/dashboard');

    document.getElementById('library-kpis').innerHTML = [
      kpi('Total Books', d.books.total),
      kpi('Available Books', d.books.available),
      kpi('Issued Books', d.books.issued),
      kpi('Active Members', d.members.active),
    ].join('');

    document.getElementById('testing-kpis').innerHTML = [
      kpi('Total Tests', d.testing.total),
      kpi('Passed', d.testing.passed),
      kpi('Failed', d.testing.failed),
      kpi('Pass Rate', d.testing.pass_rate + '%'),
    ].join('');

    document.getElementById('bugs-kpis').innerHTML = [
      kpi('Open', d.bugs.open_count),
      kpi('Critical', d.bugs.critical),
      kpi('Fixed', d.bugs.fixed),
      kpi('Closed', d.bugs.closed),
    ].join('');

    document.getElementById('system-kpis').innerHTML = [
      kpi('Logs Today', d.logs.today),
      kpi('Warnings', d.logs.warnings),
      kpi('Errors', d.logs.errors),
    ].join('');

    document.getElementById('recent-issues').innerHTML = d.recent.issues.length
      ? d.recent.issues.map(i => recentRow(i.title, i.member_name + ' · ' + i.issue_date,
          `<span class="badge ${i.status === 'Returned' ? 'badge-green' : 'badge-blue'}">${i.status}</span>`)).join('')
      : '<div class="empty-state">No recent issues.</div>';

    document.getElementById('recent-failed-tests').innerHTML = d.recent.failed_tests.length
      ? d.recent.failed_tests.map(t => recentRow(t.test_code + ' — ' + t.title, t.executed_at, '<span class="badge badge-red">FAIL</span>')).join('')
      : '<div class="empty-state">No failed tests. 🎉</div>';

    document.getElementById('recent-bugs').innerHTML = d.recent.bugs.length
      ? d.recent.bugs.map(b => recentRow(b.bug_code + ' — ' + b.title, b.severity, `<span class="badge badge-orange">${b.status}</span>`)).join('')
      : '<div class="empty-state">No bugs logged.</div>';

  } catch (err) {
    showToast(err.message || 'Failed to load dashboard.', 'error');
  }
}

document.addEventListener('DOMContentLoaded', loadDashboard);
