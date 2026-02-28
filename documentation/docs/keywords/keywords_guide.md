# Keywords Guide

This guide defines every significant UI element, application term, and domain
concept used across the demo frontend. Each entry includes a description, the
primary CSS selector or `data-testid`, element type, and interaction details.

Search this file for a specific term or element to get its selector and usage context.

**Base URL**: `http://localhost:8080`

---

## Status Values

### Status Badge

**Description**: A coloured chip/pill that shows the current lifecycle status of a record.  
**Selector**: `[data-testid="status-badge"]`  
**ARIA role**: `status`  
**Location**: Record detail page (`record-detail.html`) — next to the `<h1>` title.  
**Possible values / colours**:

| Status text    | CSS modifier class                  | Meaning                     |
| -------------- | ----------------------------------- | --------------------------- |
| Draft          | `.badge--draft` (grey)              | Not yet submitted           |
| Pending Review | `.badge--pending` (yellow)          | Awaiting reviewer action    |
| Approved       | `.badge--approved` (green)          | Accepted by reviewer        |
| Rejected       | `.badge--rejected` (red)            | Declined by reviewer        |
| Locked         | `.badge--locked` (blue + lock icon) | Immutable; no further edits |
| Archived       | `.badge--archived` (grey, italic)   | Hidden from default views   |

**Usage** — verify current status:

```
Selector: [data-testid="status-badge"]
Expected text: "Draft" | "Pending Review" | "Approved" | "Rejected" | "Locked"
Expected class contains: badge--draft | badge--pending | badge--approved | badge--rejected | badge--locked
```

---

## Buttons

### Primary Action Button

**Description**: The dominant call-to-action on a page or modal.  
**CSS class**: `.btn-primary`  
**Examples in demo**:
- "Sign In" on `login.html`
- "Submit" on `record-form.html`
- "▶ Run Report" on `reports.html`
- "Confirm" in workflow modals
- "📤 Submit for Review" on `record-detail.html`

### Success Button

**Description**: Used for positive-outcome actions.  
**CSS class**: `.btn-success`  
**Example**: "✓ Approve" on `record-detail.html`

### Secondary Action Button

**Description**: A less prominent action.  
**CSS class**: `.btn-secondary`  
**Examples**: "Cancel" in modals, "🔽 Filter", "Clear Filters", "Actions ▾"

### Danger / Destructive Button

**Description**: Buttons that trigger irreversible actions (delete, reject).  
**CSS class**: `.btn-danger`  
**Examples**: "✕ Reject", "Yes, Delete", "Deactivate" (admin user table)

### Icon Button

**Description**: A button with only an icon and no visible label text.  
**CSS class**: `.btn-icon`  
**Examples**: 👁 View record (`[data-testid="btn-view-record"]`), ✏ Edit record (`[data-testid="btn-edit-record"]`), 🔔 Notifications bell (`[data-testid="btn-notifications"]`)

### Actions Menu Button

**Description**: An "Actions ▾" dropdown menu trigger on the record detail page.  
**Selector**: `[data-testid="btn-actions-menu"]`  
**Label**: "Actions ▾"  
**Location**: `record-detail.html` — page header actions area.

**Interaction**:
1. Click `[data-testid="btn-actions-menu"]`.
2. Dropdown `#actions-dropdown` (class `actions-dropdown`) opens.
3. Click the desired action item (`[data-testid="action-<action-name>"]`).

**Available actions in dropdown**:

| Action         | `data-testid`          | Label             |
| -------------- | ---------------------- | ----------------- |
| Lock Record    | `action-lock-record`   | 🔒 Lock Record   |
| Unlock Record  | `action-unlock-record` | 🔓 Unlock Record |
| Archive        | `action-archive`       | 📦 Archive       |
| Delete         | `action-delete-record` | 🗑 Delete        |

---

## Form Fields

### Text Input

**Selector pattern**: `[data-testid="input-<fieldName>"]`  
**HTML element**: `<input type="text">`  
**Interaction**: Click → type value.

### Password Input

**Selector examples**:
- Login: `[data-testid="input-password"]` (on `login.html`)
- Current password: `[data-testid="input-current-password"]` (on `settings.html`, Security tab)
- New password: `[data-testid="input-new-password"]` (on `settings.html`, Security tab)
- Confirm password: `[data-testid="input-confirm-password"]` (on `settings.html`, Security tab)

**Type attribute**: `type="password"`

### Dropdown / Select

**Selector pattern**: `[data-testid="select-<fieldName>"]` or `[data-testid="filter-<fieldName>"]`  
**HTML element**: `<select>` with `<option>` children.  
**Interaction**: Click → select option by value or visible text.

