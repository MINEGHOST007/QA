"""
Employee Agent — LangChain Tools

All search tools exposed to the Employee (Retired Selenium Script Finder) agent:
    list_scripts, search_index, get_script_outline, read_script,
    grep_scripts, find_similar_scripts

The employee agent receives a single string input containing a user test case
and (optionally) the Documentation Agent's expanded test plan with Playwright
selectors, URLs, and steps.  These tools help the agent grep those selectors
against old Selenium scripts for high-signal matching.

Internal helpers:
    _load_index, _grep_scripts_impl, _tfidf_similarity
"""

import json
import math
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from langchain_core.tools import tool

# Add project root to sys.path so root-level utils/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.fuzzy_search import expand_synonyms  # noqa: E402

# ---------------------------------------------------------------------------
# Paths — everything is relative to this file's directory (employee/)
# ---------------------------------------------------------------------------
EMPLOYEE_DIR = Path(__file__).parent              # employee/
SCRIPTS_DIR = EMPLOYEE_DIR / "scripts"            # employee/scripts/
INDEX_PATH = EMPLOYEE_DIR / "scripts_index.json"  # employee/scripts_index.json


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_index() -> list[dict[str, Any]]:
    """Load the pre-built script index from JSON. Returns empty list if not found."""
    if not INDEX_PATH.exists():
        return []
    try:
        with INDEX_PATH.open(encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _get_script_files() -> list[Path]:
    """Return all .py files under scripts/ sorted by name."""
    if not SCRIPTS_DIR.exists():
        return []
    return sorted(SCRIPTS_DIR.rglob("*.py"))


# ---------------------------------------------------------------------------
# TF-IDF implementation (stdlib only — no sklearn/numpy needed)
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> list[str]:
    """Lowercase tokenization — splits on non-alphanumeric, drops short tokens."""
    return [t for t in re.split(r"[^a-z0-9]+", text.lower()) if len(t) > 1]


def _build_tfidf_corpus(index: list[dict[str, Any]]) -> list[tuple[str, list[str]]]:
    """Build (filename, tokens) pairs from the index for TF-IDF scoring.

    Combines filename, class names, method names, and docstrings into one
    token bag per script.
    """
    corpus: list[tuple[str, list[str]]] = []
    for entry in index:
        text_parts = [
            entry.get("filename", ""),
            " ".join(entry.get("class_names", [])),
            " ".join(entry.get("method_names", [])),
            entry.get("docstring", ""),
        ]
        tokens = _tokenize(" ".join(text_parts))
        corpus.append((entry.get("filename", "unknown"), tokens))
    return corpus


def _tfidf_similarity(
    query: str,
    index: list[dict[str, Any]],
    top_k: int = 5,
) -> list[tuple[str, float, dict[str, Any]]]:
    """Rank scripts by TF-IDF cosine similarity to the query.

    Returns [(filename, score, index_entry), ...] sorted by score descending.
    Pure Python implementation — no external dependencies.
    """
    corpus = _build_tfidf_corpus(index)
    if not corpus:
        return []

    # Expand query with synonyms for better recall
    variants = expand_synonyms(query, max_variants=8)
    query_tokens = []
    for v in variants:
        query_tokens.extend(_tokenize(v))
    query_tokens = list(set(query_tokens))  # deduplicate

    if not query_tokens:
        return []

    # Document frequency
    n_docs = len(corpus)
    df: Counter[str] = Counter()
    for _, tokens in corpus:
        unique = set(tokens)
        for t in unique:
            df[t] += 1

    # IDF
    idf: dict[str, float] = {}
    for t in df:
        idf[t] = math.log((n_docs + 1) / (df[t] + 1)) + 1  # smoothed IDF

    # Query TF-IDF vector
    q_tf = Counter(query_tokens)
    q_vec: dict[str, float] = {}
    for t, count in q_tf.items():
        q_vec[t] = count * idf.get(t, 1.0)

    # Score each document
    results: list[tuple[str, float, dict[str, Any]]] = []
    index_by_name = {e.get("filename", ""): e for e in index}

    for filename, tokens in corpus:
        d_tf = Counter(tokens)
        d_vec: dict[str, float] = {}
        for t, count in d_tf.items():
            d_vec[t] = count * idf.get(t, 1.0)

        # Cosine similarity
        dot = sum(q_vec.get(t, 0) * d_vec.get(t, 0) for t in set(q_vec) | set(d_vec))
        mag_q = math.sqrt(sum(v ** 2 for v in q_vec.values())) or 1.0
        mag_d = math.sqrt(sum(v ** 2 for v in d_vec.values())) or 1.0
        score = dot / (mag_q * mag_d)

        if score > 0.01:
            entry = index_by_name.get(filename, {})
            results.append((filename, score, entry))

    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_k]


