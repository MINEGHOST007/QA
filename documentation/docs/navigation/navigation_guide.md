# Navigation Guide

This guide documents the step-by-step navigation paths, URLs, element selectors, and user-flow
sequences for every major feature in the application. Each section corresponds to a user-visible
workflow. The application is served as a static site via `http://localhost:8080`.

**Base URL**: `http://localhost:8080`

---

## Page Inventory

| Page                | File                  | Full URL                                      |
| ------------------- | --------------------- | --------------------------------------------- |
| Login               | `login.html`          | `http://localhost:8080/login.html`             |
| Forgot Password     | `forgot-password.html`| `http://localhost:8080/forgot-password.html`   |
| Dashboard           | `dashboard.html`      | `http://localhost:8080/dashboard.html`         |
| Records List        | `records.html`        | `http://localhost:8080/records.html`           |
| Record Detail       | `record-detail.html`  | `http://localhost:8080/record-detail.html`     |
| New / Edit Record   | `record-form.html`    | `http://localhost:8080/record-form.html`       |
| Reports             | `reports.html`        | `http://localhost:8080/reports.html`           |
| Settings            | `settings.html`       | `http://localhost:8080/settings.html`          |
| Admin Panel         | `admin.html`          | `http://localhost:8080/admin.html`             |

---

## Global Elements (present on all authenticated pages)

### Sidebar

**Selector**: `[data-testid="sidebar-nav"]`

| Menu Item   | `data-testid`          | Navigates To                                     | Label Text    |
| ----------- | ---------------------- | ------------------------------------------------ | ------------- |
| Dashboard   | `nav-item-dashboard`   | `dashboard.html`                                 | Dashboard     |
| Records     | `nav-item-records`     | `records.html`                                   | Records       |
| Reports     | `nav-item-reports`     | `reports.html`                                   | Reports       |
| Settings    | `nav-item-settings`    | `settings.html`                                  | Settings      |
| Admin Panel | `nav-item-admin`       | `admin.html`                                     | Admin Panel   |

**Toggle sidebar**: Click `[data-testid="btn-sidebar-toggle"]` (hamburger icon `☰` in the header).

### Header

| Element                | `data-testid`               | Type   | Notes                                              |
| ---------------------- | --------------------------- | ------ | -------------------------------------------------- |
| Breadcrumb             | `breadcrumb`                | `nav`  | Shows current location path                        |
| Notifications bell     | `btn-notifications`         | button | Toggles notification dropdown; has badge child     |
| Unread count badge     | `notification-unread-count` | span   | Displays count (e.g. `3`) inside the bell button   |
| Notification panel     | `notifications-panel`       | div    | Dropdown that opens on bell click                  |
| Mark all read          | `btn-mark-all-read`         | button | Inside notification panel; label: "Mark all read"  |
| User avatar            | `user-avatar-menu`          | button | Top-right; displays user initials (e.g. `JD`)     |
| User display name      | `user-display-name`         | div    | Inside user dropdown; shows "John Doe"             |
| User role badge        | `user-role-badge`           | span   | Inside user dropdown; shows role (e.g. "Admin")   |
| Sign Out               | `menu-item-logout`          | `a`    | Navigates to `login.html`; label: "🚪 Sign Out"   |

### Toast Notifications

**Container**: `#toast-container` (CSS class `toast-container`). Success/error toasts appear here after actions (submit, delete, save, etc.). Toast element has `data-testid="toast-success"` when triggered.

---

## Authentication

### Login

**URL**: `http://localhost:8080/login.html`  
**Page class**: `body.auth-page`

1. Navigate to `login.html`.
2. Enter username in `[data-testid="input-username"]` (type: `text`, placeholder: "Enter your username").
3. Enter password in `[data-testid="input-password"]` (type: `password`, placeholder: "Enter your password").
4. Click `[data-testid="btn-login"]` (type: `submit`, label: "Sign In", full-width primary button).
5. On success → redirects to `dashboard.html`.
6. On failure → error banner becomes visible at `[data-testid="alert-login-error"]` (initially `display:none`; text: "Invalid username or password.").

