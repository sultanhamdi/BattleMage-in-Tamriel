import pygame as pg
from game.entities.enemies.enemy import BaseEnemy
from game.utils.projectile import ProjectileManager

# Path aset lokal untuk Goblin
GOBLIN_ASSET_PATH = 'assets/graphics/enemies/grass_monster/Goblin/'
GOBLIN_PROJECTILE_PATH = 'assets/graphics/enemies/grass_monster/Goblin/projectile/'

class Goblin(BaseEnemy):
    """
    Enemy Goblin - Versatile Fighter dengan Melee & Range Attack.
    
    BEHAVIOR PATTERN:
    1. Detect player -> Chase
    2. In range -> Start 'range' animation
    3. When animation done -> Fire projectile
    4. After 2 range attacks -> Chase for melee
    5. Melee attack -> Reset counters
    """
    
    # AI CONSTANTS
    PROJECTILE_COOLDOWN = 600  # 10 seconds at 60fps
    
    def __init__(self, x, y):
        super().__init__(
            x=x, y=y,
            width=40, height=50,
            max_hp=60,
            attack_power=15,
            speed=3.5,
            asset_path=GOBLIN_ASSET_PATH,
            scale=1.8
        )
        
        # Combat ranges
        self.detection_range = 350
        self.attack_range = 55
        self.range_attack_range = 280
        self.lose_interest_range = 450
        
        # Projectile system
        self.projectile_cooldown = 0
        self.range_attack_count = 0
        self.max_range_attacks = 2
        self.force_melee = False
        
        # Range attack STATE
        self.is_range_attacking = False  # True when playing range animation
        self.projectile_fired = False    # True after projectile fired this attack
        
        self._setup_animations()
    
    def _setup_animations(self):
        """Load animasi Goblin."""
        animation_mapping = {
            'idle': 'idle',
            'walk': 'run',
            'attack': 'attack',
            'range': 'range',   # <-- Range animation for projectile throw
            'hurt': 'take_hit',
            'die': 'death',
        }
        self.animator.load_sprites(animation_mapping)
        self.animator.animation_speed = 0.15
    
    def update(self, platforms):
        """Main update loop."""
        # Cooldown
        if self.projectile_cooldown > 0:
            self.projectile_cooldown -= 1
        
        self.update_timers()
        
        if not self.alive:
            self.physics.update(platforms, 0, apply_gravity=True)
            self.rect = self.physics.rect
            return
        
        x_velocity = self._do_behavior()
        
        self.physics.update(platforms, x_velocity, apply_gravity=True)
        self.rect = self.physics.rect
    
    def _do_behavior(self):
        """AI State Machine."""
        if not self.player_ref:
            self.state = 'idle'
            return 0
        
        distance = self.get_distance_to_player()
        direction = self.get_direction_to_player()
        self.facing_right = direction > 0
        
        # === HANDLE ONGOING RANGE ATTACK ===
        # If currently in range attack animation, wait for it to finish
        if self.is_range_attacking:
            self.state = 'range'
            
            # Fire projectile at mid-point of animation (frame 6+)
            if not self.projectile_fired and self.animator.current_frame >= 6:
                self._fire_projectile()
                self.projectile_fired = True
            
            # Animation finished - end range attack
            if self.animator.is_animation_finished():
                self.is_range_attacking = False
                self.projectile_fired = False
                self.projectile_cooldown = self.PROJECTILE_COOLDOWN
                self.range_attack_count += 1
                
                # Check if must go melee
                if self.range_attack_count >= self.max_range_attacks:
                    self.force_melee = True
                    print(f"[GOBLIN] Max range ({self.max_range_attacks})! Must melee now.")
            
            return 0  # Don't move during range attack
        
        # === NORMAL STATE MACHINE ===
        
        # Too far - lose interest
        if distance > self.lose_interest_range:
            self.state = 'idle'
            self.force_melee = False
            self.range_attack_count = 0
            return 0
        
        # Not detected yet
        if distance > self.detection_range:
            self.state = 'idle'
            return 0
        
        # In melee range - attack
        if distance <= self.attack_range:
            self.state = 'attack'
            self.do_attack()
            # Reset after melee
            self.force_melee = False
            self.range_attack_count = 0
            return 0
        
        # Forced to go melee
        if self.force_melee:
            self.state = 'walk'
            return direction * self.movement_speed
        
        # Can start range attack?
        if (distance < self.range_attack_range and 
            self.projectile_cooldown <= 0 and 
            self.range_attack_count < self.max_range_attacks):
            # START range attack animation
            self.is_range_attacking = True
            self.projectile_fired = False
            self.state = 'range'
            self.animator.reset_animation()
            print(f"[GOBLIN] Starting range attack...")
            return 0
        
        # Default - chase
        self.state = 'walk'
        return direction * self.movement_speed
    
    def _fire_projectile(self):
        """Fire projectile during range animation."""
        direction = self.get_direction_to_player()
        
        spawn_x = self.rect.centerx + (direction * 25)
        spawn_y = self.rect.centery
        
        pm = ProjectileManager.get_instance()
        pm.spawn_projectile(
            x=spawn_x,
            y=spawn_y,
            direction=direction,
            speed=6,
            damage=10,
            sprite_path=GOBLIN_PROJECTILE_PATH,
            scale=2.0,
            max_distance=350
        )
        print(f"[GOBLIN] Projectile fired! ({self.range_attack_count + 1}/{self.max_range_attacks})")
    
    def take_damage(self, amount):
        """Override - interrupt range attack if hit."""
        self.is_range_attacking = False
        self.projectile_fired = False
        super().take_damage(amount)
