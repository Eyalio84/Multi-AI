export interface CustomAiStyle {
  id: string;
  name: string;
  instructions: string;
  isDefault?: boolean;
}

export interface ComposedStyle {
  name: string;
  weight: number;
}

export interface Persona {
  id: string;
  name: string;
  baseInstructions: string;
  composedStyles: ComposedStyle[];
}

export interface Agent {
  id: string;
  name: string;
  personaId: string;
  projectId: string;
}

export interface ModelConfig {
  provider: 'gemini' | 'claude';
  model: string;
  thinkingBudget?: number;
}

export interface NlkeAgent {
  name: string;
  category: string;
  description: string;
}

export interface PlaybookMeta {
  filename: string;
  title: string;
  category: string;
  difficulty: string;
  sections: string[];
  word_count: number;
  score?: number;
}
