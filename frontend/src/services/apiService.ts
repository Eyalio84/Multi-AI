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

// --- Knowledge Graph ---
export const listKGDatabases = async () => {
  const res = await fetch(`${BASE}/kg/databases`);
  return res.json();
};

export const getKGStats = async (dbId: string) => {
  const res = await fetch(`${BASE}/kg/databases/${dbId}/stats`);
  return res.json();
};

export const listKGNodes = async (dbId: string, nodeType?: string, search?: string, limit = 100, offset = 0) => {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  if (nodeType) params.set('node_type', nodeType);
  if (search) params.set('search', search);
  const res = await fetch(`${BASE}/kg/databases/${dbId}/nodes?${params}`);
  return res.json();
};

export const getKGNode = async (dbId: string, nodeId: string) => {
  const res = await fetch(`${BASE}/kg/databases/${dbId}/nodes/${nodeId}`);
  return res.json();
};

export const getKGNeighbors = async (dbId: string, nodeId: string, depth = 1, limit = 50) => {
  const res = await fetch(`${BASE}/kg/databases/${dbId}/nodes/${nodeId}/neighbors?depth=${depth}&limit=${limit}`);
  return res.json();
};

export const listKGEdges = async (dbId: string, edgeType?: string, limit = 100, offset = 0) => {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  if (edgeType) params.set('edge_type', edgeType);
  const res = await fetch(`${BASE}/kg/databases/${dbId}/edges?${params}`);
  return res.json();
};

export const getKGTypes = async (dbId: string) => {
  const res = await fetch(`${BASE}/kg/databases/${dbId}/types`);
  return res.json();
};

export const searchKG = async (dbId: string, query: string, mode = 'hybrid', limit = 20, alpha = 0.4, beta = 0.45, gamma = 0.15) => {
  const res = await fetch(`${BASE}/kg/databases/${dbId}/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, mode, limit, alpha, beta, gamma }),
  });
  return res.json();
};

export const multiSearchKG = async (query: string, dbIds: string[], mode = 'hybrid', limit = 10) => {
  const res = await fetch(`${BASE}/kg/search/multi`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, db_ids: dbIds, mode, limit }),
  });
  return res.json();
};

export const getKGEmbeddingStatus = async (dbId: string) => {
  const res = await fetch(`${BASE}/kg/databases/${dbId}/embedding-status`);
  return res.json();
};

export const createKGDatabase = async (name: string) => {
  const res = await fetch(`${BASE}/kg/databases`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  });
  if (!res.ok) throw new Error((await res.json()).detail || 'Failed to create database');
  return res.json();
};

export const createKGNode = async (dbId: string, name: string, type = 'entity', properties?: Record<string, any>) => {
  const res = await fetch(`${BASE}/kg/databases/${dbId}/nodes`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, type, properties }),
  });
  return res.json();
};

export const updateKGNode = async (dbId: string, nodeId: string, data: { name?: string; type?: string; properties?: Record<string, any> }) => {
  const res = await fetch(`${BASE}/kg/databases/${dbId}/nodes/${nodeId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return res.json();
};

export const deleteKGNode = async (dbId: string, nodeId: string) => {
  const res = await fetch(`${BASE}/kg/databases/${dbId}/nodes/${nodeId}`, { method: 'DELETE' });
  return res.json();
};

export const createKGEdge = async (dbId: string, source: string, target: string, type = 'relates_to', properties?: Record<string, any>) => {
  const res = await fetch(`${BASE}/kg/databases/${dbId}/edges`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ source, target, type, properties }),
  });
  return res.json();
};

export const updateKGEdge = async (dbId: string, edgeId: string, data: { type?: string; properties?: Record<string, any> }) => {
  const res = await fetch(`${BASE}/kg/databases/${dbId}/edges/${edgeId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return res.json();
};

export const deleteKGEdge = async (dbId: string, edgeId: string) => {
  const res = await fetch(`${BASE}/kg/databases/${dbId}/edges/${edgeId}`, { method: 'DELETE' });
  return res.json();
};

export const bulkCreateKG = async (dbId: string, nodes: any[], edges: any[]) => {
  const res = await fetch(`${BASE}/kg/databases/${dbId}/bulk`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ nodes, edges }),
  });
  return res.json();
};

export const ingestKGText = async (dbId: string, text: string, method = 'ai', source?: string) => {
  const res = await fetch(`${BASE}/kg/databases/${dbId}/ingest`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, method, source }),
  });
  return res.json();
};

export const getKGAnalyticsSummary = async (dbId: string) => {
  const res = await fetch(`${BASE}/kg/databases/${dbId}/analytics/summary`);
  return res.json();
};

export const getKGCentrality = async (dbId: string, metric = 'degree', topK = 20) => {
  const res = await fetch(`${BASE}/kg/databases/${dbId}/analytics/centrality?metric=${metric}&top_k=${topK}`);
  return res.json();
};

export const getKGCommunities = async (dbId: string) => {
  const res = await fetch(`${BASE}/kg/databases/${dbId}/analytics/communities`);
  return res.json();
};

export const findKGPath = async (dbId: string, sourceNode: string, targetNode: string) => {
  const res = await fetch(`${BASE}/kg/databases/${dbId}/analytics/path`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ source_node: sourceNode, target_node: targetNode }),
  });
  return res.json();
};

export const compareKGs = async (dbIdA: string, dbIdB: string) => {
  const res = await fetch(`${BASE}/kg/compare`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ db_id_a: dbIdA, db_id_b: dbIdB }),
  });
  return res.json();
};

export const diffKGs = async (dbIdA: string, dbIdB: string) => {
  const res = await fetch(`${BASE}/kg/diff`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ db_id_a: dbIdA, db_id_b: dbIdB }),
  });
  return res.json();
};

export const mergeKGs = async (sourceDb: string, targetDb: string, strategy = 'union') => {
  const res = await fetch(`${BASE}/kg/merge`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ source_db: sourceDb, target_db: targetDb, strategy }),
  });
  return res.json();
};

export const batchDeleteByType = async (dbId: string, nodeType: string) => {
  const res = await fetch(`${BASE}/kg/databases/${dbId}/batch/delete-by-type`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ node_type: nodeType }),
  });
  return res.json();
};

export const batchRetype = async (dbId: string, oldType: string, newType: string) => {
  const res = await fetch(`${BASE}/kg/databases/${dbId}/batch/retype`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ old_type: oldType, new_type: newType }),
  });
  return res.json();
};

export const streamKGChat = async (dbId: string, query: string, history: any[] = [], mode = 'hybrid', limit = 10): Promise<ReadableStream<Uint8Array>> => {
  const res = await fetch(`${BASE}/kg/databases/${dbId}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, history, mode, limit }),
  });
  if (!res.ok || !res.body) throw new Error('KG chat stream failed');
  return res.body;
};

export const getKGEmbeddingProjection = async (dbId: string, method = 'pca', maxPoints = 500) => {
  const res = await fetch(`${BASE}/kg/databases/${dbId}/embeddings/projection?method=${method}&max_points=${maxPoints}`);
  return res.json();
};

export const generateKGEmbeddings = async (dbId: string, strategy = 'gemini') => {
  const res = await fetch(`${BASE}/kg/databases/${dbId}/embeddings/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ strategy }),
  });
  return res.json();
};

export const getKGEmbeddingQuality = async (dbId: string) => {
  const res = await fetch(`${BASE}/kg/databases/${dbId}/embeddings/quality`);
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
