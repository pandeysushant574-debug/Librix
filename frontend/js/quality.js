/* ============================================================
   quality.js — Quality Overview (spec section 19): 4 primary cards
   ============================================================ */

function qualityCard(icon, title, rows) {
  return `<div class="quality-card glass">
    <div class="qc-icon">${icon}</div>
    <div class="qc-title">${title}</div>
    ${rows.map(r => `<div class="qc-row"><span>${r[0]}</span><b>${r[1]}</b></div>`).join('')}
  </div>`;
}

async function loadQualityOverview() {
  try {
    const [testing, bugs, boundary, logs] = await Promise.all([
      Api.get('/reports/testing'),
      Api.get('/reports/bugs'),
      Api.get('/boundary-tests'),
      Api.get('/logs', { counters: 1 }),
    ]);

    const boundaryTotal = boundary.length;
    const boundaryPassed = boundary.filter(b => b.status === 'PASS').length;
    const boundaryFailed = boundary.filter(b => b.status === 'FAIL').length;
    const boundaryRate = boundaryTotal ? Math.round((boundaryPassed / boundaryTotal) * 100) : 0;

    document.getElementById('quality-cards').innerHTML = [
      qualityCard('🧪', 'Unit Test Cases', [
        ['Total', testing.unit.total], ['Passed', testing.unit.passed],
        ['Failed', testing.unit.failed], ['Pass Rate', testing.unit.pass_rate + '%'],
      ]),
      qualityCard('🐞', 'Bug Log Matrix', [
        ['Total', bugs.total], ['Open', bugs.open_count],
        ['Critical', bugs.critical], ['Closed', bugs.closed],
      ]),
      qualityCard('📐', 'Input Bounds Testing', [
        ['Total', boundaryTotal], ['Passed', boundaryPassed],
        ['Failed', boundaryFailed], ['Pass Rate', boundaryRate + '%'],
      ]),
      qualityCard('🗒️', 'System Logs', [
        ['Today', logs.today], ['Warnings', logs.warnings],
        ['Errors', logs.errors], ['Debug', logs.debug],
      ]),
    ].join('');
  } catch (err) {
    showToast(err.message || 'Failed to load quality overview.', 'error');
  }
}

document.addEventListener('DOMContentLoaded', loadQualityOverview);
