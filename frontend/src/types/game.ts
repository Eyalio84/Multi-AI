export interface GameProject {
  id: string;
  name: string;
  description: string;
  status: 'draft' | 'interviewing' | 'generating' | 'playable' | 'editing';
  interview_data: Record<string, any>;
  game_design_doc: GameDesignDoc | null;
  files: Record<string, string>;
  settings: Record<string, any>;
  expert_id: string;
  current_version: number;
  created_at: string;
  updated_at: string;
}

export interface GameDesignDoc {
  meta: {
    name: string;
    genre: string;
    unique_feature: string;
    starting_scenario: string;
    description: string;
  };
  player: {
    description: string;
    movement_style: 'free' | 'grid' | 'click';
    abilities: string[];
    hp_system: string;
    progression: string[];
    base_stats: { hp: number; mp: number; strength: number; defense: number; speed: number };
  };
  world: {
    map_size: string;
    tile_theme: string;
    interactive_objects: string[];
  };
  npcs: GameNPC[];
  enemies: GameEnemy[];
  systems: {
    combat: string;
    inventory: string;
    audio: string;
  };
  local_llm: {
    model: string;
    enabled: boolean;
    npc_intelligence: string;
  };
}

export interface GameNPC {
  name: string;
  role: string;
  intelligence: string;
  dialogue_lines: number;
  personality: string;
  system_prompt?: string;
}

export interface GameEnemy {
  name: string;
  hp: number;
  damage: number;
  speed: number;
  xp: number;
  color: string;
  behavior: string;
  is_boss?: boolean;
}

export interface InterviewQuestion {
  id: string;
  story: 'player' | 'world' | 'technical';
  question: string;
  type: 'select' | 'multiselect' | 'text';
  options?: { value: string; label: string }[];
  default?: string | string[];
  kg_context: string[];
  maps_to: string;
}

export interface GameVersion {
  id: string;
  project_id: string;
  version_number: number;
  files: string;
  message: string;
  timestamp: string;
}
