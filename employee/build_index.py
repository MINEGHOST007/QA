#!/usr/bin/env python3
"""
Script Index Builder — scans employee/scripts/ and creates scripts_index.json

Extracts metadata from every .py file:
  - filename, relative path
  - class names, method names, decorators
  - docstrings (class and method level)
  - import statements
  - XPath/CSS selector counts
  - line count
  - a text summary for TF-IDF search

Usage:
    # From workspace root:
    uv run python employee/build_index.py

    # Or from employee/:
    python build_index.py

    # Rebuild from the employee agent CLI:
    uv run python employee/employee.py --rebuild-index
"""

import ast
import json
import re
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
EMPLOYEE_DIR = Path(__file__).parent
SCRIPTS_DIR = EMPLOYEE_DIR / "scripts"
INDEX_PATH = EMPLOYEE_DIR / "scripts_index.json"


# ---------------------------------------------------------------------------
# AST-based metadata extractor
# ---------------------------------------------------------------------------

def extract_metadata(filepath: Path) -> dict[str, Any] | None:
    """Parse a Python file with AST and extract test script metadata.

    Returns None if the file can't be parsed.
    """
    try:
        source = filepath.read_text(encoding="utf-8")
    except OSError:
        return None

    try:
        tree = ast.parse(source, filename=str(filepath))
    except SyntaxError:
        # Some scripts may have syntax issues — still extract what we can via regex
        return _extract_metadata_regex(filepath, source)

    metadata: dict[str, Any] = {
        "filename": str(filepath.relative_to(SCRIPTS_DIR)),
        "class_names": [],
        "method_names": [],
        "docstring": "",
        "imports": [],
        "xpath_count": 0,
        "css_selector_count": 0,
        "line_count": source.count("\n") + 1,
    }

    # Module-level docstring
    module_doc = ast.get_docstring(tree)
    if module_doc:
        metadata["docstring"] = module_doc[:500]

    for node in ast.walk(tree):
        # Class definitions
        if isinstance(node, ast.ClassDef):
            metadata["class_names"].append(node.name)
            class_doc = ast.get_docstring(node)
            if class_doc and not metadata["docstring"]:
                metadata["docstring"] = class_doc[:500]

        # Method/function definitions
        elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            metadata["method_names"].append(node.name)
            # Capture docstrings from test methods
            if node.name.startswith("test_"):
                method_doc = ast.get_docstring(node)
                if method_doc:
                    metadata["docstring"] += f" | {node.name}: {method_doc[:200]}"

        # Import statements
        elif isinstance(node, ast.Import):
            for alias in node.names:
                metadata["imports"].append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                metadata["imports"].append(node.module)

    # Count XPaths and CSS selectors via regex (more reliable than AST for strings)
    metadata["xpath_count"] = len(re.findall(
        r'(?:By\.XPATH|find_element_by_xpath|XPATH\s*,|xpath\s*=)', source, re.IGNORECASE
    ))
    metadata["css_selector_count"] = len(re.findall(
        r'(?:By\.CSS_SELECTOR|find_element_by_css_selector|CSS_SELECTOR\s*,|css_selector\s*=)',
        source, re.IGNORECASE
    ))

    # Trim docstring
    metadata["docstring"] = metadata["docstring"].strip()[:500]

    return metadata


def _extract_metadata_regex(filepath: Path, source: str) -> dict[str, Any]:
    """Fallback regex-based extraction for files that fail AST parsing."""
    metadata: dict[str, Any] = {
        "filename": str(filepath.relative_to(SCRIPTS_DIR)),
        "class_names": re.findall(r"^class\s+(\w+)", source, re.MULTILINE),
        "method_names": re.findall(r"^\s*def\s+(\w+)", source, re.MULTILINE),
        "docstring": "",
        "imports": re.findall(r"^(?:from|import)\s+([\w.]+)", source, re.MULTILINE),
        "xpath_count": len(re.findall(r'By\.XPATH|find_element_by_xpath|XPATH', source, re.IGNORECASE)),
        "css_selector_count": len(re.findall(r'By\.CSS_SELECTOR|find_element_by_css_selector', source, re.IGNORECASE)),
        "line_count": source.count("\n") + 1,
    }

    # Try to extract docstrings with regex
    doc_match = re.search(r'^"""(.*?)"""', source, re.DOTALL)
    if not doc_match:
        doc_match = re.search(r"^'''(.*?)'''", source, re.DOTALL)
    if doc_match:
        metadata["docstring"] = doc_match.group(1).strip()[:500]

    return metadata


# ---------------------------------------------------------------------------
# Build and save index
# ---------------------------------------------------------------------------

def build_and_save_index() -> int:
    """Scan scripts/ and write scripts_index.json. Returns the number of scripts indexed."""
    if not SCRIPTS_DIR.exists():
        SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Created {SCRIPTS_DIR} — add your Selenium .py scripts here.")
        return 0

    py_files = sorted(SCRIPTS_DIR.rglob("*.py"))
    if not py_files:
        print(f"No .py files found in {SCRIPTS_DIR}.")
        INDEX_PATH.write_text("[]", encoding="utf-8")
        return 0

    index: list[dict[str, Any]] = []
    errors: list[str] = []

    for filepath in py_files:
        rel = filepath.relative_to(SCRIPTS_DIR)
        meta = extract_metadata(filepath)
        if meta:
            index.append(meta)
            n_methods = len(meta.get("method_names", []))
            n_xpaths = meta.get("xpath_count", 0)
            print(f"  ✓ {rel}  ({meta['line_count']} lines, {n_methods} methods, {n_xpaths} xpaths)")
        else:
            errors.append(str(rel))
            print(f"  ✗ {rel}  (failed to parse)")

    # Write index
    with INDEX_PATH.open("w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

    print(f"\nIndex saved to {INDEX_PATH}")
    print(f"  Scripts indexed: {len(index)}")
    if errors:
        print(f"  Errors: {len(errors)} — {', '.join(errors)}")

    return len(index)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print(f"Scanning {SCRIPTS_DIR} for Selenium test scripts...")
    print()
    count = build_and_save_index()
    print(f"\nDone. {count} scripts indexed.")
