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
    
    def __init__(self, x, y):
        super().__init__(
            x=x, y=y,
            width=35, height=35,
            max_hp=45,
            attack_power=12,
            speed=3.0,
            asset_path=FLYING_EYE_ASSET_PATH,
            scale=1.8
        )
        
        # NO GRAVITY - flying
        self.has_gravity = False
        
        # Combat ranges
        self.detection_range = 400
        self.attack_range = 50
        self.range_attack_range = 320
        self.lose_interest_range = 500
        
        # Hover
        self.hover_offset = 0
        
        # Range attack system
        self.projectile_cooldown = 0
        self.range_attack_count = 0
        self.max_range_attacks = 2
        self.force_melee = False
        
        # Range attack state
        self.is_range_attacking = False
        self.projectile_fired = False
        
        self._setup_animations()
    
    def _setup_animations(self):
        animation_mapping = {
            'idle': 'flight',
            'walk': 'flight',
            'attack': 'attack',
            'range': 'range',
            'hurt': 'take_hit',
            'die': 'death',
        }
        self.animator.load_sprites(animation_mapping)
        self.animator.animation_speed = 0.15
    
    def update(self, platforms):
        if self.projectile_cooldown > 0:
            self.projectile_cooldown -= 1
        
        self.update_timers()
        
        # Hover effect
        self.hover_offset += self.HOVER_FREQUENCY
        hover_y = math.sin(self.hover_offset) * self.HOVER_AMPLITUDE
        
        if not self.alive:
            self.physics.update(platforms, 0, apply_gravity=True)
            self.rect = self.physics.rect
            return
        
        x_velocity = self._do_behavior()
        
        # Apply hover
        self.physics.velocity_y = hover_y * 0.3
        self.physics.update(platforms, x_velocity, apply_gravity=False)
        self.rect = self.physics.rect
    
    def _do_behavior(self):
        if not self.player_ref:
            self.state = 'idle'
            return 0
        
        distance = self.get_distance_to_player()
        direction = self.get_direction_to_player()
        self.facing_right = direction > 0
        
        # === HANDLE ONGOING RANGE ATTACK ===
        if self.is_range_attacking:
            self.state = 'range'
            
            if not self.projectile_fired and self.animator.current_frame >= 5:
                self._fire_projectile()
                self.projectile_fired = True
            
            if self.animator.is_animation_finished():
                self.is_range_attacking = False
                self.projectile_fired = False
                self.projectile_cooldown = self.PROJECTILE_COOLDOWN
                self.range_attack_count += 1
                
                if self.range_attack_count >= self.max_range_attacks:
                    self.force_melee = True
                    print(f"[FLYING EYE] Max range ({self.max_range_attacks})! Must melee.")
            
            return 0
        
        # === STATE MACHINE ===
        
        if distance > self.lose_interest_range:
            self.state = 'idle'
            self.force_melee = False
            self.range_attack_count = 0
            return 0
        
        if distance > self.detection_range:
            self.state = 'idle'
            return 0
        
        if distance <= self.attack_range:
            self.state = 'attack'
            self.do_attack()
            self.force_melee = False
            self.range_attack_count = 0
            return 0
        
        if self.force_melee:
            self.state = 'walk'
            return direction * self.movement_speed
        
        if (distance < self.range_attack_range and 
            self.projectile_cooldown <= 0 and 
            self.range_attack_count < self.max_range_attacks):
            self.is_range_attacking = True
            self.projectile_fired = False
            self.state = 'range'
            self.animator.reset_animation()
            print(f"[FLYING EYE] Starting range attack...")
            return 0
        
        self.state = 'walk'
        return direction * self.movement_speed
    
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
    
    def take_damage(self, amount):
        self.is_range_attacking = False
        self.projectile_fired = False
        super().take_damage(amount)
