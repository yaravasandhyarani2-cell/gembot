import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { AgentTerminal } from './components/AgentTerminal';
import { WorkspaceExplorer } from './components/WorkspaceExplorer';
import { BackupsPanel } from './components/BackupsPanel';
import { DiagnosticsPanel } from './components/DiagnosticsPanel';
import { ToolsModal } from './components/ToolsModal';
import { HelpModal } from './components/HelpModal';
import { ModelSelectModal } from './components/ModelSelectModal';
import { ChatMessage, AgentConfig, ToolCallItem } from './types';

const INITIAL_MESSAGE: ChatMessage = {
  id: 'init-1',
  role: 'assistant',
  content: "Hello! I am **GEMBOT**, an autonomous AI coding, desktop, and web automation assistant. What would you like to build, debug, or automate today?\n\nTip: Type `/help` for commands, `/tools` to see all 30 tools, or click one of the quick starters below.",
  timestamp: Date.now()
};

export default function App() {
  const [activeTab, setActiveTab] = useState<'terminal' | 'workspace' | 'backups' | 'diagnostics'>('terminal');
  const [messages, setMessages] = useState<ChatMessage[]>([INITIAL_MESSAGE]);
  const [isRunning, setIsRunning] = useState(false);
  const [canUndo, setCanUndo] = useState(false);
  const [selectedFilePath, setSelectedFilePath] = useState<string | null>(null);

  const [config, setConfig] = useState<AgentConfig>({
    model: 'gemini-2.5-flash',
    fallback_model: 'qwen2.5-coder:3b',
    max_steps: 50,
    max_output: 25000,
    command_timeout: 120,
    auto_confirm: false,
    blocked_commands: [
      'format',
      'rmdir /s /q c:\\',
      'rmdir /s /q c:/',
      'del /f /s /q c:\\',
      'del /f /s /q c:/',
      'diskpart',
      'shutdown',
      'taskkill /f /im explorer.exe',
      'bcdedit',
      'reg delete hk'
    ]
  });

  const [pendingConfirmation, setPendingConfirmation] = useState<{ id: string; actionDesc: string } | null>(null);
  const [isToolsOpen, setIsToolsOpen] = useState(false);
  const [isHelpOpen, setIsHelpOpen] = useState(false);
  const [isModelSelectOpen, setIsModelSelectOpen] = useState(false);

  // Load config on mount
  useEffect(() => {
    fetch('/api/config')
      .then(res => res.json())
      .then(data => {
        if (data.config) setConfig(data.config);
      })
      .catch(() => {});

    checkCanUndo();
  }, []);

  const checkCanUndo = async () => {
    try {
      const res = await fetch('/api/backups');
      if (res.ok) {
        const data = await res.json();
        setCanUndo((data.backups || []).length > 0);
      }
    } catch (e) {}
  };

  const handleToggleAutoConfirm = async () => {
    const nextVal = !config.auto_confirm;
    const updated = { ...config, auto_confirm: nextVal };
    setConfig(updated);
    try {
      await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ auto_confirm: nextVal })
      });
      setMessages(prev => [
        ...prev,
        {
          id: `sys-${Date.now()}`,
          role: 'system',
          content: `Safety Gate confirmation is now **${nextVal ? 'BYPASSED (/auto on)' : 'ACTIVE (/auto off)'}**.`,
          timestamp: Date.now()
        }
      ]);
    } catch (e) {}
  };

  const handleSelectModel = async (modelName: string) => {
    const updated = { ...config, model: modelName };
    setConfig(updated);
    try {
      await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model: modelName })
      });
      setMessages(prev => [
        ...prev,
        {
          id: `sys-${Date.now()}`,
          role: 'system',
          content: `Active model switched to **${modelName}**.`,
          timestamp: Date.now()
        }
      ]);
    } catch (e) {}
  };

  const handleClear = () => {
    setMessages([INITIAL_MESSAGE]);
  };

  const handleUndo = async () => {
    try {
      const res = await fetch('/api/undo', { method: 'POST' });
      const data = await res.json();
      if (res.ok && data.success) {
        setMessages(prev => [
          ...prev,
          {
            id: `undo-${Date.now()}`,
            role: 'system',
            content: `⏪ **[UNDO SUCCESS]**: ${data.message}`,
            timestamp: Date.now()
          }
        ]);
        checkCanUndo();
      } else {
        setMessages(prev => [
          ...prev,
          {
            id: `undo-${Date.now()}`,
            role: 'system',
            content: `❌ **[UNDO FAILED]**: ${data.error || 'No backups available'}`,
            timestamp: Date.now()
          }
        ]);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleSendMessage = async (text: string) => {
    // Check for client-side slash commands
    const trimmed = text.trim();
    if (trimmed === '/clear') {
      handleClear();
      return;
    }
    if (trimmed === '/tools') {
      setIsToolsOpen(true);
      return;
    }
    if (trimmed === '/help') {
      setIsHelpOpen(true);
      return;
    }
    if (trimmed === '/models' || trimmed.startsWith('/models')) {
      const parts = trimmed.split(/\s+/);
      if (parts[1]) {
        handleSelectModel(parts[1]);
      } else {
        setIsModelSelectOpen(true);
      }
      return;
    }
    if (trimmed === '/auto on') {
      if (!config.auto_confirm) handleToggleAutoConfirm();
      return;
    }
    if (trimmed === '/auto off') {
      if (config.auto_confirm) handleToggleAutoConfirm();
      return;
    }
    if (trimmed === '/undo') {
      handleUndo();
      return;
    }

    if (trimmed === '/dir' || trimmed === '/pwd' || trimmed.startsWith('/dir ') || trimmed.startsWith('/cd ')) {
      const parts = trimmed.split(/\s+/, 2);
      const cmd = parts[0];
      const targetPath = parts[1];

      if (targetPath) {
        // Change working directory
        try {
          const res = await fetch('/api/directory', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: targetPath, create: true })
          });
          const data = await res.json();
          if (res.ok) {
            setMessages(prev => [
              ...prev,
              {
                id: `usr-${Date.now()}`,
                role: 'user',
                content: text,
                timestamp: Date.now()
              },
              {
                id: `sys-${Date.now()}`,
                role: 'assistant',
                content: `📂 **[LOCAL DIRECTORY POINTER]**: Working folder switched to:\n\`${data.currentDirectory}\`\n\nSubfolders: ${data.subdirectories?.length ? data.subdirectories.join(', ') : '*(none)*'}`,
                timestamp: Date.now()
              }
            ]);
            return;
          }
        } catch (e) {}
      } else {
        // Inspect active directory
        try {
          const [dirRes, workRes] = await Promise.all([
            fetch('/api/directory'),
            fetch('/api/workspace')
          ]);
          const dirData = await dirRes.json();
          const workData = await workRes.json();

          const fileList: string[] = [];
          const traverse = (items: any[], p = '') => {
            for (const item of items) {
              if (item.isDir) {
                if (item.children) traverse(item.children, p ? `${p}/${item.name}` : item.name);
              } else {
                fileList.push(p ? `${p}/${item.name}` : item.name);
              }
            }
          };
          if (workData.files) traverse(workData.files);

          const summary = `### 📂 Active File Directory Pointer\n\n` +
            `* **Local Folder Path:** \`${dirData.currentDirectory}\`\n` +
            `* **Folder Name:** \`${dirData.currentFolderName}\`\n` +
            `* **Parent Directory:** \`${dirData.parentDirectory}\`\n` +
            `* **Subdirectories:** ${dirData.subdirectories?.length ? dirData.subdirectories.map((s: string) => `\`${s}\``).join(', ') : '*(none)*'}\n\n` +
            `**Files Located in Directory (${fileList.length}):**\n` +
            (fileList.length ? fileList.map(f => `- \`${f}\``).join('\n') : '*(Directory is currently empty)*') +
            `\n\n*Tip: Type \`/cd <folder>\` or click "Point to Path" in the top bar to switch active directory.*`;

          setMessages(prev => [
            ...prev,
            {
              id: `usr-${Date.now()}`,
              role: 'user',
              content: text,
              timestamp: Date.now()
            },
            {
              id: `sys-${Date.now()}`,
              role: 'assistant',
              content: summary,
              timestamp: Date.now()
            }
          ]);
          return;
        } catch (e) {}
      }
    }

    const userMsg: ChatMessage = {
      id: `usr-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: Date.now()
    };

    setMessages(prev => [...prev, userMsg]);
    setIsRunning(true);

    const assistantMsgId = `asst-${Date.now()}`;
    const initialAssistantMsg: ChatMessage = {
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      toolCalls: [],
      timestamp: Date.now()
    };
    setMessages(prev => [...prev, initialAssistantMsg]);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: text,
          history: messages.map(m => ({ role: m.role, content: m.content })),
          config
        })
      });

      if (!response.ok || !response.body) {
        throw new Error(`Server returned error ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const jsonStr = line.slice(6).trim();
          if (!jsonStr || jsonStr === '[DONE]') continue;

          try {
            const event = JSON.parse(jsonStr);

            if (event.type === 'token') {
              setMessages(prev => prev.map(m => {
                if (m.id === assistantMsgId) {
                  return { ...m, content: m.content + event.text };
                }
                return m;
              }));
            } else if (event.type === 'tool_start') {
              const newTool: ToolCallItem = {
                id: event.toolId,
                name: event.name,
                args: event.args || {},
                status: 'running',
                timestamp: Date.now()
              };
              setMessages(prev => prev.map(m => {
                if (m.id === assistantMsgId) {
                  return {
                    ...m,
                    toolCalls: [...(m.toolCalls || []), newTool]
                  };
                }
                return m;
              }));
            } else if (event.type === 'tool_end') {
              setMessages(prev => prev.map(m => {
                if (m.id === assistantMsgId) {
                  const updatedCalls = (m.toolCalls || []).map(tc => {
                    if (tc.id === event.toolId) {
                      return {
                        ...tc,
                        status: (event.error ? 'error' : 'completed') as 'error' | 'completed',
                        result: event.result,
                        error: event.error
                      };
                    }
                    return tc;
                  });
                  return { ...m, toolCalls: updatedCalls };
                }
                return m;
              }));
              checkCanUndo();
            } else if (event.type === 'confirmation_needed') {
              setPendingConfirmation({
                id: event.actionId,
                actionDesc: event.actionDesc
              });
            } else if (event.type === 'step') {
              setMessages(prev => prev.map(m => {
                if (m.id === assistantMsgId) {
                  return {
                    ...m,
                    stepInfo: { current: event.step, max: event.maxSteps }
                  };
                }
                return m;
              }));
            }
          } catch (err) {
            console.error('Error parsing SSE event:', err);
          }
        }
      }
    } catch (err: any) {
      setMessages(prev => prev.map(m => {
        if (m.id === assistantMsgId) {
          return {
            ...m,
            content: (m.content ? m.content + '\n\n' : '') + `⚠️ [Execution Error]: ${err.message || 'Network error'}`
          };
        }
        return m;
      }));
    } finally {
      setIsRunning(false);
      checkCanUndo();
    }
  };

  const handleStop = async () => {
    try {
      await fetch('/api/stop', { method: 'POST' });
    } catch (e) {}
    setIsRunning(false);
  };

  const handleConfirmAction = async (actionId: string, proceed: boolean) => {
    setPendingConfirmation(null);
    try {
      await fetch('/api/confirm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ actionId, proceed })
      });
    } catch (e) {}
  };

  const handleOpenWorkspaceFile = (filePath: string) => {
    setSelectedFilePath(filePath);
    setActiveTab('workspace');
  };

  return (
    <div className="flex flex-col h-screen w-screen bg-[#090a10] text-gray-100 overflow-hidden select-none">
      <Header
        config={config}
        onToggleAutoConfirm={handleToggleAutoConfirm}
        onUndo={handleUndo}
        onClear={handleClear}
        onOpenHelp={() => setIsHelpOpen(true)}
        onOpenTools={() => setIsToolsOpen(true)}
        onOpenModelSelect={() => setIsModelSelectOpen(true)}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isRunning={isRunning}
        canUndo={canUndo}
      />

      <main className="flex-1 overflow-hidden relative">
        {activeTab === 'terminal' && (
          <AgentTerminal
            messages={messages}
            isRunning={isRunning}
            onSendMessage={handleSendMessage}
            onStop={handleStop}
            onConfirmAction={handleConfirmAction}
            pendingConfirmation={pendingConfirmation}
            config={config}
            onOpenWorkspaceFile={handleOpenWorkspaceFile}
            onDirectoryChange={() => checkCanUndo()}
          />
        )}

        {activeTab === 'workspace' && (
          <WorkspaceExplorer
            onRefreshWorkspace={checkCanUndo}
            selectedFilePath={selectedFilePath}
            onPointOutDirectory={(dir) => {
              setActiveTab('terminal');
              handleSendMessage('/dir');
            }}
          />
        )}

        {activeTab === 'backups' && (
          <BackupsPanel
            onRestoreUndo={checkCanUndo}
            canUndo={canUndo}
          />
        )}

        {activeTab === 'diagnostics' && (
          <DiagnosticsPanel />
        )}
      </main>

      {/* Modals */}
      <ToolsModal isOpen={isToolsOpen} onClose={() => setIsToolsOpen(false)} />
      <HelpModal 
        isOpen={isHelpOpen} 
        onClose={() => setIsHelpOpen(false)} 
        onSelectCommand={(cmd) => {
          if (cmd === '/tools') setIsToolsOpen(true);
          else if (cmd === '/models') setIsModelSelectOpen(true);
          else if (cmd === '/undo') handleUndo();
          else if (cmd === '/clear') handleClear();
          else if (cmd.startsWith('/auto')) handleToggleAutoConfirm();
        }}
      />
      <ModelSelectModal
        isOpen={isModelSelectOpen}
        onClose={() => setIsModelSelectOpen(false)}
        activeModel={config.model}
        onSelectModel={handleSelectModel}
      />
    </div>
  );
}
