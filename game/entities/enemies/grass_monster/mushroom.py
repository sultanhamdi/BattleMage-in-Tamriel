import pygame as pg
from game.entities.enemies.enemy import BaseEnemy

# Path aset lokal untuk Mushroom
MUSHROOM_ASSET_PATH = 'assets/graphics/enemies/grass_monster/Mushroom/'

class Mushroom(BaseEnemy):
    """
    Enemy Mushroom - Tanky Melee Fighter dengan Poison.
    
    KARAKTERISTIK:
    - HP: 80 (High - Tanky)
    - Damage: 10 (Low tapi bisa poison)
    - Speed: 2.0 (Slow)
    - Behavior: Defensive, patient, sustain fighter
    
    ANIMASI:
    idle(4), run(8), attack(8), attack2(8), range(11), take_hit(4), death(4)
    
    SPECIAL ABILITY:
    - High HP: Can tank many hits
    - Poison Cloud: Range attack releases spores
    - Defensive: Doesn't chase far, guards territory
    """
    
    # AI CONSTANTS
    SPORE_COOLDOWN = 150     # Frames between spore attacks
    TERRITORY_RADIUS = 250   # Doesn't chase beyond this
    
    def __init__(self, x, y):
        """Initialize Mushroom at position (x, y)."""
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
        self.detection_range = 280
        self.attack_range = 55
        self.lose_interest_range = self.TERRITORY_RADIUS  # Stay in territory
        
        # Spore system
        self.spore_cooldown = 0
        self.is_spore_attacking = False
        
        self._setup_animations()
    
    def _setup_animations(self):
        """Load animasi Mushroom."""
        animation_mapping = {
            'idle': 'idle',
            'walk': 'run',
            'chase': 'run',
            'attack': 'attack',
            'range': 'range',  # Spore attack
            'hurt': 'take_hit',
            'die': 'death',
        }
        self.animator.load_sprites(animation_mapping)
        self.animator.animation_speed = 0.10  # Slow animation
    
    def update(self, platforms):
        """Update dengan territorial behavior."""
        # Cooldown
        if self.spore_cooldown > 0:
            self.spore_cooldown -= 1
        
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
        IMPROVED AI: Defensive territorial behavior.
        Returns: x_velocity
        """
        if not self.alive or not self.player_ref:
            self.state = 'idle'
            return 0
        
        # Handle hurt state
        if self.ai_state == self.STATE_HURT or self.state == 'hurt':
            return 0  # Don't move when hurt
        
        # Handle spore attack
        if self.is_spore_attacking:
            self.state = 'range'
            # Stay still and face player during spore attack
            direction = self.get_direction_to_player()
            self.facing_right = direction > 0
            
            if self.animator.is_animation_finished():
                self.release_spores()
                self.spore_cooldown = self.SPORE_COOLDOWN
                self.is_spore_attacking = False
                self.ai_state = self.STATE_IDLE
            return 0
        
        distance = self.get_distance_to_player()
        dist_from_spawn = abs(self.rect.x - self.spawn_x)
        direction = self.get_direction_to_player()
        
        # STATE MACHINE - Territorial
        if dist_from_spawn > self.TERRITORY_RADIUS:
            # Too far from territory - return to spawn
            self.ai_state = 'return'
            self.state = 'walk'
            if self.rect.x > self.spawn_x:
                self.facing_right = False
                x_velocity = -self.movement_speed
            else:
                self.facing_right = True
                x_velocity = self.movement_speed
                
        elif distance > self.detection_range:
            # Not detected - idle or patrol in territory
            self.ai_state = self.STATE_IDLE
            self.state = 'idle'
            x_velocity = 0
            
        elif distance <= self.attack_range:
            # Melee attack
            self.ai_state = self.STATE_ATTACK
            self.facing_right = direction > 0
            self.do_attack()
            x_velocity = 0
            
        elif 50 < distance <= 150 and self.spore_cooldown <= 0:
            # Medium range - spore attack
            self.ai_state = 'spore'
            self.state = 'range'
            self.is_spore_attacking = True
            self.facing_right = direction > 0
            self.animator.reset_animation()
            x_velocity = 0
            
        elif distance < self.TERRITORY_RADIUS:
            # Chase slowly within territory
            self.ai_state = self.STATE_CHASE
            self.state = 'chase'
            self.facing_right = direction > 0
            x_velocity = direction * self.movement_speed
            
        else:
            # Too far - let them go
            self.ai_state = self.STATE_IDLE
            self.state = 'idle'
            x_velocity = 0
        
        return x_velocity
    
    def release_spores(self):
        """Release poison spores."""
        print(f"[MUSHROOM] Releases spores!")
        # TODO: Implement dengan projectile/effect system
    
    def take_damage(self, amount):
        """Override take damage - tanky, less affected."""
        # Reduce damage slightly due to thick skin
        reduced_damage = amount * 0.85
        super().take_damage(int(reduced_damage))
