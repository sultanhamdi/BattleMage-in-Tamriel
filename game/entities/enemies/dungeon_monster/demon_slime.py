import pygame as pg
from game.entities.enemies.enemy import BaseEnemy

# Path aset lokal untuk Boss Demon Slime
DEMON_SLIME_ASSET_PATH = 'assets/graphics/enemies/dungeon_monster/boss_demon_slime/'

class DemonSlime(BaseEnemy):
    """
    Enemy Demon Slime - Mini-Boss dengan High HP & Cleave Attack.
    
    KARAKTERISTIK:
    - HP: 150 (Very High - Boss tier)
    - Damage: 25 (High)
    - Speed: 1.8 (Slow but powerful)
    - Behavior: Aggressive, cleave AOE attack, relentless
    
    ANIMASI:
    01_demon_idle(6), 02_demon_walk(12), 03_demon_cleave(15), 04_demon_take_hit(5), 05_demon_death(22)
    
    SPECIAL ABILITY:
    - Cleave Attack: Wide AOE swing (high damage)
    - Boss HP: Much higher HP than normal enemies
    - Relentless: Never gives up chase
    """
    
    # AI CONSTANTS
    CLEAVE_RANGE = 80        # Wider attack range
    CLEAVE_COOLDOWN = 150    # Slower but powerful attacks
    RAGE_HP_THRESHOLD = 0.4  # Enrage when HP < 40%
    
    def __init__(self, x, y):
        """Initialize Demon Slime at position (x, y)."""
        super().__init__(
            x=x, y=y,
            width=60, height=65,
            max_hp=150,
            attack_power=25,
            speed=1.8,
            asset_path=DEMON_SLIME_ASSET_PATH,
            scale=2.2  # Larger boss
        )
        
        # Combat ranges
        self.detection_range = 500  # Detects from far
        self.attack_range = self.CLEAVE_RANGE
        self.lose_interest_range = 800  # Never gives up easily
        
        # Boss mechanics
        self.is_enraged = False
        self.cleave_cooldown = 0
        self.last_cleave_time = 0
        
        self._setup_animations()
    
    def _setup_animations(self):
        """Load animasi Demon Slime."""
        animation_mapping = {
            'idle': '01_demon_idle',
            'walk': '02_demon_walk',
            'chase': '02_demon_walk',
            'attack': '03_demon_cleave',
            'hurt': '04_demon_take_hit',
            'die': '05_demon_death',
        }
        self.animator.load_sprites(animation_mapping)
        self.animator.animation_speed = 0.09  # Slow, heavy
    
    def update(self, dt):
        """Update dengan boss mechanics."""
        # Cooldown
        if self.cleave_cooldown > 0:
            self.cleave_cooldown -= 1
        
        # Check rage mode
        hp_ratio = self.current_hp / self.max_hp
        if hp_ratio < self.RAGE_HP_THRESHOLD and not self.is_enraged:
            self.is_enraged = True
            self.base_speed = self.movement_speed  # Store base speed
            self.movement_speed = self.base_speed * 1.4  # Faster when enraged
            print(f"[DEMON SLIME] ENRAGED!")
        
        super().update(dt)
    
    def _update_ai(self):
        """
        IMPROVED AI: Boss behavior - relentless and powerful.
        """
        if not self.alive or not self.player_ref:
            return
        
        distance = self.get_distance_to_player()
        
        # STATE MACHINE - Boss never gives up
        if distance > self.lose_interest_range:
            # Even far, slowly patrol
            self.ai_state = self.STATE_PATROL
            self.physics.velocity_x = self.do_patrol()
            
        elif distance > self.detection_range:
            # Patrol aggressively
            self.ai_state = self.STATE_PATROL
            self.physics.velocity_x = self.do_patrol()
            
        elif distance <= self.attack_range:
            # CLEAVE ATTACK
            if self.cleave_cooldown <= 0:
                self.ai_state = self.STATE_ATTACK
                self.do_attack()
                self.cleave_cooldown = self.CLEAVE_COOLDOWN
                if self.is_enraged:
                    self.cleave_cooldown = int(self.CLEAVE_COOLDOWN * 0.7)  # Faster when enraged
                self.physics.velocity_x = 0
            else:
                # Wait for cooldown, move slightly
                self.ai_state = 'prepare'
                self.physics.velocity_x = self.do_chase() * 0.5
                
        else:
            # Chase relentlessly
            self.ai_state = self.STATE_CHASE
            self.physics.velocity_x = self.do_chase()
    
    def do_attack(self):
        """Override attack untuk cleave."""
        super().do_attack()
        print(f"[DEMON SLIME] CLEAVE ATTACK!")
        # TODO: Implement AOE damage area
    
    def take_damage(self, amount):
        """Override take damage - boss has defense."""
        # Reduce damage slightly (boss armor)
        reduced_damage = amount * 0.9
        super().take_damage(int(reduced_damage))
