import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react';
import { Project, ProjectFile, CustomAiStyle, Persona, Agent } from '../types/index';
import * as storageService from '../services/storageService';
import * as apiService from '../services/apiService';
import { generateUniqueId } from '../utils/common';
import { useTheme } from '../hooks/useTheme';
import type { ThemeId, ThemeDefinition } from '../themes/index';

export interface ModelCatalogEntry {
  name: string;
  category: string;
  context: string;
  cost_in: string;
  cost_out: string;
  use_case: string;
}

export type ModelCatalog = Record<string, Record<string, ModelCatalogEntry>>;

export interface WebAppBuilderState {
  isActive: boolean;
  currentStep: number;
  idea: string;
  plan: any | null;
  theme: { palette: string; typography: string };
  generatedFiles: Record<string, string> | null;
  status: { message: string; isLoading: boolean; log: string[] };
}

const initialBuilderState: WebAppBuilderState = {
  isActive: false, currentStep: 0, idea: '', plan: null,
  theme: { palette: 'Modern & Minimal', typography: 'Sans-serif & Friendly' },
  generatedFiles: null, status: { message: '', isLoading: false, log: [] },
};

const defaultPersona: Persona = {
  id: 'default', name: 'Default', baseInstructions: '',
  composedStyles: [{ name: 'The Pragmatist', weight: 1 }],
};

const defaultCustomStyles: CustomAiStyle[] = [
  { id: 'default-pragmatist', name: 'The Pragmatist', instructions: 'You are a pragmatic, code-first assistant. Prioritize functional, efficient code snippets. Keep explanations brief and technical.', isDefault: true },
  { id: 'default-muse', name: 'The Muse', instructions: 'Spark creativity. Ask insightful, guiding questions. Help explore alternatives using the Socratic method.', isDefault: true },
  { id: 'default-mentor', name: 'The Mentor', instructions: 'You are a tutor. Explain underlying principles, the "why" behind code. Discuss trade-offs and alternative approaches.', isDefault: true },
  { id: 'default-visionary', name: 'The Visionary', instructions: 'Think two steps ahead. Design robust, scalable solutions that anticipate future needs.', isDefault: true },
];