**Valid test credentials**: `admin` / `admin123`

### Logout

**Trigger**: Any authenticated page (dashboard, records, reports, settings, admin).

1. Click `[data-testid="user-avatar-menu"]` (top-right header, shows initials `JD`).
2. User dropdown opens (id: `user-dropdown`).
3. Click `[data-testid="menu-item-logout"]` (label: "🚪 Sign Out", `<a>` tag).
4. Navigates to `login.html`.

### Forgot Password

**URL**: `http://localhost:8080/forgot-password.html`  
**Page class**: `body.auth-page`

1. On the login page, click `[data-testid="link-forgot-password"]` (label: "Forgot your password?", `<a>` tag linking to `forgot-password.html`).
2. Enter email in `[data-testid="input-reset-email"]` (type: `email`, placeholder: "you@company.com").
3. Click `[data-testid="btn-send-reset"]` (type: `submit`, label: "Send Reset Link").
4. Confirmation message appears at `[data-testid="alert-reset-sent"]` (initially `display:none`; text: "A password reset link has been sent to your email address.").
5. Link "← Back to Sign In" navigates back to `login.html`.

---

## Dashboard

### Open Dashboard

**URL**: `http://localhost:8080/dashboard.html`

1. After login, the application navigates to `dashboard.html`.
2. Layout: sidebar at `[data-testid="sidebar-nav"]`, main panel at `[data-testid="main-content"]`.
3. Page heading: `<h1>Dashboard</h1>`.

### Dashboard Content

- **Stats grid**: Four stat cards (Total Records: `1,247`, Approved: `892`, Pending Review: `156`, Locked: `199`). CSS classes: `stat-purple`, `stat-green`, `stat-yellow`, `stat-blue`.
- **"+ New Record" button**: `<a>` linking to `record-form.html` (CSS class: `btn btn-primary`).
- **Recent Activity table**: Five rows, each clickable (navigates to `record-detail.html`). Columns: Record, Type, Status, Assignee, Last Updated.
- **"View All Records →"** button: `<a>` linking to `records.html`.

### Navigate via Sidebar

1. Locate `[data-testid="sidebar-nav"]`.
2. Click the desired `[data-testid="nav-item-<name>"]` (see sidebar table above).
3. The `[data-testid="breadcrumb"]` updates to reflect the current location.

---

## Records Module

### Open Records List

**URL**: `http://localhost:8080/records.html`

1. Navigate via sidebar: click `[data-testid="nav-item-records"]`.
2. Records table renders at `[data-testid="records-table"]` (wraps a `<table>` element).
3. Pagination controls at `[data-testid="pagination-controls"]`.
4. Table columns: Title, Type, Status, Assignee, Priority, Due Date, Actions.
5. Sortable column headers: `[data-testid="th-sort-title"]`, `[data-testid="th-sort-type"]`, `[data-testid="th-sort-status"]`, `[data-testid="th-sort-assignee"]`, `[data-testid="th-sort-priority"]`, `[data-testid="th-sort-dueDate"]`.

### Filter Records

1. Click `[data-testid="btn-filter"]` (label: "🔽 Filter") to toggle the filter panel.
2. Filter panel appears at `[data-testid="filter-panel"]` (initially hidden).
3. Set **Status** via `[data-testid="filter-status"]` (`<select>` — options: All Statuses, Draft, Pending Review, Approved, Rejected, Locked, Archived).
4. Set **Type** via `[data-testid="filter-type"]` (`<select>` — options: All Types, Compliance, Infrastructure, HR Document, Policy).
5. Set **Date Range** via `[data-testid="filter-date-from"]` and `[data-testid="filter-date-to"]` (type: `date`).
6. Click `[data-testid="btn-apply-filters"]` (label: "Apply").
7. Active filters shown as tags at `[data-testid="active-filter-tags"]`.
8. Clear all: click `[data-testid="btn-clear-filters"]` (label: "Clear Filters").

### Search Records

