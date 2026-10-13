/* ============================================================
   books.js — Books CRUD, search, filter, sort, pagination, export
   ============================================================ */

let allBooks = [];
let bookSort = { key: 'title', dir: 1 };
let bookPage = 1;
const BOOK_PAGE_SIZE = 8;

async function loadBooks() {
  try {
    allBooks = await Api.get('/books');
    renderBooksTable();
  } catch (err) {
    showToast(err.message || 'Failed to load books.', 'error');
  }
}

function getFilteredBooks() {
  const q = document.getElementById('book-search').value.trim().toLowerCase();
  const status = document.getElementById('book-status-filter').value;
  let rows = allBooks.filter(b => {
    const matchesQ = !q || [b.title, b.author, b.isbn].some(v => (v || '').toLowerCase().includes(q));
    const matchesStatus = !status || b.status === status;
    return matchesQ && matchesStatus;
  });
  rows.sort((a, b) => {
    const va = a[bookSort.key] ?? '';
    const vb = b[bookSort.key] ?? '';
    return (va > vb ? 1 : va < vb ? -1 : 0) * bookSort.dir;
  });
  return rows;
}

function statusBadge(status) {
  const map = { Available: 'badge-green', Unavailable: 'badge-orange', Inactive: 'badge-gray' };
  return `<span class="badge ${map[status] || 'badge-gray'}">${status}</span>`;
}

function renderBooksTable() {
  const rows = getFilteredBooks();
  const totalPages = Math.max(1, Math.ceil(rows.length / BOOK_PAGE_SIZE));
  bookPage = Math.min(bookPage, totalPages);
  const pageRows = rows.slice((bookPage - 1) * BOOK_PAGE_SIZE, bookPage * BOOK_PAGE_SIZE);

  const tbody = document.getElementById('books-tbody');
  tbody.innerHTML = pageRows.length ? pageRows.map(b => `
    <tr class="clickable-row" title="Click to view details" onclick="showBookDetails(${b.book_id})">
      <td>${escapeHtml(b.title)}</td>
      <td>${escapeHtml(b.author)}</td>
      <td>${escapeHtml(b.category || '—')}</td>
      <td>${escapeHtml(b.isbn || '—')}</td>
      <td>${b.quantity}</td>
      <td>${b.available_qty}</td>
      <td>${escapeHtml(b.shelf_location || '—')}</td>
      <td>${statusBadge(b.status)}</td>
      <td><div class="row-actions">
        <button class="btn-icon" title="Edit" onclick="event.stopPropagation(); editBook(${b.book_id})">✏️</button>
        <button class="btn-icon" title="Delete" onclick="event.stopPropagation(); deleteBook(${b.book_id})">🗑️</button>
      </div></td>
    </tr>`).join('') : `<tr><td colspan="9" class="empty-state">No books match your search.</td></tr>`;

  document.getElementById('books-pagination').innerHTML = `
    <span>${rows.length} book(s) — page ${bookPage} of ${totalPages}</span>
    <div class="pg-controls">
      <button onclick="changeBookPage(-1)" ${bookPage <= 1 ? 'disabled' : ''}>‹ Prev</button>
      <button onclick="changeBookPage(1)" ${bookPage >= totalPages ? 'disabled' : ''}>Next ›</button>
    </div>`;
}

function changeBookPage(delta) { bookPage += delta; renderBooksTable(); }

document.addEventListener('DOMContentLoaded', () => {
  loadBooks();
  document.getElementById('book-search').addEventListener('input', () => { bookPage = 1; renderBooksTable(); });
  document.getElementById('book-status-filter').addEventListener('change', () => { bookPage = 1; renderBooksTable(); });
  document.getElementById('add-book-btn').addEventListener('click', () => openBookModal());
  document.getElementById('export-books-btn').addEventListener('click', exportBooksCsv);
  document.querySelectorAll('#books-table thead th[data-key]').forEach(th => {
    th.addEventListener('click', () => {
      const key = th.dataset.key;
      bookSort.dir = bookSort.key === key ? -bookSort.dir : 1;
      bookSort.key = key;
      renderBooksTable();
    });
  });
});

function bookFormHtml(book) {
  const b = book || {};
  return `
    <div class="modal-header"><h3>${book ? 'Edit Book' : 'Add Book'}</h3><button class="modal-close" onclick="closeModal()">✕</button></div>
    <form id="book-form">
      <div class="form-grid">
        <div class="field span-2"><label>Title <span class="req">*</span></label><input type="text" id="f-title" value="${escapeHtml(b.title || '')}" required></div>
        <div class="field"><label>Author <span class="req">*</span></label><input type="text" id="f-author" value="${escapeHtml(b.author || '')}" required></div>
        <div class="field"><label>ISBN</label><input type="text" id="f-isbn" value="${escapeHtml(b.isbn || '')}"></div>
        <div class="field"><label>Category</label><input type="text" id="f-category" value="${escapeHtml(b.category || '')}"></div>
        <div class="field"><label>Publisher</label><input type="text" id="f-publisher" value="${escapeHtml(b.publisher || '')}"></div>
        <div class="field"><label>Edition</label><input type="text" id="f-edition" value="${escapeHtml(b.edition || '')}"></div>
        <div class="field"><label>Year Published</label><input type="number" id="f-year" value="${b.year_published || ''}"></div>
        <div class="field"><label>Quantity <span class="req">*</span></label><input type="number" id="f-quantity" min="0" max="9999" value="${b.quantity ?? 1}" required></div>
        <div class="field"><label>Available Qty</label><input type="number" id="f-available" min="0" value="${b.available_qty ?? ''}"></div>
        <div class="field"><label>Reorder Level</label><input type="number" id="f-reorder" min="0" value="${b.reorder_level ?? 2}"></div>
        <div class="field"><label>Shelf Location</label><input type="text" id="f-shelf" value="${escapeHtml(b.shelf_location || '')}"></div>
        <div class="field"><label>Status</label>
          <select id="f-status">
            <option ${b.status === 'Available' || !b.status ? 'selected' : ''}>Available</option>
            <option ${b.status === 'Unavailable' ? 'selected' : ''}>Unavailable</option>
            <option ${b.status === 'Inactive' ? 'selected' : ''}>Inactive</option>
          </select>
        </div>
        <div class="field span-2"><label>Description</label><textarea id="f-description" rows="6" maxlength="2000" placeholder="Basic overview of the book: what it is about, who it is for, key topics">${escapeHtml(b.description || '')}</textarea></div>
      </div>
      <div id="book-form-error" class="field-error"></div>
      <div class="form-actions">
        <button type="button" class="btn" onclick="closeModal()">Cancel</button>
        <button type="submit" class="btn btn-primary">${book ? 'Save Changes' : 'Add Book'}</button>
      </div>
    </form>`;
}

