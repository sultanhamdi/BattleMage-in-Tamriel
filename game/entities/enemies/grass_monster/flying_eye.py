import pygame as pg
import math
from game.entities.enemies.enemy import BaseEnemy
from game.utils.projectile import ProjectileManager

# Path aset
FLYING_EYE_ASSET_PATH = 'assets/graphics/enemies/grass_monster/Flying eye/'
FLYING_EYE_PROJECTILE_PATH = 'assets/graphics/enemies/grass_monster/Flying eye/projectile/'

class FlyingEye(BaseEnemy):
    """
    Enemy Flying Eye - Flying Ranged Attacker.
    
    BEHAVIOR:
    - Flies (floats, no gravity)
    - 3 range attacks then must melee
    - Fires projectile during 'range' animation
    """
    
    # Constants
    HOVER_AMPLITUDE = 15
    HOVER_FREQUENCY = 0.08
    PROJECTILE_COOLDOWN = 600  # 10 seconds at 60fps
    
    # ATTACK TIMING (Override BaseEnemy)
    HIT_FRAME = 4  # Mid-swing melee hit
    
    def __init__(self, x, y):
        super().__init__(
            x=x, y=y,
            # GAMEPLAY HITBOX FIX: Larger for fair hit registration
            width=50, height=50,
            max_hp=45,
            attack_power=12,
            speed=3.0,
            asset_path=FLYING_EYE_ASSET_PATH,
            scale=1.8
        )
        
        # NO GRAVITY - flying
        self.has_gravity = True  # FIXED: Ground-based like other enemies (was False)
        
        # Combat ranges
        self.detection_range = 400
        self.attack_range = 50
        self.range_attack_range = 320
        self.lose_interest_range = 500
        
        # Custom Attack Box
        self.attack_box_width = 60
        self.attack_box_height = 55
        
        # Hover
        self.hover_offset = 0
        
        # GAMEPLAY HITBOX FIX: Flying Unit Problem
        # Moderate positive offset to align with floating body (not too high)
        self.sprite_offset_y = 15
        
        # Range attack system
        self.projectile_cooldown = 0
        self.range_attack_count = 0
        self.max_range_attacks = 2
        self.force_melee = False
        
        # Range attack state
        self.is_range_attacking = False
        self.projectile_fired = False
        
        # Combo system (BOD-style)
        self.attack_combo_count = 0
        self.max_combo_before_attack2 = 2  # 2x attack1 then 1x attack2
        self.is_attack2 = False
        
        self._setup_animations()
    
    def _setup_animations(self):
        animation_mapping = {
            'idle': 'flight',
            'walk': 'flight',
            'attack': 'attack',
            'attack2': 'attack2',
            # DISABLED: Range/projectile for now - focus on basic actions
            # 'range': 'range',
            'hurt': 'take_hit',
            'die': 'death',
        }
        self.animator.load_sprites(animation_mapping)
        self.animator.animation_speed = 0.15
    
    def update(self, platforms):
        """Update following Skullwolf pattern with flying mechanics."""
        # 1. Update Timers
        self.update_timers()
        
        if self.projectile_cooldown > 0:
            self.projectile_cooldown -= 1
        
        # 2. Handle hurt state
        current_time = pg.time.get_ticks()
        hurt_timeout = False
        if self.state == 'hurt':
            if current_time - self.last_hit_time > 400:
                hurt_timeout = True
        
        if self.state == 'hurt' and (self.animator.is_animation_finished() or hurt_timeout):
            self.state = 'idle'
            self.ai_state = self.STATE_IDLE
            self.is_attacking = False
            self.is_range_attacking = False
            self.animator.animation_finished = False
        
        # Removed hover effect - now ground-based
        # self.hover_offset += self.HOVER_FREQUENCY
        # hover_y = math.sin(self.hover_offset) * self.HOVER_AMPLITUDE
        
        # 3. Run AI if not hurt
        if self.state != 'hurt' and self.alive:
            self._update_ai()
            
            # Map AI state to visual state
            if self.is_range_attacking:
                self.state = 'range'
            elif self.ai_state in [self.STATE_CHASE, self.STATE_PATROL]:
                self.state = 'walk'
            elif self.ai_state == self.STATE_ATTACK:
                # Combo system: choose attack or attack2
                if self.is_attack2:
                    self.state = 'attack2'
                else:
                    self.state = 'attack'
            elif self.ai_state == self.STATE_IDLE:
                self.state = 'idle'
        
        # 4. Update Physics (NOW WITH GRAVITY - ground-based)
        if self.alive:
            self.physics.update(platforms, self.physics.velocity_x, apply_gravity=self.has_gravity)
        else:
            self.physics.update(platforms, 0, apply_gravity=self.has_gravity)
        
        # 5. Avoid player collision
        self.avoid_player_collision()
        
        # 6. Sync rect
        self.rect = self.physics.rect
    
    def _update_ai(self):
        """AI State Machine - Flying ranged attacker."""
        if not self.player_ref or not self.alive:
            self.ai_state = self.STATE_IDLE
            self.physics.velocity_x = 0
            return
            
        # 1. STRICT LOCK: If attacking, freeze velocity and do nothing else
        if self.is_attacking:
            self.physics.velocity_x = 0
            return
        
        distance = self.get_distance_to_player()
        direction = self.get_direction_to_player()
        self.facing_right = direction > 0
        
        # DISABLED: Range attack logic - focus on basic actions first
        # === HANDLE ONGOING RANGE ATTACK ===
        # if self.is_range_attacking:
        #     if not self.projectile_fired and self.animator.frame_index >= 5:
        #         self._fire_projectile()
        #         self.projectile_fired = True
        #     
        #     if self.animator.is_animation_finished():
        #         self.is_range_attacking = False
        #         self.projectile_fired = False
        #         self.projectile_cooldown = self.PROJECTILE_COOLDOWN
        #         self.range_attack_count += 1
        #         
        #         if self.range_attack_count >= self.max_range_attacks:
        #             self.force_melee = True
        #     
        #     self.physics.velocity_x = 0
        #     return
        
        # === STATE MACHINE ===
        
        if distance > self.lose_interest_range:
            self.ai_state = self.STATE_IDLE
            self.force_melee = False
            self.range_attack_count = 0
            self.physics.velocity_x = 0
            return
        
        if distance > self.detection_range:
            self.ai_state = self.STATE_IDLE
            self.physics.velocity_x = 0
            return
        
        if distance <= self.attack_range:
            self.ai_state = self.STATE_ATTACK
            if not self.is_attacking:
                # Combo logic (BOD-style): alternate attack1 and attack2
                if self.attack_combo_count >= self.max_combo_before_attack2:
                    self.is_attack2 = True
                    self.attack_combo_count = 0
                else:
                    self.is_attack2 = False
                    self.attack_combo_count += 1
                
                self.do_attack()
                self.force_melee = False
                self.range_attack_count = 0
            self.physics.velocity_x = 0
            return
        
        # DISABLED: Force melee and range attack triggers
        # if self.force_melee:
        #     self.ai_state = self.STATE_CHASE
        #     self.physics.velocity_x = direction * self.movement_speed
        #     return
        # 
        # if (distance < self.range_attack_range and 
        #     self.projectile_cooldown <= 0 and 
        #     self.range_attack_count < self.max_range_attacks):
        #     self self.is_range_attacking = True
        #     self.projectile_fired = False
        #     self.animator.reset_animation()
        #     self.physics.velocity_x = 0
        #     return
        
        self.ai_state = self.STATE_CHASE
        self.physics.velocity_x = direction * self.movement_speed
    
    def _fire_projectile(self):
        direction = self.get_direction_to_player()
        
        spawn_x = self.rect.centerx + (direction * 20)
        spawn_y = self.rect.centery
        
        pm = ProjectileManager.get_instance()
        pm.spawn_projectile(
            x=spawn_x,
            y=spawn_y,
            direction=direction,
            speed=8,
            damage=12,
            sprite_path=FLYING_EYE_PROJECTILE_PATH,
            scale=2.0,
            max_distance=400
        )
        print(f"[FLYING EYE] Projectile fired! ({self.range_attack_count + 1}/{self.max_range_attacks})")
    
    def take_damage(self, amount, apply_stun=False):
        self.is_range_attacking = False
        self.projectile_fired = False
        super().take_damage(amount, apply_stun=apply_stun)
