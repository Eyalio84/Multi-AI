"""Build the Phaser 3 RPG Knowledge Graph.

Creates docs/KGS/phaser-complete-kg.db with ~243 nodes and ~350 edges
covering Phaser 3 API classes, methods, RPG patterns, recipes, configs,
asset strategies, NPC patterns, performance tips, and local LLM integrations.

Usage:
    cd backend
    python scripts/build_phaser_kg.py
"""

import sys
from pathlib import Path

# Allow running from backend/ directory
sys.path.insert(0, str(Path(__file__).parent.parent))


def build_nodes() -> list[dict]:
    """Return all KG nodes across 10 categories."""
    nodes: list[dict] = []

    # ── api_class (~40) ──────────────────────────────────────────────
    api_classes = [
        ("Phaser.Game", {"desc": "Root game object — creates renderer, scenes, clock", "constructor": "new Phaser.Game(config)"}),
        ("Phaser.Scene", {"desc": "Base scene class — preload/create/update lifecycle", "lifecycle": "init→preload→create→update"}),
        ("Phaser.GameObjects.Sprite", {"desc": "Textured game object with animation support", "parent": "GameObject"}),
        ("Phaser.GameObjects.Image", {"desc": "Lightweight textured object (no animation)", "parent": "GameObject"}),
        ("Phaser.GameObjects.Text", {"desc": "Text rendering with style options", "parent": "GameObject"}),
        ("Phaser.GameObjects.Graphics", {"desc": "Canvas-style drawing API for programmatic art", "methods": "fillRect,fillCircle,lineStyle,strokeRect"}),
        ("Phaser.GameObjects.Container", {"desc": "Groups game objects with shared transform", "parent": "GameObject"}),
        ("Phaser.GameObjects.Group", {"desc": "Collection for bulk operations and pooling", "pooling": True}),
        ("Phaser.GameObjects.TileSprite", {"desc": "Repeating texture for backgrounds", "parent": "GameObject"}),
        ("Phaser.GameObjects.Rectangle", {"desc": "Filled rectangle shape", "parent": "Shape"}),
        ("Phaser.Physics.Arcade.Sprite", {"desc": "Sprite with arcade physics body", "parent": "Sprite"}),
        ("Phaser.Physics.Arcade.Group", {"desc": "Physics-enabled group with collision support", "pooling": True}),
        ("Phaser.Physics.Arcade.StaticGroup", {"desc": "Immovable physics group for walls/platforms"}),
        ("Phaser.Physics.Arcade.Body", {"desc": "Physics body with velocity, acceleration, drag"}),
        ("Phaser.Physics.Arcade.World", {"desc": "Arcade physics simulation world", "bounds": True}),
        ("Phaser.Tilemaps.Tilemap", {"desc": "Tile-based map from JSON/CSV data", "formats": "tiled_json,csv"}),
        ("Phaser.Tilemaps.TilemapLayer", {"desc": "Renderable layer of a tilemap", "collision": True}),
        ("Phaser.Tilemaps.Tileset", {"desc": "Tile image set for tilemap rendering"}),
        ("Phaser.Input.Keyboard.KeyboardPlugin", {"desc": "Keyboard input manager", "methods": "createCursorKeys,addKey"}),
        ("Phaser.Input.Keyboard.Key", {"desc": "Individual key state tracker", "props": "isDown,isUp,duration"}),
        ("Phaser.Cameras.Scene2D.Camera", {"desc": "Scene camera with scroll, zoom, effects", "effects": "fade,flash,shake"}),
        ("Phaser.Loader.LoaderPlugin", {"desc": "Asset loader — images, audio, json, tilemaps", "methods": "image,spritesheet,audio,tilemapTiledJSON"}),
        ("Phaser.Animations.AnimationManager", {"desc": "Global animation definition and playback"}),
        ("Phaser.Sound.SoundManager", {"desc": "Audio playback manager", "formats": "mp3,ogg,wav"}),
        ("Phaser.Scale.ScaleManager", {"desc": "Game canvas scaling and resize handling", "modes": "FIT,RESIZE,ENVELOP"}),
        ("Phaser.Math.Vector2", {"desc": "2D vector for position/velocity math"}),
        ("Phaser.Math.Between", {"desc": "Random integer in range", "usage": "Phaser.Math.Between(min, max)"}),
        ("Phaser.Events.EventEmitter", {"desc": "Event pub/sub system used throughout Phaser"}),
        ("Phaser.Time.TimerEvent", {"desc": "Delayed/repeating timer", "methods": "addEvent,delayedCall"}),
        ("Phaser.Tweens.Tween", {"desc": "Property animation over time", "easing": "Linear,Quad,Cubic,Bounce"}),
        ("Phaser.Display.Color", {"desc": "Color utility for hex/rgb/hsv conversions"}),
        ("Phaser.Geom.Rectangle", {"desc": "Rectangle geometry for bounds/overlap checks"}),
        ("Phaser.Geom.Circle", {"desc": "Circle geometry for radius-based checks"}),
        ("Phaser.Structs.Map", {"desc": "Key-value map data structure"}),
        ("Phaser.Structs.List", {"desc": "Ordered list with sorting and searching"}),
        ("Phaser.Scene.Systems", {"desc": "Core systems attached to every scene — add, physics, input, cameras"}),
        ("Phaser.GameObjects.GameObjectFactory", {"desc": "scene.add — factory for creating game objects"}),
        ("Phaser.GameObjects.GameObjectCreator", {"desc": "scene.make — creates without adding to display"}),
        ("Phaser.Data.DataManager", {"desc": "Key-value data storage per game object", "methods": "set,get,values"}),
        ("Phaser.Plugins.PluginManager", {"desc": "Global and scene plugin management"}),
    ]
    for name, props in api_classes:
        nodes.append({"name": name, "type": "api_class", "properties": props})

    # ── api_method (~80) ──────────────────────────────────────────────
    api_methods = [
        ("scene.add.sprite", {"sig": "(x, y, key, frame?)", "returns": "Sprite", "desc": "Create sprite at position"}),
        ("scene.add.image", {"sig": "(x, y, key, frame?)", "returns": "Image"}),
        ("scene.add.text", {"sig": "(x, y, text, style?)", "returns": "Text"}),
        ("scene.add.graphics", {"sig": "(config?)", "returns": "Graphics"}),
        ("scene.add.rectangle", {"sig": "(x, y, w, h, fillColor)", "returns": "Rectangle"}),
        ("scene.add.container", {"sig": "(x, y, children?)", "returns": "Container"}),
        ("scene.add.group", {"sig": "(config?)", "returns": "Group"}),
        ("scene.add.tileSprite", {"sig": "(x, y, w, h, key)", "returns": "TileSprite"}),
        ("scene.add.existing", {"sig": "(gameObject)", "desc": "Add pre-created object to scene"}),
        ("scene.physics.add.sprite", {"sig": "(x, y, key)", "returns": "ArcadeSprite"}),
        ("scene.physics.add.group", {"sig": "(config?)", "returns": "ArcadeGroup"}),
        ("scene.physics.add.staticGroup", {"sig": "(config?)", "returns": "StaticGroup"}),
        ("scene.physics.add.collider", {"sig": "(obj1, obj2, callback?, processCallback?, context?)", "desc": "Add collision between objects"}),
        ("scene.physics.add.overlap", {"sig": "(obj1, obj2, callback?, processCallback?, context?)", "desc": "Add overlap detection"}),
        ("scene.physics.world.setBounds", {"sig": "(x, y, w, h)", "desc": "Set physics world boundaries"}),
        ("body.setVelocity", {"sig": "(x, y)", "desc": "Set body velocity"}),
        ("body.setVelocityX", {"sig": "(x)", "desc": "Set horizontal velocity"}),
        ("body.setVelocityY", {"sig": "(y)", "desc": "Set vertical velocity"}),
        ("body.setCollideWorldBounds", {"sig": "(value)", "desc": "Prevent leaving world bounds"}),
        ("body.setBounce", {"sig": "(x, y?)", "desc": "Set bounce factor"}),
        ("body.setDrag", {"sig": "(x, y?)", "desc": "Set drag/friction"}),
        ("body.setSize", {"sig": "(w, h, center?)", "desc": "Set physics body size"}),
        ("body.setOffset", {"sig": "(x, y)", "desc": "Offset physics body from sprite origin"}),
        ("body.setImmovable", {"sig": "(value)", "desc": "Make body unmovable by collisions"}),
        ("sprite.play", {"sig": "(key, ignoreIfPlaying?)", "desc": "Play animation on sprite"}),
        ("sprite.anims.create", {"sig": "(config)", "desc": "Create animation from config"}),
        ("sprite.setOrigin", {"sig": "(x, y?)", "desc": "Set transform origin point"}),
        ("sprite.setScale", {"sig": "(x, y?)", "desc": "Set sprite scale"}),
        ("sprite.setDepth", {"sig": "(value)", "desc": "Set render depth (z-order)"}),
        ("sprite.setTint", {"sig": "(color)", "desc": "Apply color tint"}),
        ("sprite.setAlpha", {"sig": "(value)", "desc": "Set transparency 0-1"}),
        ("sprite.setVisible", {"sig": "(value)", "desc": "Show/hide sprite"}),
        ("sprite.setActive", {"sig": "(value)", "desc": "Enable/disable update"}),
        ("sprite.destroy", {"sig": "()", "desc": "Remove from scene and free memory"}),
        ("scene.input.keyboard.createCursorKeys", {"sig": "()", "returns": "CursorKeys", "desc": "Get arrow + shift + space keys"}),
        ("scene.input.keyboard.addKey", {"sig": "(keyCode)", "returns": "Key", "desc": "Track specific key"}),
        ("scene.input.keyboard.on", {"sig": "(event, callback)", "desc": "Listen for keyboard events"}),
        ("scene.cameras.main.startFollow", {"sig": "(target, roundPixels?, lerpX?, lerpY?)", "desc": "Camera follows target"}),
        ("scene.cameras.main.setBounds", {"sig": "(x, y, w, h)", "desc": "Limit camera scroll area"}),
        ("scene.cameras.main.setZoom", {"sig": "(zoom)", "desc": "Set camera zoom level"}),
        ("scene.cameras.main.fadeIn", {"sig": "(duration, r?, g?, b?)", "desc": "Fade camera in"}),
        ("scene.cameras.main.fadeOut", {"sig": "(duration, r?, g?, b?)", "desc": "Fade camera out"}),
        ("scene.cameras.main.shake", {"sig": "(duration, intensity?)", "desc": "Screen shake effect"}),
        ("scene.load.image", {"sig": "(key, url)", "desc": "Queue image for loading"}),
        ("scene.load.spritesheet", {"sig": "(key, url, config)", "desc": "Queue spritesheet with frame dimensions"}),
        ("scene.load.audio", {"sig": "(key, urls)", "desc": "Queue audio file"}),
        ("scene.load.tilemapTiledJSON", {"sig": "(key, url)", "desc": "Queue Tiled tilemap JSON"}),
        ("scene.load.on", {"sig": "(event, callback)", "desc": "Loader events: progress, complete"}),
        ("scene.time.addEvent", {"sig": "(config)", "returns": "TimerEvent", "desc": "Create timer"}),
        ("scene.time.delayedCall", {"sig": "(delay, callback, args?, context?)", "desc": "One-shot delayed callback"}),
        ("scene.tweens.add", {"sig": "(config)", "returns": "Tween", "desc": "Create property tween"}),
        ("scene.scene.start", {"sig": "(key, data?)", "desc": "Switch to another scene"}),
        ("scene.scene.launch", {"sig": "(key, data?)", "desc": "Start scene in parallel"}),
        ("scene.scene.stop", {"sig": "(key?)", "desc": "Stop a running scene"}),
        ("scene.scene.pause", {"sig": "(key?)", "desc": "Pause scene updates"}),
        ("scene.scene.resume", {"sig": "(key?)", "desc": "Resume paused scene"}),
        ("scene.data.set", {"sig": "(key, value)", "desc": "Store data on scene"}),
        ("scene.data.get", {"sig": "(key)", "desc": "Retrieve stored data"}),
        ("scene.events.on", {"sig": "(event, callback)", "desc": "Listen for scene events"}),
        ("scene.events.emit", {"sig": "(event, ...args)", "desc": "Emit scene event"}),
        ("graphics.fillStyle", {"sig": "(color, alpha?)", "desc": "Set fill color for drawing"}),
        ("graphics.fillRect", {"sig": "(x, y, w, h)", "desc": "Draw filled rectangle"}),
        ("graphics.fillCircle", {"sig": "(x, y, radius)", "desc": "Draw filled circle"}),
        ("graphics.lineStyle", {"sig": "(width, color, alpha?)", "desc": "Set line style"}),
        ("graphics.strokeRect", {"sig": "(x, y, w, h)", "desc": "Draw rectangle outline"}),
        ("graphics.generateTexture", {"sig": "(key, w?, h?)", "desc": "Convert drawing to texture"}),
        ("tilemap.createLayer", {"sig": "(layerID, tileset, x?, y?)", "returns": "TilemapLayer"}),
        ("tilemap.addTilesetImage", {"sig": "(tilesetName, key?, tileW?, tileH?)", "returns": "Tileset"}),
        ("tilemapLayer.setCollisionByProperty", {"sig": "(properties)", "desc": "Enable collision by tile properties"}),
        ("tilemapLayer.setCollisionByExclusion", {"sig": "(indexes)", "desc": "Collide all except listed tile indexes"}),
        ("group.create", {"sig": "(x, y, key, frame?)", "returns": "GameObject", "desc": "Create and add to group"}),
        ("group.getChildren", {"sig": "()", "returns": "GameObject[]", "desc": "Get all group members"}),
        ("group.get", {"sig": "(x?, y?, key?)", "returns": "GameObject", "desc": "Get inactive member (pooling)"}),
        ("sound.play", {"sig": "(key, config?)", "desc": "Play sound effect"}),
        ("sound.add", {"sig": "(key, config?)", "returns": "Sound", "desc": "Create sound instance"}),
        ("Phaser.Math.Distance.Between", {"sig": "(x1, y1, x2, y2)", "returns": "number", "desc": "Euclidean distance"}),
        ("Phaser.Math.Angle.Between", {"sig": "(x1, y1, x2, y2)", "returns": "number", "desc": "Angle in radians"}),
        ("Phaser.Utils.Array.Shuffle", {"sig": "(array)", "returns": "array", "desc": "Fisher-Yates shuffle"}),
        ("this.anims.create", {"sig": "(config)", "desc": "Define animation globally", "config": "{key,frames,frameRate,repeat}"}),
        ("this.anims.generateFrameNumbers", {"sig": "(key, config)", "desc": "Generate frame sequence from spritesheet", "config": "{start,end}"}),
    ]
    for name, props in api_methods:
        nodes.append({"name": name, "type": "api_method", "properties": props})

    # ── pattern (~30) ─────────────────────────────────────────────────
    patterns = [
        ("grid_movement", {"desc": "Pokemon-style tile-by-tile movement with queue", "movement_type": "grid", "code_template": "// Queue-based: move TILE_SIZE px per step, block input until complete\nconst TILE = 32;\nif (!this.isMoving && cursors.left.isDown) {\n  this.targetX = this.x - TILE;\n  this.isMoving = true;\n}"}),
        ("free_movement", {"desc": "WASD/arrow 8-directional smooth movement", "movement_type": "free", "code_template": "const speed = 160;\nlet vx = 0, vy = 0;\nif (cursors.left.isDown) vx = -speed;\nif (cursors.right.isDown) vx = speed;\nif (cursors.up.isDown) vy = -speed;\nif (cursors.down.isDown) vy = speed;\nif (vx && vy) { vx *= 0.707; vy *= 0.707; }\nthis.body.setVelocity(vx, vy);"}),
        ("click_to_move", {"desc": "Click destination with BFS pathfinding", "movement_type": "click", "requires": "pathfinding_grid"}),
        ("npc_dialogue_system", {"desc": "Multi-line dialogue with typewriter effect", "ui": "text_box_bottom"}),
        ("branching_dialogue", {"desc": "Player choice branching dialogue tree", "data_structure": "tree_json"}),
        ("local_llm_dialogue", {"desc": "NPC dialogue powered by local LLM via HTTP bridge", "requires": "llm_bridge"}),
        ("action_combat", {"desc": "Real-time attack/damage with hitboxes", "combat_type": "action"}),
        ("turn_based_combat", {"desc": "Menu-driven turn-based battle system", "combat_type": "turn_based"}),
        ("simple_inventory", {"desc": "Array-based inventory with UI grid", "max_slots": 20}),
        ("full_inventory", {"desc": "Categorized inventory with equip slots", "categories": "weapon,armor,consumable,quest"}),
        ("hp_bar_ui", {"desc": "Health bar rendered with graphics API", "code_template": "const bar = this.add.graphics();\nbar.fillStyle(0x000000); bar.fillRect(x, y, w, h);\nbar.fillStyle(0xff0000); bar.fillRect(x+1, y+1, (w-2)*ratio, h-2);"}),
        ("xp_leveling", {"desc": "Experience points with level-up formula", "formula": "xpNeeded = level * 100"}),
        ("quest_tracking", {"desc": "Quest state machine: inactive→active→complete", "states": "inactive,active,complete,failed"}),
        ("tilemap_collision", {"desc": "Tile-based collision from Tiled map properties"}),
        ("programmatic_tilemap", {"desc": "Generate tilemap from 2D array in code"}),
        ("camera_follow", {"desc": "Camera follows player with deadzone", "code_template": "this.cameras.main.startFollow(player, true, 0.1, 0.1);\nthis.cameras.main.setDeadzone(50, 50);"}),
        ("scene_transition", {"desc": "Fade between scenes with data passing"}),
        ("object_pooling", {"desc": "Reuse inactive objects instead of create/destroy"}),
        ("spatial_partitioning", {"desc": "Grid-based spatial hash for collision optimization"}),
        ("sprite_animation_8dir", {"desc": "8-direction sprite animation from spritesheet rows"}),
        ("sprite_animation_4dir", {"desc": "4-direction walk animation (down/left/right/up)"}),
        ("programmatic_sprites", {"desc": "Generate sprites using Graphics API + generateTexture"}),
        ("damage_flash", {"desc": "Flash sprite white on damage using tint", "code_template": "sprite.setTint(0xffffff);\nscene.time.delayedCall(100, () => sprite.clearTint());"}),
        ("knockback", {"desc": "Push entity away on hit", "code_template": "const angle = Phaser.Math.Angle.Between(src.x, src.y, target.x, target.y);\ntarget.body.setVelocity(Math.cos(angle)*200, Math.sin(angle)*200);"}),
        ("enemy_patrol", {"desc": "Enemy moves between waypoints"}),
        ("enemy_chase", {"desc": "Enemy chases player when in range", "chase_radius": 150}),
        ("loot_drop", {"desc": "Enemies drop items on death"}),
        ("save_load_local", {"desc": "Save game state to localStorage"}),
        ("minimap", {"desc": "Corner minimap using second camera"}),
        ("day_night_cycle", {"desc": "Tinted overlay cycles between day and night"}),
    ]
    for name, props in patterns:
        nodes.append({"name": name, "type": "pattern", "properties": props})

    # ── recipe (~25) ──────────────────────────────────────────────────
    recipes = [
        ("basic_rpg_recipe", {"desc": "Minimal RPG: player + movement + 1 NPC + dialogue", "files": "index.html,config.js,main.js,player.js,scene.js", "difficulty": "beginner"}),
        ("tilemap_recipe", {"desc": "Tiled JSON tilemap with collision layers", "files": "scene.js,tilemap.json,tileset.png", "difficulty": "intermediate"}),
        ("inventory_recipe", {"desc": "Inventory system with pickup/drop/use", "files": "inventory.js,item.js", "difficulty": "intermediate"}),
        ("combat_action_recipe", {"desc": "Real-time combat with attack/damage/death", "files": "combat.js,enemy.js,player.js", "difficulty": "intermediate"}),
        ("combat_turnbased_recipe", {"desc": "Turn-based battle scene with menus", "files": "battle_scene.js,combat.js", "difficulty": "advanced"}),
        ("npc_static_recipe", {"desc": "NPCs with static multi-line dialogue", "files": "npc.js,dialogues.json", "difficulty": "beginner"}),
        ("npc_branching_recipe", {"desc": "NPCs with branching choice dialogue", "files": "npc.js,dialogue_tree.json", "difficulty": "intermediate"}),
        ("npc_llm_recipe", {"desc": "NPCs powered by local LLM via HTTP bridge", "files": "npc.js,llm-bridge.js", "difficulty": "advanced"}),
        ("enemy_basic_recipe", {"desc": "Enemies with patrol + chase + attack", "files": "enemy.js", "difficulty": "beginner"}),
        ("quest_recipe", {"desc": "Quest system with objectives and rewards", "files": "quest.js,quest_data.json", "difficulty": "intermediate"}),
        ("save_system_recipe", {"desc": "localStorage save/load with versioning", "files": "save.js", "difficulty": "intermediate"}),
        ("audio_recipe", {"desc": "Background music + SFX with volume control", "files": "audio.js", "difficulty": "beginner"}),
        ("particle_effects_recipe", {"desc": "Particle emitters for spells/explosions", "files": "effects.js", "difficulty": "intermediate"}),
        ("minimap_recipe", {"desc": "Corner minimap using second camera", "files": "minimap.js", "difficulty": "intermediate"}),
        ("scene_management_recipe", {"desc": "Multi-scene game with transitions", "files": "boot.js,menu.js,game.js,ui.js", "difficulty": "intermediate"}),
        ("grid_movement_recipe", {"desc": "Pokemon-style grid movement implementation", "files": "player.js", "difficulty": "intermediate"}),
        ("pathfinding_recipe", {"desc": "BFS click-to-move pathfinding on grid", "files": "pathfinder.js,player.js", "difficulty": "advanced"}),
        ("spritesheet_recipe", {"desc": "Load and animate multi-frame spritesheets", "files": "player.js,animations.js", "difficulty": "beginner"}),
        ("programmatic_art_recipe", {"desc": "Generate all sprites via Graphics API", "files": "assets.js", "difficulty": "beginner", "code_template": "const gfx = this.add.graphics();\ngfx.fillStyle(0x4488ff);\ngfx.fillRect(0, 0, 32, 32);\ngfx.fillStyle(0xffcc88);\ngfx.fillCircle(16, 8, 8);\ngfx.generateTexture('player', 32, 32);\ngfx.destroy();"}),
        ("hud_recipe", {"desc": "Heads-up display with HP, level, gold", "files": "hud.js", "difficulty": "beginner"}),
        ("equipment_recipe", {"desc": "Equip weapons/armor that modify stats", "files": "equipment.js,stats.js", "difficulty": "intermediate"}),
        ("shop_recipe", {"desc": "Buy/sell items from NPC shopkeepers", "files": "shop.js", "difficulty": "intermediate"}),
        ("weather_recipe", {"desc": "Rain/snow particle effects + lighting overlay", "files": "weather.js", "difficulty": "intermediate"}),
        ("door_teleport_recipe", {"desc": "Doors that teleport to other scenes/positions", "files": "scene.js", "difficulty": "beginner"}),
        ("chest_loot_recipe", {"desc": "Openable chests with random loot tables", "files": "chest.js,loot_tables.json", "difficulty": "beginner"}),
    ]
    for name, props in recipes:
        nodes.append({"name": name, "type": "recipe", "properties": props})

    # ── config (~15) ──────────────────────────────────────────────────
    configs = [
        ("game_config", {"desc": "Root Phaser.Game configuration object", "code_template": "const config = {\n  type: Phaser.AUTO,\n  width: 800, height: 600,\n  parent: 'game-container',\n  pixelArt: true,\n  physics: { default: 'arcade', arcade: { gravity: { y: 0 }, debug: false } },\n  scene: [BootScene, GameScene, UIScene]\n};"}),
        ("physics_config_topdown", {"desc": "Top-down RPG physics (no gravity)", "code_template": "physics: { default: 'arcade', arcade: { gravity: { y: 0 }, debug: false } }"}),
        ("physics_config_platformer", {"desc": "Platformer physics (gravity enabled)", "code_template": "physics: { default: 'arcade', arcade: { gravity: { y: 300 }, debug: false } }"}),
        ("scale_config_fit", {"desc": "Scale to fit container maintaining ratio", "code_template": "scale: { mode: Phaser.Scale.FIT, autoCenter: Phaser.Scale.CENTER_BOTH }"}),
        ("scale_config_responsive", {"desc": "Responsive resize to fill window", "code_template": "scale: { mode: Phaser.Scale.RESIZE, autoCenter: Phaser.Scale.CENTER_BOTH }"}),
        ("scale_config_fixed", {"desc": "Fixed size canvas (pixel art games)", "code_template": "scale: { mode: Phaser.Scale.NONE }"}),
        ("animation_config", {"desc": "Animation definition format", "code_template": "this.anims.create({ key: 'walk-down', frames: this.anims.generateFrameNumbers('player', { start: 0, end: 3 }), frameRate: 8, repeat: -1 });"}),
        ("tilemap_config", {"desc": "Tiled map import configuration", "code_template": "const map = this.make.tilemap({ key: 'map' });\nconst tileset = map.addTilesetImage('tileset-name', 'tileset-key');\nconst ground = map.createLayer('Ground', tileset);\nconst walls = map.createLayer('Walls', tileset);\nwalls.setCollisionByProperty({ collides: true });"}),
        ("camera_config", {"desc": "Camera setup for RPG", "code_template": "this.cameras.main.setBounds(0, 0, mapWidth, mapHeight);\nthis.cameras.main.startFollow(this.player, true, 0.1, 0.1);\nthis.cameras.main.setZoom(2);"}),
        ("input_config_wasd", {"desc": "WASD + arrow key mapping", "code_template": "this.cursors = this.input.keyboard.createCursorKeys();\nthis.wasd = {\n  up: this.input.keyboard.addKey('W'),\n  down: this.input.keyboard.addKey('S'),\n  left: this.input.keyboard.addKey('A'),\n  right: this.input.keyboard.addKey('D')\n};"}),
        ("debug_config", {"desc": "Enable physics debug rendering", "code_template": "physics: { default: 'arcade', arcade: { debug: true, debugShowBody: true, debugShowVelocity: true } }"}),
        ("audio_config", {"desc": "Audio system configuration", "code_template": "audio: { disableWebAudio: false, noAudio: false }"}),
        ("render_config_pixelart", {"desc": "Pixel art rendering (no antialiasing)", "code_template": "render: { pixelArt: true, antialias: false, roundPixels: true }"}),
        ("scene_config", {"desc": "Scene registration format", "code_template": "scene: [BootScene, GameScene, UIScene, BattleScene]"}),
        ("tween_config", {"desc": "Tween configuration format", "code_template": "this.tweens.add({ targets: sprite, alpha: 0, duration: 500, ease: 'Power2', yoyo: true, repeat: 2 });"}),
    ]
    for name, props in configs:
        nodes.append({"name": name, "type": "config", "properties": props})

    # ── asset_strategy (~10) ──────────────────────────────────────────
    asset_strategies = [
        ("programmatic_sprites", {"desc": "Generate all sprites with Graphics API — no external files needed", "pros": "No CDN, no CORS, instant loading", "cons": "Limited detail, more code"}),
        ("local_spritesheet", {"desc": "Serve spritesheets from local static files", "pros": "Custom art, full control", "cons": "Requires art assets"}),
        ("color_rectangles", {"desc": "Use colored rectangles as placeholder sprites", "pros": "Simplest possible, fast prototyping", "cons": "No visual appeal"}),
        ("emoji_sprites", {"desc": "Use emoji characters rendered to canvas as sprites", "pros": "Recognizable, no art needed", "cons": "Platform-dependent rendering"}),
        ("svg_sprites", {"desc": "Generate SVG sprites for crisp scaling", "pros": "Resolution independent", "cons": "Complex for animations"}),
        ("tileset_generation", {"desc": "Programmatically generate tileset texture", "code_template": "const gfx = this.add.graphics();\n// Draw grid of colored tiles\nfor (let y = 0; y < 4; y++) {\n  for (let x = 0; x < 4; x++) {\n    gfx.fillStyle(colors[y * 4 + x]);\n    gfx.fillRect(x * 32, y * 32, 32, 32);\n  }\n}\ngfx.generateTexture('tileset', 128, 128);\ngfx.destroy();"}),
        ("base64_embedded", {"desc": "Embed small images as base64 data URIs", "pros": "Single file, no server needed", "cons": "Larger HTML, harder to edit"}),
        ("atlas_packing", {"desc": "Pack multiple sprites into texture atlas", "pros": "Fewer draw calls", "cons": "Requires atlas tool"}),
        ("procedural_terrain", {"desc": "Generate terrain tiles with noise algorithms", "algo": "perlin_noise,simplex"}),
        ("asset_pack_free", {"desc": "Use free RPG asset packs from itch.io/opengameart", "sources": "itch.io,opengameart.org,kenney.nl"}),
    ]
    for name, props in asset_strategies:
        nodes.append({"name": name, "type": "asset_strategy", "properties": props})

    # ── rpg_mechanic (~20) ────────────────────────────────────────────
    rpg_mechanics = [
        ("hp_system", {"desc": "Hit points with damage/heal/death", "formula": "currentHP = Math.max(0, Math.min(currentHP + delta, maxHP))"}),
        ("mp_system", {"desc": "Magic/mana points for abilities", "regen": "mp += 1 per 2 seconds"}),
        ("level_up", {"desc": "Level progression with stat increases", "formula": "xpNeeded = level * 100 + 50"}),
        ("stat_system", {"desc": "Core stats: STR, DEF, SPD, INT, LCK", "stats": "strength,defense,speed,intelligence,luck"}),
        ("equipment_slots", {"desc": "Equip items to body slots", "slots": "weapon,shield,helmet,armor,boots,ring"}),
        ("damage_formula", {"desc": "Attack damage calculation", "formula": "damage = attacker.STR - defender.DEF / 2 + random(-2, 2)", "min_damage": 1}),
        ("critical_hit", {"desc": "Chance for double damage", "formula": "crit_chance = LCK * 0.02", "multiplier": 2.0}),
        ("status_effects", {"desc": "Buff/debuff with duration", "effects": "poison,burn,freeze,sleep,haste,shield"}),
        ("gold_currency", {"desc": "Gold currency for shop transactions"}),
        ("item_rarity", {"desc": "Item rarity tiers", "tiers": "common,uncommon,rare,epic,legendary", "color_codes": "#ffffff,#00ff00,#0088ff,#aa00ff,#ffaa00"}),
        ("quest_objectives", {"desc": "Quest objective types", "types": "kill_count,collect_items,talk_to_npc,reach_location,escort"}),
        ("dialogue_choices", {"desc": "Player dialogue choices that affect outcomes"}),
        ("faction_reputation", {"desc": "Reputation system with factions", "range": "-100 to 100"}),
        ("respawn_system", {"desc": "Player respawn on death with penalty"}),
        ("map_transitions", {"desc": "Move between map zones via doors/edges"}),
        ("item_crafting", {"desc": "Combine items to create new ones"}),
        ("skill_tree", {"desc": "Unlockable abilities in branching tree"}),
        ("random_encounters", {"desc": "Random battle encounters while exploring"}),
        ("party_system", {"desc": "Multiple party members with switching"}),
        ("battle_formations", {"desc": "Position-based battle formations"}),
    ]
    for name, props in rpg_mechanics:
        nodes.append({"name": name, "type": "rpg_mechanic", "properties": props})

    # ── npc_pattern (~10) ─────────────────────────────────────────────
    npc_patterns = [
        ("static_dialogue_npc", {"desc": "Fixed dialogue lines cycled on interaction", "complexity": "low"}),
        ("branching_dialogue_npc", {"desc": "Dialogue tree with player choices", "complexity": "medium", "data_format": "json_tree"}),
        ("local_llm_npc", {"desc": "NPC powered by local LLM for dynamic conversation", "complexity": "high", "requires": "llm_bridge,local_model"}),
        ("quest_giver_npc", {"desc": "NPC that assigns and tracks quests", "states": "available,in_progress,complete"}),
        ("shopkeeper_npc", {"desc": "NPC with buy/sell interface"}),
        ("trainer_npc", {"desc": "NPC that teaches skills/abilities"}),
        ("guard_npc", {"desc": "NPC that blocks passage until condition met"}),
        ("wandering_npc", {"desc": "NPC that moves around randomly or on path"}),
        ("story_npc", {"desc": "NPC that delivers key story exposition"}),
        ("companion_npc", {"desc": "NPC that follows and assists player"}),
    ]
    for name, props in npc_patterns:
        nodes.append({"name": name, "type": "npc_pattern", "properties": props})

    # ── performance (~8) ──────────────────────────────────────────────
    performance_tips = [
        ("object_pooling", {"desc": "Reuse inactive game objects instead of create/destroy", "impact": "high", "code_template": "const bullet = bullets.get(x, y, 'bullet');\nif (bullet) { bullet.setActive(true).setVisible(true); }"}),
        ("spatial_partitioning", {"desc": "Divide world into grid cells for faster collision checks", "impact": "high"}),
        ("texture_atlas", {"desc": "Pack sprites into atlas to reduce draw calls", "impact": "medium"}),
        ("camera_culling", {"desc": "Phaser auto-culls off-screen objects", "impact": "medium", "note": "enabled_by_default"}),
        ("physics_body_limit", {"desc": "Disable physics on off-screen entities", "impact": "medium"}),
        ("render_texture_cache", {"desc": "Pre-render complex visuals to RenderTexture", "impact": "medium"}),
        ("event_cleanup", {"desc": "Remove event listeners in scene shutdown", "impact": "low", "code_template": "this.events.on('shutdown', () => {\n  this.input.keyboard.off('keydown');\n});"}),
        ("frame_rate_throttle", {"desc": "Lock to 30fps on mobile for battery savings", "code_template": "fps: { target: 30, forceSetTimeOut: true }"}),
    ]
    for name, props in performance_tips:
        nodes.append({"name": name, "type": "performance", "properties": props})

    # ── integration (~5) ──────────────────────────────────────────────
    integrations = [
        ("local_llm_deepseek", {"desc": "DeepSeek R1 1.5B for NPC dialogue", "model_file": "deepseek-r1-1.5b", "context_len": 2048, "temperature": 0.7, "vram_mb": 1200}),
        ("local_llm_gemma3_1b", {"desc": "Gemma 3 1B for fast NPC responses", "model_file": "gemma-3-1b", "context_len": 2048, "temperature": 0.7, "vram_mb": 800}),
        ("local_llm_gemma2_2b", {"desc": "Gemma 2 2B for richer NPC dialogue", "model_file": "gemma-2-2b", "context_len": 2048, "temperature": 0.7, "vram_mb": 1600}),
        ("local_llm_qwen", {"desc": "Qwen 2.5 for multilingual NPC dialogue", "model_file": "qwen-2.5", "context_len": 2048, "temperature": 0.7, "vram_mb": 1400}),
        ("gemini_cloud_npc", {"desc": "Gemini API for cloud-powered NPC intelligence", "model": "gemini-2.5-flash", "requires": "api_key,internet"}),
    ]
    for name, props in integrations:
        nodes.append({"name": name, "type": "integration", "properties": props})

    return nodes


