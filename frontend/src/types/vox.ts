export interface VoxState {
  connected: boolean;
  mode: 'gemini' | 'claude' | null;
  voice: string;
  speaking: boolean;
  listening: boolean;
  turnCount: number;
  functionCount: number;
  sessionId: string | null;
  transcript: VoxTranscriptEntry[];
  functionLog: VoxFunctionEntry[];
  error: string | null;
  reconnecting: boolean;
}

export interface VoxTranscriptEntry {
  role: 'user' | 'model' | 'system';
  text: string;
  timestamp: number;
}

export interface VoxFunctionEntry {
  name: string;
  args: Record<string, any>;
  result?: any;
  serverHandled: boolean;
  timestamp: number;
  status: 'pending' | 'success' | 'error';
}

export interface VoxConfig {
  voice: string;
  model: string;
  systemPrompt: string;
}

export interface VoxVoice {
  id: string;
  name: string;
  gender: string;
  style: string;
}

export type VoxMode = 'gemini' | 'claude';
