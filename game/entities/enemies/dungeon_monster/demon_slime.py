import pygame as pg
from game.entities.enemies.enemy import BaseEnemy

DEMON_SLIME_ASSET_PATH = 'assets/graphics/enemies/dungeon_monster/boss_demon_slime/'

class DemonSlime(BaseEnemy):
    # mini-boss with high hp and cleave attack
    
    # ai constants
    CLEAVE_RANGE = 80
    CLEAVE_COOLDOWN = 150
    RAGE_HP_THRESHOLD = 0.4
    
    # attack timing
    HIT_FRAME = 2
    
    def __init__(self, x, y):
        super().__init__(
            x=x, y=y,
            width=100, height=150,
            max_hp=150,
            attack_power=25,
            speed=1.8,
            asset_path=DEMON_SLIME_ASSET_PATH,
            scale=2.2
        )
        
        # combat ranges
        self.detection_range = 500
        self.attack_range = 150 
        self.lose_interest_range = 800
        
        # attack hitbox
        self.attack_box_width = 180
        self.attack_box_height = 110
        
        # sprite anchor offset
        self.sprite_anchor_offset = -25.0
        
        # boss mechanics
        self.is_enraged = False
        self.enrage_damage_multiplier = 1.3
        
        self.movement_speed = 2.2
        
        self._setup_animations()
    
    def _setup_animations(self):
        animation_mapping = {
            'idle': 'idle',
            'walk': 'walk',
            'chase': 'walk',
            # KEY FIX: Ensure this key matches the state sent to animator EXACTLY
            'attack': 'attack',
            'Attack': 'attack', # Fallback for case sensitivity issues
            'hurt': 'hurt',
            'die': 'death',
        }
        self.animator.load_sprites(animation_mapping)
        self.animator.animation_speed = 0.15  # Faster, more responsive (matches Skullwolf)
    
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
        
        # 3. Check rage mode
        hp_ratio = self.current_hp / self.max_hp
        if hp_ratio < self.RAGE_HP_THRESHOLD and not self.is_enraged:
            self.is_enraged = True
            self.base_speed = self.movement_speed
            self.movement_speed = self.base_speed * 1.4  # 40% faster
            self.attack_power = int(self.attack_power * self.enrage_damage_multiplier)
            print(f"[DEMON SLIME] ENRAGED! Damage: {self.attack_power}")
            
        # 4. Run AI if not in hurt / hurt animation finished
        if self.state != 'hurt' and self.alive:
            # Use custom AI (DIRECT CALL like Skullwolf)
            self._update_ai()
            
            # Set visual state based on AI state
            if self.ai_state in [self.STATE_CHASE, self.STATE_PATROL]:
                self.state = 'walk'
            elif self.ai_state == self.STATE_ATTACK:
                self.state = 'attack'
            elif self.ai_state == self.STATE_IDLE:
                self.state = 'idle'
        
        # 5. Update Physics
        if self.alive:
            self.physics.update(platforms, self.physics.velocity_x, apply_gravity=self.has_gravity)
        else:
            self.physics.update(platforms, 0, apply_gravity=self.has_gravity)
        
        # 6. Prevent overlapping with player
        self.avoid_player_collision()
        
        # 7. Sync rect
        self.rect = self.physics.rect
    
    def _update_ai(self):
        # boss ai behavior
        if not self.alive or not self.player_ref:
            return
            
        # Don't change state while attacking - wait for animation to finish
        if self.is_attacking:
            self.physics.velocity_x = 0
            return
        
        distance = self.get_distance_to_player()
        direction = self.get_direction_to_player()
        self.facing_right = direction > 0
        
        # STATE MACHINE
        if distance > self.lose_interest_range:
            # Lost interest - patrol
            self.ai_state = self.STATE_PATROL
            self.physics.velocity_x = self.do_patrol()
            return
            
        if distance > self.detection_range:
            # Idle waiting
            self.ai_state = self.STATE_IDLE
            self.physics.velocity_x = 0
            return
            
        if distance <= self.attack_range:
            # Attack!
            self.ai_state = self.STATE_ATTACK
            if not self.is_attacking:
                self.do_attack()
            self.physics.velocity_x = 0
            return
            
        # Default - chase relentlessly
        self.ai_state = self.STATE_CHASE
        chase_speed = direction * self.movement_speed
        
        # Enraged: More aggressive movement
        if self.is_enraged:
            chase_speed *= 1.2
        
        self.physics.velocity_x = chase_speed
    
    def do_attack(self):
        # cleave attack
        super().do_attack()
        print(f"[DEMON SLIME] CLEAVE ATTACK! (Enraged: {self.is_enraged})")
    
    def take_damage(self, amount, apply_stun=False):
        # boss has defense
        reduced_damage = amount * 0.9
        super().take_damage(int(reduced_damage), apply_stun=apply_stun)
