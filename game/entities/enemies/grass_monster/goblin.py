import pygame as pg
from game.entities.enemies.enemy import BaseEnemy
from game.utils.projectile import ProjectileManager

# Path aset lokal untuk Goblin
GOBLIN_ASSET_PATH = 'assets/graphics/enemies/grass_monster/Goblin/'
GOBLIN_PROJECTILE_PATH = 'assets/graphics/enemies/grass_monster/Goblin/projectile/'

class Goblin(BaseEnemy):
    """
    Enemy Goblin - Versatile Fighter dengan Melee & Range Attack.
    
    BEHAVIOR PATTERN:
    1. Detect player -> Chase
    2. In range -> Start 'range' animation
    3. When animation done -> Fire projectile
    4. After 2 range attacks -> Chase for melee
    5. Melee attack -> Reset counters
    """
    
    # AI CONSTANTS
    PROJECTILE_COOLDOWN = 600  # 10 seconds at 60fps
    
    def __init__(self, x, y):
        super().__init__(
            x=x, y=y,
            # GAMEPLAY HITBOX: Generous for fair hits
            width=50, height=60,
            max_hp=60,
            attack_power=15,
            speed=3.5,
            asset_path=GOBLIN_ASSET_PATH,
            scale=1.8
        )
        
        # Combat ranges
        self.detection_range = 350
        self.attack_range = 55
        self.range_attack_range = 280
        self.lose_interest_range = 450
        
        # Custom Attack Box
        self.attack_box_width = 70
        self.attack_box_height = 60
        
        # Projectile system
        self.projectile_cooldown = 0
        self.range_attack_count = 0
        self.max_range_attacks = 2
        self.force_melee = False
        
        # Range attack STATE
        self.is_range_attacking = False  # True when playing range animation
        self.projectile_fired = False    # True after projectile fired this attack
        
        # Combo system (BOD-style)
        self.attack_combo_count = 0
        self.max_combo_before_attack2 = 2  # 2x attack1 then 1x attack2
        self.is_attack2 = False
        
        self._setup_animations()
    
    def _setup_animations(self):
        """Load animasi Goblin."""
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
        self.animator.animation_speed = 0.15
    
    def update(self, platforms):
        """Main update loop following Skullwolf pattern."""
        # 1. Update Timers
        self.update_timers()
        
        # Cooldown
        if self.projectile_cooldown > 0:
            self.projectile_cooldown -= 1
        
        # 2. Handle hurt state
        current_time = pg.time.get_ticks()
        hurt_timeout = False
        if self.state == 'hurt':
            if current_time - self.last_hit_time > 500:  # Max 0.5s in hurt
                hurt_timeout = True
        
        if self.state == 'hurt' and (self.animator.is_animation_finished() or hurt_timeout):
            self.state = 'idle'
            self.ai_state = self.STATE_IDLE
            self.is_attacking = False
            self.is_range_attacking = False  # Also reset range attack
            self.animator.animation_finished = False
        
        # 3. Run AI if not hurt
        if self.state != 'hurt' and self.alive:
            self._update_ai()
            
            # Map AI state to visual state
            if self.is_range_attacking:
                self.state = 'range'  # Range animation active
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
        else:
            if not self.alive:
                pass  # Dead
            elif self.state == 'hurt':
                pass  # In hurt animation
        
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
        """AI State Machine - Goblin's versatile combat."""
        if not self.player_ref or not self.alive:
            self.ai_state = self.STATE_IDLE
            self.physics.velocity_x = 0
            return
            
        # 1. STRICT LOCK: If attacking, freeze velocity and do nothing else
        if self.is_attacking:
            self.physics.velocity_x = 0
            return
        
        distance = self.get_distance_to_player()
        direction = self.get_direction_to_player()
        self.facing_right = direction > 0
        
        # DISABLED: Range attack logic - focus on basic actions first
        # === HANDLE ONGOING RANGE ATTACK ===
        # if self.is_range_attacking:
        #     # Fire projectile at mid-point of animation (frame 6+)
        #     if not self.projectile_fired and self.animator.frame_index >= 6:
        #         self._fire_projectile()
        #         self.projectile_fired = True
        #     
        #     # Animation finished - end range attack
        #     if self.animator.is_animation_finished():
        #         self.is_range_attacking = False
        #         self.projectile_fired = False
        #         self.projectile_cooldown = self.PROJECTILE_COOLDOWN
        #         self.range_attack_count += 1
        #         
        #         # Check if must go melee
        #         if self.range_attack_count >= self.max_range_attacks:
        #             self.force_melee = True
        #     
        #     self.physics.velocity_x = 0  # Don't move during range attack
        #     return
        
        # === NORMAL STATE MACHINE ===
        
        # Too far - lose interest
        if distance > self.lose_interest_range:
            self.ai_state = self.STATE_IDLE
            self.force_melee = False
            self.range_attack_count = 0
            self.physics.velocity_x = 0
            return
        
        # Not detected yet
        if distance > self.detection_range:
            self.ai_state = self.STATE_IDLE
            self.physics.velocity_x = 0
            return
        
        # In melee range - attack
        if distance <= self.attack_range:
            self.ai_state = self.STATE_ATTACK
            if not self.is_attacking:  # Guard check
                # Combo logic (BOD-style): alternate attack1 and attack2
                if self.attack_combo_count >= self.max_combo_before_attack2:
                    self.is_attack2 = True
                    self.attack_combo_count = 0
                else:
                    self.is_attack2 = False
                    self.attack_combo_count += 1
                
                self.do_attack()
                # Reset after melee
                self.force_melee = False
                self.range_attack_count = 0
            self.physics.velocity_x = 0
            return
        
        # DISABLED: Force melee logic (part of range attack system)
        # if self.force_melee:
        #     self.ai_state = self.STATE_CHASE
        #     self.physics.velocity_x = direction * self.movement_speed
        #     return
        
        # DISABLED: Range attack trigger
        # # Can start range attack?
        # if (distance < self.range_attack_range and 
        #     self.projectile_cooldown <= 0 and 
        #     self.range_attack_count < self.max_range_attacks):
        #     # START range attack animation
        #     self.is_range_attacking = True
        #     self.projectile_fired = False
        #     self.animator.reset_animation()
        #     self.physics.velocity_x = 0
        #     return
        
        # Default - chase
        self.ai_state = self.STATE_CHASE
        self.physics.velocity_x = direction * self.movement_speed
    
    def _fire_projectile(self):
        """Fire projectile during range animation."""
        direction = self.get_direction_to_player()
        
        spawn_x = self.rect.centerx + (direction * 25)
        spawn_y = self.rect.centery
        
        pm = ProjectileManager.get_instance()
        pm.spawn_projectile(
            x=spawn_x,
            y=spawn_y,
            direction=direction,
            speed=6,
            damage=10,
            sprite_path=GOBLIN_PROJECTILE_PATH,
            scale=2.0,
            max_distance=350
        )
        print(f"[GOBLIN] Projectile fired! ({self.range_attack_count + 1}/{self.max_range_attacks})")
    
    def take_damage(self, amount, apply_stun=False):
        """Override - interrupt range attack if hit."""
        self.is_range_attacking = False
        self.projectile_fired = False
        super().take_damage(amount, apply_stun=apply_stun)
