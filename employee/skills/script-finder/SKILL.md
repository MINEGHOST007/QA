---
name: script-finder
description: Use this skill when you receive a user test case + expanded test plan and need to find the 2 most similar old Selenium scripts with their XPaths and step-by-step process.
---

# Script Finder Skill

This is the primary skill. It orchestrates index lookup, grep search, TF-IDF similarity,
and script reading to find the 2 most relevant old Selenium scripts for a given test case.

## When to Use This Skill

Use this skill when the user provides:
- A user test case (e.g. "Submit the form and verify success message")
- An expanded test plan from the Documentation Agent (with steps, selectors, URLs)
- Or just a natural-language description if no expanded plan is available

## Step-by-Step Process

### Phase 0 — Plan With Todos

Before doing any searches, call `write_todos()` to plan the work:

1. Read the user test case AND the expanded test plan.
2. Extract search terms from both inputs.
3. Create todos: "Search index for <feature>", "Grep for <selector>", "Grep for <action pattern>", "Read top candidates", "Rank and output".
4. Mark each todo in-progress/complete as you go.

### Phase 1 — Mine the Expanded Test Plan (Highest Priority)

The expanded test plan is your **best source of search terms**. Extract:

1. **Selectors** — every `data-testid` value (e.g. `btn-submit-record`, `toast-success`). These can be grepped directly and are highest-signal.
2. **URLs** — page paths like `/records/new`, `/forms/contact`. These reveal which feature area the scripts cover.
3. **Action verbs** — "Click submit button", "Verify success toast", "Fill required fields". Map these to Selenium patterns like `click()`, `send_keys()`, `find_element`.
4. **Field names** — specific form fields, dropdowns, textareas mentioned in the steps.

**Example extraction** from the form-submission expanded plan:
- Selectors: `btn-submit-record`, `toast-success`, `input-record-title`, `select-record-type`
- URLs: `/records/new`, `/records/:newId`
- Actions: submit (click), fill (send_keys), verify (assert/wait)
- Feature: form submission, success message

### Phase 2 — Fast Index Search

Call `search_index('<feature keywords>')` with the primary feature name from the user test case.

- Use high-level terms: "form submission", "login", "record approval", "export report".
- If results look promising, note the top 3-5 candidates.
- If too broad, try more specific terms from the expanded plan steps.

### Phase 3 — Targeted Grep Search (Selector-Based)

For each selector extracted from the expanded test plan, grep across the scripts:

1. **By selector fragment**: `grep_scripts('submit.*btn')`, `grep_scripts('success.*message')`, `grep_scripts('toast')`.
2. **By feature name**: `grep_scripts('def test_.*form')` to find test methods about forms.
3. **By XPath/selector pattern**: `grep_scripts('data-testid.*form')` for scripts using similar testids.
4. **By action pattern**: `grep_scripts('click\\(\\)|send_keys|find_element.*submit')` for action patterns matching the expanded plan steps.
5. **By assertion**: `grep_scripts('assert.*success|assert.*Thank')` for verification patterns matching expected results.

Cross-reference grep results with index candidates to build confidence.

### Phase 4 — Semantic Similarity (if needed)

If index + grep haven't found clear matches:

```
find_similar_scripts('<full test case + key selectors from expanded plan>')
```

Include both the user test case text AND key selector names in the query for better matching.

### Phase 5 — Read Top Candidates

For the top 2-4 candidates:

1. Call `get_script_outline('<path>')` to see the structure.
2. Call `read_script('<path>')` to read the full code.
3. Extract:
   - All XPaths and CSS selectors used
   - The step-by-step test flow (setup → actions → assertions → teardown)
   - Map each script step to the corresponding expanded plan step
   - Any page object patterns or helper methods

### Phase 6 — Rank and Select

Compare candidates against BOTH the user test case and expanded plan:
- **Feature match**: Does the script test the same feature?
- **Selector overlap**: Do the script's XPaths correspond to the expanded plan's `data-testid` selectors?
- **Step overlap**: How many test steps match the expanded plan steps?
- **Assertion coverage**: Does it verify similar outcomes?

Select the **2 best matches**. If only 1 is relevant, say so. If none match, explain why.

### Phase 7 — Produce Output

Follow the output format from AGENTS.md:
- XPaths table with Expanded Plan Match column
- Step-by-step process mapped to expanded plan steps
- **Selector Mapping table** — map each expanded plan selector to its Selenium equivalent
- Search strategy summary
- Gaps and notes (which expanded plan steps have NO script coverage)

## Example: Form Submission Test Case

**Input**:
- User test case: "Submit the form and verify success message"
- Expanded plan selectors: `btn-submit-record`, `toast-success`

**Search strategy**:
1. `search_index('form submission')` → finds `test_form_submission.py`
2. `grep_scripts('submit.*btn')` → hits in `test_form_submission.py` (SUBMIT_BUTTON)
3. `grep_scripts('success.*message')` → hits in `test_form_submission.py` (SUCCESS_MESSAGE)
4. `read_script('test_form_submission.py')` → full code with XPaths
5. Map: `btn-submit-record` ↔ `form-submit-btn`, `toast-success` ↔ `form-success-message`

## Tips for Effective Searching

- **Mine the expanded plan first**: Selectors from the Documentation Agent are your best grep targets.
- **Layer your searches**: index → selector grep → action grep → TF-IDF. Each layer catches what the previous missed.
- **Grep for page objects**: Many scripts use page object patterns — `grep_scripts('class.*Page')`.
- **Look for setup methods**: `grep_scripts('def setUp|def setUpClass')` reveals test prerequisites.
