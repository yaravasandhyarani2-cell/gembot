# 🤖 gembot - Autonomous Windows Desktop, Web Browser & Coding Agent

<p align="center">
  <img src="docs/assets/hero.jpg" alt="GEMBOT - Autonomous Windows AI Agent" width="100%" />
</p>

**gembot** is a fully autonomous Windows AI agent powered by **Ollama** and modern local models like **`qwen2.5-coder:7b`**, **`qwen2.5-coder:3b`**, Google's **`gemma4:e2b`**, or ultra-lightweight coding models. It operates completely offline-first, requiring no API keys or cloud subscriptions. It acts as an autonomous digital assistant capable of full-stack coding, headless web browsing, multimodal clipboard and screenshot inspection, automated error recovery, hands-free assignments, managing your Windows system, and syncing code to GitHub.

---

## 📌 Table of Contents
1. [🌟 Complete Capabilities Breakdown](#-complete-capabilities-breakdown)
   - [1. Multimodal Clipboard & Screenshot Inspection (`/paste`)](#1-multimodal-clipboard--screenshot-inspection-paste)
   - [2. Intelligent Tool Calling & Self-Healing Execution](#2-intelligent-tool-calling--self-healing-execution)
   - [3. Full-Stack Self-Coding & Verification](#3-full-stack-self-coding--verification)
   - [4. Autonomous Web Browsing & Live Research](#4-autonomous-web-browsing--live-research)
   - [5. Git & GitHub Repository Automation](#5-git--github-repository-automation)
   - [6. Windows Desktop & File Automation](#6-windows-desktop--file-automation)
2. [🧠 Inner Loop Architecture](#-inner-loop-architecture)
3. [🛠️ Full Autonomous Tool Suite](#-full-autonomous-tool-suite)
4. [🤖 Supported & Recommended Models](#-supported--recommended-models)
5. [💻 How to Run (Commands & Modes)](#-how-to-run-commands--modes)
6. [📋 Setup & Deployment](#-setup--deployment)
7. [📂 Project Directory Structure](#-project-directory-structure)

---

## 🌟 Complete Capabilities Breakdown

### 1. Multimodal Clipboard & Screenshot Inspection (`/paste`)
- **Direct Clipboard Image Grab**: Press `Win + Shift + S` or copy any image, then type `/paste` into the gembot terminal. Gembot extracts the image directly from the Windows clipboard using PIL and attaches it for visual bug analysis and code fixes.
- **Drag-and-Drop & Quoted Path Parsing**: Seamlessly paste file paths directly into the terminal with quotes, unquoted, or PowerShell drag-and-drop syntax (`& 'C:\path\to\file'`).
- **Document & PDF Parsing**: Automatically reads and extracts contents from `.pdf`, `.log`, `.txt`, `.py`, `.js`, and config files attached or mentioned in your prompts.
- **Windows Explorer File Copy**: Copy a file in Windows Explorer (`Ctrl + C`) and run `/paste` in gembot to load and analyze it immediately.

### 2. Intelligent Tool Calling & Self-Healing Execution
- **Raw JSON Tool Fallback**: Smaller models (like `qwen2.5-coder:3b` or `1.5b`) sometimes emit tool calls formatted as raw JSON text instead of native function calls. Gembot's auto-parser catches raw JSON calls (`{"name": "write_file", ...}`), parses arguments, and executes the actions automatically.
- **Auto-Inferred Paths**: If a model generates code content but leaves the `path` argument empty, Gembot analyzes language imports, code signatures, and conversation history to auto-infer the correct filename and save the file without failing.
- **Active Retries & Recovery**: Automatically detects when a model plans or talks without acting, pushing it with structured feedback to trigger immediate execution.

### 3. Full-Stack Self-Coding & Verification
- **Multi-Language Generation**: Writes clean, functional code across Python, TypeScript/JavaScript, React/Next.js, HTML/CSS, C++, Batch, and PowerShell.
- **Project Scaffolding**: Automatically creates complex folder hierarchies, config files, unit tests, and documentation.
- **Autonomous Testing**: Uses `run_command` to test scripts (`npm run build`, `python script.py`), captures stdout/stderr, and fixes errors in subsequent reasoning steps.
- **Code Inspection & Refactoring**: Reads existing codebases with `read_file`, identifies bugs, and writes corrected versions.

### 4. Autonomous Web Browsing & Live Research
- **Headless Chromium Engine**: Uses Playwright to render modern websites, bypass JavaScript-heavy pages, and extract real webpage contents.
- **Fast HTTP Fallback**: Uses requests and BeautifulSoup for lightning-fast reading of documentation and Wikipedia.
- **DuckDuckGo Search Integration**: Queries the live internet to pull search results, links, articles, and references on any subject.
- **No API Keys Required**: Bypasses the need for expensive third-party search engine APIs or web scraping services.

### 5. Git & GitHub Repository Automation
- **Automatic Repo Initialization**: Checks for Git repositories and initializes them (`git init`) if needed.
- **Remote Linking**: Adds or updates GitHub remote origin URLs automatically.
- **Automated Staging & Commit**: Stages modified files (`git add -A`) and crafts descriptive commit messages based on work done.
- **Branch Pushing**: Switches to target branches (`git branch -M main`) and pushes directly to GitHub (`git push -u origin main`).

### 6. Complete Windows Desktop & File Automation
- **Application Launcher**: Launches Windows applications by name (e.g., `notepad`, `calc`, `chrome`, `code`) or opens documents and web URLs.
- **File System Management**: Traverses directories, inspects folder sizes, moves, copies, and renames files across your computer.
- **Autonomous Background Server**: Automatically boots the local Ollama server if it isn't running whenever you execute `gembot`.

---

## 🧠 Inner Loop Architecture

`gembot` operates on an autonomous agentic loop with self-healing tool execution:

```
                          User Prompt / /paste / Attachment
                                      │
                                      ▼
                    ┌─────────────────────────────────┐
                    │     System Prompt + Context     │
                    └────────────────┬────────────────┘
                                      │
                                      ▼
                    ┌─────────────────────────────────┐
                    │    Ollama Engine (Local LLM)    │
                    └────────────────┬────────────────┘
                                      │
                                      ├──────────────────────────────┐
                                      │                              │
                          [Tool Calls / Raw JSON]             [Goal Met]
                                      │                              │
                                      ▼                              ▼
                  ┌───────────────────────────────────────┐   Print Summary &
                  │      Autonomous Self-Healing Loop     │   Return to Prompt
                  │                                       │
                  │ • Fallback JSON Tool Extraction       │
                  │ • Missing Path Auto-Inference         │
                  │ • Action Dispatch (9 Tools)           │
                  │                                       │
                  │ 🌐 browse_webpage  🔍 web_search      │
                  │ 💾 write_file      📖 read_file       │
                  │ 📁 list_files      🔄 move_file       │
                  │ ⚡ run_command     🚀 open_app        │
                  │ 🐙 git_commit_and_push                │
                  └───────────────────┬───────────────────┘
                                      │
                                      ▼
                  Append Action Output to Context History
                                      │
                           (Loop up to 16 cycles)
```

---

## 🛠️ Full Autonomous Tool Suite

| Category | Tool | Description |
|---|---|---|
| **Coding & Files** | `write_file(path, content)` | Writes code, configs, documents, or reports to specified paths with auto-inferred paths. |
| | `read_file(path)` | Reads source code, questions, PDFs, log files, or configs. |
| | `list_files(path)` | Inspects directories and reveals folder structures. |
| | `move_file(src, dst)` | Organizes files, moves assets, and builds output folders. |
| **Browsing & Search** | `web_search(query, max_results)` | Searches DuckDuckGo for live answers, documentation, and research. |
| | `browse_webpage(url)` | Headless Chromium browser navigates to URL, parses DOM, and extracts readable text. |
| **System & Shell** | `run_command(command)` | Autonomously runs compilers, interpreters (`python`), tests (`npm run build`), and shell scripts. |
| | `open_app(name_or_path)` | Opens software (e.g. VS Code, Notepad, Chrome) or local files. |
| **GitHub Automation** | `git_commit_and_push(...)` | Stages all files, creates commits, and pushes directly to remote GitHub repositories. |

---

## 🤖 Supported & Recommended Models

Switch models anytime in the terminal with `/models`:

| Model | Command | Best For |
|---|---|---|
| **Qwen 2.5 Coder 7B** *(Recommended)* | `ollama pull qwen2.5-coder:7b` | **Best overall coding & tool calling** under 8B. Outstanding code quality and zero errors. |
| **Qwen 2.5 Coder 3B** | `ollama pull qwen2.5-coder:3b` | Lightweight & fast. Handled by Gembot's auto-parsed JSON fallback. |
| **Gemma 4:E2B** | `ollama pull gemma4:e2b` | Multi-step desktop tool automation and general reasoning. |
| **Llama 3.1 8B / 3.2 3B** | `ollama pull llama3.1:8b` | Strong instruction following and tool usage. |

---

## 💻 How to Run (Commands & Modes)

You can run `gembot` from **any** terminal in Windows:

### 1. Interactive Shell Mode
```cmd
gembot
```

Inside the interactive shell:
- `/paste` — Grab an image/screenshot or copied file directly from your Windows clipboard.
- `/models` — View all local Ollama models in a formatted table and choose/switch the active model interactively.
- `/models <name>` — Directly switch active model (e.g. `/models qwen2.5-coder:7b`).
- `/clear` — Clear the screen and reset conversation memory.
- `/help` — Display available commands and shortcuts.
- `exit` or `/exit` — Quit GEMBOT.

### 2. Multimodal & Screenshot Troubleshooting
```cmd
:: 1. Press Win + Shift + S to screenshot an error on your screen
:: 2. In Gembot terminal, simply type:
gembot> /paste look at this error and fix it in my project
```

### 3. Direct Autonomous Task Execution (Examples)

#### 💻 Self-Coding & Verification:
```cmd
gembot build a python script that fetches the top 5 trending GitHub repositories, save it to Desktop\trending.py, and run it
```

#### 🐙 Build Code & Push to GitHub:
```cmd
gembot create a full Next.js portfolio in C:\Users\Subhash\Desktop\portfolio, add README, commit all files, and push to main
```

#### 📝 Research & Assignment Completion:
```cmd
gembot research the key differences between SQL and NoSQL databases, search the web, and create a comprehensive report on my Desktop called database_assignment.md
```

---

## 📋 Setup & Deployment

Commands used to configure and update Gembot globally:

```cmd
:: 1. Core Ollama runtime
winget install -e --id Ollama.Ollama --accept-source-agreements --accept-package-agreements
ollama pull qwen2.5-coder:7b

:: 2. Python environment & Dependencies
python -m venv %USERPROFILE%\agent\venv
%USERPROFILE%\agent\venv\Scripts\pip install -r requirements.txt

:: 3. Headless Browser Engine
%USERPROFILE%\agent\venv\Scripts\playwright install chromium

:: 4. Deploy Agent Code & Global PATH command
copy c:\Users\Subhash\Desktop\gembot\agent.py %USERPROFILE%\agent\agent.py
copy c:\Users\Subhash\Desktop\gembot\gembot.cmd %LOCALAPPDATA%\Microsoft\WindowsApps\gembot.cmd
```

---

## 📂 Project Directory Structure

```text
C:\Users\Subhash\
│
├── Desktop\gembot\                         <-- Source Repository
│   ├── agent.py                            # Agent loop with multimodal paste, JSON fallback, coding & git
│   ├── gembot.cmd                          # Fast launcher
│   ├── requirements.txt                    # Python library specifications
│   └── README.md                           # Documentation & user guide
│
├── agent\                                  <-- Deployment Directory
│   ├── agent.py                            # Production script executed by CLI
│   ├── requirements.txt
│   └── venv\                               # Isolated virtual environment
│
├── AppData\Local\Microsoft\WindowsApps\
│   └── gembot.cmd                          # Globally accessible command in PATH
│
└── AppData\Local\ms-playwright\
    └── chromium-1243\                      # Headless Chromium for web navigation
```
