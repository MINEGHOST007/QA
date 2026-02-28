---
name: index-lookup
description: Use this skill when you need to quickly find candidate scripts by searching the pre-built index of script metadata (names, classes, methods, docstrings).
---

# Index Lookup Skill

## When to Use This Skill

Use this skill when:
- You have a test case and want to quickly find related scripts by name or description.
- You know a feature name (e.g., "login", "approval", "record creation") and want to see which scripts cover it.
- You want a fast initial scan before doing deeper grep or similarity searches.

## Lookup Process

### 1. Search the index first (fastest)

```
search_index('<keywords>')
```

`search_index` searches the pre-built `scripts_index.json` which contains metadata for every script:
- **filename** — the script file name
- **class_names** — Selenium test class names (e.g., `TestLoginPage`)
- **method_names** — test method names (e.g., `test_valid_login`, `test_wrong_password`)
- **docstring** — class/method docstrings describing what the test does
- **imports** — imported modules (hints at what the script interacts with)
- **xpath_count** — number of XPath expressions (indicates UI interaction density)
- **line_count** — total lines (indicates script complexity)

The search uses fuzzy matching — `"form submit"` will match scripts with `"form_submission"`,
`"submit_form"`, or `"form_submit_test"` in their names/methods/docstrings.

### 2. Narrow with list_scripts if needed

```
list_scripts()
```

Returns a compact index of ALL scripts — useful to scan when you're not sure what keywords to use.

### 3. Get a structural overview

```
get_script_outline('<script_path>')
```

Returns class names, method signatures, and docstrings — without reading the full file.
Use this to decide if a script is worth reading in full.

### 4. Combine with other tools

After finding candidates via the index:
- Use `grep_scripts('<xpath_pattern>', script_path='<file>')` to check for specific XPaths within a candidate.
- Use `read_script('<file>')` to read the full code of the best matches.

## Tips

- **Be specific**: `"login wrong password"` beats `"login"` for targeted results.
- **Use feature names**: `"approval workflow"` will match scripts named `test_approval_*.py`.
- **Check method names**: If a test case says "verify status badge", search for `"status badge"` or `"verify status"`.
- **Index is read-only**: If scripts are added, run `build_index.py` to rebuild the index.
