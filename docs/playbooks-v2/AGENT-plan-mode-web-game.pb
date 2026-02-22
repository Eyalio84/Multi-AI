# PLAYBOOK-8: Web Game Development with AI Integration

> **Synthesis Origin**: Phaser 3 Documentation + WebSocket Patterns + Local LLM Integration
> **Color Mix**: Blue (Browser APIs) + Yellow (AI Backend) = Green (Real-time AI Games)

## Overview

This playbook covers building browser-based games with AI-powered NPCs using a **dual engine strategy**: Pygame for local development with direct LLM access, and Phaser 3 for web distribution via WebSocket bridge.

**Key Insight**: Browsers cannot directly access local LLM binaries, but WebSocket bridges enable real-time AI communication with <500ms response times.

### Strategic Value

| Metric | Local (Pygame) | Web (Phaser) |
|--------|----------------|--------------|
| **Distribution** | Desktop only | Any browser |
| **LLM Access** | Direct (llama-cpp) | Bridged (WebSocket) |
| **Development Speed** | Fast iteration | Build required |
| **Multiplayer** | Complex | Native WebSocket |
| **Best For** | Prototyping, dev | Production, players |

---

## Part 1: Dual Engine Architecture

### 1.1 The Bridge Pattern

```
┌─────────────────────────────────────────────────────────────┐
│                    DUAL ENGINE ARCHITECTURE                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  LOCAL DEVELOPMENT          │     WEB DISTRIBUTION          │
│  ─────────────────          │     ────────────────          │
│                             │                                │
│  ┌─────────────┐           │     ┌─────────────┐           │
│  │   Pygame    │           │     │   Phaser 3  │           │
│  │  2D Engine  │           │     │  WebGL/2D   │           │
│  └──────┬──────┘           │     └──────┬──────┘           │
│         │                   │            │                   │
│         │ Direct Call       │            │ WebSocket         │
│         │                   │            │                   │
│         ▼                   │            ▼                   │
│  ┌─────────────┐           │     ┌─────────────┐           │
│  │  NPCBrain   │           │     │  AIBrain.js │           │
│  │ (Python)    │           │     │  (Client)   │           │
│  └──────┬──────┘           │     └──────┬──────┘           │
│         │                   │            │                   │
│         │ llama-cpp-python  │            │ ws://localhost    │
│         │                   │            │                   │
│         ▼                   │            ▼                   │
│  ┌─────────────┐           │     ┌─────────────┐           │
│  │ DeepSeek R1 │           │     │  AI Bridge  │───────────┼──► NPCBrain
│  │   (GGUF)    │           │     │  (Python)   │           │
│  └─────────────┘           │     └─────────────┘           │
│                             │                                │
│  Latency: ~200ms           │     Latency: ~400ms            │
│  No network overhead       │     +WebSocket overhead        │
│                             │                                │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Shared Asset Strategy

Both engines consume the same assets in standardized formats:

```
shared_assets/
├── maps/
│   ├── village.json          # Tiled TMX → JSON export
│   └── dungeon.json
├── sprites/
│   ├── player.png            # 32x32 sprite sheets
│   ├── npc_guard.png
│   └── npc_merchant.png
├── npcs/
│   ├── guard.json            # NPC definition + AI prompt
│   └── merchant.json
└── config/
    └── game.json             # Shared game settings
```

**NPC Definition Format** (consumed by both engines):

```json
{
  "id": "guard_captain",
  "name": "Captain Marcus",
  "sprite": "sprites/npc_guard.png",
  "position": {"x": 320, "y": 240},
  "collision_radius": 16,
  "ai_config": {
    "personality": "stern but fair military veteran",
    "knowledge": ["village security", "bandit activity", "king's orders"],
    "speech_style": "formal, clipped sentences",
    "system_prompt": "You are Captain Marcus, a veteran guard captain. You speak formally and value duty above all. You know about recent bandit attacks on trade routes."
  },
  "dialogue_range": 48
}
```

---

## Part 2: Phaser 3 Engine Setup

### 2.1 Project Structure

```
phaser_rpg/
├── index.html                # Entry point
├── src/
│   ├── main.js               # Phaser config + boot
│   ├── scenes/
│   │   ├── Boot.js           # Asset preloading
│   │   ├── Game.js           # Main gameplay
│   │   └── Dialogue.js       # AI dialogue overlay
│   ├── entities/
│   │   ├── Player.js         # Player sprite + input
│   │   └── NPC.js            # NPC with AI integration
│   ├── systems/
│   │   ├── DialogueSystem.js # Typewriter + UI
│   │   └── AIBrain.js        # WebSocket client
│   └── config/
│       └── gameConfig.js
├── assets/                   # Symlink to shared_assets/
└── server.py                 # AI Bridge server
```

### 2.2 Phaser Configuration

```javascript
// src/main.js
import Phaser from 'phaser';
import Boot from './scenes/Boot.js';
import Game from './scenes/Game.js';
import Dialogue from './scenes/Dialogue.js';

