"""gembot - Autonomous Windows Desktop, Browser, and Coding AI Agent with Rich Jules-style CLI.
Powered by Ollama + qwen2.5-coder / gemma4:e2b with autonomous tool calling, web browsing, 
multimodal file attachments (images, PDFs, documents), self-coding, and Git/GitHub automation.
"""
import base64
import ctypes
import gc
import io
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

# Ensure UTF-8 output encoding for Windows command line compatibility
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure gembot directory is on sys.path so gembot_core can be imported anywhere
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

try:
    from dotenv import load_dotenv
    load_dotenv()
    load_dotenv(os.path.expandvars(r"%USERPROFILE%\agent\.env"))
except ImportError:
    pass

import ollama
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.markdown import Markdown
from rich.status import Status

from prompt_toolkit import prompt
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style

# Import Modular Core
from gembot_core.config import load_config, save_config, get_active_model, set_active_model, GLOBAL_ENV
from gembot_core.safety import backup_file, undo_last_change, is_dangerous_command, log_session_activity
from gembot_core.coding_tools import edit_file, search_files, delete_file, copy_file, make_dir, file_info, run_tests
from gembot_core.memory import remember_fact, recall_fact, save_session, load_session, list_sessions, auto_summarize_history
from gembot_core.system_tools import take_screenshot, clipboard_read, clipboard_write, system_info, list_processes, kill_process, download_file, http_request
from gembot_core.doc_tools import create_docx, read_docx, create_excel, read_excel
from gembot_core.plugins import load_plugins
from gembot_core.process_runner import cancel_active_process, run_process

from rich.spinner import SPINNERS

console = Console()

# Custom compact bouncing-bar thinking spinner for terminal interface
SPINNERS["thinking_bar"] = {
    "interval": 80,
    "frames": [
        "[██░░░░░░░░]",
        "[░██░░░░░░░]",
        "[░░██░░░░░░]",
        "[░░░██░░░░░]",
        "[░░░░██░░░░]",
        "[░░░░░██░░░]",
        "[░░░░░░██░░]",
        "[░░░░░░░██░]",
        "[░░░░░░░░██]",
        "[░░░░░░░██░]",
        "[░░░░░░██░░]",
        "[░░░░░██░░░]",
        "[░░░░██░░░░]",
        "[░░░██░░░░░]",
        "[░░██░░░░░░]",
        "[░██░░░░░░░]",
    ]
}

# Load runtime config
CONFIG = load_config()
MODEL = CONFIG.get("model", "qwen2.5-coder:7b")
MAX_STEPS = int(CONFIG.get("max_steps", 50))
MAX_OUTPUT = int(CONFIG.get("max_output", 25000))
MAX_HISTORY = int(CONFIG.get("max_history", 24))
COMMAND_TIMEOUT = int(CONFIG.get("command_timeout", 60))
AUTO_CONFIRM = bool(CONFIG.get("auto_confirm", False))

STOP_REQUESTED = False
_STOP_LOCK = threading.Lock()
_STOP_EVENT = threading.Event()  # Event for faster cross-thread signalling
_LAST_SIGINT_TIME = 0.0  # Track double Ctrl+C for force-exit

def _set_stop_requested():
    """Thread-safe setter for STOP_REQUESTED."""
    global STOP_REQUESTED
    with _STOP_LOCK:
        STOP_REQUESTED = True
    _STOP_EVENT.set()

def _clear_stop_requested():
    """Thread-safe reset for STOP_REQUESTED."""
    global STOP_REQUESTED
    with _STOP_LOCK:
        STOP_REQUESTED = False
    _STOP_EVENT.clear()

def sigint_handler(sig, frame):
    """Handle Ctrl+C cleanly across Windows cmd/powershell.
    
    First Ctrl+C sets the stop flag so polling loops can detect it.
    Second Ctrl+C within 2 seconds force-exits the process immediately.
    """
    global _LAST_SIGINT_TIME
    now = time.time()
    if now - _LAST_SIGINT_TIME < 2.0:
        # Double Ctrl+C — force exit immediately
        try:
            sys.stderr.write("\n🛑 [gembot]: Force quit (double Ctrl+C).\n")
            sys.stderr.flush()
        except Exception:
            pass
        os._exit(1)
    _LAST_SIGINT_TIME = now
    _set_stop_requested()
    cancel_active_process()
    # Use sys.stderr.write instead of console.print to avoid Rich re-entrancy issues
    try:
        sys.stderr.write("\n🛑 [gembot]: Ctrl+C received — aborting action... (press again to force quit)\n")
        sys.stderr.flush()
    except Exception:
        pass

try:
    signal.signal(signal.SIGINT, sigint_handler)
except Exception:
    pass

# Windows-specific: register a native console control handler for reliable Ctrl+C
# Python's signal.SIGINT can't interrupt blocking C-level I/O on Windows,
# so this ensures the STOP_REQUESTED flag always gets set.
if sys.platform == "win32":
    try:
        _CTRL_C_EVENT = 0
        @ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_uint)
        def _win_ctrl_handler(ctrl_type):
            if ctrl_type == _CTRL_C_EVENT:
                now = time.time()
                global _LAST_SIGINT_TIME
                if now - _LAST_SIGINT_TIME < 2.0:
                    os._exit(1)
                _LAST_SIGINT_TIME = now
                _set_stop_requested()
                return 1  # Handled — don't kill the process
            return 0
        ctypes.windll.kernel32.SetConsoleCtrlHandler(_win_ctrl_handler, True)
    except Exception:
        pass


def load_gembot_project_context() -> str:
    """Load project conventions or rules from GEMBOT.md in the current working directory."""
    gembot_md = Path("GEMBOT.md")
    if gembot_md.is_file():
        try:
            content = gembot_md.read_text(encoding="utf-8", errors="replace").strip()
            if content:
                console.print(f"[dim green]  📋 Loaded project context from GEMBOT.md[/dim green]")
                return f"\n\n[Project Rules & Context from GEMBOT.md]:\n{content}\n"
        except Exception:
            pass
    return ""


def build_system_prompt() -> str:
    base = (
        "You are 'GEMBOT', an elite autonomous Windows AI coding and automation assistant. "
        "Use the supplied tool schema to complete execution tasks.\n\n"
        "CRITICAL RULES:\n"
        "- For work that changes files, runs commands, or researches, call one available tool immediately.\n"
        "- Only use tool names and argument shapes present in the supplied schema. Never invent a tool.\n"
        "- Make one next action at a time. If native tool calling is unavailable, output one JSON tool-call object only; do not embed several calls inside a plan.\n"
        "- A plain-text answer is allowed after the work is complete or when you need the user to decide something.\n"
        "- Use run_command for terminal work and git_publish after checking or testing the completed project.\n"
        "- Complete tasks fully — write ALL required files with complete code (never truncate, abbreviate, or use placeholders), run commands, and test thoroughly.\n"
        "- ALWAYS provide the full explicit 'path' argument when calling write_file or edit_file (e.g., 'Chatbox-X/package.json', 'src/app/page.tsx').\n"
        "- When asked to scaffold or build an application (e.g. Next.js, React, Node.js, Python), create every necessary file completely: package.json, configuration files, backend APIs, frontend UI components, styles, and documentation.\n"
        "- Use edit_file for updating parts of existing files instead of rewriting them completely.\n"
        "- After completing all task steps, give a brief clear summary."
    )
    ctx = load_gembot_project_context()
    return base + ctx


def _p(path: str) -> str:
    return os.path.abspath(os.path.expanduser(os.path.expandvars(path)))


def _cut(text: str) -> str:
    return text if len(text) <= MAX_OUTPUT else text[:MAX_OUTPUT] + "\n...[truncated]"


def ask_user_confirmation(action_desc: str) -> bool:
    """Prompt user for confirmation before performing destructive actions."""
    if AUTO_CONFIRM:
        return True
    try:
        console.print(f"\n[bold yellow]⚠ SAFETY GATE:[/bold yellow] [bold white]{action_desc}[/bold white]")
        ans = input("  Proceed? (y/n, default n): ").strip().lower()
        return ans in ("y", "yes")
    except Exception:
        return False


# ==================== FILESYSTEM & OS TOOLS ====================

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}
DOC_EXTENSIONS = {".pdf", ".txt", ".md", ".py", ".js", ".html", ".css", ".json", ".csv"}


def get_clipboard_image() -> dict:
    """Check system clipboard for copied images and return base64 data."""
    try:
        from PIL import ImageGrab
        im = ImageGrab.grabclipboard()
        if isinstance(im, list):
            for file_path in im:
                res = extract_content_from_path(str(file_path))
                if res:
                    return res
            return {}

        if im is not None and hasattr(im, "save"):
            buffered = io.BytesIO()
            im.save(buffered, format="PNG")
            b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
            return {"type": "image", "data": b64, "path": "clipboard_image.png"}
    except Exception:
        pass
    return {}


