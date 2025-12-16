import pygame as pg
import math
from game.entities.enemies.enemy import BaseEnemy

# Path aset lokal untuk Flying Eye
FLYING_EYE_ASSET_PATH = 'assets/graphics/enemies/grass_monster/Flying eye/'

class FlyingEye(BaseEnemy):
    """
    Enemy Flying Eye - Agile Flying Enemy dengan Range Attack.
    
    KARAKTERISTIK:
    - HP: 45 (Low)
    - Damage: 12 (Range), 8 (Melee)
    - Speed: 4.0 (Very Fast - Flying)
    - Behavior: Evasive, prefer range attack, hover pattern
    
    ANIMASI:
    flight(8), attack(8), attack2(8), range(6), take_hit(4), death(4)
    
    SPECIAL ABILITY:
    - Flying: Ignores gravity, can move vertically
    - Hover Pattern: Sinusoidal up-down movement
    - Range Attack: Shoots projectiles from distance
    - Evasive: Dodges by flying up/down
    """
    
    # AI CONSTANTS
    HOVER_AMPLITUDE = 15     # Pixels naik-turun (reduced for smoother motion)
    HOVER_FREQUENCY = 0.08   # Kecepatan hover (increased for visible motion)
    OPTIMAL_HEIGHT_OFFSET = -40  # Fly slightly above player
    VERTICAL_SPEED = 2.0     # Vertical movement speed (smoother)
    
    def __init__(self, x, y):
        """Initialize Flying Eye at position (x, y)."""
        super().__init__(
            x=x, y=y,
            width=35, height=35,
            max_hp=45,
            attack_power=12,
            speed=4.0,
            asset_path=FLYING_EYE_ASSET_PATH,
            scale=1.8
        )
        
        # Combat ranges
        self.detection_range = 400
        self.attack_range = 50
        self.range_attack_range = 320
        
        # Flying behavior
        self.can_fly = True
        self.hover_offset = 0
        self.target_y = y
        
        # Projectile system
        self.projectile_cooldown = 0
        self.projectile_cooldown_max = 80
        self.is_range_attacking = False
        
        self._setup_animations()
    
    def _setup_animations(self):
        """Load animasi Flying Eye."""
        animation_mapping = {
            'idle': 'flight',
            'walk': 'flight',
            'chase': 'flight',
            'attack': 'attack',
            'range': 'range',
            'hurt': 'take_hit',
            'die': 'death',
        }
        self.animator.load_sprites(animation_mapping)
        self.animator.animation_speed = 0.13
    
    def update(self, platforms):
        """Override update - Flying enemy with NO GRAVITY."""
        # Update hover animation continuously for smooth motion
        self.hover_offset += self.HOVER_FREQUENCY
        
        # Cooldown
        if self.projectile_cooldown > 0:
            self.projectile_cooldown -= 1
        
        # Update timers
        self.update_timers()
        
        if not self.alive:
            # When dead, fall with gravity
            self.physics.update(platforms, 0, apply_gravity=True)
            self.rect = self.physics.rect  # Sync rect
            return
        
        # Update AI state
        self.update_ai_state()
        
        # Execute AI behavior and get velocity
        x_velocity = self.execute_ai_behavior()
        
        # Update physics WITHOUT GRAVITY
        self.physics.update(platforms, x_velocity, apply_gravity=False)
        
        # CRITICAL: Sync rect with physics.rect
        self.rect = self.physics.rect
    
    def execute_ai_behavior(self):
        """
        Override execute_ai_behavior untuk flying enemy dengan vertical movement.
        Returns: x_velocity
        """
        if not self.alive or not self.player_ref:
            self.physics.velocity_y = 0
            self.state = 'idle'
            return 0
        
        # Handle hurt state
        if self.ai_state == self.STATE_HURT or self.state == 'hurt':
            # Slight hover during hurt
            hover_y = math.sin(self.hover_offset) * self.HOVER_AMPLITUDE * 0.3
            self.physics.velocity_y = hover_y * 0.1
            return 0  # Don't move horizontally when hurt
        
        # Handle range attack
        if self.is_range_attacking:
            self.state = 'range'
            # Still hover during attack
            hover_y = math.sin(self.hover_offset) * self.HOVER_AMPLITUDE * 0.5
            self.physics.velocity_y = hover_y * 0.15
            
            if self.animator.is_animation_finished():
                self.shoot_projectile()
                self.projectile_cooldown = self.projectile_cooldown_max
                self.is_range_attacking = False
                self.ai_state = self.STATE_CHASE
            return 0
        
        distance = self.get_distance_to_player()
        direction = self.get_direction_to_player()
        
        # Calculate target height (above player)
        if self.player_ref:
            target_height = self.player_ref.rect.centery + self.OPTIMAL_HEIGHT_OFFSET
        else:
            target_height = self.rect.centery
        
        # Calculate hover offset for natural floating
        hover_y_offset = math.sin(self.hover_offset) * self.HOVER_AMPLITUDE
        
        # Initialize x_velocity
        x_velocity = 0
        
        # STATE MACHINE with vertical movement
        if distance > self.lose_interest_range:
            # Too far - patrol with hover
            self.ai_state = self.STATE_PATROL
            self.state = 'walk'
            x_velocity = self.do_patrol()
            # Natural hovering during patrol
            self.physics.velocity_y = hover_y_offset * 0.2
            
        elif distance > self.detection_range:
            # Idle with gentle hover
            self.ai_state = self.STATE_IDLE
            self.state = 'idle'
            x_velocity = 0
            self.physics.velocity_y = hover_y_offset * 0.25
            
        elif distance <= self.attack_range:
            # Melee attack - stay stable
            self.ai_state = self.STATE_ATTACK
            self.facing_right = direction > 0
            self.do_attack()
            x_velocity = 0
            # Slight hover even during attack
            self.physics.velocity_y = hover_y_offset * 0.1
            
        elif distance <= self.range_attack_range and self.projectile_cooldown <= 0:
            # Range attack
            self.ai_state = 'range'
            self.state = 'range'
            self.is_range_attacking = True
            self.facing_right = direction > 0
            self.animator.reset_animation()
            x_velocity = 0
            self.physics.velocity_y = hover_y_offset * 0.15
            
        else:
            # Chase with vertical movement to maintain height
            self.ai_state = self.STATE_CHASE
            self.state = 'chase'
            
            # Horizontal movement with direction update
            self.facing_right = direction > 0
            x_velocity = direction * self.movement_speed
            
            # Vertical movement - smooth approach to target height
            current_y = self.rect.centery
            height_diff = target_height - current_y
            
            if abs(height_diff) > 30:
                # Need to adjust height significantly
                if height_diff > 0:
                    # Need to go down
                    vertical_move = min(self.VERTICAL_SPEED, abs(height_diff) * 0.1)
                    self.physics.velocity_y = vertical_move
                else:
                    # Need to go up
                    vertical_move = min(self.VERTICAL_SPEED, abs(height_diff) * 0.1)
                    self.physics.velocity_y = -vertical_move
            else:
                # At target height - add natural hover
                self.physics.velocity_y = hover_y_offset * 0.2
        
        return x_velocity
    
    def shoot_projectile(self):
        """Shoot projectile."""
        print(f"[FLYING EYE] Shoots projectile!")
        # TODO: Implement dengan projectile system
