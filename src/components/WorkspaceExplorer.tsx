import React, { useState, useEffect } from 'react';
import { 
  Folder, 
  File, 
  RefreshCw, 
  Download, 
  FileCode, 
  Save, 
  Trash2, 
  Eye, 
  Copy, 
  Check, 
  FolderPlus,
  FilePlus,
  Compass,
  CornerDownRight,
  ArrowUp,
  FolderInput
} from 'lucide-react';
import { WorkspaceFile } from '../types';

interface WorkspaceExplorerProps {
  onRefreshWorkspace: () => void;
  selectedFilePath?: string | null;
  onPointOutDirectory?: (path: string) => void;
}

export const WorkspaceExplorer: React.FC<WorkspaceExplorerProps> = ({
  onRefreshWorkspace,
  selectedFilePath,
  onPointOutDirectory
}) => {
  const [files, setFiles] = useState<WorkspaceFile[]>([]);
  const [rootPath, setRootPath] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<WorkspaceFile | null>(null);
  const [fileContent, setFileContent] = useState<string>('');
  const [isEditing, setIsEditing] = useState(false);
  const [saveStatus, setSaveStatus] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [copiedPath, setCopiedPath] = useState(false);
  const [isChangingDir, setIsChangingDir] = useState(false);
  const [newDirPath, setNewDirPath] = useState('');

  const fetchFiles = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/workspace');
      if (res.ok) {
        const data = await res.json();
        setFiles(data.files || []);
        if (data.root) setRootPath(data.root);
      }
    } catch (err) {
      console.error('Failed to load workspace files:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFiles();
  }, []);

  useEffect(() => {
    if (selectedFilePath && files.length > 0) {
      const findFile = (items: WorkspaceFile[]): WorkspaceFile | null => {
        for (const item of items) {
          if (item.path === selectedFilePath || item.path.endsWith(selectedFilePath)) return item;
          if (item.children) {
            const found = findFile(item.children);
            if (found) return found;
          }
        }
        return null;
      };
      const target = findFile(files);
      if (target) {
        handleOpenFile(target);
      }
    }
  }, [selectedFilePath, files]);

  const handleOpenFile = async (file: WorkspaceFile) => {
    if (file.isDir) return;
    setSelectedFile(file);
    setIsEditing(false);
    try {
      const res = await fetch(`/api/workspace/file?path=${encodeURIComponent(file.path)}`);
      if (res.ok) {
        const data = await res.json();
        setFileContent(data.content ?? '');
      }
    } catch (err) {
      setFileContent('Error loading file content.');
    }
  };

  const handleSaveFile = async () => {
    if (!selectedFile) return;
    setSaveStatus('Saving...');
    try {
      const res = await fetch('/api/workspace/file', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: selectedFile.path, content: fileContent })
      });
      if (res.ok) {
        setSaveStatus('Saved!');
        setTimeout(() => setSaveStatus(null), 2000);
        fetchFiles();
      } else {
        setSaveStatus('Save failed');
      }
    } catch (err) {
      setSaveStatus('Error');
    }
  };

  const handleDownload = () => {
    if (!selectedFile || !fileContent) return;
    const blob = new Blob([fileContent], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = selectedFile.name;
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleSwitchDir = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newDirPath.trim()) return;
    setLoading(true);
    try {
      const res = await fetch('/api/directory', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: newDirPath.trim(), create: true })
      });
      if (res.ok) {
        setIsChangingDir(false);
        fetchFiles();
        onRefreshWorkspace();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Count files & dirs recursively
  const countStats = (items: WorkspaceFile[]): { filesCount: number; dirsCount: number; totalBytes: number } => {
    let filesCount = 0;
    let dirsCount = 0;
    let totalBytes = 0;
    const traverse = (list: WorkspaceFile[]) => {
      for (const item of list) {
        if (item.isDir) {
          dirsCount++;
          if (item.children) traverse(item.children);
        } else {
          filesCount++;
          totalBytes += item.size || 0;
        }
      }
    };
    traverse(items);
    return { filesCount, dirsCount, totalBytes };
  };

  const { filesCount, dirsCount, totalBytes } = countStats(files);

  const renderTree = (items: WorkspaceFile[], depth = 0) => {
    return items.map((item) => (
      <div key={item.path}>
        <div 
          onClick={() => handleOpenFile(item)}
          className={`flex items-center gap-2 py-1.5 px-2 rounded-md cursor-pointer transition-colors text-xs font-mono group ${
            selectedFile?.path === item.path
              ? 'bg-purple-900/40 text-purple-200 border border-purple-700/50'
              : 'hover:bg-white/5 text-gray-300'
          }`}
          style={{ paddingLeft: `${depth * 14 + 8}px` }}
        >
          {item.isDir ? (
            <Folder className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
          ) : (
            <FileCode className="w-3.5 h-3.5 text-purple-400 shrink-0" />
          )}
          <span className="truncate flex-1">{item.name}</span>
          {!item.isDir ? (
            <span className="text-[10px] text-gray-500 shrink-0">
              {item.size < 1024 ? `${item.size} B` : `${(item.size / 1024).toFixed(1)} KB`}
            </span>
          ) : (
            <span className="text-[10px] text-indigo-400/80 px-1 rounded bg-indigo-950/60 shrink-0">
              DIR
            </span>
          )}
        </div>
        {item.isDir && item.children && item.children.length > 0 && (
          <div>{renderTree(item.children, depth + 1)}</div>
        )}
      </div>
    ));
  };

  return (
    <div className="flex flex-col h-full bg-[#0b0c14] border-t border-purple-900/30 overflow-hidden font-mono">
      {/* SECTION: File Directory Pointer & Local Folder Banner */}
      <div className="bg-[#101220] border-b border-purple-900/40 p-3 sm:px-4 flex flex-wrap items-center justify-between gap-3 shadow-md">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 p-0.5 flex items-center justify-center shrink-0 shadow">
            <div className="w-full h-full bg-[#0f111c] rounded-[7px] flex items-center justify-center">
              <Compass className="w-4 h-4 text-purple-300" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-gray-200 uppercase tracking-wider">
                File Directory Pointer
              </span>
              <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-indigo-950/80 text-indigo-300 border border-indigo-800/40">
                Active Local Folder
              </span>
            </div>
            <div className="flex items-center gap-1.5 text-xs text-purple-300/90 font-mono mt-0.5 truncate max-w-xl">
              <span className="truncate">{rootPath || 'Local Sandbox Workspace'}</span>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(rootPath);
                  setCopiedPath(true);
                  setTimeout(() => setCopiedPath(false), 2000);
                }}
                className="text-gray-400 hover:text-white shrink-0 ml-1"
                title="Copy full directory path"
              >
                {copiedPath ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              </button>
            </div>
          </div>
        </div>

        {/* Directory Stats & Action Buttons */}
        <div className="flex items-center gap-2">
          <div className="hidden md:flex items-center gap-2 text-[11px] text-gray-400 font-sans px-2.5 py-1 rounded bg-[#151829] border border-purple-900/30">
            <span><strong>{dirsCount}</strong> Folders</span>
            <span>·</span>
            <span><strong>{filesCount}</strong> Files</span>
            <span>·</span>
            <span><strong>{(totalBytes / 1024).toFixed(1)}</strong> KB</span>
          </div>

          <button
            onClick={() => setIsChangingDir(!isChangingDir)}
            className="px-2.5 py-1.5 rounded-lg bg-indigo-950/50 hover:bg-indigo-900/60 border border-indigo-800/50 text-indigo-300 text-xs font-semibold flex items-center gap-1.5 transition-colors"
            title="Set custom local directory to work on"
          >
            <FolderInput className="w-3.5 h-3.5" />
            <span>Point Local Folder</span>
          </button>

          {onPointOutDirectory && (
            <button
              onClick={() => onPointOutDirectory(rootPath)}
              className="px-2.5 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors shadow"
              title="Point out this directory structure in agent terminal"
            >
              <Compass className="w-3.5 h-3.5" />
              <span>Inspect in Console</span>
            </button>
          )}

          <button
            onClick={() => { fetchFiles(); onRefreshWorkspace(); }}
            disabled={loading}
            className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-gray-400 hover:text-white transition-colors"
            title="Refresh directory files"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Directory switch input modal/panel */}
      {isChangingDir && (
        <form onSubmit={handleSwitchDir} className="bg-[#14172a] p-3 border-b border-indigo-500/40 flex items-center gap-2">
          <div className="text-xs text-indigo-300 font-semibold shrink-0">
            Set Working Folder:
          </div>
          <input
            type="text"
            placeholder="e.g. C:\Users\Subhash\Desktop\test or ./chatbox-x"
            value={newDirPath}
            onChange={(e) => setNewDirPath(e.target.value)}
            className="flex-1 bg-[#0b0c16] border border-indigo-600/60 rounded px-3 py-1.5 text-xs text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-indigo-400 font-mono"
            autoFocus
          />
          <button
            type="submit"
            disabled={loading}
            className="px-3 py-1.5 rounded bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shrink-0"
          >
            Apply Folder
          </button>
          <button
            type="button"
            onClick={() => setIsChangingDir(false)}
            className="px-2.5 py-1.5 rounded hover:bg-white/10 text-gray-400 text-xs"
          >
            Cancel
          </button>
        </form>
      )}

      {/* Main Workspace Split: File Tree Left & File Viewer Right */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Tree Sidebar */}
        <div className="w-72 border-r border-purple-900/30 flex flex-col bg-[#0e101a] shrink-0">
          <div className="p-3 border-b border-purple-900/30 flex items-center justify-between text-xs">
            <span className="font-semibold text-gray-300 flex items-center gap-1.5">
              <Folder className="w-4 h-4 text-purple-400" />
              <span>Project Directory Tree</span>
            </span>
            <span className="text-[10px] text-gray-500">
              {files.length} top-level
            </span>
          </div>

          <div className="flex-1 overflow-y-auto p-2 space-y-0.5">
            {files.length === 0 ? (
              <div className="p-6 text-center text-gray-500 text-xs font-sans">
                Directory is currently empty. Ask GEMBOT to scaffold a project or create files.
              </div>
            ) : (
              renderTree(files)
            )}
          </div>
        </div>

        {/* Right Viewer / Editor Area */}
        <div className="flex-1 flex flex-col bg-[#0a0b12] overflow-hidden">
          {selectedFile ? (
            <>
              {/* File Action Bar */}
              <div className="h-10 px-4 border-b border-purple-900/30 bg-[#0e101a] flex items-center justify-between text-xs">
                <div className="flex items-center gap-2 truncate">
                  <FileCode className="w-4 h-4 text-pink-400 shrink-0" />
                  <span className="font-semibold text-gray-200 truncate">{selectedFile.path}</span>
                  <span className="text-[10px] text-gray-500">
                    ({fileContent.split('\n').length} lines · {selectedFile.size} bytes)
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  {saveStatus && (
                    <span className="text-[11px] text-purple-300 animate-pulse">{saveStatus}</span>
                  )}

                  <button
                    onClick={() => setIsEditing(!isEditing)}
                    className={`px-2.5 py-1 rounded text-xs transition-colors flex items-center gap-1 ${
                      isEditing 
                        ? 'bg-purple-900/50 text-purple-200 border border-purple-700/60' 
                        : 'hover:bg-white/5 text-gray-400 hover:text-gray-200'
                    }`}
                  >
                    <Eye className="w-3.5 h-3.5" />
                    <span>{isEditing ? 'Editing' : 'View'}</span>
                  </button>

                  {isEditing && (
                    <button
                      onClick={handleSaveFile}
                      className="px-2.5 py-1 rounded text-xs bg-emerald-600 hover:bg-emerald-500 text-white font-medium flex items-center gap-1 transition-colors"
                    >
                      <Save className="w-3.5 h-3.5" />
                      <span>Save</span>
                    </button>
                  )}

                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(fileContent);
                      setCopied(true);
                      setTimeout(() => setCopied(false), 2000);
                    }}
                    className="p-1.5 rounded hover:bg-white/5 text-gray-400 hover:text-gray-200"
                    title="Copy file content"
                  >
                    {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>

                  <button
                    onClick={handleDownload}
                    className="p-1.5 rounded hover:bg-white/5 text-gray-400 hover:text-gray-200"
                    title="Download file"
                  >
                    <Download className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {/* Content Editor */}
              <div className="flex-1 overflow-auto p-4 bg-[#080910]">
                {isEditing ? (
                  <textarea
                    value={fileContent}
                    onChange={(e) => setFileContent(e.target.value)}
                    className="w-full h-full bg-transparent text-gray-200 font-mono text-xs focus:outline-none resize-none leading-relaxed"
                    spellCheck={false}
                  />
                ) : (
                  <pre className="text-gray-300 font-mono text-xs whitespace-pre leading-relaxed select-text">
                    {fileContent || <span className="text-gray-600">(Empty file)</span>}
                  </pre>
                )}
              </div>
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-gray-500 p-6 text-center font-sans">
              <Folder className="w-12 h-12 text-purple-900/40 mb-3" />
              <h3 className="text-sm font-semibold text-gray-400 mb-1">Active File Directory Pointer</h3>
              <p className="text-xs text-gray-500 max-w-md font-mono text-[11px] mb-2">
                Currently pointing to: <code className="text-purple-300">{rootPath || './workspace'}</code>
              </p>
              <p className="text-xs text-gray-500 max-w-sm">
                Click on any file in the left directory tree to inspect, edit, or download code.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