const config = {
    type: Phaser.AUTO,  // WebGL with Canvas fallback
    width: 800,
    height: 600,
    pixelArt: true,     // Crisp pixel scaling
    physics: {
        default: 'arcade',
        arcade: {
            gravity: { y: 0 },  // Top-down RPG
            debug: false
        }
    },
    scene: [Boot, Game, Dialogue],
    scale: {
        mode: Phaser.Scale.FIT,
        autoCenter: Phaser.Scale.CENTER_BOTH
    }
};

const game = new Phaser.Game(config);
```

### 2.3 Boot Scene (Asset Loading)

```javascript
// src/scenes/Boot.js
export default class Boot extends Phaser.Scene {
    constructor() {
        super('Boot');
    }

    preload() {
        // Progress bar
        const progressBar = this.add.graphics();
        const progressBox = this.add.graphics();
        progressBox.fillStyle(0x222222, 0.8);
        progressBox.fillRect(240, 270, 320, 50);

        this.load.on('progress', (value) => {
            progressBar.clear();
            progressBar.fillStyle(0x00ff88, 1);
            progressBar.fillRect(250, 280, 300 * value, 30);
        });

        // Load shared assets
        this.load.tilemapTiledJSON('village', 'assets/maps/village.json');
        this.load.image('tiles', 'assets/tilesets/village_tileset.png');
        this.load.spritesheet('player', 'assets/sprites/player.png', {
            frameWidth: 32,
            frameHeight: 32
        });

        // Load NPC configurations
        this.load.json('npc_guard', 'assets/npcs/guard.json');
        this.load.json('npc_merchant', 'assets/npcs/merchant.json');
    }

    create() {
        // Initialize AI connection before starting game
        this.scene.start('Game');
    }
}
```

### 2.4 Game Scene (Main Gameplay)

```javascript
// src/scenes/Game.js
import Player from '../entities/Player.js';
import NPC from '../entities/NPC.js';
import AIBrain from '../systems/AIBrain.js';

export default class Game extends Phaser.Scene {
    constructor() {
        super('Game');
        this.npcs = [];
        this.aiBrain = null;
    }

    create() {
        // Initialize AI connection
        this.aiBrain = new AIBrain('ws://localhost:8766');
        this.aiBrain.connect();

        // Create tilemap
        const map = this.make.tilemap({ key: 'village' });
        const tileset = map.addTilesetImage('village_tileset', 'tiles');

        const groundLayer = map.createLayer('ground', tileset);
        const collisionLayer = map.createLayer('collision', tileset);
        collisionLayer.setCollisionByProperty({ collides: true });

        // Create player
        this.player = new Player(this, 400, 300);
        this.physics.add.collider(this.player.sprite, collisionLayer);

        // Create NPCs from loaded configs
        this.createNPCs(map, collisionLayer);

        // Camera follow
        this.cameras.main.startFollow(this.player.sprite, true, 0.1, 0.1);
        this.cameras.main.setZoom(2);

        // Input for dialogue
        this.input.keyboard.on('keydown-E', () => this.attemptInteraction());
    }

    createNPCs(map, collisionLayer) {
        const npcConfigs = ['npc_guard', 'npc_merchant'];

        npcConfigs.forEach(key => {
            const config = this.cache.json.get(key);
            if (config) {
                const npc = new NPC(this, config, this.aiBrain);
                this.npcs.push(npc);
                this.physics.add.collider(npc.sprite, collisionLayer);
            }
        });
    }

    attemptInteraction() {
        // Find nearest NPC within dialogue range
        let nearestNPC = null;
        let nearestDist = Infinity;

        this.npcs.forEach(npc => {
            const dist = Phaser.Math.Distance.Between(
                this.player.sprite.x, this.player.sprite.y,
                npc.sprite.x, npc.sprite.y
            );
            if (dist < npc.dialogueRange && dist < nearestDist) {
                nearestDist = dist;
                nearestNPC = npc;
            }
        });

        if (nearestNPC) {
            this.scene.pause();
            this.scene.launch('Dialogue', { npc: nearestNPC, aiBrain: this.aiBrain });
        }
    }

