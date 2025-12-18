import pygame as pg
from game.entities.enemies.enemy import BaseEnemy

ICE_SKELETON_ASSET_PATH = 'assets/graphics/enemies/ice_monster/Skeleton/'

class IceSkeleton(BaseEnemy):
    # undead warrior with react ability
    
    # ai constants
    REACT_COOLDOWN = 90
    DAMAGE_REDUCTION = 0.85
    
    # attack timing
    HIT_FRAME = 6
    
    def __init__(self, x, y):
        super().__init__(
            x=x, y=y,
            # GAMEPLAY HITBOX: Wider for fair hits
            width=55, height=65,
            max_hp=75,
            attack_power=18,
            speed=2.5,
            asset_path=ICE_SKELETON_ASSET_PATH,
            scale=2.5  # Increased for more imposing presence
        )
        
        # GAMEPLAY HITBOX FIX: Sprite defaults face RIGHT, flipped when LEFT
        # NEGATIVE value gets INVERTED when facing left (becomes positive shift)
        self.sprite_anchor_offset = -25
        
        # Combat ranges
        self.detection_range = 350
        # FIX BOUNCE: Attack range must be larger than player hitbox + GAP
        # This ensures enemy stops and attacks BEFORE collision pushback triggers
        self.attack_range = 70 
        self.lose_interest_range = 450
        
        # React system
        self.react_cooldown = 0
        self.is_reacting = False
        self.should_react = False  # Flag untuk trigger react setelah kena hit
        
        self._setup_animations()
    
    def _setup_animations(self):
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
        self.animator.animation_speed = 0.15  # Responsive/Fast (matches Skullwolf)
    
    def update(self, platforms):
        # 1. Update Timers
        self.update_timers()
        
        # Cooldown
        if self.react_cooldown > 0:
            self.react_cooldown -= 1
        
        # 2. Handle hurt state WITH TIMEOUT (Goblin pattern)
        current_time = pg.time.get_ticks()
        hurt_timeout = False
        if self.state == 'hurt':
            if current_time - self.last_hit_time > 500:
                hurt_timeout = True
        
        if self.state == 'hurt' and (self.animator.is_animation_finished() or hurt_timeout):
            self.state = 'idle'
            self.ai_state = self.STATE_IDLE
            self.is_attacking = False
            self.is_reacting = False
            self.animator.animation_finished = False
        
        # React trigger check
        if self.should_react and self.react_cooldown <= 0 and not self.is_reacting:
            self.is_reacting = True
            self.should_react = False
            self.ai_state = 'react'
            self.state = 'react'
            self.animator.reset_animation()
        
        # 3. Run AI if not hurt (GOBLIN PATTERN)
        if self.state != 'hurt' and self.alive:
            self._update_ai()
            
            # Map AI state to visual state (GOBLIN PATTERN)
            if self.is_reacting:
                self.state = 'react'
            elif self.ai_state in [self.STATE_CHASE, self.STATE_PATROL]:
                self.state = 'walk'
            elif self.ai_state == self.STATE_ATTACK:
                self.state = 'attack'
            elif self.ai_state == self.STATE_IDLE:
                self.state = 'idle'
        
        # 4. Update Physics (GOBLIN PATTERN)
        if self.alive:
            self.physics.update(platforms, self.physics.velocity_x, apply_gravity=self.has_gravity)
        else:
            self.physics.update(platforms, 0, apply_gravity=self.has_gravity)
        
        # 5. Avoid player collision (GOBLIN PATTERN)
        self.avoid_player_collision()
        
        # 6. Sync rect (GOBLIN PATTERN)
        self.rect = self.physics.rect

    def _update_ai(self):
        if not self.player_ref or not self.alive:
            self.ai_state = self.STATE_IDLE
            self.physics.velocity_x = 0
            return
            
        # 1. STRICT LOCK: If attacking, freeze velocity
        if self.is_attacking:
            self.physics.velocity_x = 0
            return
            
        # Handle react animation
        if self.is_reacting:
            self.physics.velocity_x = 0
            direction = self.get_direction_to_player()
            self.facing_right = direction > 0
            
            if self.animator.is_animation_finished():
                # React finished - immediate counter-attack!
                self.is_reacting = False
                self.react_cooldown = self.REACT_COOLDOWN
                # Trigger attack after react
                self.ai_state = self.STATE_ATTACK
                self.do_attack()
            return

        distance = self.get_distance_to_player()
        direction = self.get_direction_to_player()
        self.facing_right = direction > 0
        
        # STATE MACHINE (Goblin pattern)
        # Too far - lose interest
        if distance > self.lose_interest_range:
            self.ai_state = self.STATE_IDLE
            self.physics.velocity_x = 0
            return
        
        # Not detected yet
        if distance > self.detection_range:
            self.ai_state = self.STATE_IDLE
            self.physics.velocity_x = 0
            return
        
        # In attack range - attack!
        if distance <= self.attack_range:
            # FIX GLITCH: Immediate velocity lock to prevent flickering
            self.physics.velocity_x = 0
            self.ai_state = self.STATE_ATTACK
            if not self.is_attacking:
                self.do_attack()
            return
        
        # Default - chase
        self.ai_state = self.STATE_CHASE
        self.physics.velocity_x = direction * self.movement_speed
    
    def take_damage(self, amount, apply_stun=False):
        # trigger react and apply resistance
        if not self.alive or self.is_invincible:
            return
        
        # Apply undead damage reduction
        reduced_damage = int(amount * self.DAMAGE_REDUCTION)
        
        # Set flag to react after taking damage
        if self.react_cooldown <= 0 and self.alive:
            self.should_react = True
        
        # Call parent take_damage with reduced damage
        super().take_damage(reduced_damage, apply_stun=apply_stun)
        
        print(f"[ICE SKELETON] Resisted {amount - reduced_damage} damage!")
