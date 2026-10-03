import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  Cpu, 
  HardDrive, 
  Server, 
  RefreshCw, 
  Database, 
  Plus, 
  Trash2,
  Check
} from 'lucide-react';
import { SystemStats } from '../types';

export const DiagnosticsPanel: React.FC = () => {
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [memoryFacts, setMemoryFacts] = useState<Record<string, string>>({});
  const [newKey, setNewKey] = useState('');
  const [newValue, setNewValue] = useState('');
  const [factSaved, setFactSaved] = useState(false);

  const fetchDiagnostics = async () => {
    setLoading(true);
    try {
      const [sysRes, memRes] = await Promise.all([
        fetch('/api/system'),
        fetch('/api/memory')
      ]);
      if (sysRes.ok) {
        setStats(await sysRes.json());
      }
      if (memRes.ok) {
        const memData = await memRes.json();
        setMemoryFacts(memData.facts || {});
      }
    } catch (err) {
      console.error('Failed to load diagnostics:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDiagnostics();
    const interval = setInterval(fetchDiagnostics, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleAddFact = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKey.trim() || !newValue.trim()) return;
    try {
      const res = await fetch('/api/memory', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key: newKey.trim(), value: newValue.trim() })
      });
      if (res.ok) {
        setMemoryFacts(prev => ({ ...prev, [newKey.trim()]: newValue.trim() }));
        setNewKey('');
        setNewValue('');
        setFactSaved(true);
        setTimeout(() => setFactSaved(false), 2000);
      }
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#0b0c14] border-t border-purple-900/30 font-mono p-4 sm:p-6 max-w-5xl mx-auto overflow-y-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-purple-900/30">
        <div>
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-purple-400" />
            <h2 className="text-base font-bold text-gray-100">
              System Diagnostics &amp; Long-Term Memory
            </h2>
          </div>
          <p className="text-xs text-gray-400 font-sans mt-1">
            Real-time diagnostics from <code className="text-purple-300">system_info</code> and persistent facts from <code className="text-purple-300">remember_fact</code>.
          </p>
        </div>

        <button
          onClick={fetchDiagnostics}
          disabled={loading}
          className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-gray-400 hover:text-gray-200 transition-colors flex items-center gap-1.5 text-xs"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Diagnostics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <div className="p-4 rounded-xl bg-[#0f111c] border border-purple-900/30">
          <div className="flex items-center justify-between text-gray-400 mb-2">
            <span className="text-xs">CPU Load</span>
            <Cpu className="w-4 h-4 text-pink-400" />
          </div>
          <div className="text-xl font-bold text-gray-100">
            {stats ? `${stats.cpuUsage.toFixed(1)}%` : '---'}
          </div>
          <div className="w-full bg-gray-800 rounded-full h-1.5 mt-2">
            <div 
              className="bg-gradient-to-r from-pink-500 to-purple-500 h-1.5 rounded-full" 
              style={{ width: `${Math.min(100, stats?.cpuUsage || 10)}%` }}
            />
          </div>
        </div>

        <div className="p-4 rounded-xl bg-[#0f111c] border border-purple-900/30">
          <div className="flex items-center justify-between text-gray-400 mb-2">
            <span className="text-xs">Memory (RAM)</span>
            <HardDrive className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-xl font-bold text-gray-100">
            {stats ? `${stats.ramUsed.toFixed(1)} / ${stats.ramTotal.toFixed(1)} GB` : '---'}
          </div>
          <div className="w-full bg-gray-800 rounded-full h-1.5 mt-2">
            <div 
              className="bg-gradient-to-r from-purple-500 to-indigo-500 h-1.5 rounded-full" 
              style={{ width: `${Math.min(100, stats?.ramPercent || 20)}%` }}
            />
          </div>
        </div>

        <div className="p-4 rounded-xl bg-[#0f111c] border border-purple-900/30">
          <div className="flex items-center justify-between text-gray-400 mb-2">
            <span className="text-xs">OS &amp; Arch</span>
            <Server className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-sm font-bold text-gray-200 truncate">
            {stats?.os || 'Linux'} ({stats?.arch || 'x64'})
          </div>
          <div className="text-[10px] text-gray-500 mt-2 font-mono">
            Node.js 22 Runtime
          </div>
        </div>

        <div className="p-4 rounded-xl bg-[#0f111c] border border-purple-900/30">
          <div className="flex items-center justify-between text-gray-400 mb-2">
            <span className="text-xs">Memory Facts</span>
            <Database className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-xl font-bold text-gray-100">
            {Object.keys(memoryFacts).length} saved
          </div>
          <div className="text-[10px] text-gray-500 mt-2 font-mono">
            .gembot/memory.json
          </div>
        </div>
      </div>

      {/* Long-Term Memory Section */}
      <div className="bg-[#0f111c] rounded-xl border border-purple-900/30 p-4 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Database className="w-4 h-4 text-emerald-400" />
            <h3 className="text-xs font-bold text-gray-200 uppercase tracking-wider">
              Long-Term Fact Store (remember_fact / recall_fact)
            </h3>
          </div>
          <span className="text-[10px] text-gray-500">Persistent across sessions</span>
        </div>

        <form onSubmit={handleAddFact} className="flex flex-col sm:flex-row gap-2">
          <input
            type="text"
            placeholder="Fact Key (e.g. project_stack)"
            value={newKey}
            onChange={(e) => setNewKey(e.target.value)}
            className="flex-1 bg-[#141724] border border-purple-900/40 rounded-lg px-3 py-1.5 text-xs text-gray-200 placeholder-gray-500 focus:outline-none focus:border-purple-500/60"
          />
          <input
            type="text"
            placeholder="Fact Value (e.g. Next.js 14, Tailwind, Ollama)"
            value={newValue}
            onChange={(e) => setNewValue(e.target.value)}
            className="flex-2 bg-[#141724] border border-purple-900/40 rounded-lg px-3 py-1.5 text-xs text-gray-200 placeholder-gray-500 focus:outline-none focus:border-purple-500/60"
          />
          <button
            type="submit"
            className="px-3 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-medium flex items-center gap-1 shrink-0 transition-colors"
          >
            {factSaved ? <Check className="w-3.5 h-3.5" /> : <Plus className="w-3.5 h-3.5" />}
            <span>Save Fact</span>
          </button>
        </form>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-48 overflow-y-auto">
          {Object.entries(memoryFacts).length === 0 ? (
            <div className="col-span-2 text-center py-4 text-gray-500 text-xs font-sans">
              No facts stored yet. GEMBOT automatically calls remember_fact during tasks, or you can add one above.
            </div>
          ) : (
            Object.entries(memoryFacts).map(([k, v]) => (
              <div 
                key={k} 
                className="p-2.5 rounded-lg bg-[#131625] border border-purple-900/30 flex items-start justify-between text-xs"
              >
                <div className="overflow-hidden">
                  <span className="font-semibold text-purple-300 block truncate">{k}</span>
                  <span className="text-gray-400 font-sans text-[11px] break-words">{v}</span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
