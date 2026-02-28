# Navigation Guide

This guide documents the step-by-step navigation paths, URLs, and user-flow sequences
for every major feature in the application. Each section corresponds to a user-visible
workflow. Search this file by feature name or action verb.

---

## Authentication

### Login

**URL**: `/login`

1. Navigate to `/login`.
2. Enter credentials in `[data-testid="input-username"]` and `[data-testid="input-password"]`.
3. Click `[data-testid="btn-login"]` (label: "Sign In").
4. On success → redirects to `/dashboard`.
5. On failure → error banner at `[data-testid="alert-login-error"]`.

### Logout

**URL**: Any authenticated page.

1. Click the user avatar at `[data-testid="user-avatar-menu"]` (top-right header).
2. In the dropdown, click `[data-testid="menu-item-logout"]` (label: "Sign Out").
3. Redirects to `/login`.

### Forgot Password

**URL**: `/forgot-password`

1. On the login page, click `[data-testid="link-forgot-password"]`.
2. Enter email in `[data-testid="input-reset-email"]`.
3. Click `[data-testid="btn-send-reset"]` (label: "Send Reset Link").
4. Confirmation message appears at `[data-testid="alert-reset-sent"]`.

---

## Dashboard

### Open Dashboard

**URL**: `/dashboard`

1. After login, the application lands on `/dashboard` automatically.
2. Dashboard layout: left sidebar at `[data-testid="sidebar-nav"]`, main panel at `[data-testid="main-content"]`.

### Navigate via Sidebar

**Sidebar selector**: `[data-testid="sidebar-nav"]`

| Menu Item   | `data-testid`        | Target URL                 |
| ----------- | -------------------- | -------------------------- |
| Dashboard   | `nav-item-dashboard` | `/dashboard`               |
| Records     | `nav-item-records`   | `/records`                 |
| Reports     | `nav-item-reports`   | `/reports`                 |
| Settings    | `nav-item-settings`  | `/settings`                |
| Admin Panel | `nav-item-admin`     | `/admin` (admin role only) |

Steps:

1. Locate `[data-testid="sidebar-nav"]`.
2. Click the desired `[data-testid="nav-item-<name>"]`.
3. The `[data-testid="breadcrumb"]` updates to reflect the current location.

---

## Records Module

### Open Records List

**URL**: `/records`

1. Navigate via sidebar: click `[data-testid="nav-item-records"]`.
2. Records table renders at `[data-testid="records-table"]`.
3. Pagination controls at `[data-testid="pagination-controls"]`.

### Filter Records

**URL**: `/records?status=<value>&type=<value>`

1. Click `[data-testid="btn-filter"]` (label: "Filter") to open the filter panel.
2. Filter panel appears at `[data-testid="filter-panel"]`.
3. Set **Status** via `[data-testid="filter-status"]` (dropdown).
4. Set **Type** via `[data-testid="filter-type"]` (dropdown).
5. Set **Date Range** via `[data-testid="filter-date-from"]` and `[data-testid="filter-date-to"]`.
6. Click `[data-testid="btn-apply-filters"]` (label: "Apply").
7. Table refreshes; active filters shown at `[data-testid="active-filter-tags"]`.
8. Clear all: click `[data-testid="btn-clear-filters"]`.

### Search Records

**URL**: `/records?q=<term>`

1. On any records page, locate `[data-testid="search-input"]` (placeholder: "Search records…").
2. Type the search term.
3. Results update after 300 ms debounce (or on Enter).
4. Zero results: `[data-testid="empty-state-records"]` renders.

### Open a Record Detail

**URL**: `/records/:id`

1. In the records table, click any row at `[data-testid="records-table-row"]`.
2. OR click the `[data-testid="btn-view-record"]` icon on that row.
3. Detail page loads at `/records/:id`.
4. Summary panel: `[data-testid="record-summary"]`.
5. Activity log: `[data-testid="activity-log"]`.

### Create New Record

**URL**: `/records/new`

1. Click `[data-testid="btn-create-record"]` (label: "New Record") on the records list page.
2. Form opens at `/records/new`.
3. Fill required fields (see Keywords Guide → "Record Form Fields").
4. Click `[data-testid="btn-submit-record"]` (label: "Submit").
5. On success → redirect to `/records/:newId`; success toast at `[data-testid="toast-success"]`.
6. On validation error → `[data-testid="form-error-summary"]` lists errors; each field shows `[data-testid="field-error-<fieldName>"]`.

### Edit a Record

**URL**: `/records/:id/edit`

1. Open the record detail page (`/records/:id`).
2. Click `[data-testid="btn-edit-record"]` (label: "Edit").
3. Form opens in edit mode at `/records/:id/edit`.
4. Modify fields.
5. Click `[data-testid="btn-save-record"]` (label: "Save Changes").
6. Success toast at `[data-testid="toast-success"]`.

### Delete a Record

**URL**: `/records/:id`

1. On record detail, click `[data-testid="btn-actions-menu"]` (label: "Actions ▾").
2. Select `[data-testid="action-delete-record"]` (label: "Delete").
3. Confirmation dialog appears at `[data-testid="modal-confirm-delete"]`.
4. Click `[data-testid="btn-confirm-delete"]` (label: "Yes, Delete") to confirm.
5. Click `[data-testid="btn-cancel-modal"]` (label: "Cancel") to abort.
6. On confirm → redirects to `/records`; success toast at `[data-testid="toast-success"]`.

---

## Workflow Actions (Record Status Transitions)

### Submit for Review

**Applicable status**: Draft → Pending Review  
**URL**: `/records/:id`

