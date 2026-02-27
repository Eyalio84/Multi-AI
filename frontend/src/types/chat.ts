export enum MessageAuthor {
  USER = 'user',
  ASSISTANT = 'assistant',
  SYSTEM = 'system',
  TOOL = 'tool',
}

export type ChatMode = 'chat' | 'coding' | 'image-edit' | 'video-gen';

export interface MessagePart {
  text?: string;
  imageUrl?: string;
  videoUrl?: string;
  audioUrl?: string;
  sourceImageUrl?: string;
}

export interface ToolCall {
  id?: string;
  name: string;
  args: any;
}

export interface ToolResponse {
  name: string;
  tool_use_id?: string;
  response: {
    content: any;
    originalCode?: string;
  };
}

export interface GroundingMetadata {
  web: { uri: string; title: string };
}

export interface Message {
  id: string;
  author: MessageAuthor;
  parts: MessagePart[];
  provider?: 'gemini' | 'claude' | 'openai';
  toolCall?: ToolCall;
  toolResponse?: ToolResponse;
  groundingMetadata?: GroundingMetadata[];
  thinkingContent?: string;
  regenerationData?: any;
}
