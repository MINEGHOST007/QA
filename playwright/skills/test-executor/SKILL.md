---
name: test-executor
description: Use this skill when you receive a test case, documentation agent output, and employee agent output, and need to execute the test on a live website using Playwright MCP browser tools.
---

# Test Executor Skill

This is the primary skill. It orchestrates the full IFT (Integration Functional Test)
execution: parsing inputs, navigating the browser, interacting with elements, verifying
results, and producing a structured PASS/FAIL report.

## When to Use This Skill

Use this skill when:
- You receive 3 messages: test case + URL, documentation agent output, employee agent output
- You need to execute a test on a live website
- You need to produce a PASS/FAIL report

## Step-by-Step Process

### Phase 0 — Plan With Todos

Before doing anything, call `write_todos()` to plan the work:

1. Parse the 3 input messages.
2. Create one todo per test step from the Documentation Agent's steps table.
3. Add a todo for "Take final screenshot" and "Produce report".
4. Mark each todo in-progress/complete as you go.

### Phase 1 — Parse Inputs

Read all 3 messages and extract:

**From Message 1 (Task):**
- Test case description (what to test)
- Target URL (where to navigate)

**From Message 2 (Doc Agent Output):**
- Pre-conditions (required role, starting state)
- Steps table — this is your primary test plan:
  - Each row: step number, action description, locator/selector, expected result
- Post-conditions (what to verify at the end)
- Key References (all selectors and URLs used)

**From Message 3 (Emp Agent Output):**
- Suggested MCP tool steps — secondary reference, may be outdated
- Element discovery hints (data-testid values, label text, roles)
- Fallback `browser_run_code` JS function — use only if step-by-step fails
- Known Gaps — things that may have changed since old scripts were written

### Phase 2 — Navigate & Initial Snapshot

1. Call `browser_navigate` with the target URL from Message 1.
2. Call `browser_snapshot` to get the initial page structure.
3. Verify: Does the page title/content match expected pre-conditions?
4. If the page requires login first, follow the login flow from the Doc Agent output.

### Phase 3 — Execute Each Step

For each step from Message 2's steps table:

1. **Snapshot** — Call `browser_snapshot` to get current element refs.
   - NEVER reuse refs from a previous snapshot. Page state may have changed.

2. **Find the element** — Match the selector from the test plan:
   - Look for the element description in the accessibility tree
   - Try matching by accessible name, role, or data-testid hint
   - See the `browser-tools` skill for detailed element discovery

3. **Perform the action** — Based on the step action:
   - "Navigate to..." → `browser_navigate`
   - "Click..." → `browser_click` with the element ref
   - "Fill..." / "Type..." → `browser_type` with element ref and text value
   - "Select..." → `browser_select_option` with element ref and value
   - "Verify..." / "Check..." → no action needed, just verify in step 5
   - "Wait for..." → `browser_wait_for` with the expected text

4. **Handle element not found:**
   - Try fallback selectors from Message 3's "How to Find Elements" section
   - Scroll down: `browser_press_key` with key "PageDown", then snapshot again
   - Take a screenshot: `browser_take_screenshot` for visual debugging
   - If still not found: mark step as FAIL with reason "Element not found"

5. **Verify expected result** — After the action:
   - Snapshot again to see the new page state
   - Check if the expected result from the steps table matches
   - If expected text should appear: look for it in the snapshot
   - If URL should change: check current URL
   - Mark step as PASS or FAIL

6. **Update todos** — Mark the step checkpoint as complete.

### Phase 4 — Handle API Steps (if applicable)

If the test case mentions API requests, SOAP calls, or Postman collection:

1. Follow the `api-requests` skill.
2. Build the request using Postman tools.
3. Show to human for approval.
4. Execute via `browser_run_code`.
5. Verify the API response.

### Phase 5 — Final Verification

1. Take a final `browser_take_screenshot` for the report.
2. Check post-conditions from Message 2:
   - Correct URL?
   - Expected elements visible?
   - Status badges / toast messages?
3. Call `browser_snapshot` one last time to capture final state.

### Phase 6 — Produce Report

Generate the report using the format from AGENTS.md:

1. Overall status: PASS (all steps passed), FAIL (any step failed), PARTIAL (some passed, some failed).
2. Step results table with each step's action, expected, actual, and status.
3. Gaps found — elements not found, unexpected page structure.
4. Screenshots taken — list what was captured.
5. Notes — observations and suggestions.

## Quality Checklist

Before producing the final report, confirm:

- [ ] Every step from Message 2's table was attempted (not skipped).
- [ ] Every PASS result was verified with a post-action snapshot.
- [ ] Every FAIL result has a clear reason (element not found, unexpected result, etc.).
- [ ] At least one screenshot was taken (initial page + final state).
- [ ] Post-conditions from Message 2 were checked.
- [ ] Gaps section lists specific things that differed from the test plan.

## Tips

- **Doc output is authoritative**: Use Message 2's steps as your primary plan. Message 3 is fallback.
- **Test data from Message 3**: The Employee Agent may include specific test values (e.g., "username: admin"). Use those.
- **Snapshot frequency**: At minimum, snapshot before the first interaction, after every navigation, and before the final report. More is better.
- **Don't over-think**: If a step is "Navigate to /records", just call `browser_navigate`. No need for elaborate analysis.
