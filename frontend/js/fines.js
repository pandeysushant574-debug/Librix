/* ============================================================
   fines.js
   ============================================================ */

async function loadFines() {
  const status = document.getElementById('fine-status-filter').value;
  try {
    const fines = await Api.get('/fines', { status });
    const tbody = document.getElementById('fines-tbody');
    tbody.innerHTML = fines.length ? fines.map(f => `
      <tr>
        <td>${escapeHtml(f.member_name)} <span style="color:var(--text-muted)">(${escapeHtml(f.member_code)})</span></td>
        <td>${f.days_late}</td>
        <td>₹${f.rate_per_day}</td>
        <td>₹${f.amount}</td>
        <td><span class="badge ${f.status === 'Paid' ? 'badge-green' : f.status === 'Waived' ? 'badge-blue' : 'badge-red'}">${f.status}</span></td>
        <td>${escapeHtml((f.created_at || '').slice(0, 10))}</td>
        <td>${f.status === 'Unpaid' ? `<button class="btn btn-sm btn-primary" onclick="payFine(${f.fine_id})">Mark Paid</button>` : '—'}</td>
      </tr>`).join('') : '<tr><td colspan="7" class="empty-state">No fines found.</td></tr>';
  } catch (err) {
    showToast(err.message || 'Failed to load fines.', 'error');
  }
}

async function payFine(id) {
  if (!confirm('Mark this fine as paid?')) return;
  try {
    await Api.post('/fines/' + id + '/pay');
    showToast('Fine marked as paid.', 'success');
    loadFines();
  } catch (err) {
    showToast(err.message || 'Failed to update fine.', 'error');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  loadFines();
  document.getElementById('fine-status-filter').addEventListener('change', loadFines);
});
