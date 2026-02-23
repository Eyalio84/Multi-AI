// Memory + Integration types

export interface Conversation {
  id: string;
  mode: string;
  source: string;
  started_at: string;
  last_message_at: string;
  message_count: number;
  summary: string;
  messages?: ConversationMessage[];
}

export interface ConversationMessage {
  id: string;
  conversation_id: string;
  author: string;
  content: string;
  provider?: string;
  model?: string;
  metadata?: Record<string, any>;
  created_at: string;
}

export interface MemoryNode {
  id: string;
  name: string;
  type: string;
  score: number;
  properties?: Record<string, any>;
}

export interface MemoryStats {
  memory_nodes: number;
  conversations: number;
  messages: number;
  node_types: { type: string; count: number }[];
  injection_stats?: { total_injections: number; by_category: Record<string, number> };
}

export interface Integration {
  id: string | null;
  platform: string;
  enabled: boolean;
  config_keys: string[];
  message_count: number;
  user_label: string;
  created_at?: string;
  updated_at?: string;
}

export interface IntegrationSetup {
  platform: string;
  steps: string[];
  required_fields: string[];
}
