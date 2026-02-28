#!/usr/bin/env python3
"""
Documentation Agent — Playwright Test Case Expander

A deep agent that searches through documentation guides to expand natural-language
test cases into fully specified Playwright test plans.

The agent uses targeted grep and section-reader tools to query large documentation
files WITHOUT loading them entirely — keeping context clean and focused.

Architecture:
    - FilesystemBackend rooted at documentation/
    - AGENTS.md  →  loaded as agent memory (identity + output format)
    - skills/    →  progressively loaded skills (testcase-expander, keyword-lookup, etc.)
    - Tools      →  tools.py  — grep, outline, section-reader, keyword finder, navigation finder

Usage:
    # From workspace root:
    uv run python documentation/documentation.py "Submit the form and verify success"
    uv run python documentation/documentation.py --list-docs
    uv run python documentation/documentation.py --model "arcee-ai/trinity-large-preview:free" "Lock the record"
"""

import argparse
import asyncio
import hashlib
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain.agents.middleware import ModelRetryMiddleware
from langchain.agents.middleware.tool_retry import ToolRetryMiddleware
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.spinner import Spinner

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend

# Tools live in documentation/tools.py
from tools import (  # noqa: E402
    ALL_TOOLS,
    list_docs,
    find_keyword,
    find_navigation_steps,
    grep_docs,
    get_doc_outline,
    read_doc_section,
    _list_docs_impl,
)

# ---------------------------------------------------------------------------
# Paths — everything is relative to this file's directory (documentation/)
# ---------------------------------------------------------------------------
DOC_DIR = Path(__file__).parent          # documentation/
DOCS_ROOT = DOC_DIR / "docs"            # documentation/docs/
RUNS_DIR = DOC_DIR / "runs"             # documentation/runs/  — saved outputs

console = Console()


# ---------------------------------------------------------------------------
# Chat history saver
# ---------------------------------------------------------------------------

