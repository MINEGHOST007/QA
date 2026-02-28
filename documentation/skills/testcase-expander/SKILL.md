---
name: testcase-expander
description: Use this skill whenever you receive a natural-language test-case description and need to produce a fully specified Playwright test plan with exact selectors, URLs, and step-by-step actions.
---

# Test Case Expander Skill

This is the primary skill. It orchestrates keyword lookup and navigation lookup to
transform an informal test description into a precise, runnable Playwright test plan.

## When to Use This Skill

Use this skill when the user provides any of the following:
- A natural-language sentence describing what to test ("verify a user can lock the record")
- A user story ("as an admin I want to approve a submission")
- A brief scenario ("check the login flow with wrong credentials")
- A list of acceptance criteria without technical detail

## Step-by-Step Process

### Phase 0 — Plan With Todos

Before doing any lookups, call `write_todos()` to plan the work:

1. Read the test case and list the distinct action phrases you will look up.
2. Create one todo per lookup group (e.g., "Look up form submission keywords", "Find navigation for record creation").
3. Add a final todo for "Assemble expanded test case".
4. Mark each todo in-progress as you start it and complete as you finish.

This gives you (and the user) a clear progress trail and prevents skipping steps.

### Phase 1 — Understand the Test Case

1. Read the full test case description carefully.
2. Identify the implied **user role** (anonymous, regular user, reviewer, admin).
3. Identify the **starting state** (which page/URL, what data must exist).
4. Break the description into discrete **action phrases**, for example:
   - "navigate to the records list"
   - "filter by status Approved"
   - "click Lock Record"
   - "verify status badge changes to Locked"

### Phase 2 — List Available Documentation

Call `list_docs()`.  
Read the result to confirm `docs/navigation/navigation_guide.md` and
`docs/keywords/keywords_guide.md` exist before proceeding.

### Phase 3 — Extract and Look Up Keywords

For **every UI element or domain term** in the action phrases:

1. Call `find_keyword('<term>')`.
2. If found: record its `data-testid`, CSS selector, and ARIA role.
3. If not found: try synonyms or partial terms via `grep_docs('<partial>', doc_path='keywords/')`.
4. If still not found: note it as "⚠ Not in keywords guide — add entry for `<term>`".

### Phase 4 — Look Up Navigation

For **every major workflow action** in the action phrases:

1. Call `find_navigation_steps('<action verb or feature name>')`.
2. Record the full step sequence, URL, and any role/permission requirement.
3. If not found: try `grep_docs('<synonym>', doc_path='navigation/')`.
4. Note any prerequisites the navigation steps reveal (e.g., "record must be in Approved status").

### Phase 5 — Enrich With Inline Reading (if needed)

If a lookup returns a heading but not enough detail:
1. Call `get_doc_outline('navigation/navigation_guide.md')` or the keywords guide.
2. Identify the section line range.
3. Call `read_doc_section('<file>', <start>, <end>)` for just that section.

### Phase 6 — Verify Lookups

Before writing the final output:
1. Review every selector and URL you plan to include.
2. Confirm each one appeared in an actual tool result (not assumed or guessed).
3. Collect any terms that were NOT found — these go into the "Documentation Gaps" section.
4. Update your todos: mark verification complete.

### Phase 7 — Assemble the Expanded Test Case

Produce output using the exact structure from the AGENTS.md Output Format:

```
## Test Case: <derive a concise title from the description>

### Pre-conditions
- URL: <starting URL from navigation guide>
- User role: <required role>
- Application state: <any data or setup needed>

### Steps

| # | Action | Locator / Selector | Expected Result |
|---|--------|--------------------|-----------------|
| 1 | Navigate to ... | URL: `/path` | Page loads, breadcrumb shows "..." |
| 2 | Click "..." | `[data-testid="btn-..."]` | Modal/panel appears |
...

### Post-conditions
- <final state — status badge value, redirect URL, audit log entry, etc.>

### Key References
- **URLs touched**: `/path1`, `/path2`
- **Selectors used**: `[data-testid="..."]`, ...
- **Keywords Guide entries**: Status Badge, Actions Menu Button, ...
- **Navigation Guide sections**: Lock a Record, ...

### Documentation Gaps (if any)
- ⚠ `<term>` not found in docs — suggest adding to `<guide>`.
```

## Quality Checklist

Before outputting the expanded test plan, confirm:

- [ ] Every step has exactly one locator (no vague "click the button").
- [ ] Pre-conditions list the required role and any data setup.
- [ ] Status transitions reference the correct "before" and "after" values.
- [ ] Modals: the test waits for the modal to be visible before interacting.
- [ ] All `data-testid` values were found in the keywords guide (not invented).
- [ ] Post-conditions capture all observable side-effects (toast, redirect, log entry).

## Examples of Good Expanded Steps

| # | Action | Locator / Selector | Expected Result |
|---|--------|--------------------|-----------------|
| 1 | Navigate to records list | URL: `/records` | Records table visible |
| 2 | Open record with ID 42 | `[data-testid="records-table-row"]` (row for ID 42) | Detail page loads at `/records/42` |
| 3 | Open Actions menu | `[data-testid="btn-actions-menu"]` | Dropdown with "Lock Record" option |
| 4 | Click "Lock Record" | `[data-testid="action-lock-record"]` | Lock confirmation modal appears |
| 5 | Confirm lock | `[data-testid="btn-confirm-lock"]` | Modal closes |
| 6 | Verify status badge | `[data-testid="status-badge"]` | Text is "Locked", class is `.badge--locked` |
| 7 | Verify lock icon | `[data-testid="record-lock-icon"]` | Lock icon is visible |
| 8 | Verify edit disabled | `[data-testid="btn-edit-record"]` | Button is disabled (`disabled` attribute set) |