1. Open the record detail page.
2. Click `[data-testid="btn-submit-for-review"]` (label: "Submit for Review").
3. Optional comment field in the modal: `[data-testid="input-workflow-comment"]`.
4. Click `[data-testid="btn-confirm-workflow"]` (label: "Confirm").
5. Status badge at `[data-testid="status-badge"]` changes to "Pending Review".
6. Activity log entry added at `[data-testid="activity-log"]`.

### Approve a Record

**Applicable status**: Pending Review → Approved  
**Required role**: Reviewer or Admin  
**URL**: `/records/:id`

1. Open the record detail page.
2. Click `[data-testid="btn-approve"]` (label: "Approve").
3. Approval confirmation dialog at `[data-testid="modal-approve"]`.
4. Enter optional note in `[data-testid="input-approval-note"]`.
5. Click `[data-testid="btn-confirm-approval"]` (label: "Approve").
6. Status badge updates to "Approved".

### Reject a Record

**Applicable status**: Pending Review → Rejected  
**Required role**: Reviewer or Admin  
**URL**: `/records/:id`

1. Open the record detail page.
2. Click `[data-testid="btn-reject"]` (label: "Reject").
3. Rejection dialog at `[data-testid="modal-reject"]`.
4. Enter **required** reason in `[data-testid="input-rejection-reason"]`.
5. Click `[data-testid="btn-confirm-rejection"]` (label: "Reject").
6. Status badge updates to "Rejected".

### Lock a Record

**Applicable status**: Approved → Locked  
**Required role**: Admin  
**URL**: `/records/:id`

1. Open the record detail page (status must be "Approved").
2. Click `[data-testid="btn-actions-menu"]` (label: "Actions ▾").
3. Select `[data-testid="action-lock-record"]` (label: "Lock Record").
4. Lock confirmation modal at `[data-testid="modal-lock"]`.
5. Click `[data-testid="btn-confirm-lock"]` (label: "Lock").
6. Status badge updates to "Locked". Edit/Submit buttons become disabled.
7. Lock icon appears at `[data-testid="record-lock-icon"]`.

### Unlock a Record

**Applicable status**: Locked → Approved  
**Required role**: Admin  
**URL**: `/records/:id`

1. Open a Locked record detail page.
2. Click `[data-testid="btn-actions-menu"]`.
3. Select `[data-testid="action-unlock-record"]` (label: "Unlock Record").
4. Unlock confirmation modal at `[data-testid="modal-unlock"]`.
5. Enter **required** justification in `[data-testid="input-unlock-reason"]`.
6. Click `[data-testid="btn-confirm-unlock"]` (label: "Unlock").
7. Status badge updates to "Approved". Edit buttons re-enabled.

### Archive a Record

**Applicable status**: Any terminal state (Approved, Rejected, Locked)  
**URL**: `/records/:id`

1. Click `[data-testid="btn-actions-menu"]`.
2. Select `[data-testid="action-archive"]` (label: "Archive").
3. Archived records are hidden from the default list view.
4. Toggle archived visibility: `[data-testid="toggle-show-archived"]`.

---

## Reports Module

### Open Reports

**URL**: `/reports`

1. In the sidebar, click `[data-testid="nav-item-reports"]`.
2. Report list renders at `[data-testid="reports-list"]`.

### Run a Report

**URL**: `/reports/:reportId`

1. Click on a report card to open it.
2. Set date range via `[data-testid="report-date-from"]` and `[data-testid="report-date-to"]`.
3. Click `[data-testid="btn-run-report"]` (label: "Run Report").
4. Loading indicator: `[data-testid="report-loading"]`.
5. Results render in `[data-testid="report-results"]`.

### Export a Report

**URL**: `/reports/:reportId`

1. After running the report, click `[data-testid="btn-export"]`.
2. Dropdown: choose `[data-testid="export-csv"]` or `[data-testid="export-pdf"]`.
3. File download triggered via browser download event.

---

## Settings

### Open Settings

**URL**: `/settings`

1. Click `[data-testid="nav-item-settings"]` in the sidebar.
2. Settings tabs at `[data-testid="settings-tabs"]`.

### Update Profile

**URL**: `/settings/profile`

1. Click tab `[data-testid="settings-tab-profile"]`.
2. Edit fields in `[data-testid="form-profile"]`.
3. Click `[data-testid="btn-save-profile"]` (label: "Save Profile").

### Change Password

**URL**: `/settings/security`

1. Click tab `[data-testid="settings-tab-security"]`.
2. Fill `[data-testid="input-current-password"]`, `[data-testid="input-new-password"]`,
   `[data-testid="input-confirm-password"]`.
3. Click `[data-testid="btn-change-password"]` (label: "Change Password").

---

## Notifications

### Open Notification Panel

**Trigger**: Bell icon in header. `[data-testid="btn-notifications"]`.

1. Click `[data-testid="btn-notifications"]`.
2. Notification dropdown opens at `[data-testid="notifications-panel"]`.
3. Unread count badge at `[data-testid="notification-unread-count"]`.
4. Mark all read: `[data-testid="btn-mark-all-read"]`.
5. Click individual notification to navigate to the relevant record.

---

## Admin Panel

### Manage Users

**URL**: `/admin/users`  
**Required role**: Admin

1. Navigate to `/admin` via `[data-testid="nav-item-admin"]`.
2. Click `[data-testid="admin-tab-users"]`.
3. User list at `[data-testid="admin-users-table"]`.
4. Invite user: `[data-testid="btn-invite-user"]`.
5. Deactivate user: row action `[data-testid="action-deactivate-user-<userId>"]`.

### Manage Roles

**URL**: `/admin/roles`

1. On the Admin panel, click `[data-testid="admin-tab-roles"]`.
2. Role list at `[data-testid="admin-roles-list"]`.
3. Edit role permissions: click `[data-testid="btn-edit-role-<roleName>"]`.
