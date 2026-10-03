import React from 'react';
import { 
  Bot, 
  Shield, 
  ShieldAlert, 
  RotateCcw, 
  Terminal, 
  FolderTree, 
  Activity, 
  History, 
  HelpCircle, 
  Wrench, 
  Trash2,
  ChevronDown
} from 'lucide-react';
import { AgentConfig } from '../types';
import { BorderBeam } from 'border-beam';
import { ThinkingOrb } from 'thinking-orbs';

interface HeaderProps {
  config: AgentConfig;
  onToggleAutoConfirm: () => void;
  onUndo: () => void;
  onClear: () => void;
  onOpenHelp: () => void;
  onOpenTools: () => void;
  onOpenModelSelect: () => void;
  activeTab: 'terminal' | 'workspace' | 'backups' | 'diagnostics';
  setActiveTab: (tab: 'terminal' | 'workspace' | 'backups' | 'diagnostics') => void;
  isRunning: boolean;
  canUndo: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  config,
  onToggleAutoConfirm,
  onUndo,
  onClear,
  onOpenHelp,
  onOpenTools,
  onOpenModelSelect,
  activeTab,
  setActiveTab,
  isRunning,
  canUndo
}) => {
  return (
    <header className="border-b border-purple-900/40 bg-[#0d0f17]/90 backdrop-blur-md px-4 py-2.5 flex items-center justify-between gap-4 z-20">
      {/* Brand & Status */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 via-indigo-500 to-pink-500 p-0.5 flex items-center justify-center shadow-lg shadow-purple-900/30">
            <div className="w-full h-full bg-[#0e0f17] rounded-[7px] flex items-center justify-center">
              <Bot className="w-4 h-4 text-purple-400" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-mono font-bold tracking-wider text-transparent bg-clip-text bg-gradient-to-r from-purple-400 via-pink-300 to-indigo-300 text-sm">
                GEMBOT
              </span>
              <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-purple-950/80 text-purple-300 border border-purple-800/40">
                v2.0
              </span>
            </div>
            <p className="text-[11px] text-gray-400 hidden sm:block">Autonomous AI Coding Agent</p>
          </div>
        </div>

        {/* Model Switcher Badge */}
        <div className="ml-2">
          <BorderBeam size="sm" colorVariant="ocean" strength={0.65} theme="dark">
            <button
              onClick={onOpenModelSelect}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-mono bg-purple-950/40 hover:bg-purple-900/40 text-purple-300 border border-purple-800/50 transition-colors"
              title="Change active model (/models)"
            >
              <ThinkingOrb state={isRunning ? "solving" : "breathing"} size={20} theme="dark" speed={isRunning ? 1.4 : 0.8} />
              <span className="truncate max-w-[130px]">{config.model}</span>
              <ChevronDown className="w-3 h-3 text-purple-400/80" />
            </button>
          </BorderBeam>
        </div>

        {/* Safety Gate status badge */}
        <button
          onClick={onToggleAutoConfirm}
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-mono transition-colors border ${
            config.auto_confirm
              ? 'bg-amber-950/40 border-amber-800/50 text-amber-300 hover:bg-amber-900/40'
              : 'bg-emerald-950/40 border-emerald-800/50 text-emerald-300 hover:bg-emerald-900/40'
          }`}
          title={config.auto_confirm ? "Safety Gate bypassed (/auto on). Click to require confirmations." : "Safety Gate active (/auto off). Confirms destructive actions."}
        >
          {config.auto_confirm ? (
            <>
              <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
              <span>/auto: on</span>
            </>
          ) : (
            <>
              <Shield className="w-3.5 h-3.5 text-emerald-400" />
              <span>/auto: off</span>
            </>
          )}
        </button>
      </div>

      {/* Navigation Tabs */}
      <div className="flex items-center bg-[#131622] p-1 rounded-lg border border-purple-900/30 text-xs font-medium">
        <button
          onClick={() => setActiveTab('terminal')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md transition-all ${
            activeTab === 'terminal'
              ? 'bg-gradient-to-r from-purple-700 to-indigo-700 text-white shadow'
              : 'text-gray-400 hover:text-gray-200 hover:bg-white/5'
          }`}
        >
          <Terminal className="w-3.5 h-3.5" />
          <span>Agent Console</span>
        </button>

        <button
          onClick={() => setActiveTab('workspace')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md transition-all ${
            activeTab === 'workspace'
              ? 'bg-gradient-to-r from-purple-700 to-indigo-700 text-white shadow'
              : 'text-gray-400 hover:text-gray-200 hover:bg-white/5'
          }`}
        >
          <FolderTree className="w-3.5 h-3.5" />
          <span>Workspace</span>
        </button>

        <button
          onClick={() => setActiveTab('backups')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md transition-all ${
            activeTab === 'backups'
              ? 'bg-gradient-to-r from-purple-700 to-indigo-700 text-white shadow'
              : 'text-gray-400 hover:text-gray-200 hover:bg-white/5'
          }`}
        >
          <History className="w-3.5 h-3.5" />
          <span>Backups & Undo</span>
        </button>

        <button
          onClick={() => setActiveTab('diagnostics')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md transition-all ${
            activeTab === 'diagnostics'
              ? 'bg-gradient-to-r from-purple-700 to-indigo-700 text-white shadow'
              : 'text-gray-400 hover:text-gray-200 hover:bg-white/5'
          }`}
        >
          <Activity className="w-3.5 h-3.5" />
          <span>Diagnostics</span>
        </button>
      </div>

      {/* Action Buttons */}
      <div className="flex items-center gap-1.5">
        <button
          onClick={onUndo}
          disabled={!canUndo || isRunning}
          className={`flex items-center gap-1 px-2.5 py-1.5 rounded-md text-xs font-mono border transition-all ${
            canUndo && !isRunning
              ? 'bg-indigo-950/40 border-indigo-700/60 text-indigo-300 hover:bg-indigo-900/50 hover:text-white'
              : 'opacity-40 cursor-not-allowed border-gray-800 text-gray-500'
          }`}
          title="Restore last modified file (/undo)"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span className="hidden md:inline">/undo</span>
        </button>

        <button
          onClick={onOpenTools}
          className="p-1.5 rounded-md text-gray-400 hover:text-purple-300 hover:bg-purple-950/40 border border-transparent hover:border-purple-800/40 transition-colors"
          title="View all 30 tools (/tools)"
        >
          <Wrench className="w-4 h-4" />
        </button>

        <button
          onClick={onOpenHelp}
          className="p-1.5 rounded-md text-gray-400 hover:text-purple-300 hover:bg-purple-950/40 border border-transparent hover:border-purple-800/40 transition-colors"
          title="Help & slash commands (/help)"
        >
          <HelpCircle className="w-4 h-4" />
        </button>

        <button
          onClick={onClear}
          disabled={isRunning}
          className="p-1.5 rounded-md text-gray-400 hover:text-red-400 hover:bg-red-950/30 border border-transparent hover:border-red-900/40 transition-colors"
          title="Clear screen & conversation (/clear)"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
};
