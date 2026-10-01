# 🤖 gembot - Autonomous Windows Desktop, Web Browser & Coding Agent

**gembot** is a fully autonomous Windows AI agent powered by **Ollama** and Google's **`gemma4:e2b`** model. It operates completely offline-first, requiring no API keys or cloud subscriptions. It acts as an autonomous digital assistant capable of full-stack coding, headless web browsing, completing homework and research assignments without intervention, managing your Windows system, and syncing code to GitHub.

---

## 📌 Table of Contents
1. [🌟 Complete Capabilities Breakdown](#-complete-capabilities-breakdown)
   - [1. Autonomous Web Browsing & Live Research](#1-autonomous-web-browsing--live-research)
   - [2. Hands-Free Homework & Assignment Completion](#2-hands-free-homework--assignment-completion)
   - [3. Full-Stack Self-Coding & Verification](#3-full-stack-self-coding--verification)
   - [4. Git & GitHub Repository Automation](#4-git--github-repository-automation)
   - [5. Complete Windows Desktop & File Automation](#5-complete-windows-desktop--file-automation)
2. [🧠 Inner Loop Architecture](#-inner-loop-architecture)
3. [🛠️ Full Autonomous Tool Suite](#-full-autonomous-tool-suite)
4. [💻 How to Run (Commands & Modes)](#-how-to-run-commands--modes)
5. [📋 Setup & Construction History](#-setup--construction-history)
6. [📂 Project Directory Structure](#-project-directory-structure)

---

## 🌟 Complete Capabilities Breakdown

### 1. Autonomous Web Browsing & Live Research
- **Headless Chromium Engine**: Uses Playwright to render modern websites, bypass JavaScript-heavy pages, and extract real webpage contents.
- **Fast HTTP Fallback**: Uses requests and BeautifulSoup for lightning-fast reading of documentation and Wikipedia.
- **DuckDuckGo Search Integration**: Queries the live internet to pull search results, links, articles, and references on any subject.
- **No API Keys Required**: Bypasses the need for expensive third-party search engine APIs or web scraping services.

### 2. Hands-Free Homework & Assignment Completion
- **Zero-Intervention Execution**: Takes a prompt or assignment brief and independently plans, researches, writes, and saves the final result.
- **Comprehensive Report Generation**: Solves multi-part questions and outputs structured Markdown reports, summaries, or essays.
- **Math & Problem Solving**: Reads problem descriptions, writes Python scripts to calculate exact solutions, and writes formatted answers.
- **Direct Document Output**: Saves formatted `.md`, `.txt`, `.py`, or `.html` files directly onto your Desktop or designated project directories.

### 3. Full-Stack Self-Coding & Verification
- **Multi-Language Generation**: Writes clean, functional code across Python, JavaScript/Node, HTML/CSS, C++, Batch, and PowerShell.
- **Project Scaffolding**: Automatically creates complex folder hierarchies, config files, unit tests, and documentation.
- **Autonomous Testing**: Uses `run_command` to test scripts (e.g., `python script.py`), captures stdout/stderr, and fixes errors in subsequent reasoning steps.
- **Code Inspection & Refactoring**: Reads existing codebases with `read_file`, identifies bugs, and writes corrected versions.

### 4. Git & GitHub Repository Automation
- **Automatic Repo Initialization**: Checks for Git repositories and initializes them (`git init`) if needed.
- **Remote Linking**: Adds or updates GitHub remote origin URLs automatically.
- **Automated Staging & Commit**: Stages modified files (`git add -A`) and crafts descriptive commit messages based on work done.
- **Branch Pushing**: Switches to target branches (`git branch -M main`) and pushes directly to GitHub (`git push -u origin main`).

### 5. Complete Windows Desktop & File Automation
- **Application Launcher**: Launches Windows applications by name (e.g., `notepad`, `calc`, `chrome`, `code`) or opens documents and web URLs.
- **File System Management**: Traverses directories, inspects folder sizes, moves, copies, and renames files across your computer.
- **Autonomous Background Server**: Automatically boots the local Ollama server if it isn't running whenever you execute `gembot`.

---

## 🧠 Inner Loop Architecture

`gembot` operates on an autonomous agentic loop with 9 integrated tools:

```
                          User Prompt / Assignment
                                     │
                                     ▼
                    ┌─────────────────────────────────┐
                    │     System Prompt + Context     │
                    └────────────────┬────────────────┘
                                     │
                                     ▼
                    ┌─────────────────────────────────┐
                    │    Ollama Engine (gemma4:e2b)   │
                    └────────────────┬────────────────┘
                                     │
                                     ├──────────────────────────────┐
                                     │                              │
                          [Requires Actions]                  [Goal Met]
                                     │                              │
                                     ▼                              ▼
                 ┌───────────────────────────────────────┐   Print Summary &
                 │        Autonomous Action Dispatch     │   Return to Prompt
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
| **Browsing & Search** | `web_search(query, max_results)` | Searches DuckDuckGo for live answers, papers, and assignment guidance. |
| | `browse_webpage(url)` | Headless Chromium browser navigates to URL, parses DOM, and extracts readable text. |
| **Coding & Files** | `write_file(path, content)` | Writes code, answers, documents, or reports to specified paths. |
| | `read_file(path)` | Reads source code, assignment questions, PDFs/text files, or configs. |
| | `list_files(path)` | Inspects directories and reveals folder structures. |
| | `move_file(src, dst)` | Organizes files, moves assets, and builds output folders. |
| **System & Shell** | `run_command(command)` | Autonomously runs compilers, interpreters (`python`), tests, and packages. |
| | `open_app(name_or_path)` | Opens software (e.g. VS Code, Notepad, Chrome) or local files. |
| **GitHub Automation** | `git_commit_and_push(...)` | Stages all files, creates commits, and pushes directly to remote GitHub repositories. |

---

## 💻 How to Run (Commands & Modes)

You can run `gembot` from **any** terminal in Windows:

### 1. Interactive Shell Mode
```cmd
gembot
```

Inside the interactive shell, you have dedicated slash commands:
- `/models` — View all local Ollama models in a formatted table and choose/switch the active model interactively.
- `/models <name>` — Directly switch the active model (e.g. `/models yi-coder:1.5b`).
- `/clear` — Clear the screen and reset conversation memory.
- `/help` — Display available commands and shortcuts.
- `exit` or `/exit` — Quit GEMBOT.

### 2. Direct Autonomous Task Execution (Examples)

#### 📝 Finish an Assignment:
```cmd
gembot research the key differences between SQL and NoSQL databases, search the web, and create a comprehensive assignment report on my Desktop called database_assignment.md
```

#### 💻 Self-Coding & Verification:
```cmd
gembot build a python script that fetches the top 5 trending GitHub repositories, save it to Desktop\trending.py, and run it
```

#### 🐙 Build Code & Push to GitHub:
```cmd
gembot create a full Python CLI password generator with unit tests in C:\Users\Subhash\Desktop\passgen, create README, commit all files with message "initial commit", and push to main
```

#### 🖥️ Windows Automation:
```cmd
gembot open chrome to https://github.com and launch notepad
```

---

## 📋 Setup & Construction History

Commands used to build and configure this agent:

```cmd
:: 1. Core Ollama runtime
winget install -e --id Ollama.Ollama --accept-source-agreements --accept-package-agreements
ollama pull gemma4:e2b

:: 2. Python environment & Dependencies
python -m venv %USERPROFILE%\agent\venv
%USERPROFILE%\agent\venv\Scripts\pip install ollama playwright gitpython duckduckgo_search beautifulsoup4 requests

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
│   ├── agent.py                            # Agent loop with browsing, coding & git
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
