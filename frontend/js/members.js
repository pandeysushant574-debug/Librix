/* ============================================================
   members.js — Members CRUD, search, filter, sort, pagination
   ============================================================ */

let allMembers = [];
let memberSort = { key: 'name', dir: 1 };
let memberPage = 1;
const MEMBER_PAGE_SIZE = 8;

async function loadMembers() {
  try {
    allMembers = await Api.get('/members');
    renderMembersTable();
  } catch (err) {
    showToast(err.message || 'Failed to load members.', 'error');
  }
}

function getFilteredMembers() {
  const q = document.getElementById('member-search').value.trim().toLowerCase();
  const status = document.getElementById('member-status-filter').value;
  let rows = allMembers.filter(m => {
    const matchesQ = !q || [m.name, m.member_code, m.email].some(v => (v || '').toLowerCase().includes(q));
    const matchesStatus = !status || m.status === status;
    return matchesQ && matchesStatus;
  });
  rows.sort((a, b) => {
    const va = a[memberSort.key] ?? '';
    const vb = b[memberSort.key] ?? '';
    return (va > vb ? 1 : va < vb ? -1 : 0) * memberSort.dir;
  });
  return rows;
}

function renderMembersTable() {
  const rows = getFilteredMembers();
  const totalPages = Math.max(1, Math.ceil(rows.length / MEMBER_PAGE_SIZE));
  memberPage = Math.min(memberPage, totalPages);
  const pageRows = rows.slice((memberPage - 1) * MEMBER_PAGE_SIZE, memberPage * MEMBER_PAGE_SIZE);

  document.getElementById('members-tbody').innerHTML = pageRows.length ? pageRows.map(m => `
    <tr>
      <td>${escapeHtml(m.member_code)}</td>
      <td>${escapeHtml(m.name)}</td>
      <td>${escapeHtml(m.email || '—')}</td>
      <td>${escapeHtml(m.phone || '—')}</td>
      <td>${escapeHtml(m.membership_date)}</td>
      <td><span class="badge ${m.status === 'Active' ? 'badge-green' : 'badge-gray'}">${m.status}</span></td>
      <td><div class="row-actions">
        <button class="btn-icon" title="Edit" onclick="editMember(${m.member_id})">✏️</button>
        <button class="btn-icon" title="Delete" onclick="deleteMember(${m.member_id})">🗑️</button>
      </div></td>
    </tr>`).join('') : `<tr><td colspan="7" class="empty-state">No members match your search.</td></tr>`;

  document.getElementById('members-pagination').innerHTML = `
    <span>${rows.length} member(s) — page ${memberPage} of ${totalPages}</span>
    <div class="pg-controls">
      <button onclick="changeMemberPage(-1)" ${memberPage <= 1 ? 'disabled' : ''}>‹ Prev</button>
      <button onclick="changeMemberPage(1)" ${memberPage >= totalPages ? 'disabled' : ''}>Next ›</button>
    </div>`;
}

function changeMemberPage(delta) { memberPage += delta; renderMembersTable(); }

document.addEventListener('DOMContentLoaded', () => {
  loadMembers();
  document.getElementById('member-search').addEventListener('input', () => { memberPage = 1; renderMembersTable(); });
  document.getElementById('member-status-filter').addEventListener('change', () => { memberPage = 1; renderMembersTable(); });
  document.getElementById('add-member-btn').addEventListener('click', () => openMemberModal());
  document.getElementById('export-members-btn').addEventListener('click', exportMembersCsv);
  document.querySelectorAll('#members-table thead th[data-key]').forEach(th => {
    th.addEventListener('click', () => {
      const key = th.dataset.key;
      memberSort.dir = memberSort.key === key ? -memberSort.dir : 1;
      memberSort.key = key;
      renderMembersTable();
    });
  });
});

function memberFormHtml(member) {
  const m = member || {};
  return `
    <div class="modal-header"><h3>${member ? 'Edit Member' : 'Add Member'}</h3><button class="modal-close" onclick="closeModal()">✕</button></div>
    <form id="member-form">
      <div class="form-grid">
        <div class="field"><label>Member Code <span class="req">*</span></label>
          <input type="text" id="f-code" placeholder="MEM-0001" value="${escapeHtml(m.member_code || '')}" ${member ? 'readonly' : ''} required></div>
        <div class="field"><label>Name <span class="req">*</span></label><input type="text" id="f-name" value="${escapeHtml(m.name || '')}" required></div>
        <div class="field"><label>Email</label><input type="email" id="f-email" value="${escapeHtml(m.email || '')}"></div>
        <div class="field"><label>Phone</label><input type="text" id="f-phone" value="${escapeHtml(m.phone || '')}"></div>
        <div class="field"><label>Membership Date <span class="req">*</span></label><input type="date" id="f-mdate" value="${m.membership_date || ''}" required></div>
        <div class="field"><label>Expiry Date</label><input type="date" id="f-edate" value="${m.expiry_date || ''}"></div>
        <div class="field span-2"><label>Address</label><textarea id="f-address">${escapeHtml(m.address || '')}</textarea></div>
        <div class="field"><label>Status</label>
          <select id="f-status">
            <option ${m.status === 'Active' || !m.status ? 'selected' : ''}>Active</option>
            <option ${m.status === 'Inactive' ? 'selected' : ''}>Inactive</option>
          </select>
        </div>
      </div>
      <div id="member-form-error" class="field-error"></div>
      <div class="form-actions">
        <button type="button" class="btn" onclick="closeModal()">Cancel</button>
        <button type="submit" class="btn btn-primary">${member ? 'Save Changes' : 'Add Member'}</button>
      </div>
    </form>`;
}

function openMemberModal(member) {
  openModal(memberFormHtml(member));
  document.getElementById('member-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      member_code: document.getElementById('f-code').value.trim(),
      name: document.getElementById('f-name').value.trim(),
      email: document.getElementById('f-email').value.trim() || null,
      phone: document.getElementById('f-phone').value.trim() || null,
      membership_date: document.getElementById('f-mdate').value,
      expiry_date: document.getElementById('f-edate').value || null,
      address: document.getElementById('f-address').value.trim() || null,
      status: document.getElementById('f-status').value,
    };
    try {
      if (member) {
        await Api.put('/members/' + member.member_id, payload);
        showToast('Member updated.', 'success');
      } else {
        await Api.post('/members', payload);
        showToast('Member added.', 'success');
      }
      closeModal();
      loadMembers();
    } catch (err) {
      document.getElementById('member-form-error').textContent = (err.errors && err.errors.join(' ')) || err.message;
    }
  });
}

function editMember(id) {
  const member = allMembers.find(m => m.member_id === id);
  if (member) openMemberModal(member);
}

async function deleteMember(id) {
  if (!confirm('Remove this member?')) return;
  try {
    await Api.del('/members/' + id);
    showToast('Member removed.', 'success');
    loadMembers();
  } catch (err) {
    showToast(err.message || 'Delete failed.', 'error');
  }
}

function exportMembersCsv() {
  const rows = getFilteredMembers();
  const header = ['Code', 'Name', 'Email', 'Phone', 'Membership Date', 'Status'];
  const lines = [header.join(',')].concat(rows.map(m =>
    [m.member_code, m.name, m.email, m.phone, m.membership_date, m.status]
      .map(v => `"${(v ?? '').toString().replace(/"/g, '""')}"`).join(',')
  ));
  downloadCsv(lines.join('\n'), 'members.csv');
}
