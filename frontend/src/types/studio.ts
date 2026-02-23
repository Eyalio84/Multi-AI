/** Studio types — Full-Stack React Studio (replaces Builder) */

export type StudioMode = 'chat' | 'code' | 'visual';

export interface StudioFile {
  path: string;
  content: string;
  language?: string;
  isEntry?: boolean;
}

export interface StudioProject {
  id: string;
  name: string;
  description: string;
  settings: StudioProjectSettings;
  files: Record<string, StudioFile>;
  chatHistory: StudioMessage[];
  currentVersion: number;
  createdAt: string;
  updatedAt: string;
}

export interface StudioProjectSettings {
  techStack: 'react' | 'react-ts';
  cssFramework: 'tailwind' | 'css' | 'none';
  hasBackend: boolean;
  backendFramework?: 'fastapi' | 'express';
  dependencies: Record<string, string>;
}

export interface StudioVersion {
  id: string;
  projectId: string;
  versionNumber: number;
  files: Record<string, StudioFile>;
  message: string;
  timestamp: string;
}

export interface StudioMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  files?: StudioFileChange[];
  plan?: string;
  apiSpec?: StudioApiSpec | null;
  deps?: Record<string, string>;
}

export interface StudioFileChange {
  path: string;
  content: string;
  action: 'create' | 'update' | 'delete';
}

export interface StudioApiSpec {
  openapi: string;
  info: { title: string; version: string };
  paths: Record<string, any>;
  components?: { schemas?: Record<string, any> };
}

export interface StudioApiEndpoint {
  method: string;
  path: string;
  summary?: string;
  parameters?: any[];
  requestBody?: any;
  responses?: Record<string, any>;
}

export interface StudioMockServerStatus {
  running: boolean;
  port?: number;
  pid?: number;
  endpoints?: StudioApiEndpoint[];
}

export interface StudioSelection {
  componentName: string;
  elementTag: string;
  filePath: string;
  lineNumber?: number;
  props?: Record<string, any>;
  styles?: Record<string, string>;
  text?: string;
}

export interface StudioEditorTab {
  path: string;
  isDirty: boolean;
}

export interface StudioStreamEvent {
  type: 'token' | 'thinking' | 'studio_plan' | 'studio_file' | 'studio_deps' | 'studio_api_spec' | 'done' | 'error';
  content?: string;
  path?: string;
  file_content?: string;
  deps?: Record<string, string>;
  api_spec?: StudioApiSpec;
}

export interface StudioProjectSummary {
  id: string;
  name: string;
  description: string;
  updatedAt: string;
  fileCount: number;
  versionCount: number;
}
