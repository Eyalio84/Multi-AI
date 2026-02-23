// Knowledge Graph types

export interface KGDatabase {
  id: string;
  filename: string;
  path: string;
  size_bytes: number;
  size_mb: number;
}

export interface KGDatabaseStats {
  db_id: string;
  profile: string;
  node_count: number;
  edge_count: number;
  node_types: KGTypeCount[];
  edge_types: KGTypeCount[];
  has_fts: boolean;
}

export interface KGTypeCount {
  type: string;
  count: number;
}

export interface KGNode {
  id: string;
  name: string;
  type: string;
  properties: Record<string, any>;
}

export interface KGEdge {
  id: string;
  source: string;
  target: string;
  type: string;
  properties: Record<string, any>;
}

export interface KGNodePage {
  nodes: KGNode[];
  total: number;
  limit: number;
  offset: number;
}

export interface KGEdgePage {
  edges: KGEdge[];
  total: number;
  limit: number;
  offset: number;
}

export interface KGSubgraph {
  nodes: KGNode[];
  edges: KGEdge[];
}

export interface KGSearchResult {
  node: KGNode;
  score: number;
  method: string;
}

export interface KGSearchResponse {
  results: KGSearchResult[];
  query: string;
  mode: string;
  total: number;
}

export interface KGAnalyticsSummary {
  node_count: number;
  edge_count: number;
  density: number;
  components: number;
  avg_degree: number;
  clustering: number;
  isolates: number;
}

export interface KGCentralityNode {
  id: string;
  name: string;
  type: string;
  score: number;
}

export interface KGCommunity {
  id: number;
  size: number;
  members: { id: string; name: string; type: string }[];
}

export interface KGCompareResult {
  db_a: string;
  db_b: string;
  shared_nodes: number;
  unique_a: number;
  unique_b: number;
  jaccard_similarity: number;
  structural_comparison: Record<string, any>;
}

export interface KGEmbeddingStatus {
  has_embeddings: boolean;
  count: number;
  dimensions: number | null;
  coverage_pct: number;
  strategies_available: string[];
}

export interface KGProjectionPoint {
  id: string;
  name: string;
  type: string;
  x: number;
  y: number;
}

export type KGTab = 'explore' | 'search' | 'edit' | 'ingest' | 'analytics' | 'chat' | 'compare' | 'merge' | 'embeddings' | 'batch';
