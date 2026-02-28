"""
Fuzzy / meaning-aware search utilities for the Documentation Agent.

Uses only Python stdlib (difflib + re) — zero external dependencies.

Three layers of matching (all merged into one result):
  1. Synonym expansion  — maps "dialog" → also try "modal", "popup", etc.
  2. difflib fuzzy match — compares query against ### headings in .md files
  3. Context extraction  — returns surrounding lines for each matched heading

Public API:
    fuzzy_search(term, search_root, context_lines=6) -> str
    expand_synonyms(term) -> list[str]
    build_heading_index(search_root) -> list[HeadingEntry]
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from itertools import product
from pathlib import Path
from typing import Sequence


# ---------------------------------------------------------------------------
# 1. Synonym map — easy to extend: just add a new frozenset to the list
# ---------------------------------------------------------------------------

_SYNONYM_GROUPS: list[frozenset[str]] = [
    frozenset({"dialog", "modal", "popup", "dialogue"}),
    frozenset({"button", "btn", "cta"}),
    frozenset({"toast", "notification", "snackbar", "alert", "message"}),
    frozenset({"input", "field", "textbox", "text input"}),
    frozenset({"submit", "save", "confirm", "send"}),
    frozenset({"delete", "remove", "destroy", "trash"}),
    frozenset({"spinner", "loader", "loading", "skeleton"}),
    frozenset({"dropdown", "select", "combobox", "picker"}),
    frozenset({"checkbox", "check", "tick"}),
    frozenset({"error", "validation", "invalid"}),
    frozenset({"success", "saved", "created", "done"}),
    frozenset({"sidebar", "nav", "navigation", "menu"}),
    frozenset({"breadcrumb", "crumb", "trail"}),
    frozenset({"table", "grid", "data table", "data-table"}),
    frozenset({"avatar", "profile", "user menu", "user-menu"}),
    frozenset({"search", "filter", "find", "query"}),
    frozenset({"lock", "locked", "immutable", "freeze"}),
    frozenset({"unlock", "unfreeze"}),
    frozenset({"approve", "approval", "accept"}),
    frozenset({"reject", "rejection", "decline", "deny"}),
    frozenset({"edit", "update", "modify", "change"}),
    frozenset({"create", "new", "add"}),
    frozenset({"record", "entry", "item", "row"}),
    frozenset({"page", "view", "screen"}),
    frozenset({"tab", "section", "panel"}),
    frozenset({"badge", "chip", "pill", "tag", "label"}),
    frozenset({"password", "pwd", "passphrase"}),
    frozenset({"login", "log in", "sign in", "signin", "auth"}),
    frozenset({"logout", "log out", "sign out", "signout"}),
    frozenset({"form", "form fields"}),
    frozenset({"cancel", "dismiss", "close", "abort"}),
    frozenset({"export", "download"}),
    frozenset({"icon", "glyph", "symbol"}),
    frozenset({"status", "state", "lifecycle"}),
    frozenset({"pagination", "paging", "page controls", "next page", "prev page"}),
    frozenset({"attachment", "file upload", "upload", "file input"}),
    frozenset({"comment", "note", "remark"}),
    frozenset({"action", "actions menu", "kebab", "overflow menu", "three dots"}),
]

# Build a fast lookup: token → set of synonyms (including itself)
_SYNONYM_LOOKUP: dict[str, set[str]] = {}
for _group in _SYNONYM_GROUPS:
    for _word in _group:
        _SYNONYM_LOOKUP.setdefault(_word, set()).update(_group)


def _get_synonyms(token: str) -> set[str]:
    """Return the synonym set for a token, or {token} if no synonyms are known."""
    token_lower = token.lower().strip()
    if token_lower in _SYNONYM_LOOKUP:
        return _SYNONYM_LOOKUP[token_lower]
    # Try partial match — e.g. "buttons" matches "button"
    for key, syns in _SYNONYM_LOOKUP.items():
        if token_lower.startswith(key) or key.startswith(token_lower):
            return syns
    return {token_lower}


def expand_synonyms(term: str, max_variants: int = 15) -> list[str]:
    """Expand a multi-word term into synonym variants.

    E.g. "confirm dialog" → ["confirm dialog", "confirm modal", "confirm popup",
    "submit dialog", "submit modal", "submit popup", "save dialog", ...]

    Returns at most *max_variants* patterns (to avoid combinatorial explosion).
    The original term is always first.
    """
    tokens = term.lower().split()
    if not tokens:
        return [term]

    # For each token, get its synonym alternatives
    token_options: list[list[str]] = []
    for tok in tokens:
        syns = sorted(_get_synonyms(tok))
        token_options.append(syns)

    # Cartesian product, capped
    variants: list[str] = []
    for combo in product(*token_options):
        variants.append(" ".join(combo))
        if len(variants) >= max_variants:
            break

    # Ensure original term is first
    term_lower = term.lower()
    if term_lower in variants:
        variants.remove(term_lower)
    variants.insert(0, term_lower)

    return variants[:max_variants]


# ---------------------------------------------------------------------------
# 2. Heading index — extracts ### headings from .md files
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class HeadingEntry:
    """A single ### heading extracted from a markdown file."""
    text: str           # heading text without the ### prefix
    filepath: Path      # absolute path to the .md file
    line_number: int    # 1-based line number
    level: int          # heading level (1 for #, 2 for ##, 3 for ###)