def extract_content_from_path(raw_path: str) -> dict:
    """Extract text or image base64 if user dragged/pasted a file path."""
    clean_path = raw_path.strip().strip("'").strip('"').strip('& ')
    if not clean_path:
        return {}
    p = Path(clean_path).expanduser()
    if not p.is_file():
        return {}

    ext = p.suffix.lower()

    if ext in IMAGE_EXTENSIONS:
        try:
            with open(p, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
                return {"type": "image", "data": b64, "path": str(p)}
        except Exception:
            return {}

    if ext == ".pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(p))
            extracted_text = []
            for page_idx, page in enumerate(reader.pages[:20]):
                txt = page.extract_text()
                if txt:
                    extracted_text.append(f"--- Page {page_idx+1} ---\n{txt}")
            combined = "\n".join(extracted_text)
            return {"type": "text", "content": combined, "path": str(p)}
        except Exception as e:
            return {"type": "error", "content": f"Could not read PDF: {e}"}

    if ext in DOC_EXTENSIONS or ext in {".log", ".env", ".toml", ".yaml", ".sh", ".bat", ".cmd"} or ext == "":
        try:
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                return {"type": "text", "content": f.read(), "path": str(p)}
        except Exception:
            return {}

    return {}


def list_files(path: str = ".") -> str:
    """List files and folders in a directory with file types.

    Args:
        path: Directory path, e.g. C:\\Users\\Subhash\\Desktop or .
    """
    try:
        target = _p(path)
        if not os.path.exists(target):
            return f"Error: Directory '{target}' does not exist."
        items = sorted(os.listdir(target))
        if not items:
            return f"Directory '{target}' is empty."
        formatted = []
        for item in items:
            full = os.path.join(target, item)
            is_dir = os.path.isdir(full)
            tag = "[DIR] " if is_dir else "      "
            formatted.append(f"{tag} {item}")
        return _cut("\n".join(formatted))
    except Exception as e:
        return f"Error: {e}"


def move_file(source: str, destination: str) -> str:
    """Move or rename a file or folder. Creates destination folder if needed."""
    try:
        dest = _p(destination)
        src = _p(source)
        if not os.path.exists(src):
            return f"Error: Source '{src}' not found."
        if os.path.exists(dest) and os.path.isfile(dest):
            if not ask_user_confirmation(f"Overwrite existing destination file '{dest}'?"):
                return f"Action cancelled by user (move_file aborted)."
            backup_file(dest)

        if not os.path.splitext(dest)[1] and not os.path.exists(dest):
            os.makedirs(dest, exist_ok=True)
        else:
            os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
        shutil.move(src, dest)
        return f"Moved to {dest}"
    except Exception as e:
        return f"Error: {e}"


def read_file(path: str) -> str:
    """Read a text or code file."""
    try:
        full = _p(path)
        if not os.path.exists(full):
            return f"Error: File '{full}' does not exist."
        with open(full, "r", encoding="utf-8", errors="replace") as f:
            return _cut(f.read())
    except Exception as e:
        return f"Error: {e}"


def _sanitize_json(content: str) -> str:
    """Strip JS-style comments and trailing commas from JSON content."""
    lines = content.splitlines()
    cleaned = []
    in_block = False
    for line in lines:
        if in_block:
            end_idx = line.find("*/")
            if end_idx != -1:
                line = line[end_idx + 2:]
                in_block = False
            else:
                continue
        while "/*" in line:
            start = line.index("/*")
            end = line.find("*/", start + 2)
            if end != -1:
                line = line[:start] + line[end + 2:]
            else:
                line = line[:start]
                in_block = True
                break
        stripped = line.lstrip()
        if stripped.startswith("//"):
            continue
        in_string = False
        escape = False
        cut_at = -1
        for i, ch in enumerate(line):
            if escape:
                escape = False
                continue
            if ch == '\\':
                escape = True
                continue
            if ch == '"':
                in_string = not in_string
            if not in_string and i + 1 < len(line) and line[i:i+2] == '//':
                cut_at = i
                break
        if cut_at != -1:
            line = line[:cut_at].rstrip()
        if line.strip() or not cleaned or cleaned[-1].strip():
            cleaned.append(line)

    result = "\n".join(cleaned)
    result = re.sub(r',\s*([}\]])', r'\1', result)
    return result


def write_file(path: str, content: str) -> str:
    """Write or overwrite text or code to a file. Automatically creates backup if overwriting."""
    try:
        if isinstance(content, dict):
            if content.get("type") == "string" and "content" in content:
                content = str(content["content"])
            elif "content" in content:
                content = str(content["content"])
            elif "value" in content:
                content = str(content["value"])
            elif "text" in content:
                content = str(content["text"])
            elif "code" in content:
                content = str(content["code"])
            else:
                content = json.dumps(content, indent=2)
        elif not isinstance(content, str):
            content = str(content or "")

        full = _p(path)
        os.makedirs(os.path.dirname(full) or ".", exist_ok=True)

        if os.path.exists(full):
            backup_file(full)

        corrections = []
        if full.lower().endswith(".json"):
            try:
                json.loads(content)
            except json.JSONDecodeError:
                sanitized = _sanitize_json(content)
                try:
                    json.loads(sanitized)
                    content = sanitized
                    corrections.append("auto-stripped comments and/or trailing commas from JSON")
                except json.JSONDecodeError as je:
                    corrections.append(f"WARNING: JSON is still invalid after cleanup: {je}")

        with open(full, "w", encoding="utf-8") as f:
            f.write(content)

        msg = f"Successfully saved {len(content)} characters to {full}"
        if corrections:
            msg += " | Corrections applied: " + "; ".join(corrections)
        return msg
    except Exception as e:
        return f"Error: {e}"


def run_command(command: str, cwd: str = ".", timeout: int = 0) -> str:
    """Run a terminal command in a chosen working directory.

    Args:
        command: Command to run in the Windows terminal.
        cwd: Working directory. Defaults to GEMBOT's current directory.
        timeout: Maximum seconds to wait. Use 0 for the configured default.
    """
    blocked = CONFIG.get("blocked_commands", [])
    is_d, desc = is_dangerous_command(command, blocked)
    if is_d:
        if not ask_user_confirmation(f"Command flagged as dangerous ({desc}): '{command}'"):
            return f"Action cancelled by safety gate: {desc}"

    cmd_lower = command.strip().lower()
    actual_command = command
    if cmd_lower.startswith("npx ") and " -y " not in cmd_lower and " --yes " not in cmd_lower and not cmd_lower.startswith("npx -y") and not cmd_lower.startswith("npx --yes"):
        actual_command = "npx -y " + command[4:]
        console.print(f"  [dim cyan]↳ Auto-added -y flag for non-interactive execution[/dim cyan]")

    if "create-next-app" in cmd_lower and "--use-npm" not in cmd_lower:
        actual_command += " --use-npm"

    _LONG_RUNNING_PATTERNS = ["npm ", "npx ", "pip ", "pip3 ", "yarn ", "pnpm ", "cargo ", "dotnet ", "composer ",
                               "maven ", "mvn ", "gradle ", "go build", "go install", "docker ", "choco "]
    is_long_running = any(cmd_lower.startswith(p) or f" {p}" in cmd_lower for p in _LONG_RUNNING_PATTERNS)
    try:
        effective_timeout = max(1, min(int(timeout), 3600)) if timeout else (COMMAND_TIMEOUT * 5 if is_long_running else COMMAND_TIMEOUT)
    except (TypeError, ValueError):
        return "Error: timeout must be a whole number of seconds."
    workdir = _p(cwd)
    if not os.path.isdir(workdir):
        return f"Error: working directory '{workdir}' does not exist."

    console.print(f"  [bright_black]⚡ [gembot cmd]:[/bright_black] [bold yellow]{actual_command}[/bold yellow]")
    if is_long_running:
        console.print(f"  [dim]↳ Extended timeout: {effective_timeout}s (install/build detected)[/dim]")

    try:
        result = run_process(actual_command, cwd=workdir, shell=True, timeout=effective_timeout)
        out = (result.stdout + result.stderr).strip()
        return _cut(out or f"Executed successfully (exit code {result.returncode})")
    except subprocess.TimeoutExpired:
        return f"Error: command timed out after {effective_timeout} seconds and was stopped."
    except Exception as e:
        return f"Error: {e}"


def open_app(name_or_path: str) -> str:
    """Open an application, file, directory, or website in Windows."""
    try:
        target = name_or_path.strip()
        if os.path.exists(_p(target)):
            os.startfile(_p(target))
        else:
            subprocess.Popen(f'start "" "{target}"', shell=True)
        return f"Opened {target}"
    except Exception as e:
        return f"Error: {e}"


def web_search(query: str, max_results: int = 5) -> str:
    """Search the web using DuckDuckGo to find information, research topics, or find assignment solutions."""
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        if not results:
            return "No web results found."
        formatted = []
        for i, r in enumerate(results, 1):
            title = r.get("title", "")
            href = r.get("href", "")
            body = r.get("body", "")
            formatted.append(f"{i}. {title}\n   URL: {href}\n   Snippet: {body}\n")
        return _cut("\n".join(formatted))
    except Exception as e:
        return f"Search error: {e}"


def browse_webpage(url: str) -> str:
    """Browse a web page using headless browser or fast HTTP, extracting clean text."""
    try:
        import requests
        from bs4 import BeautifulSoup

        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        resp = requests.get(url, headers=headers, timeout=12)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
                tag.decompose()
            text = re.sub(r"\s+", " ", soup.get_text()).strip()
            if len(text) > 100:
                return _cut(f"Page Title: {soup.title.string if soup.title else 'No Title'}\n\nContent:\n{text}")

        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=20000)
            title = page.title()
            text = page.inner_text("body")
            browser.close()
            return _cut(f"Page Title: {title}\n\nContent:\n{text}")
    except Exception as e:
        return f"Error browsing webpage '{url}': {e}"


