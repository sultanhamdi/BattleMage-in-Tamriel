import pygame as pg
from game.entities.enemies.enemy import BaseEnemy

GOBLIN_ASSET_PATH = 'assets/graphics/enemies/grass_monster/Goblin/'

class Goblin(BaseEnemy):
    # fast melee fighter with combo attacks
    
    HIT_FRAME = 4
    
    def __init__(self, x, y):
        super().__init__(
            x=x, y=y,
            width=50, height=60,
            max_hp=60,
            attack_power=15,
            speed=3.5,
            asset_path=GOBLIN_ASSET_PATH,
            scale=1.8
        )
        
        self.detection_range = 350
        self.attack_range = 55
        self.lose_interest_range = 450
        
        self.attack_box_width = 70
        self.attack_box_height = 60
        
        # Combo system
        self.attack_combo_count = 0
        self.max_combo_before_attack2 = 2
        self.is_attack2 = False
        
        self._setup_animations()
    
    def _setup_animations(self):
        animation_mapping = {
            'idle': 'idle',
            'walk': 'run',
            'attack': 'attack',
            'attack2': 'attack2',
            'hurt': 'take_hit',
            'die': 'death',
        }
        self.animator.load_sprites(animation_mapping)
        self.animator.animation_speed = 0.15
    
    def update(self, platforms):
        self.update_timers()
        
        # Handle hurt state
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
        
        # Run AI if not hurt
        if self.state != 'hurt' and self.alive:
            self._update_ai()
            
            if self.ai_state in [self.STATE_CHASE, self.STATE_PATROL]:
                self.state = 'walk'
            elif self.ai_state == self.STATE_ATTACK:
                if self.is_attack2:
                    self.state = 'attack2'
                else:
                    self.state = 'attack'
            elif self.ai_state == self.STATE_IDLE:
                self.state = 'idle'
        
        # Update Physics
        if self.alive:
            self.physics.update(platforms, self.physics.velocity_x, apply_gravity=self.has_gravity)
        else:
            self.physics.update(platforms, 0, apply_gravity=self.has_gravity)
        
        self.avoid_player_collision()
        self.rect = self.physics.rect
    
    def _update_ai(self):
        if not self.player_ref or not self.alive:
            self.ai_state = self.STATE_IDLE
            self.physics.velocity_x = 0
            return
        
        if self.is_attacking:
            self.physics.velocity_x = 0
            return
        
        distance = self.get_distance_to_player()
        direction = self.get_direction_to_player()
        self.facing_right = direction > 0
        
        if distance > self.lose_interest_range:
            self.ai_state = self.STATE_IDLE
            self.physics.velocity_x = 0
            return
        
        if distance > self.detection_range:
            self.ai_state = self.STATE_IDLE
            self.physics.velocity_x = 0
            return
        
        if distance <= self.attack_range:
            self.ai_state = self.STATE_ATTACK
            if not self.is_attacking:
                if self.attack_combo_count >= self.max_combo_before_attack2:
                    self.is_attack2 = True
                    self.attack_combo_count = 0
                else:
                    self.is_attack2 = False
                    self.attack_combo_count += 1
                self.do_attack()
            self.physics.velocity_x = 0
            return
        
        self.ai_state = self.STATE_CHASE
        self.physics.velocity_x = direction * self.movement_speed
