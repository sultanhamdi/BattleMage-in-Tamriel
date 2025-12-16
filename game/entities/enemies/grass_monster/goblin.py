import pygame as pg
from game.entities.enemies.enemy import BaseEnemy

# Path aset lokal untuk Goblin
GOBLIN_ASSET_PATH = 'assets/graphics/enemies/grass_monster/Goblin/'

class Goblin(BaseEnemy):
    """
    Enemy Goblin - Versatile Fighter dengan Melee & Range Attack.
    
    KARAKTERISTIK:
    - HP: 60 (Menengah)
    - Damage: 15 (Melee), 10 (Range)
    - Speed: 3.5 (Agile)
    - Behavior: Aggressive, switch antara melee dan range based on distance
    
    ANIMASI:
    idle(4), run(8), attack(8), attack2(8), range(12), take_hit(4), death(4)
    
    SPECIAL ABILITY:
    - Range Attack: Melempar projectile jika player jauh
    - Tactical: Mundur jika terlalu dekat, maju jika terlalu jauh
    - Smart Positioning: Maintain optimal attack distance
    """
    
    # AI CONSTANTS
    OPTIMAL_RANGE = 180      # Jarak ideal untuk range attack
    MIN_SAFE_DISTANCE = 60   # Jarak minimum sebelum mundur
    PROJECTILE_COOLDOWN = 100  # Frames antara projectile
    
    def __init__(self, x, y):
        """Initialize Goblin at position (x, y)."""
        # Base stats
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
        
        # Projectile system
        self.projectile_cooldown = 0
        self.is_range_attacking = False
        
        # Tactical behavior
        self.retreat_distance = 0  # Counter untuk mundur
        
        self._setup_animations()
    
    def _setup_animations(self):
        """Load animasi Goblin."""
        animation_mapping = {
            'idle': 'idle',
            'walk': 'run',
            'chase': 'run',
            'attack': 'attack',
            'range': 'range',
            'hurt': 'take_hit',
            'die': 'death',
        }
        self.animator.load_sprites(animation_mapping)
        self.animator.animation_speed = 0.12  # Slightly faster
    
    def update(self, platforms):
        """Update dengan tactical behavior."""
        # Cooldown management
        if self.projectile_cooldown > 0:
            self.projectile_cooldown -= 1
        
        # Update timers
        self.update_timers()
        
        if not self.alive:
            self.physics.update(platforms, 0, apply_gravity=True)
            self.rect = self.physics.rect  # Sync rect
            return
        
        # Update AI state
        self.update_ai_state()
        
        # Execute AI behavior
        x_velocity = self.execute_ai_behavior()
        
        # Update physics with gravity
        self.physics.update(platforms, x_velocity, apply_gravity=True)
        
        # CRITICAL: Sync rect with physics.rect
        self.rect = self.physics.rect
    
    def execute_ai_behavior(self):
        """
        IMPROVED AI: Tactical positioning dan smart attack switching.
        Returns: x_velocity
        """
        if not self.alive or not self.player_ref:
            self.state = 'idle'
            return 0
        
        # Handle hurt state
        if self.ai_state == self.STATE_HURT or self.state == 'hurt':
            return 0  # Don't move when hurt
        
        # Handle range attack animation
        if self.is_range_attacking:
            self.state = 'range'
            # Stay still and face player during attack
            direction = self.get_direction_to_player()
            self.facing_right = direction > 0
            
            if self.animator.is_animation_finished():
                self.shoot_projectile()
                self.projectile_cooldown = self.PROJECTILE_COOLDOWN
                self.is_range_attacking = False
                self.ai_state = self.STATE_CHASE
            return 0
        
        distance = self.get_distance_to_player()
        direction = self.get_direction_to_player()
        
        # STATE MACHINE dengan tactical positioning
        if distance > self.lose_interest_range:
            # Too far - return to patrol
            self.ai_state = self.STATE_PATROL
            self.state = 'walk'
            x_velocity = self.do_patrol()
            
        elif distance > self.detection_range:
            # Not detected yet - idle
            self.ai_state = self.STATE_IDLE
            self.state = 'idle'
            x_velocity = 0
            
        elif distance < self.MIN_SAFE_DISTANCE:
            # TOO CLOSE - retreat!
            self.ai_state = 'retreat'
            self.state = 'walk'
            retreat_dir = -direction  # Opposite direction from player
            self.facing_right = direction > 0  # Still face player while retreating
            x_velocity = retreat_dir * self.movement_speed * 1.2  # Faster retreat
            
        elif distance <= self.attack_range:
            # In melee range - melee attack
            self.ai_state = self.STATE_ATTACK
            self.facing_right = direction > 0
            self.do_attack()
            x_velocity = 0
            
        elif self.OPTIMAL_RANGE - 50 < distance < self.range_attack_range:
            # In optimal range - try range attack
            if self.projectile_cooldown <= 0:
                self.ai_state = 'range'
                self.state = 'range'
                self.is_range_attacking = True
                self.facing_right = direction > 0
                self.animator.reset_animation()
                x_velocity = 0
            else:
                # Cooldown - maintain distance
                self.ai_state = self.STATE_CHASE
                self.state = 'chase'
                target_dist = self.OPTIMAL_RANGE
                if distance < target_dist:
                    # Too close, back off slightly
                    move_dir = -direction
                else:
                    # Too far, advance
                    move_dir = direction
                self.facing_right = direction > 0
                x_velocity = move_dir * self.movement_speed * 0.7
        else:
            # Chase to optimal range
            self.ai_state = self.STATE_CHASE
            self.state = 'chase'
            self.facing_right = direction > 0
            x_velocity = direction * self.movement_speed
        
        return x_velocity
    
    def shoot_projectile(self):
        """
        Shoot projectile ke arah player.
        TODO: Implement dengan projectile system nanti.
        """
        print(f"[GOBLIN] Shoots projectile!")
        # Placeholder - nanti implement dengan projectile manager
    
    def take_damage(self, amount):
        """Override take damage - bisa dodge/retreat."""
        super().take_damage(amount)
        if self.alive:
            # Setelah kena hit, mundur sedikit
            self.retreat_distance = 30
