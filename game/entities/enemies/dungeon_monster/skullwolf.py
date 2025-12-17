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
        # Skullwolf uses attack animation for chase/pounce (jumping bite motion)
        # This gives the predator a more aggressive visual while hunting
        animation_mapping = {
            'idle': 'idle',
            'walk': 'attack',    # Use attack sprite (pouncing motion)
            'chase': 'attack',   # Use attack sprite for chasing
            'attack': 'attack',
            'hurt': 'hurt',
            'die': 'death',
        }
        self.animator.load_sprites(animation_mapping)
        self.animator.animation_speed = 0.14  # Fast animation
    
    def update(self, platforms):
        """Override update untuk menggunakan custom AI logic."""
        # 1. Update Timers
        self.update_timers()
        
        # 2. Cooldown
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        
        # 3. Retreat counter
        if self.retreat_counter > 0:
            self.retreat_counter -= 1
            if self.retreat_counter == 0:
                self.is_retreating = False
        
        # 4. Handle hurt state - only during hurt animation, not full invincibility
        # Check if currently in hurt state and animation finished
        if self.state == 'hurt' and self.animator.is_animation_finished():
            # Hurt animation done, can resume AI even if still invincible
            self.state = 'idle'
            self.ai_state = self.STATE_IDLE
        
        # 5. Run AI if not in hurt animation (but can be invincible)
        if self.state != 'hurt' and self.alive:
            # Use custom AI (not parent's update_ai_state/execute_ai_behavior)
            self._update_ai()
            
            # Set visual state based on AI state
            if self.ai_state in [self.STATE_CHASE, 'pounce', self.STATE_PATROL]:
                self.state = 'walk'  # Will use attack animation due to mapping
            elif self.ai_state == self.STATE_ATTACK:
                self.state = 'attack'
            elif self.ai_state == self.STATE_IDLE:
                self.state = 'idle'
        
        # 5. Update Physics
        if self.alive:
            self.physics.update(platforms, self.physics.velocity_x, apply_gravity=self.has_gravity)
        else:
            self.physics.update(platforms, 0, apply_gravity=self.has_gravity)
        
        # 6. Sync rect
        self.rect = self.physics.rect
    
    def _update_ai(self):
        """
        IMPROVED AI: Hit-and-run predator behavior.
        """
        if not self.alive or not self.player_ref:
            return
        
        # Don't change state while attacking - wait for animation to finish
        if self.is_attacking:
            self.physics.velocity_x = 0
            return
        
        # Handle retreat phase
        if self.is_retreating:
            # Run away from player
            direction = -self.get_direction_to_player()
            # Only update facing if X distance is significant (threshold 10px)
            # This prevents rapid flipping when vertically aligned
            dx = self.player_ref.physics.rect.centerx - self.physics.rect.centerx
            if abs(dx) > 10:
                self.facing_right = dx > 0  # Still face player
            
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
            
        elif distance <= self.POUNCE_RANGE:
            # In pounce range - RUSH!
            self.ai_state = 'pounce'
            direction = self.get_direction_to_player()
            # Only update facing if X distance is significant (threshold 10px)
            dx = self.player_ref.physics.rect.centerx - self.physics.rect.centerx
            if abs(dx) > 10:
                self.facing_right = dx < 0  # Sprite default faces LEFT, so invert
            
            self.physics.velocity_x = direction * self.pounce_speed
            
        else:
            # Chase quickly
            self.ai_state = self.STATE_CHASE
            self.physics.velocity_x = self.do_chase()
    
    def do_chase(self):
        """Override chase with correct facing direction."""
        direction = self.get_direction_to_player()
        
        # Only update facing if X distance is significant (threshold 10px)
        # This prevents rapid flipping when vertically aligned
        dx = self.player_ref.physics.rect.centerx - self.physics.rect.centerx
        if abs(dx) > 10:
            # Sprite default faces LEFT, so invert: face left when moving right
            self.facing_right = dx < 0
            
        return direction * self.movement_speed
    
    def do_patrol(self):
        """Override patrol with correct facing direction."""
        # Check patrol bounds
        if self.rect.x > self.spawn_x + self.patrol_distance:
            self.patrol_direction = -1  # Go left
        elif self.rect.x < self.spawn_x - self.patrol_distance:
            self.patrol_direction = 1   # Go right
        
        # Sprite default faces LEFT, so invert: face left when moving right
        self.facing_right = self.patrol_direction < 0
        return self.patrol_direction * self.patrol_speed
    
    def do_attack(self):
        """Override attack - pounce attack."""
        # Guard: only attack if not already attacking
        if self.is_attacking:
            return
            
        super().do_attack()
        print(f"[SKULLWOLF] POUNCES!")
        
        # Add forward momentum during attack
        direction = self.get_direction_to_player()
        self.physics.velocity_x = direction * self.movement_speed * 1.5
        
        # Schedule retreat after attack finishes (handled in update_timers)
        self.is_retreating = True
        self.retreat_counter = 30  # Retreat for 30 frames after attack animation
    
    def take_damage(self, amount):
        """Override take damage - agile, can dodge."""
        super().take_damage(amount)
        if self.alive:
            # Quick retreat after taking damage
            self.is_retreating = True
            self.retreat_counter = 20