1. Locate `[data-testid="search-input"]` (type: `text`, placeholder: "Search records…", id: `search-input`).
2. Type the search term (triggers `oninput` handler with debounce).
3. Results update in the table.
4. Zero results: `[data-testid="empty-state-records"]` becomes visible (initially `display:none`; icon: 📭, heading: "No records found").

### Pagination

| Element         | `data-testid`       | Type     | Notes                                  |
| --------------- | -------------------- | -------- | -------------------------------------- |
| Page size select| `select-page-size`   | `select` | Options: "10 / page", "25 / page", "50 / page" |
| Previous page   | `btn-page-prev`      | button   | Disabled when on first page            |
| Next page       | `btn-page-next`      | button   | Navigates to next page                 |

Status text: "Showing 1-6 of 42 records".

### Show Archived Toggle

- Checkbox: `[data-testid="toggle-show-archived"]` (type: `checkbox`).
- Label: "Show archived records".

### Open a Record Detail

**URL**: `http://localhost:8080/record-detail.html`

1. In the records table, click any row `[data-testid="records-table-row"]` (rows have `cursor:pointer` and `onclick` handlers).
2. OR click the `[data-testid="btn-view-record"]` icon button (👁) on that row.
3. Detail page loads at `record-detail.html`.
4. Breadcrumb shows: Home / Records / Q4 Financial Review.

### Record Detail Page Elements

| Element              | `data-testid`          | Type     | Notes                                           |
| -------------------- | ---------------------- | -------- | ----------------------------------------------- |
| Record summary card  | `record-summary`       | div.card | Contains Title, Type, Priority, Assignee, Due Date, Created, Description, Attachments |
| Status badge         | `status-badge`         | span     | Shows current status (e.g. "Draft"); CSS class `badge--draft`, `badge--pending`, `badge--approved`, `badge--rejected`, `badge--locked` |
| Lock icon            | `record-lock-icon`     | span     | Visible when record is locked (🔒); initially has class `hidden` |
| Activity log         | `activity-log`         | div      | Timeline of record events in the right sidebar  |

### Create New Record

**URL**: `http://localhost:8080/record-form.html`

1. On the records list page, click `[data-testid="btn-create-record"]` (label: "+ New Record", `<a>` tag).
2. OR from the dashboard, click the "+ New Record" button linking to `record-form.html`.
3. Form loads at `record-form.html`. Breadcrumb: Home / Records / New Record.

**Form fields**:

| Field          | `data-testid`                   | Type       | Required | Notes                                                       |
| -------------- | ------------------------------- | ---------- | -------- | ----------------------------------------------------------- |
| Title          | `input-record-title`            | `text`     | Yes      | Placeholder: "Enter record title"                           |
| Type           | `select-record-type`            | `select`   | Yes      | Options: Compliance, Infrastructure, HR Document, Policy, Technical |
| Assignee       | `select-record-assignee`        | `select`   | No       | Options: Sarah Connor, Mike Chen, Emily Park, Alex Kim, Lisa Wong |
| Priority       | `select-record-priority`        | `select`   | No       | Options: Low, Medium (default), High, Critical              |
| Due Date       | `datepicker-record-due-date`    | `date`     | No       |                                                             |
| Attachments    | `input-record-attachments`      | `file`     | No       | `multiple` attribute enabled                                |
| Description    | `textarea-record-description`   | `textarea` | No       | Placeholder: "Describe the record…", 6 rows                 |

4. Click `[data-testid="btn-submit-record"]` (type: `submit`, label: "Submit").
5. On success → redirects to `record-detail.html`; success toast appears.
6. On validation error → `[data-testid="form-error-summary"]` becomes visible (text: "Please fix the highlighted errors before submitting."). Each invalid field shows an error like `[data-testid="field-error-title"]` (text: "Title is required.") and `[data-testid="field-error-type"]` (text: "Type is required.").
7. Cancel button: `<a>` linking back to `records.html`.

### Edit a Record

**URL**: `http://localhost:8080/record-form.html`

1. On the record detail page, click `[data-testid="btn-edit-record"]` (label: "✏ Edit", `<a>` tag).
2. OR on the records list page, click the `[data-testid="btn-edit-record"]` icon button (✏) on a row.
3. Both navigate to `record-form.html` (same form serves create and edit).
4. Modify fields and click `[data-testid="btn-submit-record"]` (label: "Submit").
5. Success toast appears on save.

