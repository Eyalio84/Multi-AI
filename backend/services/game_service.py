"""Game Service — project management, structured interview, GDD synthesis.

Manages game projects through: draft → interviewing → generating → playable → editing.
Stores projects in games.db with version history and feedback for compound growth.
"""

import json
import logging
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent / "games.db"

# ── Interview Questions (18 questions, 3 story arcs) ──────────────────

INTERVIEW_QUESTIONS: list[dict] = [
    # ── Player Story (8 questions) ──────────────────────────────────
    {
        "id": "genre",
        "story": "player",
        "question": "What genre and setting is your RPG?",
        "type": "select",
        "options": [
            {"value": "fantasy_medieval", "label": "Fantasy Medieval (swords, magic, castles)"},
            {"value": "fantasy_eastern", "label": "Fantasy Eastern (martial arts, spirits)"},
            {"value": "scifi", "label": "Sci-Fi (lasers, space stations, robots)"},
            {"value": "post_apocalyptic", "label": "Post-Apocalyptic (ruins, survival)"},
            {"value": "modern_urban", "label": "Modern Urban (city, detective, mystery)"},
            {"value": "pixel_retro", "label": "Retro Pixel (classic JRPG style)"},
        ],
        "default": "fantasy_medieval",
        "kg_context": ["basic_rpg_recipe"],
        "maps_to": "meta.genre",
    },
    {
        "id": "character_desc",
        "story": "player",
        "question": "Describe your main character in a sentence.",
        "type": "text",
        "default": "A young adventurer with a mysterious past",
        "kg_context": [],
        "maps_to": "player.description",
    },
    {
        "id": "movement_style",
        "story": "player",
        "question": "How should the player move?",
        "type": "select",
        "options": [
            {"value": "free", "label": "Free Movement (smooth 8-directional, WASD/Arrows)"},
            {"value": "grid", "label": "Grid Movement (tile-by-tile, Pokemon style)"},
            {"value": "click", "label": "Click-to-Move (point and click pathfinding)"},
        ],
        "default": "free",
        "kg_context": ["free_movement", "grid_movement", "click_to_move"],
        "maps_to": "player.movement_style",
    },
    {
        "id": "abilities",
        "story": "player",
        "question": "What abilities does your character have?",
        "type": "multiselect",
        "options": [
            {"value": "melee_attack", "label": "Melee Attack (sword/punch)"},
            {"value": "ranged_attack", "label": "Ranged Attack (bow/magic bolt)"},
            {"value": "dash", "label": "Dash / Dodge Roll"},
            {"value": "heal", "label": "Heal Self"},
            {"value": "interact", "label": "Interact with Objects/NPCs"},
            {"value": "stealth", "label": "Stealth / Sneak"},
        ],
        "default": ["melee_attack", "interact"],
        "kg_context": ["action_combat", "npc_dialogue_system"],
        "maps_to": "player.abilities",
    },
    {
        "id": "hp_system",
        "story": "player",
        "question": "Should the player have a health (HP) system?",
        "type": "select",
        "options": [
            {"value": "yes", "label": "Yes, with HP bar and damage"},
            {"value": "simple", "label": "Simple (3 hearts like Zelda)"},
            {"value": "no", "label": "No health system (exploration only)"},
        ],
        "default": "yes",
        "kg_context": ["hp_system", "hp_bar_ui"],
        "maps_to": "player.hp_system",
    },
    {
        "id": "progression",
        "story": "player",
        "question": "How does the player progress?",
        "type": "multiselect",
        "options": [
            {"value": "xp_levels", "label": "XP & Level Ups"},
            {"value": "equipment", "label": "Better Equipment"},
            {"value": "skills", "label": "Skill Unlocks"},
            {"value": "story", "label": "Story Progression Only"},
        ],
        "default": ["xp_levels"],
        "kg_context": ["xp_leveling", "level_up", "equipment_slots"],
        "maps_to": "player.progression",
    },
    {
        "id": "uniqueness",
        "story": "player",
        "question": "What makes your RPG unique? (one special feature)",
        "type": "text",
        "default": "NPCs remember what you said to them",
        "kg_context": [],
        "maps_to": "meta.unique_feature",
    },
    {
        "id": "starting_scenario",
        "story": "player",
        "question": "How does the game begin?",
        "type": "text",
        "default": "You wake up in a small village with no memory of who you are",
        "kg_context": [],
        "maps_to": "meta.starting_scenario",
    },
    # ── World Story (6 questions) ───────────────────────────────────
    {
        "id": "map_size",
        "story": "world",
        "question": "How big is the game world?",
        "type": "select",
        "options": [
            {"value": "small", "label": "Small (1 screen, quick demo)"},
            {"value": "medium", "label": "Medium (3-5 connected areas)"},
            {"value": "large", "label": "Large (10+ areas with world map)"},
        ],
        "default": "medium",
        "kg_context": ["tilemap_collision", "scene_transition"],
        "maps_to": "world.map_size",
    },
    {
        "id": "tile_theme",
        "story": "world",
        "question": "What's the main environment?",
        "type": "select",
        "options": [
            {"value": "village", "label": "Village / Town"},
            {"value": "forest", "label": "Forest / Wilderness"},
            {"value": "dungeon", "label": "Dungeon / Cave"},
            {"value": "castle", "label": "Castle / Fortress"},
            {"value": "mixed", "label": "Mixed (village + dungeon)"},
        ],
        "default": "village",
        "kg_context": ["tilemap_recipe", "programmatic_tilemap"],
        "maps_to": "world.tile_theme",
    },
    {
        "id": "npc_count",
        "story": "world",
        "question": "How many NPCs in the world?",
        "type": "select",
        "options": [
            {"value": "few", "label": "1-3 NPCs"},
            {"value": "moderate", "label": "4-8 NPCs"},
            {"value": "many", "label": "9+ NPCs"},
        ],
        "default": "few",
        "kg_context": ["npc_dialogue_system"],
        "maps_to": "world.npc_count",
    },
    {
        "id": "npc_intelligence",
        "story": "world",
        "question": "How smart should NPCs be?",
        "type": "select",
        "options": [
            {"value": "static", "label": "Static (fixed dialogue lines)"},
            {"value": "branching", "label": "Branching (player choices matter)"},
            {"value": "local_llm", "label": "AI-Powered (local LLM for dynamic conversation)"},
        ],
        "default": "static",
        "kg_context": ["static_dialogue_npc", "branching_dialogue_npc", "local_llm_npc"],
        "maps_to": "world.npc_intelligence",
    },
    {
        "id": "enemies",
        "story": "world",
        "question": "What enemies exist?",
        "type": "multiselect",
        "options": [
            {"value": "none", "label": "No enemies (peaceful)"},
            {"value": "slimes", "label": "Slimes / Basic Monsters"},
            {"value": "skeletons", "label": "Skeletons / Undead"},
            {"value": "bandits", "label": "Bandits / Humanoid"},
            {"value": "boss", "label": "Boss Monster"},
            {"value": "wildlife", "label": "Hostile Wildlife"},
        ],
        "default": ["slimes"],
        "kg_context": ["enemy_basic_recipe", "enemy_patrol", "enemy_chase"],
        "maps_to": "world.enemies",
    },
    {
        "id": "interactive_objects",
        "story": "world",
        "question": "What can the player interact with?",
        "type": "multiselect",
        "options": [
            {"value": "chests", "label": "Treasure Chests"},
            {"value": "doors", "label": "Doors / Portals"},
            {"value": "signs", "label": "Signs / Books"},
            {"value": "switches", "label": "Switches / Levers"},
            {"value": "shops", "label": "Shops"},
            {"value": "save_points", "label": "Save Points"},
        ],
        "default": ["chests", "doors"],
        "kg_context": ["chest_loot_recipe", "door_teleport_recipe", "shop_recipe"],
        "maps_to": "world.interactive_objects",
    },
    # ── Technical Story (4 questions) ───────────────────────────────
    {
        "id": "combat_system",
        "story": "technical",
        "question": "What combat system?",
        "type": "select",
        "options": [
            {"value": "none", "label": "None (exploration/puzzle game)"},
            {"value": "action", "label": "Action (real-time attacks, Zelda-like)"},
            {"value": "turn_based", "label": "Turn-Based (menu-driven, Final Fantasy-like)"},
        ],
        "default": "action",
        "kg_context": ["action_combat", "turn_based_combat", "combat_action_recipe"],
        "maps_to": "systems.combat",
    },
    {
        "id": "inventory_system",
        "story": "technical",
        "question": "What inventory system?",
        "type": "select",
        "options": [
            {"value": "none", "label": "No inventory"},
            {"value": "simple", "label": "Simple (list of items)"},
            {"value": "full", "label": "Full (categories, equip slots, crafting)"},
        ],
        "default": "simple",
        "kg_context": ["simple_inventory", "full_inventory", "inventory_recipe"],
        "maps_to": "systems.inventory",
    },
    {
        "id": "audio",
        "story": "technical",
        "question": "Audio support?",
        "type": "select",
        "options": [
            {"value": "none", "label": "No audio"},
            {"value": "sfx", "label": "Sound effects only"},
            {"value": "full", "label": "Music + Sound effects"},
        ],
        "default": "sfx",
        "kg_context": ["audio_recipe"],
        "maps_to": "systems.audio",
    },
    {
        "id": "local_model",
        "story": "technical",
        "question": "Local LLM for AI NPCs?",
        "type": "select",
        "options": [
            {"value": "none", "label": "No local model"},
            {"value": "deepseek", "label": "DeepSeek R1 1.5B (best reasoning)"},
            {"value": "gemma3_1b", "label": "Gemma 3 1B (fastest responses)"},
            {"value": "gemma2_2b", "label": "Gemma 2 2B (richest dialogue)"},
            {"value": "qwen", "label": "Qwen 2.5 (multilingual)"},
        ],
        "default": "none",
        "kg_context": ["local_llm_deepseek", "local_llm_gemma3_1b", "local_llm_gemma2_2b", "local_llm_qwen"],
        "maps_to": "local_llm.model",
    },
]


