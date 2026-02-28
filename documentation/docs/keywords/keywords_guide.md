# Keywords Guide

This guide defines every significant UI element, application term, and domain
concept used across the application. Each entry includes a description, the primary
Playwright-compatible locator, and any alternative selectors or ARIA attributes.

Search this file for a specific term or element to get its selector before writing a test.

---

## Status Values

### Status Badge

**Description**: A coloured chip/pill that shows the current lifecycle status of a record.  
**Selector**: `[data-testid="status-badge"]`  
**ARIA role**: `status`  
**Possible values / colours**:

| Status text    | CSS modifier class                  | Meaning                     |
| -------------- | ----------------------------------- | --------------------------- |
| Draft          | `.badge--draft` (grey)              | Not yet submitted           |
| Pending Review | `.badge--pending` (yellow)          | Awaiting reviewer action    |
| Approved       | `.badge--approved` (green)          | Accepted by reviewer        |
| Rejected       | `.badge--rejected` (red)            | Declined by reviewer        |
| Locked         | `.badge--locked` (blue + lock icon) | Immutable; no further edits |
| Archived       | `.badge--archived` (grey, italic)   | Hidden from default views   |

**Playwright usage**:

```ts
await expect(page.getByTestId("status-badge")).toHaveText("Locked");
await expect(page.getByTestId("status-badge")).toHaveClass(/badge--locked/);
```

---

## Buttons

### Primary Action Button

**Description**: The dominant call-to-action on a page or modal.  
**CSS class**: `.btn-primary`  
**Playwright**: `page.getByRole('button', { name: '<label>' })`

### Secondary Action Button

**Description**: A less prominent action.  
**CSS class**: `.btn-secondary`

### Danger / Destructive Button

**Description**: Buttons that trigger irreversible actions (delete, reject).  
**CSS class**: `.btn-danger`  
**Playwright**: `page.getByRole('button', { name: '<label>' })` — confirm it has class `.btn-danger`.

### Icon Button

**Description**: A button with only an icon (no visible label).  
**ARIA**: must have `aria-label` describing the action.  
**Playwright**: `page.getByRole('button', { name: '<aria-label>' })`

### Actions Menu Button

**Description**: A "kebab" or "Actions ▾" dropdown menu trigger.  
**Selector**: `[data-testid="btn-actions-menu"]`  
**Playwright**:

```ts
await page.getByTestId("btn-actions-menu").click();
await page.getByTestId("action-<action-name>").click();
```

---

## Form Fields

### Text Input

**Selector pattern**: `[data-testid="input-<fieldName>"]`  
**Playwright**: `page.getByTestId('input-<fieldName>').fill('value')`

### Password Input

**Selector**: `[data-testid="input-password"]` (login), `[data-testid="input-new-password"]` (settings).  
**Type attribute**: `type="password"`

### Dropdown / Select

**Selector pattern**: `[data-testid="select-<fieldName>"]`  
**Playwright**: `page.getByTestId('select-<fieldName>').selectOption('value')`

### Date Picker

**Selector pattern**: `[data-testid="datepicker-<fieldName>"]`  
**Playwright**: `page.getByTestId('datepicker-<fieldName>').fill('YYYY-MM-DD')`

### Textarea

**Selector pattern**: `[data-testid="textarea-<fieldName>"]`

### Checkbox

**Selector pattern**: `[data-testid="checkbox-<fieldName>"]`  
**Playwright**: `page.getByTestId('checkbox-<fieldName>').check()` / `.uncheck()`

### Radio Group

**Selector pattern**: `[data-testid="radio-<groupName>-<value>"]`  
**Playwright**: `page.getByTestId('radio-<groupName>-<value>').check()`

### Search Input

**Description**: Full-text search field on list pages.  
**Selector**: `[data-testid="search-input"]`  
**Placeholder**: "Search records…"

---

## Record Form Fields

Fields used on the New Record and Edit Record forms (`/records/new`, `/records/:id/edit`):

| Field label | `data-testid`                 | Type                                      |
| ----------- | ----------------------------- | ----------------------------------------- |
| Title       | `input-record-title`          | text                                      |
| Type        | `select-record-type`          | dropdown                                  |
| Description | `textarea-record-description` | textarea                                  |
| Assignee    | `select-record-assignee`      | dropdown (searchable)                     |
| Due Date    | `datepicker-record-due-date`  | date                                      |
| Priority    | `select-record-priority`      | dropdown (Low / Medium / High / Critical) |
| Attachments | `input-record-attachments`    | file input                                |

---

## Modals and Dialogs

### Confirmation Modal (Generic)

**Description**: A two-button modal (Cancel / Confirm) that gates destructive or workflow actions.  
**Selector**: `[data-testid="modal-confirm"]`  
**Overlay**: `[data-testid="modal-overlay"]`  
**Confirm button**: `[data-testid="btn-confirm-modal"]`  
**Cancel button**: `[data-testid="btn-cancel-modal"]`

Named confirmation modals:

| Action        | Modal selector         | Confirm button          |
| ------------- | ---------------------- | ----------------------- |
| Delete record | `modal-confirm-delete` | `btn-confirm-delete`    |
| Lock record   | `modal-lock`           | `btn-confirm-lock`      |
| Unlock record | `modal-unlock`         | `btn-confirm-unlock`    |
| Approve       | `modal-approve`        | `btn-confirm-approval`  |
| Reject        | `modal-reject`         | `btn-confirm-rejection` |

**Playwright — wait for modal before interacting**:

```ts
await expect(page.getByTestId("modal-lock")).toBeVisible();
await page.getByTestId("btn-confirm-lock").click();
```

