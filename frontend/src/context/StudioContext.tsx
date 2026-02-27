/** StudioContext — all studio state: files, mode, preview, versions, mock server */
import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import type {
  StudioMode, StudioFile, StudioProject, StudioMessage, StudioFileChange,
  StudioVersion, StudioApiSpec, StudioMockServerStatus, StudioSelection,
  StudioEditorTab, StudioProjectSummary,
} from '../types/studio';
import * as studioApi from '../services/studioApiService';
import { generateUniqueId } from '../utils/common';

interface StudioContextType {
  // Mode
  mode: StudioMode;
  setMode: (m: StudioMode) => void;

  // Project
  project: StudioProject | null;
  projectList: StudioProjectSummary[];
  isLoading: boolean;
  isDirty: boolean;

  // Files
  files: Record<string, StudioFile>;
  setFiles: React.Dispatch<React.SetStateAction<Record<string, StudioFile>>>;
  updateFile: (path: string, content: string) => void;
  addFile: (path: string, content: string, language?: string) => void;
  deleteFile: (path: string) => void;
  renameFile: (oldPath: string, newPath: string) => void;

  // Chat
  messages: StudioMessage[];
  streamingText: string;
  streamingPlan: string;
  streamingThinking: string;
  isStreaming: boolean;
  sendMessage: (prompt: string) => Promise<void>;
  clearChat: () => void;

  // Project operations
  createProject: (name: string, description?: string) => Promise<void>;
  loadProject: (id: string) => Promise<void>;
  saveProject: (message?: string) => Promise<void>;
  deleteProject: (id: string) => Promise<void>;
  loadProjectList: () => Promise<void>;
  closeProject: () => void;

  // Versions
  versions: StudioVersion[];
  loadVersions: () => Promise<void>;
  restoreVersion: (ver: number) => Promise<void>;

  // API / Mock
  apiSpec: StudioApiSpec | null;
  mockServerStatus: StudioMockServerStatus;
  startMockServer: () => Promise<void>;
  stopMockServer: () => Promise<void>;

  // Editor (Code mode)
  openTabs: StudioEditorTab[];
  activeTab: string | null;
  openFile: (path: string) => void;
  closeTab: (path: string) => void;
  setActiveTab: (path: string) => void;

  // Visual mode
  selectedElement: StudioSelection | null;
  setSelectedElement: (sel: StudioSelection | null) => void;

  // Provider/model
  provider: 'gemini' | 'claude' | 'openai';
  model: string;
  setProvider: (p: 'gemini' | 'claude' | 'openai') => void;
  setModel: (m: string) => void;
}

const StudioContext = createContext<StudioContextType | undefined>(undefined);

