import { Message, Persona, CustomAiStyle, Project, ProjectFile } from '../types/index';

const BASE = '/api';

// --- Chat Streaming ---
export const streamChat = async (
  messages: Message[],
  provider: 'gemini' | 'claude' | 'openai',
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
  provider: 'gemini' | 'claude' | 'openai',
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

// --- SDK Media Generation ---
export const generateImageSDK = async (
  prompt: string, model = 'gemini-3-pro-image-preview', aspectRatio = '1:1', numImages = 1
) => {
  const res = await fetch(`${BASE}/media/image/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt, model, aspect_ratio: aspectRatio, num_images: numImages }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: 'Image generation failed' }));
    throw new Error(err.message || 'Image generation failed');
  }
  return res.json();
};

export const generateTTSSDK = async (
  text: string, model = 'gemini-2.5-flash-preview-tts', voice = 'Kore', speed = 1.0
) => {
  const res = await fetch(`${BASE}/media/tts/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, model, voice, speed }),
  });
  if (!res.ok) throw new Error((await res.json()).message || 'TTS generation failed');
  return res.json();
};

export const generateVideoSDK = async (
  prompt: string, model = 'veo-3.1-generate-preview', aspectRatio = '16:9', durationSeconds = 8
) => {
  const res = await fetch(`${BASE}/media/video/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt, model, aspect_ratio: aspectRatio, duration_seconds: durationSeconds }),
  });
  if (!res.ok) throw new Error((await res.json()).message || 'Video generation failed');
  return res.json();
};

export const streamAgentSDK = async (
  prompt: string, allowedTools?: string[], model?: string, cwd?: string, maxTurns?: number, sessionId?: string
): Promise<ReadableStream<Uint8Array>> => {
  const res = await fetch(`${BASE}/agent/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      prompt,
      allowed_tools: allowedTools,
      model,
      cwd,
      max_turns: maxTurns,
      session_id: sessionId,
    }),
  });
  if (!res.ok || !res.body) throw new Error((await res.json().catch(() => ({ message: 'Agent stream failed' }))).message);
  return res.body;
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

// --- Memory + Conversations ---
export const listConversations = async (mode?: string, limit = 20) => {
  const params = new URLSearchParams({ limit: String(limit) });
  if (mode) params.set('mode', mode);
  const res = await fetch(`${BASE}/memory/conversations?${params}`);
  return res.json();
};

export const getConversation = async (id: string) => {
  const res = await fetch(`${BASE}/memory/conversations/${id}`);
  return res.json();
};

export const getConversationMessages = async (id: string, limit = 50, offset = 0) => {
  const res = await fetch(`${BASE}/memory/conversations/${id}/messages?limit=${limit}&offset=${offset}`);
  return res.json();
};

export const deleteConversation = async (id: string) => {
  const res = await fetch(`${BASE}/memory/conversations/${id}`, { method: 'DELETE' });
  return res.json();
};

export const searchMemory = async (query: string, limit = 5) => {
  const res = await fetch(`${BASE}/memory/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, limit }),
  });
  return res.json();
};

export const getMemoryStats = async () => {
  const res = await fetch(`${BASE}/memory/stats`);
  return res.json();
};

// --- Integrations ---
export const listIntegrations = async () => {
  const res = await fetch(`${BASE}/integrations`);
  return res.json();
};

export const configureIntegration = async (platform: string, config: Record<string, string>, userLabel = '') => {
  const res = await fetch(`${BASE}/integrations/${platform}/configure`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ config, user_label: userLabel }),
  });
  return res.json();
};

export const testIntegration = async (platform: string) => {
  const res = await fetch(`${BASE}/integrations/${platform}/test`, { method: 'POST' });
  return res.json();
};

export const enableIntegration = async (platform: string) => {
  const res = await fetch(`${BASE}/integrations/${platform}/enable`, { method: 'POST' });
  return res.json();
};

export const disableIntegration = async (platform: string) => {
  const res = await fetch(`${BASE}/integrations/${platform}/disable`, { method: 'POST' });
  return res.json();
};

export const deleteIntegration = async (platform: string) => {
  const res = await fetch(`${BASE}/integrations/${platform}`, { method: 'DELETE' });
  return res.json();
};

export const getIntegrationSetup = async (platform: string) => {
  const res = await fetch(`${BASE}/integrations/${platform}/setup`);
  return res.json();
};

// --- API Key Configuration ---
export const getKeysStatus = async (): Promise<{ gemini: boolean; anthropic: boolean; openai: boolean; mode: string }> => {
  const res = await fetch(`${BASE}/config/keys/status`);
  return res.json();
};

// --- Experts ---
export const listExperts = async () => {
  const res = await fetch(`${BASE}/experts`);
  return res.json();
};

export const createExpert = async (data: any) => {
  const res = await fetch(`${BASE}/experts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error((await res.json()).detail || 'Failed to create expert');
  return res.json();
};

export const getExpert = async (id: string) => {
  const res = await fetch(`${BASE}/experts/${id}`);
  if (!res.ok) throw new Error('Expert not found');
  return res.json();
};

export const updateExpert = async (id: string, data: any) => {
  const res = await fetch(`${BASE}/experts/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error((await res.json()).detail || 'Failed to update expert');
  return res.json();
};

export const deleteExpert = async (id: string) => {
  const res = await fetch(`${BASE}/experts/${id}`, { method: 'DELETE' });
  return res.json();
};

export const duplicateExpert = async (id: string) => {
  const res = await fetch(`${BASE}/experts/${id}/duplicate`, { method: 'POST' });
  return res.json();
};

export const streamExpertChat = async (
  expertId: string, query: string, conversationId?: string, history: any[] = []
): Promise<ReadableStream<Uint8Array>> => {
  const res = await fetch(`${BASE}/experts/${expertId}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, conversation_id: conversationId, history }),
  });
  if (!res.ok || !res.body) throw new Error('Expert chat stream failed');
  return res.body;
};

