import React, { useState, useRef, useEffect } from 'react';
import { 
  Send, 
  Square, 
  FileCode, 
  CheckCircle2, 
  AlertTriangle, 
  Loader2, 
  Terminal as TerminalIcon, 
  ChevronRight, 
  Copy, 
  Check, 
  Sparkles,
  Paperclip,
  Shield,
  Layers,
  FilePlus,
  Play,
  Compass,
  Folder
} from 'lucide-react';
import { ChatMessage, ToolCallItem, AgentConfig } from '../types';
import { DirectoryPointerBar } from './DirectoryPointerBar';

interface AgentTerminalProps {
  messages: ChatMessage[];
  isRunning: boolean;
  onSendMessage: (text: string) => void;
  onStop: () => void;
  onConfirmAction: (actionId: string, proceed: boolean) => void;
  pendingConfirmation: { id: string; actionDesc: string } | null;
  config: AgentConfig;
  onOpenWorkspaceFile?: (path: string) => void;
  onDirectoryChange?: (newPath: string) => void;
}

const SLASH_COMMANDS = [
  { cmd: '/dir', desc: 'Inspect and point out the active local folder and file directory' },
  { cmd: '/cd <path>', desc: 'Point Gembot to work on a specific local folder' },
  { cmd: '/pwd', desc: 'Display the absolute path of the active local directory' },
  { cmd: '/help', desc: 'Display command guide and shortcuts' },
  { cmd: '/tools', desc: 'List all 30 available autonomous tools' },
  { cmd: '/models', desc: 'Switch or select AI models' },
  { cmd: '/plan', desc: 'Force step-by-step checklist planning mode' },
  { cmd: '/undo', desc: 'Restore the last modified file from backups' },
  { cmd: '/auto on', desc: 'Bypass confirmation prompts for dangerous actions' },
  { cmd: '/auto off', desc: 'Enable confirmation prompts for dangerous actions' },
  { cmd: '/save', desc: 'Save current conversation session' },
  { cmd: '/load', desc: 'Restore a previous conversation session' },
  { cmd: '/paste', desc: 'Inspect screenshot or file from clipboard' },
  { cmd: '/clear', desc: 'Clear screen and conversation memory' },
];

