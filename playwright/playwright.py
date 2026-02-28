#!/usr/bin/env python3
"""
Playwright IFT Agent — Live Test Executor

A deep agent that executes test cases on live websites using Playwright MCP
browser tools.  It receives outputs from the Documentation Agent and Employee
Agent, opens a real browser, performs the test, and reports PASS/FAIL.

Input:  3 messages (provided interactively or via CLI flags):
  1. Test case + target URL
  2. Documentation Agent's expanded test plan
  3. Employee Agent's suggested Playwright flow

Architecture:
    - Playwright MCP tools loaded via MultiServerMCPClient (stdio transport)
    - Custom Postman/SOAP tools from tools.py (read-only)
    - Human-in-the-loop: mutation tools require human approval
    - FilesystemBackend rooted at playwright/
    - AGENTS.md  → loaded as agent memory
    - skills/    → test-executor, browser-tools, api-requests, folder-structure

Usage:
    # Interactive mode (prompts for each input):
    uv run python playwright/playwright.py --url "http://localhost:8080"

    # CLI mode (pipe or paste inputs):
    uv run python playwright/playwright.py --url "http://localhost:8080" \\
        --testcase "Login with valid credentials" \\
        --doc-output "## Test Case: Login..." \\
        --emp-output "## Suggested Playwright Flow..."

    # List available MCP tools:
    uv run python playwright/playwright.py --list-tools

    # Headed mode (default) vs headless:
    uv run python playwright/playwright.py --headless --url "http://localhost:8080"
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
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend

# Custom Postman/SOAP tools (read-only)
from tools import ALL_TOOLS as CUSTOM_TOOLS

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PLAYWRIGHT_DIR = Path(__file__).parent           # playwright/
RUNS_DIR = PLAYWRIGHT_DIR / "runs"               # playwright/runs/

console = Console()

# ---------------------------------------------------------------------------
# MCP tool categories for HITL
# ---------------------------------------------------------------------------

# Tools that are safe (read-only) — no human approval needed
SAFE_TOOLS = frozenset({
    "browser_navigate",
    "browser_snapshot",
    "browser_take_screenshot",
    "browser_console_messages",
    "browser_navigate_back",
    "browser_navigate_forward",
    "browser_tab_list",
    "browser_tab_new",
    "browser_tab_select",
    "browser_tab_close",
    "browser_pdf_save",
    "browser_wait_for",
    "browser_close",
    # Custom Postman tools (read-only)
    "list_postman_collections",
    "read_postman_collection",
    "get_postman_request",
    "build_curl_command",
})

# Tools that mutate page state — require human approval
MUTATION_TOOLS = frozenset({
    "browser_click",
    "browser_type",
    "browser_fill_form",
    "browser_select_option",
    "browser_hover",
    "browser_drag",
    "browser_file_upload",
    "browser_press_key",
    "browser_run_code",
    "browser_evaluate",
})


# ---------------------------------------------------------------------------
# Chat history saver (same pattern as other agents)
# ---------------------------------------------------------------------------

def save_chat_history(messages: list, testcase: str, output_path: str | None = None) -> Path:
    """Save all agent messages to a formatted txt file."""
    if output_path:
        filepath = Path(output_path)
        filepath.parent.mkdir(parents=True, exist_ok=True)
    else:
        RUNS_DIR.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
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
# HITL display & prompt
# ---------------------------------------------------------------------------

def display_interrupt_and_get_decisions(interrupt_data) -> list[dict]:
    """Show pending tool calls to the human and collect approve/reject/edit decisions."""
    interrupts = interrupt_data[0].value
    action_requests = interrupts["action_requests"]
    review_configs = interrupts["review_configs"]
    config_map = {cfg["action_name"]: cfg for cfg in review_configs}

    decisions = []

    for i, action in enumerate(action_requests):
        name = action["name"]
        args = action["args"]
        review_config = config_map.get(name, {"allowed_decisions": ["approve", "reject"]})
        allowed = review_config["allowed_decisions"]

        # Display the proposed action
        console.print()
        console.print(Panel.fit(
            f"[bold]{name}[/bold]\n" + "\n".join(f"  {k}: {v}" for k, v in args.items()),
            title=f"[yellow]⚠ Action {i+1}/{len(action_requests)} Needs Approval[/]",
            border_style="yellow",
        ))

        allowed_str = " / ".join(f"[bold]{d}[/]" for d in allowed)
        console.print(f"  Allowed: {allowed_str}")

        # Get decision
        while True:
            choice = Prompt.ask(
                "  Decision",
                choices=allowed,
                default="approve" if "approve" in allowed else allowed[0],
            )
            if choice == "edit" and "edit" in allowed:
                console.print("  [dim]Edit the arguments (JSON-like, one per line).[/]")
                console.print(f"  [dim]Current: {args}[/]")
                edited_args = {}
                for key, val in args.items():
                    new_val = Prompt.ask(f"    {key}", default=str(val))
                    # Try to preserve types
                    if isinstance(val, bool):
                        edited_args[key] = new_val.lower() in ("true", "1", "yes")
                    elif isinstance(val, int):
                        try:
                            edited_args[key] = int(new_val)
                        except ValueError:
                            edited_args[key] = new_val
                    else:
                        edited_args[key] = new_val
                decisions.append({
                    "type": "edit",
                    "edited_action": {"name": name, "args": edited_args},
                })
                break
            elif choice == "approve":
                decisions.append({"type": "approve"})
                break
            elif choice == "reject":
                decisions.append({"type": "reject"})
                break

    return decisions


# ---------------------------------------------------------------------------
# Rich display helper
# ---------------------------------------------------------------------------

class AgentDisplay:
    """Formats agent messages for terminal output."""

    def __init__(self):
        self.printed_count = 0
        self.spinner = Spinner("dots", text="Executing test…")

    def _update_spinner(self, text: str):
        self.spinner = Spinner("dots", text=text[:60])

    def print_message(self, msg: Any) -> None:
        if isinstance(msg, HumanMessage):
            content = str(msg.content)
            if len(content) > 200:
                content = content[:200] + "…"
            console.print(Panel(content, title="Input", border_style="blue"))

        elif isinstance(msg, AIMessage):
            content = msg.content
            if isinstance(content, list):
                content = "\n".join(
                    p.get("text", "") for p in content
                    if isinstance(p, dict) and p.get("type") == "text"
                )
            if content and content.strip():
                console.print(
                    Panel(Markdown(str(content)), title="Playwright Agent", border_style="magenta")
                )
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    name = tc.get("name", "")
                    args = tc.get("args", {})
                    # Color-code by safety
                    if name in MUTATION_TOOLS:
                        label = f"[bold yellow]⚠ {name}[/]"
                    else:
                        label = f"[bold cyan]{name}[/]"
                    args_short = str(args)
                    if len(args_short) > 80:
                        args_short = args_short[:80] + "…"
                    console.print(f"  >> {label}: {args_short}")
                    self._update_spinner(f"{name}")


# ---------------------------------------------------------------------------
# Input collection
# ---------------------------------------------------------------------------

def collect_multiline_input(prompt_text: str) -> str:
    """Collect multi-line input from the user. Empty line to finish."""
    console.print(f"\n[bold]{prompt_text}[/]")
    console.print("[dim](Paste content, then press Enter on an empty line to finish)[/]")
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line == "" and lines:
            break
        lines.append(line)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Agent factory
# ---------------------------------------------------------------------------

async def create_playwright_agent(
    headless: bool = True,
    model_id: str | None = None,
):
    """Create the Playwright IFT agent with MCP tools and HITL.

    Returns (agent, mcp_client, session) — caller must manage the session lifetime.
    """
    from langchain_mcp_adapters.tools import load_mcp_tools
    from langchain_mcp_adapters.client import MultiServerMCPClient
    from langchain_openrouter import ChatOpenRouter

    _model_id = model_id or os.environ.get(
        "PLAYWRIGHT_AGENT_MODEL", "arcee-ai/trinity-large-preview:free"
    )
    model = ChatOpenRouter(
        model=_model_id, temperature=0.5, max_tokens=8192, presence_penalty=0.3
    )

    # --- MCP client ---
    mcp_args = ["@playwright/mcp@latest"]
    if headless:
        mcp_args.append("--headless")

    mcp_client = MultiServerMCPClient({
        "playwright": {
            "command": "npx",
            "args": mcp_args,
            "transport": "stdio",
        }
    })

    # Start the MCP session (persistent — browser stays alive)
    session = mcp_client.session("playwright")
    session_ctx = await session.__aenter__()
    playwright_tools = await load_mcp_tools(session_ctx)

    # Combine MCP tools with custom Postman tools
    all_tools = playwright_tools + CUSTOM_TOOLS
    console.print(f"[dim]Loaded {len(playwright_tools)} MCP tools + {len(CUSTOM_TOOLS)} custom tools[/]")

    # --- Build interrupt_on map from discovered tools ---
    interrupt_on = {}
    for t in all_tools:
        name = t.name
        if name in MUTATION_TOOLS:
            interrupt_on[name] = {"allowed_decisions": ["approve", "edit", "reject"]}
        else:
            interrupt_on[name] = False

    # --- Checkpointer (required for HITL) ---
    checkpointer = MemorySaver()

    # --- Middleware ---
    model_retry = ModelRetryMiddleware(
        max_retries=3, backoff_factor=2.0, initial_delay=1.0,
    )
    tool_retry = ToolRetryMiddleware(
        max_retries=3, backoff_factor=2.0, initial_delay=1.0,
    )

    # --- Create the deep agent ---
    agent = create_deep_agent(
        model=model,
        name="playwright-agent",
        memory=["./AGENTS.md"],
        skills=["./skills/"],
        tools=all_tools,
        interrupt_on=interrupt_on,
        checkpointer=checkpointer,
        middleware=[model_retry, tool_retry],
        backend=FilesystemBackend(root_dir=str(PLAYWRIGHT_DIR), virtual_mode=True),
    )

    return agent, mcp_client, session, session_ctx


# ---------------------------------------------------------------------------
# Main execution loop with HITL
# ---------------------------------------------------------------------------

async def run_test_with_hitl(
    agent,
    messages: list[tuple[str, str]],
    config: dict,
    display: AgentDisplay,
    no_save: bool = False,
    output_path: str | None = None,
    testcase_title: str = "test",
) -> dict:
    """Run the agent in a loop, handling HITL interrupts."""

    all_messages: list = []
    input_payload = {"messages": messages}
    is_resume = False

    try:
        while True:
            if is_resume:
                # We're resuming after an interrupt — decisions already set
                pass
            else:
                # Normal invocation or first call
                with Live(display.spinner, console=console, refresh_per_second=10, transient=True) as live:
                    async for chunk in agent.astream(
                        input_payload,
                        config=config,
                        stream_mode="values",
                    ):
                        if "messages" in chunk:
                            msgs = chunk["messages"]
                            all_messages = msgs
                            new_msgs = msgs[display.printed_count:]
                            if new_msgs:
                                live.stop()
                                for msg in new_msgs:
                                    display.print_message(msg)
                                display.printed_count = len(msgs)
                                live.start()
                                live.update(display.spinner)

            # After streaming, check the final state for interrupts
            state = await agent.aget_state(config)

            if not state.tasks:
                # No pending tasks = agent finished
                break

            # Check for interrupts in pending tasks
            has_interrupt = False
            for task in state.tasks:
                if hasattr(task, 'interrupts') and task.interrupts:
                    has_interrupt = True
                    console.print()
                    console.print("[bold yellow]═══ Human-in-the-Loop ═══[/]")
                    decisions = display_interrupt_and_get_decisions(task.interrupts)
                    console.print("[bold green]Resuming...[/]")

                    # Resume with decisions
                    input_payload = Command(resume={"decisions": decisions})
                    is_resume = True

                    # Stream the resumed execution
                    with Live(display.spinner, console=console, refresh_per_second=10, transient=True) as live:
                        async for chunk in agent.astream(
                            input_payload,
                            config=config,
                            stream_mode="values",
                        ):
                            if "messages" in chunk:
                                msgs = chunk["messages"]
                                all_messages = msgs
                                new_msgs = msgs[display.printed_count:]
                                if new_msgs:
                                    live.stop()
                                    for msg in new_msgs:
                                        display.print_message(msg)
                                    display.printed_count = len(msgs)
                                    live.start()
                                    live.update(display.spinner)
                    break  # Will loop back to check state again

            if not has_interrupt:
                break

        console.print()
        console.print("[bold green]✓ Test execution complete.[/]")

        # Save messages
        if not no_save and all_messages:
            saved_path = save_chat_history(
                all_messages, testcase_title, output_path=output_path
            )
            console.print(f"[dim]Messages saved to: {saved_path}[/]")

        return {"messages": all_messages}

    except Exception as exc:
        console.print()
        console.print(f"[bold red]Error during agent execution:[/] {exc}")
        console.print("[yellow]The model may have returned a malformed response. "
                      "Try again or use a different model with --model.[/]")
        # Still try to save what we have
        if not no_save and all_messages:
            saved_path = save_chat_history(
                all_messages, testcase_title, output_path=output_path
            )
            console.print(f"[dim]Partial messages saved to: {saved_path}[/]")
        raise


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Playwright IFT Agent — Live Test Executor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  # Interactive mode:
  uv run python playwright/playwright.py --url "http://localhost:8080"

  # With pre-supplied inputs:
  uv run python playwright/playwright.py --url "http://localhost:8080" \\
      --testcase "Login with valid credentials" \\
      --doc-output "## Test Case: Login..." \\
      --emp-output "## Suggested Playwright Flow..."

  # List MCP tools:
  uv run python playwright/playwright.py --list-tools

  # Headless mode:
  uv run python playwright/playwright.py --headless --url "http://localhost:8080"
        """,
    )
    parser.add_argument("--url", required=False, metavar="URL",
                        help="Target URL to test against")
    parser.add_argument("--testcase", default=None,
                        help="Test case description (or interactive if omitted)")
    parser.add_argument("--doc-output", default=None, metavar="TEXT",
                        help="Documentation Agent output (or interactive if omitted)")
    parser.add_argument("--emp-output", default=None, metavar="TEXT",
                        help="Employee Agent output (or interactive if omitted)")
    parser.add_argument("--model", default=None, metavar="MODEL_ID",
                        help="OpenRouter model ID (default: arcee-ai/trinity-large-preview:free)")
    parser.add_argument("--headless", action="store_true",
                        help="Run browser in headless mode (default: headed)")
    parser.add_argument("--list-tools", action="store_true",
                        help="List available Playwright MCP tools and exit")
    parser.add_argument("--graph", action="store_true",
                        help="Print the agent's Mermaid diagram and exit")
    parser.add_argument("--output", "-o", default=None, metavar="FILE",
                        help="Save the full message log to FILE")
    parser.add_argument("--no-save", action="store_true",
                        help="Do not save messages to a file after the run")
    args = parser.parse_args()

    # Change working directory so relative paths in create_deep_agent work
    os.chdir(PLAYWRIGHT_DIR)

    # --- List tools mode ---
    if args.list_tools:
        console.print("[bold blue]Loading Playwright MCP tools...[/]")
        agent, mcp_client, session, session_ctx = await create_playwright_agent(
            headless=True, model_id=args.model,
        )
        tools = agent.get_graph().nodes  # Just list what we loaded
        console.print()

        table = Table(title="Playwright MCP Tools")
        table.add_column("Tool", style="bold")
        table.add_column("Category", style="dim")

        for t in agent.tools if hasattr(agent, 'tools') else []:
            name = t.name if hasattr(t, 'name') else str(t)
            is_custom = name in {t.name for t in CUSTOM_TOOLS}
            if name in MUTATION_TOOLS:
                cat = "[yellow]⚠ MUTATION[/]"
            elif is_custom:
                cat = "[blue]CUSTOM[/]"
            else:
                cat = "[green]SAFE[/]"
            table.add_row(name, cat)

        console.print(table)
        await session.__aexit__(None, None, None)
        return

    # --- Require URL for test execution ---
    if not args.url and not args.graph:
        parser.print_help()
        return

    # --- Graph mode ---
    if args.graph:
        agent, mcp_client, session, session_ctx = await create_playwright_agent(
            headless=True, model_id=args.model,
        )
        try:
            graph = agent.get_graph(xray=True)
            mermaid_text = graph.draw_mermaid()
            console.print(Panel(mermaid_text, title="Agent Graph", border_style="cyan"))
        except Exception as exc:
            console.print(f"[yellow]Could not draw graph: {exc}[/]")
        await session.__aexit__(None, None, None)
        return

    # --- Collect inputs ---
    testcase = args.testcase
    doc_output = args.doc_output
    emp_output = args.emp_output

    if not testcase:
        testcase = collect_multiline_input(
            "📋 Message 1 — Test Case Description:"
        )
    if not doc_output:
        doc_output = collect_multiline_input(
            "📄 Message 2 — Documentation Agent Output (paste the expanded test plan):"
        )
    if not emp_output:
        emp_output = collect_multiline_input(
            "🔧 Message 3 — Employee Agent Output (paste the suggested Playwright flow):"
        )

    if not testcase.strip():
        console.print("[red]No test case provided. Exiting.[/]")
        return

    # --- Print summary ---
    console.print()
    console.print("[bold magenta]Playwright IFT Agent — Live Test Executor[/]")
    console.print(f"[dim]URL:[/]       {args.url}")
    console.print(f"[dim]Test:[/]      {testcase.strip().split(chr(10))[0][:80]}")
    console.print(f"[dim]Doc input:[/] {len(doc_output)} chars")
    console.print(f"[dim]Emp input:[/] {len(emp_output)} chars")
    console.print(f"[dim]Headless:[/]  {args.headless}")
    console.print()

    # --- Create agent ---
    console.print("[dim]Starting Playwright MCP server...[/]")
    agent, mcp_client, session, session_ctx = await create_playwright_agent(
        headless=args.headless, model_id=args.model,
    )

    try:
        display = AgentDisplay()

        # --- Build the 3-message input ---
        # Each message is clearly labeled so the agent knows what it's reading.
        # See AGENTS.md "Input Format" for the contract.
        msg1 = (
            f"## TASK\n"
            f"Test Case: {testcase}\n"
            f"Target URL: {args.url}\n\n"
            f"## INSTRUCTIONS\n"
            f"Follow the test-executor skill to execute this test. "
            f"Use the browser-tools skill for MCP tool reference. "
            f"Produce a structured PASS/FAIL report."
        )
        msg2 = (
            f"## DOCUMENTATION AGENT OUTPUT\n\n"
            f"This is the expanded test plan from the Documentation Agent. "
            f"Use this as your PRIMARY test plan — it has the authoritative "
            f"steps, selectors, and expected results.\n\n"
            f"{doc_output}"
        )
        msg3 = (
            f"## EMPLOYEE AGENT OUTPUT\n\n"
            f"This is the suggested Playwright flow from the Employee Agent, "
            f"based on old Selenium scripts. Use this as SECONDARY reference — "
            f"fallback selectors, test data values, and JS code fallbacks. "
            f"Do NOT trust blindly; verify on the real page.\n\n"
            f"{emp_output}"
        )

        messages = [
            ("user", msg1),
            ("user", msg2),
            ("user", msg3),
        ]

        # Unique thread ID per test case
        thread_hash = hashlib.md5(testcase.encode()).hexdigest()[:8]
        config = {"configurable": {"thread_id": f"pw-{thread_hash}"}}

        # --- Run ---
        await run_test_with_hitl(
            agent=agent,
            messages=messages,
            config=config,
            display=display,
            no_save=args.no_save,
            output_path=args.output,
            testcase_title=testcase.strip().split("\n")[0],
        )

    finally:
        # Clean up MCP session
        try:
            await session.__aexit__(None, None, None)
        except Exception:
            pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted.[/]")
        sys.exit(0)
