"""Game Generator — transforms GDD into complete playable Phaser 3 game files.

Uses AI (Gemini/Claude) for creative scene generation and templates for
structural code. Streams via AsyncGenerator with ### FILE: markers.
"""

import json
import logging
import re
from typing import AsyncGenerator

logger = logging.getLogger(__name__)

# ── System Prompt ─────────────────────────────────────────────────────

GAME_SYSTEM_PROMPT = """\
You are GameForge, a Phaser 3.90.0 game code generator specializing in 2D RPGs.

You generate complete, runnable Phaser 3 game files. Each file is wrapped in markers:

### FILE: js/scene.js
// complete file content here
### END FILE

Rules:
- Use Phaser 3.90.0 API (loaded via local phaser.min.js, NOT CDN)
- Use ES6 classes extending Phaser.Scene
- Use Arcade Physics for all movement/collision
- Generate programmatic sprites via Graphics API + generateTexture (NO external image files)
- All code must be complete and runnable - NO TODOs or placeholders
- Do NOT use markdown code fences inside file markers
- Keep individual files focused (one class per file)
- Use consistent naming: PlayerScene, UIScene, BattleScene
- Player speed should be 160 for free movement, 32px grid for grid movement
- Always include collision with world bounds
"""

REFINE_SYSTEM_PROMPT = """\
You are GameForge, a Phaser 3 game code refiner. The user has an existing game and wants changes.

Existing files are provided. When refining:
1. Briefly describe what you will change (1-2 sentences).
2. Only output files that changed using the same marker format:

### FILE: js/player.js
// complete updated content
### END FILE

Rules:
- Maintain Phaser 3.90.0 API compatibility
- Generate complete file contents, not diffs
- Do NOT use markdown code fences inside file markers
- Preserve existing game structure and naming
"""


# ── Templates ─────────────────────────────────────────────────────────

