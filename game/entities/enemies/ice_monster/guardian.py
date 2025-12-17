import pygame as pg
from game.entities.enemies.enemy import BaseEnemy

# Path aset lokal untuk Ice Guardian
GUARDIAN_ASSET_PATH = 'assets/graphics/enemies/ice_monster/guardian/'

class Guardian(BaseEnemy):
    """
    Enemy Ice Guardian - Elite Ice Warrior dengan Combo Attacks.
    
    KARAKTERISTIK:
    - HP: 90 (High)
    - Damage: 20 (High)
    - Speed: 3.2 (Moderate-Fast)
    - Behavior: Elite warrior, combo attacks, freezing aura
    
    ANIMASI:
    idle(4), walk(8), attack(12), death(14), hurt(3)
    
    SPECIAL ABILITY:
    - Combo Attacks: Can chain multiple attacks
    - Ice Aura: Slows player when nearby
    - Elite Warrior: Balanced stats, skilled fighter
    """
    
    # AI CONSTANTS
    COMBO_RANGE = 70         # Range for combo
    AURA_RANGE = 120         # Slow aura range
    COMBO_COOLDOWN = 120
    
    def __init__(self, x, y):
        """Initialize Ice Guardian at position (x, y)."""
        super().__init__(
            x=x, y=y,
            # FIXED HITBOX: Adjusted for leaner fit but consistent height
            width=90, height=130,
            max_hp=90,
            attack_power=20,
            speed=3.2,
            asset_path=GUARDIAN_ASSET_PATH,
            scale=2.1
        )
        
        # FIX OFFSET: Ensure sprite centers on hitbox
        self.sprite_anchor_offset = 0
        
        # Combat ranges
        self.detection_range = 400
        # FIX RANGE: Match spear reach (150)
        self.attack_range = 120
        self.lose_interest_range = 550
        
        # Custom Attack Box for long spear
        self.attack_box_width = 150  # Extended for spear reach
        self.attack_box_height = 110  # Increased to cover more body
        
        # Elite mechanics
        self.combo_cooldown = 0
        self.combo_count = 0     # Track combo chain
        self.max_combo = 3       # Max 3-hit combo
        self.is_comboing = False
        
        self._setup_animations()
    
    def _setup_animations(self):
        """Load animasi Ice Guardian."""
        animation_mapping = {
            'idle': 'idle',
            'walk': 'walk',
            'chase': 'walk',
            'attack': 'attack',
            'hurt': 'hurt',
            'die': 'death',
        }
        self.animator.load_sprites(animation_mapping)
        self.animator.animation_speed = 0.14  # Faster combat feel
    
    def update(self, platforms):
        """Update with EXACT GOBLIN PATTERN (PROVEN WORKING)."""
        # 1. Update Timers
        self.update_timers()
        
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
        
        # 5. Avoid player collision (GOBLIN PATTERN)
        self.avoid_player_collision()
        
        # 6. Sync rect (GOBLIN PATTERN)
        self.rect = self.physics.rect
    
    def _update_ai(self):
        """
        SIMPLIFIED AI: Direct attack like Skullwolf (no complex combos).
        """
        if not self.alive or not self.player_ref:
            return
            
        # 1. STRICT LOCK: If attacking, freeze velocity and do nothing else (Skullwolf pattern)
        if self.is_attacking:
            self.physics.velocity_x = 0
            return
        
        distance = self.get_distance_to_player()
        direction = self.get_direction_to_player()
        self.facing_right = direction > 0
        
        # STATE MACHINE - Simple and direct
        if distance > self.lose_interest_range:
            # Too far - idle
            self.ai_state = self.STATE_IDLE
            self.physics.velocity_x = 0
            return
            
        if distance > self.detection_range:
            # Not detected yet
            self.ai_state = self.STATE_IDLE
            self.physics.velocity_x = 0
            return
            
        if distance <= self.attack_range:
            # In attack range - attack!
            self.ai_state = self.STATE_ATTACK
            if not self.is_attacking:  # Guard check
                self.do_attack()
            self.physics.velocity_x = 0
            return
            
        # Default - chase
        self.ai_state = self.STATE_CHASE
        self.physics.velocity_x = direction * self.movement_speed
    
    def do_attack(self):
        """Simple attack - no combos."""
        super().do_attack()
        print(f"[ICE GUARDIAN] ATTACKS!")
    
    def take_damage(self, amount, apply_stun=False):
        """Override take damage."""
        super().take_damage(amount, apply_stun=apply_stun)