    update() {
        this.player.update();
        this.npcs.forEach(npc => npc.update());
    }
}
```

---

## Part 3: WebSocket AI Bridge

### 3.1 Bridge Server (Python)

```python
# server.py - AI Bridge Server
import asyncio
import json
import websockets
from typing import Dict, Set
import sys
sys.path.append('..')  # Access parent modules

from npc_brain import NPCBrain

class AIBridgeServer:
    """WebSocket bridge between Phaser and NPCBrain."""

    def __init__(self, host: str = "localhost", port: int = 8766):
        self.host = host
        self.port = port
        self.npc_brain = NPCBrain()
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.conversation_history: Dict[str, list] = {}

    async def handle_client(self, websocket):
        """Handle individual client connection."""
        self.clients.add(websocket)
        client_id = id(websocket)
        print(f"[Bridge] Client connected: {client_id}")

        try:
            async for message in websocket:
                await self.process_message(websocket, message)
        except websockets.ConnectionClosed:
            print(f"[Bridge] Client disconnected: {client_id}")
        finally:
            self.clients.remove(websocket)

    async def process_message(self, websocket, message: str):
        """Process incoming message and route to appropriate handler."""
        try:
            data = json.loads(message)
            msg_type = data.get("type")

            if msg_type == "npc_chat":
                await self.handle_npc_chat(websocket, data)
            elif msg_type == "clear_history":
                await self.handle_clear_history(websocket, data)
            elif msg_type == "ping":
                await websocket.send(json.dumps({"type": "pong"}))
            else:
                await self.send_error(websocket, f"Unknown message type: {msg_type}")

        except json.JSONDecodeError:
            await self.send_error(websocket, "Invalid JSON")
        except Exception as e:
            await self.send_error(websocket, str(e))

    async def handle_npc_chat(self, websocket, data: dict):
        """Handle NPC dialogue request with streaming response."""
        npc_id = data.get("npc_id")
        player_message = data.get("message")
        npc_config = data.get("npc_config", {})

        if not npc_id or not player_message:
            await self.send_error(websocket, "Missing npc_id or message")
            return

        # Send thinking indicator
        await websocket.send(json.dumps({
            "type": "thinking",
            "npc_id": npc_id
        }))

        # Get conversation history for this NPC
        history_key = f"{id(websocket)}_{npc_id}"
        history = self.conversation_history.get(history_key, [])

        # Build system prompt from NPC config
        system_prompt = npc_config.get("system_prompt", f"You are {npc_id}.")

        try:
            # Generate response using NPCBrain
            response = await asyncio.to_thread(
                self.npc_brain.generate_response,
                npc_id=npc_id,
                player_message=player_message,
                system_prompt=system_prompt,
                history=history
            )

            # Update history
            history.append({"role": "user", "content": player_message})
            history.append({"role": "assistant", "content": response})

            # Trim history to last 20 exchanges
            if len(history) > 40:
                history = history[-40:]
            self.conversation_history[history_key] = history

            # Send response
            await websocket.send(json.dumps({
                "type": "response",
                "npc_id": npc_id,
                "text": response
            }))

        except Exception as e:
            await self.send_error(websocket, f"Generation error: {e}")

    async def handle_clear_history(self, websocket, data: dict):
        """Clear conversation history for an NPC."""
        npc_id = data.get("npc_id")
        history_key = f"{id(websocket)}_{npc_id}"

        if history_key in self.conversation_history:
            del self.conversation_history[history_key]

        await websocket.send(json.dumps({
            "type": "history_cleared",
            "npc_id": npc_id
        }))

    async def send_error(self, websocket, error: str):
        """Send error message to client."""
        await websocket.send(json.dumps({
            "type": "error",
            "message": error
        }))

    async def start(self):
        """Start the WebSocket server."""
        print(f"[Bridge] Starting AI Bridge on ws://{self.host}:{self.port}")
        async with websockets.serve(self.handle_client, self.host, self.port):
            await asyncio.Future()  # Run forever


if __name__ == "__main__":
    server = AIBridgeServer()
    asyncio.run(server.start())
```

### 3.2 AIBrain Client (JavaScript)

```javascript
// src/systems/AIBrain.js
export default class AIBrain {
    constructor(serverUrl = 'ws://localhost:8766') {
        this.serverUrl = serverUrl;
        this.ws = null;
        this.connected = false;
        this.messageHandlers = new Map();
        this.pendingRequests = new Map();
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
    }

