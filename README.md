# 🤖 gembot - Autonomous Windows Desktop, Web Browser & Coding Agent

<p align="center">
  <img src="docs/assets/hero.jpg" alt="GEMBOT - Autonomous Windows AI Agent" width="100%" />
</p>

**gembot** is an enterprise-grade, offline-first autonomous Windows AI agent powered by **Ollama** and modern open models (**`qwen2.5-coder:7b`**, **`qwen2.5-coder:3b`**, **`gemma4:e2b`**). It operates completely offline, requiring zero paid APIs or subscriptions. It features a modular multi-tool architecture, precision patch-editing, safety gates, automatic file backups & undo, session persistence, long-term memory, system diagnostics, and extensible plugins.

---

## 📌 Table of Contents
1. [🌟 Complete Capabilities Breakdown](#-complete-capabilities-breakdown)
   - [1. Safety & Reliability (Confirmation Gate, Blocklist, Undo)](#1-safety--reliability)
   - [2. High-Precision Coding Tools & Test Runner](#2-high-precision-coding-tools--test-runner)
   - [3. Multimodal Clipboard & Screenshot Inspection (`/paste`)](#3-multimodal-clipboard--screenshot-inspection-paste)
   - [4. Planning, Memory & Session Management](#4-planning-memory--session-management)
   - [5. Windows Desktop & System Control](#5-windows-desktop--system-control)
   - [6. Document Automation (.docx & .xlsx)](#6-document-automation-docx--xlsx)
   - [7. Extensible Plugin System](#7-extensible-plugin-system)
2. [🧠 Modular Architecture](#-modular-architecture)
3. [🛠️ Full Autonomous Tool Suite (30 Registered Tools)](#-full-autonomous-tool-suite-30-registered-tools)
4. [🤖 Supported & Recommended Models](#-supported--recommended-models)
5. [💻 How to Run & Slash Commands](#-how-to-run--slash-commands)
6. [📋 Setup & Deployment](#-setup--deployment)
7. [📂 Project Directory Structure](#-project-directory-structure)

---

## 🌟 Complete Capabilities Breakdown

### 1. Safety & Reliability
- **Confirmation Gate (`/auto on|off`)**: Interactive verification before dangerous commands (`format`, `rmdir /s /q`, `shutdown`, `git push --force`) or file overwrite operations. Can be bypassed using `/auto on`.
- **Command Blocklist & Timeout**: `run_command` enforces a configurable timeout (default 60s) and blocks dangerous commands.
- **Timestamped File Backups & Undo (`/undo`)**: Automatically creates snapshots in `.gembot/backups/` before any file is overwritten or moved. Type `/undo` to instantly restore the last modification.
- **Session Audit Logging**: Complete log of every tool execution, parameters, and results stored in `.gembot/logs/session-<date>.log`.
- **Central Configuration**: Managed centrally in `%USERPROFILE%\agent\config.json`.

### 2. High-Precision Coding Tools & Test Runner
- **Patch Editing (`edit_file`)**: Modifies files by replacing exact string snippets rather than rewriting thousands of lines, drastically improving speed and reliability on small 3B–7B models.
- **Codebase Grep Search (`search_files`)**: Recursive text & glob search across directories with smart exclusions (`.git`, `node_modules`, `venv`).
- **File & Directory Management**: Native `delete_file`, `copy_file`, `make_dir`, and `file_info` (lines of code, size, modification).
- **Automated Test Detection (`run_tests`)**: Auto-detects and runs `pytest` or `npm test` across the project, returning formatted results.
- **Custom Project Context (`GEMBOT.md`)**: Automatically loads rules, project stack, and conventions from `GEMBOT.md` in the working directory into the system prompt.

### 3. Multimodal Clipboard & Screenshot Inspection (`/paste`)
- **Direct Clipboard Image Grab**: Press `Win + Shift + S` or copy any image, then type `/paste` into the terminal. Gembot extracts the image directly from the Windows clipboard and attaches it for visual bug analysis.
- **Drag-and-Drop & Quoted Path Parsing**: Seamlessly paste file paths directly into the terminal with quotes, unquoted, or PowerShell drag-and-drop syntax (`& 'C:\path\to\file'`).
- **Document & PDF Parsing**: Automatically reads and extracts contents from `.pdf`, `.log`, `.txt`, `.py`, `.js`, and config files attached or mentioned in your prompts.

### 4. Planning, Memory & Session Management
- **Checklist Planning Mode (`/plan <task>`)**: Instructs the agent to break complex assignments into numbered steps, display the checklist, and execute immediately.
- **Session Persistence (`/save <name>`, `/load <name>`)**: Save conversations to `.gembot/sessions/` and restore them at any time.
- **Context Summarization**: Automatically condenses older conversation turns when context approaches model limits, preventing memory exhaustion.
- **Long-Term Memory (`remember_fact`, `recall_fact`)**: Saves user preferences and project configurations persistently in `.gembot/memory.json`.

### 5. Windows Desktop & System Control
- **Screenshot Tool (`take_screenshot`)**: Captures screen displays and saves to `.gembot/screenshots/`.
- **Clipboard Management (`clipboard_read`, `clipboard_write`)**: Reads and copies text directly to/from the Windows clipboard.
- **Hardware & Resource Monitor (`system_info`)**: Reports live CPU, RAM, Disk, Battery, and OS specifications via `psutil`.
- **Process Inspection & Control (`list_processes`, `kill_process`)**: Lists top memory-consuming processes and terminates tasks by PID or name.
- **Network Tools (`download_file`, `http_request`)**: Directly downloads files and issues REST API calls.

### 6. Document Automation (.docx & .xlsx)
- **Word Document Generator (`create_docx`, `read_docx`)**: Formats assignments and reports with titles, headings, and bulleted lists.
- **Excel Spreadsheet Generator (`create_excel`, `read_excel`)**: Generates and inspects `.xlsx` spreadsheets from comma- or pipe-separated tabular data.

### 7. Extensible Plugin System
- **Dynamic Plugin Directory**: Drop custom Python files into `%USERPROFILE%\agent\plugins\`. Gembot auto-discovers and registers exposed tools at startup.

---

## 🧠 Modular Architecture

Gembot's architecture is separated into a modular core package (`gembot_core`) and the reactive interactive shell (`agent.py`):

```
                        User Prompt / /paste / Attachment
                                      │
                                      ▼
                    ┌─────────────────────────────────┐
                    │     System Prompt + Context     │
                    │   (+ GEMBOT.md Project Rules)   │
                    └────────────────┬────────────────┘
                                      │
                                      ▼
                    ┌─────────────────────────────────┐
                    │    Ollama Engine (Local LLM)    │
                    │  (qwen2.5-coder:7b / 3b / etc.) │
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
                  │ • Safety Gate & Confirmation (/auto)  │
                  │ • Snapshot Backup (.gembot/backups)   │
                  │ • Fallback JSON Tool Extraction       │
                  │ • Missing Path Auto-Inference         │
                  │ • Dispatch to 30 Registered Tools     │
                  └───────────────────┬───────────────────┘
                                      │
                                      ▼
                  Append Action Output to Context History
                  (Auto-summarizes when nearing limit)
                                      │
                           (Loop up to 16 cycles)
```

---

## 🛠️ Full Autonomous Tool Suite (30 Registered Tools)

| Category | Tool | Description |
|---|---|---|
| **Files & Editing** | `write_file(path, content)` | Writes/overwrites files with auto-backup and JSON auto-sanitization. |
| | `edit_file(path, old_str, new_str)` | Precision search-and-replace patch edit on existing files. |
| | `read_file(path)` | Reads source code, questions, logs, or configs. |
| | `list_files(path)` | Inspects directories and reveals folder structures. |
| | `move_file(src, dst)` | Moves/renames files with overwrite confirmation and backup. |
| | `copy_file(src, dst)` | Copies files or directories. |
| | `delete_file(path)` | Deletes files or directories. |
| | `make_dir(path)` | Creates directory structures recursively. |
| | `file_info(path)` | Retrieves size, line counts, and metadata. |
| **Code & Tests** | `search_files(pattern, path, glob)` | Grep-style recursive keyword search across codebases. |
| | `run_tests(cwd)` | Auto-detects and executes pytest or npm test. |
| | `git_commit_and_push(...)` | Stages all changes, creates commits, and pushes to GitHub. |
| **System & Shell** | `run_command(command)` | Runs shell commands with safety checks, blocklists, and timeout. |
| | `open_app(name_or_path)` | Launches desktop applications, local files, or URLs. |
| | `system_info()` | Reports CPU, RAM, Disk, and Battery diagnostics. |
| | `list_processes(limit)` | Lists processes sorted by memory consumption. |
| | `kill_process(pid_or_name)` | Terminates a process by PID or name. |
| | `take_screenshot(save_path)` | Captures the primary display screen. |
| | `clipboard_read()` | Reads text from the Windows clipboard. |
| | `clipboard_write(text)` | Copies text directly to the Windows clipboard. |
| **Web & Network** | `web_search(query, max_results)` | Searches DuckDuckGo for live answers and documentation. |
| | `browse_webpage(url)` | Headless Chromium / HTTP parser for web page content. |
| | `download_file(url, path)` | Downloads any file directly over HTTP/HTTPS. |
| | `http_request(method, url, ...)` | Performs custom REST API requests. |
| **Documents** | `create_docx(path, title, paragraphs)` | Generates formatted Microsoft Word (.docx) documents. |
| | `read_docx(path)` | Reads text from Word documents. |
| | `create_excel(path, sheet, rows)` | Generates Microsoft Excel (.xlsx) spreadsheets. |
| | `read_excel(path)` | Reads rows and columns from Excel spreadsheets. |
| **Memory** | `remember_fact(key, value)` | Stores persistent facts and user preferences. |
| | `recall_fact(key)` | Retrieves saved facts from `.gembot/memory.json`. |

---

## 🤖 Supported & Recommended Models

Switch models anytime in the terminal with `/models`:

| Model | Command | Best For |
|---|---|---|
| **Qwen 2.5 Coder 7B** *(Recommended)* | `ollama pull qwen2.5-coder:7b` | **Best overall coding & tool calling** under 8B. Clean code and dependable tool usage. |
| **Qwen 2.5 Coder 3B** | `ollama pull qwen2.5-coder:3b` | Lightweight & fast. Handled by Gembot's auto-parsed JSON fallback. |
| **Gemma 4:E2B** | `ollama pull gemma4:e2b` | Multi-step desktop tool automation and general reasoning. |
| **Llama 3.1 8B / 3.2 3B** | `ollama pull llama3.1:8b` | Strong instruction following and tool usage. |

---

## 💻 How to Run & Slash Commands

Launch from any Windows terminal:
```cmd
gembot
```

### Slash Commands:
- `/paste` — Directly inspect screenshot/image or copied file from clipboard.
- `/undo` — Restore the last modified file from `.gembot/backups/`.
- `/auto on|off` — Toggle confirmation prompts for dangerous actions.
- `/plan <task>` — Force step-by-step checklist planning mode.
- `/save <name>` — Save current conversation session to `.gembot/sessions/`.
- `/load <name>` — Restore a previous conversation session.
- `/tools` — List all 30 available autonomous tools.
- `/models` — Interactively select or switch Ollama models.
- `/models <name>` — Directly switch model (e.g. `/models qwen2.5-coder:7b`).
- `/clear` — Clear screen and conversation memory.
- `/help` — Display command guide and shortcuts.
- `Ctrl+C` — Instantly abort any running tool or model generation.

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
Copy-Item -Path "c:\Users\Subhash\Desktop\gembot\agent.py" -Destination "%USERPROFILE%\agent\agent.py" -Force
Copy-Item -Path "c:\Users\Subhash\Desktop\gembot\gembot_core" -Destination "%USERPROFILE%\agent\gembot_core" -Recurse -Force
copy c:\Users\Subhash\Desktop\gembot\gembot.cmd %LOCALAPPDATA%\Microsoft\WindowsApps\gembot.cmd
```

---

## 📂 Project Directory Structure

```text
C:\Users\Subhash\
│
├── Desktop\gembot\                         <-- Source Repository
│   ├── agent.py                            # Reactive CLI loop & banner
│   ├── gembot_core/                        # Modular Core Architecture
│   │   ├── config.py                       # Central config manager
│   │   ├── safety.py                       # Safety gate, blocklist, backups, undo
│   │   ├── coding_tools.py                 # Precision patch edit, search, tests
│   │   ├── memory.py                       # Long-term memory, sessions, summarizer
│   │   ├── system_tools.py                 # System info, processes, screenshot
│   │   ├── doc_tools.py                    # Word (.docx) & Excel (.xlsx) tools
│   │   └── plugins.py                      # Dynamic plugin loader
│   ├── tests/                              # Pytest test suite
│   ├── gembot.cmd                          # Fast launcher
│   ├── requirements.txt                    # Python library specifications
│   └── README.md                           # Documentation & user guide
│
├── agent\                                  <-- Global Deployment Directory
│   ├── agent.py                            # Production script executed by CLI
│   ├── gembot_core\                        # Production core package
│   ├── plugins\                            # User drop-in plugin folder
│   ├── config.json                         # Central agent configuration
│   └── venv\                               # Isolated virtual environment
│
├── AppData\Local\Microsoft\WindowsApps\
│   └── gembot.cmd                          # Globally accessible command in PATH
│
└── AppData\Local\ms-playwright\
    └── chromium-1243\                      # Headless Chromium for web navigation
```
