---
name: navigation-lookup
description: Use this skill when you need the step-by-step path, URL, or permission requirement to reach or perform a specific feature or workflow action in the application.
---

# Navigation Lookup Skill

## When to Use This Skill

Use this skill when:
- A test case mentions a feature by name and you need the URL and click path.
- You need to know the required user role for a workflow action.
- You need the prerequisite state (e.g., "record must be Approved before locking").
- You need the next page/URL after completing an action.

## Lookup Process

### 1. Try the focused navigation tool first

```
find_navigation_steps('<action or feature name>')
```

`find_navigation_steps` searches only `docs/navigation/` and returns 6-line context
windows per match — usually enough to capture a complete step block.

### 2. If not found, try alternative terms

Navigation sections are titled by feature, not always by the exact verb.
Try:
- The noun form: "lock" → try "Lock a Record"
- The module: "lock" → try "Workflow Actions" or "Record"
- An adjacent concept: "approve" → try "Review", "Workflow", "Status"

```
grep_docs('<synonym>', doc_path='navigation/', context_lines=6)
```

### 3. Read the section if partial results came back

```
get_doc_outline('navigation/navigation_guide.md')
read_doc_section('navigation/navigation_guide.md', <start>, <end>)
```

### 4. Report the result

For each found navigation path, extract and report:
- **Starting URL** (where the user must be before step 1)
- **Required role** (if mentioned)
- **Prerequisite status** (e.g., record must be "Approved")
- **Each step** with the exact selector from the guide
- **Resulting URL** after completing the navigation
- **Side effects** visible to the test (status change, toast, redirect)

If not found:
```
⚠ Navigation steps for '<action>' not found in docs/navigation/navigation_guide.md.
  Suggestion: Add a section documenting the URL, steps, and any role requirements.
```

## Important Navigation Patterns

- After **login** → redirects to `/dashboard`
- Actions menu `[data-testid="btn-actions-menu"]` is the entry point for record lifecycle actions
- All workflow transition modals must be **confirmed** (they are two-step: click action → confirm in modal)
- Breadcrumb `[data-testid="breadcrumb"]` is the authoritative indicator of current location
