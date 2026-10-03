'use client';

import React, { useState, useRef, useEffect } from 'react';
import { streamOllamaChat, ChatMessage } from '@/models/chatbox';
import { Send, Bot, User, Trash2, StopCircle, RefreshCw } from 'lucide-react';

export default function Chatbox() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: 'assistant', content: 'Hello! I am Chatbox-X, running locally on Gemma 4:E2B via Ollama. How can I assist you today?' }
  ]);
  const [input, setInput] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isGenerating]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isGenerating) return;

    const userText = input.trim();
    setInput('');

    const newMessages: ChatMessage[] = [
      ...messages,
      { role: 'user', content: userText }
    ];
    setMessages(newMessages);
    setIsGenerating(true);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    // Append initial empty assistant message for streaming
    setMessages(prev => [...prev, { role: 'assistant', content: '' }]);

    try {
      for await (const chunk of streamOllamaChat(newMessages, controller.signal)) {
        setMessages(prev => {
          const last = prev[prev.length - 1];
          return [
            ...prev.slice(0, -1),
            { ...last, content: last.content + chunk }
          ];
        });
      }
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        setMessages(prev => [
          ...prev,
          { role: 'assistant', content: `⚠️ Error: Could not connect to Ollama at http://localhost:11434. Make sure Ollama is running and 'ollama pull gemma4:e2b' is installed.` }
        ]);
      }
    } finally {
      setIsGenerating(false);
      abortControllerRef.current = null;
    }
  };

  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsGenerating(false);
    }
  };

  const handleClear = () => {
    setMessages([{ role: 'assistant', content: 'Chat history cleared. How can I help?' }]);
  };

  return (
    <div className="flex flex-col h-screen bg-slate-950 text-slate-100 font-sans">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-purple-500 to-indigo-500 flex items-center justify-center shadow-lg shadow-purple-500/20">
            <Bot className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-sm tracking-wide bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-pink-300">
              Chatbox-X
            </h1>
            <p className="text-[11px] text-slate-400">Ollama · gemma4:e2b · Local Streaming</p>
          </div>
        </div>
        <button
          onClick={handleClear}
          className="p-2 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
          title="Clear Chat"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4 max-w-3xl w-full mx-auto">
        {messages.map((m, idx) => (
          <div
            key={idx}
            className={`flex items-start gap-3 ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {m.role === 'assistant' && (
              <div className="w-7 h-7 rounded-full bg-purple-900/50 border border-purple-700/50 flex items-center justify-center shrink-0 mt-0.5">
                <Bot className="w-4 h-4 text-purple-300" />
              </div>
            )}
            <div
              className={`p-4 rounded-2xl max-w-xl text-sm leading-relaxed whitespace-pre-wrap shadow-md ${
                m.role === 'user'
                  ? 'bg-purple-600 text-white rounded-tr-none'
                  : 'bg-slate-900/90 border border-slate-800 text-slate-200 rounded-tl-none'
              }`}
            >
              {m.content || (isGenerating && idx === messages.length - 1 ? <span className="animate-pulse">Thinking...</span> : '')}
            </div>
            {m.role === 'user' && (
              <div className="w-7 h-7 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center shrink-0 mt-0.5">
                <User className="w-4 h-4 text-slate-300" />
              </div>
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-slate-800 p-4 bg-slate-900/40">
        <form onSubmit={handleSend} className="max-w-3xl mx-auto flex items-center gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message to Gemma 4..."
            className="flex-1 bg-slate-800/80 border border-slate-700/80 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-purple-500/80 focus:ring-1 focus:ring-purple-500/30 placeholder-slate-500"
          />
          {isGenerating ? (
            <button
              type="button"
              onClick={handleStop}
              className="p-3 rounded-xl bg-rose-600 hover:bg-rose-500 text-white transition-colors"
              title="Stop Generation"
            >
              <StopCircle className="w-5 h-5" />
            </button>
          ) : (
            <button
              type="submit"
              disabled={!input.trim()}
              className="p-3 rounded-xl bg-purple-600 hover:bg-purple-500 disabled:opacity-40 disabled:cursor-not-allowed text-white transition-colors shadow-lg shadow-purple-900/30"
              title="Send Message"
            >
              <Send className="w-5 h-5" />
            </button>
          )}
        </form>
      </div>
    </div>
  );
}