interface AppContextType {
  // Projects
  projects: Project[];
  selectedProjectIds: Set<string>;
  filesByProject: Map<string, ProjectFile[]>;
  activeProjectView: string | null;
  editingProject: Project | null;
  isProjectPanelCollapsed: boolean;
  // AI
  activePersona: Persona;
  selectedPersonaId: string | null;
  customAiStyles: CustomAiStyle[];
  personas: Persona[];
  useWebSearch: boolean;
  // Model
  activeProvider: 'gemini' | 'claude' | 'openai';
  activeModel: string;
  thinkingEnabled: boolean;
  thinkingBudget: number;
  workspaceMode: 'standalone' | 'claude-code';
  modelCatalog: ModelCatalog;
  // Agents
  agents: Agent[];
  activeAgentId: string | null;
  // UI
  globalError: string | null;
  // Builder
  builderState: WebAppBuilderState;
  // Theme
  themeId: ThemeId;
  theme: ThemeDefinition;
  switchTheme: (id: ThemeId) => void;
  // Actions
  setActiveProvider: (p: 'gemini' | 'claude' | 'openai') => void;
  setActiveModel: (m: string) => void;
  setThinkingEnabled: (b: boolean) => void;
  setThinkingBudget: (n: number) => void;
  setWorkspaceMode: (m: 'standalone' | 'claude-code') => void;
  setUseWebSearch: React.Dispatch<React.SetStateAction<boolean>>;
  setGlobalError: React.Dispatch<React.SetStateAction<string | null>>;
  setSelectedProjectIds: React.Dispatch<React.SetStateAction<Set<string>>>;
  handleCreateProject: (name: string) => Promise<Project>;
  handleDeleteProject: (id: string) => Promise<void>;
  handleToggleProjectSelection: (id: string) => void;
  handleViewProjectFiles: (id: string) => Promise<void>;
  handleAddFile: (projectId: string, file: File) => Promise<void>;
  handleDeleteFile: (fileId: string, projectId: string) => Promise<void>;
  aiCreateFile: (projectId: string, path: string, content: string) => Promise<ProjectFile>;
  aiUpdateFile: (projectId: string, path: string, newContent: string) => Promise<ProjectFile | null>;
  aiDeleteFile: (projectId: string, path: string) => Promise<boolean>;
  handleSaveFileContent: (projectId: string, fileId: string, newContent: string) => Promise<void>;
  handleOpenProjectSettings: (project: Project) => Promise<void>;
  handleCloseProjectSettings: () => void;
  handleRenameProject: (projectId: string, newName: string) => Promise<void>;
  handleToggleProjectPanel: () => void;
  handleSelectPersona: (personaId: string | null) => void;
  handleSavePersona: (name: string, config: Omit<Persona, 'id' | 'name'>) => Promise<void>;
  handleDeletePersona: (personaId: string) => Promise<void>;
  handleAddCustomStyle: (name: string, instructions: string) => Promise<void>;
  handleUpdateCustomStyle: (id: string, name: string, instructions: string) => Promise<void>;
  handleDeleteCustomStyle: (id: string) => Promise<void>;
  handleAddAgent: (name: string, personaId: string, projectId: string) => Promise<void>;
  handleUpdateAgent: (agentId: string, name: string, personaId: string, projectId: string) => Promise<void>;
  handleDeleteAgent: (agentId: string) => Promise<void>;
  handleSelectAgent: (agentId: string | null) => void;
  setActivePersona: React.Dispatch<React.SetStateAction<Persona>>;
  setBuilderState: React.Dispatch<React.SetStateAction<WebAppBuilderState>>;
  startWebAppBuild: () => void;
  resetWebAppBuild: () => void;
  generateWebAppPlan: () => Promise<void>;
  generateWebAppCode: () => Promise<void>;
  loadGeneratedProjectIntoIDE: () => Promise<void>;
  exportGeneratedProject: () => Promise<void>;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectIds, setSelectedProjectIds] = useState<Set<string>>(new Set());
  const [filesByProject, setFilesByProject] = useState<Map<string, ProjectFile[]>>(new Map());
  const [activeProjectView, setActiveProjectView] = useState<string | null>(null);
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [isProjectPanelCollapsed, setIsProjectPanelCollapsed] = useState(false);
  const [useWebSearch, setUseWebSearch] = useState(false);
  const [customAiStyles, setCustomAiStyles] = useState<CustomAiStyle[]>([]);
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [selectedPersonaId, setSelectedPersonaId] = useState<string | null>(null);
  const [activePersona, setActivePersona] = useState<Persona>(defaultPersona);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [activeAgentId, setActiveAgentId] = useState<string | null>(null);
  const [globalError, setGlobalError] = useState<string | null>(null);
  const [builderState, setBuilderState] = useState<WebAppBuilderState>(initialBuilderState);
  const { themeId, switchTheme, theme } = useTheme();

  // Model state
  const settings = storageService.getSettings();
  const [activeProvider, _setActiveProvider] = useState<'gemini' | 'claude' | 'openai'>(settings.mode === 'claude-code' ? 'gemini' : 'gemini');
  const [activeModel, _setActiveModel] = useState(settings.defaultGeminiModel);
  const [thinkingEnabled, setThinkingEnabled] = useState(false);
  const [thinkingBudget, setThinkingBudget] = useState(settings.thinkingBudget);
  const [workspaceMode, _setWorkspaceMode] = useState<'standalone' | 'claude-code'>(settings.mode);
  const [modelCatalog, setModelCatalog] = useState<ModelCatalog>({});

  const setActiveProvider = (p: 'gemini' | 'claude' | 'openai') => {
    _setActiveProvider(p);
    if (p === 'gemini') _setActiveModel(settings.defaultGeminiModel);
    else if (p === 'openai') _setActiveModel('gpt-5-mini');
    else _setActiveModel(settings.defaultClaudeModel);
  };
  const setActiveModel = (m: string) => _setActiveModel(m);
  const setWorkspaceMode = (m: 'standalone' | 'claude-code') => {
    _setWorkspaceMode(m);
    storageService.saveSettings({ ...storageService.getSettings(), mode: m });
    if (m === 'claude-code') {
      _setActiveProvider('gemini');
      _setActiveModel(settings.defaultGeminiModel);
    }
    apiService.setMode(m).catch(() => {});
  };

  useEffect(() => {
    const load = async () => {
      setProjects(await storageService.getProjects());
      const userStyles = await storageService.getCustomAiStyles();
      setCustomAiStyles([...defaultCustomStyles, ...userStyles]);
      setPersonas(await storageService.getPersonas());
      setAgents(await storageService.getAgents());
      try {
        const catalog = await apiService.listModels();
        setModelCatalog(catalog);
      } catch {}
    };
    load();
  }, []);

  useEffect(() => {
    if (selectedPersonaId) {
      const found = personas.find(p => p.id === selectedPersonaId);
      if (found) setActivePersona(found);
    }
  }, [selectedPersonaId, personas]);

  // Project handlers
  const handleCreateProject = async (name: string): Promise<Project> => {
    const p: Project = { id: generateUniqueId(), name, createdAt: Date.now() };
    await storageService.addProject(p);
    setProjects(prev => [...prev, p]);
    return p;
  };
  const handleDeleteProject = async (id: string) => {
    await storageService.deleteProject(id);
    setProjects(prev => prev.filter(p => p.id !== id));
    setSelectedProjectIds(prev => { const s = new Set(prev); s.delete(id); return s; });
    setFilesByProject(prev => { const m = new Map(prev); m.delete(id); return m; });
    if (activeProjectView === id) setActiveProjectView(null);
  };
  const handleToggleProjectSelection = (id: string) => {
    setSelectedProjectIds(prev => { const s = new Set(prev); if (s.has(id)) s.delete(id); else s.add(id); return s; });
  };
  const handleViewProjectFiles = async (id: string) => {
    if (activeProjectView === id) { setActiveProjectView(null); return; }
    setActiveProjectView(id);
    if (!filesByProject.has(id)) {
      const files = await storageService.getFilesByProject(id);
      setFilesByProject(prev => new Map(prev).set(id, files));
    }
  };
  const handleAddFile = async (projectId: string, file: File) => {
    const content = await storageService.readFileAsText(file);
    const f: ProjectFile = { id: generateUniqueId(), projectId, path: file.name, type: file.type, content, createdAt: Date.now() };
    await storageService.addFile(f);
    setFilesByProject(prev => new Map(prev).set(projectId, [...(prev.get(projectId) || []), f]));
  };
  const handleDeleteFile = async (fileId: string, projectId: string) => {
    await storageService.deleteFile(fileId, projectId);
    setFilesByProject(prev => new Map(prev).set(projectId, (prev.get(projectId) || []).filter(f => f.id !== fileId)));
  };
  const aiCreateFile = async (projectId: string, path: string, content: string): Promise<ProjectFile> => {
    const f: ProjectFile = { id: generateUniqueId(), projectId, path, content, type: 'text/plain', createdAt: Date.now() };
    await storageService.addFile(f);
    setFilesByProject(prev => new Map(prev).set(projectId, [...(prev.get(projectId) || []), f]));
    return f;
  };
  const aiUpdateFile = async (projectId: string, path: string, newContent: string): Promise<ProjectFile | null> => {
    const files = filesByProject.get(projectId) || await storageService.getFilesByProject(projectId);
    const file = files.find(f => f.path === path);
    if (!file) return null;
    const updated = { ...file, content: newContent };
    await storageService.updateFile(projectId, updated);
    setFilesByProject(prev => new Map(prev).set(projectId, files.map(f => f.id === updated.id ? updated : f)));
    return updated;
  };
  const aiDeleteFile = async (projectId: string, path: string): Promise<boolean> => {
    const files = filesByProject.get(projectId) || await storageService.getFilesByProject(projectId);
    const file = files.find(f => f.path === path);
    if (!file) return false;
    await handleDeleteFile(file.id, projectId);
    return true;
  };
  const handleSaveFileContent = async (projectId: string, fileId: string, newContent: string) => {
    const files = filesByProject.get(projectId) || [];
    const file = files.find(f => f.id === fileId);
    if (!file) return;
    const updated = { ...file, content: newContent };
    await storageService.updateFile(projectId, updated);
    setFilesByProject(prev => { const m = new Map(prev); m.set(projectId, (m.get(projectId) || []).map(f => f.id === fileId ? updated : f)); return m; });
  };
  const handleOpenProjectSettings = async (project: Project) => {
    const files = await storageService.getFilesByProject(project.id);
    setFilesByProject(prev => new Map(prev).set(project.id, files));
    setEditingProject(project);
  };
  const handleCloseProjectSettings = () => setEditingProject(null);
  const handleRenameProject = async (projectId: string, newName: string) => {
    const project = projects.find(p => p.id === projectId);
    if (!project) return;
    const updated = { ...project, name: newName };
    await storageService.updateProject(updated);
    setProjects(prev => prev.map(p => p.id === projectId ? updated : p));
    if (editingProject?.id === projectId) setEditingProject(updated);
  };
  const handleToggleProjectPanel = () => setIsProjectPanelCollapsed(prev => !prev);

  // AI Style handlers
  const handleAddCustomStyle = async (name: string, instructions: string) => {
    const s: CustomAiStyle = { id: generateUniqueId(), name, instructions, isDefault: false };
    await storageService.addCustomAiStyle(s);
    const userStyles = await storageService.getCustomAiStyles();
    setCustomAiStyles([...defaultCustomStyles, ...userStyles]);
  };
  const handleUpdateCustomStyle = async (id: string, name: string, instructions: string) => {
    const style = customAiStyles.find(s => s.id === id);
    if (style?.isDefault) return;
    await storageService.updateCustomAiStyle({ id, name, instructions });
    const userStyles = await storageService.getCustomAiStyles();
    setCustomAiStyles([...defaultCustomStyles, ...userStyles]);
    setPersonas(await storageService.getPersonas());
  };
  const handleDeleteCustomStyle = async (id: string) => {
    const style = customAiStyles.find(s => s.id === id);
    if (style?.isDefault) return;
    await storageService.deleteCustomAiStyle(id);
    const userStyles = await storageService.getCustomAiStyles();
    setCustomAiStyles([...defaultCustomStyles, ...userStyles]);
    setPersonas(await storageService.getPersonas());
  };

  // Persona handlers
  const handleSelectPersona = (personaId: string | null) => {
    if (activeAgentId) return;
    if (personaId === null) setActivePersona(defaultPersona);
    setSelectedPersonaId(personaId);
  };
  const handleSavePersona = async (name: string, config: Omit<Persona, 'id' | 'name'>) => {
    if (selectedPersonaId) {
      const updated = { ...config, id: selectedPersonaId, name };
      await storageService.updatePersona(updated);
      setPersonas(prev => prev.map(p => p.id === selectedPersonaId ? updated : p));
    } else {
      const newP = { ...config, id: generateUniqueId(), name };
      await storageService.addPersona(newP);
      setPersonas(prev => [...prev, newP]);
      setSelectedPersonaId(newP.id);
    }
  };
  const handleDeletePersona = async (personaId: string) => {
    try {
      await storageService.deletePersona(personaId);
      setPersonas(prev => prev.filter(p => p.id !== personaId));
      if (selectedPersonaId === personaId) setSelectedPersonaId(null);
    } catch (error) {
      setGlobalError(error instanceof Error ? error.message : String(error));
    }
  };

  // Agent handlers
  const handleAddAgent = async (name: string, personaId: string, projectId: string) => {
    const a: Agent = { id: generateUniqueId(), name, personaId, projectId };
    await storageService.addAgent(a);
    setAgents(prev => [...prev, a]);
  };
  const handleUpdateAgent = async (agentId: string, name: string, personaId: string, projectId: string) => {
    const updated = { id: agentId, name, personaId, projectId };
    await storageService.updateAgent(updated);
    setAgents(prev => prev.map(a => a.id === agentId ? updated : a));
  };
  const handleDeleteAgent = async (agentId: string) => {
    await storageService.deleteAgent(agentId);
    setAgents(prev => prev.filter(a => a.id !== agentId));
    if (activeAgentId === agentId) setActiveAgentId(null);
  };
  const handleSelectAgent = (agentId: string | null) => {
    setActiveAgentId(agentId);
    if (agentId) {
      const agent = agents.find(a => a.id === agentId);
      if (agent) {
        setSelectedProjectIds(new Set([agent.projectId]));
        setSelectedPersonaId(agent.personaId);
      }
    }
  };

  // Builder handlers
  const startWebAppBuild = () => setBuilderState({ ...initialBuilderState, isActive: true, currentStep: 1 });
  const resetWebAppBuild = () => setBuilderState(initialBuilderState);
  const generateWebAppPlanHandler = async () => {
    setBuilderState(prev => ({ ...prev, status: { ...prev.status, isLoading: true, message: 'AI is creating a blueprint...' } }));
    try {
      const plan = await apiService.generateWebAppPlan(builderState.idea, activeProvider, activeModel);
      setBuilderState(prev => ({ ...prev, plan, status: { ...prev.status, isLoading: false, message: '' }, currentStep: 2 }));
    } catch (e: any) {
      setGlobalError(`Plan failed: ${e.message}`);
      setBuilderState(prev => ({ ...prev, status: { ...prev.status, isLoading: false, message: 'Error occurred.' } }));
    }
  };
  const generateWebAppCodeHandler = async () => {
    setBuilderState(prev => ({ ...prev, currentStep: 4, status: { isLoading: true, message: 'Generating files...', log: [] } }));
    try {
      const files = await apiService.generateWebAppCode(builderState.plan, builderState.theme, activeProvider, activeModel);
      setBuilderState(prev => ({ ...prev, generatedFiles: files, status: { ...prev.status, isLoading: false, message: 'Complete!' }, currentStep: 5 }));
    } catch (e: any) {
      setGlobalError(`Code gen failed: ${e.message}`);
      setBuilderState(prev => ({ ...prev, status: { ...prev.status, isLoading: false, message: 'Error during generation.' } }));
    }
  };
  const loadGeneratedProjectIntoIDE = async () => {
    if (!builderState.generatedFiles || !builderState.plan?.projectName) return;
    const project = await handleCreateProject(builderState.plan.projectName);
    for (const [path, content] of Object.entries(builderState.generatedFiles)) {
      await aiCreateFile(project.id, path, content);
    }
    resetWebAppBuild();
    handleSelectAgent(null);
    handleToggleProjectSelection(project.id);
  };
  const exportGeneratedProject = async () => {
    if (!builderState.generatedFiles || !builderState.plan?.projectName) return;
    // ZIP export via JSZip CDN
    const JSZip = (window as any).JSZip;
    if (!JSZip) { setGlobalError('JSZip not loaded'); return; }
    const zip = new JSZip();
    for (const [path, content] of Object.entries(builderState.generatedFiles)) {
      zip.file(path, content);
    }
    const blob = await zip.generateAsync({ type: 'blob' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${builderState.plan.projectName}.zip`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const value: AppContextType = {
    projects, selectedProjectIds, filesByProject, activeProjectView, editingProject, isProjectPanelCollapsed,
    activePersona, selectedPersonaId, customAiStyles, personas, useWebSearch,
    activeProvider, activeModel, thinkingEnabled, thinkingBudget, workspaceMode, modelCatalog,
    agents, activeAgentId, globalError, builderState, themeId, theme, switchTheme,
    setActiveProvider, setActiveModel, setThinkingEnabled, setThinkingBudget, setWorkspaceMode,
    setUseWebSearch, setGlobalError, setSelectedProjectIds,
    handleCreateProject, handleDeleteProject, handleToggleProjectSelection, handleViewProjectFiles,
    handleAddFile, handleDeleteFile, aiCreateFile, aiUpdateFile, aiDeleteFile,
    handleSaveFileContent, handleOpenProjectSettings, handleCloseProjectSettings, handleRenameProject, handleToggleProjectPanel,
    handleSelectPersona, handleSavePersona, handleDeletePersona,
    handleAddCustomStyle, handleUpdateCustomStyle, handleDeleteCustomStyle,
    handleAddAgent, handleUpdateAgent, handleDeleteAgent, handleSelectAgent,
    setActivePersona, setBuilderState, startWebAppBuild, resetWebAppBuild,
    generateWebAppPlan: generateWebAppPlanHandler, generateWebAppCode: generateWebAppCodeHandler,
    loadGeneratedProjectIntoIDE, exportGeneratedProject,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

export const useAppContext = () => {
  const context = useContext(AppContext);
  if (!context) throw new Error('useAppContext must be used within AppProvider');
  return context;
};
