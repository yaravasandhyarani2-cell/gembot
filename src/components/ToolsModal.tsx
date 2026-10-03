import React, { useState } from 'react';
import { X, Wrench, Search, Code, FileText, Cpu, Globe, Database, Terminal } from 'lucide-react';

interface ToolsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const TOOLS_LIST = [
  // Files & Editing
  { category: 'Files & Editing', name: 'write_file', args: 'path, content', desc: 'Writes/overwrites files with auto-backup and JSON auto-sanitization.' },
  { category: 'Files & Editing', name: 'edit_file', args: 'path, old_str, new_str', desc: 'Precision search-and-replace patch edit on existing files.' },
  { category: 'Files & Editing', name: 'read_file', args: 'path', desc: 'Reads source code, questions, logs, or configs.' },
  { category: 'Files & Editing', name: 'list_files', args: 'path', desc: 'Inspects directories and reveals folder structures.' },
  { category: 'Files & Editing', name: 'move_file', args: 'source, destination', desc: 'Moves/renames files with overwrite confirmation and backup.' },
  { category: 'Files & Editing', name: 'copy_file', args: 'source, destination', desc: 'Copies files or directories.' },
  { category: 'Files & Editing', name: 'delete_file', args: 'path', desc: 'Deletes files or directories.' },
  { category: 'Files & Editing', name: 'make_dir', args: 'path', desc: 'Creates directory structures recursively.' },
  { category: 'Files & Editing', name: 'file_info', args: 'path', desc: 'Retrieves size, line counts, and metadata.' },
  // Code & Tests
  { category: 'Code & Tests', name: 'search_files', args: 'pattern, path, glob', desc: 'Grep-style recursive keyword search across codebases.' },
  { category: 'Code & Tests', name: 'run_tests', args: 'cwd', desc: 'Auto-detects and executes pytest or npm test.' },
  { category: 'Code & Tests', name: 'git_commit_and_push', args: 'commit_message, branch', desc: 'Stages all changes, creates commits, and pushes to remote.' },
  { category: 'Code & Tests', name: 'clone_repo', args: 'repository, path', desc: 'Clones Git repository to destination folder.' },
  { category: 'Code & Tests', name: 'git_publish', args: 'repo_path, commit_message, branch', desc: 'Auto-stages, commits, and pushes branch to origin remote.' },
  // System & Shell
  { category: 'System & Shell', name: 'run_command', args: 'command, cwd, timeout', desc: 'Runs shell commands with safety checks, blocklists, and timeout.' },
  { category: 'System & Shell', name: 'open_app', args: 'name_or_path', desc: 'Launches applications, local files, or URLs.' },
  { category: 'System & Shell', name: 'system_info', args: '', desc: 'Reports CPU, RAM, Disk, and Battery diagnostics.' },
  { category: 'System & Shell', name: 'list_processes', args: 'limit', desc: 'Lists processes sorted by memory consumption.' },
  { category: 'System & Shell', name: 'kill_process', args: 'pid_or_name', desc: 'Terminates a process by PID or name.' },
  { category: 'System & Shell', name: 'take_screenshot', args: 'save_path', desc: 'Captures the primary display screen.' },
  { category: 'System & Shell', name: 'clipboard_read', args: '', desc: 'Reads text from the system clipboard.' },
  { category: 'System & Shell', name: 'clipboard_write', args: 'text', desc: 'Copies text directly to the system clipboard.' },
  // Web & Network
  { category: 'Web & Network', name: 'web_search', args: 'query, max_results', desc: 'Searches DuckDuckGo / web for live answers and documentation.' },
  { category: 'Web & Network', name: 'browse_webpage', args: 'url', desc: 'Headless parser for web page content.' },
  { category: 'Web & Network', name: 'download_file', args: 'url, path', desc: 'Downloads any file directly over HTTP/HTTPS.' },
  { category: 'Web & Network', name: 'http_request', args: 'method, url, headers, body', desc: 'Performs custom REST API requests.' },
  // Documents
  { category: 'Documents', name: 'create_docx', args: 'path, title, paragraphs', desc: 'Generates formatted Microsoft Word (.docx) documents.' },
  { category: 'Documents', name: 'read_docx', args: 'path', desc: 'Reads text from Word documents.' },
  { category: 'Documents', name: 'create_excel', args: 'path, sheet, rows', desc: 'Generates Microsoft Excel (.xlsx) spreadsheets.' },
  { category: 'Documents', name: 'read_excel', args: 'path', desc: 'Reads rows and columns from Excel spreadsheets.' },
  // Memory
  { category: 'Memory', name: 'remember_fact', args: 'key, value', desc: 'Stores persistent facts and user preferences.' },
  { category: 'Memory', name: 'recall_fact', args: 'key', desc: 'Retrieves saved facts from .gembot/memory.json.' }
];

