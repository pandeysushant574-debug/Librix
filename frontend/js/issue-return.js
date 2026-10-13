/* ============================================================
   issue-return.js — Check-in/out toggle, issue & return forms,
   active issues list. All writes go through IssueController
   (transactional BEGIN/COMMIT/ROLLBACK on the backend).
   ============================================================ */

let isReturnMode = false;

function todayStr() { return new Date().toISOString().slice(0, 10); }

async function loadFormData() {
  try {
    const [members, books, issues] = await Promise.all([
      Api.get('/members', { status: 'Active' }),
      Api.get('/books'),
      Api.get('/issues', { status: 'Issued' }),
    ]);

    const memberSelect = document.getElementById('i-member');
    memberSelect.innerHTML = members.map(m => `<option value="${m.member_id}">${escapeHtml(m.member_code)} — ${escapeHtml(m.name)}</option>`).join('');

    const bookSelect = document.getElementById('i-book');
    bookSelect.innerHTML = books.filter(b => b.available_qty > 0)
      .map(b => `<option value="${b.book_id}">${escapeHtml(b.title)} (avail: ${b.available_qty})</option>`).join('')
      || '<option value="">No books currently available</option>';

    const issueSelect = document.getElementById('r-issue');
    issueSelect.innerHTML = issues.length
      ? issues.map(i => `<option value="${i.issue_id}">#${i.issue_id} — ${escapeHtml(i.book_title)} → ${escapeHtml(i.member_name)} (due ${i.due_date})</option>`).join('')
      : '<option value="">No active issues</option>';

    renderActiveIssues(issues);
  } catch (err) {
    showToast(err.message || 'Failed to load data.', 'error');
  }
}

function renderActiveIssues(issues) {
  const el = document.getElementById('active-issues-list');
  if (!issues.length) { el.innerHTML = '<div class="empty-state">No books currently issued.</div>'; return; }
  const today = todayStr();
  el.innerHTML = issues.map(i => {
    const overdue = i.due_date < today;
    return `<div class="recent-item">
      <div><div class="ri-title">${escapeHtml(i.book_title)}</div><div class="ri-sub">${escapeHtml(i.member_name)} · due ${i.due_date}</div></div>
      <span class="badge ${overdue ? 'badge-red' : 'badge-blue'}">${overdue ? 'Overdue' : 'Issued'}</span>
    </div>`;
  }).join('');
}

function setMode(returnMode) {
  isReturnMode = returnMode;
  document.getElementById('issue-panel').style.display = returnMode ? 'none' : 'block';
  document.getElementById('return-panel').style.display = returnMode ? 'block' : 'none';
  document.getElementById('mode-toggle').classList.toggle('on', !returnMode);
  document.getElementById('lbl-checkin').classList.toggle('active', !returnMode);
  document.getElementById('lbl-checkout').classList.toggle('active', returnMode);
}

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('i-issue-date').value = todayStr();
  document.getElementById('i-due-date').value = new Date(Date.now() + 7 * 86400000).toISOString().slice(0, 10);
  document.getElementById('r-return-date').value = todayStr();

  loadFormData();
  setMode(false);

  document.getElementById('mode-toggle').addEventListener('click', () => setMode(!isReturnMode));

  document.getElementById('issue-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      member_id: document.getElementById('i-member').value,
      book_id: document.getElementById('i-book').value,
      quantity: document.getElementById('i-qty').value,
      issue_date: document.getElementById('i-issue-date').value,
      due_date: document.getElementById('i-due-date').value,
    };
    try {
      await Api.post('/issues', payload);
      showToast('Book issued successfully.', 'success');
      document.getElementById('issue-form-error').textContent = '';
      loadFormData();
    } catch (err) {
      document.getElementById('issue-form-error').textContent = (err.errors && err.errors.join(' ')) || err.message;
    }
  });

  document.getElementById('return-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      issue_id: document.getElementById('r-issue').value,
      return_date: document.getElementById('r-return-date').value,
      condition_status: document.getElementById('r-condition').value,
      remarks: document.getElementById('r-remarks').value.trim() || null,
    };
    try {
      const result = await Api.post('/returns', payload);
      const fineMsg = parseFloat(result.fine_amount) > 0 ? ` A fine of ₹${result.fine_amount} was recorded.` : '';
      showToast('Book returned successfully.' + fineMsg, 'success');
      document.getElementById('return-form-error').textContent = '';
      document.getElementById('r-remarks').value = '';
      loadFormData();
    } catch (err) {
      document.getElementById('return-form-error').textContent = (err.errors && err.errors.join(' ')) || err.message;
    }
  });
});