### Delete a Record

**URL**: `http://localhost:8080/record-detail.html`

1. On record detail, click `[data-testid="btn-actions-menu"]` (label: "Actions ▾").
2. Actions dropdown opens (id: `actions-dropdown`).
3. Select `[data-testid="action-delete-record"]` (label: "🗑 Delete").
4. Confirmation dialog appears at `[data-testid="modal-confirm-delete"]`.
5. Dialog contains a danger alert: "This action cannot be undone."
6. Click `[data-testid="btn-confirm-delete"]` (label: "Yes, Delete") to confirm.
7. Click `[data-testid="btn-cancel-modal"]` (label: "Cancel") to abort.
8. On confirm → navigates to `records.html`; success toast appears.

---

## Workflow Actions (Record Status Transitions)

All workflow actions are performed on the **Record Detail page** (`record-detail.html`).

### Submit for Review

**Transition**: Draft → Pending Review

1. On the record detail page, click `[data-testid="btn-submit-for-review"]` (label: "📤 Submit for Review").
2. Modal opens at `[data-testid="modal-confirm"]` (id: `modal-submit-review`).
3. Optional comment field: `[data-testid="input-workflow-comment"]` (`<textarea>`, placeholder: "Add a comment for the reviewer…").
4. Click `[data-testid="btn-confirm-workflow"]` (label: "Confirm").
5. OR cancel: click `[data-testid="btn-cancel-modal"]` (label: "Cancel") or `[data-testid="btn-close-modal"]` (× button).
6. Status badge at `[data-testid="status-badge"]` changes to "Pending Review".
7. Activity log entry added at `[data-testid="activity-log"]`.

### Approve a Record

**Transition**: Pending Review → Approved  
**Required role**: Reviewer or Admin

1. On the record detail page, click `[data-testid="btn-approve"]` (label: "✓ Approve").
2. Approval dialog at `[data-testid="modal-approve"]` (id: `modal-approve`).
3. Optional note: `[data-testid="input-approval-note"]` (`<textarea>`, placeholder: "Add a note…").
4. Click `[data-testid="btn-confirm-approval"]` (label: "Approve").
5. OR cancel: click `[data-testid="btn-cancel-modal"]` (label: "Cancel").
6. Status badge updates to "Approved".

### Reject a Record

**Transition**: Pending Review → Rejected  
**Required role**: Reviewer or Admin

1. On the record detail page, click `[data-testid="btn-reject"]` (label: "✕ Reject").
2. Rejection dialog at `[data-testid="modal-reject"]` (id: `modal-reject`).
3. **Required** reason: `[data-testid="input-rejection-reason"]` (`<textarea>`, placeholder: "Describe why this record is being rejected…", `required` attribute).
4. Click `[data-testid="btn-confirm-rejection"]` (label: "Reject").
5. OR cancel: click `[data-testid="btn-cancel-modal"]` (label: "Cancel").
6. Status badge updates to "Rejected".

### Lock a Record

**Transition**: Approved → Locked  
**Required role**: Admin

1. On the record detail page (status must be "Approved"), click `[data-testid="btn-actions-menu"]` (label: "Actions ▾").
2. Select `[data-testid="action-lock-record"]` (label: "🔒 Lock Record").
3. Lock confirmation modal at `[data-testid="modal-lock"]` (id: `modal-lock`).
4. Click `[data-testid="btn-confirm-lock"]` (label: "Lock").
5. OR cancel: click `[data-testid="btn-cancel-modal"]` (label: "Cancel").
6. Status badge updates to "Locked". Edit/Submit buttons become disabled.
7. Lock icon appears at `[data-testid="record-lock-icon"]` (🔒).

### Unlock a Record

**Transition**: Locked → Approved  
**Required role**: Admin

