import os
import uuid
import json
import subprocess
from typing import Any, Dict

# Deep agents + langgraph stores (based on docs)
from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend, FilesystemBackend
from langgraph.store.memory import InMemoryStore
from langgraph.checkpoint.memory import MemorySaver

# Chat model
from langchain_openrouter import ChatOpenRouter
from langchain.messages import SystemMessage, HumanMessage

# Tool
from langchain.tools import tool, ToolRuntime


# Base root for all agent-specific filesystem roots
ROOT = os.path.abspath(os.path.join(os.getcwd(), "memories"))

DEFAULT_MODEL = "arcee-ai/trinity-large-preview:free"

def ensure_dirs(path: str):
    os.makedirs(path, exist_ok=True)

def write_json(path: str, data: Any):
    ensure_dirs(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ---------------------------------------------------------------------------
# LLM Factory
# ---------------------------------------------------------------------------
def create_model(model_id: str | None = None, **kwargs: Any):
    """LLM Factory — create a chat model via OpenRouter.

    Uses ChatOpenRouter which routes to 300+ models via a single API:
        - "meta-llama/llama-3.3-70b-instruct:free"  (default: free, 128K ctx, reliable tool calling)
        - "arcee-ai/trinity-large-preview:free"
        - "stepfun/step-3.5-flash:free"
        - "google/gemini-2.5-flash"  (paid, reliable)
        - "anthropic/claude-sonnet-4.5"  (paid)

    NOTE: Avoid "google/gemma-3-27b-it:free" and similar small models — they do not
    support tool calling and will echo the tool schema as raw text instead of invoking tools.
        ... and many more at https://openrouter.ai/models

    Falls back to DEFAULT_MODEL if none specified.
    """
    model_id = model_id or DEFAULT_MODEL
    return ChatOpenRouter(
        model=model_id,
        temperature=0,
        max_tokens=8192,
        **kwargs
    )



# ---------- Backend factory for a given agent (filesystem rooted per-agent) ----------
def filesystem_backend_for(agent_name: str):
    root_dir = os.path.join(ROOT, agent_name)
    ensure_dirs(root_dir)
    # virtual_mode=True prevents traversal outside root_dir via agent tools
    return FilesystemBackend(root_dir=root_dir, virtual_mode=True)

# ---------- Checkpointer (useful for human-in-the-loop) ----------
checkpointer = MemorySaver()









def main():
    print("Hello from qa!")


if __name__ == "__main__":
    main()