def build_heading_index(search_root: Path) -> list[HeadingEntry]:
    """Scan all .md files under *search_root* and extract headings.

    Returns a list of HeadingEntry sorted by file then line number.
    Results are NOT cached — the caller should cache if needed.
    """
    md_files = sorted(search_root.rglob("*.md")) if search_root.is_dir() else [search_root]
    entries: list[HeadingEntry] = []

    for filepath in md_files:
        try:
            lines = filepath.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for lineno, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped.startswith("#"):
                continue
            # Count heading level
            level = 0
            for ch in stripped:
                if ch == "#":
                    level += 1
                else:
                    break
            text = stripped[level:].strip()
            if text:
                entries.append(HeadingEntry(
                    text=text,
                    filepath=filepath,
                    line_number=lineno,
                    level=level,
                ))

    return entries


# ---------------------------------------------------------------------------
# 3. Fuzzy heading matcher
# ---------------------------------------------------------------------------

def _similarity(a: str, b: str) -> float:
    """Return SequenceMatcher ratio between two lowercased strings."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _fuzzy_match_headings(
    term: str,
    index: list[HeadingEntry],
    threshold: float = 0.40,
    max_results: int = 8,
) -> list[tuple[HeadingEntry, float]]:
    """Find headings similar to *term* (including synonym variants).

    Returns (heading, best_score) pairs sorted by score descending.
    A heading only needs to match ONE synonym variant above *threshold*.
    """
    variants = expand_synonyms(term, max_variants=12)
    scored: dict[HeadingEntry, float] = {}

    for entry in index:
        best = 0.0
        heading_lower = entry.text.lower()
        for variant in variants:
            # Full-string similarity
            s = _similarity(variant, heading_lower)
            best = max(best, s)
            # Also check if the variant is a substring of the heading (strong signal)
            if variant in heading_lower or heading_lower in variant:
                best = max(best, 0.75)
            # Token overlap boost — if most tokens appear in the heading
            variant_tokens = set(variant.split())
            heading_tokens = set(heading_lower.replace("(", " ").replace(")", " ").split())
            if variant_tokens and heading_tokens:
                overlap = len(variant_tokens & heading_tokens) / len(variant_tokens)
                best = max(best, overlap * 0.85)
        if best >= threshold:
            scored[entry] = max(scored.get(entry, 0.0), best)

    results = sorted(scored.items(), key=lambda x: x[1], reverse=True)
    return results[:max_results]


# ---------------------------------------------------------------------------
# 4. Context extractor — reads lines around a heading
# ---------------------------------------------------------------------------

def _extract_heading_context(
    entry: HeadingEntry,
    context_lines: int,
    docs_root: Path,
) -> str:
    """Read lines around a heading entry and format them for display."""
    try:
        lines = entry.filepath.read_text(encoding="utf-8").splitlines()
    except OSError:
        return f"  (could not read {entry.filepath})"

    # Read from the heading line downward until the next heading of same-or-higher level,
    # or up to context_lines * 3 lines (whichever is shorter)
    start = entry.line_number - 1  # 0-based
    max_end = min(len(lines), start + context_lines * 3 + 1)
    end = max_end

    for i in range(start + 1, max_end):
        stripped = lines[i].strip()
        if stripped.startswith("#"):
            # Check if this heading is same-or-higher level
            hlevel = 0
            for ch in stripped:
                if ch == "#":
                    hlevel += 1
                else:
                    break
            if hlevel <= entry.level:
                end = i
                break

    try:
        rel = entry.filepath.relative_to(docs_root)
    except ValueError:
        rel = entry.filepath.name

    block: list[str] = [f"  [fuzzy] L{entry.line_number:4d}: {lines[start]}"]
    for i in range(start + 1, end):
        block.append(f"          L{i + 1:4d}: {lines[i]}")

    return "\n".join(block)


# ---------------------------------------------------------------------------
# 5. Public API — the main fuzzy search function
# ---------------------------------------------------------------------------

def fuzzy_search(
    term: str,
    search_root: Path,
    docs_root: Path,
    context_lines: int = 6,
    threshold: float = 0.40,
) -> str:
    """Run synonym-expanded regex + heading-level fuzzy search.

    Returns formatted text with [synonym] and [fuzzy] labels.
    Designed to be appended to exact-match results from _grep_impl.

    Args:
        term:          The user's search term (natural language).
        search_root:   Directory or file to search within.
        docs_root:     The top-level docs/ directory (for relative path display).
        context_lines: Lines of context around each match.
        threshold:     Minimum difflib similarity score (0.0–1.0).

    Returns:
        Formatted string of fuzzy results, or empty string if nothing found.
    """
    blocks: list[str] = []
    total = 0

    # --- Phase 1: Synonym-expanded regex search ---
    variants = expand_synonyms(term, max_variants=12)
    # Skip the first variant (it's the original term — already searched by exact regex)
    synonym_variants = variants[1:]

    if synonym_variants:
        md_files = sorted(search_root.rglob("*.md")) if search_root.is_dir() else [search_root]
        seen_lines: set[tuple[str, int]] = set()  # (filename, line_index)

        for variant in synonym_variants:
            try:
                regex = re.compile(re.escape(variant), re.IGNORECASE)
            except re.error:
                continue

            for filepath in md_files:
                try:
                    rel = str(filepath.relative_to(docs_root))
                except ValueError:
                    rel = filepath.name
                try:
                    lines = filepath.read_text(encoding="utf-8").splitlines()
                except OSError:
                    continue

                match_indices = [i for i, ln in enumerate(lines) if regex.search(ln)]
                if not match_indices:
                    continue

                file_block: list[str] = []
                for mi in match_indices:
                    key = (rel, mi)
                    if key in seen_lines:
                        continue
                    seen_lines.add(key)

                    if not file_block:
                        file_block.append(f"\n--- docs/{rel} [synonym: '{variant}'] ---")

                    s = max(0, mi - context_lines)
                    e = min(len(lines), mi + context_lines + 1)
                    for i in range(s, e):
                        line_key = (rel, i)
                        if line_key not in seen_lines or i == mi:
                            marker = ">>>" if i == mi else "   "
                            file_block.append(f"  {marker} L{i + 1:4d}: {lines[i]}")
                    file_block.append("")
                    total += 1

                    if total >= 20:
                        break

                blocks.extend(file_block)
                if total >= 20:
                    break
            if total >= 20:
                break

    # --- Phase 2: Heading-level fuzzy search ---
    index = build_heading_index(search_root)
    fuzzy_hits = _fuzzy_match_headings(term, index, threshold=threshold)

    if fuzzy_hits:
        blocks.append("\n--- Fuzzy heading matches ---")
        for entry, score in fuzzy_hits:
            try:
                rel = str(entry.filepath.relative_to(docs_root))
            except ValueError:
                rel = entry.filepath.name
            blocks.append(f"  docs/{rel} — \"{entry.text}\" (score={score:.2f})")
            ctx = _extract_heading_context(entry, context_lines, docs_root)
            blocks.append(ctx)
            blocks.append("")
            total += 1
            if total >= 30:
                break

    if not blocks:
        return ""

    header = f"\n[{total} fuzzy/synonym result(s) for '{term}']\n"
    return header + "\n".join(blocks)