### Date Input

**Selector pattern**: `[data-testid="datepicker-<fieldName>"]` or `[data-testid="filter-date-<direction>"]` or `[data-testid="report-date-<direction>"]`  
**HTML element**: `<input type="date">`  
**Interaction**: Fill with `YYYY-MM-DD` format string.

### Textarea

**Selector pattern**: `[data-testid="textarea-<fieldName>"]` or `[data-testid="input-<fieldName>"]` (modals)  
**HTML element**: `<textarea>`  
**Interaction**: Click → type value.

### File Input

**Selector**: `[data-testid="input-record-attachments"]`  
**HTML element**: `<input type="file" multiple>`  
**Location**: `record-form.html`

### Search Input

**Description**: Full-text search field on the records list page.  
**Selector**: `[data-testid="search-input"]`  
**HTML id**: `search-input`  
**Placeholder**: "Search records…"  
**Location**: `records.html` — toolbar area.  
**Behavior**: Triggers `oninput` handler with debounce.

### Checkbox (Toggle)

**Selector**: `[data-testid="toggle-show-archived"]`  
**HTML element**: `<input type="checkbox">`  
**Label**: "Show archived records"  
**Location**: `records.html` — above the records table.  
**Interaction**: Click to check/uncheck.

---

## Record Form Fields

Fields used on the New Record and Edit Record form (`record-form.html`):

| Field label | `data-testid`                 | Type       | Required | Placeholder / Options                                        |
| ----------- | ----------------------------- | ---------- | -------- | ------------------------------------------------------------ |
| Title       | `input-record-title`          | text       | Yes      | "Enter record title"                                         |
| Type        | `select-record-type`          | select     | Yes      | Compliance, Infrastructure, HR Document, Policy, Technical   |
| Assignee    | `select-record-assignee`      | select     | No       | Sarah Connor, Mike Chen, Emily Park, Alex Kim, Lisa Wong     |
| Priority    | `select-record-priority`      | select     | No       | Low, Medium (default), High, Critical                        |
| Due Date    | `datepicker-record-due-date`  | date       | No       | —                                                            |
| Attachments | `input-record-attachments`    | file       | No       | `multiple` attribute enabled                                 |
| Description | `textarea-record-description` | textarea   | No       | "Describe the record…" (6 rows)                              |

**Submit**: `[data-testid="btn-submit-record"]` (label: "Submit")  
**Cancel**: `<a>` linking to `records.html` (label: "Cancel")

**Validation errors**:
- Form-level: `[data-testid="form-error-summary"]` — text: "Please fix the highlighted errors before submitting."
- Title error: `[data-testid="field-error-title"]` — text: "Title is required."
- Type error: `[data-testid="field-error-type"]` — text: "Type is required."

---

## Filter Fields (Records List)

Fields inside the filter panel (`[data-testid="filter-panel"]`) on `records.html`:

| Field      | `data-testid`     | Type   | Options / Notes                                                  |
| ---------- | ----------------- | ------ | ---------------------------------------------------------------- |
| Status     | `filter-status`   | select | All Statuses, Draft, Pending Review, Approved, Rejected, Locked, Archived |
| Type       | `filter-type`     | select | All Types, Compliance, Infrastructure, HR Document, Policy       |
| From Date  | `filter-date-from`| date   | —                                                                |
| To Date    | `filter-date-to`  | date   | —                                                                |

**Apply**: `[data-testid="btn-apply-filters"]` (label: "Apply")  
**Toggle panel**: `[data-testid="btn-filter"]` (label: "🔽 Filter")  
**Active tags**: `[data-testid="active-filter-tags"]`  
**Clear all**: `[data-testid="btn-clear-filters"]` (label: "Clear Filters")

---

## Modals and Dialogs

### Modal Structure

All modals in the demo frontend follow this structure:
- **Overlay**: `<div class="modal-overlay">` with a unique `id` and optionally a `data-testid`.
- **Header**: `.modal-header` — contains `<h3>` title and `×` close button.
- **Body**: `.modal-body` — contains content, forms, alerts.
- **Footer**: `.modal-footer` — contains Cancel and Confirm buttons.

### Named Modals

