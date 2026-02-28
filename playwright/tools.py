"""
Playwright IFT Agent — Custom Tools

Read-only tools for Postman collection parsing and SOAP request construction.
These tools help the agent understand and prepare API requests from Postman
collections without executing them — actual execution goes through browser_run_code
with human-in-the-loop approval.

Tools exposed to the agent:
    list_postman_collections, read_postman_collection,
    get_postman_request, build_curl_command
"""

import json
from pathlib import Path
from typing import Any

from langchain_core.tools import tool

# ---------------------------------------------------------------------------
# Paths — everything is relative to this file's directory (playwright/)
# ---------------------------------------------------------------------------
PLAYWRIGHT_DIR = Path(__file__).parent          # playwright/
POSTMAN_DIR = PLAYWRIGHT_DIR / "postman"        # playwright/postman/


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _find_collection_file(collection_name: str) -> Path | None:
    """Find a collection file by name (with or without .json extension)."""
    if not POSTMAN_DIR.exists():
        return None

    # Try exact match first
    exact = POSTMAN_DIR / collection_name
    if exact.exists() and exact.is_file():
        return exact

    # Try with .json extension
    with_ext = POSTMAN_DIR / f"{collection_name}.json"
    if with_ext.exists():
        return with_ext

    # Try case-insensitive match
    for f in POSTMAN_DIR.iterdir():
        if f.is_file() and f.stem.lower() == collection_name.lower():
            return f

    return None


def _extract_requests(items: list[dict], folder_path: str = "") -> list[dict]:
    """Recursively extract requests from a Postman collection item tree."""
    requests = []
    for item in items:
        current_path = f"{folder_path}/{item.get('name', '?')}" if folder_path else item.get("name", "?")

        if "request" in item:
            req = item["request"]
            entry = {
                "name": item.get("name", "Unnamed"),
                "folder": folder_path or "(root)",
                "method": req.get("method", "GET"),
                "url": _extract_url(req.get("url", "")),
            }

            # Extract headers
            headers = req.get("header", [])
            if headers:
                entry["headers"] = [
                    f"{h.get('key', '?')}: {h.get('value', '?')}"
                    for h in headers if isinstance(h, dict)
                ]

            # Extract body (truncated for overview)
            body = req.get("body", {})
            if body:
                raw = body.get("raw", "")
                if raw:
                    entry["body_type"] = body.get("mode", "raw")
                    entry["body_preview"] = raw[:200] + ("..." if len(raw) > 200 else "")
                    entry["body_length"] = len(raw)

            requests.append(entry)

        # Recurse into sub-items (folders)
        if "item" in item:
            requests.extend(_extract_requests(item["item"], current_path))

    return requests


def _extract_url(url_obj: Any) -> str:
    """Extract URL string from Postman's URL object format."""
    if isinstance(url_obj, str):
        return url_obj
    if isinstance(url_obj, dict):
        return url_obj.get("raw", "")
    return str(url_obj)


# ---------------------------------------------------------------------------
# LangChain tools — exposed to the agent
# ---------------------------------------------------------------------------

@tool
def list_postman_collections() -> str:
    """List available Postman collection JSON files in the playwright/postman/ directory.

    Returns the name, description, and request count for each collection found.
    Call this to see what API collections are available for the current test.
    """
    if not POSTMAN_DIR.exists():
        return (
            "No postman/ directory found. Create playwright/postman/ and add "
            "Postman collection JSON files to enable API request testing."
        )

    json_files = sorted(POSTMAN_DIR.glob("*.json"))
    if not json_files:
        return (
            "postman/ directory exists but contains no .json files. "
            "Export a Postman collection and save it here."
        )

    entries: list[str] = []
    for f in json_files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            info = data.get("info", {})
            name = info.get("name", f.stem)
            desc = info.get("description", "(no description)")[:100]
            items = data.get("item", [])
            req_count = len(_extract_requests(items))
            entries.append(
                f"  **{f.name}**\n"
                f"    Name: {name}\n"
                f"    Description: {desc}\n"
                f"    Requests: {req_count}"
            )
        except (json.JSONDecodeError, OSError) as exc:
            entries.append(f"  **{f.name}** — Error reading: {exc}")

    return f"Postman collections ({len(json_files)} files):\n\n" + "\n\n".join(entries)