# ---------------------------------------------------------------------------
# Grep implementation for scripts
# ---------------------------------------------------------------------------

def _grep_scripts_impl(
    pattern: str,
    search_root: Path,
    context_lines: int = 3,
    max_matches: int = 40,
) -> str:
    """Core grep — search .py files for a regex pattern with context lines."""
    try:
        regex = re.compile(pattern, re.IGNORECASE)
    except re.error as exc:
        return f"Invalid regex '{pattern}': {exc}"

    py_files = sorted(search_root.rglob("*.py")) if search_root.is_dir() else [search_root]

    all_blocks: list[str] = []
    total_matches = 0

    for filepath in py_files:
        rel = filepath.relative_to(SCRIPTS_DIR) if SCRIPTS_DIR in filepath.parents or filepath.parent == SCRIPTS_DIR else filepath.name
        try:
            lines = filepath.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue

        match_indices = [i for i, ln in enumerate(lines) if regex.search(ln)]
        if not match_indices:
            continue

        file_block: list[str] = [f"\n--- scripts/{rel} ---"]
        seen: set[int] = set()

        for mi in match_indices:
            s = max(0, mi - context_lines)
            e = min(len(lines), mi + context_lines + 1)
            for i in range(s, e):
                if i not in seen:
                    marker = ">>>" if i == mi else "   "
                    file_block.append(f"  {marker} L{i + 1:4d}: {lines[i]}")
                    seen.add(i)
            file_block.append("")

        all_blocks.extend(file_block)
        total_matches += len(match_indices)

        if total_matches >= max_matches:
            all_blocks.append(
                f"  [Limit: {max_matches} matches reached. "
                "Narrow your pattern or add script_path= to reduce scope.]"
            )
            break

    if not all_blocks:
        return f"No matches for pattern '{pattern}' in scripts."

    return f"[{total_matches} match(es) for '{pattern}']\n" + "\n".join(all_blocks)


# ---------------------------------------------------------------------------
# LangChain tools — exposed to the agent
# ---------------------------------------------------------------------------

@tool
def list_scripts() -> str:
    """List all indexed Selenium scripts with a compact summary of each.

    Returns filename, line count, number of test methods, and XPath count
    for every script in the library. Call this to get an overview of what's available.
    """
    index = _load_index()
    if not index:
        # Fallback: list raw .py files
        files = _get_script_files()
        if not files:
            return (
                "No scripts found. Add Selenium .py test files to employee/scripts/ "
                "and run build_index.py to create the index."
            )
        entries = []
        for f in files:
            rel = f.relative_to(SCRIPTS_DIR)
            try:
                lc = sum(1 for _ in f.open(encoding="utf-8"))
            except OSError:
                lc = 0
            entries.append(f"  scripts/{rel}  ({lc} lines)")
        return "Scripts (no index — run build_index.py):\n" + "\n".join(entries)

    entries: list[str] = []
    for e in index:
        name = e.get("filename", "?")
        lines = e.get("line_count", 0)
        methods = len(e.get("method_names", []))
        xpaths = e.get("xpath_count", 0)
        entries.append(f"  scripts/{name}  ({lines} lines, {methods} methods, {xpaths} xpaths)")

    return f"Indexed scripts ({len(index)} total):\n" + "\n".join(entries)


