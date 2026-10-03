import React from 'react';
import { X, HelpCircle, Terminal, KeyRound, ShieldAlert, Cpu } from 'lucide-react';

interface HelpModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectCommand: (cmd: string) => void;
}

export const HelpModal: React.FC<HelpModalProps> = ({ isOpen, onClose, onSelectCommand }) => {
  if (!isOpen) return null;

  const commands = [
    { cmd: '/help', desc: 'Display command guide and shortcuts' },
    { cmd: '/tools', desc: 'List all 30 available autonomous tools with full argument schemas' },
    { cmd: '/models', desc: 'Switch active AI model (e.g. qwen2.5-coder:7b, gemma4:e2b, gemini-2.5-flash)' },
    { cmd: '/plan <task>', desc: 'Force step-by-step checklist planning mode before executing' },
    { cmd: '/undo', desc: 'Restore the last modified file from .gembot/backups/ snapshot' },
    { cmd: '/auto on|off', desc: 'Toggle Safety Gate confirmation prompts for destructive actions' },
    { cmd: '/save <name>', desc: 'Save current conversation session to .gembot/sessions/' },
    { cmd: '/load <name>', desc: 'Restore a previous conversation session' },
    { cmd: '/paste', desc: 'Multimodal clipboard image grab or pasted file content' },
    { cmd: '/clear', desc: 'Clear terminal screen and conversation memory' },
  ];

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4 font-mono">
      <div className="bg-[#0f111c] border border-purple-800/60 rounded-2xl w-full max-w-2xl max-h-[85vh] flex flex-col shadow-2xl">
        <div className="p-4 border-b border-purple-900/40 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <HelpCircle className="w-5 h-5 text-purple-400" />
            <h3 className="font-bold text-gray-100 text-sm">
              GEMBOT Command Guide &amp; Slash Commands
            </h3>
          </div>
          <button 
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-white/10 text-gray-400 hover:text-white"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-4 overflow-y-auto space-y-4">
          <div className="space-y-2">
            <h4 className="text-xs uppercase text-purple-400 font-semibold tracking-wider">
              Interactive Slash Commands
            </h4>
            <div className="space-y-1.5">
              {commands.map((c) => (
                <div
                  key={c.cmd}
                  onClick={() => { onSelectCommand(c.cmd.split(' ')[0]); onClose(); }}
                  className="p-2.5 rounded-lg bg-[#141727] border border-purple-900/30 hover:border-purple-600/50 hover:bg-purple-950/30 cursor-pointer transition-all flex items-center justify-between"
                >
                  <span className="font-bold text-purple-300 text-xs">{c.cmd}</span>
                  <span className="text-[11px] text-gray-400 font-sans">{c.desc}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="p-3 rounded-lg bg-purple-950/20 border border-purple-900/30 space-y-1 text-xs font-sans text-gray-300">
            <h5 className="font-semibold text-purple-300 font-mono">Keyboard Shortcuts:</h5>
            <ul className="list-disc list-inside space-y-1 text-[11px] text-gray-400">
              <li><strong className="text-gray-200">Enter:</strong> Send current instruction to agent</li>
              <li><strong className="text-gray-200">Shift + Enter:</strong> Insert newline</li>
              <li><strong className="text-gray-200">Ctrl + C / Stop Button:</strong> Abort running tool or LLM generation</li>
              <li><strong className="text-gray-200">/ :</strong> Open slash command autocomplete popup</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};
