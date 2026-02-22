import { Message, Persona, CustomAiStyle, Project, ProjectFile } from '../types/index';

const BASE = '/api';

// --- Chat Streaming ---
export const streamChat = async (
  messages: Message[],
  provider: 'gemini' | 'claude',
  model: string,
  persona?: Persona,
  customStyles?: CustomAiStyle[],
  useWebSearch?: boolean,
  thinkingBudget?: number,
): Promise<ReadableStream<Uint8Array>> => {
  const response = await fetch(`${BASE}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages, provider, model, persona, customStyles, useWebSearch, thinkingBudget }),
  });
  if (!response.ok || !response.body) {
    const err = await response.json().catch(() => ({ message: 'Stream failed' }));
    throw new Error(err.message || 'Failed to get streaming response');
  }
  return response.body;
};

// --- Coding Chat Streaming ---
export const streamCoding = async (
  history: Message[],
  projects: Project[],
  persona: Persona,
  provider: 'gemini' | 'claude',
  model: string,
  useWebSearch: boolean,
  customStyles: CustomAiStyle[],
  thinkingBudget?: number,
): Promise<ReadableStream<Uint8Array>> => {
  const response = await fetch(`${BASE}/coding/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ history, projects, persona, customStyles, useWebSearch, provider, model, thinkingBudget }),
  });
  if (!response.ok || !response.body) {
    const err = await response.json().catch(() => ({ message: 'Coding stream failed' }));
    throw new Error(err.message || 'Failed to get coding response');
  }
  return response.body;
};

// --- Image Editing ---
export const editImage = async (prompt: string, file: File): Promise<any[]> => {
  const formData = new FormData();
  formData.append('prompt', prompt);
  formData.append('file', file);
  const response = await fetch(`${BASE}/image/edit`, { method: 'POST', body: formData });
  if (!response.ok) throw new Error((await response.json()).message || 'Image edit failed');
  return response.json();
};

// --- Video Generation ---
export const generateVideo = async (prompt: string, file: File | null, updateStatus: (s: string) => void): Promise<any[]> => {
  updateStatus('Sending to Veo...');
  const formData = new FormData();
  formData.append('prompt', prompt);
  if (file) formData.append('file', file);
  const initRes = await fetch(`${BASE}/video/generate`, { method: 'POST', body: formData });
  if (!initRes.ok) throw new Error((await initRes.json()).message || 'Video generation failed');
  const { operationName } = await initRes.json();
  updateStatus('Generating video...');
  while (true) {
    await new Promise(r => setTimeout(r, 10000));
    const statusRes = await fetch(`${BASE}/video/status?operationName=${operationName}`);
    if (!statusRes.ok) throw new Error('Status check failed');
    const result = await statusRes.json();
    if (result.done) {
      if (result.error) throw new Error(result.error);
      return [{ videoUrl: result.videoUrl }];
    }
  }
};

// --- Agents ---
export const listAgents = async () => {
  const res = await fetch(`${BASE}/agents`);
  return res.json();
};

export const runAgent = async (name: string, workload: any) => {
  const res = await fetch(`${BASE}/agents/${name}/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ workload }),
  });
  return res.json();
};

export const getAgentExample = async (name: string) => {
  const res = await fetch(`${BASE}/agents/${name}/example`);
  return res.json();
};

export const runPipeline = async (steps: any[]) => {
  const res = await fetch(`${BASE}/pipelines/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ steps }),
  });
  return res.json();
};

// --- Playbooks ---
export const listPlaybooks = async () => {
  const res = await fetch(`${BASE}/playbooks`);
  return res.json();
};

export const searchPlaybooks = async (q: string, category?: string) => {
  const params = new URLSearchParams({ q });
  if (category) params.set('category', category);
  const res = await fetch(`${BASE}/playbooks/search?${params}`);
  return res.json();
};

export const getPlaybook = async (filename: string) => {
  const res = await fetch(`${BASE}/playbooks/${filename}`);
  return res.json();
};

export const listPlaybookCategories = async () => {
  const res = await fetch(`${BASE}/playbooks/categories`);
  return res.json();
};

// --- Workflows ---
export const listWorkflowTemplates = async () => {
  const res = await fetch(`${BASE}/workflows/templates`);
  return res.json();
};

export const planWorkflow = async (goal: string, template?: string) => {
  const res = await fetch(`${BASE}/workflows/plan`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ goal, template }),
  });
  return res.json();
};

export const streamWorkflowExecution = async (steps: any[], goal: string): Promise<ReadableStream<Uint8Array>> => {
  const res = await fetch(`${BASE}/workflows/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ steps, goal }),
  });
  if (!res.ok || !res.body) throw new Error('Workflow execution failed');
  return res.body;
};

// --- Builder ---
export const generateWebAppPlan = async (idea: string, provider?: string, model?: string) => {
  const res = await fetch(`${BASE}/builder/plan`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ idea, provider, model }),
  });
  if (!res.ok) throw new Error((await res.json()).message || 'Plan generation failed');
  return res.json();
};

export const generateWebAppCode = async (plan: any, theme: any, provider?: string, model?: string): Promise<Record<string, string>> => {
  const res = await fetch(`${BASE}/builder/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ plan, theme, provider, model }),
  });
  if (!res.ok) throw new Error((await res.json()).message || 'Code generation failed');
  return res.json();
};

// --- Models ---
export const listModels = async () => {
  const res = await fetch(`${BASE}/models`);
  return res.json();
};

// --- Mode & Interchange ---
export const getMode = async () => {
  const res = await fetch(`${BASE}/mode`);
  return res.json();
};

export const setMode = async (mode: 'standalone' | 'claude-code') => {
  const res = await fetch(`${BASE}/mode`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ mode }),
  });
  return res.json();
};

export const exportWorkspace = async (data: any) => {
  const res = await fetch(`${BASE}/export`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return res.json();
};

export const importWorkspace = async (data: any) => {
  const res = await fetch(`${BASE}/import`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return res.json();
};

// --- Health ---
export const healthCheck = async () => {
  const res = await fetch(`${BASE}/health`);
  return res.json();
};

// --- API Key Configuration ---
export const getKeysStatus = async (): Promise<{ gemini: boolean; anthropic: boolean; mode: string }> => {
  const res = await fetch(`${BASE}/config/keys/status`);
  return res.json();
};

export const setApiKeys = async (geminiKey?: string, anthropicKey?: string) => {
  const body: Record<string, string> = {};
  if (geminiKey) body.gemini_key = geminiKey;
  if (anthropicKey) body.anthropic_key = anthropicKey;
  const res = await fetch(`${BASE}/config/keys`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error((await res.json()).error || 'Failed to set keys');
  return res.json();
};
