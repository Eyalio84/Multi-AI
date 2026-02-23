// Expert + KG-OS types

export interface Expert {
  id: string;
  name: string;
  description: string;
  kg_db_id: string;
  kg_db_ids: string[];
  persona_name: string;
  persona_instructions: string;
  persona_style: string;
  retrieval_methods: string[];
  retrieval_alpha: number;
  retrieval_beta: number;
  retrieval_gamma: number;
  retrieval_delta: number;
  retrieval_limit: number;
  dimension_filters: Record<string, { min?: number; max?: number }>;
  playbook_skills: string[];
  custom_goal_mappings: Record<string, string[]>;
  icon: string;
  color: string;
  is_public: boolean;
  created_at: string;
  updated_at: string;
}

export interface ExpertConversation {
  id: string;
  expert_id: string;
  title: string;
  message_count: number;
  created_at: string;
  last_message_at: string;
  messages?: ExpertMessage[];
}

export interface ExpertMessage {
  id: string;
  conversation_id: string;
  author: 'user' | 'assistant';
  content: string;
  sources: ExpertSource[];
  retrieval_meta: Record<string, any>;
  created_at: string;
}

export interface ExpertSource {
  id: string;
  name: string;
  type: string;
  score: number;
  method: string;
  db_id?: string;
}

export interface KGOSSearchResult {
  node: { id: string; name: string; type: string; properties: Record<string, any> };
  score: number;
  method: string;
  scores: { embedding: number; text: number; graph: number; intent: number };
}

export interface KGOSSearchResponse {
  results: KGOSSearchResult[];
  query: string;
  intent: string;
  weights: { alpha: number; beta: number; gamma: number; delta: number };
  total: number;
}