export const listExpertConversations = async (expertId: string) => {
  const res = await fetch(`${BASE}/experts/${expertId}/conversations`);
  return res.json();
};

export const getExpertConversation = async (expertId: string, conversationId: string) => {
  const res = await fetch(`${BASE}/experts/${expertId}/conversations/${conversationId}`);
  return res.json();
};

export const deleteExpertConversation = async (expertId: string, conversationId: string) => {
  const res = await fetch(`${BASE}/experts/${expertId}/conversations/${conversationId}`, { method: 'DELETE' });
  return res.json();
};

export const kgosQuery = async (dbId: string, query: string, options: any = {}) => {
  const res = await fetch(`${BASE}/experts/kgos/query/${dbId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, ...options }),
  });
  return res.json();
};

export const kgosImpact = async (dbId: string, nodeId: string, direction = 'forward', maxDepth = 3) => {
  const res = await fetch(`${BASE}/experts/kgos/impact/${dbId}/${nodeId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ direction, max_depth: maxDepth }),
  });
  return res.json();
};

export const kgosCompose = async (dbId: string, goal: string, maxSteps = 5) => {
  const res = await fetch(`${BASE}/experts/kgos/compose/${dbId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ goal, max_steps: maxSteps }),
  });
  return res.json();
};

export const kgosSimilar = async (dbId: string, nodeId: string, k = 10) => {
  const res = await fetch(`${BASE}/experts/kgos/similar/${dbId}/${nodeId}?k=${k}`, { method: 'POST' });
  return res.json();
};

// --- Tools Playground ---
export const listTools = async () => {
  const res = await fetch(`${BASE}/tools`);
  return res.json();
};

export const getToolDetail = async (id: string) => {
  const res = await fetch(`${BASE}/tools/${id}`);
  return res.json();
};

export const runTool = async (id: string, params: Record<string, any>) => {
  const res = await fetch(`${BASE}/tools/${id}/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ params }),
  });
  return res.json();
};

export const runToolStream = async (id: string, params: Record<string, any>): Promise<ReadableStream<Uint8Array>> => {
  const res = await fetch(`${BASE}/tools/${id}/run/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ params }),
  });
  if (!res.ok || !res.body) throw new Error('Tool stream failed');
  return res.body;
};

// --- VOX Voice ---
export const getVoxStatus = async () => {
  const res = await fetch(`${BASE}/vox/status`);
  return res.json();
};

export const getVoxVoices = async () => {
  const res = await fetch(`${BASE}/vox/voices`);
  return res.json();
};

export const getVoxFunctions = async () => {
  const res = await fetch(`${BASE}/vox/functions`);
  return res.json();
};

export const runVoxFunction = async (fnName: string, args: Record<string, any> = {}) => {
  const res = await fetch(`${BASE}/vox/function/${fnName}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ args }),
  });
  return res.json();
};

