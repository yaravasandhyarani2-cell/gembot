import React, { useState, useEffect } from 'react';
import { History, RotateCcw, RefreshCw, FileCode, CheckCircle2, AlertCircle } from 'lucide-react';
import { BackupItem } from '../types';

interface BackupsPanelProps {
  onRestoreUndo: () => void;
  canUndo: boolean;
}

export const BackupsPanel: React.FC<BackupsPanelProps> = ({ onRestoreUndo, canUndo }) => {
  const [backups, setBackups] = useState<BackupItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const fetchBackups = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/backups');
      if (res.ok) {
        const data = await res.json();
        setBackups(data.backups || []);
      }
    } catch (err) {
      console.error('Failed to load backups:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBackups();
  }, []);

  const handleRestore = async (id?: string) => {
    setLoading(true);
    setStatusMessage('Restoring backup...');
    try {
      const res = await fetch('/api/undo', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ backupId: id })
      });
      const data = await res.json();
      if (res.ok && data.success) {
        setStatusMessage(data.message || 'Restored successfully!');
        fetchBackups();
        onRestoreUndo();
      } else {
        setStatusMessage(data.error || 'Undo failed.');
      }
    } catch (err) {
      setStatusMessage('Error restoring file.');
    } finally {
      setLoading(false);
      setTimeout(() => setStatusMessage(null), 3000);
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#0b0c14] border-t border-purple-900/30 font-mono p-4 sm:p-6 max-w-4xl mx-auto overflow-y-auto">
      <div className="flex items-center justify-between pb-4 border-b border-purple-900/30">
        <div>
          <div className="flex items-center gap-2">
            <History className="w-5 h-5 text-indigo-400" />
            <h2 className="text-base font-bold text-gray-100">
              Snapshot Backups &amp; Undo System
            </h2>
          </div>
          <p className="text-xs text-gray-400 font-sans mt-1">
            GEMBOT automatically captures pre-modification snapshots in <code className="text-purple-300">.gembot/backups/</code> before any write or patch edit.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => handleRestore()}
            disabled={!canUndo || loading}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
              canUndo && !loading
                ? 'bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white shadow-lg shadow-purple-950/40'
                : 'opacity-40 cursor-not-allowed bg-gray-800 text-gray-500'
            }`}
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Undo Last Action (/undo)</span>
          </button>

          <button
            onClick={fetchBackups}
            disabled={loading}
            className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-gray-400 hover:text-gray-200 transition-colors"
            title="Refresh backups"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {statusMessage && (
        <div className="my-3 p-3 rounded-lg bg-purple-950/40 border border-purple-800/50 text-purple-200 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{statusMessage}</span>
        </div>
      )}

      {/* Backups List */}
      <div className="mt-4 space-y-2">
        {backups.length === 0 ? (
          <div className="p-8 text-center text-gray-500 text-xs font-sans bg-[#0e101a] rounded-xl border border-purple-900/20">
            No backup snapshots yet. When GEMBOT edits or overwrites files, snapshots will appear here with instant restore options.
          </div>
        ) : (
          backups.map((item) => (
            <div
              key={item.id}
              className="flex items-center justify-between p-3 rounded-lg bg-[#0e101a] border border-purple-900/30 hover:border-purple-700/50 transition-colors"
            >
              <div className="flex items-center gap-3 truncate">
                <FileCode className="w-4 h-4 text-pink-400 shrink-0" />
                <div className="truncate">
                  <div className="text-xs text-gray-200 font-semibold truncate">
                    {item.originalPath}
                  </div>
                  <div className="text-[10px] text-gray-500 font-sans">
                    {new Date(item.timestamp).toLocaleString()} · {item.size} bytes
                  </div>
                </div>
              </div>

              <button
                onClick={() => handleRestore(item.id)}
                disabled={loading}
                className="px-2.5 py-1 rounded text-xs bg-indigo-950/50 hover:bg-indigo-900/50 text-indigo-300 border border-indigo-800/40 transition-colors flex items-center gap-1 shrink-0"
              >
                <RotateCcw className="w-3 h-3" />
                <span>Restore Snapshot</span>
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