1. On a Locked record detail page, click `[data-testid="btn-actions-menu"]`.
2. Select `[data-testid="action-unlock-record"]` (label: "🔓 Unlock Record").
3. Unlock confirmation modal at `[data-testid="modal-unlock"]` (id: `modal-unlock`).
4. **Required** justification: `[data-testid="input-unlock-reason"]` (`<textarea>`, placeholder: "Explain why this record needs to be unlocked…", `required` attribute).
5. Click `[data-testid="btn-confirm-unlock"]` (label: "Unlock").
6. OR cancel: click `[data-testid="btn-cancel-modal"]` (label: "Cancel").
7. Status badge updates to "Approved". Edit buttons re-enabled.

### Archive a Record

**Transition**: Any terminal state (Approved, Rejected, Locked)

1. Click `[data-testid="btn-actions-menu"]` (label: "Actions ▾").
2. Select `[data-testid="action-archive"]` (label: "📦 Archive").
3. Archived records are hidden from the default list view.
4. Toggle archived visibility on records list page: `[data-testid="toggle-show-archived"]` (checkbox).

---

## Reports Module

### Open Reports

**URL**: `http://localhost:8080/reports.html`

1. In the sidebar, click `[data-testid="nav-item-reports"]`.
2. Report cards list renders at `[data-testid="reports-list"]`.
3. Six report cards available:
   - 📊 Monthly Compliance Summary
   - 📈 Record Status Distribution
   - ⏱ Average Review Time
   - 👥 Assignee Workload
   - 📅 Due Date Compliance
   - 🔒 Locked Records Audit

### Run a Report

1. Click on a report card (e.g. "Monthly Compliance Summary") to reveal the report detail section (id: `report-detail-section`, initially `display:none`).
2. Set date range via `[data-testid="report-date-from"]` (type: `date`, default: `2026-02-01`) and `[data-testid="report-date-to"]` (type: `date`, default: `2026-02-28`).
3. Click `[data-testid="btn-run-report"]` (label: "▶ Run Report").
4. Loading indicator: `[data-testid="report-loading"]` (initially `display:none`; shows spinner and "Generating report…").
5. Results render in `[data-testid="report-results"]` (initially `display:none`; contains stat cards and a results table).

### Export a Report

1. After running the report, click `[data-testid="btn-export"]` (label: "📥 Export").
2. Dropdown appears with:
   - `[data-testid="export-csv"]` (label: "📄 Export as CSV").
   - `[data-testid="export-pdf"]` (label: "📕 Export as PDF").
3. Clicking triggers a success toast (e.g. "Downloading CSV…").

---

## Settings

### Open Settings

**URL**: `http://localhost:8080/settings.html`

1. Click `[data-testid="nav-item-settings"]` in the sidebar.
2. Settings tabs at `[data-testid="settings-tabs"]`.
3. Two tabs: Profile (default active) and Security.

### Update Profile

**Tab**: `[data-testid="settings-tab-profile"]` (label: "👤 Profile")

1. Click tab `[data-testid="settings-tab-profile"]`.
2. Profile form renders inside `[data-testid="form-profile"]` (a card element).
3. Form fields (all `<input>` type `text` unless noted):
   - First Name (id: `input-first-name`, default: "John")
   - Last Name (id: `input-last-name`, default: "Doe")
   - Email (id: `input-email`, type: `email`, default: "john.doe@company.com")
   - Phone (id: `input-phone`, type: `tel`, default: "+1 (555) 123-4567")
   - Department (id: `input-department`, default: "Engineering")
   - Job Title (id: `input-title`, default: "Senior QA Engineer")
   - Bio (id: `textarea-bio`, `<textarea>`, default: "Experienced QA engineer…")
4. Click `[data-testid="btn-save-profile"]` (label: "Save Profile").
5. Success toast appears on save.

### Change Password

**Tab**: `[data-testid="settings-tab-security"]` (label: "🔒 Security")

1. Click tab `[data-testid="settings-tab-security"]`.
2. Fill the following fields:
   - `[data-testid="input-current-password"]` (type: `password`, placeholder: "Enter current password")
   - `[data-testid="input-new-password"]` (type: `password`, placeholder: "Enter new password") — hint: "Must be at least 12 characters with uppercase, lowercase, number, and special character."
   - `[data-testid="input-confirm-password"]` (type: `password`, placeholder: "Confirm new password")