def git_commit_and_push(repo_path: str, commit_message: str, branch: str = "main", remote_url: str = "") -> str:
    """Stage all changes, commit them with a message, and push to GitHub repository."""
    try:
        path = _p(repo_path)
        if not os.path.exists(path):
            return f"Error: Repository path '{path}' does not exist."

        if not os.path.exists(os.path.join(path, ".git")):
            r = subprocess.run("git init", cwd=path, shell=True, capture_output=True, text=True)
            if r.returncode != 0:
                return f"Git init failed: {r.stderr}"

        if remote_url:
            subprocess.run(f"git remote remove origin", cwd=path, shell=True, capture_output=True)
            subprocess.run(f"git remote add origin {remote_url}", cwd=path, shell=True, capture_output=True)

        subprocess.run("git add -A", cwd=path, shell=True, check=True)
        c = subprocess.run(f'git commit -m "{commit_message}"', cwd=path, shell=True, capture_output=True, text=True)
        subprocess.run(f"git branch -M {branch}", cwd=path, shell=True, capture_output=True)
        p = subprocess.run(f"git push -u origin {branch}", cwd=path, shell=True, capture_output=True, text=True)
        if p.returncode == 0:
            return f"Successfully committed and pushed to GitHub branch '{branch}':\n{c.stdout}\n{p.stdout}"
        else:
            return f"Committed locally: {c.stdout.strip()}\nPush output: {p.stderr.strip() or p.stdout.strip()}"
    except Exception as e:
        return f"Git error: {e}"


def clone_repo(repository: str, path: str) -> str:
    """Clone a Git repository into a new, empty directory."""
    try:
        destination = _p(path)
        if not repository.startswith(("https://", "http://", "git@")):
            return "Error: repository must be an HTTPS, HTTP, or SSH Git URL."
        if os.path.exists(destination) and os.listdir(destination):
            return f"Error: destination '{destination}' already exists and is not empty."
        os.makedirs(os.path.dirname(destination) or ".", exist_ok=True)
        result = run_process(["git", "clone", repository, destination], timeout=COMMAND_TIMEOUT)
        output = (result.stdout + result.stderr).strip()
        return _cut(output or f"Cloned '{repository}' to '{destination}'.") if result.returncode == 0 else f"Git clone failed: {output}"
    except subprocess.TimeoutExpired:
        return f"Error: git clone timed out after {COMMAND_TIMEOUT} seconds."
    except Exception as e:
        return f"Git clone error: {e}"


def git_publish(repo_path: str = ".", commit_message: str = "Update project", branch: str = "") -> str:
    """Stage, commit, and push a repository to its configured origin remote."""
    try:
        path = _p(repo_path)
        if not os.path.isdir(os.path.join(path, ".git")):
            return f"Error: '{path}' is not a Git repository. Clone or initialize it first."
        remote = run_process(["git", "remote", "get-url", "origin"], cwd=path, timeout=COMMAND_TIMEOUT)
        if remote.returncode != 0 or not remote.stdout.strip():
            return "Error: no 'origin' remote is configured for this repository."
        if not branch:
            branch = run_process(["git", "branch", "--show-current"], cwd=path, timeout=COMMAND_TIMEOUT).stdout.strip()
        if not branch:
            return "Error: no current branch is checked out. Provide a branch name."
        add = run_process(["git", "add", "-A"], cwd=path, timeout=COMMAND_TIMEOUT)
        if add.returncode != 0:
            return f"Git add failed: {add.stderr.strip() or add.stdout.strip()}"
        status = run_process(["git", "status", "--porcelain"], cwd=path, timeout=COMMAND_TIMEOUT)
        if status.returncode != 0:
            return f"Git status failed: {status.stderr.strip() or status.stdout.strip()}"
        committed = "No file changes to commit."
        if status.stdout.strip():
            commit = run_process(["git", "commit", "-m", commit_message], cwd=path, timeout=COMMAND_TIMEOUT)
            if commit.returncode != 0:
                return f"Git commit failed: {commit.stderr.strip() or commit.stdout.strip()}"
            committed = commit.stdout.strip() or "Created commit."
        pushed = run_process(["git", "push", "-u", "origin", branch], cwd=path, timeout=COMMAND_TIMEOUT)
        output = (pushed.stdout + pushed.stderr).strip()
        return f"{committed}\nPushed branch '{branch}' to origin.\n{output}" if pushed.returncode == 0 else f"{committed}\nGit push failed: {output}"
    except subprocess.TimeoutExpired:
        return f"Error: Git operation timed out after {COMMAND_TIMEOUT} seconds and was stopped."
    except Exception as e:
        return f"Git publish error: {e}"


# ==================== TOOL REGISTRY ====================

TOOLS = {
    # Core filesystem
    "write_file": write_file,
    "read_file": read_file,
    "list_files": list_files,
    "move_file": move_file,
    "copy_file": copy_file,
    "delete_file": delete_file,
    "make_dir": make_dir,
    "file_info": file_info,
    "edit_file": edit_file,
    "search_files": search_files,
    "run_tests": run_tests,
    # Execution & system
    "run_command": run_command,
    "open_app": open_app,
    "system_info": system_info,
    "list_processes": list_processes,
    "kill_process": kill_process,
    "take_screenshot": take_screenshot,
    "clipboard_read": clipboard_read,
    "clipboard_write": clipboard_write,
    "download_file": download_file,
    "http_request": http_request,
    # Research & web
    "web_search": web_search,
    "browse_webpage": browse_webpage,
    "git_commit_and_push": git_commit_and_push,
    "clone_repo": clone_repo,
    "git_publish": git_publish,
    # Documents
    "create_docx": create_docx,
    "read_docx": read_docx,
    "create_excel": create_excel,
    "read_excel": read_excel,
    # Memory
    "remember_fact": remember_fact,
    "recall_fact": recall_fact,
}

# Load any third-party plugins dynamically
try:
    plugins = load_plugins()
    TOOLS.update(plugins)
except Exception:
    pass