export const ToolsModal: React.FC<ToolsModalProps> = ({ isOpen, onClose }) => {
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('All');

  if (!isOpen) return null;

  const categories = ['All', 'Files & Editing', 'Code & Tests', 'System & Shell', 'Web & Network', 'Documents', 'Memory'];

  const filtered = TOOLS_LIST.filter(t => {
    const matchesCat = selectedCategory === 'All' || t.category === selectedCategory;
    const matchesSearch = t.name.toLowerCase().includes(search.toLowerCase()) || 
                          t.desc.toLowerCase().includes(search.toLowerCase()) ||
                          t.args.toLowerCase().includes(search.toLowerCase());
    return matchesCat && matchesSearch;
  });

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-[#0f111c] border border-purple-800/60 rounded-2xl w-full max-w-4xl max-h-[85vh] flex flex-col shadow-2xl font-mono">
        {/* Header */}
        <div className="p-4 border-b border-purple-900/40 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Wrench className="w-5 h-5 text-purple-400" />
            <h3 className="font-bold text-gray-100 text-sm">
              Full Autonomous Tool Suite (30 Registered Tools)
            </h3>
          </div>
          <button 
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-white/10 text-gray-400 hover:text-white"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Filter & Search Bar */}
        <div className="p-3 border-b border-purple-900/30 bg-[#131625] flex flex-col sm:flex-row gap-2 items-center justify-between">
          <div className="flex items-center gap-1 overflow-x-auto w-full sm:w-auto pb-1 sm:pb-0">
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`px-2.5 py-1 rounded-md text-[11px] whitespace-nowrap transition-colors ${
                  selectedCategory === cat
                    ? 'bg-purple-600 text-white font-semibold'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-white/5'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>

          <div className="relative w-full sm:w-60">
            <Search className="w-3.5 h-3.5 text-gray-400 absolute left-2.5 top-2.5" />
            <input
              type="text"
              placeholder="Search tools..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-[#0a0c14] border border-purple-900/40 rounded-lg pl-8 pr-3 py-1.5 text-xs text-gray-200 placeholder-gray-500 focus:outline-none focus:border-purple-500/60"
            />
          </div>
        </div>

        {/* Tools Grid */}
        <div className="p-4 overflow-y-auto grid grid-cols-1 md:grid-cols-2 gap-2.5">
          {filtered.map((tool) => (
            <div 
              key={tool.name} 
              className="p-3 rounded-lg bg-[#141727] border border-purple-900/30 hover:border-purple-700/50 transition-colors space-y-1.5"
            >
              <div className="flex items-center justify-between">
                <span className="font-bold text-purple-300 text-xs">{tool.name}</span>
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-purple-950/60 text-purple-400 border border-purple-800/30">
                  {tool.category}
                </span>
              </div>
              <div className="text-[10px] text-gray-400 font-mono">
                args: <span className="text-gray-300">({tool.args || 'none'})</span>
              </div>
              <p className="text-[11px] text-gray-400 font-sans leading-snug">
                {tool.desc}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
