---
name: keyword-lookup
description: Use this skill when you need to find the CSS selector, data-testid, ARIA role, or description of a specific UI element, application term, or domain concept.
---

# Keyword Lookup Skill

## When to Use This Skill

Use this skill when:
- You see a term in a test case (e.g., "status badge", "actions menu", "toast notification")
  and need its exact Playwright locator.
- You know the human-visible label (e.g., "Lock" button) and need the `data-testid`.
- You want to check what status values are valid before asserting on them.

## Lookup Process

### 1. Try the focused keyword tool first

```
find_keyword('<term>')
```

`find_keyword` searches only `docs/keywords/` and returns up to 6 lines of context
per match — usually enough to get the selector and description.

### 2. Review fuzzy / synonym results

The search tools now **automatically** return synonym-expanded and fuzzy heading
matches alongside exact results. Look for lines marked `[synonym]` or `[fuzzy]`
in the output — these are meaning-based matches found via difflib similarity.

- **Exact matches** (marked `>>>`) are highest confidence — use directly.
- **Synonym matches** (marked `[synonym: '...']`) matched a known synonym of your term.
- **Fuzzy matches** (marked `[fuzzy]`, with a score) are approximate — verify by
  reading the full section with `get_doc_outline` + `read_doc_section` before using.

If no results at all (exact + fuzzy), try a shorter sub-term or a different word:

### 3. If you find a heading but need the full entry

```
get_doc_outline('keywords/keywords_guide.md')
read_doc_section('keywords/keywords_guide.md', <start>, <end>)
```

Use the line numbers from the outline to read only the relevant section.

### 4. Report the result

For each found term, extract and report:
- **`data-testid`** (primary Playwright locator)
- **CSS class** (for class-based assertions)
- **ARIA role** (for `getByRole` patterns)
- **Playwright snippet** (if the guide provides one)
- **Notes** (e.g., "required field", "admin only", "appears only when status=Locked")

If not found:
```
⚠ Term '<term>' not found in docs/keywords/keywords_guide.md.
  Suggestion: Add an entry with selector, data-testid, and description.
```

## Priority Selector Order

When a guide entry lists multiple locators, prefer in this order:
1. `data-testid` attribute — most stable
2. ARIA role + accessible name — `getByRole('button', { name: '...' })`
3. CSS class — only if the above are unavailable
4. XPath — last resort, not recommended