def _gen_index_html(gdd: dict) -> str:
    """Generate index.html that loads Phaser from local file."""
    name = gdd.get("meta", {}).get("name", "RPG Game")
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>{name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ background: #000; overflow: hidden; display: flex; justify-content: center; align-items: center; height: 100vh; }}
        #game-container {{ position: relative; }}
        canvas {{ display: block; image-rendering: pixelated; }}
    </style>
</head>
<body>
    <div id="game-container"></div>
    <script src="/docs/phaser/phaser.min.js"></script>
    <script src="js/config.js"></script>
    <script src="js/player.js"></script>
    <script src="js/npc.js"></script>
    <script src="js/enemy.js"></script>
    <script src="js/combat.js"></script>
    <script src="js/inventory.js"></script>
    <script src="js/scene.js"></script>
    <script src="js/main.js"></script>
</body>
</html>"""


def _gen_config_js(gdd: dict) -> str:
    """Generate game configuration from GDD."""
    player = gdd.get("player", {})
    world = gdd.get("world", {})
    systems = gdd.get("systems", {})

    map_sizes = {"small": (800, 600), "medium": (1600, 1200), "large": (3200, 2400)}
    w, h = map_sizes.get(world.get("map_size", "medium"), (1600, 1200))

    return f"""// Game Configuration — generated from GDD
const GAME_CONFIG = {{
    meta: {{
        name: '{gdd.get("meta", {}).get("name", "RPG Game")}',
        genre: '{gdd.get("meta", {}).get("genre", "fantasy_medieval")}',
    }},
    player: {{
        speed: {160 if player.get('movement_style') == 'free' else 100},
        movementStyle: '{player.get("movement_style", "free")}',
        hp: {player.get("base_stats", {}).get("hp", 100)},
        mp: {player.get("base_stats", {}).get("mp", 50)},
        strength: {player.get("base_stats", {}).get("strength", 10)},
        defense: {player.get("base_stats", {}).get("defense", 5)},
        abilities: {json.dumps(player.get("abilities", ["melee_attack", "interact"]))},
        hpSystem: '{player.get("hp_system", "yes")}',
    }},
    world: {{
        width: {w},
        height: {h},
        tileSize: 32,
        theme: '{world.get("tile_theme", "village")}',
        mapSize: '{world.get("map_size", "medium")}',
    }},
    systems: {{
        combat: '{systems.get("combat", "action")}',
        inventory: '{systems.get("inventory", "simple")}',
        audio: '{systems.get("audio", "sfx")}',
    }},
    npcs: {json.dumps([{"name": n.get("name","NPC"), "role": n.get("role","story"), "intelligence": n.get("intelligence","static")} for n in gdd.get("npcs", [])])},
    enemies: {json.dumps([{"name": e.get("name","Slime"), "hp": e.get("hp",20), "damage": e.get("damage",5), "speed": e.get("speed",40), "xp": e.get("xp",10), "color": e.get("color","0x44ff44"), "behavior": e.get("behavior","patrol")} for e in gdd.get("enemies", [])])},
}};
"""


def _gen_main_js(gdd: dict) -> str:
    """Generate main.js entry point."""
    return """// Main entry point
const config = {
    type: Phaser.AUTO,
    width: 800,
    height: 600,
    parent: 'game-container',
    pixelArt: true,
    roundPixels: true,
    physics: {
        default: 'arcade',
        arcade: {
            gravity: { y: 0 },
            debug: false
        }
    },
    scale: {
        mode: Phaser.Scale.FIT,
        autoCenter: Phaser.Scale.CENTER_BOTH
    },
    scene: [GameScene]
};

const game = new Phaser.Game(config);
"""


def _gen_player_js(gdd: dict) -> str:
    """Generate player class based on movement style."""
    movement = gdd.get("player", {}).get("movement_style", "free")
    hp_system = gdd.get("player", {}).get("hp_system", "yes")
    stats = gdd.get("player", {}).get("base_stats", {})

    hp_code = ""
    if hp_system != "no":
        hp_code = f"""
        this.maxHp = {stats.get('hp', 100)};
        this.hp = this.maxHp;
        this.strength = {stats.get('strength', 10)};
        this.defense = {stats.get('defense', 5)};
        this.level = 1;
        this.xp = 0;
        this.xpToLevel = 100;"""

    if movement == "grid":
        return f"""// Player class — Grid Movement (Pokemon-style)
class Player extends Phaser.Physics.Arcade.Sprite {{
    constructor(scene, x, y) {{
        super(scene, x, y, 'player');
        scene.add.existing(this);
        scene.physics.add.existing(this);

        this.setCollideWorldBounds(true);
        this.body.setSize(28, 28);
        this.body.setOffset(2, 2);

        this.tileSize = GAME_CONFIG.world.tileSize;
        this.isMoving = false;
        this.moveSpeed = 4; // pixels per frame during move
        this.targetX = this.x;
        this.targetY = this.y;
        this.facing = 'down';
        this.canInteract = true;
        {hp_code}
    }}

    update(cursors) {{
        if (this.isMoving) {{
            const dx = this.targetX - this.x;
            const dy = this.targetY - this.y;
            const dist = Math.sqrt(dx * dx + dy * dy);

            if (dist < this.moveSpeed) {{
                this.x = this.targetX;
                this.y = this.targetY;
                this.body.setVelocity(0, 0);
                this.isMoving = false;
            }}
            return;
        }}

        if (cursors.left.isDown) {{
            this.targetX = this.x - this.tileSize;
            this.isMoving = true;
            this.facing = 'left';
            this.body.setVelocityX(-GAME_CONFIG.player.speed);
        }} else if (cursors.right.isDown) {{
            this.targetX = this.x + this.tileSize;
            this.isMoving = true;
            this.facing = 'right';
            this.body.setVelocityX(GAME_CONFIG.player.speed);
        }} else if (cursors.up.isDown) {{
            this.targetY = this.y - this.tileSize;
            this.isMoving = true;
            this.facing = 'up';
            this.body.setVelocityY(-GAME_CONFIG.player.speed);
        }} else if (cursors.down.isDown) {{
            this.targetY = this.y + this.tileSize;
            this.isMoving = true;
            this.facing = 'down';
            this.body.setVelocityY(GAME_CONFIG.player.speed);
        }}

        this.play('player-' + this.facing, true);
    }}

    takeDamage(amount) {{
        if (this.hp === undefined) return;
        this.hp = Math.max(0, this.hp - Math.max(1, amount - this.defense / 2));
        this.setTint(0xff0000);
        this.scene.time.delayedCall(100, () => this.clearTint());
        if (this.hp <= 0) this.scene.events.emit('player-death');
    }}

    gainXp(amount) {{
        if (this.xp === undefined) return;
        this.xp += amount;
        while (this.xp >= this.xpToLevel) {{
            this.xp -= this.xpToLevel;
            this.level++;
            this.xpToLevel = this.level * 100 + 50;
            this.maxHp += 10;
            this.hp = this.maxHp;
            this.strength += 2;
            this.defense += 1;
            this.scene.events.emit('level-up', this.level);
        }}
    }}
}}"""
    else:
        # Free movement (default)
        return f"""// Player class — Free Movement (8-directional)
class Player extends Phaser.Physics.Arcade.Sprite {{
    constructor(scene, x, y) {{
        super(scene, x, y, 'player');
        scene.add.existing(this);
        scene.physics.add.existing(this);

        this.setCollideWorldBounds(true);
        this.body.setSize(28, 28);
        this.body.setOffset(2, 2);

        this.speed = GAME_CONFIG.player.speed;
        this.facing = 'down';
        this.canInteract = true;
        {hp_code}
    }}

    update(cursors) {{
        let vx = 0;
        let vy = 0;

        if (cursors.left.isDown) {{ vx = -this.speed; this.facing = 'left'; }}
        else if (cursors.right.isDown) {{ vx = this.speed; this.facing = 'right'; }}

        if (cursors.up.isDown) {{ vy = -this.speed; this.facing = 'up'; }}
        else if (cursors.down.isDown) {{ vy = this.speed; this.facing = 'down'; }}

        // Normalize diagonal movement
        if (vx !== 0 && vy !== 0) {{
            vx *= 0.707;
            vy *= 0.707;
        }}

        this.body.setVelocity(vx, vy);

        if (vx !== 0 || vy !== 0) {{
            this.play('player-' + this.facing, true);
        }} else {{
            this.play('player-idle', true);
        }}
    }}

    takeDamage(amount) {{
        if (this.hp === undefined) return;
        this.hp = Math.max(0, this.hp - Math.max(1, amount - this.defense / 2));
        this.setTint(0xff0000);
        this.scene.time.delayedCall(100, () => this.clearTint());
        if (this.hp <= 0) this.scene.events.emit('player-death');
    }}

    gainXp(amount) {{
        if (this.xp === undefined) return;
        this.xp += amount;
        while (this.xp >= this.xpToLevel) {{
            this.xp -= this.xpToLevel;
            this.level++;
            this.xpToLevel = this.level * 100 + 50;
            this.maxHp += 10;
            this.hp = this.maxHp;
            this.strength += 2;
            this.defense += 1;
            this.scene.events.emit('level-up', this.level);
        }}
    }}
}}"""


def _gen_npc_js(gdd: dict) -> str:
    """Generate NPC class with dialogue system."""
    npcs = gdd.get("npcs", [])
    intelligence = gdd.get("local_llm", {}).get("npc_intelligence", "static")

    npc_data_lines = []
    for npc in npcs:
        name = npc.get("name", "NPC")
        role = npc.get("role", "story")
        npc_data_lines.append(
            f'    {{ name: "{name}", role: "{role}", '
            f'dialogues: ["{name}: Welcome, traveler!", "{name}: Be careful out there.", "{name}: Come back anytime."] }}'
        )
    npc_data = "[\n" + ",\n".join(npc_data_lines) + "\n]" if npc_data_lines else "[]"

    llm_section = ""
    if intelligence == "local_llm":
        llm_section = """
    async talkLLM(playerMessage) {
        if (!this.llmEnabled) return this.talk();
        try {
            const res = await fetch('/api/games/llm/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    npc_name: this.npcData.name,
                    system_prompt: `You are ${this.npcData.name}, a ${this.npcData.role}. Stay in character. Keep responses short (1-3 sentences).`,
                    message: playerMessage,
                    history: this.chatHistory || []
                })
            });
            const data = await res.json();
            if (data.response) {
                if (!this.chatHistory) this.chatHistory = [];
                this.chatHistory.push({ role: 'user', content: playerMessage });
                this.chatHistory.push({ role: 'assistant', content: data.response });
                return data.response;
            }
        } catch (e) {
            console.warn('LLM chat failed, falling back to static:', e);
        }
        return this.talk();
    }"""

    return f"""// NPC class with dialogue system
