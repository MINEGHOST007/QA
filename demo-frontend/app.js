/* ========================================================================
   Records Management System — App JavaScript
   Fully functional with DataStore (localStorage-backed JSON storage)
   ======================================================================== */

// ── Session Guard ─────────────────────────────────────────────────────
(function sessionGuard() {
  const page = window.location.pathname.split('/').pop() || '';
  const publicPages = ['login.html', 'forgot-password.html', ''];
  if (!publicPages.includes(page) && !DataStore.getCurrentUser()) {
    window.location.href = 'login.html';
  }
})();

// ── Sidebar Toggle ────────────────────────────────────────────────────
function toggleSidebar() {
  const sidebar = document.querySelector('.sidebar');
  if (sidebar) sidebar.classList.toggle('sidebar--collapsed');
}

// ── User Avatar Menu ──────────────────────────────────────────────────
function toggleUserMenu() {
  const dropdown = document.getElementById('user-dropdown');
  if (dropdown) dropdown.classList.toggle('visible');
}

// ── Notifications Panel ───────────────────────────────────────────────
function toggleNotifications() {
  const panel = document.getElementById('notifications-panel');
  if (panel) panel.classList.toggle('visible');
}

function markAllRead() {
  const currentUser = DataStore.getCurrentUser();
  if (currentUser) DataStore.markAllNotificationsRead(currentUser.id);
  const items = document.querySelectorAll('.notification-item.unread');
  items.forEach(item => item.classList.remove('unread'));
  const badge = document.querySelector('.notification-badge');
  if (badge) badge.textContent = '0';
}

// ── Modal Management ──────────────────────────────────────────────────
function openModal(modalId) {
  const overlay = document.getElementById(modalId);
  if (overlay) overlay.classList.add('visible');
}

function closeModal(modalId) {
  const overlay = document.getElementById(modalId);
  if (overlay) overlay.classList.remove('visible');
}

function closeAllModals() {
  document.querySelectorAll('.modal-overlay').forEach(m => m.classList.remove('visible'));
}

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') closeAllModals();
});

document.addEventListener('click', (e) => {
  if (e.target.classList.contains('modal-overlay')) {
    e.target.classList.remove('visible');
  }
});