| Action            | Modal `data-testid` / `id` | Confirm `data-testid`   | Confirm Label  | Input Field(s)                      |
| ----------------- | -------------------------- | ----------------------- | -------------- | ----------------------------------- |
| Submit for Review | `modal-confirm` / `modal-submit-review` | `btn-confirm-workflow`  | "Confirm"      | `input-workflow-comment` (optional) |
| Approve           | `modal-approve`            | `btn-confirm-approval`  | "Approve"      | `input-approval-note` (optional)    |
| Reject            | `modal-reject`             | `btn-confirm-rejection` | "Reject"       | `input-rejection-reason` (required) |
| Lock              | `modal-lock`               | `btn-confirm-lock`      | "Lock"         | —                                   |
| Unlock            | `modal-unlock`             | `btn-confirm-unlock`    | "Unlock"       | `input-unlock-reason` (required)    |
| Delete            | `modal-confirm-delete`     | `btn-confirm-delete`    | "Yes, Delete"  | —                                   |
| Invite User       | (id: `modal-invite`)       | —                       | "Send Invitation" | Email input + Role select        |

### Close / Dismiss Modal

**Cancel button**: `[data-testid="btn-cancel-modal"]` (label: "Cancel")  
**Close button**: `[data-testid="btn-close-modal"]` (× in top-right of modal header)  
**Overlay click**: Clicking the `.modal-overlay` background also closes the modal.

### Modal Interaction Pattern

1. Trigger the modal (click a workflow button, actions menu item, or invite button).
2. Wait for the modal overlay to become visible.
3. Fill any input fields in `.modal-body` if needed.
4. Click the confirm button in `.modal-footer`.
5. Verify outcome: status badge change, toast notification, or page redirect.

---

## Notifications and Feedback

### Toast Notification

**Description**: Transient success/error message overlaid in the top-right.  
**Container**: `#toast-container` (CSS class: `toast-container`).  
**Trigger**: JavaScript `showToast(type, message)` where type is `'success'` or `'error'`.  
**Toast element**: `[data-testid="toast-success"]` or class-based.  
**Behavior**: Auto-dismiss after timeout.

### Alert Banner

**Description**: A persistent inline notification (not self-dismissing).  
**CSS classes**: `.alert .alert-error`, `.alert .alert-success`, `.alert .alert-info`  
**Instances in demo**:
- `[data-testid="alert-login-error"]` — login failure ("Invalid username or password."), initially `display:none`.
- `[data-testid="alert-reset-sent"]` — forgotten password success, initially `display:none`.
- Delete confirmation modal contains a `.alert-error` warning.
- Settings Security tab contains a `.alert-info` for 2FA status.

### Form Validation Error

**Description**: Per-field red text below an input, initially hidden.  
**CSS class**: `.form-error`  
**Instances**:
- `[data-testid="field-error-title"]` — "Title is required."
- `[data-testid="field-error-type"]` — "Type is required."

**Form-level summary**: `[data-testid="form-error-summary"]` (CSS class: `.form-error-summary`)

### Empty State

**Description**: Shown when a list has no results.  
**CSS class**: `.empty-state`  
**Instances**:
- `[data-testid="empty-state-records"]` — icon: 📭, heading: "No records found", initially `display:none`.
- `[data-testid="empty-state-reports"]` — icon: 📭, heading: "No report data", initially `display:none`.

### Loading Spinner

**Selector**: `[data-testid="report-loading"]`  
**CSS class**: `.loading-spinner`  
**Location**: `reports.html` — shown while generating a report.  
**Content**: Spinner animation + "Generating report…"  
**Initially**: `display:none`

---

## Navigation Elements

### Sidebar Navigation

**Selector**: `[data-testid="sidebar-nav"]`  
**HTML element**: `<aside class="sidebar">`  
**Toggle**: `[data-testid="btn-sidebar-toggle"]` — hamburger ☰ button in the header.  
**Brand**: `.sidebar-brand` contains the 📋 logo and "Records Manager" text.

**Nav items**:

| Menu Item   | `data-testid`          | `href`           | Icon | Section  |
| ----------- | ---------------------- | ---------------- | ---- | -------- |
| Dashboard   | `nav-item-dashboard`   | `dashboard.html` | 📊   | Main     |
| Records     | `nav-item-records`     | `records.html`   | 📁   | Main     |
| Reports     | `nav-item-reports`     | `reports.html`   | 📈   | Main     |
| Settings    | `nav-item-settings`    | `settings.html`  | ⚙    | Account  |
| Admin Panel | `nav-item-admin`       | `admin.html`     | 🛡   | Account  |

### Breadcrumb

**Description**: Shows the current page hierarchy in the header.  
**Selector**: `[data-testid="breadcrumb"]`  
**HTML element**: `<nav class="breadcrumb">`  
**Structure**: `<a>Home</a> / <span class="current">Current Page</span>`  
**Breadcrumb trails by page**:
- Dashboard: Home / Dashboard
- Records: Home / Records
- Record Detail: Home / Records / Q4 Financial Review
- Record Form: Home / Records / New Record
- Reports: Home / Reports
- Settings: Home / Settings
- Admin: Home / Admin Panel