const NPC_DATA = {npc_data};

class NPC extends Phaser.Physics.Arcade.Sprite {{
    constructor(scene, x, y, npcData) {{
        super(scene, x, y, 'npc');
        scene.add.existing(this);
        scene.physics.add.existing(this);

        this.body.setImmovable(true);
        this.body.setSize(28, 28);
        this.npcData = npcData;
        this.dialogueIndex = 0;
        this.isTalking = false;
        this.llmEnabled = {'true' if intelligence == 'local_llm' else 'false'};

        // Name label
        this.nameLabel = scene.add.text(x, y - 24, npcData.name, {{
            fontSize: '10px',
            color: '#ffffff',
            backgroundColor: '#00000088',
            padding: {{ x: 3, y: 1 }}
        }}).setOrigin(0.5);
    }}

    talk() {{
        const dialogues = this.npcData.dialogues || [this.npcData.name + ': ...'];
        const line = dialogues[this.dialogueIndex % dialogues.length];
        this.dialogueIndex++;
        return line;
    }}
    {llm_section}

    preUpdate(time, delta) {{
        super.preUpdate(time, delta);
        if (this.nameLabel) {{
            this.nameLabel.setPosition(this.x, this.y - 24);
        }}
    }}
}}"""


def _gen_enemy_js(gdd: dict) -> str:
    """Generate enemy class."""
    enemies = gdd.get("enemies", [])
    if not enemies:
        return "// No enemies in this game\n"

    return """// Enemy class with patrol and chase behavior
class Enemy extends Phaser.Physics.Arcade.Sprite {
    constructor(scene, x, y, enemyData) {
        super(scene, x, y, 'enemy-' + (enemyData.name || 'slime').toLowerCase());
        scene.add.existing(this);
        scene.physics.add.existing(this);

        this.setCollideWorldBounds(true);
        this.body.setSize(24, 24);
        this.body.setOffset(4, 4);
        this.body.setBounce(1, 1);

        this.enemyData = enemyData;
        this.hp = enemyData.hp || 20;
        this.maxHp = this.hp;
        this.damage = enemyData.damage || 5;
        this.moveSpeed = enemyData.speed || 40;
        this.xpReward = enemyData.xp || 10;
        this.behavior = enemyData.behavior || 'patrol';
        this.chaseRange = 150;
        this.attackCooldown = 0;

        // Patrol state
        this.patrolDir = Phaser.Math.Between(0, 3);
        this.patrolTimer = 0;
        this.patrolDuration = Phaser.Math.Between(60, 180);

        // HP bar
        this.hpBar = scene.add.graphics();
    }

