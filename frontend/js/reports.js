/* ============================================================
   reports.js — renders each of the 6 spec reports from real SQL data
   ============================================================ */

const REPORT_COLUMNS = {
  library: [
    ['title', 'Title'], ['author', 'Author'], ['category', 'Category'],
    ['quantity', 'Qty'], ['available_qty', 'Available'], ['status', 'Status'],
  ],
  issues: [
    ['title', 'Book'], ['member_name', 'Member'], ['issue_date', 'Issued'],
    ['due_date', 'Due'], ['return_date', 'Returned'], ['status', 'Status'], ['fine_amount', 'Fine'],
  ],
  fines: [
    ['member_name', 'Member'], ['days_late', 'Days Late'], ['rate_per_day', 'Rate/Day'],
    ['amount', 'Amount'], ['status', 'Status'], ['created_at', 'Created'],
  ],
  'system-logs': [
    ['level', 'Level'], ['count', 'Count'],
  ],
};

let currentReportRows = [];
let currentReportType = 'library';

function kpi(label, value) {
  return `<div class="kpi-card glass"><div class="kpi-label">${label}</div><div class="kpi-value">${value}</div></div>`;
}

async function loadReport() {
  currentReportType = document.getElementById('report-picker').value;
  const kpiBox = document.getElementById('report-kpis');
  const table = document.getElementById('report-table');

  if (currentReportType === 'testing' || currentReportType === 'bugs') {
    table.style.display = 'none';
    kpiBox.style.display = 'grid';
    try {
      const data = currentReportType === 'testing' ? await Api.get('/reports/testing') : await Api.get('/reports/bugs');
      if (currentReportType === 'testing') {
        kpiBox.innerHTML = [
          kpi('Unit Tests Total', data.unit.total), kpi('Unit Passed', data.unit.passed),
          kpi('Unit Failed', data.unit.failed), kpi('Unit Pass Rate', data.unit.pass_rate + '%'),
          kpi('Boundary Total', data.boundary.total), kpi('Boundary Passed', data.boundary.passed),
          kpi('Boundary Failed', data.boundary.failed), kpi('Boundary Coverage', data.boundary.coverage + '%'),
        ].join('');
      } else {
        kpiBox.innerHTML = [
          kpi('Total Bugs', data.total), kpi('Critical', data.critical),
          kpi('Open', data.open_count), kpi('Fixed', data.fixed), kpi('Closed', data.closed),
        ].join('');
      }
    } catch (err) {
      showToast(err.message || 'Failed to load report.', 'error');
    }
    return;
  }

  kpiBox.style.display = 'none';
  table.style.display = 'table';
  try {
    currentReportRows = await Api.get('/reports/' + currentReportType);
    const cols = REPORT_COLUMNS[currentReportType];
    document.getElementById('report-thead').innerHTML = '<tr>' + cols.map(c => `<th>${c[1]}</th>`).join('') + '</tr>';
    document.getElementById('report-tbody').innerHTML = currentReportRows.length
      ? currentReportRows.map(row => '<tr>' + cols.map(c => `<td>${escapeHtml(row[c[0]] ?? '—')}</td>`).join('') + '</tr>').join('')
      : `<tr><td colspan="${cols.length}" class="empty-state">No data.</td></tr>`;
  } catch (err) {
    showToast(err.message || 'Failed to load report.', 'error');
  }
}

function exportReportCsv() {
  if (currentReportType === 'testing' || currentReportType === 'bugs') {
    showToast('This report is summary-only; switch to a tabular report to export.', 'warning');
    return;
  }
  const cols = REPORT_COLUMNS[currentReportType];
  if (!cols || !currentReportRows.length) { showToast('Nothing to export.', 'warning'); return; }
  const lines = [cols.map(c => c[1]).join(',')].concat(
    currentReportRows.map(row => cols.map(c => `"${(row[c[0]] ?? '').toString().replace(/"/g, '""')}"`).join(','))
  );
  downloadCsv(lines.join('\n'), currentReportType + '-report.csv');
}

document.addEventListener('DOMContentLoaded', () => {
  loadReport();
  document.getElementById('report-picker').addEventListener('change', loadReport);
  document.getElementById('export-report-btn').addEventListener('click', exportReportCsv);
});