@tool
def read_postman_collection(collection_name: str) -> str:
    """Read and parse a Postman collection, showing all requests with their methods, URLs, and body previews.

    Use this to get an overview of what API requests are available in a collection.
    For the full request body, use get_postman_request() with the specific request name.

    Args:
        collection_name: The filename of the collection (with or without .json extension),
                         e.g. "my_api_collection" or "my_api_collection.json".
    """
    filepath = _find_collection_file(collection_name)
    if filepath is None:
        return (
            f"Collection '{collection_name}' not found in postman/. "
            "Use list_postman_collections() to see available files."
        )

    try:
        data = json.loads(filepath.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return f"Error reading '{collection_name}': {exc}"

    info = data.get("info", {})
    collection_title = info.get("name", filepath.stem)
    items = data.get("item", [])
    requests = _extract_requests(items)

    if not requests:
        return f"Collection '{collection_title}' has no requests."

    lines = [f"**Collection: {collection_title}** ({len(requests)} requests)\n"]

    for i, req in enumerate(requests, 1):
        line = f"\n  {i}. [{req['method']}] {req['name']}"
        line += f"\n     Folder: {req['folder']}"
        line += f"\n     URL: {req['url']}"
        if "headers" in req:
            line += f"\n     Headers: {', '.join(req['headers'][:3])}"
            if len(req["headers"]) > 3:
                line += f" (+{len(req['headers']) - 3} more)"
        if "body_preview" in req:
            line += f"\n     Body ({req['body_type']}, {req['body_length']} chars): {req['body_preview']}"
        lines.append(line)

    return "\n".join(lines)


@tool
def get_postman_request(collection_name: str, request_name: str) -> str:
    """Get the full details of a specific request from a Postman collection.

    Returns the complete URL, all headers, and the FULL request body (not truncated).
    Use this when you need to see the exact XML/JSON body before building a request.

    Args:
        collection_name: The filename of the collection (with or without .json extension).
        request_name: The name of the specific request to retrieve (case-insensitive partial match).
    """
    filepath = _find_collection_file(collection_name)
    if filepath is None:
        return (
            f"Collection '{collection_name}' not found. "
            "Use list_postman_collections() to see available files."
        )

    try:
        data = json.loads(filepath.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return f"Error reading '{collection_name}': {exc}"

    items = data.get("item", [])
    all_requests = _extract_requests_full(items)

    # Find by name (case-insensitive partial match)
    search = request_name.lower()
    matches = [r for r in all_requests if search in r["name"].lower()]

    if not matches:
        names = [r["name"] for r in all_requests]
        return (
            f"Request '{request_name}' not found in collection. "
            f"Available requests: {', '.join(names)}"
        )

    if len(matches) > 1:
        # Return the best match (shortest name containing the search term)
        matches.sort(key=lambda r: len(r["name"]))

    req = matches[0]
    lines = [
        f"**Request: {req['name']}**",
        f"Method: {req['method']}",
        f"URL: {req['url']}",
    ]

    if req.get("headers"):
        lines.append("\nHeaders:")
        for h in req["headers"]:
            lines.append(f"  {h}")

    if req.get("body"):
        lines.append(f"\nBody ({req.get('body_type', 'raw')}):")
        lines.append(req["body"])

    return "\n".join(lines)


def _extract_requests_full(items: list[dict], folder_path: str = "") -> list[dict]:
    """Like _extract_requests but includes the FULL body (not truncated)."""
    requests = []
    for item in items:
        current_path = f"{folder_path}/{item.get('name', '?')}" if folder_path else item.get("name", "?")

        if "request" in item:
            req = item["request"]
            entry = {
                "name": item.get("name", "Unnamed"),
                "folder": folder_path or "(root)",
                "method": req.get("method", "GET"),
                "url": _extract_url(req.get("url", "")),
            }

            headers = req.get("header", [])
            if headers:
                entry["headers"] = [
                    f"{h.get('key', '?')}: {h.get('value', '?')}"
                    for h in headers if isinstance(h, dict)
                ]

            body = req.get("body", {})
            if body:
                raw = body.get("raw", "")
                if raw:
                    entry["body_type"] = body.get("mode", "raw")
                    entry["body"] = raw

            requests.append(entry)

        if "item" in item:
            requests.extend(_extract_requests_full(item["item"], current_path))

    return requests


@tool
def build_curl_command(
    method: str,
    url: str,
    headers: str = "",
    body: str = "",
) -> str:
    """Build a curl command string from request components for human review.

    This does NOT execute the request — it builds the command so the human can
    review it before the agent runs it via browser_run_code using fetch().

    Also generates a browser_run_code-compatible fetch() snippet.

    Args:
        method:  HTTP method (GET, POST, PUT, DELETE, etc.).
        url:     The full request URL.
        headers: Comma-separated header pairs, e.g. "Content-Type: text/xml, SOAPAction: MyAction".
        body:    The request body (XML, JSON, etc.). Can be multi-line.
    """
    # Build curl command
    parts = [f'curl -X {method}']

    if headers:
        for header in headers.split(","):
            header = header.strip()
            if header:
                parts.append(f"  -H '{header}'")

    if body:
        # Escape single quotes in body for curl
        escaped = body.replace("'", "'\\''")
        parts.append(f"  -d '{escaped}'")

    parts.append(f"  '{url}'")
    curl_cmd = " \\\n".join(parts)

    # Build fetch() snippet for browser_run_code
    header_dict = {}
    if headers:
        for h in headers.split(","):
            h = h.strip()
            if ":" in h:
                key, val = h.split(":", 1)
                header_dict[key.strip()] = val.strip()

    fetch_opts = {
        "method": method,
        "headers": header_dict,
    }
    if body:
        fetch_opts["body"] = "<BODY_PLACEHOLDER>"

    fetch_lines = [
        "async (page) => {",
        f"  const response = await page.evaluate(async () => {{",
        f"    const res = await fetch('{url}', {{",
        f"      method: '{method}',",
    ]
    if header_dict:
        fetch_lines.append(f"      headers: {json.dumps(header_dict)},")
    if body:
        # Use template literal for multi-line body
        fetch_lines.append(f"      body: `{body}`,")
    fetch_lines.extend([
        "    });",
        "    const text = await res.text();",
        "    return { status: res.status, statusText: res.statusText, body: text };",
        "  });",
        "  return response;",
        "}",
    ])
    fetch_snippet = "\n".join(fetch_lines)

    return (
        "## Curl Command (for reference)\n\n"
        f"```bash\n{curl_cmd}\n```\n\n"
        "## browser_run_code Snippet (for execution)\n\n"
        f"```javascript\n{fetch_snippet}\n```\n\n"
        "> ⚠️ This request requires human approval before execution."
    )


# ---------------------------------------------------------------------------
# Convenience: all custom tools in a list for easy import
# ---------------------------------------------------------------------------

ALL_TOOLS = [
    list_postman_collections,
    read_postman_collection,
    get_postman_request,
    build_curl_command,
]
