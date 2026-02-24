export interface ToolParam {
  name: string;
  type: 'string' | 'text' | 'json' | 'integer' | 'float' | 'boolean';
  label: string;
  required: boolean;
  default: any;
  description: string;
  multiline: boolean;
}

export interface ToolDetail {
  id: string;
  name: string;
  category: string;
  description: string;
  is_async: boolean;
  output_format: string;
  params: ToolParam[];
}

export interface ToolSummary {
  id: string;
  name: string;
  description: string;
  is_async: boolean;
  param_count: number;
}

export interface ToolsListResponse {
  categories: string[];
  tools: Record<string, ToolSummary[]>;
  total: number;
}

export interface ToolRunResult {
  success: boolean;
  result?: any;
  error?: string;
  traceback?: string;
}