@tool
def search_index(query: str) -> str:
    """Search the pre-built script index for scripts matching a keyword query.

    This is the FASTEST search — it matches against filenames, class names,
    method names, and docstrings from the index. Use this before grep or
    similarity search.

    Uses fuzzy/synonym matching automatically. E.g., "form submit" will also
    match "form_submission", "submit_form", "confirm form", etc.

    Args:
        query: Keywords describing the feature or test, e.g. "login wrong password",
               "form submission", "record approval workflow", "export report".
    """
    index = _load_index()
    if not index:
        return (
            "Script index not found. Add scripts to employee/scripts/ "
            "and run: python employee/build_index.py"
        )

    # Expand query with synonyms
    variants = expand_synonyms(query, max_variants=12)
    query_tokens_all: set[str] = set()
    for v in variants:
        query_tokens_all.update(_tokenize(v))

    if not query_tokens_all:
        return f"No searchable tokens in query '{query}'."

    # Score each index entry
    scored: list[tuple[float, dict[str, Any]]] = []
    for entry in index:
        text = " ".join([
            entry.get("filename", ""),
            " ".join(entry.get("class_names", [])),
            " ".join(entry.get("method_names", [])),
            entry.get("docstring", ""),
        ]).lower()

        text_tokens = set(_tokenize(text))
        if not text_tokens:
            continue

        # Token overlap score
        overlap = len(query_tokens_all & text_tokens)
        if overlap == 0:
            continue

        # Bonus for filename match
        fname_tokens = set(_tokenize(entry.get("filename", "")))
        fname_overlap = len(query_tokens_all & fname_tokens)

        score = overlap + fname_overlap * 0.5
        scored.append((score, entry))

    scored.sort(key=lambda x: x[0], reverse=True)

    if not scored:
        return f"No scripts matching '{query}' found in index. Try grep_scripts() or find_similar_scripts()."

    # Return top 10
    results: list[str] = []
    for score, entry in scored[:10]:
        name = entry.get("filename", "?")
        classes = ", ".join(entry.get("class_names", []))
        methods = ", ".join(entry.get("method_names", [])[:5])
        if len(entry.get("method_names", [])) > 5:
            methods += f" (+{len(entry['method_names']) - 5} more)"
        doc = (entry.get("docstring", "") or "")[:120]
        xpaths = entry.get("xpath_count", 0)
        lines = entry.get("line_count", 0)

        results.append(
            f"\n  **scripts/{name}** (score={score:.1f}, {lines} lines, {xpaths} xpaths)\n"
            f"    Classes: {classes or '(none)'}\n"
            f"    Methods: {methods or '(none)'}\n"
            f"    Summary: {doc or '(no docstring)'}"
        )

    return f"[{len(scored)} scripts match '{query}', showing top {min(10, len(scored))}]\n" + "\n".join(results)


@tool
def get_script_outline(script_path: str) -> str:
    """Return the class names, method signatures, and docstrings of a Selenium script.

    Use this to understand a script's structure before reading it in full.
    Much cheaper than read_script() — gives you the skeleton.

    Args:
        script_path: Path relative to scripts/, e.g. "test_login.py" or "auth/test_sso.py".
    """
    full = SCRIPTS_DIR / script_path
    if not full.exists():
        return f"Script not found: scripts/{script_path}. Use list_scripts() to see available files."
    if full.is_dir():
        return "Provide a file path, not a directory. Use list_scripts() to see available files."

    try:
        lines = full.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return f"Error reading scripts/{script_path}: {exc}"

    outline: list[str] = []
    for i, line in enumerate(lines, 1):
        stripped = line.rstrip()
        # Match class definitions, method definitions, and docstrings
        if re.match(r"^\s*(class |def |    \"\"\"|\"\"\"|    \'\'\'|\'\'\')", stripped):
            outline.append(f"  L{i:4d}: {stripped}")
        # Also capture decorators
        elif re.match(r"^\s*@", stripped):
            outline.append(f"  L{i:4d}: {stripped}")

    if not outline:
        return f"No class/method definitions found in scripts/{script_path}."

    return f"Outline of scripts/{script_path} ({len(lines)} lines):\n" + "\n".join(outline)


@tool
def read_script(script_path: str, start_line: int = 1, end_line: int = 0) -> str:
    """Read lines from a Selenium script file.

    Call get_script_outline() first to see the structure, then read specific
    sections. If end_line is 0, reads the entire file (capped at 300 lines).

    Args:
        script_path: Path relative to scripts/, e.g. "test_login.py".
        start_line:  First line to read (1-based, inclusive). Default: 1.
        end_line:    Last line to read (1-based, inclusive). 0 = entire file.
    """
    full = SCRIPTS_DIR / script_path
    if not full.exists():
        return f"Script not found: scripts/{script_path}. Use list_scripts() to see available files."

    try:
        lines = full.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return f"Error reading scripts/{script_path}: {exc}"

    total = len(lines)
    if end_line <= 0:
        end_line = total

    # Clamp
    start_line = max(1, start_line)
    end_line = min(total, end_line)

    clamp_note = ""
    if end_line - start_line >= 300:
        clamp_note = (
            f"\n\n[Range clamped to 300 lines. "
            f"Call again from L{start_line + 300} for the rest.]"
        )
        end_line = start_line + 299

    collected: list[str] = []
    for i, line in enumerate(lines, 1):
        if i > end_line:
            break
        if i >= start_line:
            collected.append(f"{i:4d}: {line}")

    if not collected:
        return f"No content in range L{start_line}-L{end_line} of scripts/{script_path}."

    return (
        f"scripts/{script_path}  (L{start_line}–L{end_line} of {total}):\n"
        + "\n".join(collected)
        + clamp_note
    )


