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
            width=70, height=80,
            max_hp=120,
            attack_power=28,
            speed=1.5,
            asset_path=GOLEM_ASSET_PATH,
            scale=2.3
        )
        
        # Combat ranges
        self.detection_range = 350
        self.attack_range = self.SLAM_RANGE
        self.lose_interest_range = 500
        
        # Tank mechanics
        self.slam_cooldown = 0
        self.is_appearing = True  # Start with appear animation
        self.appear_timer = 60    # Appear for 60 frames
        
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
            'die': 'die',
        }
        self.animator.load_sprites(animation_mapping)
        self.animator.animation_speed = 0.08  # Very slow, heavy
    
    def update(self, dt):
        """Update dengan tank mechanics."""
        # Handle appear animation
        if self.is_appearing:
            self.appear_timer -= 1
            if self.appear_timer <= 0:
                self.is_appearing = False
                self.ai_state = self.STATE_IDLE
            return
        
        # Cooldown
        if self.slam_cooldown > 0:
            self.slam_cooldown -= 1
        
        super().update(dt)
    
    def _update_ai(self):
        """
        IMPROVED AI: Tank behavior - slow but unstoppable.
        """
        if not self.alive or not self.player_ref:
            return
        
        distance = self.get_distance_to_player()
        
        # STATE MACHINE - Tank
        if distance > self.lose_interest_range:
            # Too far - slow patrol
            self.ai_state = self.STATE_PATROL
            self.physics.velocity_x = self.do_patrol() * 0.8  # Even slower patrol
            
        elif distance > self.detection_range:
            # Idle stance
            self.ai_state = self.STATE_IDLE
            self.physics.velocity_x = 0
            
        elif distance <= self.attack_range and self.slam_cooldown <= 0:
            # GROUND SLAM!
            self.ai_state = self.STATE_ATTACK
            self.do_attack()
            self.slam_cooldown = self.SLAM_COOLDOWN
            self.physics.velocity_x = 0
            
        else:
            # Slow, relentless chase
            self.ai_state = self.STATE_CHASE
            self.physics.velocity_x = self.do_chase()
    
    def do_attack(self):
        """Override attack - ground slam."""
        super().do_attack()
        print(f"[ICE GOLEM] GROUND SLAM!")
        # TODO: Implement AOE damage + stun effect
    
    def take_damage(self, amount):
        """Override take damage - extreme tank."""
        # High damage reduction
        reduced_damage = amount * self.DAMAGE_REDUCTION
        super().take_damage(int(reduced_damage))
        print(f"[ICE GOLEM] Absorbed {amount - int(reduced_damage)} damage!")
