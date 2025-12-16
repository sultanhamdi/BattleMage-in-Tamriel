import pygame as pg
from game.entities.enemies.enemy import BaseEnemy
from game.utils.projectile import ProjectileManager

# Path aset
MUSHROOM_ASSET_PATH = 'assets/graphics/enemies/grass_monster/Mushroom/'
MUSHROOM_PROJECTILE_PATH = 'assets/graphics/enemies/grass_monster/Mushroom/projectile/'

class Mushroom(BaseEnemy):
    """
    Enemy Mushroom - Territorial defender with spore attacks.
    
    BEHAVIOR:
    - Stays near spawn (territorial)
    - 2 spore attacks then must melee
    - Fires spore during 'range' animation
    """
    
    TERRITORY_RADIUS = 200
    SPORE_COOLDOWN = 600  # 10 seconds at 60fps
    
    def __init__(self, x, y):
        super().__init__(
            x=x, y=y,
            width=42, height=50,
            max_hp=80,
            attack_power=10,
            speed=2.0,
            asset_path=MUSHROOM_ASSET_PATH,
            scale=1.8
        )
        
        # Combat ranges
        self.detection_range = 250
        self.attack_range = 55
        self.spore_range = 150
        
        # Spore system
        self.spore_cooldown = 0
        self.spore_count = 0
        self.max_spores = 2
        self.force_melee = False
        
        # Spore attack state
        self.is_spore_attacking = False
        self.spore_fired = False
        
        self._setup_animations()
    
    def _setup_animations(self):
        animation_mapping = {
            'idle': 'idle',
            'walk': 'run',
            'attack': 'attack',
            'range': 'range',
            'hurt': 'take_hit',
            'die': 'death',
        }
        self.animator.load_sprites(animation_mapping)
        self.animator.animation_speed = 0.12
    
    def update(self, platforms):
        if self.spore_cooldown > 0:
            self.spore_cooldown -= 1
        
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
        dist_from_spawn = abs(self.rect.x - self.spawn_x)
        direction = self.get_direction_to_player()
        self.facing_right = direction > 0
        
        # === HANDLE ONGOING SPORE ATTACK ===
        if self.is_spore_attacking:
            self.state = 'range'
            
            if not self.spore_fired and self.animator.current_frame >= 5:
                self._fire_spore()
                self.spore_fired = True
            
            if self.animator.is_animation_finished():
                self.is_spore_attacking = False
                self.spore_fired = False
                self.spore_cooldown = self.SPORE_COOLDOWN
                self.spore_count += 1
                
                if self.spore_count >= self.max_spores:
                    self.force_melee = True
                    print(f"[MUSHROOM] Max spores ({self.max_spores})! Must melee.")
            
            return 0
        
        # === STATE MACHINE ===
        
        # Outside territory - return
        if dist_from_spawn > self.TERRITORY_RADIUS:
            self.state = 'walk'
            self.force_melee = False
            self.spore_count = 0
            return -direction * self.movement_speed
        
        if distance > self.detection_range:
            self.state = 'idle'
            self.force_melee = False
            self.spore_count = 0
            return 0
        
        if distance <= self.attack_range:
            self.state = 'attack'
            self.do_attack()
            self.force_melee = False
            self.spore_count = 0
            return 0
        
        if self.force_melee:
            self.state = 'walk'
            return direction * self.movement_speed
        
        if (distance < self.spore_range and 
            self.spore_cooldown <= 0 and 
            self.spore_count < self.max_spores):
            self.is_spore_attacking = True
            self.spore_fired = False
            self.state = 'range'
            self.animator.reset_animation()
            print(f"[MUSHROOM] Starting spore attack...")
            return 0
        
        # Chase within territory
        if dist_from_spawn < self.TERRITORY_RADIUS:
            self.state = 'walk'
            return direction * self.movement_speed
        
        self.state = 'idle'
        return 0
    
    def _fire_spore(self):
        direction = self.get_direction_to_player()
        
        spawn_x = self.rect.centerx + (direction * 15)
        spawn_y = self.rect.top + 15
        
        pm = ProjectileManager.get_instance()
        pm.spawn_projectile(
            x=spawn_x,
            y=spawn_y,
            direction=direction,
            speed=4,
            damage=8,
            sprite_path=MUSHROOM_PROJECTILE_PATH,
            scale=2.0,
            max_distance=200
        )
        print(f"[MUSHROOM] Spore fired! ({self.spore_count + 1}/{self.max_spores})")
    
    def take_damage(self, amount):
        self.is_spore_attacking = False
        self.spore_fired = False
        super().take_damage(int(amount * 0.85))
