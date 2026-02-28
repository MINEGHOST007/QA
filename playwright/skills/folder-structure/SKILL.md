---
name: folder-structure
description: Use this skill to understand the layout of the Playwright IFT agent directory before starting a test, or when you need to locate files.
---

# Folder Structure Skill

## Playwright IFT Agent Layout

```
playwright/
├── AGENTS.md                         # Agent identity, workflow, safety rules, output format
├── playwright.py                     # Main agent entry point (run this file)
├── tools.py                          # Custom tools (Postman collection parser)
│
├── postman/                          # Postman collection files (JSON)
│   └── *.json                        # Export collections from Postman and save here
│
├── runs/                             # Saved agent output (written during runs)
│   └── <timestamp>_<slug>.txt        # Full message log from each test execution
│
└── skills/                           # Progressive skill disclosure
    ├── folder-structure/
    │   └── SKILL.md                  # This file — explains the layout
    ├── test-executor/
    │   └── SKILL.md                  # Main skill — full IFT execution workflow
    ├── browser-tools/
    │   └── SKILL.md                  # How to use Playwright MCP browser tools
    └── api-requests/
        └── SKILL.md                  # How to handle SOAP/Postman API requests
```

## Which tool to use for what

### Playwright MCP Tools (loaded dynamically)

| I need to... | Tool to call | Requires HITL? |
|---|---|---|
| Go to a URL | `browser_navigate` | No |
| See page elements and get refs | `browser_snapshot` | No |
| Click a button or link | `browser_click` | ⚠ Yes |
| Type text into an input | `browser_type` | ⚠ Yes |
| Select from a dropdown | `browser_select_option` | ⚠ Yes |
| Wait for text to appear | `browser_wait_for` | No |
| Take a screenshot | `browser_take_screenshot` | No |
| Scroll the page | `browser_press_key` (PageDown) | ⚠ Yes |
| Run JavaScript code | `browser_run_code` | ⚠ Yes |

### Custom Postman Tools (from tools.py)

| I need to... | Tool to call | Requires HITL? |
|---|---|---|
| List available API collections | `list_postman_collections` | No |
| See requests in a collection | `read_postman_collection` | No |
| Get full request details | `get_postman_request` | No |
| Build a curl/fetch command | `build_curl_command` | No |

## How inputs are consumed

- The agent receives **3 separate messages** (not one combined message):
  1. Test case + URL
  2. Documentation Agent output (expanded test plan)
  3. Employee Agent output (suggested Playwright flow)
- Message 2 is the primary test plan. Message 3 is secondary reference.
- The agent never loads all inputs at once into a single analysis — it processes
  steps sequentially, using targeted tool calls.

## How results are saved

- After each test run, the full message log is saved to `runs/`.
- Filename format: `<timestamp>_<test-slug>.txt`
- Contains: all user inputs, agent reasoning, tool calls and results.
