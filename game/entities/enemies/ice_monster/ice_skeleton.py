import pygame as pg
from game.entities.enemies.enemy import BaseEnemy

# Path aset lokal untuk Ice Skeleton
ICE_SKELETON_ASSET_PATH = 'assets/graphics/enemies/ice_monster/Skeleton/'

class IceSkeleton(BaseEnemy):
    """
    Enemy Ice Skeleton - Undead Warrior dengan React Ability.
    
    KARAKTERISTIK:
    - HP: 75 (Medium-High)
    - Damage: 18 (Medium-High)
    - Speed: 2.5 (Medium)
    - Behavior: Reactive fighter, counter-attacks when hit
    
    ANIMASI (dari folder assets):
    Attack, Dead, Hit, Idle, React, Walk
    
    SPECIAL ABILITY:
    - React: Counter-attack animation setelah terkena hit
    - Undead Resilience: Reduced damage from normal attacks
    - Cold Aura: Presence in ice areas
    """
    
    # AI CONSTANTS
    REACT_COOLDOWN = 90       # Frames antara react
    DAMAGE_REDUCTION = 0.85   # Takes 85% damage (undead resilience)
    
    def __init__(self, x, y):
        """Initialize Ice Skeleton at position (x, y)."""
        super().__init__(
            x=x, y=y,
            width=45, height=55,
            max_hp=75,
            attack_power=18,
            speed=2.5,
            asset_path=ICE_SKELETON_ASSET_PATH,
            scale=2.0
        )
        
        # Combat ranges
        self.detection_range = 350
        self.attack_range = 60
        self.lose_interest_range = 450
        
        # React system
        self.react_cooldown = 0
        self.is_reacting = False
        self.should_react = False  # Flag untuk trigger react setelah kena hit
        
        self._setup_animations()
    
    def _setup_animations(self):
        """Load animasi Ice Skeleton."""
        animation_mapping = {
            'idle': 'Idle',
            'walk': 'Walk',
            'chase': 'Walk',
            'attack': 'Attack',
            'react': 'React',
            'hurt': 'Hit',
            'die': 'Dead',
        }
        self.animator.load_sprites(animation_mapping)
        self.animator.animation_speed = 0.12
    
    def update(self, platforms):
        """Update dengan react behavior."""
        # Cooldown
        if self.react_cooldown > 0:
            self.react_cooldown -= 1
        
        # Update timers
        self.update_timers()
        
        if not self.alive:
            self.physics.update(platforms, 0, apply_gravity=True)
            self.rect = self.physics.rect
            return
        
        # Check if should trigger react
        if self.should_react and self.react_cooldown <= 0 and not self.is_reacting:
            self.is_reacting = True
            self.should_react = False
            self.ai_state = 'react'
            self.state = 'react'
            self.animator.reset_animation()
        
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
        IMPROVED AI: Reactive undead warrior behavior.
        Returns: x_velocity
        """
        if not self.alive or not self.player_ref:
            self.state = 'idle'
            return 0
        
        # Handle hurt state
        if self.ai_state == self.STATE_HURT or self.state == 'hurt':
            return 0
        
        # Handle react animation
        if self.is_reacting:
            self.state = 'react'
            direction = self.get_direction_to_player()
            self.facing_right = direction > 0
            
            if self.animator.is_animation_finished():
                # React finished - immediate counter-attack!
                self.is_reacting = False
                self.react_cooldown = self.REACT_COOLDOWN
                # Trigger attack after react
                self.ai_state = self.STATE_ATTACK
                self.do_attack()
            return 0
        
        distance = self.get_distance_to_player()
        direction = self.get_direction_to_player()
        
        # STATE MACHINE
        if distance > self.lose_interest_range:
            # Too far - patrol
            self.ai_state = self.STATE_PATROL
            self.state = 'walk'
            x_velocity = self.do_patrol()
            
        elif distance > self.detection_range:
            # Idle
            self.ai_state = self.STATE_IDLE
            self.state = 'idle'
            x_velocity = 0
            
        elif distance <= self.attack_range:
            # Melee attack
            self.ai_state = self.STATE_ATTACK
            self.facing_right = direction > 0
            self.do_attack()
            x_velocity = 0
            
        else:
            # Chase
            self.ai_state = self.STATE_CHASE
            self.state = 'chase'
            self.facing_right = direction > 0
            x_velocity = direction * self.movement_speed
        
        return x_velocity
    
    def take_damage(self, amount):
        """Override take damage - trigger react and apply resistance."""
        if not self.alive or self.is_invincible:
            return
        
        # Apply undead damage reduction
        reduced_damage = int(amount * self.DAMAGE_REDUCTION)
        
        # Set flag to react after taking damage
        if self.react_cooldown <= 0 and self.alive:
            self.should_react = True
        
        # Call parent take_damage with reduced damage
        super().take_damage(reduced_damage)
        
        print(f"[ICE SKELETON] Resisted {amount - reduced_damage} damage!")
