import pygame as pg
import sys
from game.settings import *
from game.entities.player import Player
from game.utils.camera import Camera
from game.utils.projectile import ProjectileManager
from game.utils.audio.audio_manager import AudioManager
from game.level.level_manager import LevelManager
from game.ui.hud import HUD
from game.items.item_manager import ItemManager
from game.screens.item_selection_screen import ItemSelectionScreen
from game.screens.pause_menu import PauseMenu


from game.entities.enemies import (
    DemonSlime, BringerOfDeath, Skullwolf,  # Dungeon Monsters
    FlyingEye, Goblin, Mushroom, Skeleton,   # Grass Monsters
    Golem, Guardian, IceSkeleton              # Ice Monsters
)


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
        
        # AUDIO SYSTEM (Init early for Player)
        self.audio_manager = AudioManager()
        
        # Setup Level Manager
        self.level_manager = LevelManager(current_theme='dungeon')
        
        # Generate Rects, Gambar, dan Spawn Point dari Map
        self.platforms, self.visual_tiles, spawn_point, finish_rect, self.bg_images, self.enemy_spawns = self.level_manager.create_level()
        
        # Hitung Ukuran Level (World Size)
        max_x = 0
        max_y = 0
        if self.visual_tiles:
            max_x = max(r.right for _, r in self.visual_tiles)
            max_y = max(r.bottom for _, r in self.visual_tiles)
        else:
            max_x = WINDOW_WIDTH
            max_y = WINDOW_HEIGHT
            
        # add padding
        level_width = max(WINDOW_WIDTH, max_x)
        level_height = max(WINDOW_HEIGHT, max_y)
        self.camera.set_world_size(level_width, level_height)
        
        self.background = self.level_manager.create_world_background(level_width, level_height)
        
        # Create void background 
        self.void_image = None  # Not used with Tiled system
        
        # Spawn player
        self.player = Player(spawn_point[0], spawn_point[1], self.audio_manager)
        
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
        
        # Audio Theme Start
        self.audio_manager.play_theme_music(self.level_manager.theme)
        
        # ITEM SYSTEM
        self.item_manager = ItemManager()
        self.awaiting_item_selection = False
        self.current_item_choices = []
        self.selected_item_index = 0
        self.item_selection_screen = ItemSelectionScreen(self.screen, WINDOW_WIDTH, WINDOW_HEIGHT)
        
        # PAUSE MENU SYSTEM
        self.pause_menu = PauseMenu(self.screen, self.audio_manager)
        self.is_paused = False

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
        """Check if any enemy's attack hits player.
        
        Uses enemy.HIT_FRAME constant to determine when attack becomes active.
        Uses enemy.get_attack_hitbox() for attack rect calculation.
        """
        if not self.player.alive:
            return
        
        for enemy in self.enemies:
            if not enemy.alive or not enemy.is_attacking:
                # Reset tracking when not attacking
                self.enemy_hit_player.discard(id(enemy))
                if hasattr(self, 'enemy_last_attack_times') and id(enemy) in self.enemy_last_attack_times:
                    del self.enemy_last_attack_times[id(enemy)]
                continue
            
            # Track new attacks to reset hit tracking
            enemy_id = id(enemy)
            if not hasattr(self, 'enemy_last_attack_times'):
                self.enemy_last_attack_times = {}
            
            current_attack_time = enemy.last_attack_time
            if enemy_id not in self.enemy_last_attack_times or self.enemy_last_attack_times[enemy_id] != current_attack_time:
                self.enemy_hit_player.discard(enemy_id)
                self.enemy_last_attack_times[enemy_id] = current_attack_time
            
            # Skip if already hit player this attack
            if enemy_id in self.enemy_hit_player:
                continue
            
            # === FRAME CHECK: Use enemy's HIT_FRAME constant ===
            current_frame = int(enemy.animator.frame_index) if hasattr(enemy.animator, 'frame_index') else 0
            
            # Special handling for BringerOfDeath spell state
            if type(enemy).__name__ == 'BringerOfDeath':
                if enemy.state == 'cast':
                    continue  # Cast is channeling, no damage
                elif enemy.state == 'spell':
                    hit_frame = getattr(enemy, 'SPELL_HIT_FRAME', 6)
                    if current_frame < hit_frame:
                        continue
                else:
                    # Normal attack
                    if current_frame < enemy.HIT_FRAME:
                        continue
            elif enemy.state == 'shield':
                # Skeleton shield - no damage
                continue
            else:
                # Default: use enemy's HIT_FRAME constant
                if current_frame < enemy.HIT_FRAME:
                    continue
            
            # === GET ATTACK HITBOX from enemy ===
            attack_rect = enemy.get_attack_hitbox()
            
            # Special BOD spell has wider range
            if type(enemy).__name__ == 'BringerOfDeath' and enemy.state == 'spell':
                attack_rect = pg.Rect(
                    enemy.physics.rect.centerx - 90,
                    enemy.physics.rect.centery - 60,
                    180, 120
                )
            
            # Check collision with player
            if attack_rect.colliderect(self.player.physics.rect):
                print(f"[COLLISION] {type(enemy).__name__} attack_rect {attack_rect} hits Player {self.player.physics.rect}")
                
                damage = enemy.attack_power
                
                # Special BOD Spell Damage & Stun
                if type(enemy).__name__ == 'BringerOfDeath' and enemy.state == 'spell':
                    if hasattr(enemy, 'spell_damage'):
                        damage = enemy.spell_damage
                    
                    # Apply STUN to player
                    self.player.is_stunned = True
                    self.player.stun_end_time = pg.time.get_ticks() + 2000
                    self.player.state = 'hurt'
                    self.player.animator.frame_index = 0
                    print(f"[COMBAT] Player STUNNED by BOD Spell! Duration: 2s")
                    
                    # Apply knockback
                    knockback = getattr(enemy, 'spell_knockback', 0)
                    if knockback > 0:
                        if self.player.physics.rect.centerx > enemy.physics.rect.centerx:
                            self.player.physics.velocity.x = knockback
                        else:
                            self.player.physics.velocity.x = -knockback
                        self.player.physics.velocity.y = -8
                        print(f"[KNOCKBACK] Player knocked back! vx={self.player.physics.velocity.x}")
                
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
            
            # handle pause menu events first
            if self.is_paused:
                result = self.pause_menu.handle_event(event)
                if result == "resume":
                    self.is_paused = False
                    self.pause_menu.hide()
                elif result == "exit_menu":
                    return "exit_menu"
                continue
            
            if event.type == pg.KEYDOWN:
                # ESC = toggle pause menu
                if event.key == pg.K_ESCAPE:
                    self.is_paused = True
                    self.pause_menu.show()
                    continue
                
                # handle item selection input (block other inputs)
                if self.awaiting_item_selection:
                    if event.key == pg.K_LEFT or event.key == pg.K_a:
                        self.selected_item_index = 0
                    elif event.key == pg.K_RIGHT or event.key == pg.K_d:
                        self.selected_item_index = 1
                    elif event.key == pg.K_1:
                        self.confirm_item_selection(0)
                    elif event.key == pg.K_2:
                        self.confirm_item_selection(1)
                    elif event.key == pg.K_RETURN or event.key == pg.K_SPACE:
                        self.confirm_item_selection(self.selected_item_index)
                    continue
                
                if event.key == pg.K_F4:
                    is_fullscreen = self.screen.get_flags() & pg.FULLSCREEN
                    if is_fullscreen:
                        self.screen = pg.display.set_mode(WINDOW_SIZE)
                    else:
                        self.screen = pg.display.set_mode(WINDOW_SIZE, pg.FULLSCREEN)
                
                if event.key == pg.K_UP or event.key == pg.K_SPACE:
                    self.player.jump()
                
                # cheat: press F to instantly finish level
                if event.key == pg.K_f:
                    if not self.transitioning:
                        print("[CHEAT] Skipping level...")
                        self.transitioning = True
                        self.fade_state = 'OUT'
                
                # F3 = toggle debug hitbox visualization
                if event.key == pg.K_F3:
                    self.debug_mode = not self.debug_mode
                    print(f"[DEBUG] Hitbox visualization: {'ON' if self.debug_mode else 'OFF'}")
        
        return None
    
    def confirm_item_selection(self, index):
        """Player confirms item selection"""
        if index < len(self.current_item_choices):
            item_id = self.current_item_choices[index]
            
            # Pick and apply item
            self.item_manager.pick_item(item_id)
            self.item_manager.apply_item_to_player(self.player, item_id)
            
            # Clear selection state
            self.awaiting_item_selection = False
            self.current_item_choices = []
            
            print(f"[ITEM] Applied: {item_id}")
    
    def update(self):
        # Skip all updates when item selection is active
        if self.awaiting_item_selection:
            return
        
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
            
            # Update projectiles and check for player damage
            projectile_damage = self.projectile_manager.update(self.player, self.platforms)
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
            
            # Trigger Item Selection (if items available)
            if self.item_manager.get_pool_size() >= 2:
                self.current_item_choices = self.item_manager.get_random_choices(2)
                self.awaiting_item_selection = True
                self.selected_item_index = 0
                print(f"[ITEM] Choose: {self.current_item_choices}")
            
            self.level_manager.set_level(next_level_index)
            
            # Re-Generate Level
            self.platforms, self.visual_tiles, spawn_point, finish_rect, self.bg_images, self.enemy_spawns = self.level_manager.create_level()
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
            
            # Play BGM for new level theme
            self.audio_manager.play_theme_music(self.level_manager.theme)
            
        else:
            print("[INFO] No more levels! Game Completed.")
            self.level_manager.set_level(0)
            self.change_level()

    def draw(self):
        # Draw Item Selection Overlay if active
        if self.awaiting_item_selection:
            self.screen.fill((20, 20, 30))
            self.item_selection_screen.render(self.item_manager, self.current_item_choices, self.selected_item_index)
            pg.display.flip()
            return
        
        # Fill background with solid color (void)
        if self.level_manager.theme == 'snow':
            self.screen.fill((20, 30, 45))  # Dark blue for snow
        else:
            self.screen.fill((20, 20, 30))  # Dark grey for dungeon
        
        # Draw Level Background (Tiled Background)
        bg_x = -self.camera.offset.x
        bg_y = -self.camera.offset.y
        self.screen.blit(self.background, (bg_x, bg_y))
        
        # Draw TMX Image Layers with repeat support
        for bg_data in self.bg_images:
            if len(bg_data) >= 5:
                bg_img, offset_x, offset_y, repeat_x, repeat_y = bg_data
            else:
                bg_img, offset_x, offset_y = bg_data[:3]
                repeat_x, repeat_y = False, False
            
            img_w = bg_img.get_width()
            img_h = bg_img.get_height()
            
            # Calculate base position with camera offset
            base_x = offset_x - self.camera.offset.x
            base_y = offset_y - self.camera.offset.y
            
            if repeat_x or repeat_y:
                # Calculate world size for repeat
                world_w = max(r.right for _, r in self.visual_tiles) if self.visual_tiles else 5000
                world_h = max(r.bottom for _, r in self.visual_tiles) if self.visual_tiles else 3000
                
                # Calculate start/end positions for tiling
                if repeat_x:
                    start_x = int(offset_x - self.camera.offset.x) % img_w - img_w
                    end_x = int(world_w + 1280)
                else:
                    start_x = int(base_x)
                    end_x = start_x + img_w
                
                if repeat_y:
                    start_y = int(offset_y - self.camera.offset.y) % img_h - img_h
                    end_y = int(world_h + 720)
                else:
                    start_y = int(base_y)
                    end_y = start_y + img_h
                
                # Tile the image
                for x in range(start_x, end_x, img_w):
                    for y in range(start_y, end_y, img_h):
                        self.screen.blit(bg_img, (x, y))
            else:
                # Static (no repeat) - just draw once
                self.screen.blit(bg_img, (int(base_x), int(base_y)))
        
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
        
        # Draw Pause Menu Overlay
        if self.is_paused:
            self.pause_menu.draw()
        
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
            result = self.events()
            
            # handle pause menu result
            if result == "exit_menu":
                self.running = False
                return "exit_menu"
            
            if not self.is_paused:
                self.update()
            else:
                self.pause_menu.update()
            
            self.draw()
            self.clock.tick(FPS)
        
        return None