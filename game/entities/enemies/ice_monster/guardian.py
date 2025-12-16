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
            width=55, height=65,
            max_hp=90,
            attack_power=20,
            speed=3.2,
            asset_path=GUARDIAN_ASSET_PATH,
            scale=2.1
        )
        
        # Combat ranges
        self.detection_range = 400
        self.attack_range = self.COMBO_RANGE
        self.lose_interest_range = 550
        
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
        self.animator.animation_speed = 0.11
    
    def update(self, dt):
        """Update dengan combo mechanics."""
        # Cooldown
        if self.combo_cooldown > 0:
            self.combo_cooldown -= 1
        
        # Check if player in aura range
        if self.player_ref and self.alive:
            distance = self.get_distance_to_player()
            if distance <= self.AURA_RANGE:
                # TODO: Apply slow effect to player
                pass
        
        super().update(dt)
    
    def _update_ai(self):
        """
        IMPROVED AI: Elite warrior behavior with combos.
        """
        if not self.alive or not self.player_ref:
            return
        
        # Handle combo chain
        if self.is_comboing:
            self.physics.velocity_x = 0
            if self.animator.is_animation_finished():
                self.combo_count += 1
                if self.combo_count >= self.max_combo:
                    # Combo finished
                    self.is_comboing = False
                    self.combo_count = 0
                    self.combo_cooldown = self.COMBO_COOLDOWN
                    self.ai_state = self.STATE_CHASE
                else:
                    # Continue combo
                    distance = self.get_distance_to_player()
                    if distance <= self.attack_range:
                        self.animator.reset_animation()
                        print(f"[GUARDIAN] Combo hit {self.combo_count + 1}!")
                    else:
                        # Player escaped, break combo
                        self.is_comboing = False
                        self.combo_count = 0
                        self.ai_state = self.STATE_CHASE
            return
        
        distance = self.get_distance_to_player()
        
        # STATE MACHINE - Elite warrior
        if distance > self.lose_interest_range:
            # Too far - patrol
            self.ai_state = self.STATE_PATROL
            self.physics.velocity_x = self.do_patrol()
            
        elif distance > self.detection_range:
            # Idle stance
            self.ai_state = self.STATE_IDLE
            self.physics.velocity_x = 0
            
        elif distance <= self.attack_range and self.combo_cooldown <= 0:
            # START COMBO!
            self.ai_state = self.STATE_ATTACK
            self.do_attack()
            self.is_comboing = True
            self.combo_count = 0
            self.physics.velocity_x = 0
            
        else:
            # Chase with purpose
            self.ai_state = self.STATE_CHASE
            chase_speed = self.do_chase()
            
            # Speed up if close to attack range
            if distance < self.attack_range + 50:
                chase_speed *= 1.2
            
            self.physics.velocity_x = chase_speed
    
    def do_attack(self):
        """Override attack - combo attack."""
        super().do_attack()
        print(f"[ICE GUARDIAN] COMBO START!")
    
    def take_damage(self, amount):
        """Override take damage - skilled fighter."""
        # Interrupt combo if hit
        if self.is_comboing:
            self.is_comboing = False
            self.combo_count = 0
        
        super().take_damage(amount)
