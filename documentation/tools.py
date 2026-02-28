"""
Documentation Agent — LangChain Tools

All search tools exposed to the agent live here:
    list_docs, get_doc_outline, read_doc_section, grep_docs,
    find_keyword, find_navigation_steps

Internal helpers (_resolve_search_root, _grep_impl, _list_docs_impl)
are also kept here since the tools depend on them directly.
"""

import re
import sys
from pathlib import Path

from langchain_core.tools import tool

# Add project root to sys.path so root-level utils/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.fuzzy_search import fuzzy_search  # noqa: E402

# ---------------------------------------------------------------------------
# Paths — everything is relative to this file's directory (documentation/)
# ---------------------------------------------------------------------------
DOC_DIR = Path(__file__).parent          # documentation/
DOCS_ROOT = DOC_DIR / "docs"            # documentation/docs/


# ---------------------------------------------------------------------------
# Internal helpers (not exposed as LangChain tools)
# ---------------------------------------------------------------------------

def _resolve_search_root(doc_path: str) -> tuple[Path | None, str | None]:
    """Return (resolved_path, error_message).  error_message is None on success."""
    if not doc_path:
        return DOCS_ROOT, None
    full = DOCS_ROOT / doc_path
    if not full.exists():
        return None, (
            f"Path not found: 'docs/{doc_path}'. "
            "Use list_docs() to see what is available."
        )
    return full, None


def _grep_impl(
    pattern: str,
    search_root: Path,
    context_lines: int = 3,
    fuzzy_term: str | None = None,
) -> str:
    """Core grep implementation — returns matching lines with context, capped at 40 matches.

    When *fuzzy_term* is provided, synonym-expanded regex and heading-level
    difflib fuzzy matches are appended after the exact results.
    """
    try:
        regex = re.compile(pattern, re.IGNORECASE)
    except re.error as exc:
        return f"Invalid regex '{pattern}': {exc}"

    md_files = sorted(search_root.rglob("*.md")) if search_root.is_dir() else [search_root]

    all_blocks: list[str] = []
    total_matches = 0

    for filepath in md_files:
        rel = filepath.relative_to(DOCS_ROOT)
        try:
            lines = filepath.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue

        match_indices = [i for i, ln in enumerate(lines) if regex.search(ln)]
        if not match_indices:
            continue

        file_block: list[str] = [f"\n--- docs/{rel} ---"]
        seen: set[int] = set()

        for mi in match_indices:
            s = max(0, mi - context_lines)
            e = min(len(lines), mi + context_lines + 1)
            for i in range(s, e):
                if i not in seen:
                    marker = ">>>" if i == mi else "   "
                    file_block.append(f"  {marker} L{i + 1:4d}: {lines[i]}")
                    seen.add(i)
            file_block.append("")  # blank separator between match clusters

        all_blocks.extend(file_block)
        total_matches += len(match_indices)

        if total_matches >= 40:
            all_blocks.append(
                "  [Limit: 40 matches reached. "
                "Narrow your pattern or add doc_path= to reduce scope.]"
            )
            break

    # --- Fuzzy / synonym layer (always runs when fuzzy_term is provided) ---
    fuzzy_text = ""
    if fuzzy_term:
        fuzzy_text = fuzzy_search(
            term=fuzzy_term,
            search_root=search_root,
            docs_root=DOCS_ROOT,
            context_lines=context_lines,
        )

    if not all_blocks and not fuzzy_text:
        return f"No matches for pattern '{pattern}'."

    parts: list[str] = []
    if all_blocks:
        parts.append(f"[{total_matches} exact match(es) for '{pattern}']\n")
        parts.append("\n".join(all_blocks))
    if fuzzy_text:
        parts.append(fuzzy_text)

    return "\n".join(parts)


def _list_docs_impl() -> str:
    """Return a formatted list of all .md docs with line counts."""
    entries: list[str] = []
    for path in sorted(DOCS_ROOT.rglob("*.md")):
        rel = path.relative_to(DOCS_ROOT)
        with path.open(encoding="utf-8") as fh:
            line_count = sum(1 for _ in fh)
        entries.append(f"  docs/{rel}  ({line_count} lines)")
    if not entries:
        return (
            "No documentation files found under docs/. "
            "Add .md files to docs/navigation/ or docs/keywords/ to get started."
        )
    return "Available documentation:\n" + "\n".join(entries)


# ---------------------------------------------------------------------------
# LangChain tools — exposed to the agent
# ---------------------------------------------------------------------------

@tool
def list_docs() -> str:
    """List all documentation files available for searching, along with their line counts.

    Call this first so you know what reference material is available.
    Returns a structured index of every .md file under docs/.
    """
    return _list_docs_impl()