### Tab Bar

**Description**: Horizontal row of tabs.  
**Active class**: `.tab--active` on the active `<button>`.  
**Tab content**: The matching `<div id="tab-<name>" class="tab-content">` div gets class `active`.

**Settings tabs** (container: `[data-testid="settings-tabs"]`):
- `[data-testid="settings-tab-profile"]` — label: "👤 Profile"
- `[data-testid="settings-tab-security"]` — label: "🔒 Security"

**Admin tabs** (container: `#admin-tabs`):
- `[data-testid="admin-tab-users"]` — label: "👥 Users"
- `[data-testid="admin-tab-roles"]` — label: "🛡 Roles"

**Interaction**: Click the tab button → the corresponding `tab-content` div becomes visible.

### Pagination Controls

**Selector**: `[data-testid="pagination-controls"]`  
**Location**: `records.html` — bottom of the records table.

| Element         | `data-testid`       | Type     | Notes                                    |
| --------------- | -------------------- | -------- | ---------------------------------------- |
| Previous page   | `btn-page-prev`      | button   | Disabled when on first page              |
| Next page       | `btn-page-next`      | button   | Navigates to next page                   |
| Page size select| `select-page-size`   | select   | Options: "10 / page", "25 / page", "50 / page" |

**Status text**: "Showing 1-6 of 42 records"

---

## Tables

### Records Table

**Selector**: `[data-testid="records-table"]`  
**Location**: `records.html`  
**Columns**: Title, Type, Status, Assignee, Priority, Due Date, Actions

### Admin Users Table

**Selector**: `[data-testid="admin-users-table"]`  
**Location**: `admin.html` — Users tab  
**Columns**: User, Email, Role, Status, Last Active, Actions

### Table Row

**Selector**: `[data-testid="records-table-row"]`  
**Interaction**: Clickable rows — clicking navigates to `record-detail.html` (via `onclick` handler).  
**Note**: Multiple rows share the same `data-testid`; select by index or by inner text content.

### Sortable Column Headers

**Selector pattern**: `[data-testid="th-sort-<columnName>"]`  
**Location**: `records.html` table headers.  
**Available**:
- `[data-testid="th-sort-title"]` — has `.sort--asc` by default
- `[data-testid="th-sort-type"]`
- `[data-testid="th-sort-status"]`
- `[data-testid="th-sort-assignee"]`
- `[data-testid="th-sort-priority"]`
- `[data-testid="th-sort-dueDate"]`

**Sort indicator classes**: `.sort--asc`, `.sort--desc` (on the `<span class="sort-icon">` child).

### Row Action Buttons

**Selector pattern**: `[data-testid="btn-view-record"]` (👁), `[data-testid="btn-edit-record"]` (✏)  
**Location**: Actions column of each records table row.  
**Note**: Each row may have both or just the view button (locked records omit edit). Buttons call `event.stopPropagation()` to prevent row click navigation.

---

## User & Session Elements

### User Avatar Menu

**Description**: Top-right avatar button that opens a dropdown.  
**Selector**: `[data-testid="user-avatar-menu"]`  
**Content**: User initials (e.g. `JD`).  
**Dropdown id**: `user-dropdown`

**Dropdown items**:
- ⚙ Settings → `settings.html`
- 👤 Profile → `settings.html`
- 🚪 Sign Out → `login.html` (`[data-testid="menu-item-logout"]`)

### Current User Display Name

**Selector**: `[data-testid="user-display-name"]`  
**Default value**: "John Doe"  
**Location**: Inside user dropdown header.

### Role Badge

**Description**: Shows the current user's role.  
**Selector**: `[data-testid="user-role-badge"]`  
**Default value**: "Admin" (CSS class `.badge--approved`)  
**Location**: Inside user dropdown header, below display name.

---

## Workflow-Specific Elements

### Workflow Buttons (Record Detail Page)

| Button               | `data-testid`            | Label                  | CSS class      |
| -------------------- | ------------------------ | ---------------------- | -------------- |
| Submit for Review    | `btn-submit-for-review`  | 📤 Submit for Review   | `.btn-primary` |
| Approve              | `btn-approve`            | ✓ Approve             | `.btn-success` |
| Reject               | `btn-reject`             | ✕ Reject              | `.btn-danger`  |
| Edit                 | `btn-edit-record`        | ✏ Edit                | `.btn-secondary` (is an `<a>` tag → `record-form.html`) |

