import { Agent, CustomAiStyle, Persona, Project, ProjectFile } from '../types/index';

const PROJECTS_KEY = 'gemini_projects';
const FILES_KEY_PREFIX = 'gemini_files_';
const CUSTOM_STYLES_KEY = 'gemini_custom_ai_styles';
const PERSONAS_KEY = 'gemini_personas';
const AGENTS_KEY = 'gemini_agents';
const SETTINGS_KEY = 'workspace_settings';

const getFromStorage = <T>(key: string, defaultValue: T): T => {
  try {
    const data = localStorage.getItem(key);
    if (data) return JSON.parse(data) as T;
    return defaultValue;
  } catch {
    return defaultValue;
  }
};

const saveToStorage = <T>(key: string, data: T) => {
  try {
    localStorage.setItem(key, JSON.stringify(data));
  } catch (e) {
    console.error(`Failed to save "${key}"`, e);
  }
};

// Settings
export interface WorkspaceSettings {
  mode: 'standalone' | 'claude-code';
  defaultGeminiModel: string;
  defaultClaudeModel: string;
  thinkingBudget: number;
}

const defaultSettings: WorkspaceSettings = {
  mode: 'standalone',
  defaultGeminiModel: 'gemini-2.5-flash',
  defaultClaudeModel: 'claude-sonnet-4-6',
  thinkingBudget: 0,
};

export const getSettings = (): WorkspaceSettings => getFromStorage(SETTINGS_KEY, defaultSettings);
export const saveSettings = (settings: WorkspaceSettings) => saveToStorage(SETTINGS_KEY, settings);

// Agents
export const getAgents = async (): Promise<Agent[]> => getFromStorage<Agent[]>(AGENTS_KEY, []);
export const addAgent = async (agent: Agent) => { const agents = await getAgents(); saveToStorage(AGENTS_KEY, [...agents, agent]); };
export const updateAgent = async (updated: Agent) => { const agents = await getAgents(); saveToStorage(AGENTS_KEY, agents.map(a => a.id === updated.id ? updated : a)); };
export const deleteAgent = async (id: string) => { const agents = await getAgents(); saveToStorage(AGENTS_KEY, agents.filter(a => a.id !== id)); };

// Personas
export const getPersonas = async (): Promise<Persona[]> => getFromStorage<Persona[]>(PERSONAS_KEY, []);
export const addPersona = async (persona: Persona) => { const personas = await getPersonas(); saveToStorage(PERSONAS_KEY, [...personas, persona]); };
export const updatePersona = async (updated: Persona) => { const personas = await getPersonas(); saveToStorage(PERSONAS_KEY, personas.map(p => p.id === updated.id ? updated : p)); };
export const deletePersona = async (id: string) => {
  const agents = await getAgents();
  const using = agents.filter(a => a.personaId === id);
  if (using.length > 0) throw new Error(`Persona in use by: ${using.map(a => a.name).join(', ')}`);
  const personas = await getPersonas();
  saveToStorage(PERSONAS_KEY, personas.filter(p => p.id !== id));
};

// Custom AI Styles
export const getCustomAiStyles = async (): Promise<CustomAiStyle[]> => getFromStorage<CustomAiStyle[]>(CUSTOM_STYLES_KEY, []);
export const addCustomAiStyle = async (style: CustomAiStyle) => { const styles = await getCustomAiStyles(); saveToStorage(CUSTOM_STYLES_KEY, [...styles, style]); };
export const updateCustomAiStyle = async (updated: CustomAiStyle) => {
  const styles = await getCustomAiStyles();
  const oldStyle = styles.find(s => s.id === updated.id);
  saveToStorage(CUSTOM_STYLES_KEY, styles.map(s => s.id === updated.id ? updated : s));
  if (oldStyle && oldStyle.name !== updated.name) {
    const personas = await getPersonas();
    const updatedPersonas = personas.map(p => ({
      ...p,
      composedStyles: p.composedStyles.map(cs => cs.name === oldStyle.name ? { ...cs, name: updated.name } : cs),
    }));
    saveToStorage(PERSONAS_KEY, updatedPersonas);
  }
};
export const deleteCustomAiStyle = async (id: string) => {
  const styles = await getCustomAiStyles();
  const toDelete = styles.find(s => s.id === id);
  if (!toDelete) return;
  saveToStorage(CUSTOM_STYLES_KEY, styles.filter(s => s.id !== id));
  const personas = await getPersonas();
  saveToStorage(PERSONAS_KEY, personas.map(p => ({ ...p, composedStyles: p.composedStyles.filter(cs => cs.name !== toDelete.name) })));
};

// Projects & Files
export const getProjects = async (): Promise<Project[]> => getFromStorage<Project[]>(PROJECTS_KEY, []);
export const addProject = async (project: Project) => { const projects = await getProjects(); saveToStorage(PROJECTS_KEY, [...projects, project]); };
export const updateProject = async (updated: Project) => { const projects = await getProjects(); saveToStorage(PROJECTS_KEY, projects.map(p => p.id === updated.id ? updated : p)); };
export const deleteProject = async (id: string) => {
  saveToStorage(PROJECTS_KEY, (await getProjects()).filter(p => p.id !== id));
  localStorage.removeItem(`${FILES_KEY_PREFIX}${id}`);
  saveToStorage(AGENTS_KEY, (await getAgents()).filter(a => a.projectId !== id));
};
export const getFilesByProject = async (projectId: string): Promise<ProjectFile[]> => getFromStorage<ProjectFile[]>(`${FILES_KEY_PREFIX}${projectId}`, []);
export const addFile = async (file: ProjectFile) => { const files = await getFilesByProject(file.projectId); saveToStorage(`${FILES_KEY_PREFIX}${file.projectId}`, [...files, file]); };
export const deleteFile = async (fileId: string, projectId: string) => { const files = await getFilesByProject(projectId); saveToStorage(`${FILES_KEY_PREFIX}${projectId}`, files.filter(f => f.id !== fileId)); };
export const updateFile = async (projectId: string, updated: ProjectFile) => { const files = await getFilesByProject(projectId); saveToStorage(`${FILES_KEY_PREFIX}${projectId}`, files.map(f => f.id === updated.id ? updated : f)); };

// File Reader
export const readFileAsText = (file: File): Promise<string> => new Promise((resolve, reject) => { const r = new FileReader(); r.onload = () => resolve(r.result as string); r.onerror = reject; r.readAsText(file); });