    update(player) {
        if (!this.active) return;

        const dist = Phaser.Math.Distance.Between(this.x, this.y, player.x, player.y);

        if (this.behavior === 'chase' && dist < this.chaseRange) {
            // Chase player
            const angle = Phaser.Math.Angle.Between(this.x, this.y, player.x, player.y);
            this.body.setVelocity(
                Math.cos(angle) * this.moveSpeed * 1.5,
                Math.sin(angle) * this.moveSpeed * 1.5
            );
        } else {
            // Patrol
            this.patrolTimer++;
            if (this.patrolTimer >= this.patrolDuration) {
                this.patrolTimer = 0;
                this.patrolDir = Phaser.Math.Between(0, 3);
                this.patrolDuration = Phaser.Math.Between(60, 180);
            }

            const dirs = [[0,-1],[0,1],[-1,0],[1,0]];
            const [dx, dy] = dirs[this.patrolDir];
            this.body.setVelocity(dx * this.moveSpeed, dy * this.moveSpeed);
        }

        // Attack cooldown
        if (this.attackCooldown > 0) this.attackCooldown--;

        // Draw HP bar
        this.hpBar.clear();
        if (this.hp < this.maxHp) {
            this.hpBar.fillStyle(0x000000);
            this.hpBar.fillRect(this.x - 16, this.y - 20, 32, 4);
            this.hpBar.fillStyle(0xff0000);
            this.hpBar.fillRect(this.x - 15, this.y - 19, 30 * (this.hp / this.maxHp), 2);
        }
    }

    takeDamage(amount) {
        this.hp -= amount;
        this.setTint(0xff0000);
        this.scene.time.delayedCall(100, () => {
            if (this.active) this.clearTint();
        });

        if (this.hp <= 0) {
            this.die();
            return true;
        }
        return false;
    }

    die() {
        this.hpBar.destroy();
        this.destroy();
    }
}"""


def _gen_combat_js(gdd: dict) -> str:
    """Generate combat system."""
    combat_type = gdd.get("systems", {}).get("combat", "none")
    if combat_type == "none":
        return "// No combat system\nconst CombatSystem = { init() {}, update() {} };\n"

    return """// Combat System — Action-based
const CombatSystem = {
    scene: null,
    attackCooldown: 0,
    attackRange: 40,
    attackDuration: 200,

    init(scene) {
        this.scene = scene;
    },

    update() {
        if (this.attackCooldown > 0) this.attackCooldown--;
    },

    playerAttack(player, enemies) {
        if (this.attackCooldown > 0) return;
        this.attackCooldown = 30; // frames

        // Visual attack effect
        const fx = this.scene.add.circle(
            player.x + (player.facing === 'right' ? 20 : player.facing === 'left' ? -20 : 0),
            player.y + (player.facing === 'down' ? 20 : player.facing === 'up' ? -20 : 0),
            12, 0xffff00, 0.8
        );
        this.scene.time.delayedCall(this.attackDuration, () => fx.destroy());

        // Check hits
        enemies.getChildren().forEach(enemy => {
            if (!enemy.active) return;
            const dist = Phaser.Math.Distance.Between(player.x, player.y, enemy.x, enemy.y);
            if (dist < this.attackRange) {
                const damage = Math.max(1, player.strength + Phaser.Math.Between(-2, 2));
                const killed = enemy.takeDamage(damage);
                if (killed) {
                    player.gainXp(enemy.xpReward);
                    this.scene.events.emit('enemy-killed', enemy.enemyData);
                }

                // Knockback
                const angle = Phaser.Math.Angle.Between(player.x, player.y, enemy.x, enemy.y);
                if (enemy.active) {
                    enemy.body.setVelocity(Math.cos(angle) * 200, Math.sin(angle) * 200);
                    this.scene.time.delayedCall(150, () => {
                        if (enemy.active) enemy.body.setVelocity(0, 0);
                    });
                }
            }
        });
    },

    enemyAttack(enemy, player) {
        if (enemy.attackCooldown > 0) return;
        enemy.attackCooldown = 60;

        const dist = Phaser.Math.Distance.Between(enemy.x, enemy.y, player.x, player.y);
        if (dist < 30) {
            player.takeDamage(enemy.damage);
        }
    }
};"""


def _gen_inventory_js(gdd: dict) -> str:
    """Generate inventory system."""
    inv_type = gdd.get("systems", {}).get("inventory", "none")
    if inv_type == "none":
        return "// No inventory system\nconst Inventory = { items: [], add() {}, remove() {} };\n"

    return """// Inventory System
const Inventory = {
    items: [],
    maxSlots: 20,
    gold: 0,

    add(item) {
        if (this.items.length >= this.maxSlots) return false;
        const existing = this.items.find(i => i.name === item.name && i.stackable);
        if (existing) {
            existing.quantity = (existing.quantity || 1) + 1;
        } else {
            this.items.push({ ...item, quantity: 1 });
        }
        return true;
    },

    remove(itemName) {
        const idx = this.items.findIndex(i => i.name === itemName);
        if (idx === -1) return false;
        this.items[idx].quantity--;
        if (this.items[idx].quantity <= 0) this.items.splice(idx, 1);
        return true;
    },

    has(itemName) {
        return this.items.some(i => i.name === itemName);
    },

    getCount(itemName) {
        const item = this.items.find(i => i.name === itemName);
        return item ? (item.quantity || 0) : 0;
    },

    addGold(amount) { this.gold += amount; },

    use(itemName, player) {
        const item = this.items.find(i => i.name === itemName);
        if (!item || !item.effect) return false;
        if (item.effect.type === 'heal') {
            player.hp = Math.min(player.maxHp, player.hp + item.effect.value);
        }
        this.remove(itemName);
        return true;
    }
};"""


def _gen_llm_bridge_js(gdd: dict) -> str:
    """Generate LLM bridge for local NPC dialogue."""
    if not gdd.get("local_llm", {}).get("enabled"):
        return ""
    return """// LLM Bridge — connects game NPCs to local LLM backend
