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
  thinking?: string;
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

// ── Pipeline Orchestration Types ──────────────────────────────────

export type StudioPipelineStrategy =
  | 'single'
  | 'advisor_builder'
  | 'builder_critic'
  | 'ping_pong'
  | 'chain';

export interface StudioPipelineStage {
  role: 'builder' | 'advisor' | 'critic' | 'image';
  provider: 'gemini' | 'claude' | 'openai';
  model: string;
}

export interface StudioVisualConfig {
  typography: 'system' | 'editorial' | 'playful' | 'minimal' | 'bold';
  theme: 'auto' | 'light' | 'dark' | 'colorful';
  motion: 'none' | 'subtle' | 'rich';
  background: 'flat' | 'gradient' | 'pattern' | 'glass';
  stateManagement: 'context' | 'zustand' | 'redux';
  stylingParadigm: 'tailwind' | 'css-modules' | 'styled' | 'inline';
  antiSlop: boolean;
  selfReflection: boolean;
}

export interface StudioPipelineConfig {
  strategy: StudioPipelineStrategy;
  stages: StudioPipelineStage[];
  visualConfig: StudioVisualConfig;
}

export interface StudioOrchestrationEvent {
  type: 'orchestration_stage' | 'advisor_suggestion' | 'critic_feedback' | 'orchestration_ping' | 'orchestration_cost' | 'studio_image';
  stage?: number;
  role?: string;
  provider?: string;
  model?: string;
  status?: string;
  content?: string;
  improvements?: string[];
  imageUrl?: string;
  originalPlaceholder?: string;
  estimated_usd?: number;
  tokens_used?: number;
  duration_ms?: number;
}

export const DEFAULT_VISUAL_CONFIG: StudioVisualConfig = {
  typography: 'system',
  theme: 'auto',
  motion: 'subtle',
  background: 'flat',
  stateManagement: 'context',
  stylingParadigm: 'inline',
  antiSlop: false,
  selfReflection: false,
};

export const DEFAULT_PIPELINE_CONFIG: StudioPipelineConfig = {
  strategy: 'single',
  stages: [],
  visualConfig: { ...DEFAULT_VISUAL_CONFIG },
};
