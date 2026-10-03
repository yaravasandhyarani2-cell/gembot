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
  FilePlus
} from 'lucide-react';
import { WorkspaceFile } from '../types';

interface WorkspaceExplorerProps {
  onRefreshWorkspace: () => void;
  selectedFilePath?: string | null;
}

export const WorkspaceExplorer: React.FC<WorkspaceExplorerProps> = ({
  onRefreshWorkspace,
  selectedFilePath
}) => {
  const [files, setFiles] = useState<WorkspaceFile[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<WorkspaceFile | null>(null);
  const [fileContent, setFileContent] = useState<string>('');
  const [isEditing, setIsEditing] = useState(false);
  const [saveStatus, setSaveStatus] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const fetchFiles = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/workspace');
      if (res.ok) {
        const data = await res.json();
        setFiles(data.files || []);
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

  const renderTree = (items: WorkspaceFile[], depth = 0) => {
    return items.map((item) => (
      <div key={item.path}>
        <div 
          onClick={() => handleOpenFile(item)}
          className={`flex items-center gap-2 py-1.5 px-2 rounded-md cursor-pointer transition-colors text-xs font-mono ${
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
          {!item.isDir && (
            <span className="text-[10px] text-gray-500 shrink-0">
              {item.size < 1024 ? `${item.size} B` : `${(item.size / 1024).toFixed(1)} KB`}
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
    <div className="flex h-full bg-[#0b0c14] border-t border-purple-900/30 overflow-hidden font-mono">
      {/* File Tree Left Sidebar */}
      <div className="w-72 border-r border-purple-900/30 flex flex-col bg-[#0e101a] shrink-0">
        <div className="p-3 border-b border-purple-900/30 flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs font-semibold text-purple-300">
            <Folder className="w-4 h-4 text-purple-400" />
            <span>Sandbox Files</span>
          </div>
          <button
            onClick={() => { fetchFiles(); onRefreshWorkspace(); }}
            disabled={loading}
            className="p-1 rounded hover:bg-purple-950/40 text-gray-400 hover:text-purple-300 transition-colors"
            title="Refresh files"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-2 space-y-0.5">
          {files.length === 0 ? (
            <div className="p-4 text-center text-gray-500 text-xs font-sans">
              No files in workspace yet. Ask GEMBOT to create files or scaffold an app!
            </div>
          ) : (
            renderTree(files)
          )}
        </div>
      </div>

      {/* File Viewer / Editor Area */}
      <div className="flex-1 flex flex-col bg-[#0a0b12] overflow-hidden">
        {selectedFile ? (
          <>
            {/* Action Bar */}
            <div className="h-10 px-4 border-b border-purple-900/30 bg-[#0e101a] flex items-center justify-between text-xs">
              <div className="flex items-center gap-2 truncate">
                <FileCode className="w-4 h-4 text-pink-400 shrink-0" />
                <span className="font-semibold text-gray-200 truncate">{selectedFile.path}</span>
                <span className="text-[10px] text-gray-500">
                  ({fileContent.split('\n').length} lines)
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

            {/* Content Area */}
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
            <FileCode className="w-12 h-12 text-purple-900/50 mb-3" />
            <h3 className="text-sm font-semibold text-gray-400 mb-1">Select a File to Inspect</h3>
            <p className="text-xs text-gray-500 max-w-sm">
              Files created by GEMBOT (such as Chatbox-X components, package.json, or README.md) will be listed here.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
