"""Cancellable subprocess support shared by GEMBOT tools."""
from __future__ import annotations
import os
import subprocess
import time
from dataclasses import dataclass
from typing import Sequence

_active_process: subprocess.Popen | None = None

@dataclass
class ProcessResult:
    returncode: int
    stdout: str
    stderr: str

def cancel_active_process() -> None:
    global _active_process
    process = _active_process
    if process is None or process.poll() is not None:
        return
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True, timeout=5)
        else:
            process.terminate()
    except Exception:
        try:
            process.kill()
        except Exception:
            pass

def run_process(command: str | Sequence[str], *, cwd: str | None = None, shell: bool = False, timeout: int = 60) -> ProcessResult:
    global _active_process
    flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) if os.name == "nt" else 0
    process = subprocess.Popen(command, cwd=cwd, shell=shell, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=flags)
    _active_process = process
    started = time.monotonic()
    try:
        while True:
            try:
                stdout, stderr = process.communicate(timeout=0.1)
                return ProcessResult(process.returncode, stdout or "", stderr or "")
            except subprocess.TimeoutExpired:
                if time.monotonic() - started >= timeout:
                    cancel_active_process()
                    stdout, stderr = process.communicate()
                    raise subprocess.TimeoutExpired(command, timeout, output=stdout, stderr=stderr)
    except KeyboardInterrupt:
        cancel_active_process()
        process.communicate()
        raise
    finally:
        if _active_process is process:
            _active_process = None
