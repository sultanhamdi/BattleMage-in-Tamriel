import pygame as pg
import random
from game.entities.enemies.enemy import BaseEnemy
from game.utils.projectile import ProjectileManager

SKELETON_ASSET_PATH = 'assets/graphics/enemies/grass_monster/Skeleton/'
SKELETON_PROJECTILE_PATH = 'assets/graphics/enemies/grass_monster/Skeleton/projectile/'

class Skeleton(BaseEnemy):
    # defensive warrior with shield and bone throw
    
    BONE_COOLDOWN = 600
    SHIELD_TRIGGER_HITS = 3
    SHIELD_COOLDOWN = 900
    SHIELD_DAMAGE_REDUCTION = 0.5
    
    # attack timing
    HIT_FRAME = 5
    
    def __init__(self, x, y):
        super().__init__(
            x=x, y=y,
            # GAMEPLAY HITBOX: Wider for fair hits
            width=50, height=60,
            max_hp=70,
            attack_power=14,
            speed=2.8,
            asset_path=SKELETON_ASSET_PATH,
            scale=1.8
        )
        
        # Combat ranges
        self.detection_range = 320
        self.attack_range = 55
        self.bone_range = 260
        self.lose_interest_range = 400
        
        # Custom Attack Box
        self.attack_box_width = 70
        self.attack_box_height = 65
        
        # Shield
        self.shield_active = False
        
        # Bone throw system
        self.bone_cooldown = 0
        self.bone_count = 0
        self.max_bones = 2
        self.force_melee = False
        
        # Bone throw state
        self.is_throwing = False
        self.bone_thrown = False
        
        # Combo system (BOD-style)
        self.attack_combo_count = 0
        self.max_combo_before_attack2 = 2  # 2x attack1 then 1x attack2
        self.is_attack2 = False
        
        # Shield system (BOD-style hit counter)
        self.hit_counter = 0
        self.is_shield_ready = False
        self.is_shielding = False
        self.shield_cooldown = 0
        
        # GAMEPLAY HITBOX FIX: Sprite defaults face RIGHT, flipped when LEFT
        # POSITIVE value gets INVERTED when facing left (becomes negative shift)
        self.sprite_anchor_offset = +15
        
        self._setup_animations()
    
    def _setup_animations(self):
        animation_mapping = {
            'idle': 'idle',
            'walk': 'walk',
            'attack': 'attack',
            'attack2': 'attack2',
            # DISABLED: Range/projectile for now - focus on basic actions
            # 'range': 'range',
            'shield': 'shield',
            'hurt': 'take_hit',
            'die': 'death',
        }
        self.animator.load_sprites(animation_mapping)
        self.animator.animation_speed = 0.12
    

    
    def update(self, platforms):
        # 1. Update Timers
        self.update_timers()
        
        if self.bone_cooldown > 0:
            self.bone_cooldown -= 1
        
        if self.shield_cooldown > 0:
            self.shield_cooldown -= 1
        
        # 2. Handle hurt state
        current_time = pg.time.get_ticks()
        hurt_timeout = False
        if self.state == 'hurt':
            if current_time - self.last_hit_time > 500:
                hurt_timeout = True
        
        if self.state == 'hurt' and (self.animator.is_animation_finished() or hurt_timeout):
            self.state = 'idle'
            self.ai_state = self.STATE_IDLE
            self.is_attacking = False
            self.is_throwing = False
            self.animator.animation_finished = False
        
        # 3. Run AI if not hurt
        if self.state != 'hurt' and self.alive:
            self._update_ai()
            
            # Map AI state to visual state
            if self.is_throwing:
                self.state = 'range'
            elif self.is_shielding:
                self.state = 'shield'
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
        
        # 4. Update Physics
        if self.alive:
            self.physics.update(platforms, self.physics.velocity_x, apply_gravity=self.has_gravity)
        else:
            self.physics.update(platforms, 0, apply_gravity=self.has_gravity)
        
        # 5. Avoid player collision
        self.avoid_player_collision()
        
        # 6. Sync rect
        self.rect = self.physics.rect
    
    def _update_ai(self):
        if not self.player_ref or not self.alive:
            self.ai_state = self.STATE_IDLE
            self.physics.velocity_x = 0
            return
            
        # 1. STRICT LOCK: If attacking, freeze velocity and do nothing else
        if self.is_attacking:
            self.physics.velocity_x = 0
            return
        
        # PRIORITY: Shield if ready (BOD pattern)
        if self.is_shield_ready and not self.is_shielding:
            self.is_shielding = True
            self.is_shield_ready = False
            self.hit_counter = 0
            self.state = 'shield'
            self.ai_state = 'shield'
            self.animator.reset_animation()
            self.physics.velocity_x = 0
            print(f"[SKELETON] RAISING SHIELD!")
            return
        
        # Handle shield state
        if self.is_shielding:
            self.physics.velocity_x = 0
            if self.animator.is_animation_finished():
                self.is_shielding = False
                self.shield_cooldown = self.SHIELD_COOLDOWN
                self.state = 'idle'
                self.ai_state = self.STATE_IDLE
                print(f"[SKELETON] Shield lowered, cooldown active")
            return
        
        distance = self.get_distance_to_player()
        direction = self.get_direction_to_player()
        self.facing_right = direction > 0
        
        # === HANDLE ONGOING BONE THROW ===
        
        # DISABLED: Bone throw logic - focus on basic actions first
        # === HANDLE ONGOING BONE THROW ===
        # if self.is_throwing:
        #     if not self.bone_thrown and self.animator.frame_index >= 6:
        #         self._throw_bone()
        #         self.bone_thrown = True
        #     
        #     if self.animator.is_animation_finished():
        #         self.is_throwing = False
        #         self.bone_thrown = False
        #         self.bone_cooldown = self.BONE_COOLDOWN
        #         self.bone_count += 1
        #         
        #         if self.bone_count >= self.max_bones:
        #             self.force_melee = True
        #     
        #     self.physics.velocity_x = 0
        #     return
        
        # === STATE MACHINE ===
        
        if distance > self.lose_interest_range:
            self.ai_state = self.STATE_IDLE
            self.force_melee = False
            self.bone_count = 0
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
                self.bone_count = 0
            self.physics.velocity_x = 0
            return
        
        if self.force_melee:
            self.ai_state = self.STATE_CHASE
            self.physics.velocity_x = direction * self.movement_speed
            return
        
        # DISABLED: Bone throw trigger
        # if (distance < self.bone_range and 
        #     self.bone_cooldown <= 0 and 
        #     self.bone_count < self.max_bones):
        #     self.is_throwing = True
        #     self.bone_thrown = False
        #     self.animator.reset_animation()
        #     self.physics.velocity_x = 0
        #     return
        
        self.ai_state = self.STATE_CHASE
        self.physics.velocity_x = direction * self.movement_speed
    
    def _throw_bone(self):
        direction = self.get_direction_to_player()
        
        spawn_x = self.rect.centerx + (direction * 25)
        spawn_y = self.rect.centery - 10
        
        pm = ProjectileManager.get_instance()
        pm.spawn_projectile(
            x=spawn_x,
            y=spawn_y,
            direction=direction,
            speed=5,
            damage=12,
            sprite_path=SKELETON_PROJECTILE_PATH,
            scale=2.0,
            max_distance=300
        )
        print(f"[SKELETON] Bone thrown! ({self.bone_count + 1}/{self.max_bones})")
    
    def take_damage(self, amount, apply_stun=False):
        # hit counter for shield trigger
        # Damage reduction during shield
        if self.is_shielding:
            reduced = int(amount * self.SHIELD_DAMAGE_REDUCTION)
            print(f"[SKELETON] BLOCKED {amount - reduced} damage with shield!")
            super().take_damage(reduced, apply_stun=apply_stun)
            return
        
        # Interrupt bone throw
        self.is_throwing = False
        self.bone_thrown = False
        
        # Normal damage
        super().take_damage(amount, apply_stun=apply_stun)
        
        # Hit counter for shield trigger (BOD pattern)
        if self.alive:
            self.hit_counter += 1
            print(f"[SKELETON] Hit counter: {self.hit_counter}/{self.SHIELD_TRIGGER_HITS}")
            
            if self.hit_counter >= self.SHIELD_TRIGGER_HITS and self.shield_cooldown <= 0:
                self.is_shield_ready = True
                print(f"[SKELETON] SHIELD READY!")
