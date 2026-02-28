/* ========================================================================
   Records Management System — App JavaScript
   Handles sidebar, modals, toasts, tabs, menus, and page interactions
   ======================================================================== */

// ── Sidebar Toggle ────────────────────────────────────────────
function toggleSidebar() {
  const sidebar = document.querySelector('.sidebar');
  if (sidebar) sidebar.classList.toggle('sidebar--collapsed');
}

// ── User Avatar Menu ──────────────────────────────────────────
function toggleUserMenu() {
  const dropdown = document.getElementById('user-dropdown');
  if (dropdown) dropdown.classList.toggle('visible');
}

// ── Notifications Panel ───────────────────────────────────────
function toggleNotifications() {
  const panel = document.getElementById('notifications-panel');
  if (panel) panel.classList.toggle('visible');
}

function markAllRead() {
  const items = document.querySelectorAll('.notification-item.unread');
  items.forEach(item => item.classList.remove('unread'));
  const badge = document.querySelector('.notification-badge');
  if (badge) badge.textContent = '0';
}

// ── Modal Management ──────────────────────────────────────────
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

// Close modals on Escape key
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') closeAllModals();
});

// Close modals on overlay click
document.addEventListener('click', (e) => {
  if (e.target.classList.contains('modal-overlay')) {
    e.target.classList.remove('visible');
  }
});

// ── Toast Notifications ───────────────────────────────────────
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

// ── Filter Panel ──────────────────────────────────────────────
function toggleFilters() {
  const panel = document.getElementById('filter-panel');
  if (panel) panel.classList.toggle('visible');
}

function applyFilters() {
  showToast('success', 'Filters applied successfully');
  toggleFilters();
}

function clearFilters() {
  const tags = document.getElementById('active-filter-tags');
  if (tags) tags.innerHTML = '';
  showToast('success', 'Filters cleared');
}

// ── Tabs ──────────────────────────────────────────────────────
function switchTab(tabName, groupId) {
  const group = groupId ? document.getElementById(groupId) : document;

  // Deactivate all tabs
  group.querySelectorAll('.tab').forEach(tab => tab.classList.remove('tab--active'));
  group.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

  // Activate selected tab
  const selectedTab = group.querySelector(`[data-tab="${tabName}"]`);
  const selectedContent = group.querySelector(`#tab-${tabName}`);

  if (selectedTab) selectedTab.classList.add('tab--active');
  if (selectedContent) selectedContent.classList.add('active');
}

// ── Actions Menu ──────────────────────────────────────────────
function toggleActionsMenu() {
  const dropdown = document.getElementById('actions-dropdown');
  if (dropdown) dropdown.classList.toggle('visible');
}

// ── Close dropdowns on outside click ──────────────────────────
document.addEventListener('click', (e) => {
  // Close user dropdown
  if (!e.target.closest('.user-menu-wrapper')) {
    const d = document.getElementById('user-dropdown');
    if (d) d.classList.remove('visible');
  }
  // Close notifications panel
  if (!e.target.closest('.notifications-wrapper')) {
    const n = document.getElementById('notifications-panel');
    if (n) n.classList.remove('visible');
  }
  // Close actions menu
  if (!e.target.closest('.actions-menu-wrapper')) {
    const a = document.getElementById('actions-dropdown');
    if (a) a.classList.remove('visible');
  }
});

// ── Form Validation (Demo) ────────────────────────────────────
function validateLoginForm(e) {
  e.preventDefault();
  const username = document.getElementById('input-username').value;
  const password = document.getElementById('input-password').value;
  const errorBanner = document.getElementById('alert-login-error');

  if (!username || !password) {
    if (errorBanner) {
      errorBanner.style.display = 'flex';
      errorBanner.querySelector('.alert-text').textContent = 'Please enter both username and password.';
    }
    return;
  }

  // Demo: simulate success
  if (errorBanner) errorBanner.style.display = 'none';
  showToast('success', 'Login successful! Redirecting...');
  setTimeout(() => {
    window.location.href = 'dashboard.html';
  }, 1200);
}

function validateRecordForm(e) {
  e.preventDefault();
  const title = document.getElementById('input-record-title');
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

  if (hasError) {
    if (errorSummary) {
      errorSummary.classList.add('visible');
      errorSummary.textContent = 'Please fix the highlighted errors before submitting.';
    }
    return;
  }

  showToast('success', 'Record created successfully!');
  setTimeout(() => {
    window.location.href = 'record-detail.html';
  }, 1200);
}

function submitForgotPassword(e) {
  e.preventDefault();
  const email = document.getElementById('input-reset-email').value;
  const alert = document.getElementById('alert-reset-sent');

  if (!email) {
    showToast('error', 'Please enter your email address.');
    return;
  }

  if (alert) alert.style.display = 'flex';
  showToast('success', 'Reset link sent to your email!');
}

// ── Search (Demo) ─────────────────────────────────────────────
function handleSearch(e) {
  const term = e.target.value.toLowerCase();
  const rows = document.querySelectorAll('tbody tr');
  let hasResults = false;

  rows.forEach(row => {
    const text = row.textContent.toLowerCase();
    const match = text.includes(term);
    row.style.display = match ? '' : 'none';
    if (match) hasResults = true;
  });

  const emptyState = document.getElementById('empty-state-records');
  if (emptyState) {
    emptyState.style.display = hasResults ? 'none' : 'block';
  }
}

// ── Workflow Actions (Demo) ───────────────────────────────────
function submitForReview() {
  closeAllModals();
  updateStatusBadge('Pending Review', 'badge--pending');
  showToast('success', 'Record submitted for review');
}

function approveRecord() {
  closeAllModals();
  updateStatusBadge('Approved', 'badge--approved');
  showToast('success', 'Record approved');
}

function rejectRecord() {
  closeAllModals();
  updateStatusBadge('Rejected', 'badge--rejected');
  showToast('success', 'Record rejected');
}

function lockRecord() {
  closeAllModals();
  updateStatusBadge('Locked', 'badge--locked');
  showToast('success', 'Record locked');
}

function unlockRecord() {
  closeAllModals();
  updateStatusBadge('Approved', 'badge--approved');
  showToast('success', 'Record unlocked');
}

function deleteRecord() {
  closeAllModals();
  showToast('success', 'Record deleted');
  setTimeout(() => {
    window.location.href = 'records.html';
  }, 1200);
}

function archiveRecord() {
  closeAllModals();
  updateStatusBadge('Archived', 'badge--archived');
  showToast('success', 'Record archived');
}

function updateStatusBadge(text, className) {
  const badge = document.getElementById('status-badge');
  if (!badge) return;
  badge.className = 'badge';
  badge.classList.add(className);
  badge.textContent = text;
}

// ── Save Profile / Change Password (Demo) ─────────────────────
function saveProfile(e) {
  e.preventDefault();
  showToast('success', 'Profile saved successfully');
}

function changePassword(e) {
  e.preventDefault();
  showToast('success', 'Password changed successfully');
}

// ── Run Report (Demo) ─────────────────────────────────────────
function runReport() {
  const loading = document.getElementById('report-loading');
  const results = document.getElementById('report-results');

  if (loading) loading.style.display = 'flex';
  if (results) results.style.display = 'none';

  setTimeout(() => {
    if (loading) loading.style.display = 'none';
    if (results) results.style.display = 'block';
    showToast('success', 'Report generated successfully');
  }, 1500);
}

// ── Active nav highlighting ───────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const currentPage = window.location.pathname.split('/').pop() || 'dashboard.html';
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
});
