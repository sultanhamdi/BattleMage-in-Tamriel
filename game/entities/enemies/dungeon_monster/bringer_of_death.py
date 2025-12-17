import pygame as pg
from game.entities.enemies.enemy import BaseEnemy

# Path aset lokal untuk Bringer of Death
BRINGER_ASSET_PATH = 'assets/graphics/enemies/dungeon_monster/bringer_of_death/'

class BringerOfDeath(BaseEnemy):
    """
    Enemy Bringer of Death - Elite Boss dengan Spell Casting.
    
    KARAKTERISTIK:
    - HP: 200 (Boss - Highest)
    - Damage: 30 (Attack), 40 (Spell)
    - Speed: 2.5 (Moderate)
    - Behavior: Spell caster, teleport, powerful magic attacks
    
    ANIMASI:
    Idle(8), Walk(8), Attack(10), Cast(10), Spell(16), Hurt(3), Death(10)
    
    SPECIAL ABILITY:
    - Spell Casting: Powerful magic attacks
    - Phase Shift: Different behavior based on HP
    - Elite Boss: Hardest enemy in dungeon
    """
    
    # AI CONSTANTS
    SPELL_RANGE = 350
    SPELL_COOLDOWN = 180
    MELEE_RANGE = 70
    PHASE2_HP_THRESHOLD = 0.6  # Phase 2 when HP < 60%
    PHASE3_HP_THRESHOLD = 0.3  # Phase 3 when HP < 30%
    
    def __init__(self, x, y):
        """Initialize Bringer of Death at position (x, y)."""
        super().__init__(
            x=x, y=y,
            width=65, height=75,
            max_hp=200,
            attack_power=30,
            speed=2.5,
            asset_path=BRINGER_ASSET_PATH,
            scale=2.5  # Large boss
        )
        
        # Combat ranges
        self.detection_range = 600
        self.attack_range = self.MELEE_RANGE
        self.lose_interest_range = 1000  # Boss never forgets
        
        # Boss mechanics
        self.spell_cooldown = 0
        self.is_casting = False
        self.current_phase = 1
        
        # Sprite anchor offset - character is positioned to the RIGHT in sprite canvas
        # This compensates for the asymmetry when flipping facing direction
        self.sprite_anchor_offset = 80  # Adjust this value as needed
        
        self._setup_animations()
    
    def _setup_animations(self):
        """Load animasi Bringer of Death."""
        animation_mapping = {
            'idle': 'idle',
            'walk': 'walk',
            'chase': 'walk',
            'attack': 'attack',
            'cast': 'cast',
            'spell': 'spell',
            'hurt': 'hurt',
            'die': 'death',
        }
        self.animator.load_sprites(animation_mapping)
        self.animator.animation_speed = 0.10
    
    def update(self, platforms):
        """Update dengan phase mechanics."""
        # Cooldown
        if self.spell_cooldown > 0:
            self.spell_cooldown -= 1
        
        # HURT ANIMATION FIX
        # If in hurt state and animation finished, return to idle immediately
        # This prevents the 3-frame animation from looping 3-4 times
        if self.state == 'hurt' and self.animator.is_animation_finished():
            self.state = self.STATE_IDLE
            # Optional: Clear invincibility early if you want it to be vulnerable again? 
            # self.invincibility_timer = 0

        
        # Check phase
        hp_ratio = self.current_hp / self.max_hp
        if hp_ratio < self.PHASE3_HP_THRESHOLD and self.current_phase < 3:
            self.current_phase = 3
            if not hasattr(self, 'base_speed'):
                self.base_speed = self.movement_speed
            self.movement_speed = self.base_speed * 1.5
            print(f"[BRINGER] PHASE 3 - DESPERATE FURY!")
        elif hp_ratio < self.PHASE2_HP_THRESHOLD and self.current_phase < 2:
            self.current_phase = 2
            if not hasattr(self, 'base_speed'):
                self.base_speed = self.movement_speed
            self.movement_speed = self.base_speed * 1.2
            print(f"[BRINGER] PHASE 2 - DARK POWER!")
        
        super().update(platforms)
    
    def _update_ai(self):
        """
        IMPROVED AI: Multi-phase boss behavior.
        """
        if not self.alive or not self.player_ref:
            return
        
        # Handle spell casting
        if self.is_casting:
            self.physics.velocity_x = 0
            if self.animator.is_animation_finished():
                self.cast_spell()
                spell_cd = self.SPELL_COOLDOWN
                if self.current_phase >= 2:
                    spell_cd = int(spell_cd * 0.7)  # Faster spells in phase 2+
                self.spell_cooldown = spell_cd
                self.is_casting = False
                self.ai_state = self.STATE_CHASE
            return
        
        distance = self.get_distance_to_player()
        
        # STATE MACHINE - Phase-based behavior
        if distance > self.detection_range:
            # Patrol menacingly
            self.ai_state = self.STATE_PATROL
            self.physics.velocity_x = self.do_patrol()
            
        elif distance <= self.attack_range:
            # Melee attack
            self.ai_state = self.STATE_ATTACK
            self.do_attack()
            self.physics.velocity_x = 0
            
        elif distance <= self.SPELL_RANGE and self.spell_cooldown <= 0:
            # SPELL CAST
            self.ai_state = 'cast'
            self.is_casting = True
            self.animator.reset_animation()
            self.physics.velocity_x = 0
            
        else:
            # Chase with phase-based aggression
            self.ai_state = self.STATE_CHASE
            chase_speed = self.do_chase()
            
            # Phase 3: More aggressive movement
            if self.current_phase >= 3:
                chase_speed *= 1.2
            
            self.physics.velocity_x = chase_speed
    
    def cast_spell(self):
        """Cast powerful spell."""
        damage_multiplier = 1.0 + (0.3 * self.current_phase)  # More damage per phase
        print(f"[BRINGER] CASTS SPELL! (Phase {self.current_phase})")
        # TODO: Implement spell projectile/effect
    
    def take_damage(self, amount):
        """Override take damage - boss resistance."""
        # High resistance
        reduced_damage = amount * 0.85
        super().take_damage(int(reduced_damage))