### Lock Icon (Locked Record Indicator)

**Description**: Renders alongside the status badge when a record is locked.  
**Selector**: `[data-testid="record-lock-icon"]`  
**Content**: 🔒  
**Initially**: Has class `hidden` (not visible until record is locked).

### Workflow Comment Input

**Description**: Optional text area in the "Submit for Review" modal.  
**Selector**: `[data-testid="input-workflow-comment"]`  
**HTML element**: `<textarea>`  
**Placeholder**: "Add a comment for the reviewer…"

### Approval Note Input

**Selector**: `[data-testid="input-approval-note"]`  
**HTML element**: `<textarea>`  
**Placeholder**: "Add a note…"

### Rejection Reason Input

**Selector**: `[data-testid="input-rejection-reason"]`  
**HTML element**: `<textarea>` with `required` attribute  
**Placeholder**: "Describe why this record is being rejected…"

### Unlock Justification Input

**Selector**: `[data-testid="input-unlock-reason"]`  
**HTML element**: `<textarea>` with `required` attribute  
**Placeholder**: "Explain why this record needs to be unlocked…"

### Activity Log

**Description**: Chronological trail of record events, shown in the right sidebar of `record-detail.html`.  
**Selector**: `[data-testid="activity-log"]`  
**Entry class**: `.log-entry`  
**Entry structure**: Each entry has a `.log-dot` (status color), `.log-text` (event description), and `.log-meta` (timestamp).  
**Latest entry**: `[data-testid="activity-log"] .log-entry:first-child`

---

## Record Detail Page Summary

**URL**: `http://localhost:8080/record-detail.html`

**Key selectors on this page**:

| Element            | `data-testid`           | Notes                                    |
| ------------------ | ----------------------- | ---------------------------------------- |
| Record summary     | `record-summary`        | Card with Title, Type, Priority, etc.    |
| Status badge       | `status-badge`          | Shows current status                     |
| Lock icon          | `record-lock-icon`      | Hidden unless locked                     |
| Activity log       | `activity-log`          | Right sidebar timeline                   |
| Submit for Review  | `btn-submit-for-review` | Workflow button                          |
| Approve            | `btn-approve`           | Workflow button                          |
| Reject             | `btn-reject`            | Workflow button                          |
| Edit               | `btn-edit-record`       | Links to `record-form.html`             |
| Actions menu       | `btn-actions-menu`      | Opens lock/unlock/archive/delete dropdown|

---

## Admin Panel Elements

### Users Tab

| Element              | `data-testid`                          | Notes                                    |
| -------------------- | -------------------------------------- | ---------------------------------------- |
| Users table          | `admin-users-table`                    | Table with all users                     |
| Invite user button   | `btn-invite-user`                      | Label: "+ Invite User"                   |
| Deactivate user      | `action-deactivate-user-<userId>`      | Per-row; e.g. `-u002`, `-u003`, `-u004`, `-u006` |

### Roles Tab

| Element              | `data-testid`                          | Notes                                    |
| -------------------- | -------------------------------------- | ---------------------------------------- |
| Roles list           | `admin-roles-list`                     | Grid of role cards                       |
| Edit Admin role      | `btn-edit-role-admin`                  | Edit button on Admin card                |
| Edit Reviewer role   | `btn-edit-role-reviewer`               | Edit button on Reviewer card             |
| Edit Editor role     | `btn-edit-role-editor`                 | Edit button on Editor card               |
| Edit Viewer role     | `btn-edit-role-viewer`                 | Edit button on Viewer card               |

---

## URLs Reference

| Page                | File                    | Full URL                                    |
| ------------------- | ----------------------- | ------------------------------------------- |
| Login               | `login.html`            | `http://localhost:8080/login.html`           |
| Forgot Password     | `forgot-password.html`  | `http://localhost:8080/forgot-password.html` |
| Dashboard           | `dashboard.html`        | `http://localhost:8080/dashboard.html`       |
| Records List        | `records.html`          | `http://localhost:8080/records.html`         |
| Record Detail       | `record-detail.html`    | `http://localhost:8080/record-detail.html`   |
| New / Edit Record   | `record-form.html`      | `http://localhost:8080/record-form.html`     |
| Reports             | `reports.html`          | `http://localhost:8080/reports.html`         |
| Settings            | `settings.html`         | `http://localhost:8080/settings.html`        |
| Admin Panel         | `admin.html`            | `http://localhost:8080/admin.html`           |

---

## Test Credentials

| Username | Password   | Role   |
| -------- | ---------- | ------ |
| `admin`  | `admin123` | Admin  |