export const setApiKeys = async (geminiKey?: string, anthropicKey?: string, openaiKey?: string) => {
  const body: Record<string, string> = {};
  if (geminiKey) body.gemini_key = geminiKey;
  if (anthropicKey) body.anthropic_key = anthropicKey;
  if (openaiKey) body.openai_key = openaiKey;
  const res = await fetch(`${BASE}/config/keys`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error((await res.json()).error || 'Failed to set keys');
  return res.json();
};

// ── Games (Phaser 3 RPG) ──────────────────────────────────────────────

export const listGames = async () => {
  const res = await fetch(`${BASE}/games`);
  return res.json();
};

export const createGame = async (name: string, description: string = '') => {
  const res = await fetch(`${BASE}/games`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, description }),
  });
  if (!res.ok) throw new Error((await res.json()).detail || 'Failed to create game');
  return res.json();
};

export const getGame = async (id: string) => {
  const res = await fetch(`${BASE}/games/${id}`);
  if (!res.ok) throw new Error('Game not found');
  return res.json();
};

export const updateGame = async (id: string, data: any) => {
  const res = await fetch(`${BASE}/games/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return res.json();
};

export const deleteGame = async (id: string) => {
  const res = await fetch(`${BASE}/games/${id}`, { method: 'DELETE' });
  return res.json();
};

export const getInterviewQuestions = async () => {
  const res = await fetch(`${BASE}/games/interview/questions`);
  return res.json();
};

export const submitInterviewAnswer = async (gameId: string, questionId: string, answer: any) => {
  const res = await fetch(`${BASE}/games/${gameId}/interview`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question_id: questionId, answer }),
  });
  return res.json();
};

export const synthesizeGDD = async (gameId: string) => {
  const res = await fetch(`${BASE}/games/${gameId}/synthesize`, { method: 'POST' });
  return res.json();
};

export const streamGenerateGame = async (gameId: string): Promise<ReadableStream<Uint8Array>> => {
  const res = await fetch(`${BASE}/games/${gameId}/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({}),
  });
  if (!res.ok || !res.body) {
    const err = await res.json().catch(() => ({ detail: 'Game generation failed' }));
    throw new Error(err.detail || 'Game generation failed');
  }
  return res.body;
};

export const streamRefineGame = async (gameId: string, prompt: string, files: Record<string, string> = {}): Promise<ReadableStream<Uint8Array>> => {
  const res = await fetch(`${BASE}/games/${gameId}/refine`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt, files }),
  });
  if (!res.ok || !res.body) throw new Error('Game refinement failed');
  return res.body;
};

export const saveGameVersion = async (gameId: string) => {
  const res = await fetch(`${BASE}/games/${gameId}/save`, { method: 'POST' });
  return res.json();
};

export const listGameVersions = async (gameId: string) => {
  const res = await fetch(`${BASE}/games/${gameId}/versions`);
  return res.json();
};

export const restoreGameVersion = async (gameId: string, versionNumber: number) => {
  const res = await fetch(`${BASE}/games/${gameId}/versions/${versionNumber}/restore`, { method: 'POST' });
  return res.json();
};

export const exportGame = async (gameId: string) => {
  const res = await fetch(`${BASE}/games/${gameId}/export`);
  return res.blob();
};

export const streamGameChat = async (
  gameId: string, query: string, conversationId?: string, history: any[] = []
): Promise<ReadableStream<Uint8Array>> => {
  const res = await fetch(`${BASE}/games/${gameId}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, conversation_id: conversationId, history }),
  });
  if (!res.ok || !res.body) throw new Error('Game chat failed');
  return res.body;
};

export const extractGamePatterns = async (gameId: string) => {
  const res = await fetch(`${BASE}/games/${gameId}/extract-patterns`, { method: 'POST' });
  return res.json();
};

export const gameLLMStatus = async () => {
  const res = await fetch(`${BASE}/games/llm/status`);
  return res.json();
};

export const gameLLMLoad = async (modelType: string) => {
  const res = await fetch(`${BASE}/games/llm/load`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ model_type: modelType }),
  });
  return res.json();
};

export const gameLLMUnload = async () => {
  const res = await fetch(`${BASE}/games/llm/unload`, { method: 'POST' });
  return res.json();
};

export const gameLLMChat = async (npcName: string, systemPrompt: string, message: string, history: any[] = []) => {
  const res = await fetch(`${BASE}/games/llm/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ npc_name: npcName, system_prompt: systemPrompt, message, history }),
  });
  return res.json();
};
