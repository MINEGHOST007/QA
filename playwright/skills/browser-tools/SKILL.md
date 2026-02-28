---
name: browser-tools
description: Use this skill to understand how to use Playwright MCP browser tools for navigating, finding elements, filling forms, clicking buttons, and verifying page state.
---

# Browser Tools Skill

A reference guide for the Playwright MCP browser tools available to this agent.
These tools control a real browser and are loaded dynamically from `@playwright/mcp`.

## Tool Reference

### Navigation Tools

| Tool | When to Use | Key Arguments | Notes |
|------|-------------|---------------|-------|
| `browser_navigate` | Go to a URL | `url` | Always call snapshot after |
| `browser_navigate_back` | Go back in history | — | Like clicking browser Back |
| `browser_navigate_forward` | Go forward in history | — | Like clicking browser Forward |

### Observation Tools (SAFE — no human approval needed)

| Tool | When to Use | Key Arguments | Notes |
|------|-------------|---------------|-------|
| `browser_snapshot` | **Before EVERY interaction** | — | Returns accessibility tree with element refs |
| `browser_take_screenshot` | Visual debugging, final report | — | Returns a screenshot image |
| `browser_console_messages` | Check for JS errors | — | Returns browser console log |
| `browser_wait_for` | Wait for text/element | `text` | Blocks until text appears on page |

### Interaction Tools (MUTATION — requires human approval)

| Tool | When to Use | Key Arguments | Notes |
|------|-------------|---------------|-------|
| `browser_click` | Click a button, link, checkbox | `element` (ref from snapshot) | ⚠ Requires approval |
| `browser_type` | Type text into an input field | `element`, `text` | ⚠ Requires approval |
| `browser_select_option` | Select from a dropdown | `element`, `values` | ⚠ Requires approval |
| `browser_hover` | Hover to reveal menus/tooltips | `element` | ⚠ Requires approval |
| `browser_press_key` | Press keyboard keys | `key` (e.g., "Enter", "Tab", "PageDown") | ⚠ Requires approval |
| `browser_drag` | Drag and drop | `startElement`, `endElement` | ⚠ Requires approval |
| `browser_file_upload` | Upload a file | `paths` | ⚠ Requires approval |
| `browser_run_code` | Run arbitrary JS in page context | `code` (async function) | ⚠ Requires approval. Last resort. |

### Tab Management Tools (SAFE)

| Tool | When to Use | Key Arguments | Notes |
|------|-------------|---------------|-------|
| `browser_tab_list` | See open tabs | — | Returns list of tabs |
| `browser_tab_new` | Open a new tab | `url` | — |
| `browser_tab_select` | Switch to a tab | `index` | — |
| `browser_tab_close` | Close a tab | `index` | — |

## Element Discovery Process

This is the most critical part of using Playwright MCP tools. Understanding how
`browser_snapshot` works is essential.

### How `browser_snapshot` Works

`browser_snapshot` returns an **accessibility tree** — a structured representation
of all interactive elements on the page. Each element has:

- **ref** — a unique identifier (e.g., `ref="e42"`) used to reference the element in other tool calls
- **role** — the ARIA role (e.g., `button`, `textbox`, `link`, `heading`)
- **name** — the accessible name (visible label, aria-label, or alt text)
- **value** — current value (for inputs)
- **description** — additional description
- **state** — disabled, checked, expanded, etc.

### How to Find an Element

Given a selector from the test plan (e.g., `[data-testid="btn-submit"]`):

1. **Call `browser_snapshot`** — get the current accessibility tree.
2. **Search by accessible name** — look for an element whose `name` matches the expected button/input label.
   - Example: For `[data-testid="btn-submit"]`, the button might have name "Submit" or "Submit Record".
3. **Search by role** — narrow by role type (button, textbox, link, etc.).
4. **Use the ref** — once found, use the `ref` value as the `element` argument:
   ```
   browser_click(element="e42")
   ```

### Important: Snapshot Refs Are Ephemeral

> ⚠️ Refs from `browser_snapshot` are **ONLY VALID until the next page change**.
>
> If you navigate, click something that triggers navigation, or the page dynamically
> updates, you MUST call `browser_snapshot` again to get fresh refs.
>
> Using a stale ref will cause an error or click the wrong element.

### Element Not Found — Recovery Steps

If you can't find an element matching the test plan selector:

1. **Scroll down** — the element might be below the fold:
   ```
   browser_press_key(key="PageDown")
   browser_snapshot()  // Get new refs after scrolling
   ```
2. **Take a screenshot** — visual inspection helps:
   ```
   browser_take_screenshot()
   ```
3. **Try alternative names** — the element may have a different label than expected:
   - Check Message 3 (Employee Agent) for alternative selector hints
   - Try partial name match (e.g., "Submit" instead of "Submit Record")
4. **Wait for it** — the element might load asynchronously:
   ```
   browser_wait_for(text="Submit")
   browser_snapshot()
   ```
5. **Check for modals/overlays** — the element might be behind a modal:
   - Look for modal/dialog elements in the snapshot
   - Close the modal first if needed
6. **Give up gracefully** — mark the step as FAIL with "Element not found" and continue.

## Common Patterns

### Fill a Form

```
1. browser_snapshot()           // Get form field refs
2. browser_type(element="e10", text="John")     // First name
3. browser_type(element="e11", text="Doe")      // Last name
4. browser_select_option(element="e12", values=["admin"])  // Role dropdown
5. browser_snapshot()           // Verify fields are filled
```

### Submit and Verify

```
1. browser_click(element="e15")     // Click submit button
2. browser_wait_for(text="Success") // Wait for success message
3. browser_snapshot()               // Verify final state
```

### Navigate and Inspect

```
1. browser_navigate(url="http://localhost:8080/records")
2. browser_snapshot()               // See what's on the page
3. browser_take_screenshot()        // Visual verification
```