    connect() {
        return new Promise((resolve, reject) => {
            this.ws = new WebSocket(this.serverUrl);

            this.ws.onopen = () => {
                console.log('[AIBrain] Connected to AI Bridge');
                this.connected = true;
                this.reconnectAttempts = 0;
                resolve();
            };

            this.ws.onmessage = (event) => {
                this.handleMessage(JSON.parse(event.data));
            };

            this.ws.onclose = () => {
                console.log('[AIBrain] Disconnected from AI Bridge');
                this.connected = false;
                this.attemptReconnect();
            };

            this.ws.onerror = (error) => {
                console.error('[AIBrain] WebSocket error:', error);
                reject(error);
            };
        });
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
            console.log(`[AIBrain] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
            setTimeout(() => this.connect(), delay);
        }
    }

    handleMessage(data) {
        const { type, npc_id } = data;

        // Check for pending request handlers
        if (npc_id && this.pendingRequests.has(npc_id)) {
            const handlers = this.pendingRequests.get(npc_id);

            if (type === 'thinking' && handlers.onThinking) {
                handlers.onThinking();
            } else if (type === 'response' && handlers.onResponse) {
                handlers.onResponse(data.text);
                this.pendingRequests.delete(npc_id);
            } else if (type === 'error' && handlers.onError) {
                handlers.onError(data.message);
                this.pendingRequests.delete(npc_id);
            }
        }

        // Global message handlers
        if (this.messageHandlers.has(type)) {
            this.messageHandlers.get(type)(data);
        }
    }

    /**
     * Send chat message to NPC and get AI response.
     * @param {string} npcId - NPC identifier
     * @param {string} message - Player's message
     * @param {object} npcConfig - NPC configuration with system_prompt
     * @param {object} callbacks - {onThinking, onResponse, onError}
     */
    chat(npcId, message, npcConfig, callbacks = {}) {
        if (!this.connected) {
            if (callbacks.onError) {
                callbacks.onError('Not connected to AI Bridge');
            }
            return;
        }

        // Store callbacks for this request
        this.pendingRequests.set(npcId, callbacks);

        // Send chat request
        this.ws.send(JSON.stringify({
            type: 'npc_chat',
            npc_id: npcId,
            message: message,
            npc_config: npcConfig
        }));
    }

    clearHistory(npcId) {
        if (this.connected) {
            this.ws.send(JSON.stringify({
                type: 'clear_history',
                npc_id: npcId
            }));
        }
    }

    onMessage(type, handler) {
        this.messageHandlers.set(type, handler);
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
        }
    }
}
```

---

## Part 4: Dialogue System

### 4.1 Dialogue Scene

```javascript
// src/scenes/Dialogue.js
import DialogueSystem from '../systems/DialogueSystem.js';

export default class Dialogue extends Phaser.Scene {
    constructor() {
        super('Dialogue');
    }

    init(data) {
        this.npc = data.npc;
        this.aiBrain = data.aiBrain;
    }

    create() {
        // Semi-transparent background
        this.add.rectangle(400, 300, 800, 600, 0x000000, 0.7);

        // Dialogue box
        this.dialogueBox = this.add.rectangle(400, 480, 760, 180, 0x1a1a2e, 0.95);
        this.dialogueBox.setStrokeStyle(2, 0x00ff88);

        // NPC name
        this.nameText = this.add.text(40, 400, this.npc.config.name, {
            fontSize: '20px',
            fontFamily: 'monospace',
            color: '#00ff88'
        });

        // Dialogue text with typewriter
        this.dialogueSystem = new DialogueSystem(this, 40, 440, 720);

        // Input field
        this.createInputField();

        // Thinking indicator
        this.thinkingText = this.add.text(40, 550, '', {
            fontSize: '14px',
            fontFamily: 'monospace',
            color: '#888888',
            fontStyle: 'italic'
        });

        // Close button
        this.add.text(740, 400, '[X]', {
            fontSize: '16px',
            fontFamily: 'monospace',
            color: '#ff6b6b'
        }).setInteractive()
          .on('pointerdown', () => this.closeDialogue());

        // Start with NPC greeting
        this.showGreeting();
    }

    createInputField() {
        // Input background
        this.inputBg = this.add.rectangle(400, 550, 680, 32, 0x16213e);
        this.inputBg.setStrokeStyle(1, 0x00ff88);

        // Input text
        this.inputText = this.add.text(70, 542, '', {
            fontSize: '16px',
            fontFamily: 'monospace',
            color: '#ffffff'
        });

        // Cursor
        this.cursor = this.add.text(70, 542, '_', {
            fontSize: '16px',
            fontFamily: 'monospace',
            color: '#00ff88'
        });

        // Blinking cursor
        this.time.addEvent({
            delay: 500,
            callback: () => {
                this.cursor.visible = !this.cursor.visible;
            },
            loop: true
        });

        // Keyboard input
        this.playerInput = '';
        this.input.keyboard.on('keydown', (event) => this.handleKeyInput(event));
    }

    handleKeyInput(event) {
        if (this.isWaitingForResponse) return;

        if (event.key === 'Enter' && this.playerInput.trim()) {
            this.sendMessage();
        } else if (event.key === 'Backspace') {
            this.playerInput = this.playerInput.slice(0, -1);
            this.updateInputDisplay();
        } else if (event.key === 'Escape') {
            this.closeDialogue();
        } else if (event.key.length === 1 && this.playerInput.length < 100) {
            this.playerInput += event.key;
            this.updateInputDisplay();
        }
    }

    updateInputDisplay() {
        this.inputText.setText(this.playerInput);
        this.cursor.x = 70 + this.inputText.width;
    }

    showGreeting() {
        const greeting = `*${this.npc.config.name} turns to face you*\n\nGreetings, traveler. What brings you here?`;
        this.dialogueSystem.showText(greeting);
    }

    sendMessage() {
        const message = this.playerInput.trim();
        this.playerInput = '';
        this.updateInputDisplay();

        // Show player message
        this.dialogueSystem.showText(`You: "${message}"\n\n`, false);

        // Set waiting state
        this.isWaitingForResponse = true;
        this.thinkingText.setText('...');

        // Send to AI
        this.aiBrain.chat(
            this.npc.config.id,
            message,
            this.npc.config.ai_config,
            {
                onThinking: () => {
                    this.animateThinking();
                },
                onResponse: (text) => {
                    this.isWaitingForResponse = false;
                    this.thinkingText.setText('');
                    this.dialogueSystem.showText(`${this.npc.config.name}: "${text}"`, true);
                },
                onError: (error) => {
                    this.isWaitingForResponse = false;
                    this.thinkingText.setText('');
                    this.dialogueSystem.showText(`[Connection error: ${error}]`, false);
                }
            }
        );
    }

    animateThinking() {
        let dots = 0;
        this.thinkingTimer = this.time.addEvent({
            delay: 300,
            callback: () => {
                dots = (dots + 1) % 4;
                this.thinkingText.setText('.'.repeat(dots) + ' thinking');
            },
            loop: true
        });
    }

    closeDialogue() {
        if (this.thinkingTimer) {
            this.thinkingTimer.destroy();
        }
        this.scene.stop();
        this.scene.resume('Game');
    }
}
```

### 4.2 Typewriter Effect System

```javascript
// src/systems/DialogueSystem.js
export default class DialogueSystem {
    constructor(scene, x, y, maxWidth) {
        this.scene = scene;
        this.x = x;
        this.y = y;
        this.maxWidth = maxWidth;

        this.textObject = scene.add.text(x, y, '', {
            fontSize: '16px',
            fontFamily: 'monospace',
            color: '#ffffff',
            wordWrap: { width: maxWidth }
        });

        this.charDelay = 30;  // ms per character
        this.currentText = '';
        this.targetText = '';
        this.charIndex = 0;
        this.typewriterTimer = null;
    }

    showText(text, useTypewriter = true) {
        // Stop any existing typewriter
        if (this.typewriterTimer) {
            this.typewriterTimer.destroy();
        }

        this.targetText = text;

        if (useTypewriter) {
            this.currentText = '';
            this.charIndex = 0;
            this.startTypewriter();
        } else {
            this.currentText = text;
            this.textObject.setText(text);
        }
    }

    startTypewriter() {
        this.typewriterTimer = this.scene.time.addEvent({
            delay: this.charDelay,
            callback: () => {
                if (this.charIndex < this.targetText.length) {
                    this.currentText += this.targetText[this.charIndex];
                    this.textObject.setText(this.currentText);
                    this.charIndex++;

                    // Play typing sound (optional)
                    // this.scene.sound.play('type', { volume: 0.1 });
                } else {
                    this.typewriterTimer.destroy();
                }
            },
            loop: true
        });
    }

    appendText(text, useTypewriter = true) {
        this.showText(this.currentText + text, useTypewriter);
    }

    skip() {
        if (this.typewriterTimer) {
            this.typewriterTimer.destroy();
        }
        this.currentText = this.targetText;
        this.textObject.setText(this.currentText);
    }

    clear() {
        if (this.typewriterTimer) {
            this.typewriterTimer.destroy();
        }
        this.currentText = '';
        this.targetText = '';
        this.textObject.setText('');
    }

    isTyping() {
        return this.typewriterTimer && this.typewriterTimer.hasDispatched === false;
    }
}
```

---

## Part 5: Entity Classes

### 5.1 Player Entity

```javascript
// src/entities/Player.js
export default class Player {
    constructor(scene, x, y) {
        this.scene = scene;

        // Create sprite with physics
        this.sprite = scene.physics.add.sprite(x, y, 'player');
        this.sprite.setCollideWorldBounds(true);

        // Movement speed
        this.speed = 160;

        // Create animations
        this.createAnimations();

        // Input
        this.cursors = scene.input.keyboard.createCursorKeys();
        this.wasd = scene.input.keyboard.addKeys({
            up: Phaser.Input.Keyboard.KeyCodes.W,
            down: Phaser.Input.Keyboard.KeyCodes.S,
            left: Phaser.Input.Keyboard.KeyCodes.A,
            right: Phaser.Input.Keyboard.KeyCodes.D
        });
    }

    createAnimations() {
        const anims = this.scene.anims;

        // Only create if not already exists
        if (!anims.exists('player_down')) {
            anims.create({
                key: 'player_down',
                frames: anims.generateFrameNumbers('player', { start: 0, end: 3 }),
                frameRate: 8,
                repeat: -1
            });

            anims.create({
                key: 'player_up',
                frames: anims.generateFrameNumbers('player', { start: 4, end: 7 }),
                frameRate: 8,
                repeat: -1
            });

            anims.create({
                key: 'player_left',
                frames: anims.generateFrameNumbers('player', { start: 8, end: 11 }),
                frameRate: 8,
                repeat: -1
            });

            anims.create({
                key: 'player_right',
                frames: anims.generateFrameNumbers('player', { start: 12, end: 15 }),
                frameRate: 8,
                repeat: -1
            });

            anims.create({
                key: 'player_idle',
                frames: [{ key: 'player', frame: 0 }],
                frameRate: 1
            });
        }
    }

    update() {
        const { cursors, wasd, sprite, speed } = this;

        // Reset velocity
        sprite.setVelocity(0);

        // Horizontal movement
        if (cursors.left.isDown || wasd.left.isDown) {
            sprite.setVelocityX(-speed);
            sprite.anims.play('player_left', true);
        } else if (cursors.right.isDown || wasd.right.isDown) {
            sprite.setVelocityX(speed);
            sprite.anims.play('player_right', true);
        }

        // Vertical movement
        if (cursors.up.isDown || wasd.up.isDown) {
            sprite.setVelocityY(-speed);
            if (sprite.body.velocity.x === 0) {
                sprite.anims.play('player_up', true);
            }
        } else if (cursors.down.isDown || wasd.down.isDown) {
            sprite.setVelocityY(speed);
            if (sprite.body.velocity.x === 0) {
                sprite.anims.play('player_down', true);
            }
        }

        // Idle state
        if (sprite.body.velocity.x === 0 && sprite.body.velocity.y === 0) {
            sprite.anims.play('player_idle', true);
        }

        // Normalize diagonal movement
        sprite.body.velocity.normalize().scale(speed);
    }
}
```

### 5.2 NPC Entity

```javascript
// src/entities/NPC.js
export default class NPC {
    constructor(scene, config, aiBrain) {
        this.scene = scene;
        this.config = config;
        this.aiBrain = aiBrain;

        // Create sprite
        const spriteKey = config.sprite.split('/').pop().replace('.png', '');
        this.sprite = scene.physics.add.sprite(
            config.position.x,
            config.position.y,
            spriteKey
        );
        this.sprite.setImmovable(true);

        // Dialogue range (for interaction detection)
        this.dialogueRange = config.dialogue_range || 48;

        // Name tag
        this.nameTag = scene.add.text(
            config.position.x,
            config.position.y - 24,
            config.name,
            {
                fontSize: '10px',
                fontFamily: 'monospace',
                color: '#00ff88',
                backgroundColor: '#000000',
                padding: { x: 2, y: 1 }
            }
        ).setOrigin(0.5);

        // Interaction indicator
        this.interactIcon = scene.add.text(
            config.position.x,
            config.position.y - 36,
            '[E]',
            {
                fontSize: '12px',
                fontFamily: 'monospace',
                color: '#ffff00'
            }
        ).setOrigin(0.5).setVisible(false);

        // Create idle animation
        this.createAnimations();
    }

    createAnimations() {
        const anims = this.scene.anims;
        const spriteKey = this.config.sprite.split('/').pop().replace('.png', '');

        if (!anims.exists(`${spriteKey}_idle`)) {
            anims.create({
                key: `${spriteKey}_idle`,
                frames: [{ key: spriteKey, frame: 0 }],
                frameRate: 1
            });
        }

        this.sprite.anims.play(`${spriteKey}_idle`);
    }

    update() {
        // Check if player is in range
        const player = this.scene.player;
        if (player) {
            const dist = Phaser.Math.Distance.Between(
                player.sprite.x, player.sprite.y,
                this.sprite.x, this.sprite.y
            );
            this.interactIcon.setVisible(dist < this.dialogueRange);
        }
    }

    startDialogue() {
        // Called when player initiates dialogue
        this.scene.scene.pause();
        this.scene.scene.launch('Dialogue', {
            npc: this,
            aiBrain: this.aiBrain
        });
    }
}
```

---

## Part 6: Build and Deployment

### 6.1 Development Server

```python
# dev_server.py - Combined dev server for Phaser + AI Bridge
import asyncio
import http.server
import socketserver
import threading
from pathlib import Path

# Import AI Bridge
from server import AIBridgeServer

class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler with CORS headers for local development."""

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()


def start_http_server(port: int = 8080, directory: str = "."):
    """Start HTTP server for Phaser game."""
    handler = CORSRequestHandler
    handler.directory = directory

    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"[HTTP] Serving Phaser at http://localhost:{port}")
        httpd.serve_forever()


async def main():
    # Start HTTP server in background thread
    http_thread = threading.Thread(
        target=start_http_server,
        kwargs={"port": 8080, "directory": "phaser_rpg"},
        daemon=True
    )
    http_thread.start()

    # Start AI Bridge server
    ai_bridge = AIBridgeServer(host="localhost", port=8766)
    await ai_bridge.start()


if __name__ == "__main__":
    print("=== Development Server ===")
    print("Game:    http://localhost:8080")
    print("AI API:  ws://localhost:8766")
    print("========================")
    asyncio.run(main())
```

### 6.2 Production Build (Vite)

```javascript
// vite.config.js
import { defineConfig } from 'vite';

export default defineConfig({
    base: './',  // Relative paths for deployment
    build: {
        outDir: 'dist',
        assetsDir: 'assets',
        rollupOptions: {
            output: {
                manualChunks: {
                    phaser: ['phaser']
                }
            }
        }
    },
    server: {
        port: 8080,
        proxy: {
            '/ws': {
                target: 'ws://localhost:8766',
                ws: true
            }
        }
    }
});
```

### 6.3 Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy game files
COPY phaser_rpg/ ./phaser_rpg/
COPY server.py .
COPY npc_brain.py .
COPY models/ ./models/

# Expose ports
EXPOSE 8080 8766

# Start both servers
CMD ["python", "dev_server.py"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  game:
    build: .
    ports:
      - "8080:8080"
      - "8766:8766"
    volumes:
      - ./models:/app/models
    environment:
      - MODEL_PATH=/app/models/deepseek-r1-1.5b.Q4_K_M.gguf
```

---

## Part 7: Performance Optimization

### 7.1 Response Time Targets

| Component | Target | Actual | Optimization |
|-----------|--------|--------|--------------|
| WebSocket roundtrip | <50ms | ~30ms | Keep-alive |
| AI generation (local) | <500ms | ~300ms | Q4_K_M quantization |
| Total dialogue response | <600ms | ~400ms | Streaming |
| Typewriter animation | 30ms/char | 30ms | requestAnimationFrame |

### 7.2 Connection Pooling

```javascript
// Singleton AI connection manager
class AIConnectionManager {
    static instance = null;

    static getInstance() {
        if (!AIConnectionManager.instance) {
            AIConnectionManager.instance = new AIBrain('ws://localhost:8766');
        }
        return AIConnectionManager.instance;
    }
}

// Use in scenes
const aiBrain = AIConnectionManager.getInstance();
```

### 7.3 Response Caching

```javascript
// Cache recent responses to reduce LLM calls
class ResponseCache {
    constructor(maxSize = 100, ttlMs = 300000) {
        this.cache = new Map();
        this.maxSize = maxSize;
        this.ttlMs = ttlMs;
    }

    generateKey(npcId, message) {
        // Normalize message for cache matching
        const normalized = message.toLowerCase().trim();
        return `${npcId}:${normalized}`;
    }

    get(npcId, message) {
        const key = this.generateKey(npcId, message);
        const entry = this.cache.get(key);

        if (entry && Date.now() - entry.timestamp < this.ttlMs) {
            return entry.response;
        }
        return null;
    }

    set(npcId, message, response) {
        const key = this.generateKey(npcId, message);

        // Evict oldest if at capacity
        if (this.cache.size >= this.maxSize) {
            const oldest = this.cache.keys().next().value;
            this.cache.delete(oldest);
        }

        this.cache.set(key, {
            response,
            timestamp: Date.now()
        });
    }
}
```

---

## Part 8: Decision Framework

### When to Use Each Engine

```
┌─────────────────────────────────────────────────────────────┐
│                    ENGINE SELECTION GUIDE                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Use PYGAME when:                Use PHASER when:            │
│  ─────────────────               ─────────────────           │
│  • Rapid prototyping             • Player distribution       │
│  • Testing AI prompts            • Cross-platform reach      │
│  • Offline development           • Multiplayer features      │
│  • Direct LLM debugging          • No install required       │
│  • Desktop-only release          • Mobile browser support    │
│                                                              │
│  Development Flow:                                           │
│  ────────────────                                            │
│  1. Prototype in Pygame (fast iteration)                     │
│  2. Test AI personalities and prompts                        │
│  3. Port to Phaser for web                                   │
│  4. Deploy with Docker                                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### AI Integration Decision Tree

```
Is the feature AI-powered?
│
├─► No → Implement directly in Phaser/Pygame
│
└─► Yes → What type?
    │
    ├─► NPC Dialogue
    │   ├─► Development → Pygame + Direct LLM
    │   └─► Production → Phaser + WebSocket Bridge
    │
    ├─► Procedural Content (quests, items)
    │   ├─► Pre-generate → Generate at build time, cache
    │   └─► Runtime → Use Bridge with response caching
    │
    └─► Real-time (difficulty, events)
        └─► Always use Bridge for consistency
```

---

## Checklist

### Setup Phase
- [ ] Phaser 3 project structure created
- [ ] Shared asset directory configured
- [ ] AI Bridge server implemented
- [ ] WebSocket client (AIBrain.js) implemented
- [ ] Development server running both HTTP and WebSocket

### Core Implementation
- [ ] Boot scene loads all assets
- [ ] Player movement with WASD/Arrows
- [ ] Tilemap rendering with collision
- [ ] Camera following player
- [ ] NPC spawning from JSON configs

### AI Integration
- [ ] WebSocket connection with reconnect logic
- [ ] Dialogue scene with typewriter effect
- [ ] Player input handling
- [ ] Thinking indicator animation
- [ ] Error handling for connection failures

### Production
- [ ] Vite build configuration
- [ ] Docker deployment tested
- [ ] Response caching implemented
- [ ] Performance targets met (<600ms dialogue)

---

## Troubleshooting

### WebSocket Connection Refused

**Symptom**: `WebSocket connection to 'ws://localhost:8766' failed`

**Causes & Fixes**:
1. AI Bridge not running → Start `python server.py`
2. Port conflict → Check `netstat -tlnp | grep 8766`
3. Firewall blocking → Allow port 8766

### Slow AI Responses

**Symptom**: Dialogue takes >2 seconds

**Causes & Fixes**:
1. Model too large → Use Q4_K_M quantization
2. No GPU → Ensure llama-cpp compiled with CUDA/Metal
3. Context too long → Trim conversation history to 20 turns

### CORS Errors in Browser

**Symptom**: `Cross-Origin Request Blocked`

**Causes & Fixes**:
1. Missing CORS headers → Use CORSRequestHandler
2. Different ports → Use proxy in vite.config.js
3. Production → Configure nginx with CORS headers

### Asset Loading Failures

**Symptom**: Sprites/tilemaps not appearing

**Causes & Fixes**:
1. Path mismatch → Check asset paths are relative to index.html
2. Case sensitivity → Linux is case-sensitive for filenames
3. Format issues → Ensure Tiled exports as JSON, not TMX

---

## Resources

### Official Documentation
- [Phaser 3 Documentation](https://photonstorm.github.io/phaser3-docs/)
- [Phaser 3 Examples](https://phaser.io/examples)
- [Tiled Map Editor](https://www.mapeditor.org/)
- [WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)

### This Project
- `phaser_rpg/` - Web game engine
- `pygame_rpg/` - Local game engine
- `server.py` - AI Bridge server
- `shared_assets/` - Cross-engine assets