@tool
def grep_scripts(
    pattern: str,
    script_path: str = "",
    context_lines: int = 3,
) -> str:
    """Search Selenium script files with a regex pattern and return matching lines + context.

    This is the most powerful search tool — use it to find specific XPaths, selectors,
    method calls, assertions, or any code pattern across all scripts or within a specific file.

    Strategy tips:
    - Specific beats broad: "find_element.*login" > "login"
    - Search for XPaths: 'XPATH.*"//.*input"' or 'By\\.XPATH'
    - Search for actions: "click\\(\\)|send_keys|find_element"
    - Search for assertions: "assert.*True|assertEqual|assert_element"
    - Search for page objects: "class.*Page"
    - Narrow scope with script_path: "test_login.py" to search just one file

    Args:
        pattern:       Case-insensitive regex. E.g. "find_element.*username", "assert.*success".
        script_path:   Optional path relative to scripts/ to restrict search.
                       Leave empty to search all scripts.
        context_lines: Lines of context above/below each match (1–8, default 3).
    """
    if script_path:
        full = SCRIPTS_DIR / script_path
        if not full.exists():
            return f"Script not found: scripts/{script_path}. Use list_scripts() to see available files."
        search_root = full
    else:
        if not SCRIPTS_DIR.exists():
            return "scripts/ directory not found. Add Selenium test files to employee/scripts/."
        search_root = SCRIPTS_DIR

    return _grep_scripts_impl(
        pattern, search_root, min(max(int(context_lines), 1), 8)
    )


@tool
def find_similar_scripts(query: str, top_k: int = 5) -> str:
    """Find scripts semantically similar to a natural-language query using TF-IDF scoring.

    This is the best tool for natural-language queries like expanded test case descriptions.
    It compares your query against all script metadata (names, classes, methods, docstrings)
    using TF-IDF cosine similarity with automatic synonym expansion.

    Use this when keyword search (search_index) and grep haven't found good matches.

    Args:
        query: Natural language description of the test case or feature.
               E.g., "submit the registration form and verify success message appears"
               or "navigate to admin panel and lock a record after approval".
        top_k: Number of top results to return (default 5, max 10).
    """
    index = _load_index()
    if not index:
        return (
            "Script index not found. Add scripts to employee/scripts/ "
            "and run: python employee/build_index.py"
        )

    top_k = min(max(int(top_k), 1), 10)
    results = _tfidf_similarity(query, index, top_k=top_k)

    if not results:
        return f"No scripts with similarity > 0.01 for query: '{query}'"

    blocks: list[str] = []
    for filename, score, entry in results:
        classes = ", ".join(entry.get("class_names", []))
        methods = ", ".join(entry.get("method_names", [])[:5])
        if len(entry.get("method_names", [])) > 5:
            methods += f" (+{len(entry['method_names']) - 5} more)"
        doc = (entry.get("docstring", "") or "")[:150]
        xpaths = entry.get("xpath_count", 0)
        lines = entry.get("line_count", 0)

        blocks.append(
            f"\n  **scripts/{filename}** (similarity={score:.3f}, {lines} lines, {xpaths} xpaths)\n"
            f"    Classes: {classes or '(none)'}\n"
            f"    Methods: {methods or '(none)'}\n"
            f"    Summary: {doc or '(no docstring)'}"
        )

    return f"[Top {len(results)} similar scripts for '{query[:60]}...']\n" + "\n".join(blocks)


# ---------------------------------------------------------------------------
# Convenience: all tools in a list for easy import
# ---------------------------------------------------------------------------

ALL_TOOLS = [
    list_scripts,
    search_index,
    get_script_outline,
    read_script,
    grep_scripts,
    find_similar_scripts,
]
