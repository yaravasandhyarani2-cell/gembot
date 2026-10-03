export interface ToolCallItem {
  id: string;
  name: string;
  args: Record<string, any>;
  result?: string;
  status: 'running' | 'completed' | 'error' | 'awaiting_confirmation';
  error?: string;
  timestamp: number;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  toolCalls?: ToolCallItem[];
  timestamp: number;
  inferredFile?: string;
  stepInfo?: {
    current: number;
    max: number;
  };
}

export interface WorkspaceFile {
  name: string;
  path: string;
  size: number;
  isDir: boolean;
  modified: number;
  children?: WorkspaceFile[];
}

export interface BackupItem {
  id: string;
  originalPath: string;
  backupPath: string;
  timestamp: number;
  size: number;
}

export interface SystemStats {
  os: string;
  platform: string;
  arch: string;
  cpuUsage: number;
  ramUsed: number;
  ramTotal: number;
  ramPercent: number;
  uptime: number;
  workspaceItems: number;
  processes: {
    pid: number;
    name: string;
    cpu: number;
    mem: number;
  }[];
}

export interface AgentConfig {
  model: string;
  fallback_model: string;
  max_steps: number;
  max_output: number;
  command_timeout: number;
  auto_confirm: boolean;
  blocked_commands: string[];
}
