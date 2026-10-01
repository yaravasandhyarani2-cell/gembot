"""gembot - Autonomous Windows Desktop, Browser, and Coding AI Agent with Rich Jules-style CLI.
Powered by Ollama + gemma4:e2b with autonomous tool calling, web browsing, 
multimodal file attachments (images, PDFs, documents), self-coding, and Git/GitHub automation.
"""
import base64
import json
import os
import re
import shutil
import subprocess
import sys
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
from prompt_toolkit.styles import Style

console = Console()


# Central agent configuration path (%USERPROFILE%\agent\.env) and repo installation path
GLOBAL_ENV = Path(os.path.expandvars(r"%USERPROFILE%\agent\.env"))
REPO_ENV = Path(__file__).resolve().parent / ".env"

def load_active_model() -> str:
    """Read the latest MODEL setting from central config, falling back to local repo or default."""
    if GLOBAL_ENV.is_file():
        load_dotenv(GLOBAL_ENV, override=True)
    elif REPO_ENV.is_file():
        load_dotenv(REPO_ENV, override=True)
    return os.getenv("MODEL", "gemma4:e2b")

def save_active_model(new_model: str) -> None:
    """Save selected model to central %USERPROFILE%\\agent\\.env (and repo .env if existing).
    
    Never creates a new .env file in the user's current working project directory.
    """
    global MODEL
    MODEL = new_model
    os.environ["MODEL"] = new_model

    targets = [GLOBAL_ENV]
    if REPO_ENV.resolve() != GLOBAL_ENV.resolve() and REPO_ENV.exists():
        targets.append(REPO_ENV)

    for p in targets:
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            if p.is_file():
                lines = p.read_text(encoding="utf-8").splitlines()
                updated = False
                for idx, line in enumerate(lines):
                    if line.strip().startswith("MODEL="):
                        lines[idx] = f"MODEL={new_model}"
                        updated = True
                        break
                if not updated:
                    lines.append(f"MODEL={new_model}")
                p.write_text("\n".join(lines) + "\n", encoding="utf-8")
            else:
                p.write_text(f"MODEL={new_model}\n", encoding="utf-8")
        except Exception:
            pass

MODEL = load_active_model()
MAX_STEPS = int(os.getenv("MAX_STEPS", "16"))
MAX_OUTPUT = int(os.getenv("MAX_OUTPUT", "4000"))

SYSTEM = (
    "You are 'GEMBOT', an elite autonomous Windows AI assistant. "
    "You MUST use your tools to complete every task. NEVER just describe or plan — always ACT immediately.\n\n"
    "CRITICAL RULES (violating these is FAILURE):\n"
    "- ALWAYS call a tool on EVERY response. Never output a plan without calling a tool.\n"
    "- Start executing immediately. Write the first file NOW, run the first command NOW.\n"
    "- If a task has multiple steps, do the FIRST step immediately with a tool call.\n"
    "- Never say 'I will do X' without also DOING X in the same response via a tool call.\n"
    "- Complete tasks fully — write all files, run all commands, push to git if asked.\n\n"
    "Your Available Tools:\n"
    "1. write_file: Create or overwrite any file with content. Use for ALL code/config/text files.\n"
    "2. run_command: Execute any Windows shell command (mkdir, npm install, git, etc).\n"
    "3. read_file: Read existing file contents.\n"
    "4. list_files: List directory contents.\n"
    "5. web_search: Search the internet for information.\n"
    "6. browse_webpage: Open and read any webpage URL.\n"
    "7. git_commit_and_push: Stage, commit, and push to GitHub.\n\n"
    "Rules: Always use absolute paths. After completing a task, give a brief summary. "
    "REMEMBER: You MUST call a tool — text-only responses are NOT acceptable."
)


def _p(path: str) -> str:
    return os.path.abspath(os.path.expanduser(os.path.expandvars(path)))


def _cut(text: str) -> str:
    return text if len(text) <= MAX_OUTPUT else text[:MAX_OUTPUT] + "\n...[truncated]"


# ==================== JULES-STYLE RETRO GRADIENT BANNER ====================

