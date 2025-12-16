import pygame as pg
import sys
from game.settings import *
from game.entities.player import Player
from game.utils.camera import Camera
from game.utils.projectile import ProjectileManager
from game.level.level_manager import LevelManager

# Import All Enemy Classes
from game.entities.enemies import (
    DemonSlime, BringerOfDeath, Skullwolf,  # Dungeon Monsters
    FlyingEye, Goblin, Mushroom, Skeleton,   # Grass Monsters
    Golem, Guardian, IceSkeleton              # Ice Monsters
)

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
        self.platforms, self.visual_tiles, spawn_point, finish_rect = self.level_manager.create_level()
        
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
        
        # Enemy System
        self.enemies = []
        self.player_hit_enemies = set()  # Track which enemies were hit in current attack
        self.enemy_hit_player = set()     # Track which enemies hit player in current attack
        self.spawn_enemies()
        
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

    def spawn_enemies(self):
        """
        Spawn enemies untuk level saat ini.
        Konfigurasi spawn per level.
        """
        # Clear existing enemies
        self.enemies = []
        self.player_hit_enemies.clear()
        self.enemy_hit_player.clear()
        
        # Get current level index
        level_index = self.level_manager.current_level_index
        
        # Enemy spawn configuration per level
        # Format: [(EnemyClass, x, y), ...]
        # Y positions should be on or near platforms (check TMX spawn point)
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
        
        print(f"[INFO] Total enemies spawned: {len(self.enemies)}")
    
    def check_player_attack_collision(self):
        """Check if player's attack hits any enemies"""
        if not self.player.is_attacking or not self.player.alive:
            # Reset tracking when not attacking
            self.player_hit_enemies.clear()
            return
        
        # Create attack hitbox based on player position and facing direction
        attack_width = 60
        attack_height = 70
        
        if self.player.physics.facing_right:
            attack_x = self.player.physics.rect.right
        else:
            attack_x = self.player.physics.rect.left - attack_width
        
        attack_y = self.player.physics.rect.centery - attack_height // 2
        attack_rect = pg.Rect(attack_x, attack_y, attack_width, attack_height)
        
        # Check collision with all enemies
        for enemy in self.enemies:
            if not enemy.alive:
                continue
            
            # Skip if already hit in this attack
            if id(enemy) in self.player_hit_enemies:
                continue
            
            # Check if attack hitbox overlaps enemy
            if attack_rect.colliderect(enemy.physics.rect):
                enemy.take_damage(self.player.attack_power)
                self.player_hit_enemies.add(id(enemy))
                print(f"[HIT] Player hits {type(enemy).__name__}! ({enemy.current_hp}/{enemy.max_hp} HP)")
    
    def check_enemy_attack_collision(self):
        """Check if any enemy's attack hits player"""
        if not self.player.alive:
            return
        
        for enemy in self.enemies:
            if not enemy.alive or not enemy.is_attacking:
                # Reset tracking when not attacking
                self.enemy_hit_player.discard(id(enemy))
                continue
            
            # Skip if already hit player in this attack
            if id(enemy) in self.enemy_hit_player:
                continue
            
            # Create attack hitbox for enemy
            attack_width = 50
            attack_height = 60
            
            if enemy.facing_right:
                attack_x = enemy.physics.rect.right
            else:
                attack_x = enemy.physics.rect.left - attack_width
            
            attack_y = enemy.physics.rect.centery - attack_height // 2
            attack_rect = pg.Rect(attack_x, attack_y, attack_width, attack_height)
            
            # Check collision with player - USE PHYSICS.RECT
            if attack_rect.colliderect(self.player.physics.rect):
                self.player.take_damage(enemy.attack_power)
                self.enemy_hit_player.add(id(enemy))
                print(f"[HIT] {type(enemy).__name__} hits Player! ({self.player.current_hp}/{self.player.max_hp} HP)")
    
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
            self.remove_dead_enemies()
            
            # Update projectiles and check for hits
            projectile_damage = self.projectile_manager.update(self.player)
            if projectile_damage > 0 and self.player.alive:
                self.player.take_damage(projectile_damage)
        
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
            self.platforms, self.visual_tiles, spawn_point, finish_rect = self.level_manager.create_level()
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
            self.spawn_enemies()
            
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
        
        # Draw Fade Overlay
        if self.transitioning or self.fade_alpha > 0:
            self.fade_surface.set_alpha(self.fade_alpha)
            self.screen.blit(self.fade_surface, (0, 0))
        
        pg.display.flip()

    def run(self):
        while self.running:
            self.events()
            self.update()
            self.draw()
            self.clock.tick(FPS)