---
name: folder-structure
description: Use this skill to understand the layout of the documentation library before searching, or when you need to explain the structure to a user.
---

# Folder Structure Skill

## Documentation Library Layout

```
documentation/
├── AGENTS.md                         # Agent identity, workflow, and output format
├── documentation.py                  # Main agent entry point (run this file)
│
├── docs/                             # Reference documentation (search via tools)
│   ├── navigation/
│   │   └── navigation_guide.md       # Step-by-step navigation paths and URLs
│   └── keywords/
│       └── keywords_guide.md         # UI element definitions and Playwright selectors
│
├── memory/                           # Agent session memory (written during runs)
│   └── (agent writes context here)
│
└── skills/                           # Progressive skill disclosure
    ├── folder-structure/
    │   └── SKILL.md                  # This file — explains the layout
    ├── keyword-lookup/
    │   └── SKILL.md                  # How to look up UI element selectors
    ├── navigation-lookup/
    │   └── SKILL.md                  # How to look up navigation steps and URLs
    └── testcase-expander/
        └── SKILL.md                  # Main skill — full test-case expansion workflow
```

## Which file to search for what

| I need to find... | Tool to call | File to search |
|---|---|---|
| A UI element's selector or `data-testid` | `find_keyword()` | `keywords/keywords_guide.md` |
| Valid status values for a record | `find_keyword()` | `keywords/keywords_guide.md` |
| Navigation steps to reach a feature | `find_navigation_steps()` | `navigation/navigation_guide.md` |
| The URL for a page | `grep_docs('URL.*<page>')` | `navigation/navigation_guide.md` |
| A required user role for an action | `find_navigation_steps()` | `navigation/navigation_guide.md` |
| Playwright code snippets | `grep_docs('Playwright')` | Either file |

## How docs are consumed

- The agent **never loads a full doc file** — it uses targeted grep/section tools.
- `grep_docs(pattern, doc_path)` returns only the matching lines + context.
- `get_doc_outline(file)` returns headings-only to navigate to the right section.
- `read_doc_section(file, start, end)` loads a bounded line range.
- Typical test-case expansion uses 4–8 tool calls, not a full file read.

## Adding new docs

To extend the documentation library:
1. Add `.md` files to `docs/navigation/` or `docs/keywords/`.
2. Follow the heading conventions used in the existing guides.
3. Use `[data-testid="..."]` format for selectors (this is what the grep tools target).
4. Call `list_docs()` to verify the new file is indexed.