3. Click `[data-testid="btn-change-password"]` (label: "Change Password").
4. Success toast appears.

---

## Notifications

### Open Notification Panel

**Trigger**: Bell icon in header.

1. Click `[data-testid="btn-notifications"]` (🔔 icon button in header).
2. Notification dropdown opens at `[data-testid="notifications-panel"]`.
3. Unread count badge at `[data-testid="notification-unread-count"]` (displays a number, e.g. `3`).
4. Mark all read: click `[data-testid="btn-mark-all-read"]` (label: "Mark all read").
5. Click an individual notification item (class: `notification-item`) to navigate to the relevant record (`record-detail.html`).

---

## Admin Panel

### Open Admin Panel

**URL**: `http://localhost:8080/admin.html`  
**Required role**: Admin

1. Navigate to `admin.html` via `[data-testid="nav-item-admin"]`.
2. Two tabs: Users (default active) and Roles.

### Manage Users

**Tab**: `[data-testid="admin-tab-users"]` (label: "👥 Users")

1. Click `[data-testid="admin-tab-users"]`.
2. User table at `[data-testid="admin-users-table"]`.
3. Table columns: User, Email, Role, Status, Last Active, Actions.
4. Invite user: click `[data-testid="btn-invite-user"]` (label: "+ Invite User"). Opens invite modal (id: `modal-invite`) with email input and role dropdown.
5. Deactivate user: click the row-level button `[data-testid="action-deactivate-user-<userId>"]` (label: "Deactivate").
   - Known user IDs in the table: `u002` (Sarah Connor), `u003` (Mike Chen), `u004` (Emily Park), `u006` (Lisa Wong).
   - Example: `[data-testid="action-deactivate-user-u002"]` deactivates Sarah Connor.

### Manage Roles

**Tab**: `[data-testid="admin-tab-roles"]` (label: "🛡 Roles")

1. Click `[data-testid="admin-tab-roles"]`.
2. Role cards list at `[data-testid="admin-roles-list"]`.
3. Four roles displayed: Admin, Reviewer, Editor, Viewer.
4. Edit role permissions: click `[data-testid="btn-edit-role-<roleName>"]`.
   - Available: `[data-testid="btn-edit-role-admin"]`, `[data-testid="btn-edit-role-reviewer"]`, `[data-testid="btn-edit-role-editor"]`, `[data-testid="btn-edit-role-viewer"]`.

---

## Common Interaction Patterns

### Opening a Dropdown / Actions Menu

1. Click the trigger button (e.g. `[data-testid="btn-actions-menu"]`, `[data-testid="user-avatar-menu"]`, `[data-testid="btn-export"]`).
2. The adjacent `div` with class `actions-dropdown`, `user-dropdown`, or similar toggles a `visible` CSS class.
3. Click an item inside the dropdown.
4. The dropdown auto-closes on outside click (handled by `app.js`).

### Working with Modals

1. A trigger opens the modal overlay (class: `modal-overlay`, e.g. `id="modal-confirm-delete"`).
2. Modal contains: `.modal-header` (title + close button ×), `.modal-body` (content/forms), `.modal-footer` (Cancel + Confirm buttons).
3. Close via: `[data-testid="btn-cancel-modal"]` (label: "Cancel"), or the × button `[data-testid="btn-close-modal"]`, or clicking the overlay.
4. Confirm via the specific confirm button (e.g. `[data-testid="btn-confirm-delete"]`, `[data-testid="btn-confirm-lock"]`).

### Tab Switching (Settings / Admin)

1. Click a tab button with `[data-testid="settings-tab-<name>"]` or `[data-testid="admin-tab-<name>"]`.
2. The clicked tab gets class `tab--active`.
3. The corresponding `tab-content` div (id: `tab-<name>`) gets class `active`, others lose it.

### Toast Messages

- Toasts appear in `#toast-container`.
- Triggered by JavaScript function `showToast(type, message)` where type is `'success'` or `'error'`.
- Auto-dismiss after a configurable timeout.