function openBookModal(book) {
  openModal(bookFormHtml(book));
  document.getElementById('book-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      title: document.getElementById('f-title').value.trim(),
      author: document.getElementById('f-author').value.trim(),
      isbn: document.getElementById('f-isbn').value.trim() || null,
      category: document.getElementById('f-category').value.trim() || null,
      publisher: document.getElementById('f-publisher').value.trim() || null,
      edition: document.getElementById('f-edition').value.trim() || null,
      year_published: document.getElementById('f-year').value || null,
      quantity: document.getElementById('f-quantity').value,
      available_qty: document.getElementById('f-available').value,
      reorder_level: document.getElementById('f-reorder').value,
      shelf_location: document.getElementById('f-shelf').value.trim() || null,
      status: document.getElementById('f-status').value,
      description: document.getElementById('f-description').value.trim() || null,
    };
    try {
      if (book) {
        await Api.put('/books/' + book.book_id, payload);
        showToast('Book updated.', 'success');
      } else {
        await Api.post('/books', payload);
        showToast('Book added.', 'success');
      }
      closeModal();
      loadBooks();
    } catch (err) {
      document.getElementById('book-form-error').textContent = (err.errors && err.errors.join(' ')) || err.message;
    }
  });
}

function showBookDetails(id) {
  const b = allBooks.find(x => x.book_id === id);
  if (!b) return;
  const total = Number(b.quantity) || 0, avail = Number(b.available_qty) || 0;
  const pct = total ? Math.round((avail / total) * 100) : 0;
  const detail = (label, value) => `<div class="bk-detail"><span class="bk-label">${label}</span><span class="bk-value">${escapeHtml(String(value ?? '—') || '—')}</span></div>`;
  openModal(`
    <div class="modal-header"><h3>📖 Book Details</h3><button class="modal-close" onclick="closeModal()">✕</button></div>
    <div class="bk-card">
      <div class="bk-title">${escapeHtml(b.title)}</div>
      <div class="bk-author">by ${escapeHtml(b.author)}</div>
      <div class="bk-tags">
        ${b.category ? `<span class="badge badge-blue">${escapeHtml(b.category)}</span>` : ''}
        ${statusBadge(b.status)}
      </div>
      <div class="bk-section-title">About this book</div>
      <p class="bk-desc">${b.description ? escapeHtml(b.description) : '<em>No description has been added for this book yet.</em>'}</p>
      <div class="bk-grid">
        ${detail('ISBN', b.isbn)}
        ${detail('Publisher', b.publisher)}
        ${detail('Edition', b.edition)}
        ${detail('Year', b.year_published)}
        ${detail('Shelf', b.shelf_location)}
        ${detail('Category', b.category)}
      </div>
      <div class="bk-section-title">Availability</div>
      <div class="bk-avail"><span><strong>${avail}</strong> of <strong>${total}</strong> copies available</span></div>
      <div class="progress-track"><div class="progress-fill" style="width:${pct}%"></div></div>
    </div>
    <div class="form-actions">
      <button type="button" class="btn" onclick="closeModal()">Close</button>
      <button type="button" class="btn btn-primary" onclick="editBook(${b.book_id})">✏️ Edit Book</button>
    </div>`);
}

function editBook(id) {
  const book = allBooks.find(b => b.book_id === id);
  if (book) openBookModal(book);
}

async function deleteBook(id) {
  if (!confirm('Delete this book? This cannot be undone.')) return;
  try {
    await Api.del('/books/' + id);
    showToast('Book deleted.', 'success');
    loadBooks();
  } catch (err) {
    showToast(err.message || 'Delete failed.', 'error');
  }
}

function exportBooksCsv() {
  const rows = getFilteredBooks();
  const header = ['Title', 'Author', 'Category', 'ISBN', 'Quantity', 'Available', 'Shelf', 'Status'];
  const lines = [header.join(',')].concat(rows.map(b =>
    [b.title, b.author, b.category, b.isbn, b.quantity, b.available_qty, b.shelf_location, b.status]
      .map(v => `"${(v ?? '').toString().replace(/"/g, '""')}"`).join(',')
  ));
  downloadCsv(lines.join('\n'), 'books.csv');
}
