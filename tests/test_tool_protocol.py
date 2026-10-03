import sys
import threading
import time

import agent
from gembot_core.process_runner import cancel_active_process, run_process


def test_raw_json_call_uses_ollama_wire_format():
    calls = agent._parse_raw_tool_calls(
        '{"name":"clone_repo","arguments":{"repository":"https://github.com/example/repo.git","path":"repo"}}'
    )
    assert calls == [{"function": {"name": "clone_repo", "arguments": {"repository": "https://github.com/example/repo.git", "path": "repo"}}}]
    assert agent._tool_call_parts(calls[0])[0] == "clone_repo"


def test_invalid_raw_calls_are_rejected():
    assert agent._parse_raw_tool_calls('{"name":"copy_file","arguments":"bad"}') == []
    assert agent._parse_raw_tool_calls('{"name":"not_a_tool","arguments":{}}') == []


def test_active_command_can_be_cancelled():
    timer = threading.Timer(0.2, cancel_active_process)
    started = time.monotonic()
    timer.start()
    try:
        result = run_process([sys.executable, "-c", "import time; time.sleep(10)"], timeout=15)
    finally:
        timer.cancel()
    assert result.returncode != 0
    assert time.monotonic() - started < 5