def ensure_ollama_running() -> bool:
    """Check if Ollama server is responding, start it if not."""
    try:
        req = urllib.request.Request("http://127.0.0.1:11434/")
        with urllib.request.urlopen(req, timeout=2) as response:
            if response.status == 200:
                return True
    except Exception:
        pass

    console.print("[dim cyan][gembot] Starting Ollama server in background...[/dim cyan]")
    ollama_path = os.path.expandvars(r"%LOCALAPPDATA%\Programs\Ollama\ollama.exe")
    if not os.path.exists(ollama_path):
        ollama_path = "ollama"
    try:
        subprocess.Popen(
            [ollama_path, "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        for _ in range(10):
            time.sleep(1)
            try:
                with urllib.request.urlopen("http://127.0.0.1:11434/", timeout=1) as resp:
                    if resp.status == 200:
                        return True
            except Exception:
                continue
    except Exception as e:
        console.print(f"[yellow]Warning: Could not auto-launch Ollama: {e}[/yellow]")
    return False


def _get_active_project_dir(history: list) -> str:
    """Find the directory created or focused on during the current session."""
    if not history:
        return ""
    for msg in reversed(history):
        content = ""
        tool_calls = []
        if isinstance(msg, dict):
            content = str(msg.get("content", ""))
            tool_calls = msg.get("tool_calls") or []
        else:
            content = str(getattr(msg, "content", ""))
            tool_calls = getattr(msg, "tool_calls", None) or []

        for tc in tool_calls:
            fn = tc.get("function", {}) if isinstance(tc, dict) else getattr(tc, "function", {})
            name = fn.get("name") if isinstance(fn, dict) else getattr(fn, "name", "")
            args = fn.get("arguments") if isinstance(fn, dict) else getattr(fn, "arguments", {})
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except Exception:
                    args = {}
            if name in ("make_dir", "create_dir", "clone_repo"):
                p = str(args.get("path") or "").strip().strip("./").replace("\\", "/")
                if p and "/" not in p:
                    return p

        m = re.search(r'(?:git\s+clone\s+[^\s]+/([a-zA-Z0-9_-]+)(?:\.git)?|cd\s+([a-zA-Z0-9_-]+))', content)
        if m:
            folder = m.group(1) or m.group(2)
            if folder:
                return folder

    try:
        subdirs = [d for d in os.listdir(".") if os.path.isdir(d) and not d.startswith(".")]
        if len(subdirs) == 1:
            return subdirs[0]
    except Exception:
        pass
    return ""


def _infer_filename_from_content(content: any, history: list) -> str | None:
    if isinstance(content, dict):
        content = str(content.get("content") or json.dumps(content, indent=2))
    elif not isinstance(content, str):
        content = str(content or "")

    if not content or not content.strip():
        return None

    prefix = _get_active_project_dir(history)
    def _with_prefix(filename: str) -> str:
        if prefix and not filename.startswith(prefix + "/") and not filename.startswith("./" + prefix + "/"):
            return f"{prefix}/{filename}"
        return filename

    first_lines = content[:2000]
    first_line = content.split("\n", 1)[0].strip()

    header_match = re.match(
        r'^(?://|#|/\*|<!--)\s*(?:file(?:name)?:\s*|path:\s*)?([a-zA-Z0-9_./\\-]+\.[a-zA-Z0-9]+)',
        first_line,
        re.IGNORECASE,
    )
    if header_match:
        return _with_prefix(header_match.group(1).replace("\\", "/"))

    if first_line.startswith("#!"):
        if "python" in first_line:
            return _with_prefix("script.py")
        if "node" in first_line:
            return _with_prefix("script.js")

    # Search history for explicitly mentioned file paths
    if history:
        for msg in reversed(history[-8:]):
            text = ""
            if isinstance(msg, dict):
                text = str(msg.get("content", ""))
            elif hasattr(msg, "content"):
                text = str(getattr(msg, "content", ""))
            matches = re.findall(r'[\s`\'"]([a-zA-Z0-9_./\\-]+\.[a-zA-Z0-9]{1,5})[\s`\'"]', text)
            for m in matches:
                m_clean = m.replace("\\", "/").strip("./")
                m_lower = m_clean.lower()
                if m_lower.endswith(".json") and ('"name"' in content or '"dependencies"' in content or '"compilerOptions"' in content):
                    return m_clean
                if (m_lower.endswith(".tsx") or m_lower.endswith(".jsx")) and ("React" in content or "export default" in content or "useState" in content or "use client" in content):
                    return m_clean
                if m_lower.endswith(".ts") and ("export " in content or "import " in content):
                    return m_clean
                is_js_or_react = bool(re.search(r'(\bconst\b|\blet\b|\bvar\b|\bfunction\b|\bfrom\s+[\'"]|import\s+React|useState|useRef|useEffect|\bexport\b|;\s*$|<[A-Z]\w*>)', content))
                if m_lower.endswith(".py") and not is_js_or_react and ("def " in content or "import os" in content or "import sys" in content or "__main__" in content):
                    return m_clean

    # JSON configurations
    stripped = content.strip()
    if stripped.startswith("{") or stripped.startswith("["):
        if '"dependencies"' in content or '"devDependencies"' in content or '"scripts"' in content:
            return _with_prefix("package.json")
        if '"compilerOptions"' in content:
            return _with_prefix("tsconfig.json")
        return _with_prefix("data.json")

    # Git & Environment
    if re.search(r'^(node_modules|\.next|\.env|\.turbo|dist|build|coverage)\b', content, re.MULTILINE):
        return _with_prefix(".gitignore")

    # Next.js / React / TypeScript / JSX
    is_ts = bool(re.search(r'(interface\s+\w+|type\s+\w+\s*=|:\s*(string|number|boolean|any|void)\b|<[A-Z]\w*>)', content))
    is_react = bool(re.search(r'(\'use client\'|"use client"|import\s+React|from\s+[\'"]react[\'"]|useState|useEffect|useRef|useMemo|useCallback|<[a-zA-Z]+[^>]*>)', content))
    has_export = bool(re.search(r'^(export\s+default|export\s+const|export\s+function|export\s+class)', content, re.MULTILINE))

    comp_match = re.search(r'export\s+default\s+(?:function|const)\s+([A-Za-z0-9_]+)', content)
    if comp_match:
        comp_name = comp_match.group(1)
        if is_react and comp_name not in ("App", "Page", "Home"):
            return _with_prefix(f"src/components/{comp_name}.tsx" if is_ts else f"src/components/{comp_name}.jsx")

    if "export async function GET" in content or "export async function POST" in content or "NextResponse" in content:
        return _with_prefix("route.ts" if is_ts else "route.js")

    if is_react:
        if "RootLayout" in content or "<html" in content or "metadata" in content:
            return _with_prefix("src/app/layout.tsx" if is_ts else "src/app/layout.jsx")
        return _with_prefix("src/app/page.tsx" if is_ts else "src/app/page.jsx")

    if is_ts and has_export:
        return _with_prefix("src/models/chatbox.ts" if ("ollama" in content.lower() or "chat" in content.lower()) else "index.ts")

    # Python
    has_python_patterns = bool(re.search(r'^(from\s+[a-zA-Z0-9_.]+\s+import\s+|import\s+[a-zA-Z0-9_, ]+$|def\s+[a-zA-Z0-9_]+\s*\(|class\s+[a-zA-Z0-9_]+\s*[:\(]|if\s+__name__\s*==\s*[\'"]__main__[\'"]:)', first_lines, re.MULTILINE))
    has_js_tokens = bool(re.search(r'(\bconst\b|\blet\b|\bvar\b|\bfunction\b|\bfrom\s+[\'"]|\bexport\b|\bconsole\.log\b|\b=>\b|;\s*$)', first_lines, re.MULTILINE))

    if has_python_patterns and not has_js_tokens:
        return _with_prefix("main.py")

    # HTML / CSS / Markdown
    if re.search(r'^<!DOCTYPE html|^<html|^<head|^<body', first_lines, re.IGNORECASE | re.MULTILINE):
        return _with_prefix("index.html")
    if re.search(r'^(@import |@charset |@tailwind |body\s*\{|html\s*\{|\.[\w-]+\s*\{)', first_lines, re.MULTILINE):
        return _with_prefix("src/app/globals.css")
    if re.search(r'^#\s+.+', first_lines, re.MULTILINE):
        return _with_prefix("README.md")

    # General JS fallback
    if has_js_tokens or has_export:
        return _with_prefix("index.js")

    return None


# ==================== JULES-STYLE RETRO GRADIENT BANNER ====================

GEMBOT_LOGO = [
    r" ██████╗ ███████╗███╗   ███╗██████╗  ██████╗ ████████╗",
    r"██╔════╝ ██╔════╝████╗ ████║██╔══██╗██╔═══██╗╚══██╔══╝",
    r"██║  ███╗█████╗  ██╔████╔██║██████╔╝██║   ██║   ██║   ",
    r"██║   ██║██╔══╝  ██║╚██╔╝██║██╔══██╗██║   ██║   ██║   ",
    r"╚██████╔╝███████╗██║ ╚═╝ ██║██████╔╝╚██████╔╝   ██║   ",
    r" ╚═════╝ ╚══════╝╚═╝     ╚═╝╚═════╝  ╚═════╝    ╚═╝   ",
]

GRADIENT_COLORS = [
    "#E0C3FC",
    "#C8B6FF",
    "#B8C0FF",
    "#9D4EDD",
    "#7B2CBF",
    "#5A189A",
]


def print_banner() -> None:
    console.print()
    banner_text = ""
    for i, line in enumerate(GEMBOT_LOGO):
        color = GRADIENT_COLORS[i % len(GRADIENT_COLORS)]
        banner_text += f"[{color}]{line}[/{color}]\n"

    cwd = os.getcwd()
    git_branch = "unknown/unknown"
    try:
        r = subprocess.run("git branch --show-current", shell=True, capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            git_branch = f"git:{r.stdout.strip()}"
    except Exception:
        pass

    info_text = (
        f"{banner_text}\n"
        f"[bold bright_magenta]✨ GEMBOT AUTONOMOUS AI AGENT CLI[/bold bright_magenta] [dim]• v2.0.0[/dim]\n"
        f"[dim]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/dim]\n"
        f" [bold bright_cyan]● MODEL:[/bold bright_cyan]     [bold white]{MODEL}[/bold white]  [dim]• type [bold yellow]/models[/bold yellow] to change[/dim]\n"
        f" [bold bright_yellow]📂 FOLDER:[/bold bright_yellow]    [bold cyan]{cwd}[/bold cyan]  [dim]({git_branch})[/dim]\n"
        f" [bold bright_green]⚡ TOOLS:[/bold bright_green]     [white]30 Autonomous Tools Active[/white] [dim](patch edits, backups, web browse)[/dim]\n"
        f" [bold bright_blue]🌐 WEB APP:[/bold bright_blue]   [link=http://localhost:3000][bold underline bright_blue]http://localhost:3000[/bold underline bright_blue][/link]  [dim](BorderBeam & ThinkingOrbs UI)[/dim]\n"
        f"[dim]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/dim]\n"
        f" [italic white]What would you like to build or automate today?[/italic white]\n"
        f" [dim]Shortcuts: [bold cyan]Ctrl+V[/bold cyan] attach image · [bold yellow]/plan[/bold yellow] checklist mode · [bold red]Ctrl+C[/bold red] abort[/dim]"
    )

    console.print(Panel(
        info_text,
        border_style="bright_magenta",
        title="[bold bright_white on dark_magenta] 🤖 GEMBOT NEURAL CONSOLE [/bold bright_white on dark_magenta]",
        subtitle="[bold dim]Autonomous Multi-Tool Self-Healing Loop[/bold dim]",
        padding=(1, 2)
    ))
    console.print()


def _tool_call_parts(call) -> tuple[str, dict]:
    """Read an Ollama tool call from its model object or wire-format dict."""
    function = call.get("function", {}) if isinstance(call, dict) else getattr(call, "function", None)
    if isinstance(function, dict):
        name, arguments = function.get("name"), function.get("arguments", {})
    else:
        name, arguments = getattr(function, "name", None), getattr(function, "arguments", {})
    if isinstance(arguments, str):
        arguments = json.loads(arguments)
    if not isinstance(name, str) or not name or not isinstance(arguments, dict):
        raise ValueError("tool call must contain a function name and an arguments object")
    return name, arguments


def _normalize_tool_args(name: str, args: dict) -> tuple[dict, str | None]:
    """Repair known local-model wrappers while keeping tool contracts strict."""
    normalized = dict(args)
    if name == "write_file":
        content = normalized.get("content")
        if isinstance(content, dict):
            if content.get("type") == "string" and "content" in content:
                normalized["content"] = str(content["content"])
            elif "content" in content:
                normalized["content"] = str(content["content"])
            elif "value" in content:
                normalized["content"] = str(content["value"])
            elif "text" in content:
                normalized["content"] = str(content["text"])
            elif "code" in content:
                normalized["content"] = str(content["code"])
            else:
                normalized["content"] = json.dumps(content, indent=2)
        elif not isinstance(content, str) and content is not None:
            normalized["content"] = str(content)
        elif content is None:
            normalized["content"] = ""

        path = normalized.get("path")
        if isinstance(path, dict):
            normalized["path"] = str(path.get("path") or path.get("file") or path.get("filename") or "")
        elif not isinstance(path, str) and path is not None:
            normalized["path"] = str(path)

    elif name == "edit_file":
        for k in ("old_str", "new_str", "path"):
            v = normalized.get(k)
            if isinstance(v, dict):
                normalized[k] = str(v.get("content") or v.get("value") or v.get("text") or json.dumps(v))
            elif not isinstance(v, str) and v is not None:
                normalized[k] = str(v)

    elif name == "run_command":
        cmd = normalized.get("command")
        if isinstance(cmd, dict):
            normalized["command"] = str(cmd.get("command") or cmd.get("cmd") or cmd.get("value") or "")
        elif not isinstance(cmd, str) and cmd is not None:
            normalized["command"] = str(cmd)

    return normalized, None


def _parse_raw_tool_calls(reply: str) -> list[dict]:
    """Extract all complete, schema-valid JSON actions from model text."""
    decoder = json.JSONDecoder()
    extracted = []
    idx = 0
    while idx < len(reply):
        start = reply.find("{", idx)
        if start == -1:
            break
        try:
            payload, end = decoder.raw_decode(reply[start:])
            idx = start + max(1, end)
            if not isinstance(payload, dict):
                continue
            name = payload.get("name") or payload.get("tool")
            if name == "create_dir":
                name = "make_dir"
            elif name == "git_clone":
                name = "clone_repo"
            has_arguments = any(key in payload for key in ("arguments", "parameters", "args"))
            arguments = payload.get("arguments", payload.get("parameters", payload.get("args", {})))
            if isinstance(name, str) and name in TOOLS and has_arguments and isinstance(arguments, dict):
                extracted.append({"function": {"name": name, "arguments": arguments}})
        except json.JSONDecodeError:
            idx = start + 1
            continue
    return extracted


def _extract_code_block_writes(reply: str, history: list) -> list[dict]:
    """Fallback: extract code blocks with file paths or headers when model outputs prose code."""
    blocks = re.findall(r'(?:###?\s*(?:file(?:name)?:\s*|path:\s*)?([a-zA-Z0-9_./\\-]+\.[a-zA-Z0-9]+)\s*\n+)?```([a-zA-Z0-9_-]*)\n(.*?)```', reply, re.DOTALL)
    calls = []
    for file_hint, lang, code in blocks:
        code_str = code.strip()
        if not code_str or len(code_str) < 15:
            continue
        target_path = file_hint.strip() if file_hint else None
        if not target_path:
            inferred = _infer_filename_from_content(code_str, history)
            if inferred:
                target_path = inferred
        if target_path:
            calls.append({"function": {"name": "write_file", "arguments": {"path": target_path, "content": code_str}}})
    return calls


def run_task(instruction: str, history: list, images: list = None) -> None:
    global STOP_REQUESTED, MODEL
    _clear_stop_requested()

    msg = {"role": "user", "content": instruction}
    if images:
        msg["images"] = images
    history.append(msg)
    consecutive_text_retries = 0
    files_created: set[str] = set()

    for step in range(MAX_STEPS):
        if STOP_REQUESTED:
            console.print("\n[bold red]🛑 [gembot]: Execution cancelled by user.[/bold red]\n")
            return

        # Auto-summarize history if getting long
        history[:] = auto_summarize_history(history, max_messages=MAX_HISTORY)
        gc.collect()

        # Run ollama.chat in a daemon thread so the main thread stays responsive
        # to Ctrl+C. On Windows, blocking C-level I/O can't be interrupted by signals.
        # We create a dedicated ollama.Client per call so we can forcefully close
        # its underlying httpx connection when the user presses Ctrl+C.
        def _ollama_chat_threaded(model, messages, tools):
            """Run ollama.chat in a background thread, returns (response, error)."""
            container = {"resp": None, "error": None}
            # Create a per-call client so we can kill its connection on abort
            client = ollama.Client()
            def _call():
                try:
                    options = {
                        "num_predict": int(CONFIG.get("num_predict", 4096)),
                        "num_ctx": int(CONFIG.get("num_ctx", 8192)),
                    }
                    container["resp"] = client.chat(model=model, messages=messages, tools=tools, options=options)
                except Exception as e:
                    container["error"] = e
            t = threading.Thread(target=_call, daemon=True)
            t.start()
            while t.is_alive():
                if STOP_REQUESTED:
                    # Forcefully close the underlying HTTP connection to unblock the thread
                    try:
                        if hasattr(client, '_client') and client._client:
                            client._client.close()
                    except Exception:
                        pass
                    # Give the thread a moment to notice the closed connection
                    t.join(timeout=0.5)
                    return None, "stopped"
                t.join(timeout=0.1)
            if container["error"]:
                return None, container["error"]
            return container["resp"], None

        try:
            status = Status(
                f"[bold bright_magenta]GEMBOT[/bold bright_magenta] "
                f"[bold bright_cyan]Thinking Engine[/bold bright_cyan] "
                f"[dim](Model: [bold white]{MODEL}[/bold white] • Step {step+1}/{MAX_STEPS})[/dim] "
                f"[dim]• [bold red]Ctrl+C[/bold red] to stop[/dim]",
                spinner="thinking_bar",
                spinner_style="bold bright_cyan",
                console=console
            )
            status.start()
        except Exception:
            status = None
        try:
            resp, err = _ollama_chat_threaded(MODEL, history, list(TOOLS.values()))
            if err == "stopped":
                console.print("\n[bold red]🛑 [gembot]: Execution STOPPED by user (Ctrl+C).[/bold red]\n")
                return
            if isinstance(err, MemoryError):
                console.print("\n[bold yellow]⚠ Memory pressure detected — trimming context and retrying...[/bold yellow]")
                history[:] = auto_summarize_history(history, max_messages=MAX_HISTORY // 2)
                gc.collect()
                resp, err2 = _ollama_chat_threaded(MODEL, history, list(TOOLS.values()))
                if err2 == "stopped":
                    console.print("\n[bold red]🛑 [gembot]: Execution STOPPED by user (Ctrl+C).[/bold red]\n")
                    return
                if err2:
                    console.print(f"\n[bold red][!] Memory Error:[/bold red] {err2}")
                    return
            elif err is not None:
                if images and "does not support multimodal requests" in str(err).lower():
                    console.print(
                        "\n[bold yellow]⚠ This model can't read images.[/bold yellow] "
                        "Use [bold cyan]/models[/bold cyan] to switch to a vision-capable model "
                        "such as [bold white]gemma4:e2b[/bold white], then retry [bold cyan]/paste[/bold cyan].\n"
                    )
                    return
                # Model fallback handling
                fallback = CONFIG.get("fallback_model", "qwen2.5-coder:3b")
                if fallback != MODEL:
                    console.print(f"\n[bold yellow]⚠ Model '{MODEL}' failed. Auto-falling back to '{fallback}'...[/bold yellow]")
                    MODEL = fallback
                    resp, err_fb = _ollama_chat_threaded(MODEL, history, list(TOOLS.values()))
                    if err_fb == "stopped":
                        console.print("\n[bold red]🛑 [gembot]: Execution STOPPED by user (Ctrl+C).[/bold red]\n")
                        return
                    if err_fb:
                        console.print(f"[bold red][!] Fallback also failed:[/bold red] {err_fb}")
                        return
                else:
                    console.print(f"\n[bold red][!] Ollama Error:[/bold red] {err}\n[dim]Verify model '{MODEL}'[/dim]")
                    return
        except KeyboardInterrupt:
            _set_stop_requested()
            console.print("\n[bold red]🛑 [gembot]: Execution STOPPED by user (Ctrl+C).[/bold red]\n")
            return
        finally:
            try:
                if status:
                    status.stop()
            except Exception:
                pass

        msg = resp.message
        history.append(msg)
        tool_calls = list(msg.tool_calls or [])

        # Fallback raw-JSON and markdown-block tool call parsing
        if not tool_calls:
            reply = msg.content.strip() if msg.content else ""
            extracted_tool_calls = _parse_raw_tool_calls(reply)
            if not extracted_tool_calls:
                extracted_tool_calls = _extract_code_block_writes(reply, history)
            if extracted_tool_calls:
                tool_calls = extracted_tool_calls
                history[-1] = {"role": "assistant", "content": reply, "tool_calls": tool_calls}
                console.print(f"  [bold bright_green]🧠 AUTO-PARSED ACTIONS:[/bold bright_green] [dim]Extracted {len(tool_calls)} action(s) from model text[/dim]")
            else:
                consecutive_text_retries += 1
                lower_reply = reply.lower()

                # Check if user requested building/coding an application
                user_wants_code = any(kw in instruction.lower() for kw in (
                    "build", "create", "code", "app", "ui", "chat", "next", "react", "component", "scaffold", "implement", "stream"
                ))
                has_code_file = any(
                    f.endswith((".tsx", ".ts", ".jsx", ".js", ".py", ".html", ".css"))
                    for f in files_created
                )

                if user_wants_code and not has_code_file and step < MAX_STEPS - 3:
                    if reply:
                        console.print()
                        console.print(Panel(Markdown(reply), title="[bold bright_magenta]GEMBOT Progress[/bold bright_magenta]", border_style="dim magenta"))
                    console.print(f"  [bold yellow]⚡ PROCEEDING WITH CODE GENERATION:[/bold yellow] [dim]Source code files not yet written. Prompting model for next file (step {step+2}/{MAX_STEPS})...[/dim]")
                    active_dir = _get_active_project_dir(history) or "chatbox-x"
                    history.append({
                        "role": "user",
                        "content": (
                            f"DO NOT STOP YET. You have not written the actual application source code files yet. "
                            f"You must call write_file now to create the main application component (e.g. {active_dir}/src/app/page.tsx or Chatbox.tsx) "
                            f"and the model streaming client (e.g. {active_dir}/src/models/chatbox.ts). "
                            f"Output a valid write_file tool call now."
                        )
                    })
                    continue

                is_completed = (
                    (not user_wants_code or has_code_file) and (
                        any(p in lower_reply for p in ("all steps completed", "work is complete", "task is complete", "project is ready", "summary of completed"))
                        or consecutive_text_retries >= 3
                    )
                )

                if is_completed or step == MAX_STEPS - 1:
                    if reply:
                        console.print()
                        console.print(Panel(Markdown(reply), title="[bold bright_magenta]GEMBOT Response[/bold bright_magenta]", border_style="bright_magenta"))
                        console.print()
                    return

                if reply:
                    console.print()
                    console.print(Panel(Markdown(reply), title="[bold bright_magenta]GEMBOT Thinking...[/bold bright_magenta]", border_style="dim magenta"))
                console.print(f"  [bold yellow]⚡ CONTINUING TASK:[/bold yellow] [dim]Requesting next action from schema (step {step+2}/{MAX_STEPS})...[/dim]")
                history.append({"role": "user", "content": "Please continue with the remaining steps to fulfill the user's task. Output schema-valid tool calls (e.g. write_file, edit_file, run_command) for each file or command needed until the entire project is completed."})
                continue

        # Execute Tools and reset consecutive text retry counter
        consecutive_text_retries = 0
        for call in tool_calls:
            if STOP_REQUESTED:
                console.print("\n[bold red]🛑 [gembot]: Action aborted by user.[/bold red]\n")
                return

            try:
                name, args = _tool_call_parts(call)
            except (TypeError, ValueError, json.JSONDecodeError) as e:
                result = f"Error: ignored malformed tool call: {e}."
                console.print(f"  [bold red]⚠ {result}[/bold red]")
                history.append({"role": "tool", "tool_name": "invalid_tool_call", "content": result})
                continue

            args, argument_error = _normalize_tool_args(name, args)
            if argument_error:
                result = f"Error: {argument_error}"
                console.print(f"  [bold red]⚠ {result}[/bold red]")
                history.append({"role": "tool", "tool_name": name, "content": result})
                continue

            if name == "write_file":
                path = args.get("path", "").strip() if isinstance(args.get("path"), str) else ""
                content = args.get("content", "")
                if isinstance(content, dict):
                    content = str(content.get("content") or json.dumps(content, indent=2))
                elif not isinstance(content, str):
                    content = str(content or "")

                if not path:
                    inferred = _infer_filename_from_content(content, history)
                    if inferred:
                        path = os.path.join(os.getcwd(), inferred)
                        args["path"] = path
                        console.print(f"\n  [bold bright_green]🧠 AUTO-INFERRED PATH:[/bold bright_green] [dim]Inferred as[/dim] [bold white]{path}[/bold white]")
                    else:
                        path = os.path.join(os.getcwd(), f"output_{int(time.time())}.txt")
                        args["path"] = path

                files_created.add(path)
                console.print(f"\n  [bold bright_green]🔨 BUILDING / CREATING FILE:[/bold bright_green] [bold white]{path}[/bold white]")
                code_lines = content.splitlines()
                preview = "\n".join(code_lines[:20])
                if len(code_lines) > 20:
                    preview += f"\n... [+{len(code_lines) - 20} more lines written to {path}]"
                console.print(Panel(preview, title=f"[dim cyan]Live Code Generator: {os.path.basename(path)}[/dim cyan]", border_style="cyan"))

            elif name == "edit_file":
                target_p = args.get("path", "")
                console.print(f"\n  [bold bright_yellow]✏ PRECISION PATCH EDIT:[/bold bright_yellow] [bold white]{target_p}[/bold white]")

            elif name in ("web_search", "browse_webpage"):
                val = list(args.values())[0] if args else ""
                console.print(f"\n  [bold bright_blue]🌐 LIVE WEB RESEARCH:[/bold bright_blue] [white]{name} -> {val}[/white]")

            elif name == "run_command":
                cmd = args.get("command", "")
                console.print(f"\n  [bold bright_yellow]⚡ EXECUTING COMMAND:[/bold bright_yellow] [bold yellow]{cmd}[/bold yellow]")

            elif name == "git_commit_and_push":
                msg_txt = args.get("commit_message", "")
                console.print(f"\n  [bold bright_magenta]🐙 GITHUB AUTOMATION:[/bold bright_magenta] [white]{msg_txt}[/white]")

            else:
                console.print(f"\n  [dim cyan]⚡ [tool] {name}({args})[/dim cyan]")

            try:
                tool_status = Status(f"[dim]Running action {name}...[/dim]", spinner="dots", console=console)
                tool_status.start()
            except Exception:
                tool_status = None
            try:
                fn = TOOLS.get(name)
                if fn is None:
                    result = f"Error: unknown tool '{name}'. Available: {', '.join(TOOLS.keys())}."
                else:
                    result = fn(**args)
                # Check if Ctrl+C was pressed during tool execution
                if STOP_REQUESTED:
                    console.print(f"\n[bold red]🛑 [gembot]: Action '{name}' aborted by user.[/bold red]\n")
                    result = "User aborted this action via Ctrl+C."
                    history.append({"role": "tool", "tool_name": name, "content": str(result)})
                    return
            except KeyboardInterrupt:
                _set_stop_requested()
                console.print(f"\n[bold red]🛑 [gembot]: Action '{name}' aborted by user.[/bold red]\n")
                result = "User aborted this action via Ctrl+C."
                history.append({"role": "tool", "tool_name": name, "content": str(result)})
                return
            except TypeError as e:
                result = f"Error: Tool '{name}' invalid arguments: {e}. Args: {args}."
            except Exception as e:
                result = f"Error executing tool '{name}': {e}."
            finally:
                try:
                    if tool_status:
                        tool_status.stop()
                except Exception:
                    pass

            # Log activity to session log
            log_session_activity(name, args, str(result))

            if name != "write_file":
                short_result = str(result)[:300] + ("..." if len(str(result)) > 300 else "")
                console.print(f"     [dim]↳ Result:[/dim] [bright_black]{short_result}[/bright_black]")

            res_str = str(result)
            if len(res_str) > MAX_OUTPUT:
                res_str = res_str[:MAX_OUTPUT] + f"\n... [Output truncated to {MAX_OUTPUT} characters]"
            history.append({"role": "tool", "tool_name": name, "content": res_str})

    console.print("\n[dim][gembot] Completed maximum autonomous steps for this task.[/dim]\n")


def parse_multimodal_input(raw_input: str) -> tuple[str, list]:
    """Inspect input for paths to images, PDFs, files, or clipboard paste and attach their contents."""
    images = []
    text_additions = []
    handled_paths = set()

    trimmed = raw_input.strip()
    paste_match = re.fullmatch(r"(?:/paste|paste|/clip|clip)(?:\s+(.*))?", trimmed, re.IGNORECASE | re.DOTALL)
    is_paste_command = paste_match is not None
    paste_question = paste_match.group(1).strip() if paste_match and paste_match.group(1) else ""

    patterns = [
        r'(?:&?\s*["\']([A-Za-z]:\\[^"\'<>|]+)["\'])',
        r'(?:&?\s*["\']([.]{1,2}/[^"\'<>|]+|/[^"\'<>|]+)["\'])',
        r'(?:[A-Za-z]:\\[^\s"\'<>|]+(?:\.[A-Za-z0-9_-]+)?)',
        r'(?:(?:\.{1,2}[/\\]|[a-zA-Z0-9_-]+[/\\])[^\s"\'<>|]+\.[a-zA-Z0-9]+)',
        r'(?:[a-zA-Z0-9_-]+\.(?:png|jpg|jpeg|webp|bmp|gif|pdf|txt|log|py|js|json|html|css|md|csv|env))',
    ]

    found_candidates = []
    for pat in patterns:
        for match in re.findall(pat, raw_input):
            p_val = match if isinstance(match, str) else match[0]
            if p_val and p_val not in found_candidates:
                found_candidates.append(p_val)

    for p_str in found_candidates:
        res = extract_content_from_path(p_str)
        if not res and not os.path.isabs(p_str):
            res = extract_content_from_path(os.path.join(os.getcwd(), p_str))

        if res and res.get("path") not in handled_paths:
            handled_paths.add(res["path"])
            if res.get("type") == "image":
                images.append(res["data"])
                console.print(f"[dim green]  📎 Attached Image: {res['path']}[/dim green]")
            elif res.get("type") == "text":
                text_additions.append(f"\n[Attached File Contents of {res['path']}]:\n{res['content']}\n")
                console.print(f"[dim green]  📎 Read & Attached Document: {res['path']}[/dim green]")

    # Only read the clipboard on an explicit paste command. Otherwise a stale
    # image can be attached to every normal text prompt and rejected by models
    # that do not accept multimodal input.
    if is_paste_command:
        clip_res = get_clipboard_image()
        if clip_res:
            if clip_res.get("type") == "image":
                images.append(clip_res["data"])
                console.print(f"[bold bright_green]  📎 Attached Image directly from Clipboard[/bold bright_green]")
            elif clip_res.get("type") == "text" and is_paste_command:
                text_additions.append(f"\n[Attached File Contents of {clip_res['path']}]:\n{clip_res['content']}\n")
                console.print(f"[bold bright_green]  📎 Attached File from Clipboard: {clip_res['path']}[/bold bright_green]")

    full_prompt = raw_input
    if is_paste_command:
        full_prompt = paste_question or "Analyze the attached image or file from clipboard and help me fix the issue shown in it."

    if text_additions:
        full_prompt = full_prompt + "\n" + "\n".join(text_additions)

    return full_prompt, images


def make_terminal_key_bindings(pending_images: list) -> KeyBindings:
    """Let Ctrl+V explicitly attach the current clipboard image to the prompt."""
    bindings = KeyBindings()

    @bindings.add("c-v")
    def paste_clipboard(event):
        clipboard_item = get_clipboard_image()
        if clipboard_item.get("type") == "image":
            pending_images.append(clipboard_item["data"])
            event.app.invalidate()
            return

        # Preserve text-paste behavior when the system clipboard has no image.
        text = clipboard_read()
        if text and not text.lower().startswith("error") and "clipboard is empty" not in text.lower():
            event.current_buffer.insert_text(text)
            return
        try:
            internal_clipboard = event.app.clipboard.get_data()
            if internal_clipboard.text:
                event.current_buffer.insert_text(internal_clipboard.text)
        except Exception:
            pass

    return bindings


def select_model_interactive() -> str:
    """List available Ollama models in a rich table and allow the user to select one."""
    global MODEL
    ensure_ollama_running()
    try:
        res = ollama.list()
        raw_models = getattr(res, "models", []) or res.get("models", [])
    except Exception as e:
        console.print(f"[bold red]Error fetching models from Ollama:[/bold red] {e}")
        return MODEL

    model_list = []
    for m in raw_models:
        name = getattr(m, "model", None) or (m.get("name") if isinstance(m, dict) else str(m))
        if name:
            size_b = getattr(m, "size", 0) or (m.get("size", 0) if isinstance(m, dict) else 0)
            if size_b and size_b > 1024 * 1024 * 1024:
                size_str = f"{size_b / (1024**3):.1f} GB"
            elif size_b and size_b > 1024 * 1024:
                size_str = f"{size_b / (1024**2):.1f} MB"
            else:
                size_str = "-"
            model_list.append({"name": name, "size": size_str})

    if not model_list:
        console.print("[yellow]No models found in local Ollama library.[/yellow]")
        return MODEL

    table = Table(title="[bold bright_magenta]🤖 Available Ollama Models[/bold bright_magenta]", border_style="bright_magenta")
    table.add_column("#", style="bold yellow", justify="center", width=4)
    table.add_column("Model Name", style="bold cyan", min_width=24)
    table.add_column("Size", style="dim white", justify="right", width=12)
    table.add_column("Status", style="bold green", justify="center", width=14)

    for idx, item in enumerate(model_list, 1):
        status = "[bold green]● Active[/bold green]" if item["name"] == MODEL else "[dim]available[/dim]"
        table.add_row(str(idx), item["name"], item["size"], status)

    console.print()
    console.print(table)
    console.print(f"\n[dim]Current model is:[/dim] [bold cyan]{MODEL}[/bold cyan]")
    console.print("[bright_yellow]Enter number or full model name to switch (or press Enter to cancel):[/bright_yellow]")

    try:
        choice = prompt("select> ").strip()
    except (EOFError, KeyboardInterrupt):
        return MODEL

    if not choice:
        return MODEL

    chosen_name = None
    if choice.isdigit():
        idx_choice = int(choice)
        if 1 <= idx_choice <= len(model_list):
            chosen_name = model_list[idx_choice - 1]["name"]
        else:
            console.print(f"[bold red]Invalid selection number: {choice}[/bold red]")
            return MODEL
    else:
        for item in model_list:
            if item["name"].lower() == choice.lower():
                chosen_name = item["name"]
                break
        if not chosen_name:
            chosen_name = choice

    set_active_model(chosen_name)
    MODEL = chosen_name
    console.print(f"[bold bright_green]✓ Active model switched to:[/bold bright_green] [bold white]{chosen_name}[/bold white]")
    return chosen_name


def main() -> None:
    global MODEL, AUTO_CONFIRM
    ensure_ollama_running()
    print_banner()

    args = sys.argv[1:]
    if args:
        direct_task = " ".join(args).strip()
        console.print(f"[bold cyan]Task:[/bold cyan] {direct_task}")
        processed_prompt, imgs = parse_multimodal_input(direct_task)
        history = [{"role": "system", "content": build_system_prompt()}]
        run_task(processed_prompt, history, imgs)
        return

    history = [{"role": "system", "content": build_system_prompt()}]

    custom_style = Style.from_dict({
        'prompt': '#D946EF bold',
        'toolbar': '#94A3B8 italic',
    })
    pending_clipboard_images = []
    input_key_bindings = make_terminal_key_bindings(pending_clipboard_images)

    def input_toolbar():
        if pending_clipboard_images:
            count = len(pending_clipboard_images)
            label = "image" if count == 1 else "images"
            return HTML(f"<ansigreen>📎 {count} {label} attached</ansigreen>  <ansigray>Ctrl+V add more · Enter send · /paste [question] also works</ansigray>")
        return HTML("<ansigray>💡 Tip: Type / for commands (/plan, /undo, /tools, /models) · Web UI: http://localhost:3000</ansigray>")

    while True:
        # Always clear the stop flag before waiting for input
        _clear_stop_requested()
        try:
            task = prompt(
                [('class:prompt', '┌──(gembot㉿terminal)-[autonomous]\n└─◆ ')],
                style=custom_style,
                key_bindings=input_key_bindings,
                bottom_toolbar=input_toolbar,
            ).strip()
        except KeyboardInterrupt:
            # Ctrl+C at the prompt just cancels the current input, not the program
            _clear_stop_requested()
            console.print("\n[dim yellow]  (Input cancelled — press Ctrl+C again or type 'exit' to quit)[/dim yellow]")
            continue
        except EOFError:
            console.print("\n[bright_magenta]Goodbye from GEMBOT![/bright_magenta]")
            break

        if not task:
            if pending_clipboard_images:
                task = "Please analyze the attached image and help me fix the issue shown."
            else:
                continue
        if task.lower() in {"exit", "quit", "q", "/exit"}:
            console.print("[bright_magenta]Exiting GEMBOT. Have a great day![/bright_magenta]")
            break

        if task.lower() in {"clear", "/clear"}:
            history = [{"role": "system", "content": build_system_prompt()}]
            console.clear()
            print_banner()
            console.print("[dim cyan]Conversation memory cleared.[/dim cyan]")
            continue

        if task.lower() in {"/undo", "undo"}:
            success, msg = undo_last_change()
            color = "bright_green" if success else "yellow"
            console.print(f"[{color}]{msg}[/{color}]")
            continue

        if task.lower().startswith(("/dir", "/pwd", "dir", "pwd", "/where", "/cd ", "cd ")):
            parts = task.split(maxsplit=1)
            cmd = parts[0].lower()
            target_path = parts[1].strip().strip('"').strip("'") if len(parts) > 1 else ""

            if target_path and cmd in ("/cd", "cd", "/dir", "dir"):
                try:
                    os.makedirs(target_path, exist_ok=True)
                    os.chdir(target_path)
                    console.print(f"[bold bright_green]✓ Active working folder switched to:[/bold bright_green] [bold white]{os.getcwd()}[/bold white]")
                except Exception as e:
                    console.print(f"[bold red]Error changing directory:[/bold red] {e}")
                continue

            # Point out directory structure
            curr = os.getcwd()
            try:
                items = os.listdir(curr)
                dirs = [d for d in items if os.path.isdir(os.path.join(curr, d)) and not d.startswith(".")]
                files = [f for f in items if os.path.isfile(os.path.join(curr, f))]
            except Exception as e:
                console.print(f"[bold red]Error reading directory:[/bold red] {e}")
                continue

            tree_text = f"[bold cyan]📁 Local Working Directory:[/bold cyan] [bold white]{curr}[/bold white]\n\n"
            tree_text += f"[bold yellow]Subdirectories ({len(dirs)}):[/bold yellow] " + (", ".join(dirs) if dirs else "[dim]none[/dim]") + "\n"
            tree_text += f"[bold green]Files ({len(files)}):[/bold green] " + (", ".join(files[:25]) if files else "[dim]none[/dim]")
            if len(files) > 25:
                tree_text += f" [dim](+{len(files)-25} more files)[/dim]"
            tree_text += "\n\n[dim]Tip: Type '/cd <folder>' to change active directory.[/dim]"
            console.print(Panel(tree_text, title="[bold bright_magenta]📂 File Directory Pointer[/bold bright_magenta]", border_style="bright_magenta"))
            continue

        if task.lower().startswith("/auto"):
            parts = task.split(maxsplit=1)
            if len(parts) > 1 and parts[1].strip().lower() in ("on", "1", "true"):
                AUTO_CONFIRM = True
                console.print("[bold bright_green]✓ Auto-confirmation mode enabled (prompts skipped).[/bold bright_green]")
            elif len(parts) > 1 and parts[1].strip().lower() in ("off", "0", "false"):
                AUTO_CONFIRM = False
                console.print("[bold yellow]✓ Confirmation gate active (asking y/n for dangerous actions).[/bold yellow]")
            else:
                state = "ON (auto-confirm)" if AUTO_CONFIRM else "OFF (asks confirmation)"
                console.print(f"[dim]Auto mode is currently:[/dim] [bold cyan]{state}[/bold cyan] [dim](usage: /auto on|off)[/dim]")
            continue

        if task.lower().startswith("/save"):
            parts = task.split(maxsplit=1)
            name = parts[1].strip() if len(parts) > 1 else f"session_{int(time.time())}"
            ok, msg = save_session(name, history)
            console.print(f"[dim cyan]{msg}[/dim cyan]")
            continue

        if task.lower().startswith("/load"):
            parts = task.split(maxsplit=1)
            if len(parts) > 1 and parts[1].strip():
                loaded, msg = load_session(parts[1].strip())
                if loaded:
                    history = loaded
                    console.print(f"[bold bright_green]✓ {msg}[/bold bright_green]")
                else:
                    console.print(f"[bold red]{msg}[/bold red]")
            else:
                console.print(f"[yellow]Available sessions: {', '.join(list_sessions()) or 'None'}[/yellow]")
            continue

        if task.lower().startswith("/plan"):
            parts = task.split(maxsplit=1)
            prompt_plan = parts[1].strip() if len(parts) > 1 else ""
            instruction = (
                f"PLANNING MODE: Break this task down into a numbered checklist with clear steps, "
                f"show the checklist, then execute step 1 immediately with a tool call:\n{prompt_plan}"
            )
            processed_prompt, imgs = parse_multimodal_input(instruction)
            imgs.extend(pending_clipboard_images)
            pending_clipboard_images.clear()
            run_task(processed_prompt, history, imgs)
            continue

        if task.lower().startswith("/models") or task.lower().startswith("/model"):
            parts = task.split(maxsplit=1)
            if len(parts) > 1 and parts[1].strip():
                new_m = parts[1].strip()
                set_active_model(new_m)
                MODEL = new_m
                console.print(f"[bold bright_green]✓ Active model switched to:[/bold bright_green] [bold white]{new_m}[/bold white]\n")
            else:
                select_model_interactive()
            continue

        if task.lower() in {"/tools", "tools"}:
            console.print("\n[bold bright_magenta]Registered GEMBOT Tools (Total: " + str(len(TOOLS)) + "):[/bold bright_magenta]")
            for k in sorted(TOOLS.keys()):
                console.print(f"  • [bold cyan]{k}[/bold cyan]")
            console.print()
            continue

        if task.lower() in {"/help", "help"}:
            console.print("\n[bold bright_magenta]GEMBOT Slash Commands & Shortcuts:[/bold bright_magenta]")
            console.print("  [bold yellow]/models[/bold yellow]          - List and interactively select your Ollama model")
            console.print("  [bold yellow]/models <name>[/bold yellow]   - Directly switch model (e.g. /models qwen2.5-coder:7b)")
            console.print("  [bold yellow]/paste [question][/bold yellow] - Attach clipboard image and ask a question")
            console.print("  [bold yellow]Ctrl+V[/bold yellow]            - Attach the clipboard image to the message being composed")
            console.print("  [bold yellow]/undo[/bold yellow]            - Restore the last modified file from backups")
            console.print("  [bold yellow]/auto on|off[/bold yellow]    - Toggle confirmation prompts for dangerous actions")
            console.print("  [bold yellow]/plan <task>[/bold yellow]    - Force step-by-step checklist planning mode")
            console.print("  [bold yellow]/save <name>[/bold yellow]    - Save current conversation session")
            console.print("  [bold yellow]/load <name>[/bold yellow]    - Restore a previous session")
            console.print("  [bold yellow]/tools[/bold yellow]           - List all available autonomous tools")
            console.print("  [bold yellow]/clear[/bold yellow]           - Clear screen and conversation memory")
            console.print("  [bold yellow]/exit[/bold yellow] or [bold yellow]exit[/bold yellow]    - Exit the gembot CLI")
            console.print("  [bold yellow]Ctrl+C[/bold yellow]          - Immediately abort running action or tool\n")
            continue

        processed_prompt, imgs = parse_multimodal_input(task)
        imgs.extend(pending_clipboard_images)
        pending_clipboard_images.clear()
        _clear_stop_requested()
        try:
            run_task(processed_prompt, history, imgs)
        except KeyboardInterrupt:
            console.print("\n[bold red]🛑 [gembot]: Execution interrupted.[/bold red]\n")
        finally:
            _clear_stop_requested()


if __name__ == "__main__":
    sys.exit(main())