export const StudioProvider: React.FC<{ children: ReactNode; initialProvider: 'gemini' | 'claude' | 'openai'; initialModel: string }> = ({
  children, initialProvider, initialModel,
}) => {
  // Mode
  const [mode, setMode] = useState<StudioMode>('chat');

  // Project
  const [project, setProject] = useState<StudioProject | null>(null);
  const [projectList, setProjectList] = useState<StudioProjectSummary[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isDirty, setIsDirty] = useState(false);

  // Files
  const [files, setFiles] = useState<Record<string, StudioFile>>({});

  // Chat
  const [messages, setMessages] = useState<StudioMessage[]>([]);
  const [streamingText, setStreamingText] = useState('');
  const [streamingPlan, setStreamingPlan] = useState('');
  const [streamingThinking, setStreamingThinking] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);

  // Versions
  const [versions, setVersions] = useState<StudioVersion[]>([]);

  // API / Mock
  const [apiSpec, setApiSpec] = useState<StudioApiSpec | null>(null);
  const [mockServerStatus, setMockServerStatus] = useState<StudioMockServerStatus>({ running: false });

  // Editor
  const [openTabs, setOpenTabs] = useState<StudioEditorTab[]>([]);
  const [activeTab, setActiveTabState] = useState<string | null>(null);

  // Visual
  const [selectedElement, setSelectedElement] = useState<StudioSelection | null>(null);

  // Provider/model
  const [provider, setProvider] = useState<'gemini' | 'claude' | 'openai'>(initialProvider);
  const [model, setModel] = useState(initialModel);

  // --- File operations ---
  const updateFile = useCallback((path: string, content: string) => {
    setFiles(prev => ({
      ...prev,
      [path]: { ...prev[path], path, content },
    }));
    setIsDirty(true);
    // Mark tab dirty
    setOpenTabs(prev => prev.map(t => t.path === path ? { ...t, isDirty: true } : t));
  }, []);

  const addFile = useCallback((path: string, content: string, language?: string) => {
    setFiles(prev => ({
      ...prev,
      [path]: { path, content, language: language || guessLanguage(path) },
    }));
    setIsDirty(true);
  }, []);

  const deleteFileHandler = useCallback((path: string) => {
    setFiles(prev => {
      const next = { ...prev };
      delete next[path];
      return next;
    });
    setOpenTabs(prev => prev.filter(t => t.path !== path));
    if (activeTab === path) setActiveTabState(null);
    setIsDirty(true);
  }, [activeTab]);

  const renameFile = useCallback((oldPath: string, newPath: string) => {
    setFiles(prev => {
      const next = { ...prev };
      if (next[oldPath]) {
        next[newPath] = { ...next[oldPath], path: newPath, language: guessLanguage(newPath) };
        delete next[oldPath];
      }
      return next;
    });
    setOpenTabs(prev => prev.map(t => t.path === oldPath ? { ...t, path: newPath } : t));
    if (activeTab === oldPath) setActiveTabState(newPath);
    setIsDirty(true);
  }, [activeTab]);

  // --- Chat / Streaming ---
  const sendMessage = useCallback(async (prompt: string) => {
    if (isStreaming) return;

    const userMsg: StudioMessage = {
      id: generateUniqueId(),
      role: 'user',
      content: prompt,
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMsg]);
    setIsStreaming(true);
    setStreamingText('');
    setStreamingPlan('');
    setStreamingThinking('');

    try {
      const isFirstMessage = Object.keys(files).length === 0 && messages.length === 0;
      const chatHistory = [...messages, userMsg].map(m => ({
        role: m.role,
        content: m.content,
      }));

      const stream = await studioApi.streamStudio(
        project?.id || null,
        prompt,
        files,
        chatHistory,
        provider,
        model,
        isFirstMessage ? 'generate' : 'refine',
      );

      const reader = stream.getReader();
      const decoder = new TextDecoder();
      let accText = '';
      let accPlan = '';
      let accThinking = '';
      const collectedFiles: StudioFileChange[] = [];
      let collectedDeps: Record<string, string> = {};
      let collectedApiSpec: StudioApiSpec | null = null;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n').filter(l => l.startsWith('data: '));

        for (const line of lines) {
          try {
            const data = JSON.parse(line.slice(6));

            switch (data.type) {
              case 'token':
                accText += data.content;
                setStreamingText(accText);
                break;

              case 'thinking':
                accThinking += data.content || '';
                setStreamingThinking(accThinking);
                break;

              case 'studio_plan':
                accPlan = data.content || '';
                setStreamingPlan(accPlan);
                break;

              case 'studio_file': {
                const filePath = data.path;
                const fileContent = data.file_content || data.content || '';
                collectedFiles.push({ path: filePath, content: fileContent, action: 'create' });
                // Immediately update Sandpack files
                setFiles(prev => ({
                  ...prev,
                  [filePath]: { path: filePath, content: fileContent, language: guessLanguage(filePath) },
                }));
                break;
              }

              case 'studio_deps':
                collectedDeps = { ...collectedDeps, ...(data.dependencies || data.deps || data.content || {}) };
                break;

              case 'studio_api_spec':
                collectedApiSpec = data.api_spec || data.content || null;
                if (collectedApiSpec) setApiSpec(collectedApiSpec);
                break;

              case 'error':
                accText += `\n\nError: ${data.content}`;
                setStreamingText(accText);
                break;

              case 'done':
                break;
            }
          } catch {
            // Skip malformed lines
          }
        }
      }

      // Add assistant message
      const assistantMsg: StudioMessage = {
        id: generateUniqueId(),
        role: 'assistant',
        content: accText,
        timestamp: new Date().toISOString(),
        thinking: accThinking || undefined,
        files: collectedFiles.length > 0 ? collectedFiles : undefined,
        plan: accPlan || undefined,
        apiSpec: collectedApiSpec,
        deps: Object.keys(collectedDeps).length > 0 ? collectedDeps : undefined,
      };
      setMessages(prev => [...prev, assistantMsg]);
      setIsDirty(true);

    } catch (err: any) {
      const errorMsg: StudioMessage = {
        id: generateUniqueId(),
        role: 'system',
        content: `Error: ${err.message}`,
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsStreaming(false);
      setStreamingText('');
      setStreamingPlan('');
      setStreamingThinking('');
    }
  }, [isStreaming, files, messages, project, provider, model]);

  const clearChat = useCallback(() => {
    setMessages([]);
  }, []);

  // --- Project CRUD ---
  const createProjectHandler = useCallback(async (name: string, description?: string) => {
    setIsLoading(true);
    try {
      const p = await studioApi.createProject(name, description);
      setProject(p);
      setFiles(p.files || {});
      setMessages(p.chatHistory || []);
      setVersions([]);
      setIsDirty(false);
      setOpenTabs([]);
      setActiveTabState(null);
      await loadProjectListHandler();
    } finally {
      setIsLoading(false);
    }
  }, []);

  const loadProject = useCallback(async (id: string) => {
    setIsLoading(true);
    try {
      const p = await studioApi.getProject(id);
      setProject(p);
      setFiles(p.files || {});
      setMessages(p.chatHistory || []);
      setIsDirty(false);
      setOpenTabs([]);
      setActiveTabState(null);
      setApiSpec(null);
      setMockServerStatus({ running: false });
      setSelectedElement(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const saveProjectHandler = useCallback(async (message?: string) => {
    if (!project) return;
    setIsLoading(true);
    try {
      // Update project files and chat (backend expects snake_case keys)
      await studioApi.updateProject(project.id, {
        files,
        chat_history: messages,
      } as any);
      // Save version snapshot
      await studioApi.saveVersion(project.id, message || `Save v${project.currentVersion + 1}`);
      setIsDirty(false);
      setProject(prev => prev ? { ...prev, currentVersion: prev.currentVersion + 1 } : null);
      // Clean tab dirty flags
      setOpenTabs(prev => prev.map(t => ({ ...t, isDirty: false })));
    } finally {
      setIsLoading(false);
    }
  }, [project, files, messages]);

  const deleteProjectHandler = useCallback(async (id: string) => {
    setIsLoading(true);
    try {
      await studioApi.deleteProject(id);
      if (project?.id === id) {
        setProject(null);
        setFiles({});
        setMessages([]);
        setVersions([]);
        setOpenTabs([]);
        setActiveTabState(null);
      }
      await loadProjectListHandler();
    } finally {
      setIsLoading(false);
    }
  }, [project]);

  const loadProjectListHandler = useCallback(async () => {
    const list = await studioApi.listProjects();
    setProjectList(list);
  }, []);

  const closeProject = useCallback(() => {
    setProject(null);
    setFiles({});
    setMessages([]);
    setVersions([]);
    setOpenTabs([]);
    setActiveTabState(null);
    setApiSpec(null);
    setMockServerStatus({ running: false });
    setSelectedElement(null);
    setIsDirty(false);
  }, []);

  // --- Versions ---
  const loadVersionsHandler = useCallback(async () => {
    if (!project) return;
    const v = await studioApi.listVersions(project.id);
    setVersions(v);
  }, [project]);

  const restoreVersionHandler = useCallback(async (ver: number) => {
    if (!project) return;
    setIsLoading(true);
    try {
      const restored = await studioApi.restoreVersion(project.id, ver);
      setProject(restored);
      setFiles(restored.files || {});
      setIsDirty(false);
    } finally {
      setIsLoading(false);
    }
  }, [project]);

  // --- Mock Server ---
  const startMockServerHandler = useCallback(async () => {
    if (!project) return;
    try {
      const status = await studioApi.startMockServer(project.id);
      setMockServerStatus(status);
    } catch (err: any) {
      console.error('Mock server start failed:', err);
    }
  }, [project]);

  const stopMockServerHandler = useCallback(async () => {
    if (!project) return;
    await studioApi.stopMockServer(project.id);
    setMockServerStatus({ running: false });
  }, [project]);

  // --- Editor ---
  const openFile = useCallback((path: string) => {
    setOpenTabs(prev => {
      if (prev.some(t => t.path === path)) return prev;
      return [...prev, { path, isDirty: false }];
    });
    setActiveTabState(path);
  }, []);

  const closeTab = useCallback((path: string) => {
    setOpenTabs(prev => prev.filter(t => t.path !== path));
    setActiveTabState(prev => prev === path ? null : prev);
  }, []);

  const setActiveTab = useCallback((path: string) => {
    setActiveTabState(path);
  }, []);

  const value: StudioContextType = {
    mode, setMode,
    project, projectList, isLoading, isDirty,
    files, setFiles, updateFile, addFile, deleteFile: deleteFileHandler, renameFile,
    messages, streamingText, streamingPlan, streamingThinking, isStreaming, sendMessage, clearChat,
    createProject: createProjectHandler, loadProject, saveProject: saveProjectHandler,
    deleteProject: deleteProjectHandler, loadProjectList: loadProjectListHandler, closeProject,
    versions, loadVersions: loadVersionsHandler, restoreVersion: restoreVersionHandler,
    apiSpec, mockServerStatus, startMockServer: startMockServerHandler, stopMockServer: stopMockServerHandler,
    openTabs, activeTab, openFile, closeTab, setActiveTab,
    selectedElement, setSelectedElement,
    provider, model, setProvider, setModel,
  };

  return <StudioContext.Provider value={value}>{children}</StudioContext.Provider>;
};

export const useStudio = () => {
  const ctx = useContext(StudioContext);
  if (!ctx) throw new Error('useStudio must be used within StudioProvider');
  return ctx;
};

// --- Utility ---
function guessLanguage(path: string): string {
  const ext = path.split('.').pop()?.toLowerCase() || '';
  const map: Record<string, string> = {
    tsx: 'typescript', ts: 'typescript', jsx: 'javascript', js: 'javascript',
    css: 'css', html: 'html', json: 'json', md: 'markdown', py: 'python',
    sql: 'sql', yaml: 'yaml', yml: 'yaml', txt: 'text',
  };
  return map[ext] || 'text';
}