def save_chat_history(messages: list, testcase: str, output_path: str | None = None) -> Path:
    """Save all agent messages to a formatted txt file.

    Writes to ``documentation/runs/<datetime>.txt`` by default, or to
    *output_path* if the caller supplied ``--output``.

    Returns the Path of the saved file.
    """
    if output_path:
        filepath = Path(output_path)
        filepath.parent.mkdir(parents=True, exist_ok=True)
    else:
        RUNS_DIR.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        # Sanitise testcase for filename (first 40 chars, alphanumeric + hyphens)
        slug = re.sub(r"[^a-z0-9]+", "-", testcase.lower())[:40].strip("-")
        filepath = RUNS_DIR / f"{timestamp}_{slug}.txt"

    lines: list[str] = []
    lines.append(f"Test Case : {testcase}")
    lines.append(f"Timestamp : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 80)
    lines.append("")

    for msg in messages:
        if isinstance(msg, HumanMessage):
            lines.append("[USER]")
            lines.append(str(msg.content))
            lines.append("")

        elif isinstance(msg, AIMessage):
            content = msg.content
            if isinstance(content, list):
                text_parts = [
                    p.get("text", "")
                    for p in content
                    if isinstance(p, dict) and p.get("type") == "text"
                ]
                content = "\n".join(text_parts)

            lines.append("[AGENT]")
            if content and content.strip():
                lines.append(content.strip())

            if msg.tool_calls:
                for tc in msg.tool_calls:
                    name = tc.get("name", "unknown")
                    args = tc.get("args", {})
                    lines.append(f"  >> Tool call: {name}")
                    args_str = str(args)
                    if len(args_str) > 500:
                        args_str = args_str[:500] + "..."
                    lines.append(f"     Args: {args_str}")
            lines.append("")

        elif isinstance(msg, ToolMessage):
            name = getattr(msg, "name", "tool")
            lines.append(f"[TOOL RESULT: {name}]")
            content = str(msg.content)
            if len(content) > 1500:
                content = content[:1500] + "\n... (truncated)"
            lines.append(content)
            lines.append("")

    filepath.write_text("\n".join(lines), encoding="utf-8")
    return filepath


# ---------------------------------------------------------------------------
# Mermaid diagram helper
# ---------------------------------------------------------------------------

def print_mermaid_diagram(agent: Any) -> None:
    """Print the agent's Mermaid graph to the terminal.

    Uses ``agent.get_graph(xray=True).draw_mermaid()`` which returns the
    raw Mermaid text.  Optionally saves a PNG if the SDK supports it.
    """
    try:
        graph = agent.get_graph(xray=True)
    except Exception as exc:
        console.print(f"[yellow]Could not retrieve agent graph: {exc}[/]")
        return

    # --- Text-based Mermaid diagram (always works) ---
    try:
        mermaid_text = graph.draw_mermaid()
        console.print()
        console.print(Panel(
            mermaid_text,
            title="Agent Graph (Mermaid)",
            border_style="cyan",
            subtitle="Paste into https://mermaid.live to visualise",
        ))
    except Exception as exc:
        console.print(f"[yellow]draw_mermaid() failed: {exc}[/]")

    # --- PNG diagram (requires optional deps: grandalf, etc.) ---
    try:
        png_bytes = graph.draw_mermaid_png()
        png_path = DOC_DIR / "agent_graph.png"
        png_path.write_bytes(png_bytes)
        console.print(f"[dim]PNG saved to {png_path.relative_to(DOC_DIR.parent)}[/]")
    except Exception:
        # Silently skip PNG if the rendering deps aren't installed.
        pass

    # --- ASCII fallback ---
    try:
        ascii_art = graph.draw_ascii()
        if ascii_art:
            console.print()
            console.print(Panel(ascii_art, title="Agent Graph (ASCII)", border_style="dim"))
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Agent factory
# ---------------------------------------------------------------------------

def create_documentation_agent(model_id: str | None = None) -> Any:
    """Create and return the documentation deep agent.

    The agent is configured with:
    - memory:  AGENTS.md — identity, output format, search strategy
    - skills:  skills/   — progressively loaded workflow guides
    - tools:   grep, outline, section-reader, keyword-finder, navigation-finder
    - middleware: ModelRetryMiddleware + ToolRetryMiddleware for resilience
    - backend: FilesystemBackend rooted at documentation/
    """
    from langchain_openrouter import ChatOpenRouter

    _model_id = model_id or os.environ.get(
        "DOC_AGENT_MODEL", "arcee-ai/trinity-large-preview:free"
    )
    model = ChatOpenRouter(model=_model_id, temperature=0, max_tokens=8192)

    # Retry middleware — catches transient API failures and malformed responses
    model_retry = ModelRetryMiddleware(
        max_retries=3,
        backoff_factor=2.0,
        initial_delay=1.0,
    )

    # Tool retry middleware — feeds tool execution errors back to the LLM
    # so it can self-correct (e.g. missing/wrong arguments)
    tool_retry = ToolRetryMiddleware(
        max_retries=3,
        backoff_factor=2.0,
        initial_delay=1.0,
    )

    return create_deep_agent(
        model=model,
        name="documentation-agent",
        memory=["./AGENTS.md"],
        skills=["./skills/"],
        tools=ALL_TOOLS,
        middleware=[model_retry, tool_retry],
        backend=FilesystemBackend(root_dir=str(DOC_DIR), virtual_mode=True),
    )


# ---------------------------------------------------------------------------
# Rich display helper
# ---------------------------------------------------------------------------

class AgentDisplay:
    """Formats agent messages for terminal output."""

    TOOL_LABELS = {
        "grep_docs":             ("[bold cyan]grep[/]",         lambda a: f"'{a.get('pattern','')[:45]}' in {a.get('doc_path','all docs') or 'all docs'}"),
        "find_keyword":          ("[bold yellow]keyword[/]",    lambda a: a.get("term", "")[:50]),
        "find_navigation_steps": ("[bold magenta]navigation[/]",lambda a: a.get("action", "")[:50]),
        "get_doc_outline":       ("[bold blue]outline[/]",      lambda a: a.get("doc_path", "")[:50]),
        "read_doc_section":      ("[bold blue]section[/]",      lambda a: f"{a.get('doc_path','')} L{a.get('start_line','?')}-{a.get('end_line','?')}"),
        "list_docs":             ("[bold blue]list docs[/]",    lambda _: ""),
    }

    def __init__(self):
        self.printed_count = 0
        self.spinner = Spinner("dots", text="Searching documentation…")

    def _update_spinner(self, text: str):
        self.spinner = Spinner("dots", text=text[:60])

    def print_message(self, msg: Any) -> None:
        if isinstance(msg, HumanMessage):
            console.print(Panel(str(msg.content), title="Test Case", border_style="blue"))

        elif isinstance(msg, AIMessage):
            # Print text content
            content = msg.content
            if isinstance(content, list):
                content = "\n".join(
                    p.get("text", "") for p in content
                    if isinstance(p, dict) and p.get("type") == "text"
                )
            if content and content.strip():
                console.print(
                    Panel(Markdown(str(content)), title="Documentation Agent", border_style="green")
                )

            # Print tool call summaries
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    name = tc.get("name", "")
                    args = tc.get("args", {})
                    if name in self.TOOL_LABELS:
                        label, detail_fn = self.TOOL_LABELS[name]
                        detail = detail_fn(args)
                        suffix = f": {detail}" if detail else ""
                        console.print(f"  >> {label}{suffix}")
                        self._update_spinner(f"{name}{suffix}")
                    else:
                        console.print(f"  >> [dim]{name}[/]")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Documentation Agent — Playwright Test Case Expander",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run python documentation/documentation.py "Submit the form and verify success message"
  uv run python documentation/documentation.py "Lock the record after approval"
  uv run python documentation/documentation.py --list-docs
    uv run python documentation/documentation.py --model "arcee-ai/trinity-large-preview:free" "Login with wrong password"
        """,
    )
    parser.add_argument("testcase", nargs="?", help="Natural language test case to expand")
    parser.add_argument("--model", default=None, metavar="MODEL_ID",
                        help="OpenRouter model ID (default: arcee-ai/trinity-large-preview:free)")
    parser.add_argument("--list-docs", action="store_true",
                        help="List available documentation files and exit")
    parser.add_argument("--graph", action="store_true",
                        help="Print the agent's Mermaid diagram and exit")
    parser.add_argument("--output", "-o", default=None, metavar="FILE",
                        help="Save the full message log to FILE (default: documentation/runs/<timestamp>.txt)")
    parser.add_argument("--no-save", action="store_true",
                        help="Do not save messages to a file after the run")
    args = parser.parse_args()

    # Change working directory to documentation/ so relative paths in create_deep_agent work
    os.chdir(DOC_DIR)

    if args.graph:
        agent = create_documentation_agent(model_id=args.model)
        print_mermaid_diagram(agent)
        return

    if args.list_docs:
        console.print(_list_docs_impl())
        return

    if not args.testcase:
        parser.print_help()
        return

    console.print()
    console.print("[bold blue]Documentation Agent — Playwright Test Case Expander[/]")
    console.print(f"[dim]Input:[/] {args.testcase}")
    console.print()

    agent = create_documentation_agent(model_id=args.model)
    display = AgentDisplay()

    # Prompt engineering: instruct the agent to follow the testcase-expander skill
    prompt = (
        "Expand the following natural-language test case into a fully specified "
        "Playwright test plan.\n\n"
        f"**Test Case**: {args.testcase}\n\n"
        "Follow the `testcase-expander` skill:\n"
        "0. **Plan first** — call `write_todos()` to break this test case into lookup tasks before doing anything else.\n"
        "1. Call `list_docs()` to confirm available documentation.\n"
        "2. Extract every action keyword and UI element from the test case.\n"
        "3. Use `find_keyword()` and `find_navigation_steps()` for each item. Mark todos as you go.\n"
        "4. Fill any gaps with targeted `grep_docs()` calls.\n"
        "5. **Verify** every selector and URL against actual tool results — flag anything not found as a documentation gap.\n"
        "6. Produce the expanded test plan in the structured table format defined in AGENTS.md, "
        "including the Documentation Gaps section."
    )

    # Unique thread ID per test case for reproducible sessions
    thread_hash = hashlib.md5(args.testcase.encode()).hexdigest()[:8]
    config = {"configurable": {"thread_id": f"doc-{thread_hash}"}}

    all_messages: list = []  # collect every message for saving

    try:
        with Live(display.spinner, console=console, refresh_per_second=10, transient=True) as live:
            async for chunk in agent.astream(
                {"messages": [("user", prompt)]},
                config=config,
                stream_mode="values",
            ):
                if "messages" in chunk:
                    messages = chunk["messages"]
                    all_messages = messages  # keep latest full list
                    new_msgs = messages[display.printed_count:]
                    if new_msgs:
                        live.stop()
                        for msg in new_msgs:
                            display.print_message(msg)
                        display.printed_count = len(messages)
                        live.start()
                        live.update(display.spinner)

        console.print()
        console.print("[bold green]✓ Test case expansion complete.[/]")

        # --- Save messages to file ---
        if not args.no_save and all_messages:
            saved_path = save_chat_history(
                all_messages, args.testcase, output_path=args.output
            )
            console.print(
                f"[dim]Messages saved to: {saved_path.relative_to(DOC_DIR.parent)}[/]"
            )

    except Exception as exc:
        console.print()
        console.print(f"[bold red]Error during agent execution:[/] {exc}")
        console.print("[yellow]The model may have returned a malformed response. "
                      "Try again or use a different model with --model.[/]")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted.[/]")
        sys.exit(0)
