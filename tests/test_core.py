"""Test suite for gembot upgrades: safety, precision editing, undo, path inference, and raw JSON fallback."""
import json
import os
import shutil
from pathlib import Path
import pytest

from gembot_core.safety import backup_file, undo_last_change, is_dangerous_command
from gembot_core.coding_tools import edit_file, search_files, make_dir, copy_file
from gembot_core.config import DEFAULT_CONFIG
from gembot_core.memory import remember_fact, recall_fact, auto_summarize_history


def test_dangerous_command_blocklist():
    blocked = DEFAULT_CONFIG["blocked_commands"]
    is_d, desc = is_dangerous_command("format c: /fs:ntfs", blocked)
    assert is_d is True
    assert "blocked" in desc.lower() or "format" in desc.lower()

    is_d, _ = is_dangerous_command("git push origin main --force", blocked)
    assert is_d is True

    is_d, _ = is_dangerous_command("git status", blocked)
    assert is_d is False


def test_edit_file(tmp_path):
    f = tmp_path / "hello.py"
    f.write_text("def hello():\n    return 'old'\n", encoding="utf-8")
    
    res = edit_file(str(f), "return 'old'", "return 'new'")
    assert "Successfully" in res
    assert "return 'new'" in f.read_text(encoding="utf-8")

    # Negative test
    err = edit_file(str(f), "nonexistent_code", "replacement")
    assert "Error" in err


def test_backup_and_undo(tmp_path):
    target = tmp_path / "target.txt"
    target.write_text("Version 1", encoding="utf-8")

    # Take backup
    b = backup_file(str(target))
    assert b is not None
    assert os.path.exists(b)

    # Overwrite
    target.write_text("Version 2 - Corrupted", encoding="utf-8")
    assert target.read_text() == "Version 2 - Corrupted"

    # Undo
    success, msg = undo_last_change()
    assert success is True
    assert target.read_text() == "Version 1"


def test_search_files(tmp_path):
    src = tmp_path / "script.py"
    src.write_text("def calculate_total():\n    return 42\n", encoding="utf-8")

    res = search_files("calculate_total", path=str(tmp_path), glob="*.py")
    assert "calculate_total" in res
    assert "Found 1 matches" in res


def test_memory_remember_and_recall(tmp_path, monkeypatch):
    import gembot_core.memory as mem_mod
    test_mem = tmp_path / "memory.json"
    monkeypatch.setattr(mem_mod, "MEMORY_FILE", test_mem)

    remember_fact("favorite_color", "magenta")
    res = recall_fact("favorite_color")
    assert "magenta" in res


def test_auto_summarize_history():
    hist = [{"role": "system", "content": "system prompt"}]
    for i in range(30):
        hist.append({"role": "user", "content": f"User question {i}"})
        hist.append({"role": "assistant", "content": f"Assistant response {i}"})

    summarized = auto_summarize_history(hist, max_messages=10)
    assert len(summarized) <= 12
    assert "Previous Conversation Summary" in summarized[1]["content"]


def test_infer_filename_react_tsx():
    from agent import _infer_filename_from_content
    react_code = (
        "import React, { useState } from 'react';\n\n"
        "interface Message {\n"
        "  sender: 'user' | 'ai';\n"
        "  text: string;\n"
        "}\n\n"
        "export default function HomePage() {\n"
        "  const [input, setInput] = useState<string>('');\n"
        "  return <div>{input}</div>;\n"
        "}\n"
    )
    inferred = _infer_filename_from_content(react_code, [])
    assert inferred == "page.tsx"


def test_infer_filename_package_json():
    from agent import _infer_filename_from_content
    pkg_code = '{\n  "name": "chatbox-x",\n  "version": "0.1.0",\n  "dependencies": {\n    "next": "14.2.0"\n  }\n}'
    inferred = _infer_filename_from_content(pkg_code, [])
    assert inferred == "package.json"


def test_infer_filename_python():
    from agent import _infer_filename_from_content
    py_code = "import os\nimport sys\n\ndef main():\n    print('Hello World')\n\nif __name__ == '__main__':\n    main()\n"
    inferred = _infer_filename_from_content(py_code, [])
    assert inferred == "main.py"


def test_infer_filename_from_history():
    from agent import _infer_filename_from_content
    history = [{"role": "user", "content": "Please write the code for Chatbox-X/app/page.tsx now."}]
    code = "import React from 'react'; export default function Page() { return <h1>Chat</h1>; }"
    inferred = _infer_filename_from_content(code, history)
    assert inferred == "Chatbox-X/app/page.tsx"


def test_config_num_predict_and_ctx():
    from gembot_core.config import DEFAULT_CONFIG, load_config
    assert "num_predict" in DEFAULT_CONFIG
    assert "num_ctx" in DEFAULT_CONFIG
    assert DEFAULT_CONFIG["num_predict"] >= 4096
    assert DEFAULT_CONFIG["num_ctx"] >= 8192
    cfg = load_config()
    assert cfg["num_predict"] >= 4096
    assert cfg["num_ctx"] >= 8192