export const AgentTerminal: React.FC<AgentTerminalProps> = ({
  messages,
  isRunning,
  onSendMessage,
  onStop,
  onConfirmAction,
  pendingConfirmation,
  config,
  onOpenWorkspaceFile,
  onDirectoryChange
}) => {
  const [input, setInput] = useState('');
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [showSlashMenu, setShowSlashMenu] = useState(false);
  const [slashFilter, setSlashFilter] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isRunning, pendingConfirmation]);

  // Focus input on load
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const val = e.target.value;
    setInput(val);
    if (val.startsWith('/')) {
      setShowSlashMenu(true);
      setSlashFilter(val.toLowerCase());
    } else {
      setShowSlashMenu(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    } else if (e.key === 'Escape') {
      setShowSlashMenu(false);
    }
  };

  const handleSend = () => {
    if (!input.trim() || isRunning) return;
    onSendMessage(input.trim());
    setInput('');
    setShowSlashMenu(false);
  };

  const handleSelectSlash = (cmd: string) => {
    setInput(cmd + ' ');
    setShowSlashMenu(false);
    inputRef.current?.focus();
  };

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const filteredSlash = SLASH_COMMANDS.filter(s => 
    s.cmd.toLowerCase().includes(slashFilter) || s.desc.toLowerCase().includes(slashFilter)
  );

  return (
    <div className="flex flex-col h-full bg-[#0b0c14] relative overflow-hidden font-mono text-xs sm:text-sm">
      {/* Active Local Folder & Directory Pointer Bar */}
      <DirectoryPointerBar 
        onDirectoryChange={onDirectoryChange}
        onPointOutDirectory={(dir) => onSendMessage(`/dir ${dir}`)}
      />

      {/* Messages Scroll Area */}
      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-4 space-y-4 font-mono scroll-smooth"
      >
        {/* Banner */}
        <div className="bg-[#10121d] rounded-xl p-4 border border-purple-900/30 text-center select-none shadow-xl shadow-purple-950/20">
          <pre className="text-[9px] sm:text-[11px] leading-tight text-transparent bg-clip-text bg-gradient-to-r from-purple-400 via-pink-400 to-indigo-400 font-bold inline-block text-left mb-2">
{` ██████╗ ███████╗███╗   ███╗██████╗  ██████╗ ████████╗
██╔════╝ ██╔════╝████╗ ████║██╔══██╗██╔═══██╗╚══██╔══╝
██║  ███╗█████╗  ██╔████╔██║██████╔╝██║   ██║   ██║   
██║   ██║██╔══╝  ██║╚██╔╝██║██╔══██╗██║   ██║   ██║   
╚██████╔╝███████╗██║ ╚═╝ ██║██████╔╝╚██████╔╝   ██║   
 ╚═════╝ ╚══════╝╚═╝     ╚═╝╚═════╝  ╚═════╝    ╚═╝   `}
          </pre>
          <div className="text-gray-300 font-sans text-xs max-w-xl mx-auto space-y-1">
            <p className="font-semibold text-purple-300">
              Welcome to GEMBOT Autonomous AI Agent
            </p>
            <p className="text-gray-400 text-[11px]">
              Multi-tool agent with 30 tools, precision patch-editing, undo backups, and self-healing task loop.
            </p>
            <div className="flex items-center justify-center gap-2 pt-2 text-[10px] text-gray-500 font-mono">
              <span className="px-2 py-0.5 rounded bg-purple-950/60 border border-purple-900/40 text-purple-300">
                Model: {config.model}
              </span>
              <span className="px-2 py-0.5 rounded bg-emerald-950/60 border border-emerald-900/40 text-emerald-300">
                Auto-Confirm: {config.auto_confirm ? 'ON' : 'OFF'}
              </span>
              <span className="px-2 py-0.5 rounded bg-indigo-950/60 border border-indigo-900/40 text-indigo-300">
                Max Steps: {config.max_steps}
              </span>
            </div>
          </div>
        </div>

        {/* Suggestion Chips */}
        {messages.length <= 1 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 pt-1">
            <button
              onClick={() => onSendMessage("Build Chatbox-X: clean Next.js + Tailwind web application connecting to local Ollama with real-time text streaming, package.json, components, and git commit ready.")}
              className="p-3 rounded-lg bg-[#121522] border border-purple-900/40 hover:border-purple-500/60 hover:bg-purple-950/20 text-left transition-all group"
            >
              <div className="flex items-center gap-2 text-purple-400 font-semibold mb-1 text-xs">
                <Sparkles className="w-3.5 h-3.5 text-pink-400 group-hover:scale-110 transition-transform" />
                <span>Build Chatbox-X App</span>
              </div>
              <p className="text-[11px] text-gray-400">Scaffold full Next.js/Tailwind chatbox connected to Ollama without early termination.</p>
            </button>

            <button
              onClick={() => onSendMessage("/plan Scaffold a full-stack REST API with user authentication, SQLite database, and test suite")}
              className="p-3 rounded-lg bg-[#121522] border border-purple-900/40 hover:border-purple-500/60 hover:bg-purple-950/20 text-left transition-all group"
            >
              <div className="flex items-center gap-2 text-indigo-400 font-semibold mb-1 text-xs">
                <Layers className="w-3.5 h-3.5 text-indigo-400 group-hover:scale-110 transition-transform" />
                <span>Checklist Plan Mode</span>
              </div>
              <p className="text-[11px] text-gray-400">Break complex fullstack requirements into ordered execution checklist.</p>
            </button>

            <button
              onClick={() => onSendMessage("Run system_info diagnostics and check CPU, RAM, and workspace health")}
              className="p-3 rounded-lg bg-[#121522] border border-purple-900/40 hover:border-purple-500/60 hover:bg-purple-950/20 text-left transition-all group"
            >
              <div className="flex items-center gap-2 text-emerald-400 font-semibold mb-1 text-xs">
                <TerminalIcon className="w-3.5 h-3.5 text-emerald-400 group-hover:scale-110 transition-transform" />
                <span>System Diagnostics</span>
              </div>
              <p className="text-[11px] text-gray-400">Inspect live hardware usage, OS specs, and sandbox environment state.</p>
            </button>

            <button
              onClick={() => onSendMessage("/dir")}
              className="p-3 rounded-lg bg-[#121522] border border-purple-900/40 hover:border-purple-500/60 hover:bg-purple-950/20 text-left transition-all group sm:col-span-2 lg:col-span-3"
            >
              <div className="flex items-center gap-2 text-pink-400 font-semibold mb-1 text-xs">
                <Compass className="w-3.5 h-3.5 text-pink-400 group-hover:scale-110 transition-transform" />
                <span>Point Out File Directory</span>
              </div>
              <p className="text-[11px] text-gray-400">Inspect active local folder, list all subdirectories, and point Gembot to any directory.</p>
            </button>
          </div>
        )}

        {/* Message Stream */}
        {messages.map((msg) => (
          <div key={msg.id} className="space-y-2">
            {msg.role === 'user' ? (
              <div className="flex items-start gap-2 bg-[#171a29]/80 border border-purple-900/30 rounded-lg p-3">
                <div className="w-6 h-6 rounded bg-purple-700/60 flex items-center justify-center shrink-0 mt-0.5">
                  <ChevronRight className="w-4 h-4 text-purple-200" />
                </div>
                <div className="flex-1 overflow-x-auto whitespace-pre-wrap font-sans text-gray-100 text-xs sm:text-sm">
                  {msg.content}
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                {/* Step info pill if available */}
                {msg.stepInfo && (
                  <div className="flex items-center gap-2 text-[10px] text-purple-400/80 font-mono">
                    <span className="w-1.5 h-1.5 rounded-full bg-purple-400" />
                    <span>Autonomous Cycle: Step {msg.stepInfo.current} / {msg.stepInfo.max}</span>
                  </div>
                )}

                {/* Assistant Content / Thoughts */}
                {msg.content && (
                  <div className="bg-[#10121d] border border-purple-900/20 rounded-lg p-3 text-gray-200 font-sans leading-relaxed text-xs sm:text-sm">
                    <div className="whitespace-pre-wrap">{msg.content}</div>
                  </div>
                )}

                {/* Tool Executions */}
                {msg.toolCalls && msg.toolCalls.length > 0 && (
                  <div className="space-y-2">
                    {msg.toolCalls.map((call) => (
                      <div 
                        key={call.id}
                        className="rounded-lg border border-purple-900/40 bg-[#0f111c] overflow-hidden"
                      >
                        {/* Tool Header */}
                        <div className="bg-[#141824] px-3 py-2 flex items-center justify-between border-b border-purple-900/30">
                          <div className="flex items-center gap-2">
                            {call.status === 'running' ? (
                              <Loader2 className="w-3.5 h-3.5 text-purple-400 animate-spin" />
                            ) : call.status === 'completed' ? (
                              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                            ) : call.status === 'error' ? (
                              <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
                            ) : (
                              <Shield className="w-3.5 h-3.5 text-amber-400" />
                            )}

                            <span className="font-mono font-semibold text-purple-300">
                              {call.name}
                            </span>

                            {call.args.path && (
                              <span 
                                onClick={() => onOpenWorkspaceFile && onOpenWorkspaceFile(call.args.path)}
                                className="text-gray-400 text-[11px] font-mono hover:text-purple-300 hover:underline cursor-pointer truncate max-w-xs"
                              >
                                {call.args.path}
                              </span>
                            )}
                          </div>

                          <div className="flex items-center gap-2">
                            <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono ${
                              call.status === 'completed' ? 'bg-emerald-950/80 text-emerald-300 border border-emerald-800/40' :
                              call.status === 'running' ? 'bg-purple-950/80 text-purple-300 border border-purple-800/40 animate-pulse' :
                              call.status === 'awaiting_confirmation' ? 'bg-amber-950/80 text-amber-300 border border-amber-800/40' :
                              'bg-rose-950/80 text-rose-300 border border-rose-800/40'
                            }`}>
                              {call.status}
                            </span>
                            <button
                              onClick={() => copyToClipboard(JSON.stringify(call.args, null, 2), call.id)}
                              className="text-gray-500 hover:text-gray-300"
                              title="Copy args"
                            >
                              {copiedId === call.id ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                            </button>
                          </div>
                        </div>

                        {/* Arguments / Live Code Preview */}
                        {call.name === 'write_file' && typeof call.args.content === 'string' && (
                          <div className="p-3 bg-[#0a0c14] border-b border-purple-950/40">
                            <div className="flex items-center justify-between text-[11px] text-purple-400/90 mb-1.5">
                              <span className="flex items-center gap-1 font-mono">
                                <FileCode className="w-3 h-3 text-pink-400" />
                                Live Code Generator: {call.args.path || 'file'}
                              </span>
                              <span className="text-[10px] text-gray-500">
                                {call.args.content.split('\n').length} lines
                              </span>
                            </div>
                            <pre className="text-[11px] text-gray-300 bg-[#07080e] p-2.5 rounded border border-purple-900/20 max-h-48 overflow-y-auto whitespace-pre font-mono">
                              {call.args.content.slice(0, 1500)}
                              {call.args.content.length > 1500 ? `\n... [+${call.args.content.length - 1500} more characters]` : ''}
                            </pre>
                          </div>
                        )}

                        {/* Tool Result */}
                        {call.result && (
                          <div className="p-2.5 bg-[#0c0d16] text-[11px] font-mono text-gray-300 overflow-x-auto whitespace-pre-wrap">
                            <span className="text-gray-500">↳ Result: </span>
                            <span className={call.status === 'error' ? 'text-rose-300' : 'text-emerald-300/90'}>
                              {call.result}
                            </span>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}

        {/* Safety Gate Confirmation Prompt */}
        {pendingConfirmation && (
          <div className="bg-amber-950/30 border border-amber-500/50 rounded-lg p-4 animate-in fade-in duration-200">
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-lg bg-amber-500/20 text-amber-400 shrink-0">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div className="flex-1 space-y-2">
                <div className="flex items-center justify-between">
                  <h4 className="font-semibold text-amber-300 text-sm">
                    ⚠ SAFETY GATE: Confirmation Required
                  </h4>
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-900/60 text-amber-200">
                    /auto is off
                  </span>
                </div>
                <p className="text-gray-300 text-xs font-mono">
                  {pendingConfirmation.actionDesc}
                </p>
                <div className="flex items-center gap-2 pt-1">
                  <button
                    onClick={() => onConfirmAction(pendingConfirmation.id, true)}
                    className="px-3 py-1.5 rounded-md bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs flex items-center gap-1.5 transition-colors shadow"
                  >
                    <Check className="w-3.5 h-3.5" />
                    <span>Proceed (Execute)</span>
                  </button>
                  <button
                    onClick={() => onConfirmAction(pendingConfirmation.id, false)}
                    className="px-3 py-1.5 rounded-md bg-rose-950/80 border border-rose-800/60 hover:bg-rose-900 text-rose-300 font-medium text-xs transition-colors"
                  >
                    Cancel Action
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Running Progress Bar */}
        {isRunning && (
          <div className="flex items-center gap-2 text-purple-400 font-mono text-xs bg-purple-950/30 border border-purple-900/40 p-2.5 rounded-lg animate-pulse">
            <Loader2 className="w-4 h-4 animate-spin text-pink-400" />
            <span>GEMBOT autonomous loop thinking & executing actions...</span>
          </div>
        )}
      </div>

      {/* Slash command dropdown */}
      {showSlashMenu && filteredSlash.length > 0 && (
        <div className="absolute bottom-20 left-4 right-4 sm:left-6 sm:right-6 max-h-56 overflow-y-auto bg-[#141726] border border-purple-800/60 rounded-xl shadow-2xl p-1.5 z-30 space-y-1">
          <div className="text-[10px] text-gray-400 px-2 py-1 font-mono uppercase tracking-wider">
            Available Slash Commands
          </div>
          {filteredSlash.map((item) => (
            <button
              key={item.cmd}
              onClick={() => handleSelectSlash(item.cmd)}
              className="w-full text-left px-2.5 py-1.5 rounded-lg hover:bg-purple-900/40 flex items-center justify-between text-xs transition-colors group"
            >
              <span className="font-mono text-purple-300 group-hover:text-purple-200 font-semibold">
                {item.cmd}
              </span>
              <span className="text-gray-400 text-[11px] truncate max-w-xs">
                {item.desc}
              </span>
            </button>
          ))}
        </div>
      )}

      {/* Input Form Bar */}
      <div className="p-3 border-t border-purple-900/30 bg-[#0e101a]">
        <div className="relative flex items-center bg-[#131624] border border-purple-900/50 rounded-xl focus-within:border-purple-500/80 focus-within:ring-1 focus-within:ring-purple-500/30 shadow-inner">
          <div className="pl-3 text-purple-400 font-mono font-bold select-none text-xs">
            gembot&gt;
          </div>
          <textarea
            ref={inputRef}
            rows={1}
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder="Type task, paste code, or type / for commands (/plan, /undo, /tools)..."
            className="w-full bg-transparent px-3 py-3 text-xs sm:text-sm text-gray-100 placeholder-gray-500 focus:outline-none resize-none font-mono max-h-32"
          />

          <div className="flex items-center gap-1.5 pr-2">
            {isRunning ? (
              <button
                onClick={onStop}
                className="px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-mono text-xs flex items-center gap-1 shadow-lg shadow-rose-950/40 transition-all"
                title="Stop execution (Ctrl+C)"
              >
                <Square className="w-3 h-3 fill-current" />
                <span>Stop</span>
              </button>
            ) : (
              <button
                onClick={handleSend}
                disabled={!input.trim()}
                className={`p-2 rounded-lg font-mono text-xs flex items-center justify-center transition-all ${
                  input.trim()
                    ? 'bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white shadow-lg shadow-purple-950/50'
                    : 'text-gray-600 cursor-not-allowed'
                }`}
                title="Send task"
              >
                <Send className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        <div className="flex items-center justify-between px-1 pt-1.5 text-[10px] text-gray-500 font-mono">
          <span>Press Enter to send · Shift+Enter for newline · / for commands</span>
          <span className="hidden sm:inline">Ctrl+C aborts active task</span>
        </div>
      </div>
    </div>
  );
};