class GameService:
    """Manages game projects, interviews, and GDD synthesis."""

    def __init__(self):
        self._conn: sqlite3.Connection | None = None

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
            self._init_schema()
        return self._conn

    def _init_schema(self):
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS game_projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                status TEXT DEFAULT 'draft',
                interview_data TEXT DEFAULT '{}',
                game_design_doc TEXT DEFAULT '{}',
                files TEXT DEFAULT '{}',
                settings TEXT DEFAULT '{}',
                expert_id TEXT DEFAULT '',
                current_version INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS game_versions (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                version_number INTEGER NOT NULL,
                files TEXT DEFAULT '{}',
                message TEXT DEFAULT '',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES game_projects(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS game_feedback (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                pattern_name TEXT NOT NULL,
                pattern_type TEXT DEFAULT 'generated_recipe',
                pattern_data TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES game_projects(id) ON DELETE CASCADE
            );
        """)
        self._conn.commit()

    def _row_to_dict(self, row: sqlite3.Row | None) -> dict | None:
        if row is None:
            return None
        d = dict(row)
        for key in ("interview_data", "game_design_doc", "files", "settings", "pattern_data"):
            if key in d and isinstance(d[key], str):
                try:
                    d[key] = json.loads(d[key])
                except (json.JSONDecodeError, TypeError):
                    pass
        return d

    # ── CRUD ──────────────────────────────────────────────────────

    def create_project(self, name: str, description: str = "") -> dict:
        conn = self._get_conn()
        project_id = str(uuid.uuid4())[:8]
        now = datetime.utcnow().isoformat()
        conn.execute(
            "INSERT INTO game_projects (id, name, description, created_at, updated_at) VALUES (?,?,?,?,?)",
            (project_id, name, description, now, now),
        )
        conn.commit()
        return self.get_project(project_id)

    def get_project(self, project_id: str) -> dict | None:
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM game_projects WHERE id=?", (project_id,)).fetchone()
        return self._row_to_dict(row)

    def list_projects(self) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM game_projects ORDER BY updated_at DESC").fetchall()
        return [self._row_to_dict(r) for r in rows]

    def update_project(self, project_id: str, updates: dict) -> dict | None:
        conn = self._get_conn()
        existing = self.get_project(project_id)
        if not existing:
            return None

        json_fields = {"interview_data", "game_design_doc", "files", "settings"}
        sets = ["updated_at = ?"]
        vals: list[Any] = [datetime.utcnow().isoformat()]

        for key, val in updates.items():
            if key in ("id", "created_at"):
                continue
            if key in json_fields and not isinstance(val, str):
                val = json.dumps(val)
            sets.append(f"{key} = ?")
            vals.append(val)

        vals.append(project_id)
        conn.execute(f"UPDATE game_projects SET {', '.join(sets)} WHERE id=?", vals)
        conn.commit()
        return self.get_project(project_id)

    def delete_project(self, project_id: str) -> bool:
        conn = self._get_conn()
        conn.execute("DELETE FROM game_projects WHERE id=?", (project_id,))
        conn.commit()
        return True

    # ── Interview ─────────────────────────────────────────────────

    def get_interview_questions(self) -> list[dict]:
        return INTERVIEW_QUESTIONS

    def submit_answer(self, project_id: str, question_id: str, answer: Any) -> dict | None:
        project = self.get_project(project_id)
        if not project:
            return None

        interview_data = project.get("interview_data", {})
        if isinstance(interview_data, str):
            interview_data = json.loads(interview_data) if interview_data else {}

        interview_data[question_id] = answer

        # Check completion
        answered = set(interview_data.keys())
        total = {q["id"] for q in INTERVIEW_QUESTIONS}
        all_answered = total.issubset(answered)

        status = "interviewing"
        if all_answered:
            status = "interviewing"  # Keep interviewing until explicit synthesize

        self.update_project(project_id, {
            "interview_data": interview_data,
            "status": status,
        })

        return {
            "project_id": project_id,
            "question_id": question_id,
            "answer": answer,
            "progress": len(answered),
            "total": len(total),
            "complete": all_answered,
        }

    # ── GDD Synthesis ─────────────────────────────────────────────

    def synthesize_gdd(self, project_id: str) -> dict | None:
        project = self.get_project(project_id)
        if not project:
            return None

        data = project.get("interview_data", {})
        if isinstance(data, str):
            data = json.loads(data) if data else {}

        # Build structured GDD from interview answers
        enemies_list = data.get("enemies", ["slimes"])
        if "none" in enemies_list:
            enemies_list = []

        npc_count_map = {"few": 3, "moderate": 6, "many": 12}
        npc_count = npc_count_map.get(data.get("npc_count", "few"), 3)

        # Generate NPC definitions
        npcs = []
        npc_templates = self._generate_npc_templates(
            count=npc_count,
            intelligence=data.get("npc_intelligence", "static"),
            genre=data.get("genre", "fantasy_medieval"),
            setting=data.get("tile_theme", "village"),
        )
        npcs = npc_templates

        # Generate enemy definitions
        enemies = []
        for enemy_type in enemies_list:
            enemies.append(self._generate_enemy_template(enemy_type, data.get("genre", "fantasy_medieval")))

        gdd = {
            "meta": {
                "name": project.get("name", "Untitled RPG"),
                "genre": data.get("genre", "fantasy_medieval"),
                "unique_feature": data.get("uniqueness", ""),
                "starting_scenario": data.get("starting_scenario", "You begin your adventure..."),
                "description": project.get("description", ""),
            },
            "player": {
                "description": data.get("character_desc", "A brave adventurer"),
                "movement_style": data.get("movement_style", "free"),
                "abilities": data.get("abilities", ["melee_attack", "interact"]),
                "hp_system": data.get("hp_system", "yes"),
                "progression": data.get("progression", ["xp_levels"]),
                "base_stats": {
                    "hp": 100,
                    "mp": 50,
                    "strength": 10,
                    "defense": 5,
                    "speed": 160,
                },
            },
            "world": {
                "map_size": data.get("map_size", "medium"),
                "tile_theme": data.get("tile_theme", "village"),
                "interactive_objects": data.get("interactive_objects", ["chests", "doors"]),
            },
            "npcs": npcs,
            "enemies": enemies,
            "systems": {
                "combat": data.get("combat_system", "action"),
                "inventory": data.get("inventory_system", "simple"),
                "audio": data.get("audio", "sfx"),
            },
            "local_llm": {
                "model": data.get("local_model", "none"),
                "enabled": data.get("local_model", "none") != "none",
                "npc_intelligence": data.get("npc_intelligence", "static"),
            },
        }

        self.update_project(project_id, {
            "game_design_doc": gdd,
            "status": "generating",
        })

        return gdd

    def _generate_npc_templates(self, count: int, intelligence: str, genre: str, setting: str) -> list[dict]:
        """Generate NPC template definitions based on interview choices."""
        genre_names = {
            "fantasy_medieval": ["Elena", "Thorin", "Mira", "Gideon", "Sage Alaric", "Rosalind",
                                 "Barkeep Holt", "Captain Brynn", "Witch Agatha", "Farmer Odric",
                                 "Priestess Luna", "Blacksmith Kael"],
            "fantasy_eastern": ["Master Li", "Mei", "Akira", "Jade", "Ren", "Lotus",
                                "Elder Shu", "Monk Taro", "Fox Spirit Yuki", "General Zhao",
                                "Herbalist Lin", "Merchant Chen"],
            "scifi": ["Dr. Nova", "ARIA-7", "Rex", "Commander Vex", "Zara", "Bot-4N",
                      "Professor Quark", "Pilot Dash", "Engineer Sparks", "Admiral Storm",
                      "Medic Pulse", "Trader Neon"],
            "post_apocalyptic": ["Ash", "Rust", "Doc Mercy", "Scrapper Kai", "Elder Hope", "Wolf",
                                 "Trader Six", "Guard Stone", "Healer Dawn", "Scout Ember",
                                 "Chief Raven", "Mechanic Bolt"],
            "modern_urban": ["Detective Kay", "Professor Chen", "Barista Max", "Officer Diaz",
                             "Librarian Rose", "Hacker Zero", "Chef Marco", "Reporter Jade",
                             "Doctor Patel", "Shopkeeper Sam", "Janitor Pete", "Mayor Chen"],
            "pixel_retro": ["Elder Sage", "Knight Arin", "Mage Zell", "Thief Vex", "Princess Eira",
                            "Merchant Pip", "Guard Rex", "Healer Fay", "King Aldric", "Bard Lyra",
                            "Witch Hex", "Farmer Joe"],
        }

        role_pool = ["quest_giver", "shopkeeper", "story", "guard", "trainer", "wandering",
                     "companion", "healer", "guide", "merchant"]

        names = genre_names.get(genre, genre_names["fantasy_medieval"])
        npcs = []
        for i in range(min(count, len(names))):
            role = role_pool[i % len(role_pool)]
            npc = {
                "name": names[i],
                "role": role,
                "intelligence": intelligence,
                "dialogue_lines": 3 if intelligence == "static" else 0,
                "personality": f"A {role.replace('_', ' ')} in the {setting}",
            }
            if intelligence == "local_llm":
                npc["system_prompt"] = (
                    f"You are {names[i]}, a {role.replace('_', ' ')} in a {genre.replace('_', ' ')} world. "
                    f"Stay in character. Keep responses short (1-3 sentences). "
                    f"Be helpful but mysterious."
                )
            npcs.append(npc)

        return npcs

    def _generate_enemy_template(self, enemy_type: str, genre: str) -> dict:
        """Generate enemy definition from type."""
        templates = {
            "slimes": {"name": "Slime", "hp": 20, "damage": 5, "speed": 40, "xp": 10, "color": "0x44ff44", "behavior": "patrol"},
            "skeletons": {"name": "Skeleton", "hp": 40, "damage": 10, "speed": 60, "xp": 25, "color": "0xcccccc", "behavior": "chase"},
            "bandits": {"name": "Bandit", "hp": 50, "damage": 12, "speed": 80, "xp": 30, "color": "0xaa4444", "behavior": "chase"},
            "boss": {"name": "Boss", "hp": 200, "damage": 25, "speed": 50, "xp": 100, "color": "0xff0000", "behavior": "boss_pattern", "is_boss": True},
            "wildlife": {"name": "Wild Beast", "hp": 30, "damage": 8, "speed": 70, "xp": 15, "color": "0x886644", "behavior": "patrol"},
        }
        return templates.get(enemy_type, templates["slimes"])

    # ── Versions ──────────────────────────────────────────────────

    def save_version(self, project_id: str, message: str = "") -> dict | None:
        project = self.get_project(project_id)
        if not project:
            return None

        conn = self._get_conn()
        version_id = str(uuid.uuid4())[:8]
        version_number = project.get("current_version", 0) + 1

        files = project.get("files", {})
        if isinstance(files, dict):
            files = json.dumps(files)

        conn.execute(
            "INSERT INTO game_versions (id, project_id, version_number, files, message) VALUES (?,?,?,?,?)",
            (version_id, project_id, version_number, files, message),
        )
        conn.execute(
            "UPDATE game_projects SET current_version=?, updated_at=? WHERE id=?",
            (version_number, datetime.utcnow().isoformat(), project_id),
        )
        conn.commit()

        return {"id": version_id, "version_number": version_number, "message": message}

    def list_versions(self, project_id: str) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM game_versions WHERE project_id=? ORDER BY version_number DESC",
            (project_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def restore_version(self, project_id: str, version_number: int) -> dict | None:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM game_versions WHERE project_id=? AND version_number=?",
            (project_id, version_number),
        ).fetchone()
        if not row:
            return None

        files = row["files"]
        if isinstance(files, str):
            try:
                files = json.loads(files)
            except json.JSONDecodeError:
                pass

        self.update_project(project_id, {"files": files, "status": "playable"})
        return self.get_project(project_id)

    # ── Feedback / Compound Growth ────────────────────────────────

    def extract_patterns(self, project_id: str) -> list[dict]:
        """Extract reusable patterns from a completed game for KG enrichment."""
        project = self.get_project(project_id)
        if not project:
            return []

        gdd = project.get("game_design_doc", {})
        files = project.get("files", {})
        if not gdd or not files:
            return []

        conn = self._get_conn()
        patterns = []

        # Extract movement pattern
        movement = gdd.get("player", {}).get("movement_style", "free")
        pattern = {
            "id": str(uuid.uuid4())[:8],
            "project_id": project_id,
            "pattern_name": f"generated_{movement}_movement",
            "pattern_type": "generated_recipe",
            "pattern_data": json.dumps({
                "movement_style": movement,
                "source_project": project.get("name", ""),
                "genre": gdd.get("meta", {}).get("genre", ""),
                "code_file": "js/player.js",
                "code_snippet": files.get("js/player.js", "")[:500],
            }),
        }
        conn.execute(
            "INSERT OR IGNORE INTO game_feedback (id, project_id, pattern_name, pattern_type, pattern_data) VALUES (?,?,?,?,?)",
            (pattern["id"], pattern["project_id"], pattern["pattern_name"], pattern["pattern_type"], pattern["pattern_data"]),
        )
        patterns.append(pattern)

        # Extract combat pattern
        combat = gdd.get("systems", {}).get("combat", "none")
        if combat != "none":
            cp = {
                "id": str(uuid.uuid4())[:8],
                "project_id": project_id,
                "pattern_name": f"generated_{combat}_combat",
                "pattern_type": "generated_recipe",
                "pattern_data": json.dumps({
                    "combat_type": combat,
                    "source_project": project.get("name", ""),
                    "code_file": "js/combat.js",
                    "code_snippet": files.get("js/combat.js", "")[:500],
                }),
            }
            conn.execute(
                "INSERT OR IGNORE INTO game_feedback (id, project_id, pattern_name, pattern_type, pattern_data) VALUES (?,?,?,?,?)",
                (cp["id"], cp["project_id"], cp["pattern_name"], cp["pattern_type"], cp["pattern_data"]),
            )
            patterns.append(cp)

        # Extract NPC intelligence pattern
        npc_intel = gdd.get("local_llm", {}).get("npc_intelligence", "static")
        if npc_intel != "static":
            np_entry = {
                "id": str(uuid.uuid4())[:8],
                "project_id": project_id,
                "pattern_name": f"generated_{npc_intel}_npc",
                "pattern_type": "generated_recipe",
                "pattern_data": json.dumps({
                    "intelligence": npc_intel,
                    "model": gdd.get("local_llm", {}).get("model", "none"),
                    "source_project": project.get("name", ""),
                    "npc_count": len(gdd.get("npcs", [])),
                }),
            }
            conn.execute(
                "INSERT OR IGNORE INTO game_feedback (id, project_id, pattern_name, pattern_type, pattern_data) VALUES (?,?,?,?,?)",
                (np_entry["id"], np_entry["project_id"], np_entry["pattern_name"], np_entry["pattern_type"], np_entry["pattern_data"]),
            )
            patterns.append(np_entry)

        conn.commit()

        # Optionally push to KG
        try:
            from services.kg_service import kg_service
            kg_nodes = []
            for p in patterns:
                pd = json.loads(p["pattern_data"]) if isinstance(p["pattern_data"], str) else p["pattern_data"]
                kg_nodes.append({
                    "name": p["pattern_name"],
                    "type": "generated_recipe",
                    "properties": pd,
                })
            if kg_nodes:
                kg_service.bulk_create("phaser-complete-kg", kg_nodes, [])
                logger.info(f"Added {len(kg_nodes)} patterns to phaser-complete-kg")
        except Exception as ex:
            logger.warning(f"KG enrichment skipped: {ex}")

        return patterns

    # ── Expert Auto-Creation ──────────────────────────────────────

    def ensure_expert(self) -> str:
        """Create the Phaser expert if it doesn't exist. Returns expert_id."""
        try:
            from services.expert_service import expert_service
            experts = expert_service.list_experts()
            for ex in experts:
                if ex.get("name") == "GameForge":
                    return ex["id"]

            expert = expert_service.create_expert({
                "name": "GameForge",
                "description": "Phaser 3 RPG game engine specialist. Helps design, build, and refine 2D RPG games with structured interviews, AI code generation, and local LLM NPC support.",
                "kg_db_id": "phaser-complete-kg",
                "kg_db_ids": ["phaser-complete-kg"],
                "persona_name": "GameForge",
                "persona_instructions": (
                    "You are GameForge, a Phaser 3 RPG game development expert. "
                    "You help users design and build complete 2D RPG games. "
                    "When answering questions, reference specific Phaser 3 API methods and patterns from the KG. "
                    "Provide code snippets that use Phaser 3.90.0 API correctly. "
                    "Always suggest programmatic sprite generation when no external assets are available."
                ),
                "persona_style": "technical_friendly",
                "retrieval_methods": ["hybrid", "intent"],
                "retrieval_alpha": 0.30,
                "retrieval_beta": 0.45,
                "retrieval_gamma": 0.15,
                "retrieval_delta": 0.10,
                "icon": "gamepad",
                "color": "#10b981",
                "is_public": True,
            })
            return expert["id"]
        except Exception as ex:
            logger.warning(f"Expert auto-creation failed: {ex}")
            return ""


game_service = GameService()