const LLMBridge = {
    baseUrl: '/api/games',
    loaded: false,

    async loadModel(modelType) {
        try {
            const res = await fetch(this.baseUrl + '/llm/load', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ model_type: modelType })
            });
            const data = await res.json();
            this.loaded = data.status === 'loaded';
            return data;
        } catch (e) {
            console.error('LLM load failed:', e);
            return { error: e.message };
        }
    },

    async chat(npcName, systemPrompt, message, history) {
        try {
            const res = await fetch(this.baseUrl + '/llm/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    npc_name: npcName,
                    system_prompt: systemPrompt,
                    message: message,
                    history: history || []
                })
            });
            return await res.json();
        } catch (e) {
            return { error: e.message, response: '...' };
        }
    },

    async unload() {
        const res = await fetch(this.baseUrl + '/llm/unload', { method: 'POST' });
        this.loaded = false;
        return await res.json();
    }
};"""


# ── File Marker Parser ────────────────────────────────────────────────

def parse_file_markers(text: str) -> tuple[str, dict[str, str]]:
    """Extract files from ### FILE: markers. Returns (plan_text, files_dict)."""
    files = {}
    file_pattern = re.compile(r'### FILE:\s*([^\n]+)\n(.*?)### END FILE', re.DOTALL)

    plan_text = text
    first_pos = None
    for m in file_pattern.finditer(text):
        if first_pos is None:
            first_pos = m.start()
        path = m.group(1).strip()
        content = m.group(2).rstrip("\n")
        # Strip code fences
        content = re.sub(r'^```\w*\n?', '', content)
        content = re.sub(r'\n?```\s*$', '', content)
        files[path] = content

    if first_pos is not None:
        plan_text = text[:first_pos].strip()

    return plan_text, files


# ── Generator ─────────────────────────────────────────────────────────

