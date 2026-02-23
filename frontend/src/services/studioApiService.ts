/** Studio API service — all /api/studio/* fetch calls */
import type { StudioProjectSummary, StudioProject, StudioVersion, StudioMockServerStatus, StudioApiSpec } from '../types/studio';

const BASE = '/api/studio';

/** Map snake_case backend response to camelCase frontend types */
function mapProject(raw: any): StudioProject {
  // Backend stores files as {path: content_string} or {path: {path, content, language}}
  // Frontend expects Record<string, StudioFile> where StudioFile = {path, content, language}
  const rawFiles = raw.files || {};
  const mappedFiles: Record<string, any> = {};
  for (const [path, value] of Object.entries(rawFiles)) {
    if (typeof value === 'string') {
      mappedFiles[path] = { path, content: value, language: guessLang(path) };
    } else if (value && typeof value === 'object') {
      const v = value as any;
      mappedFiles[path] = { path: v.path || path, content: v.content || '', language: v.language || guessLang(path) };
    }
  }

  return {
    id: raw.id,
    name: raw.name,
    description: raw.description || '',
    settings: raw.settings || {},
    files: mappedFiles,
    chatHistory: raw.chat_history || raw.chatHistory || [],
    currentVersion: raw.current_version ?? raw.currentVersion ?? 0,
    createdAt: raw.created_at || raw.createdAt || '',
    updatedAt: raw.updated_at || raw.updatedAt || '',
  };
}

function guessLang(path: string): string {
  const ext = path.split('.').pop()?.toLowerCase() || '';
  const m: Record<string, string> = {
    tsx: 'typescript', ts: 'typescript', jsx: 'javascript', js: 'javascript',
    css: 'css', html: 'html', json: 'json', py: 'python', md: 'markdown',
  };
  return m[ext] || 'text';
}

function mapProjectSummary(raw: any): StudioProjectSummary {
  return {
    id: raw.id,
    name: raw.name,
    description: raw.description || '',
    updatedAt: raw.updated_at || raw.updatedAt || '',
    fileCount: raw.file_count ?? raw.fileCount ?? 0,
    versionCount: raw.current_version ?? raw.versionCount ?? 0,
  };
}

function mapVersion(raw: any): StudioVersion {
  return {
    id: raw.id,
    projectId: raw.project_id || raw.projectId || '',
    versionNumber: raw.version_number ?? raw.versionNumber ?? 0,
    files: raw.files || {},
    message: raw.message || '',
    timestamp: raw.timestamp || '',
  };
}

// --- Streaming ---
export const streamStudio = async (
  projectId: string | null,
  prompt: string,
  files: Record<string, { path: string; content: string }>,
  chatHistory: any[],
  provider: 'gemini' | 'claude',
  model: string,
  mode: 'generate' | 'refine',
): Promise<ReadableStream<Uint8Array>> => {
  const response = await fetch(`${BASE}/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ project_id: projectId, prompt, files, chat_history: chatHistory, provider, model, mode }),
  });
  if (!response.ok || !response.body) {
    const err = await response.json().catch(() => ({ message: 'Studio stream failed' }));
    throw new Error(err.message || err.detail || 'Failed to get studio response');
  }
  return response.body;
};

// --- Project CRUD ---
export const createProject = async (name: string, description?: string): Promise<StudioProject> => {
  const res = await fetch(`${BASE}/projects`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, description }),
  });
  if (!res.ok) throw new Error((await res.json()).detail || 'Failed to create project');
  const raw = await res.json();
  return mapProject(raw);
};

export const listProjects = async (): Promise<StudioProjectSummary[]> => {
  const res = await fetch(`${BASE}/projects`);
  if (!res.ok) return [];
  const raw = await res.json();
  return (raw as any[]).map(mapProjectSummary);
};

export const getProject = async (id: string): Promise<StudioProject> => {
  const res = await fetch(`${BASE}/projects/${id}`);
  if (!res.ok) throw new Error((await res.json()).detail || 'Failed to load project');
  const raw = await res.json();
  return mapProject(raw);
};

export const updateProject = async (id: string, data: Partial<StudioProject>): Promise<StudioProject> => {
  const res = await fetch(`${BASE}/projects/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error((await res.json()).detail || 'Failed to update project');
  const raw = await res.json();
  return mapProject(raw);
};

export const deleteProject = async (id: string): Promise<void> => {
  const res = await fetch(`${BASE}/projects/${id}`, { method: 'DELETE' });
  if (!res.ok) throw new Error((await res.json()).detail || 'Failed to delete project');
};

// --- Versions ---
export const saveVersion = async (id: string, message?: string): Promise<StudioVersion> => {
  const res = await fetch(`${BASE}/projects/${id}/save`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
  });
  if (!res.ok) throw new Error((await res.json()).detail || 'Failed to save version');
  const raw = await res.json();
  return mapVersion(raw);
};

export const listVersions = async (id: string): Promise<StudioVersion[]> => {
  const res = await fetch(`${BASE}/projects/${id}/versions`);
  if (!res.ok) return [];
  const raw = await res.json();
  return (raw as any[]).map(mapVersion);
};

export const getVersion = async (id: string, ver: number): Promise<StudioVersion> => {
  const res = await fetch(`${BASE}/projects/${id}/versions/${ver}`);
  if (!res.ok) throw new Error((await res.json()).detail || 'Failed to load version');
  const raw = await res.json();
  return mapVersion(raw);
};

export const restoreVersion = async (id: string, ver: number): Promise<StudioProject> => {
  const res = await fetch(`${BASE}/projects/${id}/versions/${ver}/restore`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error((await res.json()).detail || 'Failed to restore version');
  const raw = await res.json();
  return mapProject(raw);
};

// --- Mock Server ---
export const startMockServer = async (id: string): Promise<StudioMockServerStatus> => {
  const res = await fetch(`${BASE}/projects/${id}/mock/start`, { method: 'POST' });
  if (!res.ok) throw new Error((await res.json()).detail || 'Failed to start mock server');
  return res.json();
};

export const stopMockServer = async (id: string): Promise<void> => {
  await fetch(`${BASE}/projects/${id}/mock/stop`, { method: 'POST' });
};

export const getMockServerStatus = async (id: string): Promise<StudioMockServerStatus> => {
  const res = await fetch(`${BASE}/projects/${id}/mock/status`);
  if (!res.ok) return { running: false };
  return res.json();
};

export const updateMockServer = async (id: string): Promise<StudioMockServerStatus> => {
  const res = await fetch(`${BASE}/projects/${id}/mock/update`, { method: 'POST' });
  if (!res.ok) throw new Error((await res.json()).detail || 'Failed to update mock server');
  return res.json();
};

// --- API Spec & Types ---
export const getApiSpec = async (id: string): Promise<StudioApiSpec | null> => {
  const res = await fetch(`${BASE}/projects/${id}/api-spec`);
  if (!res.ok) return null;
  return res.json();
};

export const getGeneratedTypes = async (id: string): Promise<string> => {
  const res = await fetch(`${BASE}/projects/${id}/types`);
  if (!res.ok) return '';
  const data = await res.json();
  return data.types || '';
};

// --- Export ---
export const exportProject = async (id: string, scope: 'frontend' | 'fullstack' = 'fullstack'): Promise<Blob> => {
  const res = await fetch(`${BASE}/projects/${id}/export?scope=${scope}`);
  if (!res.ok) throw new Error('Failed to export project');
  return res.blob();
};
