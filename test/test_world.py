"""
TEST WORLD - All Enemies Debug Level with GameManager Integration

Complete test environment with proper combat system.
"""

import pygame as pg
from game.entities.player import Player
from game.game_manager import Game
from game.entities.enemies.dungeon_monster.bringer_of_death import BringerOfDeath
from game.entities.enemies.dungeon_monster.skullwolf import Skullwolf
from game.entities.enemies.dungeon_monster.demon_slime import DemonSlime
from game.entities.enemies.grass_monster.goblin import Goblin
from game.entities.enemies.grass_monster.skeleton import Skeleton
from game.entities.enemies.grass_monster.mushroom import Mushroom
from game.entities.enemies.grass_monster.flying_eye import FlyingEye
from game.entities.enemies.ice_monster.ice_skeleton import IceSkeleton
from game.entities.enemies.ice_monster.guardian import Guardian
from game.entities.enemies.ice_monster.golem import Golem

class TestWorld:
    """Test world using GameManager for proper combat."""
    
    def __init__(self, screen):
        self.screen = screen
        self.clock = pg.time.Clock()
        
        # Create game instance without screen
        self.game = Game()
        
        # Override with simple FLAT GROUND ONLY (no obstacles)
        self.game.platforms = [
            pg.Rect(0, 600, 5000, 50),      # Extended flat ground
        ]
        
        # Spawn player at start
        self.game.player = Player(x=400, y=400)
        
        # Make player immortal for testing
        self.game.player.max_hp = 999999
        self.game.player.current_hp = 999999
        
        # Camera
        self.camera_offset = pg.math.Vector2(0, 0)
        
        # Spawn all enemies
        self.spawn_all_enemies()
        
        # Debug mode
        self.debug_mode = True
        self.freeze_enemies = False  # F to toggle freeze
        self.show_attack_rects = True  # Toggle to always show attack rects
        
        print("\n" + "="*60)
        print("TEST WORLD - GAME MANAGER INTEGRATED")
        print("="*60)
        print("CONTROLS:")
        print("  WASD/Arrows - Move")
        print("  J - Attack")
        print("  K - Spell")
        print("  F3 - Toggle debug")
        print("  F4 - Toggle attack rects (always show)")
        print("  R - Reset enemies")
        print("\nFEATURES:")
        print("  ✓ Full combat system")
        print("  ✓ Enemy attacks work")
        print("  ✓ Player immortal (999999 HP)")
        print("  ✓ Attack boxes visible")
        print("\n" + "="*60)
        print("ENEMY SPAWN TOGGLES (Clear all & spawn single):")
        print("="*60)
        print("  1 - Skullwolf      (Fast melee)")
        print("  2 - BringerOfDeath (Boss - scythe + spell)")
        print("  3 - Goblin         (Ranger - throws spears)")
        print("  4 - Skeleton       (Ranger - throws bones + shield)")
        print("  5 - Mushroom       (Ranger - spore cloud)")
        print("  6 - FlyingEye      (Flying ranger)")
        print("  7 - IceSkeleton    (Elite undead - react)")
        print("  8 - DemonSlime     (Boss - cleave)")
        print("  9 - Guardian       (Elite - combo spear)")
        print("  0 - Golem          (Tank - ground slam)")
        print("  BACKSPACE - Spawn ALL enemies")
        print("="*60)
        print("\nENEMIES SPAWNED:")
        for i, enemy in enumerate(self.game.enemies, 1):
            print(f"  {i}. {type(enemy).__name__} at x={enemy.rect.x}")
        print("="*60 + "\n")
    
    def spawn_all_enemies(self):
        """Spawn all 10 enemy types."""
        self.game.enemies.clear()
        
        enemies_to_spawn = [
            # Closer spawns for easier testing
            (Skullwolf, 200),
            (BringerOfDeath, 500),
            (Goblin, 800),
            (Skeleton, 1100),
            (Mushroom, 1400),
            (FlyingEye, 1700),
            (IceSkeleton, 2000),
            (DemonSlime, 2300),
            (Guardian, 2600),
            (Golem, 2900),
        ]
        
        for enemy_class, x_pos in enemies_to_spawn:
            # Calculate spawn y based on ground (600) minus hitbox height
            # Ground is at y=600, so enemy bottom should be at y=600
            if enemy_class == DemonSlime:
                spawn_y = 600 - 150  # height=150
            elif enemy_class == Guardian:
                spawn_y = 600 - 140  # height=140
            elif enemy_class == BringerOfDeath:
                spawn_y = 600 - 120  # height=120
            elif enemy_class == Golem:
                spawn_y = 600 - 80   # height=80
            elif enemy_class == Mushroom or enemy_class == IceSkeleton:
                spawn_y = 600 - 65   # height=65
            elif enemy_class == Goblin or enemy_class == Skeleton:
                spawn_y = 600 - 60   # height=60
            elif enemy_class == FlyingEye:
                spawn_y = 600 - 50 - 70  # height=50, offset_y=70 (floating)
            else:
                spawn_y = 600 - 48   # default (Skullwolf)
            
            enemy = enemy_class(x=x_pos, y=spawn_y)
            enemy.player_ref = self.game.player
            self.game.enemies.append(enemy)
    
    def spawn_single_enemy(self, enemy_class):
        """Clear all enemies and spawn single enemy for testing."""
        # Clear all enemies
        self.game.enemies.clear()
        
        # Spawn position (center-ish of screen)
        x_pos = 800
        
        # Calculate spawn y based on enemy hitbox height
        if enemy_class == DemonSlime:
            spawn_y = 600 - 150
        elif enemy_class == Guardian:
            spawn_y = 600 - 140
        elif enemy_class == BringerOfDeath:
            spawn_y = 600 - 120
        elif enemy_class == Golem:
            spawn_y = 600 - 80
        elif enemy_class == Mushroom or enemy_class == IceSkeleton:
            spawn_y = 600 - 65
        elif enemy_class == Goblin or enemy_class == Skeleton:
            spawn_y = 600 - 60
        elif enemy_class == FlyingEye:
            spawn_y = 600 - 50 - 70
        else:
            spawn_y = 600 - 48  # Skullwolf
        
        # Create and add enemy
        enemy = enemy_class(x=x_pos, y=spawn_y)
        enemy.player_ref = self.game.player
        self.game.enemies.append(enemy)
        
        print(f"\n[TEST] Spawned: {type(enemy).__name__} at x={x_pos}\n")
    
    def update_camera(self):
        """Camera follow player."""
        target_x = self.game.player.rect.centerx - 640
        target_y = self.game.player.rect.centery - 360
        
        self.camera_offset.x += (target_x - self.camera_offset.x) * 0.1
        self.camera_offset.y += (target_y - self.camera_offset.y) * 0.1
        
        self.camera_offset.x = max(0, min(self.camera_offset.x, 3200 - 1280))
        self.camera_offset.y = max(0, min(self.camera_offset.y, 720 - 720))
    
    def handle_input(self):
        """Handle test controls."""
        # No longer needed - all inputs moved to KEYDOWN events
        pass
    
    def run(self):
        """Main loop."""
        running = True
        
        while running:
            # Events
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    return False
                elif event.type == pg.KEYDOWN:
                    if event.key == pg.K_ESCAPE:
                        return True
                    elif event.key == pg.K_F3:
                        self.debug_mode = not self.debug_mode
                        print(f"[DEBUG] Hitboxes: {self.debug_mode}")
                    elif event.key == pg.K_F4:
                        self.show_attack_rects = not self.show_attack_rects
                        print(f"[DEBUG] Show attack rects: {self.show_attack_rects}")
                    elif event.key == pg.K_f:
                        self.freeze_enemies = not self.freeze_enemies
                        print(f"[DEBUG] Freeze Enemies: {self.freeze_enemies}")
                    
                    # Enemy spawn toggles (number keys 1-0)
                    elif event.key == pg.K_1:
                        self.spawn_single_enemy(Skullwolf)
                    elif event.key == pg.K_2:
                        self.spawn_single_enemy(BringerOfDeath)
                    elif event.key == pg.K_3:
                        self.spawn_single_enemy(Goblin)
                    elif event.key == pg.K_4:
                        self.spawn_single_enemy(Skeleton)
                    elif event.key == pg.K_5:
                        self.spawn_single_enemy(Mushroom)
                    elif event.key == pg.K_6:
                        self.spawn_single_enemy(FlyingEye)
                    elif event.key == pg.K_7:
                        self.spawn_single_enemy(IceSkeleton)
                    elif event.key == pg.K_8:
                        self.spawn_single_enemy(DemonSlime)
                    elif event.key == pg.K_9:
                        self.spawn_single_enemy(Guardian)
                    elif event.key == pg.K_0:
                        self.spawn_single_enemy(Golem)
                    elif event.key == pg.K_BACKSPACE:
                        self.spawn_all_enemies()
                        self.game.player.current_hp = 999999
                        print("[TEST] Reset - spawned ALL enemies!")
                    
                    elif event.key in [pg.K_UP, pg.K_SPACE, pg.K_w]:
                        self.game.player.jump()
            
            # Test controls
            self.handle_input()
            
            # Player keyboard state (like GameManager)
            keys = pg.key.get_pressed()
            
            # CHECK PLAYER STUN - freeze controls if stunned
            if hasattr(self.game.player, 'is_stunned') and self.game.player.is_stunned:
                current_time = pg.time.get_ticks()
                if current_time >= self.game.player.stun_end_time:
                    # Stun ended
                    self.game.player.is_stunned = False
                    print(f"[STUN] Player recovered from stun!")
                else:
                    # Still stunned - freeze player completely
                    self.game.player.physics.velocity.x = 0
                    # Skip all input processing
            else:
                # Normal input processing (not stunned)
                if keys[pg.K_LEFT] or keys[pg.K_a]:
                    self.game.player.physics.velocity.x = -self.game.player.movement_speed
                elif keys[pg.K_RIGHT] or keys[pg.K_d]:
                    self.game.player.physics.velocity.x = self.game.player.movement_speed
                else:
                    self.game.player.physics.velocity.x = 0
                
                if keys[pg.K_j]:
                    self.game.player.attack()
                if keys[pg.K_k]:
                    self.game.player.cast_spell()
            
            # Update player
            self.game.player.update(self.game.platforms)
            
            # Keep player immortal
            self.game.player.current_hp = min(self.game.player.current_hp, 999999)
            
            # Update enemies (skip if frozen)
            if not self.freeze_enemies:
                for enemy in self.game.enemies:
                    enemy.update(self.game.platforms)
            
            # Check combat (use GameManager methods)
            self.game.check_player_attack_collision()
            self.game.check_enemy_attack_collision()
            
            # Camera
            self.update_camera()
            
            # Draw
            self.screen.fill((40, 40, 50))
            
            # Platforms
            for platform in self.game.platforms:
                draw_rect = platform.copy()
                draw_rect.x -= self.camera_offset.x
                draw_rect.y -= self.camera_offset.y
                pg.draw.rect(self.screen, (100, 100, 120), draw_rect)
            
            # Enemies
            for enemy in self.game.enemies:
                enemy.draw(self.screen, self.camera_offset)
                
                if self.debug_mode:
                    # Enemy hitbox (red)
                    debug_rect = enemy.rect.copy()
                    debug_rect.x -= self.camera_offset.x
                    debug_rect.y -= self.camera_offset.y
                    pg.draw.rect(self.screen, (255, 0, 0), debug_rect, 2)
                    
                    # Facing direction arrow
                    center_y = debug_rect.centery
                    if enemy.facing_right:
                        # Arrow pointing RIGHT
                        arrow_start_x = debug_rect.right
                        arrow_end_x = debug_rect.right + 15
                        pg.draw.line(self.screen, (0, 255, 255), 
                                   (arrow_start_x, center_y), 
                                   (arrow_end_x, center_y), 3)
                        # Arrowhead
                        pg.draw.polygon(self.screen, (0, 255, 255), [
                            (arrow_end_x, center_y),
                            (arrow_end_x - 5, center_y - 4),
                            (arrow_end_x - 5, center_y + 4)
                        ])
                    else:
                        # Arrow pointing LEFT
                        arrow_start_x = debug_rect.left
                        arrow_end_x = debug_rect.left - 15
                        pg.draw.line(self.screen, (0, 255, 255), 
                                   (arrow_start_x, center_y), 
                                   (arrow_end_x, center_y), 3)
                        # Arrowhead
                        pg.draw.polygon(self.screen, (0, 255, 255), [
                            (arrow_end_x, center_y),
                            (arrow_end_x + 5, center_y - 4),
                            (arrow_end_x + 5, center_y + 4)
                        ])
                    
                    # Attack box (if attacking OR if show_attack_rects is enabled)
                    if enemy.is_attacking or self.show_attack_rects:
                        # Use enemy's actual attack box dimensions
                        attack_width = getattr(enemy, 'attack_box_width', 80)
                        attack_height = getattr(enemy, 'attack_box_height', 70)
                        
                        if enemy.facing_right:
                            attack_x = enemy.rect.right
                        else:
                            attack_x = enemy.rect.left - attack_width
                        
                        attack_box = pg.Rect(
                            attack_x - self.camera_offset.x,
                            enemy.rect.centery - attack_height//2 - self.camera_offset.y,
                            attack_width,
                            attack_height
                        )
                        pg.draw.rect(self.screen, (255, 255, 0), attack_box, 2)
                    
                    # Name with HP and POSITION
                    font = pg.font.Font(None, 20)
                    name = type(enemy).__name__
                    pos_x = int(enemy.rect.x)
                    pos_y = int(enemy.rect.y)
                    hp_text = f"{name} ({enemy.current_hp}/{enemy.max_hp}) POS:{pos_x},{pos_y}"
                    text = font.render(hp_text, True, (255, 255, 0))
                    self.screen.blit(text, (debug_rect.centerx - 80, debug_rect.top - 20))
            
            # Player
            self.game.player.draw(self.screen, self.camera_offset)
            
            if self.debug_mode:
                # Player hitbox (green)
                debug_rect = self.game.player.rect.copy()
                debug_rect.x -= self.camera_offset.x
                debug_rect.y -= self.camera_offset.y
                pg.draw.rect(self.screen, (0, 255, 0), debug_rect, 2)
                
                # Player attack box
                if self.game.player.is_attacking:
                    if self.game.player.physics.facing_right:
                        attack_x = self.game.player.rect.right
                    else:
                        attack_x = self.game.player.rect.left - 80
                    
                    attack_box = pg.Rect(
                        attack_x - self.camera_offset.x,
                        self.game.player.rect.centery - 35 - self.camera_offset.y,
                        80, 70
                    )
                    pg.draw.rect(self.screen, (0, 255, 255), attack_box, 2)
            
            # ===== ON-SCREEN UI OVERLAY =====
            # Background overlay for readability
            overlay = pg.Surface((450, 520))
            overlay.set_alpha(180)
            overlay.fill((20, 20, 30))
            self.screen.blit(overlay, (10, 10))
            
            # Title
            font_title = pg.font.Font(None, 36)
            title = font_title.render("TEST WORLD - Combat Ready", True, (255, 200, 50))
            self.screen.blit(title, (20, 20))
            
            # Status Info
            font = pg.font.Font(None, 24)
            y_offset = 60
            
            status_lines = [
                f"Player: IMMORTAL ({int(self.game.player.current_hp)} HP)",
                f"Enemies Alive: {len([e for e in self.game.enemies if e.alive])}/{len(self.game.enemies)}",
                f"Freeze: {'ON' if self.freeze_enemies else 'OFF'} (F)",
            ]
            
            for line in status_lines:
                surf = font.render(line, True, (255, 255, 255))
                self.screen.blit(surf, (20, y_offset))
                y_offset += 28
            
            # Controls
            y_offset += 10
            controls = font.render("F3-Debug | F4-AttackBox | BACKSPACE-Reset | ESC-Exit", True, (200, 200, 200))
            self.screen.blit(controls, (20, y_offset))
            
            # Enemy Spawn Toggles
            y_offset += 40
            font_toggle = pg.font.Font(None, 22)
            toggle_title = font.render("ENEMY SPAWN TOGGLES:", True, (100, 255, 255))
            self.screen.blit(toggle_title, (20, y_offset))
            y_offset += 30
            
            enemy_toggles = [
                "1-Skullwolf  2-BringerOfDeath  3-Goblin",
                "4-Skeleton   5-Mushroom        6-FlyingEye",
                "7-IceSkeleton 8-DemonSlime     9-Guardian",
                "0-Golem      BACKSPACE-ALL ENEMIES",
            ]
            
            for line in enemy_toggles:
                surf = font_toggle.render(line, True, (180, 255, 180))
                self.screen.blit(surf, (25, y_offset))
                y_offset += 24
            
            # Current Spawned Enemies
            y_offset += 15
            spawned_title = font.render("CURRENT ENEMIES:", True, (255, 200, 100))
            self.screen.blit(spawned_title, (20, y_offset))
            y_offset += 28
            
            font_small = pg.font.Font(None, 20)
            if self.game.enemies:
                for i, enemy in enumerate(self.game.enemies[:15], 1):  # Max 15 to prevent overflow
                    status = "ALIVE" if enemy.alive else "DEAD"
                    color = (100, 255, 100) if enemy.alive else (255, 100, 100)
                    enemy_info = f"{i}. {type(enemy).__name__} - {status}"
                    surf = font_small.render(enemy_info, True, color)
                    self.screen.blit(surf, (25, y_offset))
                    y_offset += 22
            else:
                no_enemy = font_small.render("No enemies spawned", True, (255, 100, 100))
                self.screen.blit(no_enemy, (25, y_offset))
            
            pg.display.flip()
            self.clock.tick(60)
        
        return True


def run_test_world():
    """Entry point."""
    pg.init()
    screen = pg.display.set_mode((1280, 720))
    pg.display.set_caption("Test World - Combat Debug")
    
    test = TestWorld(screen)
    result = test.run()
    
    return result


if __name__ == "__main__":
    run_test_world()
    pg.quit()