class GameGenerator:
    """Generates complete Phaser 3 games from GDD."""

    async def generate(self, gdd: dict, kg_context: str = "") -> AsyncGenerator[str, None]:
        """Generate all game files. Yields JSON SSE messages."""
        files: dict[str, str] = {}

        # Phase 1: Template files (instant)
        yield json.dumps({"type": "status", "message": "Generating template files..."})

        files["index.html"] = _gen_index_html(gdd)
        files["js/config.js"] = _gen_config_js(gdd)
        files["js/main.js"] = _gen_main_js(gdd)
        files["js/player.js"] = _gen_player_js(gdd)
        files["js/npc.js"] = _gen_npc_js(gdd)
        files["js/combat.js"] = _gen_combat_js(gdd)
        files["js/inventory.js"] = _gen_inventory_js(gdd)

        enemies = gdd.get("enemies", [])
        if enemies:
            files["js/enemy.js"] = _gen_enemy_js(gdd)
        else:
            files["js/enemy.js"] = "// No enemies\n"

        llm_bridge = _gen_llm_bridge_js(gdd)
        if llm_bridge:
            files["js/llm-bridge.js"] = llm_bridge

        yield json.dumps({"type": "files", "count": len(files), "names": list(files.keys())})

        # Phase 2: AI-generated scene (the creative core)
        yield json.dumps({"type": "status", "message": "AI is crafting your game scene..."})

        scene_code = await self._generate_scene(gdd, kg_context)
        if scene_code:
            files["js/scene.js"] = scene_code
        else:
            # Fallback: template scene
            files["js/scene.js"] = self._fallback_scene(gdd)

        yield json.dumps({"type": "files_complete", "files": files})
        yield json.dumps({"type": "done"})

    async def _generate_scene(self, gdd: dict, kg_context: str = "") -> str | None:
        """Use AI to generate the main game scene."""
        meta = gdd.get("meta", {})
        player = gdd.get("player", {})
        world = gdd.get("world", {})
        npcs = gdd.get("npcs", [])
        enemies = gdd.get("enemies", [])
        systems = gdd.get("systems", {})

        prompt = f"""Generate js/scene.js for a Phaser 3 RPG game with these specs:

GAME: {meta.get('name', 'RPG')} — {meta.get('genre', 'fantasy')}
SETTING: {meta.get('starting_scenario', 'An adventure begins...')}
UNIQUE FEATURE: {meta.get('unique_feature', 'none')}

PLAYER: {player.get('movement_style', 'free')} movement, abilities: {player.get('abilities', [])}
WORLD: {world.get('map_size', 'medium')} map, {world.get('tile_theme', 'village')} theme
NPCs: {len(npcs)} NPCs — {', '.join(n.get('name','NPC') for n in npcs[:5])}
ENEMIES: {len(enemies)} types — {', '.join(e.get('name','Slime') for e in enemies[:3])}
COMBAT: {systems.get('combat', 'none')}
INVENTORY: {systems.get('inventory', 'none')}

The scene must:
1. Create programmatic sprites for player, NPCs, enemies using Graphics API + generateTexture
2. Generate a tile-based world using colored rectangles (no image files)
3. Set up physics collisions between player, walls, NPCs, enemies
4. Include a HUD showing HP, level, and dialogue box
5. Handle NPC interaction on proximity + key press
6. Use the Player, NPC, Enemy, CombatSystem, Inventory classes defined in other files
7. Camera follows player
8. Be a complete, single-file Phaser.Scene subclass called GameScene

{f"KG Reference Patterns: {kg_context}" if kg_context else ""}

Generate ONLY the js/scene.js file wrapped in markers:
### FILE: js/scene.js
// your code here
### END FILE"""

        try:
            from services.gemini_service import gemini_service
            accumulated = ""
            async for chunk in gemini_service.stream(
                prompt=prompt,
                system_prompt=GAME_SYSTEM_PROMPT,
                model="gemini-2.5-flash",
            ):
                accumulated += chunk

            _, parsed_files = parse_file_markers(accumulated)
            return parsed_files.get("js/scene.js", accumulated)
        except Exception as ex:
            logger.warning(f"AI scene generation failed: {ex}")
            return None

    def _fallback_scene(self, gdd: dict) -> str:
        """Template-based fallback scene when AI generation fails."""
        world = gdd.get("world", {})
        npcs = gdd.get("npcs", [])
        enemies = gdd.get("enemies", [])
        systems = gdd.get("systems", {})

        map_sizes = {"small": (800, 600), "medium": (1600, 1200), "large": (3200, 2400)}
        mw, mh = map_sizes.get(world.get("map_size", "medium"), (1600, 1200))

        theme_colors = {
            "village": {"ground": "0x7ec850", "wall": "0x8b6914", "accent": "0xd4a574"},
            "forest": {"ground": "0x2d5016", "wall": "0x1a3a0a", "accent": "0x4a8c2a"},
            "dungeon": {"ground": "0x333333", "wall": "0x1a1a1a", "accent": "0x666666"},
            "castle": {"ground": "0x888888", "wall": "0x555555", "accent": "0xaaaaaa"},
            "mixed": {"ground": "0x7ec850", "wall": "0x8b6914", "accent": "0x555555"},
        }
        colors = theme_colors.get(world.get("tile_theme", "village"), theme_colors["village"])

        npc_spawns = "\n".join(
            f'        this.spawnNPC({100 + i * 120}, {200 + (i % 3) * 100}, NPC_DATA[{i}]);'
            for i in range(min(len(npcs), 6))
        )

        enemy_spawns = ""
        if enemies:
            enemy_spawns = "\n".join(
                f'        for (let i = 0; i < 3; i++) {{\n'
                f'            this.spawnEnemy(\n'
                f'                Phaser.Math.Between(100, {mw - 100}),\n'
                f'                Phaser.Math.Between(100, {mh - 100}),\n'
                f'                GAME_CONFIG.enemies[{i}]\n'
                f'            );\n'
                f'        }}'
                for i in range(min(len(enemies), 3))
            )

        combat_init = 'CombatSystem.init(this);' if systems.get("combat") != "none" else ""
        combat_update = 'CombatSystem.update();' if systems.get("combat") != "none" else ""
        attack_code = """
        // Attack on Space
        if (Phaser.Input.Keyboard.JustDown(this.spaceKey)) {
            CombatSystem.playerAttack(this.player, this.enemyGroup);
        }""" if systems.get("combat") != "none" else ""

        return f"""// GameScene — Main game scene (template-generated)
class GameScene extends Phaser.Scene {{
    constructor() {{
        super('GameScene');
    }}

    preload() {{
        // Generate all textures programmatically
        this.generateTextures();
    }}

    create() {{
        // World
        this.physics.world.setBounds(0, 0, {mw}, {mh});
        this.generateWorld({mw}, {mh});

        // Player
        this.player = new Player(this, 400, 300);

        // NPCs
        this.npcGroup = this.physics.add.staticGroup();
        this.npcs = [];
{npc_spawns}

        // Enemies
        this.enemyGroup = this.physics.add.group();
        this.enemies = [];
{enemy_spawns}

        // Collisions
        this.physics.add.collider(this.player, this.wallLayer);
        this.physics.add.collider(this.player, this.npcGroup);
        this.physics.add.collider(this.enemyGroup, this.wallLayer);
        this.physics.add.overlap(this.player, this.enemyGroup, this.onEnemyContact, null, this);

        // Camera
        this.cameras.main.setBounds(0, 0, {mw}, {mh});
        this.cameras.main.startFollow(this.player, true, 0.1, 0.1);
        this.cameras.main.setZoom(1);

        // Input
        this.cursors = this.input.keyboard.createCursorKeys();
        this.wasd = {{
            up: this.input.keyboard.addKey('W'),
            down: this.input.keyboard.addKey('S'),
            left: this.input.keyboard.addKey('A'),
            right: this.input.keyboard.addKey('D')
        }};
        this.spaceKey = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.SPACE);
        this.eKey = this.input.keyboard.addKey('E');

        // Combat
        {combat_init}

        // HUD
        this.createHUD();

        // Dialogue
        this.dialogueBox = null;
        this.dialogueText = null;
        this.createDialogueBox();

        // Events
        this.events.on('player-death', () => this.onPlayerDeath());
        this.events.on('level-up', (level) => this.showMessage('Level Up! Level ' + level));
        this.events.on('enemy-killed', (data) => this.showMessage('+' + data.xp + ' XP'));
    }}

    update() {{
        // Merge WASD and cursors
        const cursors = {{
            left: {{ isDown: this.cursors.left.isDown || this.wasd.left.isDown }},
            right: {{ isDown: this.cursors.right.isDown || this.wasd.right.isDown }},
            up: {{ isDown: this.cursors.up.isDown || this.wasd.up.isDown }},
            down: {{ isDown: this.cursors.down.isDown || this.wasd.down.isDown }},
        }};

        this.player.update(cursors);

        // Update enemies
        this.enemies.forEach(e => {{ if (e.active) e.update(this.player); }});

        {combat_update}
        {attack_code}

        // NPC interaction
        if (Phaser.Input.Keyboard.JustDown(this.eKey)) {{
            this.tryNPCInteraction();
        }}

        // Update HUD
        this.updateHUD();
    }}

    // ── Texture Generation ──────────────────────────────────
    generateTextures() {{
        const gfx = this.add.graphics();

        // Player
        gfx.clear();
        gfx.fillStyle(0x4488ff);
        gfx.fillRect(4, 8, 24, 20);
        gfx.fillStyle(0xffcc88);
        gfx.fillCircle(16, 8, 8);
        gfx.generateTexture('player', 32, 32);

        // NPC
        gfx.clear();
        gfx.fillStyle(0x44cc44);
        gfx.fillRect(4, 8, 24, 20);
        gfx.fillStyle(0xffcc88);
        gfx.fillCircle(16, 8, 8);
        gfx.generateTexture('npc', 32, 32);

        // Enemies
        const enemyColors = [0x44ff44, 0xcccccc, 0xaa4444, 0xff0000, 0x886644];
        GAME_CONFIG.enemies.forEach((e, i) => {{
            gfx.clear();
            const color = parseInt(e.color) || enemyColors[i % enemyColors.length];
            gfx.fillStyle(color);
            gfx.fillCircle(16, 16, 12);
            gfx.fillStyle(0x000000);
            gfx.fillCircle(11, 13, 2);
            gfx.fillCircle(21, 13, 2);
            gfx.generateTexture('enemy-' + e.name.toLowerCase(), 32, 32);
        }});

        // Tiles
        gfx.clear();
        gfx.fillStyle({colors['ground']});
        gfx.fillRect(0, 0, 32, 32);
        gfx.generateTexture('tile-ground', 32, 32);

        gfx.clear();
        gfx.fillStyle({colors['wall']});
        gfx.fillRect(0, 0, 32, 32);
        gfx.lineStyle(1, 0x000000, 0.3);
        gfx.strokeRect(0, 0, 32, 32);
        gfx.generateTexture('tile-wall', 32, 32);

        gfx.destroy();

        // Create idle animation
        this.anims.create({{ key: 'player-idle', frames: [{{ key: 'player' }}], frameRate: 1, repeat: -1 }});
        this.anims.create({{ key: 'player-down', frames: [{{ key: 'player' }}], frameRate: 8, repeat: -1 }});
        this.anims.create({{ key: 'player-up', frames: [{{ key: 'player' }}], frameRate: 8, repeat: -1 }});
        this.anims.create({{ key: 'player-left', frames: [{{ key: 'player' }}], frameRate: 8, repeat: -1 }});
        this.anims.create({{ key: 'player-right', frames: [{{ key: 'player' }}], frameRate: 8, repeat: -1 }});
    }}

    // ── World Generation ────────────────────────────────────
    generateWorld(w, h) {{
        const ts = 32;
        const cols = Math.ceil(w / ts);
        const rows = Math.ceil(h / ts);

        this.wallLayer = this.physics.add.staticGroup();

        for (let y = 0; y < rows; y++) {{
            for (let x = 0; x < cols; x++) {{
                const px = x * ts + ts / 2;
                const py = y * ts + ts / 2;

                if (x === 0 || y === 0 || x === cols - 1 || y === rows - 1) {{
                    // Border walls
                    this.wallLayer.create(px, py, 'tile-wall');
                }} else if (Math.random() < 0.08 && (Math.abs(x - 12) > 3 || Math.abs(y - 9) > 3)) {{
                    // Random walls (not near spawn)
                    this.wallLayer.create(px, py, 'tile-wall');
                }} else {{
                    this.add.image(px, py, 'tile-ground');
                }}
            }}
        }}
    }}

    // ── NPC Spawning ────────────────────────────────────────
    spawnNPC(x, y, data) {{
        if (!data) return;
        const npc = new NPC(this, x, y, data);
        this.npcGroup.add(npc);
        this.npcs.push(npc);
    }}

    // ── Enemy Spawning ──────────────────────────────────────
    spawnEnemy(x, y, data) {{
        if (!data) return;
        const enemy = new Enemy(this, x, y, data);
        this.enemyGroup.add(enemy);
        this.enemies.push(enemy);
    }}

    onEnemyContact(player, enemy) {{
        if (enemy.attackCooldown > 0) return;
        enemy.attackCooldown = 60;
        player.takeDamage(enemy.damage);
    }}

    // ── NPC Interaction ─────────────────────────────────────
    tryNPCInteraction() {{
        let closest = null;
        let closestDist = 60;

        this.npcs.forEach(npc => {{
            const dist = Phaser.Math.Distance.Between(
                this.player.x, this.player.y, npc.x, npc.y
            );
            if (dist < closestDist) {{
                closest = npc;
                closestDist = dist;
            }}
        }});

        if (closest) {{
            const line = closest.talk();
            this.showDialogue(line);
        }}
    }}

    // ── HUD ─────────────────────────────────────────────────
    createHUD() {{
        this.hudBg = this.add.rectangle(0, 0, 250, 60, 0x000000, 0.7)
            .setOrigin(0).setScrollFactor(0).setDepth(100);

        this.hudText = this.add.text(10, 8, '', {{
            fontSize: '12px', color: '#ffffff', lineSpacing: 4
        }}).setScrollFactor(0).setDepth(101);

        this.hpBarBg = this.add.rectangle(10, 48, 150, 8, 0x333333)
            .setOrigin(0).setScrollFactor(0).setDepth(100);
        this.hpBarFill = this.add.rectangle(10, 48, 150, 8, 0x00ff00)
            .setOrigin(0).setScrollFactor(0).setDepth(101);
    }}

    updateHUD() {{
        const p = this.player;
        const hp = p.hp !== undefined ? p.hp : '-';
        const maxHp = p.maxHp !== undefined ? p.maxHp : '-';
        const lvl = p.level || 1;
        const xp = p.xp !== undefined ? p.xp : '-';
        const xpNext = p.xpToLevel || 100;

        this.hudText.setText(`HP: ${{hp}}/${{maxHp}}  Lv.${{lvl}}  XP: ${{xp}}/${{xpNext}}`);

        if (p.hp !== undefined && p.maxHp > 0) {{
            const ratio = p.hp / p.maxHp;
            this.hpBarFill.setSize(150 * ratio, 8);
            this.hpBarFill.fillColor = ratio > 0.5 ? 0x00ff00 : ratio > 0.25 ? 0xffff00 : 0xff0000;
        }}
    }}

    // ── Dialogue Box ────────────────────────────────────────
    createDialogueBox() {{
        this.dialogueBox = this.add.rectangle(400, 550, 700, 60, 0x000000, 0.85)
            .setScrollFactor(0).setDepth(200).setVisible(false);
        this.dialogueText = this.add.text(80, 530, '', {{
            fontSize: '14px', color: '#ffffff', wordWrap: {{ width: 620 }}
        }}).setScrollFactor(0).setDepth(201).setVisible(false);
    }}

    showDialogue(text) {{
        this.dialogueBox.setVisible(true);
        this.dialogueText.setVisible(true);
        this.dialogueText.setText(text);

        this.time.delayedCall(3000, () => {{
            this.dialogueBox.setVisible(false);
            this.dialogueText.setVisible(false);
        }});
    }}

    showMessage(text) {{
        const msg = this.add.text(400, 200, text, {{
            fontSize: '18px', color: '#ffff00', fontStyle: 'bold',
            stroke: '#000000', strokeThickness: 3
        }}).setOrigin(0.5).setScrollFactor(0).setDepth(300);

        this.tweens.add({{
            targets: msg, alpha: 0, y: 160, duration: 1500,
            onComplete: () => msg.destroy()
        }});
    }}

    onPlayerDeath() {{
        this.showMessage('You Died! Respawning...');
        this.time.delayedCall(2000, () => {{
            this.player.hp = this.player.maxHp;
            this.player.setPosition(400, 300);
        }});
    }}
}}"""

    async def refine(self, files: dict, prompt: str) -> AsyncGenerator[str, None]:
        """Refine existing game files based on user prompt."""
        yield json.dumps({"type": "status", "message": "Refining game..."})

        # Build context
        file_context = "\n".join(
            f"### FILE: {path}\n{content}\n### END FILE"
            for path, content in files.items()
        )

        full_prompt = f"""Here are the current game files:

{file_context}

---
User request: {prompt}

Output only the changed files using ### FILE: markers."""

        try:
            from services.gemini_service import gemini_service
            accumulated = ""
            async for chunk in gemini_service.stream(
                prompt=full_prompt,
                system_prompt=REFINE_SYSTEM_PROMPT,
                model="gemini-2.5-flash",
            ):
                accumulated += chunk

            _, parsed = parse_file_markers(accumulated)
            # Merge with existing files
            merged = {**files, **parsed}
            yield json.dumps({"type": "files_complete", "files": merged})
        except Exception as ex:
            logger.error(f"Refine failed: {ex}")
            yield json.dumps({"type": "error", "message": str(ex)})

        yield json.dumps({"type": "done"})


game_generator = GameGenerator()
