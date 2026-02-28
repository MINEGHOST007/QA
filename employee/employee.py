#!/usr/bin/env python3
"""
Employee Agent — Retired Selenium Script Finder

A deep agent that searches through a library of ~400 old Selenium regression test
scripts to find the 2 most similar scripts for a given natural-language test case.

Input:  A single string containing BOTH:
  1. The user's test case  (e.g. "Submit the form and verify success message")
  2. The expanded test plan from the Documentation Agent (copy-pasted — contains
     selectors, URLs, steps, pre/post-conditions)

The expanded test plan provides concrete selectors and URLs that the agent greps
for inside old Selenium scripts, yielding much higher-signal matches than
keyword search alone.

Architecture:
    - FilesystemBackend rooted at employee/
    - AGENTS.md  →  loaded as agent memory (identity + output format)
    - skills/    →  progressively loaded skills (script-finder, index-lookup, etc.)
    - Tools      →  tools.py  — grep, index search, TF-IDF similarity, script reader

Workflow (two separate manual steps):
    # Step 1 — Run the Documentation Agent, copy its final output
    uv run python documentation/documentation.py "Submit the form and verify success message"

    # Step 2 — Paste test case + expanded plan into the Employee Agent
    uv run python employee/employee.py "<test case> + <pasted expanded plan>"

Usage:
    uv run python employee/employee.py "Submit the form and verify success message
    ## Test Case: Submit the form and verify success message
    ### Steps
    | # | Action | Locator / Selector | Expected Result |
    | 1 | Click submit | [data-testid=btn-submit-record] | Form submits |
    | 2 | Verify toast | [data-testid=toast-success] | Success message |
    "

    uv run python employee/employee.py --list-scripts
    uv run python employee/employee.py --rebuild-index
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

# Tools live in employee/tools.py
from tools import (  # noqa: E402
    ALL_TOOLS
)

# ---------------------------------------------------------------------------
# Paths — everything is relative to this file's directory (employee/)
# ---------------------------------------------------------------------------
EMPLOYEE_DIR = Path(__file__).parent          # employee/
SCRIPTS_DIR = EMPLOYEE_DIR / "scripts"        # employee/scripts/
RUNS_DIR = EMPLOYEE_DIR / "runs"              # employee/runs/  — saved outputs

console = Console()


# ---------------------------------------------------------------------------
# Chat history saver
# ---------------------------------------------------------------------------

def save_chat_history(messages: list, testcase: str, output_path: str | None = None) -> Path:
    """Save all agent messages to a formatted txt file.

    Writes to ``employee/runs/<datetime>.txt`` by default, or to
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
            if len(content) > 2000:
                content = content[:2000] + "\n... (truncated)"
            lines.append(content)
            lines.append("")

    filepath.write_text("\n".join(lines), encoding="utf-8")
    return filepath


# ---------------------------------------------------------------------------
# Mermaid diagram helper
# ---------------------------------------------------------------------------

def print_mermaid_diagram(agent: Any) -> None:
    """Print the agent's Mermaid graph to the terminal."""
    try:
        graph = agent.get_graph(xray=True)
    except Exception as exc:
        console.print(f"[yellow]Could not retrieve agent graph: {exc}[/]")
        return

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

    try:
        png_bytes = graph.draw_mermaid_png()
        png_path = EMPLOYEE_DIR / "agent_graph.png"
        png_path.write_bytes(png_bytes)
        console.print(f"[dim]PNG saved to {png_path.relative_to(EMPLOYEE_DIR.parent)}[/]")
    except Exception:
        pass

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

def create_employee_agent(model_id: str | None = None) -> Any:
    """Create and return the employee deep agent.

    The agent is configured with:
    - memory:  AGENTS.md — identity, output format, search strategy
    - skills:  skills/   — progressively loaded workflow guides
    - tools:   index search, grep, TF-IDF similarity, script reader
    - middleware: ModelRetryMiddleware + ToolRetryMiddleware for resilience
    - backend: FilesystemBackend rooted at employee/
    """
    from langchain_openrouter import ChatOpenRouter

    _model_id = model_id or os.environ.get(
        "EMPLOYEE_AGENT_MODEL", "arcee-ai/trinity-large-preview:free"
    )
    model = ChatOpenRouter(model=_model_id, temperature=0, max_tokens=8192, presence_penalty=0.3)

    # Retry middleware — catches transient API failures and malformed responses
    model_retry = ModelRetryMiddleware(
        max_retries=3,
        backoff_factor=2.0,
        initial_delay=1.0,
    )

    # Tool retry middleware — feeds tool execution errors back to the LLM
    tool_retry = ToolRetryMiddleware(
        max_retries=3,
        backoff_factor=2.0,
        initial_delay=1.0,
    )

    return create_deep_agent(
        model=model,
        name="employee-agent",
        memory=["./AGENTS.md"],
        skills=["./skills/"],
        tools=ALL_TOOLS,
        middleware=[model_retry, tool_retry],
        backend=FilesystemBackend(root_dir=str(EMPLOYEE_DIR), virtual_mode=True),
    )


