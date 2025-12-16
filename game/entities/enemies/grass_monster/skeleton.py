import pygame as pg
from game.entities.enemies.enemy import BaseEnemy

# Path aset lokal untuk Skeleton
SKELETON_ASSET_PATH = 'assets/graphics/enemies/grass_monster/Skeleton/'

class Skeleton(BaseEnemy):
    """
    Enemy Skeleton - Balanced Fighter dengan Shield Defense.
    
    KARAKTERISTIK:
    - HP: 65 (Medium)
    - Damage: 14 (Medium)
    - Speed: 2.8 (Medium)
    - Behavior: Defensive, can block attacks with shield
    
    ANIMASI:
    idle(4), walk(9), attack(18), attack2(15), range(13), shield(4), take_hit(4), death(15)
    
    SPECIAL ABILITY:
    - Shield: Can block attacks (reduce damage)
    - Range Attack: Throws bone projectile
    - Defensive Stance: Raise shield when low HP
    """
    
    # AI CONSTANTS
    SHIELD_HP_THRESHOLD = 0.3  # Raise shield when HP < 30%
    SHIELD_BLOCK_CHANCE = 0.6  # 60% chance to block when shielded
    BONE_THROW_COOLDOWN = 120
    
    def __init__(self, x, y):
        """Initialize Skeleton at position (x, y)."""
        super().__init__(
            x=x, y=y,
            width=40, height=52,
            max_hp=65,
            attack_power=14,
            speed=2.8,
            asset_path=SKELETON_ASSET_PATH,
            scale=1.8
        )
        
        # Combat ranges
        self.detection_range = 320
        self.attack_range = 55
        self.range_attack_range = 260
        
        # Shield system
        self.is_shielding = False
        self.shield_active = False
        
        # Projectile system
        self.bone_cooldown = 0
        self.is_throwing = False
        
        self._setup_animations()
    
    def _setup_animations(self):
        """Load animasi Skeleton."""
        animation_mapping = {
            'idle': 'idle',
            'walk': 'walk',
            'chase': 'walk',
            'attack': 'attack',
            'range': 'range',
            'shield': 'shield',
            'hurt': 'take_hit',
            'die': 'death',
        }
        self.animator.load_sprites(animation_mapping)
        self.animator.animation_speed = 0.11
    
    def update(self, platforms):
        """Update dengan shield behavior."""
        # Cooldown
        if self.bone_cooldown > 0:
            self.bone_cooldown -= 1
        
        # Check if should shield (low HP)
        hp_ratio = self.current_hp / self.max_hp
        self.should_shield = hp_ratio < self.SHIELD_HP_THRESHOLD
        
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
        IMPROVED AI: Defensive dengan shield behavior.
        Returns: x_velocity
        """
        if not self.alive or not self.player_ref:
            self.state = 'idle'
            return 0
        
        # Handle hurt state
        if self.ai_state == self.STATE_HURT or self.state == 'hurt':
            return 0  # Don't move when hurt
        
        # Get direction to player for proper facing
        direction = self.get_direction_to_player()
        
        # Handle shield animation
        if self.is_shielding:
            self.state = 'shield'
            self.shield_active = True
            self.facing_right = direction > 0  # Face player while shielding
            
            # Hold shield for a moment
            if self.animator.current_frame >= 2:  # Shield raised
                # After holding, decide next action
                if self.animator.is_animation_finished():
                    self.is_shielding = False
                    self.shield_active = False
                    self.ai_state = self.STATE_CHASE
            return 0
        
        # Handle range attack
        if self.is_throwing:
            self.state = 'range'
            self.facing_right = direction > 0  # Face player while throwing
            
            if self.animator.is_animation_finished():
                self.throw_bone()
                self.bone_cooldown = self.BONE_THROW_COOLDOWN
                self.is_throwing = False
                self.ai_state = self.STATE_CHASE
            return 0
        
        distance = self.get_distance_to_player()
        
        # STATE MACHINE
        if distance > self.lose_interest_range:
            # Too far - patrol
            self.ai_state = self.STATE_PATROL
            self.state = 'walk'
            self.shield_active = False
            x_velocity = self.do_patrol()
            
        elif distance > self.detection_range:
            # Idle
            self.ai_state = self.STATE_IDLE
            self.state = 'idle'
            self.shield_active = False
            x_velocity = 0
            
        elif distance <= self.attack_range:
            # Melee attack or shield
            if self.should_shield and not self.is_attacking:
                # Low HP - raise shield instead
                self.ai_state = 'shield'
                self.state = 'shield'
                self.is_shielding = True
                self.facing_right = direction > 0
                self.animator.reset_animation()
                x_velocity = 0
            else:
                # Normal attack
                self.ai_state = self.STATE_ATTACK
                self.facing_right = direction > 0
                self.do_attack()
                self.shield_active = False
                x_velocity = 0
            
        elif 80 < distance <= self.range_attack_range and self.bone_cooldown <= 0:
            # Range attack
            self.ai_state = 'range'
            self.state = 'range'
            self.is_throwing = True
            self.facing_right = direction > 0
            self.animator.reset_animation()
            self.shield_active = False
            x_velocity = 0
            
        else:
            # Chase
            self.ai_state = self.STATE_CHASE
            self.state = 'chase'
            self.facing_right = direction > 0
            self.shield_active = False
            x_velocity = direction * self.movement_speed
        
        return x_velocity
    
    def throw_bone(self):
        """Throw bone projectile."""
        print(f"[SKELETON] Throws bone!")
        # TODO: Implement dengan projectile system
    
    def take_damage(self, amount):
        """Override take damage - can block with shield."""
        if self.shield_active:
            # Chance to block
            import random
            if random.random() < self.SHIELD_BLOCK_CHANCE:
                print(f"[SKELETON] Blocked attack with shield!")
                # Reduce damage significantly
                amount = int(amount * 0.3)
        
        super().take_damage(amount)
