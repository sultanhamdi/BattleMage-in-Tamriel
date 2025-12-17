import pygame as pg
import sys
from game.settings import *
from game.entities.player import Player
from game.utils.camera import Camera
from game.utils.projectile import ProjectileManager
from game.level.level_manager import LevelManager
from game.ui.hud import HUD  # RESTORED HUD IMPORT

# Import All Enemy Classes
from game.entities.enemies import (
    DemonSlime, BringerOfDeath, Skullwolf,  # Dungeon Monsters
    FlyingEye, Goblin, Mushroom, Skeleton,   # Grass Monsters
    Golem, Guardian, IceSkeleton              # Ice Monsters
)

# Mapping nama enemy (dari TMX) ke class
ENEMY_CLASSES = {
    'DemonSlime': DemonSlime,
    'BringerOfDeath': BringerOfDeath,
    'Skullwolf': Skullwolf,
    'FlyingEye': FlyingEye,
    'Goblin': Goblin,
    'Mushroom': Mushroom,
    'Skeleton': Skeleton,
    'Golem': Golem,
    'Guardian': Guardian,
    'IceSkeleton': IceSkeleton,
}

class Game:
    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode(WINDOW_SIZE)
        pg.display.set_caption(TITLE)
        self.clock = pg.time.Clock()
        self.running = True
        
        # Inisialisasi Kamera
        self.camera = Camera(WINDOW_WIDTH, WINDOW_HEIGHT)
        
        # Setup Level Manager
        self.level_manager = LevelManager(current_theme='dungeon')
        
        # Generate Rects, Gambar, dan Spawn Point dari Map
        self.platforms, self.visual_tiles, spawn_point, finish_rect, bg_images, self.enemy_spawns = self.level_manager.create_level()
        
        # Hitung Ukuran Level (World Size)
        max_x = 0
        max_y = 0
        if self.visual_tiles:
            max_x = max(r.right for _, r in self.visual_tiles)
            max_y = max(r.bottom for _, r in self.visual_tiles)
        else:
            max_x = WINDOW_WIDTH
            max_y = WINDOW_HEIGHT
            
        # Tambahkan sedikit padding
        level_width = max(WINDOW_WIDTH, max_x)
        level_height = max(WINDOW_HEIGHT, max_y)
        self.camera.set_world_size(level_width, level_height)
        
        self.background = self.level_manager.create_world_background(level_width, level_height)
        
        # Create void background (fallback solid color)
        self.void_image = None  # Not used with Tiled system
        
        # Spawn player
        self.player = Player(spawn_point[0], spawn_point[1])
        
        # UI HUD System (RESTORED)
        self.hud = HUD(self.screen, self.player)
        
        # Enemy System
        self.enemies = []
        self.player_hit_enemies = set()  # Track which enemies were hit in current attack
        self.enemy_hit_player = set()     # Track which enemies hit player in current attack
        self.enemy_last_attack_times = {}  # Track last attack time per enemy to detect new attacks
        self.last_player_attack_state = None  # Track attack state for combo reset
        self.spawn_enemies(self.enemy_spawns)
        
        # Projectile System
        self.projectile_manager = ProjectileManager.get_instance()
        self.projectile_manager.clear()  # Clear any leftover projectiles
        
        # Level Transition
        self.finish_rect = finish_rect
        self.transitioning = False
        self.fade_alpha = 0
        self.fade_speed = 5
        self.fade_surface = pg.Surface(WINDOW_SIZE)
        self.fade_surface.fill((0, 0, 0))
        self.fade_state = 'IN'
        
        # DEBUG MODE - Press F3 to toggle hitbox visualization
        self.debug_mode = False

    def spawn_enemies(self, enemy_spawns=None):
        """
        Spawn enemies untuk level saat ini.
        Prioritas: TMX enemy_spawns, fallback ke spawn_config.
        """
        # Clear existing enemies
        self.enemies = []
        self.player_hit_enemies.clear()
        self.enemy_hit_player.clear()
        
        # Prioritas 1: Spawn dari TMX enemy_spawns
        if enemy_spawns:
            for enemy_name, x, y in enemy_spawns:
                EnemyClass = ENEMY_CLASSES.get(enemy_name)
                if EnemyClass:
                    enemy = EnemyClass(x, y)
                    enemy.set_player_reference(self.player)
                    self.enemies.append(enemy)
                    print(f"[SPAWN] {enemy_name} at ({x}, {y})")
                else:
                    print(f"[WARNING] Unknown enemy class: {enemy_name}")
            
            print(f"[INFO] Total enemies spawned from TMX: {len(self.enemies)}")
            return
        
        # Prioritas 2: Fallback ke spawn_config (backward compatibility)
        level_index = self.level_manager.current_level_index
        
        # Enemy spawn configuration per level (legacy)
        spawn_config = {
            0: [  # Level 1 - Dungeon Monsters
                (DemonSlime, 800, 2150),
                (Skullwolf, 1100, 2150),
                (DemonSlime, 1400, 2150),
            ],
            1: [  # Level 2 - Dungeon Monsters (harder)
                (Skullwolf, 900, 1400),
                (BringerOfDeath, 1300, 1450),
                (DemonSlime, 1600, 1450),
                (Skullwolf, 1900, 1450),
            ],
            2: [  # Level 3 - Dungeon Monsters (boss prep)
                (BringerOfDeath, 1000, 3550),
                (Skullwolf, 1400, 3550),
                (BringerOfDeath, 1800, 3550),
                (DemonSlime, 2200, 3550),
            ],
            3: [  # Level 4 - Ice Zone (Ice Monsters)
                (Golem, 900, 2100),
                (IceSkeleton, 1200, 2100),
                (Guardian, 1500, 2100),
                (IceSkeleton, 1800, 2100),
            ],
            4: [  # Level 5 - Grass Monsters (final)
                (Goblin, 800, 2100),
                (FlyingEye, 1000, 2000),
                (Skeleton, 1400, 2100),
                (Mushroom, 1800, 2100),
            ],
        }
        
        # Get enemies for current level
        enemies_to_spawn = spawn_config.get(level_index, [])
        
        # Spawn enemies
        for EnemyClass, x, y in enemies_to_spawn:
            enemy = EnemyClass(x, y)
            enemy.set_player_reference(self.player)
            self.enemies.append(enemy)
            print(f"[SPAWN] {EnemyClass.__name__} at ({x}, {y})")
        
        print(f"[INFO] Total enemies spawned (fallback): {len(self.enemies)}")
    
    def check_player_attack_collision(self):
        """Check if player's attack hits any enemies"""
        # Determine if player is in any attack state
        attack_states = ['attack1', 'attack2', 'attack3', 'crouch_attack', 'spin_attack', 'sustain_arcane']
        current_state = self.player.state
        
        is_attacking = self.player.is_attacking or current_state in ['spin_attack', 'sustain_arcane']
        
        if not is_attacking or not self.player.alive:
            # Reset tracking when not attacking
            self.player_hit_enemies.clear()
            self.last_player_attack_state = None
            return
        
        # Check if attack state changed (e.g., attack1 -> attack2)
        # This allows each combo hit to damage enemies separately
        if current_state != self.last_player_attack_state:
            self.player_hit_enemies.clear()
            self.last_player_attack_state = current_state
        
        # Create attack hitbox based on attack type
        # ACTIVE FRAME: Damage only applies when animation reaches the "impact" frames
        current_frame = int(self.player.animator.frame_index)
        
        if current_state == 'spin_attack':
            # Spin attack: 360-degree AOE around player (active from frame 2)
            if current_frame < 2:
                return  # Not yet swinging
            attack_width = 100
            attack_height = 80
            attack_x = self.player.physics.rect.centerx - attack_width // 2
            attack_y = self.player.physics.rect.centery - attack_height // 2
            damage = int(self.player.attack_power * 1.5)  # 50% more damage
            
        elif current_state == 'sustain_arcane':
            # Sustain Arcane: Long range fire attack (active from frame 3)
            if current_frame < 3:
                return  # Channeling
            attack_width = 120
            attack_height = 50
            if self.player.physics.facing_right:
                attack_x = self.player.physics.rect.right + 8
            else:
                attack_x = self.player.physics.rect.left - attack_width - 8
            attack_y = self.player.physics.rect.centery - attack_height // 2 - 10
            damage = int(self.player.attack_power * 0.8)  # Per-frame damage (lower)
            
        elif current_state == 'crouch_attack':
            # Crouch attack: Lower hitbox (active from frame 2)
            if current_frame < 2:
                return  # Winding up
            attack_width = 50
            attack_height = 40
            if self.player.physics.facing_right:
                attack_x = self.player.physics.rect.right
            else:
                attack_x = self.player.physics.rect.left - attack_width
            attack_y = self.player.physics.rect.bottom - attack_height
            damage = self.player.attack_power
            
        else:
            # Normal combo attacks (attack1, attack2, attack3)
            # Active from frame 3 - when sword is actually swinging
            if current_frame < 3:
                return  # Sword not yet in swing arc
            attack_width = 60
            attack_height = 70
            if self.player.physics.facing_right:
                attack_x = self.player.physics.rect.right
            else:
                attack_x = self.player.physics.rect.left - attack_width
            attack_y = self.player.physics.rect.centery - attack_height // 2
            damage = self.player.attack_power
        
        attack_rect = pg.Rect(attack_x, attack_y, attack_width, attack_height)
        
        # Check collision with all enemies
        for enemy in self.enemies:
            if not enemy.alive:
                continue
            
            # Skip if already hit in this attack (except sustain_arcane which can hit multiple times)
            if current_state != 'sustain_arcane' and id(enemy) in self.player_hit_enemies:
                continue
            
            # For sustain_arcane, add a frame-based cooldown per enemy
            if current_state == 'sustain_arcane':
                # Only hit every few frames to prevent instant kill
                frame_idx = int(self.player.animator.frame_index)
                if frame_idx % 5 != 0:  # Hit every 5 frames
                    continue
            
            # Check if attack hitbox overlaps enemy
            if attack_rect.colliderect(enemy.physics.rect):
                # Apply stun if using arcane spell
                apply_stun = (current_state == 'sustain_arcane')
                enemy.take_damage(damage, apply_stun=apply_stun)
                self.player_hit_enemies.add(id(enemy))
                print(f"[HIT] Player hits {type(enemy).__name__}! ({enemy.current_hp}/{enemy.max_hp} HP)")
    
    def check_enemy_attack_collision(self):
        """Check if any enemy's attack hits player"""
        if not self.player.alive:
            return
        
        for enemy in self.enemies:
            # Debug: Log BringerOfDeath attacking state
            if type(enemy).__name__ == 'BringerOfDeath':
                print(f"[BOD DEBUG] is_attacking={enemy.is_attacking} state={enemy.state} ai_state={enemy.ai_state}")
            
            if not enemy.alive or not enemy.is_attacking:
                # Reset tracking when not attacking
                self.enemy_hit_player.discard(id(enemy))
                # FIX: Also reset the attack time tracking so next attack is treated as NEW
                if hasattr(self, 'enemy_last_attack_times') and id(enemy) in self.enemy_last_attack_times:
                    del self.enemy_last_attack_times[id(enemy)]
                    # DEBUG: Log when tracking is reset for Golem
                    if type(enemy).__name__ == 'Golem':
                        print(f"[GOLEM RESET] is_attacking={enemy.is_attacking} state={enemy.state} - Tracking CLEARED")
                continue
            
            # NEW: Track when each enemy starts a new attack
            # If this is a new attack (different last_attack_time), clear the hit tracking
            enemy_id = id(enemy)
            if not hasattr(self, 'enemy_last_attack_times'):
                self.enemy_last_attack_times = {}
            
            current_attack_time = enemy.last_attack_time
            if enemy_id not in self.enemy_last_attack_times or self.enemy_last_attack_times[enemy_id] != current_attack_time:
                # New attack started, clear hit tracking for this enemy
                self.enemy_hit_player.discard(enemy_id)
                self.enemy_last_attack_times[enemy_id] = current_attack_time
            
            # Skip if already hit player in THIS specific attack
            if enemy_id in self.enemy_hit_player:
                print(f"[DEBUG] Enemy {type(enemy).__name__} already hit player in current attack")
                continue
            
            # Create attack hitbox for enemy
            # Attack box extends IN FRONT of enemy hitbox (not overlapping)
            # Use enemy's custom attack box size if available
            attack_width = getattr(enemy, 'attack_box_width', 70)
            attack_height = getattr(enemy, 'attack_box_height', 60)
            
            # ACTIVE FRAME CHECK: Only apply damage during specific animation frames
            # This makes attacks feel more realistic and gives player chance to dodge
            current_frame = int(enemy.animator.frame_index) if hasattr(enemy.animator, 'frame_index') else 0
            
            # Special handling for BringerOfDeath
            if type(enemy).__name__ == 'BringerOfDeath':
                if enemy.state == 'attack':
                    # Normal attack: active from frame 5 (when scythe swings)
                    if current_frame < 5:
                        continue  # Not yet in active frames
                elif enemy.state == 'cast':
                    # Cast spell: larger hitbox, active from frame 4
                    if current_frame < 4:
                        continue  # Still channeling
                    attack_width = 180  # Wider spell range
                    attack_height = 120
                    
            # Special handling for DemonSlime (15 frames total)
            elif type(enemy).__name__ == 'DemonSlime':
                if enemy.state == 'attack':
                    # User feedback: still delayed, reduce to frame 2
                    if current_frame < 2:
                        continue
                    # Use custom attack box (already set via attack_box_width/height)
            
            # Grass Monsters - Different thresholds per enemy
            elif type(enemy).__name__ in ['FlyingEye', 'Goblin']:
                if enemy.state in ['attack', 'attack2']:
                    # 8 frames: hit at frame 4 (mid-swing) - OK
                    if current_frame < 4:
                       continue
            
            elif type(enemy).__name__ in ['Mushroom', 'Skeleton']:
                if enemy.state in ['attack', 'attack2']:
                    # User feedback: slightly early, increase to frame 5
                    if current_frame < 5:
                       continue
                elif enemy.state == 'shield':  # Skeleton only
                    continue
            
            # Ice Skeleton (18 frames total)
            elif type(enemy).__name__ == 'IceSkeleton':
                # FIX: Check lowercase 'attack' (matches enemy.state assignment)
                if enemy.state == 'attack':
                    # User says: udah pas at frame 6
                    if current_frame < 6:
                        continue
            
            # Golem (11 frames total)
            elif type(enemy).__name__ == 'Golem':
                if enemy.state == 'attack':
                    # Asset: 004 = visual impact at frame 4 (Increased to 6 for delay)
                    if current_frame < 6:
                        continue
                else:
                    continue
            
            # Guardian (14 frames total)
            elif type(enemy).__name__ == 'Guardian':
                if enemy.state == 'attack':
                    # Asset: 1_atk_6 = visual impact at frame 6 (Increased to 11 for delay)
                    if current_frame < 11:
                        continue
                else:
                    continue
            
            # Skullwolf (5 frames total) - keep default
            elif type(enemy).__name__ == 'Skullwolf':
                if enemy.state == 'attack':
                    # 5 frames: quick pounce, hit early (frame 2)
                    if current_frame < 2:
                        continue  # Starting pounce
                    
            else:
                # Default for any other enemies (frame 3+)
                if current_frame < 3:
                    continue
            
            # Start from hitbox edge, extend in facing direction
            if enemy.facing_right:
                attack_x = enemy.physics.rect.right  # Start from right edge
            else:
                attack_x = enemy.physics.rect.left - attack_width  # Start from left edge
            
            
            # Calculate Y position (raised for spell cast)
            if type(enemy).__name__ == 'BringerOfDeath' and enemy.state == 'cast':
                # CURSE MECHANIC: Tornado follows player! (unavoidable)
                if hasattr(enemy, 'spell_target_player') and enemy.spell_target_player:
                    # Lock onto player center, 100px above head
                    attack_x = self.player.physics.rect.centerx - attack_width // 2
                    attack_y = self.player.physics.rect.top - 100  # 100px above player
                    print(f"🎯 [CURSE TRACKING] Tornado following player at ({attack_x}, {attack_y})")
                else:
                    # Normal spell at BOD's position
                    attack_y = enemy.physics.rect.centery - attack_height // 2 - 100  # Raised 100px for tornado
            else:
                attack_y = enemy.physics.rect.centery - attack_height // 2
            
            attack_rect = pg.Rect(attack_x, attack_y, attack_width, attack_height)
            
            # Debug collision check for BringerOfDeath only
            if type(enemy).__name__ == 'BringerOfDeath':
                print(f"[BOD ATTACK] attack_rect={attack_rect} player_rect={self.player.physics.rect} collision={attack_rect.colliderect(self.player.physics.rect)}")
            
            # Check collision with player - USE PHYSICS.RECT
            if attack_rect.colliderect(self.player.physics.rect):
                print(f"[COLLISION] {type(enemy).__name__} attack_rect {attack_rect} hits Player {self.player.physics.rect}")
                
                # Apply damage
                damage = enemy.attack_power
                
                # Special handling for BringerOfDeath spell attacks
                if type(enemy).__name__ == 'BringerOfDeath' and enemy.state == 'cast':
                    # Use spell damage instead of normal attack power
                    damage = getattr(enemy, 'spell_damage', enemy.attack_power)
                    
                    # Apply knockback
                    knockback = getattr(enemy, 'spell_knockback', 0)
                    if knockback > 0:
                        # Determine knockback direction (away from BOD)
                        if self.player.physics.rect.centerx > enemy.physics.rect.centerx:
                            # Player on right, knock right
                            self.player.physics.velocity.x = knockback
                        else:
                            # Player on left, knock left
                            self.player.physics.velocity.x = -knockback
                        
                        # Also knock upward
                        self.player.physics.velocity.y = -8
                        print(f"[KNOCKBACK] Player knocked back! vx={self.player.physics.velocity.x}")
                        
                        # Apply player stun at frame 6+ (when tornado visually hits)
                        current_frame = int(enemy.animator.frame_index)
                        print(f"[DEBUG STUN] BOD spell frame={current_frame}, checking if >= 6...")
                        if current_frame >= 6:
                            if not hasattr(self.player, 'is_stunned'):
                                self.player.is_stunned = False
                                self.player.stun_end_time = 0
                            
                            # Only stun if not already stunned (prevent re-stunning)
                            if not self.player.is_stunned:
                                self.player.is_stunned = True
                                self.player.stun_end_time = pg.time.get_ticks() + 2000  # 2 second stun
                                # Force player into hurt state for visual feedback
                                self.player.state = 'hurt'
                                self.player.animator.reset_animation()
                                print(f"[STUN] Player STUNNED at frame {current_frame}! Tornado hit! Hurt loop for 2s")
                        else:
                            print(f"[DEBUG STUN] Frame {current_frame} < 6, not stunning yet")
                
                self.player.take_damage(damage)
                self.enemy_hit_player.add(id(enemy))
                print(f"[HIT] {type(enemy).__name__} hits Player! ({self.player.current_hp}/{self.player.max_hp} HP)")
    
    def check_entity_collision(self):
        """
        One-way collision: Enemy cannot overlap player (player = wall for enemy).
        Player CAN walk through enemies freely.
        When enemy is inside player, push enemy back to attack_range distance.
        """
        if not self.player.alive:
            return
        
        player_rect = self.player.physics.rect
        
        for enemy in self.enemies:
            if not enemy.alive:
                continue
            
            enemy_rect = enemy.physics.rect
            
            if player_rect.colliderect(enemy_rect):
                # Push enemy out to attack_range distance from player
                # This makes enemy stand at proper attack distance, not inside player
                attack_dist = enemy.attack_range
                
                if enemy_rect.centerx < player_rect.centerx:
                    # Enemy on left - push to left side at attack range
                    enemy.physics.rect.right = player_rect.left - attack_dist + enemy.physics.rect.width
                else:
                    # Enemy on right - push to right side at attack range
                    enemy.physics.rect.left = player_rect.right + attack_dist - enemy.physics.rect.width
                
                # Sync float position
                enemy.physics.pos.x = enemy.physics.rect.x
    
    def remove_dead_enemies(self):
        """Remove enemies that finished their death animation"""
        # Keep enemies that are alive OR still playing death animation
        self.enemies = [
            e for e in self.enemies 
            if e.alive or (not e.alive and not e.animator.is_animation_finished())
        ]

    def events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
                pg.quit()
                sys.exit()
            
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_F4:
                    is_fullscreen = self.screen.get_flags() & pg.FULLSCREEN
                    if is_fullscreen:
                        self.screen = pg.display.set_mode(WINDOW_SIZE)
                    else:
                        self.screen = pg.display.set_mode(WINDOW_SIZE, pg.FULLSCREEN)
                
                if event.key == pg.K_UP or event.key == pg.K_SPACE:
                    self.player.jump()
                
                # Cheat: Press F to instantly finish level (for development)
                if event.key == pg.K_f:
                    if not self.transitioning:
                        print("[CHEAT] Skipping level...")
                        self.transitioning = True
                        self.fade_state = 'OUT'
                
                # F3 = Toggle debug hitbox visualization
                if event.key == pg.K_F3:
                    self.debug_mode = not self.debug_mode
                    print(f"[DEBUG] Hitbox visualization: {'ON' if self.debug_mode else 'OFF'}")
    
    def update(self):
        # Update Player & Camera (Hanya jika tidak sedang transisi penuh)
        if not self.transitioning or (self.transitioning and self.fade_state == 'IN'):
            self.player.update(self.platforms)
            self.camera.follow(self.player.physics.rect)  # USE PHYSICS.RECT
            
            # Update all enemies
            for enemy in self.enemies:
                enemy.update(self.platforms)
            
            # Combat checks
            self.check_player_attack_collision()
            self.check_enemy_attack_collision()
            # Note: Entity collision is handled in BaseEnemy.avoid_player_collision()
            self.remove_dead_enemies()
            
            if projectile_damage > 0 and self.player.alive:
                self.player.take_damage(projectile_damage)
            
            # Update HUD
            self.hud.update()
        
        # Cek Finish Point Trigger - USE PHYSICS.RECT
        if self.finish_rect and not self.transitioning:
            if self.player.physics.rect.colliderect(self.finish_rect):
                print("[EVENT] Player reached finish point! Starting transition...")
                self.transitioning = True
                self.fade_state = 'OUT' 

        # Handle Transition Fade
        if self.transitioning:
            if self.fade_state == 'OUT':
                self.fade_alpha += self.fade_speed
                if self.fade_alpha >= 255:
                    self.fade_alpha = 255
                    # Layar sudah hitam pekat, Ganti Level
                    self.change_level()
                    self.fade_state = 'IN'
            
            elif self.fade_state == 'IN':
                self.fade_alpha -= self.fade_speed
                if self.fade_alpha <= 0:
                    self.fade_alpha = 0
                    self.transitioning = False
                    
    def change_level(self):
        # Naikkan index level
        next_level_index = self.level_manager.current_level_index + 1
        
        # Cek apakah level selanjutnya ada
        if next_level_index < len(self.level_manager.levels):
            print(f"[INFO] Loading Level {next_level_index + 1}...")
            self.level_manager.set_level(next_level_index)
            
            # Re-Generate Level
            self.platforms, self.visual_tiles, spawn_point, finish_rect, bg_images, self.enemy_spawns = self.level_manager.create_level()
            self.finish_rect = finish_rect
            
            # Re-Calculate Background Size
            max_x = 0
            max_y = 0
            if self.visual_tiles:
                max_x = max(r.right for _, r in self.visual_tiles)
                max_y = max(r.bottom for _, r in self.visual_tiles)
            else:
                max_x = WINDOW_WIDTH
                max_y = WINDOW_HEIGHT
            
            level_width = max(WINDOW_WIDTH, max_x)
            level_height = max(WINDOW_HEIGHT, max_y)
            self.camera.set_world_size(level_width, level_height)
            
            # Re-Create Background (World Size)
            self.background = self.level_manager.create_world_background(level_width, level_height)
            
            # Re-spawn enemies for new level
            self.spawn_enemies(self.enemy_spawns)
            
            # Clear projectiles from previous level
            self.projectile_manager.clear()
            
            # Reset Player Position & Camera - USE PHYSICS.RECT
            self.player.physics.rect.topleft = spawn_point
            self.player.physics.pos.x = spawn_point[0]
            self.player.physics.pos.y = spawn_point[1]
            self.player.physics.velocity.xy = (0, 0)
            # Sync rect after position update
            self.player.rect = self.player.physics.rect
            
            self.camera.follow(self.player.physics.rect)
            
        else:
            print("[INFO] No more levels! Game Completed.")
            self.level_manager.set_level(0)
            self.change_level()

    def draw(self):
        # Fill background with solid color (void)
        if self.level_manager.theme == 'snow':
            self.screen.fill((20, 30, 45))  # Dark blue for snow
        else:
            self.screen.fill((20, 20, 30))  # Dark grey for dungeon
        
        # Draw Level Background (Dungeon Image)
        bg_x = -self.camera.offset.x
        bg_y = -self.camera.offset.y
        self.screen.blit(self.background, (bg_x, bg_y))
        
        # Gambar Tileset
        for img, rect in self.visual_tiles:
            draw_pos_x = rect.x - self.camera.offset.x
            draw_pos_y = rect.y - self.camera.offset.y
            self.screen.blit(img, (draw_pos_x, draw_pos_y))
        
        # Draw all enemies
        for enemy in self.enemies:
            enemy.draw(self.screen, self.camera.offset)
        
        # Draw projectiles
        self.projectile_manager.draw(self.screen, self.camera.offset)

        # Gambar Player
        self.player.draw(self.screen, self.camera.offset)
        
        # Draw HUD (UI Layer)
        self.hud.draw()
        
        # DEBUG: Draw hitboxes if debug mode is on
        if self.debug_mode:
            self.draw_debug_hitboxes()
        
        # Draw Fade Overlay
        if self.transitioning or self.fade_alpha > 0:
            self.fade_surface.set_alpha(self.fade_alpha)
            self.screen.blit(self.fade_surface, (0, 0))
        
        pg.display.flip()
    
    def draw_debug_hitboxes(self):
        """Draw debug visualization of hitboxes and attack rects."""
        cam = self.camera.offset
        
        # Player hitbox (BLUE)
        player_rect = self.player.physics.rect.copy()
        player_rect.x -= cam.x
        player_rect.y -= cam.y
        pg.draw.rect(self.screen, (0, 100, 255), player_rect, 2)
        
        # Log player info
        p = self.player
        print(f"[PLAYER] pos=({p.physics.rect.x}, {p.physics.rect.y}) size=({p.physics.rect.width}x{p.physics.rect.height}) state={p.state} facing={'R' if p.physics.facing_right else 'L'}")
        
        # Player attack box (GREEN) - when attacking
        if p.is_attacking or p.state in ['spin_attack', 'sustain_arcane']:
            # Replicate attack rect logic from check_player_attack_collision
            current_frame = int(p.animator.frame_index)
            attack_rect = None
            
            if p.state == 'spin_attack' and current_frame >= 2:
                attack_width = 100
                attack_height = 80
                attack_x = p.physics.rect.centerx - attack_width // 2
                attack_y = p.physics.rect.centery - attack_height // 2
                attack_rect = pg.Rect(attack_x - cam.x, attack_y - cam.y, attack_width, attack_height)
                
            elif p.state == 'sustain_arcane' and current_frame >= 3:
                attack_width = 120
                attack_height = 50
                if p.physics.facing_right:
                    attack_x = p.physics.rect.right + 8
                else:
                    attack_x = p.physics.rect.left - attack_width - 8
                attack_y = p.physics.rect.centery - attack_height // 2 - 10
                attack_rect = pg.Rect(attack_x - cam.x, attack_y - cam.y, attack_width, attack_height)
                
            elif p.state == 'crouch_attack' and current_frame >= 2:
                attack_width = 50
                attack_height = 40
                if p.physics.facing_right:
                    attack_x = p.physics.rect.right
                else:
                    attack_x = p.physics.rect.left - attack_width
                attack_y = p.physics.rect.bottom - attack_height
                attack_rect = pg.Rect(attack_x - cam.x, attack_y - cam.y, attack_width, attack_height)
                
            elif p.state in ['attack1', 'attack2', 'attack3'] and current_frame >= 3:
                attack_width = 60
                attack_height = 70
                if p.physics.facing_right:
                    attack_x = p.physics.rect.right
                else:
                    attack_x = p.physics.rect.left - attack_width
                attack_y = p.physics.rect.centery - attack_height // 2
                attack_rect = pg.Rect(attack_x - cam.x, attack_y - cam.y, attack_width, attack_height)
            
            if attack_rect:
                pg.draw.rect(self.screen, (0, 255, 100), attack_rect, 2)  # GREEN
        
        # Enemies
        for enemy in self.enemies:
            if not enemy.alive:
                continue
            
            # Enemy hitbox (RED)
            enemy_rect = enemy.physics.rect.copy()
            enemy_rect.x -= cam.x
            enemy_rect.y -= cam.y
            pg.draw.rect(self.screen, (255, 50, 50), enemy_rect, 2)
            
            # Log enemy info
            e = enemy
            e_name = type(e).__name__
            print(f"[{e_name}] pos=({e.physics.rect.x}, {e.physics.rect.y}) size=({e.physics.rect.width}x{e.physics.rect.height}) state={e.state} facing={'R' if e.facing_right else 'L'} attacking={e.is_attacking}")
            
            # Enemy attack rect (YELLOW) - only when attacking
            if enemy.is_attacking:
                attack_width = getattr(enemy, 'attack_box_width', 70)
                attack_height = getattr(enemy, 'attack_box_height', 60)
                if enemy.facing_right:
                    attack_x = enemy.physics.rect.right  # Start from right edge
                else:
                    attack_x = enemy.physics.rect.left - attack_width  # Start from left edge
                attack_y = enemy.physics.rect.centery - attack_height // 2
                
                attack_rect = pg.Rect(attack_x - cam.x, attack_y - cam.y, attack_width, attack_height)
                pg.draw.rect(self.screen, (255, 255, 0), attack_rect, 2)
                
                # Log attack rect
                print(f"  [ATTACK_RECT] x={attack_x} y={attack_y} w={attack_width} h={attack_height}")
                
                # Log distance to player
                dist_x = p.physics.rect.centerx - e.physics.rect.centerx
                dist_y = p.physics.rect.centery - e.physics.rect.centery
                print(f"  [DISTANCE] dx={dist_x} dy={dist_y}")

    def run(self):
        while self.running:
            self.events()
            self.update()
            self.draw()
            self.clock.tick(FPS)