# ---------------------------------------------------------------------------
# Rich display helper
# ---------------------------------------------------------------------------

class AgentDisplay:
    """Formats agent messages for terminal output."""

    TOOL_LABELS = {
        "grep_scripts":          ("[bold cyan]grep[/]",          lambda a: f"'{a.get('pattern','')[:45]}' in {a.get('script_path','all scripts') or 'all scripts'}"),
        "search_index":          ("[bold yellow]index[/]",       lambda a: a.get("query", "")[:50]),
        "find_similar_scripts":  ("[bold magenta]similarity[/]", lambda a: a.get("query", "")[:50]),
        "get_script_outline":    ("[bold blue]outline[/]",       lambda a: a.get("script_path", "")[:50]),
        "read_script":           ("[bold blue]read[/]",          lambda a: f"{a.get('script_path','')} L{a.get('start_line','1')}-{a.get('end_line','end')}"),
        "list_scripts":          ("[bold blue]list scripts[/]",  lambda _: ""),
    }

    def __init__(self):
        self.printed_count = 0
        self.spinner = Spinner("dots", text="Searching scripts…")

    def _update_spinner(self, text: str):
        self.spinner = Spinner("dots", text=text[:60])

    def print_message(self, msg: Any) -> None:
        if isinstance(msg, HumanMessage):
            console.print(Panel(str(msg.content), title="Test Case", border_style="blue"))

        elif isinstance(msg, AIMessage):
            content = msg.content
            if isinstance(content, list):
                content = "\n".join(
                    p.get("text", "") for p in content
                    if isinstance(p, dict) and p.get("type") == "text"
                )
            if content and content.strip():
                console.print(
                    Panel(Markdown(str(content)), title="Employee Agent", border_style="yellow")
                )

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
        description="Employee Agent — Retired Selenium Script Finder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Workflow (two separate manual steps):
  1. Run the Documentation Agent and copy its final output:
     uv run python documentation/documentation.py "Submit the form and verify success message"

  2. Paste test case + expanded plan into the Employee Agent:
     uv run python employee/employee.py "<test case>  <pasted expanded plan>"

