import pygame as pg
from game.entities.enemies.enemy import BaseEnemy

GUARDIAN_ASSET_PATH = 'assets/graphics/enemies/ice_monster/guardian/'

class Guardian(BaseEnemy):
    # elite ice warrior with combo attacks
    
    # ai constants
    COMBO_RANGE = 70
    AURA_RANGE = 120
    COMBO_COOLDOWN = 120
    
    # attack timing
    HIT_FRAME = 11
    
    def __init__(self, x, y):
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
        # FIX DELAY: attack_range must be smaller so attack_box REACHES player
        # Demon Slime: range=150, box=180. Ratio ~0.83
        # Guardian: box=150, so range should be ~125 -> 80 for safety
        self.attack_range = 80
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
        animation_mapping = {
            'idle': 'idle',
            'walk': 'walk',
            'chase': 'walk',
            'attack': 'attack',
            'hurt': 'hurt',
            'die': 'death',
        }
        self.animator.load_sprites(animation_mapping)
        self.animator.animation_speed = 0.15  # Match Demon Slime for consistent timing
    
    def update(self, platforms):
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
        # simple direct attack ai
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
        # simple attack
        super().do_attack()
        print(f"[ICE GUARDIAN] ATTACKS!")
    
    def take_damage(self, amount, apply_stun=False):
        super().take_damage(amount, apply_stun=apply_stun)
