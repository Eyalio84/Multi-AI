# Phaser.js RPG - Advanced Features & Optimization Guide

## Table of Contents

1. [Advanced Movement Systems](#advanced-movement-systems)
2. [Combat System Implementation](#combat-system-implementation)
3. [Inventory & Items](#inventory--items)
4. [Particle Effects](#particle-effects)
5. [Audio & Sound](#audio--sound)
6. [Performance Optimization](#performance-optimization)
7. [Debugging & Best Practices](#debugging--best-practices)

---

## Advanced Movement Systems

### Grid-Based Movement (Pokemon-Style)

For tile-locked movement, implement a queue-based system:

```javascript
class GridPlayer extends Player {
    constructor(scene, x, y) {
        super(scene, x, y);
        this.tileSize = 16;
        this.isMoving = false;
        this.moveQueue = [];
        this.moveDuration = 200; // ms per tile
    }
    
    update() {
        if (!this.isMoving) {
            // Check input and queue movement
            if (this.keys.up.isDown || this.keys.upArrow.isDown) {
                this.queueMove(0, -this.tileSize);
                this.currentDirection = 'up';
            } else if (this.keys.down.isDown || this.keys.downArrow.isDown) {
                this.queueMove(0, this.tileSize);
                this.currentDirection = 'down';
            } else if (this.keys.left.isDown || this.keys.leftArrow.isDown) {
                this.queueMove(-this.tileSize, 0);
                this.currentDirection = 'left';
            } else if (this.keys.right.isDown || this.keys.rightArrow.isDown) {
                this.queueMove(this.tileSize, 0);
                this.currentDirection = 'right';
            }
        }
        
        // Process movement queue
        if (this.moveQueue.length > 0 && !this.isMoving) {
            this.executeMove();
        }
    }
    
    queueMove(dx, dy) {
        // Don't queue if same direction key is held
        if (this.moveQueue.length === 0) {
            this.moveQueue.push({ dx, dy });
        }
    }
    
    executeMove() {
        const move = this.moveQueue.shift();
        const targetX = this.x + move.dx;
        const targetY = this.y + move.dy;
        
        // Check collision
        if (this.canMoveTo(targetX, targetY)) {
            this.isMoving = true;
            this.play(`walk-${this.currentDirection}`, true);
            
            this.scene.tweens.add({
                targets: this,
                x: targetX,
                y: targetY,
                duration: this.moveDuration,
                onComplete: () => {
                    this.isMoving = false;
                }
            });
        }
    }
    
    canMoveTo(x, y) {
        // Check if tile at position is walkable
        const tile = this.scene.wallLayer.getTileAtWorldXY(x, y);
        return tile && tile.index <= 1; // Tiles 0-1 are walkable
    }
}
```

### Pathfinding (Click-to-Move)

```javascript
class PathfindingPlayer extends Player {
    constructor(scene, x, y) {
        super(scene, x, y);
        this.path = [];
        this.pathIndex = 0;
    }
    
    /**
     * Calculate path to target using A* or simple BFS
     */
    moveTo(targetX, targetY) {
        this.path = this.calculatePath(
            Math.floor(this.x / 16),
            Math.floor(this.y / 16),
            Math.floor(targetX / 16),
            Math.floor(targetY / 16)
        );
        this.pathIndex = 0;
    }
    
    calculatePath(startX, startY, endX, endY) {
        // Simple breadth-first search
        const queue = [[startX, startY, []]];
        const visited = new Set();
        
        while (queue.length > 0) {
            const [x, y, path] = queue.shift();
            
            if (x === endX && y === endY) {
                return path;
            }
            
            const key = `${x},${y}`;
            if (visited.has(key)) continue;
            visited.add(key);
            
            // Check 4 directions
            const directions = [
                [0, -1], [0, 1], [-1, 0], [1, 0]
            ];
            
            for (const [dx, dy] of directions) {
                const nx = x + dx;
                const ny = y + dy;
                
                if (this.isWalkable(nx, ny)) {
                    queue.push([nx, ny, [...path, [nx, ny]]]);
                }
            }
        }
        
        return [];
    }
    
    isWalkable(x, y) {
        const tile = this.scene.wallLayer.getTileAt(x, y);
        return tile && tile.index <= 1;
    }
    
    update() {
        if (this.path.length > this.pathIndex) {
            const [tx, ty] = this.path[this.pathIndex];
            const targetWorldX = tx * 16;
            const targetWorldY = ty * 16;
            
            const angle = Phaser.Math.Angle.Between(
                this.x, this.y, targetWorldX, targetWorldY
            );
            
            this.body.setVelocity(
                Math.cos(angle) * this.moveSpeed,
                Math.sin(angle) * this.moveSpeed
            );
            
            const distance = Phaser.Math.Distance.Between(
                this.x, this.y, targetWorldX, targetWorldY
            );
            
            if (distance < 10) {
                this.pathIndex++;
            }
        } else {
            this.body.setVelocity(0, 0);
        }
    }
}
```

---

## Combat System Implementation

### Simple Combat Mechanics

```javascript
/**
 * Combat system with attack, defense, and damage
 */
class CombatSystem {
    constructor(scene) {
        this.scene = scene;
        this.inCombat = false;
        this.currentTarget = null;
        this.combatLog = [];
    }
    
    /**
     * Initiate combat with target
     */
    startCombat(attacker, defender) {
        this.inCombat = true;
        this.currentTarget = defender;
        this.combatLog = [];
        
        this.scene.events.emit('combat-start', { attacker, defender });
    }
    
    /**
     * Execute attack action
     */
    attack(attacker, defender) {
        const attackPower = attacker.attackPower || 10;
        const defense = defender.defense || 0;
        
        // Calculate damage (random + stats)
        const baseDamage = attackPower + Phaser.Math.Between(-2, 2);
        const finalDamage = Math.max(1, baseDamage - defense);
        
        // Apply damage
        defender.takeDamage(finalDamage);
        
        const message = `${attacker.name} attacks for ${finalDamage} damage!`;
        this.combatLog.push(message);
        
        // Visual feedback
        this.createDamagePopup(defender, finalDamage);
        
        return finalDamage;
    }
    
    /**
     * Create floating damage number
     */
    createDamagePopup(target, damage) {
        const text = this.scene.add.text(
            target.x,
            target.y - 30,
            `-${damage}`,
            {
                fontSize: '20px',
                color: '#FF0000',
                fontStyle: 'bold'
            }
        );
        
        this.scene.tweens.add({
            targets: text,
            y: text.y - 40,
            alpha: 0,
            duration: 1000,
            onComplete: () => text.destroy()
        });
    }
    
    /**
     * Check if target is defeated
     */
    isDefeated(target) {
        return target.health <= 0;
    }
    
    /**
     * End combat
     */
    endCombat() {
        this.inCombat = false;
        this.currentTarget = null;
    }
}
```

### Enemy AI

```javascript
class Enemy extends Phaser.Physics.Arcade.Sprite {
    constructor(scene, x, y, name = 'Enemy') {
        super(scene, x, y, 'enemy');
        
        scene.add.existing(this);
        scene.physics.add.existing(this);
        this.setScale(2);
        
        // Stats
        this.enemyName = name;
        this.health = 30;
        this.maxHealth = 30;
        this.attackPower = 5;
        this.defense = 1;
        this.speed = 100;
        
        // AI
        this.visionRange = 150;
        this.attackRange = 50;
        this.chasing = false;
        this.lastAttackTime = 0;
        this.attackCooldown = 1500; // ms
        
        this.createAnimations(scene);
    }
    
    createAnimations(scene) {
        scene.anims.create({
            key: 'enemy-walk',
            frames: scene.anims.generateFrameNumbers('enemy', 
                { start: 0, end: 2 }
            ),
            frameRate: 8,
            repeat: -1
        });
    }
    
    /**
     * Update enemy AI each frame
     */
    update(player) {
        const distanceToPlayer = Phaser.Math.Distance.Between(
            this.x, this.y, player.x, player.y
        );
        
        // Check if player is in vision range
        if (distanceToPlayer < this.visionRange) {
            this.chasing = true;
        } else {
            this.chasing = false;
            this.body.setVelocity(0, 0);
            this.stop();
            return;
        }
        
        // Chase player
        if (this.chasing) {
            const angle = Phaser.Math.Angle.Between(
                this.x, this.y, player.x, player.y
            );
            
            this.body.setVelocity(
                Math.cos(angle) * this.speed,
                Math.sin(angle) * this.speed
            );
            
            this.play('enemy-walk', true);
            
            // Attack if in range
            if (distanceToPlayer < this.attackRange) {
                this.attackPlayer(player);
            }
        }
    }
    
    /**
     * Attack the player
     */
    attackPlayer(player) {
        const now = this.scene.time.now;
        
        if (now - this.lastAttackTime > this.attackCooldown) {
            player.takeDamage(this.attackPower);
            this.lastAttackTime = now;
            
            // Visual feedback
            this.scene.cameras.main.shake(100, 0.01);
        }
    }
    
    takeDamage(amount) {
        this.health = Math.max(0, this.health - amount);
        
        // Death
        if (this.health <= 0) {
            this.die();
        }
    }
    
    die() {
        // Explosion effect
        const particles = this.scene.add.particles('enemy');
        const emitter = particles.createEmitter({
            speed: { min: -200, max: 200 },
            angle: { min: 240, max: 300 },
            scale: { start: 1, end: 0 },
            lifespan: 600,
            gravityY: 300
        });
        
        emitter.emitParticleAt(this.x, this.y, 8);
        
        // Remove enemy
        this.destroy();
    }
}
```

---

## Inventory & Items

### Simple Inventory System

```javascript
class Inventory {
    constructor(maxSlots = 10) {
        this.slots = Array(maxSlots).fill(null);
        this.maxSlots = maxSlots;
    }
    
    /**
     * Add item to inventory
     */
    addItem(item) {
        // Check for stackable items
        if (item.stackable) {
            for (let i = 0; i < this.slots.length; i++) {
                if (this.slots[i] && this.slots[i].id === item.id) {
                    this.slots[i].quantity += item.quantity;
                    return true;
                }
            }
        }
        
        // Add to empty slot
        for (let i = 0; i < this.slots.length; i++) {
            if (!this.slots[i]) {
                this.slots[i] = item;
                return true;
            }
        }
        
        return false; // Inventory full
    }
    
    /**
     * Remove item from inventory
     */
    removeItem(index) {
        if (this.slots[index]) {
            const item = this.slots[index];
            this.slots[index] = null;
            return item;
        }
        return null;
    }
    
    /**
     * Use consumable item
     */
    useItem(index, player) {
        const item = this.slots[index];
        if (!item) return;
        
        if (item.type === 'potion') {
            player.heal(item.healAmount);
        } else if (item.type === 'weapon') {
            player.equippedWeapon = item;
        }
        
        // Decrease quantity
        item.quantity--;
        if (item.quantity <= 0) {
            this.removeItem(index);
        }
    }
    
    /**
     * Get item at slot
     */
    getItem(index) {
        return this.slots[index];
    }
    
    /**
     * Get all items
     */
    getAllItems() {
        return this.slots.filter(item => item !== null);
    }
}

// Item definition
class Item {
    constructor(id, name, type, stackable = true, quantity = 1) {
        this.id = id;
        this.name = name;
        this.type = type; // 'potion', 'weapon', 'armor', 'key', etc.
        this.stackable = stackable;
        this.quantity = quantity;
    }
}

// Example items
const ITEMS = {
    HEALTH_POTION: new Item('hpotion', 'Health Potion', 'potion', true, 1),
    IRON_SWORD: new Item('isword', 'Iron Sword', 'weapon', false),
    GOLD_COIN: new Item('coin', 'Gold Coin', 'currency', true, 1)
};

ITEMS.HEALTH_POTION.healAmount = 50;
```

### Item Pickup System

```javascript
class ItemPickup extends Phaser.Physics.Arcade.Sprite {
    constructor(scene, x, y, item) {
        super(scene, x, y, 'item');
        
        scene.add.existing(this);
        scene.physics.add.existing(this);
        
        this.item = item;
        this.setScale(1.5);
        this.body.setImmovable(true);
        
        // Floating animation
        this.floatOffset = 0;
        scene.tweens.add({
            targets: this,
            y: y - 8,
            duration: 800,
            yoyo: true,
            repeat: -1
        });
    }
    
    collect() {
        this.destroy();
    }
}
```

---

## Particle Effects

### Create Particle Systems

```javascript
class ParticleEffects {
    /**
     * Explosion effect
     */
    static explosion(scene, x, y) {
        const particles = scene.add.particles('particle');
        const emitter = particles.createEmitter({
            speed: { min: -200, max: 200 },
            angle: { min: 0, max: 360 },
            scale: { start: 1, end: 0 },
            lifespan: 600,
            gravityY: 300,
            emitZone: {
                source: new Phaser.Geom.Circle(0, 0, 5),
                type: 'random'
            }
        });
        
        emitter.emitParticleAt(x, y, 15);
        
        scene.time.delayedCall(600, () => particles.destroy());
    }
    
    /**
     * Healing effect
     */
    static heal(scene, x, y) {
        const particles = scene.add.particles('particle');
        particles.setEmitterSpeeds(0, 0);
        particles.setEmitterGravityY(-150);
        
        const emitter = particles.createEmitter({
            speed: 0,
            alpha: { start: 1, end: 0 },
            scale: { start: 0.5, end: 0.2 },
            lifespan: 1000,
            tint: 0x00FF00,
            emitZone: {
                source: new Phaser.Geom.Circle(0, 0, 10),
                type: 'random'
            }
        });
        
        emitter.emitParticleAt(x, y, 10);
        
        scene.time.delayedCall(1000, () => particles.destroy());
    }
    
    /**
     * Dust effect on footsteps
     */
    static dust(scene, x, y) {
        const particles = scene.add.particles('particle');
        const emitter = particles.createEmitter({
            speed: { min: 20, max: 60 },
            angle: { min: 200, max: 340 },
            alpha: { start: 0.6, end: 0 },
            scale: { start: 0.3, end: 0 },
            lifespan: 400,
            gravityY: 100
        });
        
        emitter.emitParticleAt(x, y, 3);
        
        scene.time.delayedCall(400, () => particles.destroy());
    }
}
```

---

## Audio & Sound

### Audio Management

```javascript
class AudioManager {
    constructor(scene) {
        this.scene = scene;
        this.soundVolume = 0.7;
        this.musicVolume = 0.5;
        this.sounds = {};
        this.currentMusic = null;
    }
    
    /**
     * Preload audio files
     */
    preload() {
        // Sound effects
        this.scene.load.audio('footstep', 'assets/audio/footstep.wav');
        this.scene.load.audio('attack', 'assets/audio/attack.wav');
        this.scene.load.audio('hit', 'assets/audio/hit.wav');
        this.scene.load.audio('heal', 'assets/audio/heal.wav');
        this.scene.load.audio('levelup', 'assets/audio/levelup.wav');
        
        // Music
        this.scene.load.audio('bgm-village', 'assets/audio/village.mp3');
        this.scene.load.audio('bgm-forest', 'assets/audio/forest.mp3');
        this.scene.load.audio('bgm-boss', 'assets/audio/boss.mp3');
    }
    
    /**
     * Play sound effect
     */
    playSound(key, volume = 1) {
        const sound = this.scene.sound.add(key);
        sound.volume = this.soundVolume * volume;
        sound.play();
        return sound;
    }
    
    /**
     * Play background music
     */
    playMusic(key, loop = true, fadeIn = false) {
        // Stop current music
        if (this.currentMusic) {
            this.currentMusic.stop();
        }
        
        const music = this.scene.sound.add(key);
        music.volume = this.musicVolume;
        music.loop = loop;
        
        if (fadeIn) {
            music.volume = 0;
            this.scene.tweens.add({
                targets: music,
                volume: this.musicVolume,
                duration: 2000
            });
        }
        
        music.play();
        this.currentMusic = music;
        return music;
    }
    
    /**
     * Stop music with fade out
     */
    stopMusic(duration = 1000) {
        if (this.currentMusic) {
            this.scene.tweens.add({
                targets: this.currentMusic,
                volume: 0,
                duration: duration,
                onComplete: () => {
                    this.currentMusic.stop();
                    this.currentMusic = null;
                }
            });
        }
    }
    
    /**
     * Set volume
     */
    setSoundVolume(volume) {
        this.soundVolume = Phaser.Math.Clamp(volume, 0, 1);
    }
    
    setMusicVolume(volume) {
        this.musicVolume = Phaser.Math.Clamp(volume, 0, 1);
        if (this.currentMusic) {
            this.currentMusic.volume = this.musicVolume;
        }
    }
}
```

---

## Performance Optimization

### Common Performance Bottlenecks

```javascript
/**
 * Performance optimization techniques
 */
class PerformanceOptimizer {
    /**
     * Object pooling for frequently created objects
     */
    static createObjectPool(scene, spriteKey, size = 10) {
        const pool = {
            active: [],
            inactive: [],
            
            get() {
                if (this.inactive.length > 0) {
                    return this.inactive.pop();
                }
                return scene.add.sprite(0, 0, spriteKey);
            },
            
            release(obj) {
                obj.setActive(false);
                obj.setVisible(false);
                this.inactive.push(obj);
            },
            
            releaseAll() {
                this.active.forEach(obj => this.release(obj));
                this.active = [];
            }
        };
        
        // Pre-allocate pool
        for (let i = 0; i < size; i++) {
            pool.inactive.push(scene.add.sprite(0, 0, spriteKey));
        }
        
        return pool;
    }
    
    /**
     * Spatial partitioning for collision detection
     */
    static createSpatialGrid(width, height, cellSize) {
        const cols = Math.ceil(width / cellSize);
        const rows = Math.ceil(height / cellSize);
        const grid = {};
        
        return {
            cellSize,
            cols,
            rows,
            grid,
            
            addObject(obj) {
                const cellX = Math.floor(obj.x / cellSize);
                const cellY = Math.floor(obj.y / cellSize);
                const key = `${cellX},${cellY}`;
                
                if (!this.grid[key]) {
                    this.grid[key] = [];
                }
                this.grid[key].push(obj);
            },
            
            getNearbyObjects(x, y, range = 1) {
                const cellX = Math.floor(x / cellSize);
                const cellY = Math.floor(y / cellSize);
                const nearby = [];
                
                for (let dx = -range; dx <= range; dx++) {
                    for (let dy = -range; dy <= range; dy++) {
                        const key = `${cellX + dx},${cellY + dy}`;
                        if (this.grid[key]) {
                            nearby.push(...this.grid[key]);
                        }
                    }
                }
                
                return nearby;
            },
            
            clear() {
                this.grid = {};
            }
        };
    }
    
    /**
     * Lazy animation updates
     */
    static optimizeAnimations(sprite, distanceFromCamera, visibilityRange = 500) {
        if (distanceFromCamera > visibilityRange) {
            sprite.anims.stop();
        } else {
            sprite.anims.resume();
        }
    }
}
```

### FPS Monitoring

```javascript
class FPSMonitor {
    constructor(scene) {
        this.scene = scene;
        this.fpsText = scene.add.text(10, 10, '', {
            fontSize: '14px',
            color: '#00FF00',
            fontFamily: 'monospace'
        });
        this.fpsText.setScrollFactor(0);
        this.fpsText.setDepth(1000);
    }
    
    update() {
        const fps = Phaser.Math.RoundTo(
            this.scene.game.loop.actualFps, -1
        );
        this.fpsText.setText(`FPS: ${fps}`);
    }
}
```

---

## Debugging & Best Practices

### Debug Mode

```javascript
// In game config
debug: {
    enableInspector: true,
    showInfo: true,
    showFPS: true,
    showPhysicsBodies: false,
    showWorldBounds: false
}
```

### Logging System

```javascript
class GameLogger {
    static log(message, category = 'INFO') {
        const timestamp = new Date().toLocaleTimeString();
        console.log(`[${timestamp}] [${category}] ${message}`);
    }
    
    static error(message) {
        this.log(message, 'ERROR');
    }
    
    static warning(message) {
        this.log(message, 'WARNING');
    }
    
    static debug(message) {
        this.log(message, 'DEBUG');
    }
}
```

### Memory Leak Prevention

```javascript
// Always clean up in scene shutdown
class GameScene extends Phaser.Scene {
    shutdown() {
        // Remove listeners
        this.events.off('update');
        
        // Destroy sprites
        this.children.list.forEach(child => {
            if (child.destroy) child.destroy();
        });
        
        // Clear tweens
        this.tweens.killAll();
        
        // Stop sounds
        this.sound.stopAll();
    }
}
```

---

**Congratulations!** You now have the knowledge to build complex RPGs with Phaser.js. Keep experimenting and have fun! ðŸŽ®âœ¨
