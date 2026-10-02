"""gembot_core.memory - Long-term facts, persistent chat sessions, context summarization, and planning."""
import datetime
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

MEMORY_FILE = Path(".gembot/memory.json")
SESSIONS_DIR = Path(".gembot/sessions")


def ensure_memory_dir() -> None:
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


def remember_fact(key: str, value: str) -> str:
    """Save a user preference, project detail, or permanent note to .gembot/memory.json."""
    try:
        ensure_memory_dir()
        mem: Dict[str, Any] = {}
        if MEMORY_FILE.is_file():
            try:
                mem = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
            except Exception:
                mem = {}
        mem[key] = {
            "value": value,
            "updated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        MEMORY_FILE.write_text(json.dumps(mem, indent=2), encoding="utf-8")
        return f"Remembered '{key}': {value}"
    except Exception as e:
        return f"Error remembering fact: {e}"


def recall_fact(key: str = "") -> str:
    """Recall saved facts or all preferences from .gembot/memory.json."""
    if not MEMORY_FILE.is_file():
        return "No remembered facts found."
    try:
        mem = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
        if not mem:
            return "Memory is currently empty."
        if key:
            if key in mem:
                val = mem[key]["value"]
                return f"Fact for '{key}': {val}"
            # Fuzzy match
            matches = {k: v["value"] for k, v in mem.items() if key.lower() in k.lower()}
            if matches:
                return "Matching facts:\n" + "\n".join(f"- {k}: {v}" for k, v in matches.items())
            return f"No fact found matching '{key}'."
        return "All remembered facts:\n" + "\n".join(f"- {k}: {v['value']}" for k, v in mem.items())
    except Exception as e:
        return f"Error recalling facts: {e}"


def save_session(name: str, history: List[Dict[str, Any]]) -> Tuple[bool, str]:
    """Save current chat history to .gembot/sessions/<name>.json."""
    try:
        ensure_memory_dir()
        safe_name = "".join(c for c in name if c.isalnum() or c in ("-", "_")).strip() or "session"
        fpath = SESSIONS_DIR / f"{safe_name}.json"
        fpath.write_text(json.dumps(history, indent=2), encoding="utf-8")
        return True, f"Session saved to {fpath.name}."
    except Exception as e:
        return False, f"Failed to save session: {e}"


def load_session(name: str) -> Tuple[Optional[List[Dict[str, Any]]], str]:
    """Load a chat session from .gembot/sessions/<name>.json."""
    try:
        ensure_memory_dir()
        safe_name = "".join(c for c in name if c.isalnum() or c in ("-", "_")).strip()
        fpath = SESSIONS_DIR / f"{safe_name}.json"
        if not fpath.is_file():
            # Try finding any matching session
            candidates = list(SESSIONS_DIR.glob(f"*{safe_name}*.json"))
            if candidates:
                fpath = candidates[0]
            else:
                return None, f"Session '{name}' not found."

        data = json.loads(fpath.read_text(encoding="utf-8"))
        return data, f"Loaded session {fpath.stem} ({len(data)} messages)."
    except Exception as e:
        return None, f"Error loading session: {e}"


def list_sessions() -> List[str]:
    """List available saved sessions."""
    ensure_memory_dir()
    return [p.stem for p in SESSIONS_DIR.glob("*.json")]


def auto_summarize_history(history: List[Dict[str, Any]], max_messages: int = 24) -> List[Dict[str, Any]]:
    """When history grows too long, condense middle turns into a summary instead of dropping them."""
    if len(history) <= max_messages + 1:
        return history

    system = history[0] if history[0].get("role") == "system" else None
    msgs = history[1:] if system else history

    if len(msgs) <= max_messages:
        return history

    # Take oldest messages to compress
    cutoff = len(msgs) - max_messages
    old_slice = msgs[:cutoff]
    recent_slice = msgs[cutoff:]

    # Build concise summary of old messages
    summary_lines = []
    for m in old_slice:
        role = m.get("role", "unknown")
        content = m.get("content", "") or ""
        tool_name = m.get("tool_name", "")
        if tool_name:
            summary_lines.append(f"- Tool executed ({tool_name}): {content[:100]}")
        elif role == "user":
            summary_lines.append(f"- User: {content[:120]}")
        elif role == "assistant":
            summary_lines.append(f"- Assistant: {content[:100]}")

    summary_content = (
        "[Previous Conversation Summary to conserve context memory]:\n" +
        "\n".join(summary_lines[-10:])
    )
    summary_msg = {"role": "system", "content": summary_content}

    result = [system] if system else []
    result.append(summary_msg)
    result.extend(recent_slice)
    return result