Examples:
  uv run python employee/employee.py "Submit the form and verify success message"
  uv run python employee/employee.py --list-scripts
  uv run python employee/employee.py --rebuild-index
  uv run python employee/employee.py --model "arcee-ai/trinity-large-preview:free" "Login test"
        """,
    )
    parser.add_argument("testcase", nargs="?",
                        help="Test case + expanded plan from Documentation Agent (one string)")
    parser.add_argument("--model", default=None, metavar="MODEL_ID",
                        help="OpenRouter model ID (default: arcee-ai/trinity-large-preview:free)")
    parser.add_argument("--list-scripts", action="store_true",
                        help="List all indexed scripts and exit")
    parser.add_argument("--rebuild-index", action="store_true",
                        help="Rebuild the script index and exit")
    parser.add_argument("--graph", action="store_true",
                        help="Print the agent's Mermaid diagram and exit")
    parser.add_argument("--output", "-o", default=None, metavar="FILE",
                        help="Save the full message log to FILE (default: employee/runs/<timestamp>.txt)")
    parser.add_argument("--no-save", action="store_true",
                        help="Do not save messages to a file after the run")
    args = parser.parse_args()

    # Change working directory to employee/ so relative paths in create_deep_agent work
    os.chdir(EMPLOYEE_DIR)

    if args.rebuild_index:
        console.print("[bold blue]Rebuilding script index...[/]")
        from build_index import build_and_save_index
        count = build_and_save_index()
        console.print(f"[bold green]✓ Index rebuilt: {count} scripts indexed.[/]")
        return

    if args.graph:
        agent = create_employee_agent(model_id=args.model)
        print_mermaid_diagram(agent)
        return

    if args.list_scripts:
        # Call the tool implementation directly
        from tools import list_scripts as _ls_tool
        result = _ls_tool.invoke({})
        console.print(result)
        return

    if not args.testcase:
        parser.print_help()
        return

    # -----------------------------------------------------------------------
    # Detect whether the input contains an expanded test plan
    # (the user pastes both the test case and the Documentation Agent output
    #  as a single string)
    # -----------------------------------------------------------------------
    raw_input = args.testcase
    has_expanded = any(marker in raw_input for marker in [
        "### Steps", "### Pre-conditions", "Locator / Selector",
        "data-testid", "### Key References",
    ])

    console.print()
    console.print("[bold yellow]Employee Agent — Retired Selenium Script Finder[/]")
    if has_expanded:
        # Show just the first line as the test case title
        title_line = raw_input.strip().split("\n")[0].strip()
        console.print(f"[dim]Test case:[/]  {title_line}")
        console.print(f"[dim]Expanded:[/]   included (detected selectors/steps in input)")
    else:
        console.print(f"[dim]Test case:[/]  {raw_input}")
        console.print("[dim]Expanded:[/]   not detected (tip: paste Documentation Agent output for better results)")
    console.print()

    agent = create_employee_agent(model_id=args.model)
    display = AgentDisplay()

    # -----------------------------------------------------------------------
    # Prompt construction
    #
    # The user's input is passed directly.  When it contains an expanded plan
    # (selectors, URLs, steps) the agent is told to mine those for grep
    # targets.  Otherwise it falls back to keyword + TF-IDF search.
    # -----------------------------------------------------------------------
    if has_expanded:
        prompt = (
            "Find the 2 most similar old Selenium regression scripts for the following "
            "input. The input contains BOTH a test case description AND an expanded test "
            "plan with selectors, URLs, and steps from the Documentation Agent.\n\n"
            f"{raw_input}\n\n"
            "Follow the `script-finder` skill:\n"
            "0. **Plan first** — call `write_todos()` to break this into search tasks before doing anything else.\n"
            "1. **Extract selectors and URLs** from the expanded test plan above — these are your highest-signal search terms.\n"
            "2. Call `search_index()` with feature names from the test case (e.g. 'form submission', 'success message').\n"
            "3. Call `grep_scripts()` for EACH concrete selector from the expanded plan (e.g. 'submit.*btn', 'success.*message', 'toast').\n"
            "4. Call `grep_scripts()` for action patterns found in the steps (e.g. 'click.*submit', 'find_element.*form').\n"
            "5. Call `find_similar_scripts()` with the full test case + key selectors for TF-IDF matching.\n"
            "6. Read the top candidates with `get_script_outline()` and `read_script()`. "
            "Extract test data values from helper methods (e.g. default params in `_fill_form()`).\n"
            "7. **Select the 2 best matches** and produce the 'Suggested Playwright Flow' output from AGENTS.md:\n"
            "   - Suggested Steps table using Playwright MCP tool names (browser_navigate, browser_snapshot, browser_type, browser_click, etc.)\n"
            "   - 'How to Find Elements' section with data-testid hints, label fallbacks, and role fallbacks\n"
            "   - 'Fallback: browser_run_code' block with a ready-to-use Playwright JS function\n"
            "   - Source scripts with similarity scores and caveats\n"
            "   - 'Known Gaps' with specific things to verify on the real page\n"
            "   IMPORTANT: Frame everything as a SUGGESTION. Include warnings that selectors are estimated. "
            "Do NOT repeat any section. Each heading must appear exactly once."
        )
    else:
        prompt = (
            "Find the 2 most similar old Selenium regression scripts for the following "
            "test case.\n\n"
            f"**Test Case**: {raw_input}\n\n"
            "Follow the `script-finder` skill:\n"
            "0. **Plan first** — call `write_todos()` to break this into search tasks before doing anything else.\n"
            "1. Call `list_scripts()` to see what's available.\n"
            "2. Use `search_index()` with key feature names and action verbs from the test case.\n"
            "3. Use `grep_scripts()` to find specific XPaths, selectors, or code patterns.\n"
            "4. Use `find_similar_scripts()` with the full test case description for semantic matching.\n"
            "5. Read the top candidates with `get_script_outline()` and `read_script()`.\n"
            "6. **Select the 2 best matches** and produce the full output format from AGENTS.md:\n"
            "   - All XPaths and selectors used in each script\n"
            "   - Step-by-step test process with code snippets\n"
            "   - Search strategy summary\n"
            "   - Gaps and notes"
        )

    # Unique thread ID per test case for reproducible sessions
    thread_hash = hashlib.md5(raw_input.encode()).hexdigest()[:8]
    config = {"configurable": {"thread_id": f"emp-{thread_hash}"}}

    all_messages: list = []

    try:
        with Live(display.spinner, console=console, refresh_per_second=10, transient=True) as live:
            async for chunk in agent.astream(
                {"messages": [("user", prompt)]},
                config=config,
                stream_mode="values",
            ):
                if "messages" in chunk:
                    messages = chunk["messages"]
                    all_messages = messages
                    new_msgs = messages[display.printed_count:]
                    if new_msgs:
                        live.stop()
                        for msg in new_msgs:
                            display.print_message(msg)
                        display.printed_count = len(messages)
                        live.start()
                        live.update(display.spinner)

        console.print()
        console.print("[bold green]✓ Script search complete.[/]")

        # --- Save messages to file ---
        if not args.no_save and all_messages:
            # Use the first line of input as the title for the saved file
            save_title = raw_input.strip().split("\n")[0].strip()
            saved_path = save_chat_history(
                all_messages, save_title, output_path=args.output
            )
            console.print(
                f"[dim]Messages saved to: {saved_path.relative_to(EMPLOYEE_DIR.parent)}[/]"
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