def build_edges(nodes: list[dict]) -> list[dict]:
    """Return all KG edges connecting the nodes."""
    edges: list[dict] = []

    def e(src: str, tgt: str, rel: str, props: dict | None = None):
        edges.append({"source": src, "target": tgt, "type": rel, "properties": props or {}})

    # ── api_class → api_method (uses) ──────────────────────────────
    class_method_map = {
        "Phaser.Scene": [
            "scene.add.sprite", "scene.add.image", "scene.add.text", "scene.add.graphics",
            "scene.add.rectangle", "scene.add.container", "scene.add.group", "scene.add.tileSprite",
            "scene.add.existing", "scene.physics.add.sprite", "scene.physics.add.group",
            "scene.physics.add.staticGroup", "scene.physics.add.collider", "scene.physics.add.overlap",
            "scene.input.keyboard.createCursorKeys", "scene.input.keyboard.addKey",
            "scene.cameras.main.startFollow", "scene.cameras.main.setBounds",
            "scene.cameras.main.setZoom", "scene.load.image", "scene.load.spritesheet",
            "scene.load.audio", "scene.time.addEvent", "scene.time.delayedCall",
            "scene.tweens.add", "scene.scene.start", "scene.scene.launch",
            "scene.data.set", "scene.data.get", "scene.events.on", "scene.events.emit",
        ],
        "Phaser.Physics.Arcade.Body": [
            "body.setVelocity", "body.setVelocityX", "body.setVelocityY",
            "body.setCollideWorldBounds", "body.setBounce", "body.setDrag",
            "body.setSize", "body.setOffset", "body.setImmovable",
        ],
        "Phaser.GameObjects.Sprite": [
            "sprite.play", "sprite.anims.create", "sprite.setOrigin", "sprite.setScale",
            "sprite.setDepth", "sprite.setTint", "sprite.setAlpha", "sprite.setVisible",
            "sprite.setActive", "sprite.destroy",
        ],
        "Phaser.GameObjects.Graphics": [
            "graphics.fillStyle", "graphics.fillRect", "graphics.fillCircle",
            "graphics.lineStyle", "graphics.strokeRect", "graphics.generateTexture",
        ],
        "Phaser.Tilemaps.Tilemap": [
            "tilemap.createLayer", "tilemap.addTilesetImage",
        ],
        "Phaser.Tilemaps.TilemapLayer": [
            "tilemapLayer.setCollisionByProperty", "tilemapLayer.setCollisionByExclusion",
        ],
        "Phaser.GameObjects.Group": [
            "group.create", "group.getChildren", "group.get",
        ],
    }
    for cls, methods in class_method_map.items():
        for method in methods:
            e(cls, method, "uses")

    # ── pattern → api_method (uses) ───────────────────────────────
    pattern_api = {
        "free_movement": ["body.setVelocity", "scene.input.keyboard.createCursorKeys"],
        "grid_movement": ["body.setVelocity", "scene.input.keyboard.createCursorKeys", "scene.time.delayedCall"],
        "click_to_move": ["scene.input.keyboard.on", "body.setVelocity"],
        "npc_dialogue_system": ["scene.add.text", "scene.add.rectangle", "scene.time.delayedCall"],
        "action_combat": ["scene.physics.add.collider", "body.setVelocity", "sprite.play"],
        "camera_follow": ["scene.cameras.main.startFollow", "scene.cameras.main.setBounds"],
        "scene_transition": ["scene.cameras.main.fadeOut", "scene.cameras.main.fadeIn", "scene.scene.start"],
        "hp_bar_ui": ["graphics.fillStyle", "graphics.fillRect"],
        "damage_flash": ["sprite.setTint", "scene.time.delayedCall"],
        "knockback": ["body.setVelocity"],
        "object_pooling": ["group.get", "sprite.setActive", "sprite.setVisible"],
        "programmatic_sprites": ["graphics.fillStyle", "graphics.fillRect", "graphics.fillCircle", "graphics.generateTexture"],
        "sprite_animation_4dir": ["sprite.play", "this.anims.create", "this.anims.generateFrameNumbers"],
        "sprite_animation_8dir": ["sprite.play", "this.anims.create", "this.anims.generateFrameNumbers"],
        "minimap": ["scene.cameras.main.setBounds", "scene.cameras.main.setZoom"],
    }
    for pattern, methods in pattern_api.items():
        for method in methods:
            e(pattern, method, "uses")

    # ── recipe → pattern (requires) ───────────────────────────────
    recipe_patterns = {
        "basic_rpg_recipe": ["free_movement", "npc_dialogue_system", "hp_bar_ui", "programmatic_sprites"],
        "tilemap_recipe": ["tilemap_collision", "camera_follow"],
        "inventory_recipe": ["simple_inventory"],
        "combat_action_recipe": ["action_combat", "damage_flash", "knockback", "hp_bar_ui"],
        "combat_turnbased_recipe": ["turn_based_combat", "hp_bar_ui"],
        "npc_static_recipe": ["npc_dialogue_system"],
        "npc_branching_recipe": ["branching_dialogue"],
        "npc_llm_recipe": ["local_llm_dialogue"],
        "enemy_basic_recipe": ["enemy_patrol", "enemy_chase"],
        "grid_movement_recipe": ["grid_movement"],
        "pathfinding_recipe": ["click_to_move"],
        "spritesheet_recipe": ["sprite_animation_4dir"],
        "programmatic_art_recipe": ["programmatic_sprites"],
        "hud_recipe": ["hp_bar_ui"],
        "equipment_recipe": ["simple_inventory"],
    }
    for recipe, pats in recipe_patterns.items():
        for pat in pats:
            e(recipe, pat, "requires")

    # ── recipe → config (uses) ────────────────────────────────────
    recipe_configs = {
        "basic_rpg_recipe": ["game_config", "physics_config_topdown", "render_config_pixelart", "input_config_wasd"],
        "tilemap_recipe": ["tilemap_config", "camera_config"],
        "audio_recipe": ["audio_config"],
        "scene_management_recipe": ["scene_config"],
    }
    for recipe, confs in recipe_configs.items():
        for conf in confs:
            e(recipe, conf, "uses")

    # ── pattern alternatives ──────────────────────────────────────
    alternatives = [
        ("grid_movement", "free_movement"),
        ("grid_movement", "click_to_move"),
        ("free_movement", "click_to_move"),
        ("action_combat", "turn_based_combat"),
        ("simple_inventory", "full_inventory"),
        ("static_dialogue_npc", "branching_dialogue_npc"),
        ("branching_dialogue_npc", "local_llm_npc"),
        ("programmatic_sprites", "local_spritesheet"),
        ("color_rectangles", "programmatic_sprites"),
    ]
    for a, b in alternatives:
        e(a, b, "alternative_to")
        e(b, a, "alternative_to")

    # ── pattern composes_with ─────────────────────────────────────
    composes = [
        ("free_movement", "action_combat"),
        ("free_movement", "npc_dialogue_system"),
        ("grid_movement", "turn_based_combat"),
        ("grid_movement", "npc_dialogue_system"),
        ("hp_bar_ui", "action_combat"),
        ("hp_bar_ui", "turn_based_combat"),
        ("simple_inventory", "loot_drop"),
        ("enemy_patrol", "enemy_chase"),
        ("camera_follow", "tilemap_collision"),
        ("xp_leveling", "hp_system"),
        ("quest_tracking", "quest_giver_npc"),
        ("save_load_local", "simple_inventory"),
        ("day_night_cycle", "camera_follow"),
        ("damage_flash", "knockback"),
    ]
    for a, b in composes:
        e(a, b, "composes_with")

    # ── rpg_mechanic → pattern (implements) ───────────────────────
    mechanic_patterns = {
        "hp_system": "hp_bar_ui",
        "level_up": "xp_leveling",
        "equipment_slots": "full_inventory",
        "damage_formula": "action_combat",
        "critical_hit": "action_combat",
        "quest_objectives": "quest_tracking",
        "dialogue_choices": "branching_dialogue",
        "map_transitions": "scene_transition",
        "respawn_system": "scene_transition",
    }
    for mech, pat in mechanic_patterns.items():
        e(mech, pat, "implements")

    # ── npc_pattern → pattern/integration (depends_on) ────────────
    e("static_dialogue_npc", "npc_dialogue_system", "depends_on")
    e("branching_dialogue_npc", "branching_dialogue", "depends_on")
    e("local_llm_npc", "local_llm_dialogue", "depends_on")
    e("quest_giver_npc", "quest_tracking", "depends_on")
    e("shopkeeper_npc", "gold_currency", "depends_on")
    e("shopkeeper_npc", "simple_inventory", "depends_on")
    e("wandering_npc", "enemy_patrol", "depends_on")
    e("companion_npc", "free_movement", "depends_on")

    # ── integration → npc_pattern (integrates_with) ───────────────
    for llm in ["local_llm_deepseek", "local_llm_gemma3_1b", "local_llm_gemma2_2b", "local_llm_qwen", "gemini_cloud_npc"]:
        e(llm, "local_llm_npc", "integrates_with")
        e(llm, "local_llm_dialogue", "integrates_with")

    # ── performance → pattern (optimized_by) ──────────────────────
    e("object_pooling", "enemy_basic_recipe", "optimized_by")
    e("object_pooling", "loot_drop", "optimized_by")
    e("spatial_partitioning", "action_combat", "optimized_by")
    e("camera_culling", "tilemap_collision", "optimized_by")
    e("physics_body_limit", "enemy_basic_recipe", "optimized_by")
    e("texture_atlas", "spritesheet_recipe", "optimized_by")
    e("frame_rate_throttle", "basic_rpg_recipe", "optimized_by")

    # ── config → api_class (part_of) ──────────────────────────────
    e("game_config", "Phaser.Game", "part_of")
    e("physics_config_topdown", "Phaser.Physics.Arcade.World", "part_of")
    e("physics_config_platformer", "Phaser.Physics.Arcade.World", "part_of")
    e("scale_config_fit", "Phaser.Scale.ScaleManager", "part_of")
    e("camera_config", "Phaser.Cameras.Scene2D.Camera", "part_of")
    e("animation_config", "Phaser.Animations.AnimationManager", "part_of")
    e("audio_config", "Phaser.Sound.SoundManager", "part_of")
    e("render_config_pixelart", "Phaser.Game", "part_of")

    # ── asset_strategy → pattern (uses) ───────────────────────────
    e("programmatic_sprites", "programmatic_art_recipe", "uses")
    e("local_spritesheet", "spritesheet_recipe", "uses")
    e("tileset_generation", "programmatic_tilemap", "uses")

    return edges


def main():
    """Build the Phaser 3 KG using kg_service."""
    import os
    os.chdir(Path(__file__).parent.parent)  # cd to backend/

    from services.kg_service import kg_service

    db_name = "phaser-complete-kg"

    # Create database (skip if exists)
    try:
        result = kg_service.create_database(db_name)
        print(f"Created database: {result}")
    except FileExistsError:
        print(f"Database '{db_name}' already exists — will add to it")

    nodes = build_nodes()
    edges = build_edges(nodes)

    print(f"Prepared {len(nodes)} nodes and {len(edges)} edges")

    # Bulk create
    result = kg_service.bulk_create(db_name, nodes, edges)
    print(f"Created {result['nodes_created']} nodes and {result['edges_created']} edges")

    # Summary by type
    type_counts: dict[str, int] = {}
    for n in nodes:
        t = n["type"]
        type_counts[t] = type_counts.get(t, 0) + 1

    print("\nNode distribution:")
    for t, c in sorted(type_counts.items()):
        print(f"  {t}: {c}")

    print(f"\nTotal: {len(nodes)} nodes, {len(edges)} edges")
    print(f"Database: docs/KGS/{db_name}.db")


if __name__ == "__main__":
    main()
