import pygame as pg
from game.entities.enemies.enemy import BaseEnemy
from game.utils.projectile import ProjectileManager

MUSHROOM_ASSET_PATH = 'assets/graphics/enemies/grass_monster/Mushroom/'
MUSHROOM_PROJECTILE_PATH = 'assets/graphics/enemies/grass_monster/Mushroom/projectile/'

class Mushroom(BaseEnemy):
    # territorial defender with spore attacks
    
    TERRITORY_RADIUS = 200
    SPORE_COOLDOWN = 600
    
    # attack timing
    HIT_FRAME = 5
    
    def __init__(self, x, y):
        super().__init__(
            x=x, y=y,
            # GAMEPLAY HITBOX: Generous for fair hits
            width=55, height=65,
            max_hp=80,
            attack_power=10,
            speed=2.0,
            asset_path=MUSHROOM_ASSET_PATH,
            scale=1.8
        )
        
        # Combat ranges
        self.detection_range = 250
        self.attack_range = 55
        self.spore_range = 150
        
        # Custom Attack Box
        self.attack_box_width = 65
        self.attack_box_height = 60
        
        # Spore system
        self.spore_cooldown = 0
        self.spore_count = 0
        self.max_spores = 2
        self.force_melee = False
        
        # Spore attack state
        self.is_spore_attacking = False
        self.spore_fired = False
        
        # Combo system (BOD-style)
        self.attack_combo_count = 0
        self.max_combo_before_attack2 = 2  # 2x attack1 then 1x attack2
        self.is_attack2 = False
        
        self._setup_animations()
    
    def _setup_animations(self):
        animation_mapping = {
            'idle': 'idle',
            'walk': 'run',
            'attack': 'attack',
            'attack2': 'attack2',
            # DISABLED: Range/projectile for now - focus on basic actions
            # 'range': 'range',
            'hurt': 'take_hit',
            'die': 'death',
        }
        self.animator.load_sprites(animation_mapping)
        self.animator.animation_speed = 0.12
    
    def update(self, platforms):
        # 1. Update Timers
        self.update_timers()
        
        if self.spore_cooldown > 0:
            self.spore_cooldown -= 1
        
        # 2. Handle hurt state
        current_time = pg.time.get_ticks()
        hurt_timeout = False
        if self.state == 'hurt':
            if current_time - self.last_hit_time > 500:
                hurt_timeout = True
        
        if self.state == 'hurt' and (self.animator.is_animation_finished() or hurt_timeout):
            self.state = 'idle'
            self.ai_state = self.STATE_IDLE
            self.is_attacking = False
            self.is_spore_attacking = False
            self.animator.animation_finished = False
        
        # 3. Run AI if not hurt
        if self.state != 'hurt' and self.alive:
            self._update_ai()
            
            # Map AI state to visual state
            if self.is_spore_attacking:
                self.state = 'range'
            elif self.ai_state in [self.STATE_CHASE, self.STATE_PATROL]:
                self.state = 'walk'
            elif self.ai_state == self.STATE_ATTACK:
                # Combo system: choose attack or attack2
                if self.is_attack2:
                    self.state = 'attack2'
                else:
                    self.state = 'attack'
            elif self.ai_state == self.STATE_IDLE:
                self.state = 'idle'
        
        # 4. Update Physics
        if self.alive:
            self.physics.update(platforms, self.physics.velocity_x, apply_gravity=self.has_gravity)
        else:
            self.physics.update(platforms, 0, apply_gravity=self.has_gravity)
        
        # 5. Avoid player collision
        self.avoid_player_collision()
        
        # 6. Sync rect
        self.rect = self.physics.rect
    
    def _update_ai(self):
        if not self.player_ref or not self.alive:
            self.ai_state = self.STATE_IDLE
            self.physics.velocity_x = 0
            return
            
        # 1. STRICT LOCK: If attacking, freeze velocity and do nothing else
        if self.is_attacking:
            self.physics.velocity_x = 0
            return
        
        distance = self.get_distance_to_player()
        dist_from_spawn = abs(self.rect.x - self.spawn_x)
        direction = self.get_direction_to_player()
        self.facing_right = direction > 0
        
        # DISABLED: Spore attack logic - focus on basic actions first
        # === HANDLE ONGOING SPORE ATTACK ===
        # if self.is_spore_attacking:
        #     if not self.spore_fired and self.animator.frame_index >= 5:
        #         self._fire_spore()
        #         self.spore_fired = True
        #     
        #     if self.animator.is_animation_finished():
        #         self.is_spore_attacking = False
        #         self.spore_fired = False
        #         self.spore_cooldown = self.SPORE_COOLDOWN
        #         self.spore_count += 1
        #         
        #         if self.spore_count >= self.max_spores:
        #             self.force_melee = True
        #     
        #     self.physics.velocity_x = 0
        #     return
        
        # === STATE MACHINE ===
        
        # Outside territory - return
        if dist_from_spawn > self.TERRITORY_RADIUS:
            self.ai_state = self.STATE_PATROL
            self.force_melee = False
            self.spore_count = 0
            self.physics.velocity_x = -direction * self.movement_speed
            return
        
        if distance > self.detection_range:
            self.ai_state = self.STATE_IDLE
            self.force_melee = False
            self.spore_count = 0
            self.physics.velocity_x = 0
            return
        
        if distance <= self.attack_range:
            self.ai_state = self.STATE_ATTACK
            if not self.is_attacking:
                # Combo logic (BOD-style): alternate attack1 and attack2
                if self.attack_combo_count >= self.max_combo_before_attack2:
                    self.is_attack2 = True
                    self.attack_combo_count = 0
                else:
                    self.is_attack2 = False
                    self.attack_combo_count += 1
                
                self.do_attack()
                self.force_melee = False
                self.spore_count = 0
            self.physics.velocity_x = 0
            return
        
        # DISABLED: Force melee and spore attack triggers
        # if self.force_melee:
        #     self.ai_state = self.STATE_CHASE
        #     self.physics.velocity_x = direction * self.movement_speed
        #     return
        # 
        # if (distance < self.spore_range and 
        #     self.spore_cooldown <= 0 and 
        #     self.spore_count < self.max_spores):
        #     self.is_spore_attacking = True
        #     self.spore_fired = False
        #     self.animator.reset_animation()
        #     self.physics.velocity_x = 0
        #     return
        
        # Chase within territory
        if dist_from_spawn < self.TERRITORY_RADIUS:
            self.ai_state = self.STATE_CHASE
            self.physics.velocity_x = direction * self.movement_speed
            return
        
        self.ai_state = self.STATE_IDLE
        self.physics.velocity_x = 0
    
    def _fire_spore(self):
        direction = self.get_direction_to_player()
        
        spawn_x = self.rect.centerx + (direction * 15)
        spawn_y = self.rect.top + 15
        
        pm = ProjectileManager.get_instance()
        pm.spawn_projectile(
            x=spawn_x,
            y=spawn_y,
            direction=direction,
            speed=4,
            damage=8,
            sprite_path=MUSHROOM_PROJECTILE_PATH,
            scale=2.0,
            max_distance=200
        )
        print(f"[MUSHROOM] Spore fired! ({self.spore_count + 1}/{self.max_spores})")
    
    def take_damage(self, amount, apply_stun=False):
        self.is_spore_attacking = False
        self.spore_fired = False
        super().take_damage(int(amount * 0.85), apply_stun=apply_stun)
