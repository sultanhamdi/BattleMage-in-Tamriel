import pygame as pg
import random
from game.entities.enemies.enemy import BaseEnemy
from game.utils.projectile import ProjectileManager

# Path aset
SKELETON_ASSET_PATH = 'assets/graphics/enemies/grass_monster/Skeleton/'
SKELETON_PROJECTILE_PATH = 'assets/graphics/enemies/grass_monster/Skeleton/projectile/'

class Skeleton(BaseEnemy):
    """
    Enemy Skeleton - Defensive warrior with shield and bone throw.
    
    BEHAVIOR:
    - Can block when HP low
    - 2 bone throws then must melee
    - Throws bone during 'range' animation
    """
    
    BONE_COOLDOWN = 600  # 10 seconds at 60fps
    SHIELD_BLOCK_CHANCE = 0.4
    LOW_HP_THRESHOLD = 0.3
    
    def __init__(self, x, y):
        super().__init__(
            x=x, y=y,
            width=40, height=55,
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
        
        self._setup_animations()
    
    def _setup_animations(self):
        animation_mapping = {
            'idle': 'idle',
            'walk': 'walk',
            'attack': 'attack',
            'range': 'range',
            'shield': 'shield',
            'hurt': 'take_hit',
            'die': 'death',
        }
        self.animator.load_sprites(animation_mapping)
        self.animator.animation_speed = 0.12
    
    @property
    def should_shield(self):
        return self.hp < self.max_hp * self.LOW_HP_THRESHOLD
    
    def update(self, platforms):
        if self.bone_cooldown > 0:
            self.bone_cooldown -= 1
        
        self.update_timers()
        
        if not self.alive:
            self.physics.update(platforms, 0, apply_gravity=True)
            self.rect = self.physics.rect
            return
        
        x_velocity = self._do_behavior()
        
        self.physics.update(platforms, x_velocity, apply_gravity=True)
        self.rect = self.physics.rect
    
    def _do_behavior(self):
        if not self.player_ref:
            self.state = 'idle'
            return 0
        
        distance = self.get_distance_to_player()
        direction = self.get_direction_to_player()
        self.facing_right = direction > 0
        
        # === HANDLE ONGOING BONE THROW ===
        if self.is_throwing:
            self.state = 'range'
            
            if not self.bone_thrown and self.animator.current_frame >= 6:
                self._throw_bone()
                self.bone_thrown = True
            
            if self.animator.is_animation_finished():
                self.is_throwing = False
                self.bone_thrown = False
                self.bone_cooldown = self.BONE_COOLDOWN
                self.bone_count += 1
                
                if self.bone_count >= self.max_bones:
                    self.force_melee = True
                    print(f"[SKELETON] Max bones ({self.max_bones})! Must melee.")
            
            return 0
        
        # === STATE MACHINE ===
        
        if distance > self.lose_interest_range:
            self.state = 'idle'
            self.shield_active = False
            self.force_melee = False
            self.bone_count = 0
            return 0
        
        if distance > self.detection_range:
            self.state = 'idle'
            self.shield_active = False
            return 0
        
        if distance <= self.attack_range:
            if self.should_shield and random.random() < 0.3:
                self.state = 'shield'
                self.shield_active = True
                return 0
            
            self.state = 'attack'
            self.shield_active = False
            self.do_attack()
            self.force_melee = False
            self.bone_count = 0
            return 0
        
        if self.force_melee:
            self.state = 'walk'
            self.shield_active = False
            return direction * self.movement_speed
        
        if (distance < self.bone_range and 
            self.bone_cooldown <= 0 and 
            self.bone_count < self.max_bones):
            self.is_throwing = True
            self.bone_thrown = False
            self.state = 'range'
            self.animator.reset_animation()
            print(f"[SKELETON] Starting bone throw...")
            return 0
        
        self.state = 'walk'
        self.shield_active = False
        return direction * self.movement_speed
    
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
    
    def take_damage(self, amount):
        self.is_throwing = False
        self.bone_thrown = False
        if self.shield_active and random.random() < self.SHIELD_BLOCK_CHANCE:
            print(f"[SKELETON] Blocked!")
            amount = int(amount * 0.3)
        super().take_damage(amount)
