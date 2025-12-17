import pygame as pg
from game.entities.enemies.enemy import BaseEnemy

# Path aset lokal untuk Ice Golem
GOLEM_ASSET_PATH = 'assets/graphics/enemies/ice_monster/golem/'

class Golem(BaseEnemy):
    """
    Enemy Ice Golem - Super Tank dengan Slam Attack.
    
    KARAKTERISTIK:
    - HP: 120 (Very High)
    - Damage: 28 (Very High)
    - Speed: 1.5 (Very Slow)
    - Behavior: Tank, ground slam, appear animation
    
    ANIMASI:
    idle(4), walk(12), attack(12), die(15), hurt(5)
    
    SPECIAL ABILITY:
    - Tank: Highest defense, very high HP
    - Ground Slam: AOE attack that stuns
    - Appear Animation: Rises from ground when spawned
    - Slow but Unstoppable
    """
    
    # AI CONSTANTS
    SLAM_RANGE = 90          # Wide slam range
    SLAM_COOLDOWN = 200      # Slow but devastating
    DAMAGE_REDUCTION = 0.75  # Takes only 75% damage
    
    def __init__(self, x, y):
        """Initialize Ice Golem at position (x, y)."""
        super().__init__(
            x=x, y=y,
            # FIXED HITBOX: Increased to match large sprite (scale 2.6)
            width=110, height=120, 
            max_hp=120,
            attack_power=28,
            speed=1.5,
            asset_path=GOLEM_ASSET_PATH,
            scale=2.6  # Increased for giant tank presence
        )
        
        # FIX OFFSET: Center the sprite properly relative to hitbox
        self.sprite_anchor_offset = 0
        
        # Combat ranges
        self.detection_range = 350
        # BENCHMARK: Match Guardian's attack_range (120) which works without bounce
        self.attack_range = 120 
        self.lose_interest_range = 500
        
        # Tank mechanics
        self.slam_cooldown = 0
        self.is_appearing = True  # Start with appear animation
        self.appear_timer = 60    # Appear for 60 frames
        
        # KEY FIX: Custom Attack Box (User Request: "too small")
        self.attack_box_width = 150  # Wide slam area
        self.attack_box_height = 120 # Full height
        
        self._setup_animations()
        
        # Override initial state
        self.ai_state = self.STATE_APPEAR
    
    def _setup_animations(self):
        """Load animasi Ice Golem."""
        animation_mapping = {
            'idle': 'idle',
            'walk': 'walk',
            'chase': 'walk',
            'attack': 'attack',
            'appear': 'idle',  # Use idle for appear
            'hurt': 'hurt',
            'die': 'death',
        }
        self.animator.load_sprites(animation_mapping)
        self.animator.animation_speed = 0.11  # Faster but still heavy (was 0.08)
    
    def update(self, platforms):
        """Update with EXACT GOBLIN PATTERN (PROVEN WORKING)."""
        # 1. Update Timers
        self.update_timers()
        
        # Handle appear animation
        if self.is_appearing:
            self.appear_timer -= 1
            self.state = 'appear'
            if self.appear_timer <= 0:
                self.is_appearing = False
                self.ai_state = self.STATE_IDLE
            self.physics.update(platforms, 0, apply_gravity=True)
            self.rect = self.physics.rect
            return
        
        # Cooldowns
        if self.slam_cooldown > 0:
            self.slam_cooldown -= 1
        
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
            self.animator.animation_finished = False
        
        # 3. Run AI if not hurt (GOBLIN PATTERN)
        if self.state != 'hurt' and self.alive:
            self._update_ai()
            
            # Map AI state to visual state (GOBLIN PATTERN)
            if self.ai_state in [self.STATE_CHASE, self.STATE_PATROL]:
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
        
        # 5. FIXED: Re-enable collision avoidance (matches Skullwolf/BOD)
        self.avoid_player_collision()
        
        # 6. Sync rect (GOBLIN PATTERN)
        self.rect = self.physics.rect
    
    def _update_ai(self):
        """
        IMPROVED AI: Tank behavior - slow but unstoppable.
        """
        if not self.alive or not self.player_ref:
            return
            
        # 1. STRICT LOCK: If attacking, freeze velocity
        if self.is_attacking:
            self.physics.velocity_x = 0
            return
        
        distance = self.get_distance_to_player()
        direction = self.get_direction_to_player()
        self.facing_right = direction > 0
        
        # STATE MACHINE - Tank
        if distance > self.lose_interest_range:
            # Too far - slow patrol
            self.ai_state = self.STATE_PATROL
            self.physics.velocity_x = self.do_patrol() * 0.8  # Even slower patrol
            return
            
        if distance > self.detection_range:
            # Idle stance
            self.ai_state = self.STATE_IDLE
            self.physics.velocity_x = 0
            return
            
        if distance <= self.attack_range:
            # In attack range - ALWAYS stop (even during cooldown)
            self.physics.velocity_x = 0
            self.ai_state = self.STATE_ATTACK
            # Only actually attack if cooldown finished
            if self.slam_cooldown <= 0 and not self.is_attacking:
                self.do_attack()
                self.slam_cooldown = self.SLAM_COOLDOWN
            return
            
        # Default - chase
        self.ai_state = self.STATE_CHASE
        self.physics.velocity_x = direction * self.movement_speed
    
    def do_attack(self):
        """Override attack - ground slam."""
        super().do_attack()
        print(f"[ICE GOLEM] GROUND SLAM!")
        # TODO: Implement AOE damage + stun effect
    
    def take_damage(self, amount, apply_stun=False):
        """Override take damage - extreme tank."""
        # High damage reduction
        reduced_damage = amount * self.DAMAGE_REDUCTION
        super().take_damage(int(reduced_damage), apply_stun=apply_stun)
        print(f"[ICE GOLEM] Absorbed {amount - int(reduced_damage)} damage!")
