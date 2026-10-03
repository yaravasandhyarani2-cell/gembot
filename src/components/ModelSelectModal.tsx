import React from 'react';
import { X, Cpu, Check, Sparkles } from 'lucide-react';

interface ModelSelectModalProps {
  isOpen: boolean;
  onClose: () => void;
  activeModel: string;
  onSelectModel: (modelName: string) => void;
}

const MODELS = [
  { id: 'gemini-2.5-flash', name: 'Gemini 2.5 Flash', tag: 'Fast & Intelligent (Recommended)', desc: 'Best overall performance, ultra-fast tool calling and reasoning.' },
  { id: 'gemini-2.5-pro', name: 'Gemini 2.5 Pro', tag: 'Complex Code Reasoning', desc: 'Deep architectural logic and multi-file reasoning.' },
  { id: 'qwen2.5-coder:7b', name: 'Qwen 2.5 Coder 7B', tag: 'Ollama Coding Champion', desc: 'Offline coding specialist with precision patch-edit capability.' },
  { id: 'qwen2.5-coder:3b', name: 'Qwen 2.5 Coder 3B', tag: 'Lightweight & Ultra-Fast', desc: 'Fast local iteration with Gembot self-healing JSON fallback.' },
  { id: 'gemma4:e2b', name: 'Gemma 4:E2B', tag: 'Multimodal Vision & Desktop', desc: 'Windows desktop tool automation and multimodal clipboard analysis.' },
  { id: 'llama3.1:8b', name: 'Llama 3.1 8B', tag: 'Open General Reasoner', desc: 'Robust general instruction following.' },
];

export const ModelSelectModal: React.FC<ModelSelectModalProps> = ({
  isOpen,
  onClose,
  activeModel,
  onSelectModel
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4 font-mono">
      <div className="bg-[#0f111c] border border-purple-800/60 rounded-2xl w-full max-w-xl flex flex-col shadow-2xl overflow-hidden">
        <div className="p-4 border-b border-purple-900/40 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Cpu className="w-5 h-5 text-purple-400" />
            <h3 className="font-bold text-gray-100 text-sm">
              Select Active Agent Model (/models)
            </h3>
          </div>
          <button 
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-white/10 text-gray-400 hover:text-white"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-4 overflow-y-auto space-y-2 max-h-[70vh]">
          {MODELS.map((m) => {
            const isSelected = activeModel === m.id;
            return (
              <div
                key={m.id}
                onClick={() => { onSelectModel(m.id); onClose(); }}
                className={`p-3 rounded-xl border cursor-pointer transition-all flex items-start justify-between gap-3 ${
                  isSelected
                    ? 'bg-purple-950/50 border-purple-500 shadow-md shadow-purple-950/40'
                    : 'bg-[#141727] border-purple-900/30 hover:border-purple-700/60 hover:bg-purple-950/20'
                }`}
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-gray-100 text-xs">{m.name}</span>
                    <span className="text-[10px] px-1.5 py-0.2 rounded bg-purple-900/60 text-purple-300 font-sans">
                      {m.tag}
                    </span>
                  </div>
                  <p className="text-[11px] text-gray-400 font-sans">{m.desc}</p>
                  <code className="text-[10px] text-purple-400/80">{m.id}</code>
                </div>

                {isSelected && (
                  <div className="w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center shrink-0 mt-0.5">
                    <Check className="w-3.5 h-3.5" />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