// ── Toast Notifications ───────────────────────────────────────────────
function showToast(type, message) {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.setAttribute('data-testid', `toast-${type}`);
  const icons = { success: '✓', error: '✕', warning: '⚠' };
  toast.innerHTML = `
    <span>${icons[type] || '●'}</span>
    <span>${message}</span>
    <button class="toast-dismiss" onclick="this.parentElement.remove()">×</button>
  `;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

// ── Close dropdowns on outside click ──────────────────────────────────
document.addEventListener('click', (e) => {
  if (!e.target.closest('.user-menu-wrapper')) {
    const d = document.getElementById('user-dropdown');
    if (d) d.classList.remove('visible');
  }
  if (!e.target.closest('.notifications-wrapper')) {
    const n = document.getElementById('notifications-panel');
    if (n) n.classList.remove('visible');
  }
  if (!e.target.closest('.actions-menu-wrapper')) {
    const a = document.getElementById('actions-dropdown');
    if (a) a.classList.remove('visible');
  }
});

// ── Tabs ──────────────────────────────────────────────────────────────
function switchTab(tabName, groupId) {
  const group = groupId ? document.getElementById(groupId) : document;
  group.querySelectorAll('.tab').forEach(tab => tab.classList.remove('tab--active'));
  group.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
  const selectedTab = group.querySelector(`[data-tab="${tabName}"]`);
  const selectedContent = group.querySelector(`#tab-${tabName}`);
  if (selectedTab) selectedTab.classList.add('tab--active');
  if (selectedContent) selectedContent.classList.add('active');
}

// ── Actions Menu ──────────────────────────────────────────────────────
function toggleActionsMenu() {
  const dropdown = document.getElementById('actions-dropdown');
  if (dropdown) dropdown.classList.toggle('visible');
}

// ═══════════════════════════════════════════════════════════════════════
//  HELPER: Status badge rendering
// ═══════════════════════════════════════════════════════════════════════
function getStatusBadgeClass(status) {
  const map = {
    'Draft': 'badge--draft',
    'Pending Review': 'badge--pending',
    'Approved': 'badge--approved',
    'Rejected': 'badge--rejected',
    'Locked': 'badge--locked',
    'Archived': 'badge--archived'
  };
  return map[status] || 'badge--draft';
}

function getStatusBadgeHTML(status) {
  const cls = getStatusBadgeClass(status);
  const prefix = status === 'Locked' ? '🔒 ' : '';
  return `<span class="badge ${cls}">${prefix}${status}</span>`;
}

function getPriorityHTML(priority) {
  const colorMap = {
    'Critical': 'var(--danger)',
    'High': 'var(--danger)',
    'Medium': 'var(--warning)',
    'Low': 'var(--text-muted)'
  };
  const color = colorMap[priority] || 'var(--text-muted)';
  return `<span style="color:${color};">● ${priority}</span>`;
}

// ═══════════════════════════════════════════════════════════════════════
//  HELPER: Update user display across all pages
// ═══════════════════════════════════════════════════════════════════════
function updateUserDisplay() {
  const user = DataStore.getCurrentUser();
  if (!user) return;

  const initials = (user.firstName[0] || '') + (user.lastName[0] || '');
  document.querySelectorAll('.user-avatar').forEach(el => { el.textContent = initials; });
  document.querySelectorAll('[data-testid="user-display-name"]').forEach(el => { el.textContent = `${user.firstName} ${user.lastName}`; });
  document.querySelectorAll('[data-testid="user-role-badge"]').forEach(el => { el.textContent = user.role; });

  // Update notification count
  const count = DataStore.getUnreadCount(user.id);
  document.querySelectorAll('[data-testid="notification-unread-count"]').forEach(el => { el.textContent = count; });
}


// ═══════════════════════════════════════════════════════════════════════
//  LOGIN PAGE
// ═══════════════════════════════════════════════════════════════════════
function validateLoginForm(e) {
  e.preventDefault();
  const username = document.getElementById('input-username').value.trim();
  const password = document.getElementById('input-password').value;
  const errorBanner = document.getElementById('alert-login-error');

  if (!username || !password) {
    if (errorBanner) {
      errorBanner.style.display = 'flex';
      errorBanner.querySelector('.alert-text').textContent = 'Please enter both username and password.';
    }
    return;
  }

  const user = DataStore.authenticateUser(username, password);
  if (!user) {
    if (errorBanner) {
      errorBanner.style.display = 'flex';
      errorBanner.querySelector('.alert-text').textContent = 'Invalid username or password.';
    }
    return;
  }

  if (errorBanner) errorBanner.style.display = 'none';
  DataStore.setCurrentUser(user.id);
  showToast('success', 'Login successful! Redirecting...');
  setTimeout(() => { window.location.href = 'dashboard.html'; }, 1200);
}

function submitForgotPassword(e) {
  e.preventDefault();
  const email = document.getElementById('input-reset-email').value;
  const alert = document.getElementById('alert-reset-sent');
  if (!email) { showToast('error', 'Please enter your email address.'); return; }
  if (alert) alert.style.display = 'flex';
  showToast('success', 'Reset link sent to your email!');
}


// ═══════════════════════════════════════════════════════════════════════
//  DASHBOARD PAGE
// ═══════════════════════════════════════════════════════════════════════
function renderDashboard() {
  const statsGrid = document.getElementById('dashboard-stats');
  const activityTbody = document.getElementById('dashboard-activity-tbody');
  if (!statsGrid && !activityTbody) return;

  const stats = DataStore.getDashboardStats();

  if (statsGrid) {
    statsGrid.innerHTML = `
      <div class="card stat-card stat-purple">
        <div class="stat-label">Total Records</div>
        <div class="stat-value">${stats.total}</div>
      </div>
      <div class="card stat-card stat-green">
        <div class="stat-label">Approved</div>
        <div class="stat-value">${stats.approved}</div>
      </div>
      <div class="card stat-card stat-yellow">
        <div class="stat-label">Pending Review</div>
        <div class="stat-value">${stats.pending}</div>
      </div>
      <div class="card stat-card stat-blue">
        <div class="stat-label">Locked</div>
        <div class="stat-value">${stats.locked}</div>
      </div>
    `;
  }

  if (activityTbody) {
    const records = DataStore.getRecords();
    const recent = records.slice(0, 5);
    activityTbody.innerHTML = recent.map(r => `
      <tr onclick="window.location.href='record-detail.html?id=${r.id}'" style="cursor:pointer;">
        <td><strong>${r.title}</strong></td>
        <td>${r.type}</td>
        <td>${getStatusBadgeHTML(r.status)}</td>
        <td>${DataStore.getAssigneeName(r.assigneeId)}</td>
        <td>${DataStore.formatDateTime(r.updatedAt)}</td>
      </tr>
    `).join('');
  }
}


// ═══════════════════════════════════════════════════════════════════════
//  RECORDS LIST PAGE
// ═══════════════════════════════════════════════════════════════════════
let recordsState = {
  page: 1,
  pageSize: 10,
  search: '',
  filterStatus: '',
  filterType: '',
  filterDateFrom: '',
  filterDateTo: '',
  showArchived: false,
  sortBy: '',
  sortDir: 'asc'
};

function renderRecordsList() {
  const tbody = document.getElementById('records-tbody');
  if (!tbody) return;

  const filters = {
    search: recordsState.search,
    status: recordsState.filterStatus,
    type: recordsState.filterType,
    dateFrom: recordsState.filterDateFrom,
    dateTo: recordsState.filterDateTo,
    showArchived: recordsState.showArchived,
    sortBy: recordsState.sortBy,
    sortDir: recordsState.sortDir
  };

  const allRecords = DataStore.getRecords(filters);
  const totalRecords = allRecords.length;
  const totalPages = Math.max(1, Math.ceil(totalRecords / recordsState.pageSize));
  if (recordsState.page > totalPages) recordsState.page = totalPages;

  const start = (recordsState.page - 1) * recordsState.pageSize;
  const pageRecords = allRecords.slice(start, start + recordsState.pageSize);

  const emptyState = document.getElementById('empty-state-records');
  const tableContainer = document.querySelector('[data-testid="records-table"]');

  if (totalRecords === 0) {
    if (emptyState) emptyState.style.display = 'block';
    if (tableContainer) tableContainer.style.display = 'none';
    return;
  } else {
    if (emptyState) emptyState.style.display = 'none';
    if (tableContainer) tableContainer.style.display = '';
  }

  tbody.innerHTML = pageRecords.map(r => `
    <tr data-testid="records-table-row" onclick="window.location.href='record-detail.html?id=${r.id}'" style="cursor:pointer;">
      <td><strong>${r.title}</strong></td>
      <td>${r.type}</td>
      <td>${getStatusBadgeHTML(r.status)}</td>
      <td>${DataStore.getAssigneeName(r.assigneeId)}</td>
      <td>${getPriorityHTML(r.priority)}</td>
      <td>${DataStore.formatDate(r.dueDate)}</td>
      <td>
        <div class="row-actions">
          <button class="btn btn-icon btn-sm" data-testid="btn-view-record" title="View" onclick="event.stopPropagation();window.location.href='record-detail.html?id=${r.id}'">👁</button>
          ${r.status !== 'Locked' ? `<button class="btn btn-icon btn-sm" data-testid="btn-edit-record" title="Edit" onclick="event.stopPropagation();window.location.href='record-form.html?id=${r.id}'">✏</button>` : ''}
        </div>
      </td>
    </tr>
  `).join('');

  // Pagination
  const paginationEl = document.getElementById('records-pagination-info');
  if (paginationEl) {
    paginationEl.textContent = `Showing ${start + 1}-${Math.min(start + recordsState.pageSize, totalRecords)} of ${totalRecords} records`;
  }

  const pagesContainer = document.getElementById('records-pagination-pages');
  if (pagesContainer) {
    let pagesHTML = `<button class="page-btn" data-testid="btn-page-prev" onclick="changePage(${recordsState.page - 1})" ${recordsState.page <= 1 ? 'disabled' : ''}>←</button>`;
    for (let i = 1; i <= totalPages; i++) {
      pagesHTML += `<button class="page-btn ${i === recordsState.page ? 'active' : ''}" onclick="changePage(${i})">${i}</button>`;
    }
    pagesHTML += `<button class="page-btn" data-testid="btn-page-next" onclick="changePage(${recordsState.page + 1})" ${recordsState.page >= totalPages ? 'disabled' : ''}>→</button>`;
    pagesContainer.innerHTML = pagesHTML;
  }
}

function changePage(page) {
  const allRecords = DataStore.getRecords({ showArchived: recordsState.showArchived });
  const totalPages = Math.max(1, Math.ceil(allRecords.length / recordsState.pageSize));
  if (page < 1 || page > totalPages) return;
  recordsState.page = page;
  renderRecordsList();
}

function handleSearch(e) {
  recordsState.search = e.target.value;
  recordsState.page = 1;
  renderRecordsList();
}

function toggleFilters() {
  const panel = document.getElementById('filter-panel');
  if (panel) panel.classList.toggle('visible');
}

function applyFilters() {
  const statusEl = document.querySelector('[data-testid="filter-status"]');
  const typeEl = document.querySelector('[data-testid="filter-type"]');
  const fromEl = document.querySelector('[data-testid="filter-date-from"]');
  const toEl = document.querySelector('[data-testid="filter-date-to"]');

  recordsState.filterStatus = statusEl ? statusEl.value : '';
  recordsState.filterType = typeEl ? typeEl.value : '';
  recordsState.filterDateFrom = fromEl ? fromEl.value : '';
  recordsState.filterDateTo = toEl ? toEl.value : '';
  recordsState.page = 1;

  // Update active filter tags
  const tagsContainer = document.getElementById('active-filter-tags');
  if (tagsContainer) {
    let tags = '';
    if (recordsState.filterStatus) tags += `<span class="filter-tag">Status: ${recordsState.filterStatus} <span class="remove-tag" onclick="recordsState.filterStatus='';this.parentElement.remove();renderRecordsList()">×</span></span>`;
    if (recordsState.filterType) tags += `<span class="filter-tag">Type: ${recordsState.filterType} <span class="remove-tag" onclick="recordsState.filterType='';this.parentElement.remove();renderRecordsList()">×</span></span>`;
    if (recordsState.filterDateFrom) tags += `<span class="filter-tag">From: ${recordsState.filterDateFrom} <span class="remove-tag" onclick="recordsState.filterDateFrom='';this.parentElement.remove();renderRecordsList()">×</span></span>`;
    if (recordsState.filterDateTo) tags += `<span class="filter-tag">To: ${recordsState.filterDateTo} <span class="remove-tag" onclick="recordsState.filterDateTo='';this.parentElement.remove();renderRecordsList()">×</span></span>`;
    tagsContainer.innerHTML = tags;
  }

  renderRecordsList();
  toggleFilters();
  showToast('success', 'Filters applied successfully');
}

function clearFilters() {
  recordsState.filterStatus = '';
  recordsState.filterType = '';
  recordsState.filterDateFrom = '';
  recordsState.filterDateTo = '';
  recordsState.page = 1;

  const statusEl = document.querySelector('[data-testid="filter-status"]');
  const typeEl = document.querySelector('[data-testid="filter-type"]');
  const fromEl = document.querySelector('[data-testid="filter-date-from"]');
  const toEl = document.querySelector('[data-testid="filter-date-to"]');
  if (statusEl) statusEl.value = '';
  if (typeEl) typeEl.value = '';
  if (fromEl) fromEl.value = '';
  if (toEl) toEl.value = '';

  const tags = document.getElementById('active-filter-tags');
  if (tags) tags.innerHTML = '';
  renderRecordsList();
  showToast('success', 'Filters cleared');
}

function handleSort(column) {
  if (recordsState.sortBy === column) {
    recordsState.sortDir = recordsState.sortDir === 'asc' ? 'desc' : 'asc';
  } else {
    recordsState.sortBy = column;
    recordsState.sortDir = 'asc';
  }

  // Update sort icons
  document.querySelectorAll('.sort-icon').forEach(el => { el.className = 'sort-icon'; });
  const th = document.querySelector(`[data-testid="th-sort-${column}"] .sort-icon`);
  if (th) th.className = `sort-icon sort--${recordsState.sortDir}`;

  renderRecordsList();
}

function handlePageSizeChange(e) {
  recordsState.pageSize = parseInt(e.target.value) || 10;
  recordsState.page = 1;
  renderRecordsList();
}

function handleShowArchived(e) {
  recordsState.showArchived = e.target.checked;
  recordsState.page = 1;
  renderRecordsList();
}


// ═══════════════════════════════════════════════════════════════════════
//  RECORD DETAIL PAGE
// ═══════════════════════════════════════════════════════════════════════
let currentRecordId = null;

function renderRecordDetail() {
  const params = new URLSearchParams(window.location.search);
  currentRecordId = params.get('id');
  if (!currentRecordId) {
    // Fallback to first record
    const recs = DataStore.getRecords();
    if (recs.length > 0) currentRecordId = recs[0].id;
    else return;
  }

  const record = DataStore.getRecordById(currentRecordId);
  if (!record) return;

  // Page title
  const titleEl = document.getElementById('record-detail-title');
  if (titleEl) titleEl.textContent = record.title;
  document.title = `${record.title} — Records Management System`;

  // Breadcrumb
  const breadcrumbCurrent = document.querySelector('.breadcrumb .current');
  if (breadcrumbCurrent) breadcrumbCurrent.textContent = record.title;

  // Status badge
  const badge = document.getElementById('status-badge');
  if (badge) {
    badge.className = `badge ${getStatusBadgeClass(record.status)}`;
    badge.textContent = record.status;
    badge.setAttribute('role', 'status');
  }

  // Lock icon
  const lockIcon = document.getElementById('record-lock-icon');
  if (lockIcon) lockIcon.className = record.status === 'Locked' ? '' : 'hidden';

  // Record meta
  const metaEl = document.getElementById('record-detail-meta');
  if (metaEl) {
    const creatorName = DataStore.getUserName(record.createdBy);
    metaEl.textContent = `Record #${record.id.replace('r', '10')} • Created by ${creatorName} on ${DataStore.formatDate(record.createdAt)}`;
  }

  // Detail fields
  const summaryEl = document.getElementById('record-summary-fields');
  if (summaryEl) {
    summaryEl.innerHTML = `
      <div style="display:grid; grid-template-columns:1fr 1fr; gap:var(--space-lg);">
        <div class="detail-field">
          <div class="detail-field-label">Title</div>
          <div class="detail-field-value">${record.title}</div>
        </div>
        <div class="detail-field">
          <div class="detail-field-label">Type</div>
          <div class="detail-field-value">${record.type}</div>
        </div>
        <div class="detail-field">
          <div class="detail-field-label">Priority</div>
          <div class="detail-field-value">${getPriorityHTML(record.priority)}</div>
        </div>
        <div class="detail-field">
          <div class="detail-field-label">Assignee</div>
          <div class="detail-field-value">${DataStore.getAssigneeName(record.assigneeId)}</div>
        </div>
        <div class="detail-field">
          <div class="detail-field-label">Due Date</div>
          <div class="detail-field-value">${DataStore.formatDateFull(record.dueDate)}</div>
        </div>
        <div class="detail-field">
          <div class="detail-field-label">Created</div>
          <div class="detail-field-value">${DataStore.formatDateFull(record.createdAt)}</div>
        </div>
      </div>
      <div class="detail-field" style="margin-top:var(--space-md);">
        <div class="detail-field-label">Description</div>
        <div class="detail-field-value" style="line-height:1.7;">${record.description || '<em>No description</em>'}</div>
      </div>
      <div class="detail-field" style="margin-top:var(--space-md);">
        <div class="detail-field-label">Attachments</div>
        <div class="detail-field-value">
          ${record.attachments.length > 0
            ? `<div style="display:flex; gap:var(--space-sm); flex-wrap:wrap;">${record.attachments.map(a => `<span class="filter-tag">📄 ${a} <span class="remove-tag">↓</span></span>`).join('')}</div>`
            : '<em>No attachments</em>'}
        </div>
      </div>
    `;
  }

  // Activity log
  const activityEl = document.getElementById('record-activity-log');
  if (activityEl) {
    const entries = DataStore.getActivityLog(currentRecordId);
    activityEl.innerHTML = entries.map(entry => {
      const userName = DataStore.getUserName(entry.userId);
      return `
        <div class="log-entry">
          <span class="log-dot created"></span>
          <div>
            <div class="log-text"><strong>${userName}</strong> ${entry.action}</div>
            <div class="log-meta">${DataStore.formatDateTime(entry.timestamp)}</div>
          </div>
        </div>
      `;
    }).join('');
  }

  // Edit button href
  const editBtn = document.querySelector('[data-testid="btn-edit-record"]');
  if (editBtn && editBtn.tagName === 'A') {
    editBtn.href = `record-form.html?id=${currentRecordId}`;
  }

  // Update delete modal text
  const deleteText = document.querySelector('#modal-confirm-delete .modal-body p');
  if (deleteText) deleteText.textContent = `Are you sure you want to delete "${record.title}"?`;
}

// Workflow actions
function submitForReview() {
  if (!currentRecordId) return;
  const comment = document.querySelector('[data-testid="input-workflow-comment"]');
  DataStore.updateRecordStatus(currentRecordId, 'Pending Review', comment ? comment.value : '');
  closeAllModals();
  showToast('success', 'Record submitted for review');
  renderRecordDetail();
}

function approveRecord() {
  if (!currentRecordId) return;
  const note = document.querySelector('[data-testid="input-approval-note"]');
  DataStore.updateRecordStatus(currentRecordId, 'Approved', note ? note.value : '');
  closeAllModals();
  showToast('success', 'Record approved');
  renderRecordDetail();
}

function rejectRecord() {
  if (!currentRecordId) return;
  const reason = document.querySelector('[data-testid="input-rejection-reason"]');
  DataStore.updateRecordStatus(currentRecordId, 'Rejected', reason ? reason.value : '');
  closeAllModals();
  showToast('success', 'Record rejected');
  renderRecordDetail();
}

function lockRecord() {
  if (!currentRecordId) return;
  DataStore.updateRecordStatus(currentRecordId, 'Locked');
  closeAllModals();
  showToast('success', 'Record locked');
  renderRecordDetail();
}

function unlockRecord() {
  if (!currentRecordId) return;
  const reason = document.querySelector('[data-testid="input-unlock-reason"]');
  DataStore.updateRecordStatus(currentRecordId, 'Approved', reason ? reason.value : '');
  closeAllModals();
  showToast('success', 'Record unlocked');
  renderRecordDetail();
}

function deleteRecord() {
  if (!currentRecordId) return;
  DataStore.deleteRecord(currentRecordId);
  closeAllModals();
  showToast('success', 'Record deleted');
  setTimeout(() => { window.location.href = 'records.html'; }, 1200);
}

function archiveRecord() {
  if (!currentRecordId) return;
  DataStore.updateRecordStatus(currentRecordId, 'Archived');
  closeAllModals();
  showToast('success', 'Record archived');
  renderRecordDetail();
}

function updateStatusBadge(text, className) {
  const badge = document.getElementById('status-badge');
  if (!badge) return;
  badge.className = 'badge';
  badge.classList.add(className);
  badge.textContent = text;
}


// ═══════════════════════════════════════════════════════════════════════
//  RECORD FORM PAGE (Create / Edit)
// ═══════════════════════════════════════════════════════════════════════
function initRecordForm() {
  const form = document.getElementById('record-form');
  if (!form) return;

  const params = new URLSearchParams(window.location.search);
  const editId = params.get('id');

  if (editId) {
    const record = DataStore.getRecordById(editId);
    if (record) {
      // Update page title
      const pageTitle = document.querySelector('.page-header h1');
      if (pageTitle) pageTitle.textContent = 'Edit Record';
      document.title = `Edit Record — Records Management System`;
      const breadcrumbCurrent = document.querySelector('.breadcrumb .current');
      if (breadcrumbCurrent) breadcrumbCurrent.textContent = 'Edit Record';

      // Fill form fields
      const titleInput = document.getElementById('input-record-title');
      if (titleInput) titleInput.value = record.title;
      const typeSelect = document.getElementById('select-record-type');
      if (typeSelect) typeSelect.value = record.type.toLowerCase() === 'hr document' ? 'hr' : record.type.toLowerCase();
      const assigneeSelect = document.getElementById('select-record-assignee');
      if (assigneeSelect) assigneeSelect.value = record.assigneeId ? DataStore.getUserById(record.assigneeId)?.username || '' : '';
      const prioritySelect = document.getElementById('select-record-priority');
      if (prioritySelect) prioritySelect.value = record.priority.toLowerCase();
      const dueDateInput = document.getElementById('datepicker-record-due-date');
      if (dueDateInput) dueDateInput.value = record.dueDate;
      const descInput = document.getElementById('textarea-record-description');
      if (descInput) descInput.value = record.description;

      form.dataset.editId = editId;
    }
  }

  // Populate assignee dropdown from data
  const assigneeSelect = document.getElementById('select-record-assignee');
  if (assigneeSelect) {
    const users = DataStore.getUsers().filter(u => u.status === 'Active');
    assigneeSelect.innerHTML = '<option value="">Select assignee…</option>' +
      users.map(u => `<option value="${u.id}" ${editId && DataStore.getRecordById(editId)?.assigneeId === u.id ? 'selected' : ''}>${u.firstName} ${u.lastName}</option>`).join('');
  }
}

function validateRecordForm(e) {
  e.preventDefault();
  const title = document.getElementById('input-record-title');
  const typeSelect = document.getElementById('select-record-type');
  const errorSummary = document.getElementById('form-error-summary');
  let hasError = false;

  // Reset errors
  document.querySelectorAll('.form-error').forEach(el => el.classList.remove('visible'));
  if (errorSummary) errorSummary.classList.remove('visible');

  if (!title || !title.value.trim()) {
    const err = document.getElementById('field-error-title');
    if (err) err.classList.add('visible');
    hasError = true;
  }

  if (!typeSelect || !typeSelect.value) {
    const err = document.querySelector('[data-testid="field-error-type"]');
    if (err) err.classList.add('visible');
    hasError = true;
  }

  if (hasError) {
    if (errorSummary) {
      errorSummary.classList.add('visible');
      errorSummary.textContent = 'Please fix the highlighted errors before submitting.';
    }
    return;
  }

  const typeMap = { compliance: 'Compliance', infrastructure: 'Infrastructure', hr: 'HR Document', policy: 'Policy', technical: 'Technical' };
  const assigneeSelect = document.getElementById('select-record-assignee');
  const prioritySelect = document.getElementById('select-record-priority');
  const dueDateInput = document.getElementById('datepicker-record-due-date');
  const descInput = document.getElementById('textarea-record-description');

  const data = {
    title: title.value.trim(),
    type: typeMap[typeSelect.value] || typeSelect.value,
    assigneeId: assigneeSelect ? assigneeSelect.value : '',
    priority: prioritySelect ? (prioritySelect.value.charAt(0).toUpperCase() + prioritySelect.value.slice(1)) : 'Medium',
    dueDate: dueDateInput ? dueDateInput.value : '',
    description: descInput ? descInput.value : ''
  };

  const form = document.getElementById('record-form');
  const editId = form ? form.dataset.editId : null;

  let record;
  if (editId) {
    record = DataStore.updateRecord(editId, data);
    showToast('success', 'Record updated successfully!');
  } else {
    record = DataStore.createRecord(data);
    showToast('success', 'Record created successfully!');
  }

  setTimeout(() => {
    window.location.href = `record-detail.html?id=${record.id}`;
  }, 1200);
}


// ═══════════════════════════════════════════════════════════════════════
//  SETTINGS PAGE
// ═══════════════════════════════════════════════════════════════════════
function initSettings() {
  const profileForm = document.querySelector('[data-testid="form-profile"]');
  if (!profileForm) return;

  const user = DataStore.getCurrentUser();
  if (!user) return;

  const setVal = (id, val) => { const el = document.getElementById(id); if (el) el.value = val || ''; };
  setVal('input-first-name', user.firstName);
  setVal('input-last-name', user.lastName);
  setVal('input-email', user.email);
  setVal('input-phone', user.phone);
  setVal('input-department', user.department);
  setVal('input-title', user.jobTitle);
  const bioEl = document.getElementById('textarea-bio');
  if (bioEl) bioEl.value = user.bio || '';
}

function saveProfile(e) {
  e.preventDefault();
  const data = {
    firstName: document.getElementById('input-first-name')?.value || '',
    lastName: document.getElementById('input-last-name')?.value || '',
    email: document.getElementById('input-email')?.value || '',
    phone: document.getElementById('input-phone')?.value || '',
    department: document.getElementById('input-department')?.value || '',
    jobTitle: document.getElementById('input-title')?.value || '',
    bio: document.getElementById('textarea-bio')?.value || ''
  };
  DataStore.saveProfile(data);
  updateUserDisplay();
  showToast('success', 'Profile saved successfully');
}

function changePassword(e) {
  e.preventDefault();
  const current = document.getElementById('input-current-password')?.value || '';
  const newPw = document.getElementById('input-new-password')?.value || '';
  const confirm = document.getElementById('input-confirm-password')?.value || '';

  if (!current || !newPw || !confirm) {
    showToast('error', 'Please fill in all password fields.');
    return;
  }
  if (newPw !== confirm) {
    showToast('error', 'New passwords do not match.');
    return;
  }
  if (newPw.length < 12) {
    showToast('error', 'Password must be at least 12 characters.');
    return;
  }

  const result = DataStore.changePassword(current, newPw);
  if (result.success) {
    showToast('success', 'Password changed successfully');
    document.getElementById('input-current-password').value = '';
    document.getElementById('input-new-password').value = '';
    document.getElementById('input-confirm-password').value = '';
  } else {
    showToast('error', result.error);
  }
}


// ═══════════════════════════════════════════════════════════════════════
//  ADMIN PAGE
// ═══════════════════════════════════════════════════════════════════════
function renderAdminUsers() {
  const tbody = document.getElementById('admin-users-tbody');
  if (!tbody) return;

  const users = DataStore.getUsers();
  const currentUser = DataStore.getCurrentUser();

  tbody.innerHTML = users.map(u => {
    const roleClassMap = { Admin: 'badge--approved', Reviewer: 'badge--locked', Editor: 'badge--pending', Viewer: 'badge--draft' };
    const roleClass = roleClassMap[u.role] || 'badge--draft';
    const statusColor = u.status === 'Active' ? 'var(--success)' : 'var(--text-muted)';
    const isCurrent = currentUser && u.id === currentUser.id;

    let actionHTML;
    if (isCurrent) {
      actionHTML = '<span class="text-muted" style="font-size:var(--font-size-xs);">Current user</span>';
    } else if (u.status === 'Active') {
      actionHTML = `<button class="btn btn-sm btn-danger" data-testid="action-deactivate-user-${u.id}" onclick="deactivateUser('${u.id}')">Deactivate</button>`;
    } else {
      actionHTML = `<button class="btn btn-sm btn-success" onclick="reactivateUser('${u.id}')">Reactivate</button>`;
    }

    return `
      <tr>
        <td><strong>${u.firstName} ${u.lastName}</strong></td>
        <td>${u.email}</td>
        <td><span class="badge ${roleClass}" style="text-transform:none;">${u.role}</span></td>
        <td><span style="color:${statusColor};">● ${u.status}</span></td>
        <td>${u.lastActive}</td>
        <td>${actionHTML}</td>
      </tr>
    `;
  }).join('');
}

function deactivateUser(id) {
  DataStore.deactivateUser(id);
  showToast('success', 'User deactivated');
  renderAdminUsers();
}

function reactivateUser(id) {
  DataStore.reactivateUser(id);
  showToast('success', 'User reactivated');
  renderAdminUsers();
}

function inviteUser() {
  const emailInput = document.getElementById('invite-email');
  const roleSelect = document.getElementById('invite-role');
  const email = emailInput ? emailInput.value.trim() : '';
  const role = roleSelect ? roleSelect.value : 'Viewer';

  if (!email) {
    showToast('error', 'Please enter an email address.');
    return;
  }

  DataStore.inviteUser(email, role);
  closeModal('modal-invite');
  showToast('success', 'Invitation sent!');
  if (emailInput) emailInput.value = '';
  renderAdminUsers();
}


// ═══════════════════════════════════════════════════════════════════════
//  REPORTS PAGE
// ═══════════════════════════════════════════════════════════════════════
function runReport() {
  const loading = document.getElementById('report-loading');
  const results = document.getElementById('report-results');

  if (loading) loading.style.display = 'flex';
  if (results) results.style.display = 'none';

  setTimeout(() => {
    if (loading) loading.style.display = 'none';

    const records = DataStore.getRecords();
    const total = records.length || 1;
    const approved = records.filter(r => r.status === 'Approved' || r.status === 'Locked').length;
    const pending = records.filter(r => r.status === 'Pending Review' || r.status === 'Draft').length;
    const rejected = records.filter(r => r.status === 'Rejected').length;

    const compPct = Math.round((approved / total) * 100);
    const pendPct = Math.round((pending / total) * 100);
    const nonPct = Math.round((rejected / total) * 100);

    // Update stats
    const statsEl = document.getElementById('report-stats');
    if (statsEl) {
      statsEl.innerHTML = `
        <div class="card stat-card stat-green" style="padding:var(--space-md);">
          <div class="stat-label">Compliant</div>
          <div class="stat-value" style="font-size:var(--font-size-xl);">${compPct}%</div>
        </div>
        <div class="card stat-card stat-yellow" style="padding:var(--space-md);">
          <div class="stat-label">Pending</div>
          <div class="stat-value" style="font-size:var(--font-size-xl);">${pendPct}%</div>
        </div>
        <div class="card stat-card stat-purple" style="padding:var(--space-md);">
          <div class="stat-label">Non-Compliant</div>
          <div class="stat-value" style="font-size:var(--font-size-xl);">${nonPct}%</div>
        </div>
      `;
    }

    // Update table
    const reportTbody = document.getElementById('report-results-tbody');
    if (reportTbody) {
      reportTbody.innerHTML = records.map(r => {
        let compliance = 'Pending Review';
        let compColor = 'var(--warning)';
        if (r.status === 'Approved' || r.status === 'Locked') { compliance = 'Compliant'; compColor = 'var(--success)'; }
        if (r.status === 'Rejected') { compliance = 'Non-Compliant'; compColor = 'var(--danger)'; }
        return `<tr><td>${r.title}</td><td>${getStatusBadgeHTML(r.status)}</td><td><span style="color:${compColor};">${compliance}</span></td><td>${DataStore.formatDate(r.dueDate)}</td></tr>`;
      }).join('');
    }

    if (results) results.style.display = 'block';
    showToast('success', 'Report generated successfully');
  }, 1500);
}


// ═══════════════════════════════════════════════════════════════════════
//  DOMContentLoaded — Initialize the current page
// ═══════════════════════════════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
  const currentPage = window.location.pathname.split('/').pop() || 'dashboard.html';

  // Active nav highlighting
  const navMap = {
    'dashboard.html': 'nav-item-dashboard',
    'records.html': 'nav-item-records',
    'record-detail.html': 'nav-item-records',
    'record-form.html': 'nav-item-records',
    'reports.html': 'nav-item-reports',
    'settings.html': 'nav-item-settings',
    'admin.html': 'nav-item-admin'
  };
  const activeId = navMap[currentPage];
  if (activeId) {
    const navItem = document.querySelector(`[data-testid="${activeId}"]`);
    if (navItem) navItem.classList.add('active');
  }

  // Update user display (header avatar, name, role)
  updateUserDisplay();

  // Page-specific init
  switch (currentPage) {
    case 'dashboard.html':
      renderDashboard();
      break;
    case 'records.html':
      // Initialize sort click handlers
      document.querySelectorAll('[data-testid^="th-sort-"]').forEach(th => {
        const col = th.getAttribute('data-testid').replace('th-sort-', '');
        th.style.cursor = 'pointer';
        th.addEventListener('click', () => handleSort(col));
      });
      // Initialize page size handler
      const pageSizeEl = document.querySelector('[data-testid="select-page-size"]');
      if (pageSizeEl) pageSizeEl.addEventListener('change', handlePageSizeChange);
      // Initialize show archived
      const archivedEl = document.querySelector('[data-testid="toggle-show-archived"]');
      if (archivedEl) archivedEl.addEventListener('change', handleShowArchived);
      // Clear initial filter tags
      const tags = document.getElementById('active-filter-tags');
      if (tags) tags.innerHTML = '';
      renderRecordsList();
      break;
    case 'record-detail.html':
      renderRecordDetail();
      break;
    case 'record-form.html':
      initRecordForm();
      break;
    case 'settings.html':
      initSettings();
      break;
    case 'admin.html':
      renderAdminUsers();
      break;
  }
});
