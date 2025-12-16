import pygame as pg
from game.entities.enemies.enemy import BaseEnemy

# Path aset lokal untuk Skullwolf
SKULLWOLF_ASSET_PATH = 'assets/graphics/enemies/dungeon_monster/Skullwolf/'

class Skullwolf(BaseEnemy):
    """
    Enemy Skullwolf - Fast Predator dengan Pack Hunter Behavior.
    
    KARAKTERISTIK:
    - HP: 70 (Medium)
    - Damage: 18 (Medium-High)
    - Speed: 4.5 (Very Fast - Fastest ground enemy)
    - Behavior: Aggressive, fast attacks, hit-and-run tactics
    
    ANIMASI:
    idle(6), attack(9), death(5), hurt(2)
    
    SPECIAL ABILITY:
    - Speed: Fastest ground enemy
    - Pounce Attack: Leap at player
    - Hit-and-Run: Attack then retreat quickly
    """
    
    # AI CONSTANTS
    POUNCE_RANGE = 150       # Distance to start pounce
    RETREAT_DISTANCE = 100   # Retreat after attack
    ATTACK_COOLDOWN = 60     # Fast attacks
    
    def __init__(self, x, y):
        """Initialize Skullwolf at position (x, y)."""
        super().__init__(
            x=x, y=y,
            width=48, height=48,
            max_hp=70,
            attack_power=18,
            speed=4.5,
            asset_path=SKULLWOLF_ASSET_PATH,
            scale=2.0
        )
        
        # Combat ranges
        self.detection_range = 450
        self.attack_range = 60
        self.lose_interest_range = 600
        
        # Hit-and-run mechanics
        self.attack_cooldown = 0
        self.is_retreating = False
        self.retreat_counter = 0
        self.pounce_speed = self.movement_speed * 1.8  # Use movement_speed instead of speed
        
        self._setup_animations()
    
    def _setup_animations(self):
        """Load animasi Skullwolf."""
        animation_mapping = {
            'idle': 'idle',
            'walk': 'idle',  # No walk, use idle
            'chase': 'idle',  # Running uses idle (fast)
            'attack': 'attack',
            'hurt': 'hurt',
            'die': 'death',
        }
        self.animator.load_sprites(animation_mapping)
        self.animator.animation_speed = 0.14  # Fast animation
    
    def update(self, platforms):
        """Update dengan hit-and-run behavior."""
        # Cooldown
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        
        # Retreat counter
        if self.retreat_counter > 0:
            self.retreat_counter -= 1
            if self.retreat_counter == 0:
                self.is_retreating = False
        
        super().update(platforms)
    
    def _update_ai(self):
        """
        IMPROVED AI: Hit-and-run predator behavior.
        """
        if not self.alive or not self.player_ref:
            return
        
        # Handle retreat phase
        if self.is_retreating:
            # Run away from player
            direction = -self.get_direction_to_player()
            self.facing_right = self.get_direction_to_player() > 0  # Still face player
            self.physics.velocity_x = direction * self.pounce_speed
            return
        
        distance = self.get_distance_to_player()
        
        # STATE MACHINE - Aggressive predator
        if distance > self.lose_interest_range:
            # Lost prey - patrol
            self.ai_state = self.STATE_PATROL
            self.physics.velocity_x = self.do_patrol()
            
        elif distance > self.detection_range:
            # Idle, waiting
            self.ai_state = self.STATE_IDLE
            self.physics.velocity_x = 0
            
        elif distance <= self.attack_range and self.attack_cooldown <= 0:
            # POUNCE ATTACK!
            self.ai_state = self.STATE_ATTACK
            self.do_attack()
            self.attack_cooldown = self.ATTACK_COOLDOWN
            self.physics.velocity_x = 0
            
            # After attack, retreat
            self.is_retreating = True
            self.retreat_counter = 30  # Retreat for 30 frames
            
        elif distance <= self.POUNCE_RANGE:
            # In pounce range - RUSH!
            self.ai_state = 'pounce'
            direction = self.get_direction_to_player()
            self.facing_right = direction > 0
            self.physics.velocity_x = direction * self.pounce_speed
            
        else:
            # Chase quickly
            self.ai_state = self.STATE_CHASE
            self.physics.velocity_x = self.do_chase()
    
    def do_attack(self):
        """Override attack - pounce attack."""
        super().do_attack()
        print(f"[SKULLWOLF] POUNCES!")
        # Add forward momentum during attack
        direction = self.get_direction_to_player()
        self.physics.velocity_x = direction * self.movement_speed * 1.5
    
    def take_damage(self, amount):
        """Override take damage - agile, can dodge."""
        super().take_damage(amount)
        if self.alive:
            # Quick retreat after taking damage
            self.is_retreating = True
            self.retreat_counter = 20
