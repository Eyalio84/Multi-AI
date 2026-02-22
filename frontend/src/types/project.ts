export interface Project {
  id: string;
  name: string;
  createdAt: number;
  dependencySummary?: string;
}

export interface ProjectFile {
  id: string;
  projectId: string;
  path: string;
  content: string;
  type: string;
  createdAt: number;
}
