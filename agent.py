"""gembot - Autonomous Windows Desktop, Browser, and Coding AI Agent.
Powered by Ollama + gemma4:e2b with autonomous tool calling, web browsing, 
assignment completion, self-coding, and Git/GitHub automation.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request

# Ensure UTF-8 output encoding for Windows command line compatibility
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    from dotenv import load_dotenv
    # Look for .env in current directory or user agent folder
    load_dotenv()
    load_dotenv(os.path.expandvars(r"%USERPROFILE%\agent\.env"))
except ImportError:
    pass

import ollama

MODEL = os.getenv("MODEL", "gemma4:e2b")
MAX_STEPS = int(os.getenv("MAX_STEPS", "16"))
MAX_OUTPUT = int(os.getenv("MAX_OUTPUT", "4000"))

SYSTEM = (
    "You are 'gembot', an autonomous Windows AI assistant capable of full software engineering, "
    "automated web browsing, solving school/work assignments, file management, and GitHub automation.\n\n"
    "Your Available Capabilities:\n"
    "1. Autonomous execution: Complete user instructions end-to-end.\n"
    "2. Web Browsing & Research: Use web_search to find information and browse_webpage to read pages, "
    "articles, study materials, questions, or documentation.\n"
    "3. Assignments & Problem Solving: Read assignments/specs, perform research, write comprehensive "
    "solutions, code them, verify, and output reports or complete project directories.\n"
    "4. Self-Coding & Creation: Write robust, bug-free scripts and programs using write_file.\n"
    "5. Git & GitHub: Use git_commit_and_push to commit changes and push directly to GitHub repositories.\n"
    "6. Windows Automation: Open apps, read/write/move files, inspect directories, and run shell commands.\n\n"
    "Rules: Use full absolute paths when managing files. When finished, provide a concise summary of what was accomplished."
)


def _p(path: str) -> str:
    return os.path.abspath(os.path.expanduser(os.path.expandvars(path)))


def _cut(text: str) -> str:
    return text if len(text) <= MAX_OUTPUT else text[:MAX_OUTPUT] + "\n...[truncated]"


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
    print(f"\n  [gembot cmd]: {command}")
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
        # First attempt: Fast request with BeautifulSoup
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

        # Initialize repo if not already
        if not os.path.exists(os.path.join(path, ".git")):
            r = subprocess.run("git init", cwd=path, shell=True, capture_output=True, text=True)
            if r.returncode != 0:
                return f"Git init failed: {r.stderr}"

        if remote_url:
            subprocess.run(f"git remote remove origin", cwd=path, shell=True, capture_output=True)
            subprocess.run(f"git remote add origin {remote_url}", cwd=path, shell=True, capture_output=True)

        # Stage all files
        subprocess.run("git add -A", cwd=path, shell=True, check=True)

        # Commit
        c = subprocess.run(f'git commit -m "{commit_message}"', cwd=path, shell=True, capture_output=True, text=True)

        # Check / set branch
        subprocess.run(f"git branch -M {branch}", cwd=path, shell=True, capture_output=True)

        # Push to remote
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

    print("[gembot] Starting Ollama server in background...")
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
        print(f"[gembot] Warning: Could not auto-launch Ollama: {e}")
    return False


def run_task(instruction: str, history: list) -> None:
    history.append({"role": "user", "content": instruction})
    print(f"  [gembot thinking using {MODEL} (please wait, loading weights)...]")

    for step in range(MAX_STEPS):
        try:
            resp = ollama.chat(model=MODEL, messages=history, tools=list(TOOLS.values()))
        except Exception as e:
            print(f"\n[!] Ollama Error: {e}\nEnsure model '{MODEL}' is available.")
            return

        msg = resp.message
        history.append(msg)


        if not msg.tool_calls:
            reply = msg.content.strip() if msg.content else "Task completed."
            print(f"\n[gembot]: {reply}\n")
            return

        for call in msg.tool_calls:
            name = call.function.name
            args = dict(call.function.arguments)
            if name == "write_file":
                path = args.get("path", "")
                content = args.get("content", "")
                print(f"\n  -> [action] Saving code/file to: {path}")
                print("  " + "-" * 50)
                for line in content.splitlines()[:25]:
                    print(f"     {line}")
                if len(content.splitlines()) > 25:
                    print("     ... [remaining code written to file]")
                print("  " + "-" * 50 + "\n")
            elif name in ("web_search", "browse_webpage", "run_command", "open_app"):
                arg_val = list(args.values())[0] if args else ""
                print(f"\n  -> [action] {name}: {arg_val}")
            else:
                print(f"\n  -> [action] {name}({args})")

            fn = TOOLS.get(name)
            result = fn(**args) if fn else f"Error: unknown tool '{name}'"
            print(f"     Result: {result}")
            history.append({"role": "tool", "tool_name": name, "content": str(result)})

    print("\n[gembot] Completed maximum autonomous steps for this task.\n")



def main() -> None:
    ensure_ollama_running()

    print("=" * 65)
    print(" GEMBOT - Autonomous AI Coding, Web Browsing & Automation Agent")
    print(f" Model: {MODEL} | Web & Browser | GitHub | Autonomous")
    print(" Commands: 'exit' to quit | 'clear' to reset memory")
    print("=" * 65)

    args = sys.argv[1:]
    if args:
        direct_task = " ".join(args).strip()
        print(f"\nTask: {direct_task}")
        history = [{"role": "system", "content": SYSTEM}]
        run_task(direct_task, history)
        return

    history = [{"role": "system", "content": SYSTEM}]
    while True:
        try:
            task = input("gembot> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not task:
            continue
        if task.lower() in {"exit", "quit", "q"}:
            print("Exiting gembot. Have a great day!")
            break
        if task.lower() == "clear":
            history = [{"role": "system", "content": SYSTEM}]
            print("Conversation history cleared.")
            continue

        run_task(task, history)


if __name__ == "__main__":
    sys.exit(main())
