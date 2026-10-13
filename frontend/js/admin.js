/* ============================================================
   admin.js — Admin > Users screen
   ============================================================ */

let allUsers = [];

async function loadUsers() {
  try {
    allUsers = await Api.get('/users');
    renderUsersTable();
  } catch (err) {
    showToast(err.message || 'Failed to load users.', 'error');
  }
}

function renderUsersTable() {
  document.getElementById('users-tbody').innerHTML = allUsers.length ? allUsers.map(u => `
    <tr>
      <td>${escapeHtml(u.name)}</td>
      <td>${escapeHtml(u.username)}</td>
      <td><span class="badge badge-blue">${escapeHtml(u.role)}</span></td>
      <td><span class="badge ${u.status === 'Active' ? 'badge-green' : 'badge-gray'}">${u.status}</span></td>
      <td>${escapeHtml(u.email || '—')}</td>
      <td>${escapeHtml((u.created_at || '').slice(0, 10))}</td>
      <td><button class="btn btn-sm" onclick="toggleUserStatus(${u.user_id}, '${u.status === 'Active' ? 'Inactive' : 'Active'}')">
        ${u.status === 'Active' ? 'Deactivate' : 'Activate'}
      </button></td>
    </tr>`).join('') : '<tr><td colspan="7" class="empty-state">No users found.</td></tr>';
}

async function toggleUserStatus(id, status) {
  try {
    await Api.put('/users/' + id + '/status', { status });
    showToast('User status updated.', 'success');
    loadUsers();
  } catch (err) {
    showToast(err.message || 'Update failed.', 'error');
  }
}

function userFormHtml() {
  return `
    <div class="modal-header"><h3>Add User</h3><button class="modal-close" onclick="closeModal()">✕</button></div>
    <form id="user-form">
      <div class="form-grid">
        <div class="field"><label>Name <span class="req">*</span></label><input type="text" id="u-name" required></div>
        <div class="field"><label>Username <span class="req">*</span></label><input type="text" id="u-username" required></div>
        <div class="field"><label>Password <span class="req">*</span></label><input type="password" id="u-password" required></div>
        <div class="field"><label>Role <span class="req">*</span></label>
          <select id="u-role"><option>Admin</option><option>Librarian</option><option>Assistant</option></select></div>
        <div class="field"><label>Email</label><input type="email" id="u-email"></div>
        <div class="field"><label>Phone</label><input type="text" id="u-phone"></div>
      </div>
      <div id="user-form-error" class="field-error"></div>
      <div class="form-actions">
        <button type="button" class="btn" onclick="closeModal()">Cancel</button>
        <button type="submit" class="btn btn-primary">Add User</button>
      </div>
    </form>`;
}

document.addEventListener('DOMContentLoaded', () => {
  loadUsers();
  document.getElementById('add-user-btn').addEventListener('click', () => {
    openModal(userFormHtml());
    document.getElementById('user-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const payload = {
        name: document.getElementById('u-name').value.trim(),
        username: document.getElementById('u-username').value.trim(),
        password: document.getElementById('u-password').value,
        role: document.getElementById('u-role').value,
        email: document.getElementById('u-email').value.trim() || null,
        phone: document.getElementById('u-phone').value.trim() || null,
      };
      try {
        await Api.post('/users', payload);
        showToast('User created.', 'success');
        closeModal();
        loadUsers();
      } catch (err) {
        document.getElementById('user-form-error').textContent = err.message;
      }
    });
  });
});