GEMBOT_LOGO = [
    " ██████╗ ███████╗███╗   ███╗██████╗  ██████╗ ████████╗",
    "██╔════╝ ██╔════╝████╗ ████║██╔══██╗██╔═══██╗╚══██╔══╝",
    "██║  ███╗█████╗  ██╔████╔██║██████╔╝██║   ██║   ██║   ",
    "██║   ██║██╔══╝  ██║╚██╔╝██║██╔══██╗██║   ██║   ██║   ",
    "╚██████╔╝███████╗██║ ╚═╝ ██║██████╔╝╚██████╔╝   ██║   ",
    " ╚═════╝ ╚══════╝╚═╝     ╚═╝╚═════╝  ╚═════╝    ╚═╝   ",
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
    """Print the stunning Jules-style shaded gradient banner and metadata."""
    console.print()
    for i, line in enumerate(GEMBOT_LOGO):
        color = GRADIENT_COLORS[i % len(GRADIENT_COLORS)]
        console.print(f"[{color}]{line}[/{color}]")

    cwd = os.getcwd()
    git_branch = "unknown/unknown"
    try:
        r = subprocess.run("git branch --show-current", shell=True, capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            git_branch = f"git:{r.stdout.strip()}"
    except Exception:
        pass

    console.print()
    console.print(f"[bold bright_magenta]Welcome to GEMBOT CLI![/bold bright_magenta]")
    console.print(f"[dim]v1.0.0 • Autonomous Multi-Tool AI Agent[/dim]")
    console.print(f"[bright_cyan]Active Model:[/bright_cyan] [bold white]{MODEL}[/bold white]  [dim](type [bold yellow]/models[/bold yellow] to change)[/dim]")
    console.print(f"[bright_yellow]Working in:[/bright_yellow] [cyan]{cwd}[/cyan]  [dim]({git_branch})[/dim]")
    console.print(f"[italic white]What would you like to build or automate today?[/italic white]")
    console.print(f"[dim]Tip: Drag & drop files, or type [bold cyan]/models[/bold cyan] to switch models, [bold cyan]/help[/bold cyan] for commands.[/dim]")
    console.print(f"[bold bright_red]Stop Execution:[/bold bright_red] [dim]Press [bold white]Ctrl+C[/bold white] anytime while running to immediately halt the agent.[/dim]")
    console.print()



# ==================== MULTIMODAL / FILE ATTACHMENT EXTRACTOR ====================

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}
DOC_EXTENSIONS = {".pdf", ".txt", ".md", ".py", ".js", ".html", ".css", ".json", ".csv"}


def extract_content_from_path(raw_path: str) -> dict:
    """Extract text or image base64 if user dragged/pasted a file path."""
    clean_path = raw_path.strip().strip("'").strip('"')
    p = Path(clean_path)
    if not p.is_file():
        return {}

    ext = p.suffix.lower()

    # Image file: return image bytes for vision models
    if ext in IMAGE_EXTENSIONS:
        try:
            with open(p, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
                return {"type": "image", "data": b64, "path": str(p)}
        except Exception:
            return {}

    # PDF file: extract textual contents
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

    # Text / Code file
    if ext in DOC_EXTENSIONS or ext == "":
        try:
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                return {"type": "text", "content": f.read(), "path": str(p)}
        except Exception:
            return {}

    return {}


# ==================== FILESYSTEM & OS TOOLS ====================

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
            return "(directory is empty)"
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
    """Move or rename a file or folder. Creates destination folder if needed.

    Args:
        source: Existing file or folder path
        destination: New path (file path or target folder)
    """
    try:
        dest = _p(destination)
        src = _p(source)
        if not os.path.exists(src):
            return f"Error: Source '{src}' not found."
        if not os.path.splitext(dest)[1] and not os.path.exists(dest):
            os.makedirs(dest, exist_ok=True)
        else:
            os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
        shutil.move(src, dest)
        return f"Moved to {dest}"
    except Exception as e:
        return f"Error: {e}"


def read_file(path: str) -> str:
    """Read a text or code file.

    Args:
        path: Path to the file to inspect
    """
    try:
        full = _p(path)
        if not os.path.exists(full):
            return f"Error: File '{full}' does not exist."
        with open(full, "r", encoding="utf-8", errors="replace") as f:
            return _cut(f.read())
    except Exception as e:
        return f"Error: {e}"


def write_file(path: str, content: str) -> str:
    """Write or overwrite text or code to a file. Automatically creates folders.

    Args:
        path: Destination file path (e.g. C:\\Users\\Subhash\\Desktop\\assignment.py)
        content: Complete code or text content to write
    """
    try:
        full = _p(path)
        os.makedirs(os.path.dirname(full) or ".", exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully saved {len(content)} characters to {full}"
    except Exception as e:
        return f"Error: {e}"


def run_command(command: str) -> str:
    """Run a shell command autonomously (e.g. python script.py, npm test, pip install).

    Args:
        command: The shell command line to execute
    """
    console.print(f"  [bright_black]⚡ [gembot cmd]:[/bright_black] [bold yellow]{command}[/bold yellow]")
    try:
        r = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=120)
        out = (r.stdout + r.stderr).strip()
        return _cut(out or f"Executed successfully (exit code {r.returncode})")
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 120 seconds"
    except Exception as e:
        return f"Error: {e}"


def open_app(name_or_path: str) -> str:
    """Open an application, file, directory, or website in Windows.

    Args:
        name_or_path: App name (e.g. notepad, code, chrome), directory, or URL
    """
    try:
        target = name_or_path.strip()
        if os.path.exists(_p(target)):
            os.startfile(_p(target))
        else:
            subprocess.Popen(f'start "" "{target}"', shell=True)
        return f"Opened {target}"
    except Exception as e:
        return f"Error: {e}"


# ==================== WEB BROWSING & RESEARCH TOOLS ====================

def web_search(query: str, max_results: int = 5) -> str:
    """Search the web using DuckDuckGo to find information, research topics, or find assignment solutions.

    Args:
        query: Search keywords or question
        max_results: Number of results to return (default 5)
    """
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
    """Browse a web page using a headless browser, extracting the clean text and content.

    Args:
        url: The web URL to visit (e.g. https://en.wikipedia.org/... or documentation)
    """
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

        # Fallback to Playwright headless browser for JS-rendered pages
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


# ==================== GIT & GITHUB AUTOMATION TOOLS ====================

def git_commit_and_push(repo_path: str, commit_message: str, branch: str = "main", remote_url: str = "") -> str:
    """Stage all changes, commit them with a message, and push to GitHub repository.

    Args:
        repo_path: Local folder of the git repository (e.g. C:\\Users\\Subhash\\Desktop\\myproject)
        commit_message: Description of the changes made
        branch: Git branch name (default 'main')
        remote_url: Optional remote GitHub URL if repo needs to be linked (e.g. https://github.com/user/repo.git)
    """
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


TOOLS = {
    f.__name__: f
    for f in (
        list_files,
        move_file,
        read_file,
        write_file,
        run_command,
        open_app,
        web_search,
        browse_webpage,
        git_commit_and_push,
    )
}


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


def run_task(instruction: str, history: list, images: list = None) -> None:
    msg = {"role": "user", "content": instruction}
    if images:
        msg["images"] = images
    history.append(msg)

    for step in range(MAX_STEPS):
        # Dynamic Live Status Spinner
        with Status(f"[bold bright_magenta]GEMBOT[/bold bright_magenta] [bright_cyan]thinking with {MODEL}[/bright_cyan] [dim](Step {step+1}/{MAX_STEPS}) • Press [bold white]Ctrl+C[/bold white] to stop...[/dim]", spinner="dots", console=console) as status:
            try:
                # Request Ollama response
                resp = ollama.chat(model=MODEL, messages=history, tools=list(TOOLS.values()))
            except KeyboardInterrupt:
                console.print("\n[bold red]🛑 [gembot]: Execution STOPPED by user (Ctrl+C).[/bold red]\n")
                history.append({"role": "assistant", "content": "[Execution stopped by user]"})
                return
            except Exception as e:
                console.print(f"\n[bold red][!] Ollama Error:[/bold red] {e}\n[dim]Verify model '{MODEL}' in .env[/dim]")
                return

        msg = resp.message
        history.append(msg)

        # If model answered with text only (no tool calls) — retry up to 3 times
        if not msg.tool_calls:
            reply = msg.content.strip() if msg.content else ""

            # Check if this looks like a final summary (short, no file/command mentions)
            is_final = (
                step >= 1
                and len(reply) < 800
                and not any(kw in reply.lower() for kw in ["step 1", "step 2", "will create", "will write", "i will", "execution plan", "first,", "next,"])
            )

            if is_final or step == MAX_STEPS - 1:
                # Genuine final answer — display it
                if reply:
                    console.print()
                    console.print(Panel(Markdown(reply), title="[bold bright_magenta]GEMBOT Response[/bold bright_magenta]", border_style="bright_magenta"))
                    console.print()
                return
            else:
                # Model described instead of doing — kick it back into action
                if reply:
                    console.print()
                    console.print(Panel(Markdown(reply), title="[bold bright_magenta]GEMBOT Thinking...[/bold bright_magenta]", border_style="dim magenta"))
                console.print(f"  [bold yellow]⚡ RETRYING:[/bold yellow] [dim]Model planned but didn't act — pushing it to execute now (step {step+2}/{MAX_STEPS})...[/dim]")
                # Force the model to execute immediately
                history.append({
                    "role": "user",
                    "content": "NOW EXECUTE: Stop describing and immediately call a tool to start. Write the first file or run the first command RIGHT NOW. Do not output any more text — just call a tool."
                })
                continue

        # If model generated actions / code / file creations
        for call in msg.tool_calls:
            name = call.function.name
            args = dict(call.function.arguments)

            if name == "write_file":
                path = args.get("path", "").strip()
                content = args.get("content", "")
                if not path:
                    console.print(f"\n  [bold red]⚠ SKIPPED write_file:[/bold red] [dim]Model forgot to provide a filename. Skipping this call.[/dim]")
                    history.append({"role": "tool", "tool_name": name, "content": "Error: 'path' argument was empty. Please provide a valid file path."})
                    continue
                console.print(f"\n  [bold bright_green]🔨 BUILDING / CREATING FILE:[/bold bright_green] [bold white]{path}[/bold white]")
                code_lines = content.splitlines()
                preview = "\n".join(code_lines[:20])
                if len(code_lines) > 20:
                    preview += f"\n... [+{len(code_lines) - 20} more lines written to {path}]"
                console.print(Panel(preview, title=f"[dim cyan]Live Code Generator: {os.path.basename(path)}[/dim cyan]", border_style="cyan"))
            elif name in ("web_search", "browse_webpage"):
                query_or_url = list(args.values())[0] if args else ""
                console.print(f"\n  [bold bright_blue]🌐 LIVE WEB RESEARCH:[/bold bright_blue] [white]{name} -> {query_or_url}[/white]")
            elif name == "run_command":
                cmd = args.get("command", "")
                console.print(f"\n  [bold bright_yellow]⚡ EXECUTING COMMAND:[/bold bright_yellow] [bold yellow]{cmd}[/bold yellow]")
            elif name == "git_commit_and_push":
                msg_txt = args.get("commit_message", "")
                console.print(f"\n  [bold bright_magenta]🐙 GITHUB AUTOMATION:[/bold bright_magenta] [white]{msg_txt}[/white]")
            else:
                console.print(f"\n  [dim cyan]⚡ [tool] {name}({args})[/dim cyan]")

            # Run the tool with live status
            with Status(f"[dim]Running action {name}...[/dim]", spinner="dots", console=console):
                try:
                    fn = TOOLS.get(name)
                    result = fn(**args) if fn else f"Error: unknown tool '{name}'"
                except KeyboardInterrupt:
                    console.print(f"\n[bold red]🛑 [gembot]: Action '{name}' aborted by user.[/bold red]\n")
                    result = "User cancelled this action."
                    history.append({"role": "tool", "tool_name": name, "content": str(result)})
                    return
                except TypeError as e:
                    # Model called a tool with missing/wrong arguments — recover gracefully
                    result = f"Error: Tool '{name}' called with invalid arguments: {e}. Args received: {args}"
                    console.print(f"\n  [bold red]⚠ Tool call error (recovering):[/bold red] [dim]{result}[/dim]")

            # Print action execution result
            if name != "write_file":
                short_result = str(result)[:300] + ("..." if len(str(result)) > 300 else "")
                console.print(f"     [dim]↳ Result:[/dim] [bright_black]{short_result}[/bright_black]")

            history.append({"role": "tool", "tool_name": name, "content": str(result)})

    console.print("\n[dim][gembot] Completed maximum autonomous steps for this task.[/dim]\n")




def parse_multimodal_input(raw_input: str) -> tuple[str, list]:
    """Inspect input for paths to images, PDFs, or files and attach their contents."""
    images = []
    text_additions = []

    # Check for file path mentions or drag-and-drop paths
    # Matches patterns like C:\path\to\file.ext or "C:\path\to\file.ext"
    potential_paths = re.findall(r'(?:[A-Za-z]:\\[^\s"\'<>|]+(?:\.[A-Za-z0-9]+)?)|(?:"[A-Za-z]:\\[^"<>|]+")|(?:\'[A-Za-z]:\\[^\'<>|]+\')', raw_input)

    for p_str in potential_paths:
        res = extract_content_from_path(p_str)
        if res.get("type") == "image":
            images.append(res["data"])
            console.print(f"[dim green]  📎 Attached Image: {res['path']}[/dim green]")
        elif res.get("type") == "text":
            text_additions.append(f"\n[Attached File Contents of {res['path']}]:\n{res['content']}\n")
            console.print(f"[dim green]  📎 Read & Attached Document: {res['path']}[/dim green]")

    full_prompt = raw_input
    if text_additions:
        full_prompt = full_prompt + "\n" + "\n".join(text_additions)

    return full_prompt, images


def select_model_interactive() -> str:
    """List available Ollama models in a rich table and allow the user to select one."""
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
            chosen_name = choice  # Allow setting custom tag or model name

    save_active_model(chosen_name)
    console.print(f"[bold bright_green]✓ Active model switched to:[/bold bright_green] [bold white]{chosen_name}[/bold white]")
    console.print(f"[dim]Saved configuration to central agent config ({GLOBAL_ENV}).[/dim]\n")
    return chosen_name


def main() -> None:
    global MODEL
    ensure_ollama_running()
    print_banner()

    args = sys.argv[1:]
    if args:
        direct_task = " ".join(args).strip()
        console.print(f"[bold cyan]Task:[/bold cyan] {direct_task}")
        processed_prompt, imgs = parse_multimodal_input(direct_task)
        history = [{"role": "system", "content": SYSTEM}]
        run_task(processed_prompt, history, imgs)
        return

    history = [{"role": "system", "content": SYSTEM}]

    custom_style = Style.from_dict({
        'prompt': '#FFB703 bold',
    })

    while True:
        try:
            task = prompt([('class:prompt', '> Search sessions or type / to use commands\ngembot> ')], style=custom_style).strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[bright_magenta]Goodbye from GEMBOT![/bright_magenta]")
            break

        if not task:
            continue
        if task.lower() in {"exit", "quit", "q", "/exit"}:
            console.print("[bright_magenta]Exiting GEMBOT. Have a great day![/bright_magenta]")
            break
        if task.lower() in {"clear", "/clear"}:
            history = [{"role": "system", "content": SYSTEM}]
            console.clear()
            print_banner()
            console.print("[dim cyan]Conversation memory cleared.[/dim cyan]")
            continue
        if task.lower().startswith("/models") or task.lower().startswith("/model"):
            parts = task.split(maxsplit=1)
            if len(parts) > 1 and parts[1].strip():
                new_m = parts[1].strip()
                save_active_model(new_m)
                console.print(f"[bold bright_green]✓ Active model switched to:[/bold bright_green] [bold white]{new_m}[/bold white]\n")
            else:
                select_model_interactive()
            continue
        if task.lower() in {"/help", "help"}:
            console.print("\n[bold bright_magenta]GEMBOT Slash Commands & Shortcuts:[/bold bright_magenta]")
            console.print("  [bold yellow]/models[/bold yellow]          - List and interactively select your Ollama model")
            console.print("  [bold yellow]/models <name>[/bold yellow]   - Directly switch model (e.g. /models yi-coder:1.5b)")
            console.print("  [bold yellow]/clear[/bold yellow]           - Clear screen and conversation memory")
            console.print("  [bold yellow]/exit[/bold yellow] or [bold yellow]exit[/bold yellow]    - Exit the gembot CLI")
            console.print("  [bold yellow]Ctrl+C[/bold yellow]          - Halt any ongoing action immediately\n")
            continue

        processed_prompt, imgs = parse_multimodal_input(task)
        run_task(processed_prompt, history, imgs)


if __name__ == "__main__":
    sys.exit(main())