@tool
def get_doc_outline(doc_path: str) -> str:
    """Return all heading lines (# ## ###) from a documentation file — no body text.

    Use this to understand a file's structure and identify the exact line numbers
    of sections you need, before calling read_doc_section().

    Args:
        doc_path: Path relative to docs/, e.g. "navigation/navigation_guide.md".
    """
    full, err = _resolve_search_root(doc_path)
    if err:
        return err
    assert full is not None  # _resolve_search_root guarantees full is set when err is None
    if full.is_dir():
        return "Provide a file path (not a directory). Use list_docs() to see available files."

    headings: list[str] = []
    with full.open(encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            stripped = line.rstrip()
            if stripped.startswith("#"):
                headings.append(f"  L{lineno:4d}  {stripped}")

    if not headings:
        return f"No headings found in docs/{doc_path}."
    return f"Outline of docs/{doc_path}:\n" + "\n".join(headings)


@tool
def read_doc_section(doc_path: str, start_line: int, end_line: int) -> str:
    """Read a specific line range from a documentation file.

    Use get_doc_outline() first to discover section boundaries, then call this
    tool to read only the lines you need. Keep ranges under 100 lines to stay
    focused — make multiple calls for large sections.

    Args:
        doc_path:   Path relative to docs/, e.g. "keywords/keywords_guide.md".
        start_line: First line to read (1-based, inclusive).
        end_line:   Last line to read (1-based, inclusive).
    """
    full, err = _resolve_search_root(doc_path)
    if err:
        return err
    assert full is not None  # _resolve_search_root guarantees full is set when err is None

    clamp_note = ""
    if end_line - start_line > 100:
        clamp_note = (
            f"\n\n[Range clamped to 100 lines. "
            f"Call again from L{start_line + 100} for the rest.]"
        )
        end_line = start_line + 99

    collected: list[str] = []
    with full.open(encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            if lineno > end_line:
                break
            if lineno >= start_line:
                collected.append(f"{lineno:4d}: {line.rstrip()}")

    if not collected:
        return f"No content in range L{start_line}-L{end_line} of docs/{doc_path}."
    return (
        f"docs/{doc_path}  (L{start_line}–L{end_line}):\n"
        + "\n".join(collected)
        + clamp_note
    )


@tool
def grep_docs(
    pattern: str,
    doc_path: str = "",
    context_lines: int = 3,
) -> str:
    """Search documentation files with a regex pattern and return matching lines + context.

    Never loads full files — returns only matched snippets. Use multiple calls with
    specific patterns rather than one broad search.

    Strategy tips:
    - Specific beats broad: "btn-lock" > "lock"
    - Narrow scope with doc_path: "keywords/" or "navigation/navigation_guide.md"
    - context_lines=5 for full definitions, context_lines=2 for quick existence checks
    - For data-testid values use: "data-testid.*<name>" or just the testid literal

    Args:
        pattern:       Case-insensitive regex. E.g. "status-badge", r"\\.btn-primary", "lock.*record".
        doc_path:      Optional path relative to docs/ to restrict search scope.
                       Leave empty to search all docs.
        context_lines: Lines of context above/below each match (1–8, default 3).
    """
    root, err = _resolve_search_root(doc_path)
    if err:
        return err
    assert root is not None  # _resolve_search_root guarantees root is set when err is None
    return _grep_impl(pattern, root, min(max(int(context_lines), 1), 8), fuzzy_term=pattern)


@tool
def find_keyword(term: str) -> str:
    """Look up a UI element, application term, or domain keyword in the keywords guide.

    Returns the definition, CSS selector, data-testid, ARIA role, and any Playwright
    code snippets documented for the term. Use this before writing any locator.

    Args:
        term: The keyword to find, e.g. "status badge", "actions menu", "toast notification",
              "lock icon", "confirmation modal".
    """
    root = DOCS_ROOT / "keywords"
    if not root.exists():
        return "docs/keywords/ directory not found. Add docs/keywords/keywords_guide.md."
    return _grep_impl(term, root, context_lines=6, fuzzy_term=term)


@tool
def find_navigation_steps(action: str) -> str:
    """Find the step-by-step navigation path for a feature, workflow, or UI action.

    Returns the starting URL, required user role, prerequisite application state,
    each numbered step with selectors, and the resulting URL or side-effect.

    Args:
        action: The feature or action to navigate to, e.g. "lock record", "login",
                "create new record", "approve", "filter records", "export report".
    """
    root = DOCS_ROOT / "navigation"
    if not root.exists():
        return "docs/navigation/ directory not found. Add docs/navigation/navigation_guide.md."
    return _grep_impl(action, root, context_lines=7, fuzzy_term=action)


# ---------------------------------------------------------------------------
# Convenience: all tools in a list for easy import
# ---------------------------------------------------------------------------

ALL_TOOLS = [
    list_docs,
    get_doc_outline,
    read_doc_section,
    grep_docs,
    find_keyword,
    find_navigation_steps,
]