### Form Modal

**Description**: A modal that contains a form (e.g., workflow comment).  
**Selector**: `[data-testid="modal-form"]`

### Close / Dismiss Modal

**Button**: `[data-testid="btn-close-modal"]` (×) OR `[data-testid="btn-cancel-modal"]` (Cancel).  
**Keyboard**: `Escape` key closes any modal.

---

## Notifications and Feedback

### Toast Notification

**Description**: Transient success/error message overlaid in a corner.  
**Success**: `[data-testid="toast-success"]`  
**Error**: `[data-testid="toast-error"]`  
**Warning**: `[data-testid="toast-warning"]`  
**Playwright**:

```ts
await expect(page.getByTestId("toast-success")).toBeVisible();
await expect(page.getByTestId("toast-success")).toContainText("saved");
```

### Alert Banner

**Description**: A persistent top-of-page or inline notification (not self-dismissing).  
**Selector pattern**: `[data-testid="alert-<type>"]`  
**Types**: `alert-error`, `alert-warning`, `alert-info`, `alert-success`

### Form Validation Error

**Description**: Per-field red text below an input.  
**Selector pattern**: `[data-testid="field-error-<fieldName>"]`  
**Form-level summary**: `[data-testid="form-error-summary"]`

### Empty State

**Description**: Shown when a list has no results.  
**Selector**: `[data-testid="empty-state-<context>"]`  
**E.g.**: `empty-state-records`, `empty-state-reports`

### Loading Spinner / Skeleton

**Selector**: `[data-testid="loading-spinner"]` (global) or `[data-testid="<context>-loading"]`.  
**Playwright — wait for content to load**:

```ts
await expect(page.getByTestId("loading-spinner")).not.toBeVisible();
```

---

## Navigation Elements

### Sidebar Navigation

**Selector**: `[data-testid="sidebar-nav"]`  
**Collapsed class**: `.sidebar--collapsed`  
**Toggle**: `[data-testid="btn-sidebar-toggle"]`

### Breadcrumb

**Description**: Shows the current page hierarchy.  
**Selector**: `[data-testid="breadcrumb"]`  
**Playwright**: `page.getByTestId('breadcrumb').getByText('<Page Name>')`

### Tab Bar

**Description**: Horizontal row of tabs (e.g., Settings, Record detail sub-sections).  
**Selector pattern**: `[data-testid="tab-<name>"]`  
**Active class**: `.tab--active`

### Pagination Controls

**Selector**: `[data-testid="pagination-controls"]`  
**Next page**: `[data-testid="btn-page-next"]`  
**Previous page**: `[data-testid="btn-page-prev"]`  
**Page size select**: `[data-testid="select-page-size"]`

---

## Tables

### Data Table

**Selector**: `[data-testid="<context>-table"]`  
**E.g.**: `records-table`, `admin-users-table`

### Table Row

**Selector**: `[data-testid="<context>-table-row"]`  
**Specific row by ID**: `[data-testid="<context>-table-row-<id>"]`

### Table Sort Header

**Selector**: `[data-testid="th-sort-<columnName>"]`  
**Ascending class**: `.sort--asc`  
**Descending class**: `.sort--desc`

### Row Action Buttons

**Selector pattern**: `[data-testid="btn-view-record"]`, `[data-testid="btn-edit-record"]`, `[data-testid="btn-delete-record"]` — these appear on each row.

---

## User & Session Elements

### User Avatar Menu

**Description**: Top-right avatar that opens a dropdown with profile/logout links.  
**Selector**: `[data-testid="user-avatar-menu"]`

### Current User Display Name

**Selector**: `[data-testid="user-display-name"]`

### Role Badge

**Description**: Shows the current user's role (e.g., "Admin", "Reviewer").  
**Selector**: `[data-testid="user-role-badge"]`

---

## Workflow-Specific Elements

### Lock Icon (Locked Record Indicator)

**Description**: Renders alongside the status badge when a record is locked.  
**Selector**: `[data-testid="record-lock-icon"]`  
**Playwright**:

```ts
await expect(page.getByTestId("record-lock-icon")).toBeVisible();
```

### Workflow Comment Input

**Description**: Optional/required text area in workflow transition modals.  
**Selector**: `[data-testid="input-workflow-comment"]`

### Approval Note Input

**Selector**: `[data-testid="input-approval-note"]`

### Rejection Reason Input

**Selector**: `[data-testid="input-rejection-reason"]` (required; submit blocked if empty)

### Unlock Justification Input

**Selector**: `[data-testid="input-unlock-reason"]` (required)

### Activity Log

**Description**: Chronological trail of all status changes and comments on a record.  
**Selector**: `[data-testid="activity-log"]`  
**Latest entry**: `[data-testid="activity-log"] >> .log-entry:first-child`

---

## URLs Reference

| Page                | URL pattern                    |
| ------------------- | ------------------------------ |
| Login               | `/login`                       |
| Dashboard           | `/dashboard`                   |
| Records list        | `/records`                     |
| Records filtered    | `/records?status=<s>&type=<t>` |
| Record search       | `/records?q=<term>`            |
| Record detail       | `/records/:id`                 |
| New record          | `/records/new`                 |
| Edit record         | `/records/:id/edit`            |
| Reports list        | `/reports`                     |
| Report detail       | `/reports/:reportId`           |
| Settings            | `/settings`                    |
| Settings – Profile  | `/settings/profile`            |
| Settings – Security | `/settings/security`           |
| Admin               | `/admin`                       |
| Admin – Users       | `/admin/users`                 |
| Admin – Roles       | `/admin/roles`                 |
| Forgot password     | `/forgot-password`             |
