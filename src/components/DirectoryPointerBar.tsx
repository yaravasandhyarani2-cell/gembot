import React, { useState, useEffect } from 'react';
import { 
  Folder, 
  FolderTree, 
  ChevronRight, 
  ArrowUp, 
  Copy, 
  Check, 
  CornerDownRight, 
  FolderInput, 
  Compass, 
  RefreshCw,
  FolderPlus,
  ExternalLink,
  Download
} from 'lucide-react';
import { BorderBeam } from 'border-beam';

interface DirectoryPointerBarProps {
  onDirectoryChange?: (newPath: string) => void;
  onPointOutDirectory?: (dirPath: string) => void;
}

interface DirectoryInfo {
  currentDirectory: string;
  currentFolderName: string;
  parentDirectory: string;
  subdirectories: string[];
  exists: boolean;
}

export const DirectoryPointerBar: React.FC<DirectoryPointerBarProps> = ({
  onDirectoryChange,
  onPointOutDirectory
}) => {
  const [dirInfo, setDirInfo] = useState<DirectoryInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [customPath, setCustomPath] = useState('');
  const [copied, setCopied] = useState(false);
  const [showSubfolders, setShowSubfolders] = useState(false);

  const fetchDirectory = async () => {
    try {
      const res = await fetch('/api/directory');
      if (res.ok) {
        const data = await res.json();
        setDirInfo(data);
        setCustomPath(data.currentDirectory);
      }
    } catch (err) {
      console.error('Failed to load directory info:', err);
    }
  };

  useEffect(() => {
    fetchDirectory();
  }, []);

  const handleSwitchDirectory = async (newPath: string) => {
    if (!newPath.trim()) return;
    setLoading(true);
    try {
      const res = await fetch('/api/directory', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: newPath.trim(), create: true })
      });
      if (res.ok) {
        const data = await res.json();
        setDirInfo(data);
        setCustomPath(data.currentDirectory);
        setIsEditing(false);
        if (onDirectoryChange) onDirectoryChange(data.currentDirectory);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCopyPath = () => {
    if (!dirInfo?.currentDirectory) return;
    navigator.clipboard.writeText(dirInfo.currentDirectory);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const breadcrumbs = dirInfo?.currentDirectory 
    ? dirInfo.currentDirectory.replace(/\\/g, '/').split('/').filter(Boolean)
    : [];

  return (
    <div className="bg-[#0e101a] border-b border-purple-900/40 px-4 py-2 flex flex-wrap items-center justify-between gap-3 text-xs font-mono">
      {/* Current Directory & Breadcrumbs */}
      <div className="flex items-center gap-2 flex-1 min-w-[280px]">
        <div className="flex items-center gap-1.5 px-2 py-1 rounded bg-purple-950/60 border border-purple-800/40 text-purple-300 font-semibold shrink-0">
          <Folder className="w-3.5 h-3.5 text-pink-400" />
          <span className="hidden sm:inline">Active Folder:</span>
        </div>

        {isEditing ? (
          <form 
            onSubmit={(e) => { e.preventDefault(); handleSwitchDirectory(customPath); }}
            className="flex items-center gap-1.5 flex-1"
          >
            <input
              type="text"
              value={customPath}
              onChange={(e) => setCustomPath(e.target.value)}
              placeholder="e.g. C:\Users\Subhash\Desktop\test\chatbox-x or ./chatbox-x"
              className="flex-1 bg-[#141727] border border-purple-600/70 rounded px-2.5 py-1 text-xs text-gray-100 focus:outline-none focus:ring-1 focus:ring-purple-400"
              autoFocus
            />
            <button
              type="submit"
              disabled={loading}
              className="px-2.5 py-1 rounded bg-purple-600 hover:bg-purple-500 text-white font-medium text-xs transition-colors shrink-0"
            >
              Point Here
            </button>
            <button
              type="button"
              onClick={() => setIsEditing(false)}
              className="px-2 py-1 rounded hover:bg-white/10 text-gray-400 text-xs"
            >
              Cancel
            </button>
          </form>
        ) : (
          <div className="flex items-center gap-1 overflow-x-auto py-0.5 max-w-xl">
            {breadcrumbs.length > 0 ? (
              breadcrumbs.map((segment, idx) => {
                const isLast = idx === breadcrumbs.length - 1;
                return (
                  <React.Fragment key={idx}>
                    <button
                      onClick={() => {
                        const pathSlice = '/' + breadcrumbs.slice(0, idx + 1).join('/');
                        handleSwitchDirectory(pathSlice);
                      }}
                      className={`hover:underline transition-colors truncate max-w-[120px] ${
                        isLast 
                          ? 'font-bold text-gray-100 bg-purple-900/30 px-1.5 py-0.5 rounded border border-purple-700/50' 
                          : 'text-gray-400 hover:text-purple-300'
                      }`}
                      title={segment}
                    >
                      {segment}
                    </button>
                    {!isLast && <ChevronRight className="w-3 h-3 text-gray-600 shrink-0" />}
                  </React.Fragment>
                );
              })
            ) : (
              <span className="text-gray-400 truncate">{dirInfo?.currentDirectory || 'workspace'}</span>
            )}
          </div>
        )}
      </div>

      {/* Directory Pointer Actions */}
      <div className="flex items-center gap-1.5 shrink-0">
        <button
          onClick={() => setIsEditing(!isEditing)}
          className="px-2.5 py-1 rounded bg-white/5 hover:bg-purple-950/40 border border-purple-900/40 text-gray-300 hover:text-purple-300 transition-colors flex items-center gap-1"
          title="Switch active directory"
        >
          <FolderInput className="w-3.5 h-3.5 text-indigo-400" />
          <span>Point to Path</span>
        </button>

        <a
          href="/api/workspace/download-zip"
          download="chatbox-x-project.zip"
          className="px-2.5 py-1 rounded bg-emerald-950/60 hover:bg-emerald-900/70 border border-emerald-800/40 text-emerald-300 font-semibold text-xs transition-colors flex items-center gap-1"
          title="Download workspace files as ZIP"
        >
          <Download className="w-3.5 h-3.5" />
          <span>Download ZIP</span>
        </a>

        {dirInfo?.parentDirectory && (
          <button
            onClick={() => handleSwitchDirectory(dirInfo.parentDirectory)}
            disabled={loading}
            className="p-1 rounded bg-white/5 hover:bg-white/10 text-gray-400 hover:text-gray-200 transition-colors"
            title="Go to parent directory (cd ..)"
          >
            <ArrowUp className="w-3.5 h-3.5" />
          </button>
        )}

        <button
          onClick={handleCopyPath}
          className="p-1 rounded bg-white/5 hover:bg-white/10 text-gray-400 hover:text-gray-200 transition-colors"
          title="Copy absolute folder path"
        >
          {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
        </button>

        {onPointOutDirectory && (
          <button
            onClick={() => onPointOutDirectory(dirInfo?.currentDirectory || '')}
            className="px-2.5 py-1 rounded bg-gradient-to-r from-purple-700 to-pink-700 hover:from-purple-600 hover:to-pink-600 text-white font-medium shadow transition-all flex items-center gap-1.5"
            title="Point out file directory structure in console"
          >
            <Compass className="w-3.5 h-3.5" />
            <span>Point Out Directory</span>
          </button>
        )}

        {/* Subdirectories quick dropdown toggle */}
        {dirInfo && dirInfo.subdirectories && dirInfo.subdirectories.length > 0 && (
          <div className="relative">
            <button
              onClick={() => setShowSubfolders(!showSubfolders)}
              className="px-2 py-1 rounded bg-purple-950/40 hover:bg-purple-900/50 border border-purple-800/40 text-purple-300 text-[11px] flex items-center gap-1"
            >
              <span>{dirInfo.subdirectories.length} Subfolders</span>
              <CornerDownRight className="w-3 h-3" />
            </button>

            {showSubfolders && (
              <div className="absolute right-0 top-8 w-48 bg-[#141727] border border-purple-800/60 rounded-lg shadow-2xl p-1.5 z-40 space-y-1">
                <div className="text-[10px] text-gray-400 px-2 py-0.5 uppercase tracking-wider font-semibold">
                  Jump to Subfolder:
                </div>
                {dirInfo.subdirectories.map((sub) => (
                  <button
                    key={sub}
                    onClick={() => {
                      setShowSubfolders(false);
                      handleSwitchDirectory(`${dirInfo.currentDirectory}/${sub}`);
                    }}
                    className="w-full text-left px-2 py-1 rounded hover:bg-purple-900/40 text-xs text-gray-200 hover:text-white flex items-center gap-1.5 transition-colors truncate"
                  >
                    <Folder className="w-3 h-3 text-indigo-400 shrink-0" />
                    <span className="truncate">{sub}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
