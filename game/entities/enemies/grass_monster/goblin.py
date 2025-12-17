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
    RANGE_COOLDOWN = 420  # 7 seconds at 60fps
    PROJECTILE_SPAWN_FRAME = 6  # Frame in range animation when projectile spawns
    PROJECTILE_IMPACT_FRAME = 12  # Frame in projectile anim where impact starts
    
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
        
        # Range attack system
        self.range_cooldown = 0
        self.is_range_attacking = False  # True when playing range animation
        self.projectile_fired = False    # True after projectile fired this attack
        
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
            'range': 'range',  # Range attack animation
            'hurt': 'take_hit',
            'die': 'death',
        }
        self.animator.load_sprites(animation_mapping)
        self.animator.animation_speed = 0.15
    
    def update(self, platforms):
        """Main update loop following Skullwolf pattern."""
        # 1. Update Timers
        self.update_timers()
        
        # Cooldowns
        if self.range_cooldown > 0:
            self.range_cooldown -= 1
        
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
        """AI State Machine - Goblin's versatile combat with range attack."""
        if not self.player_ref or not self.alive:
            self.ai_state = self.STATE_IDLE
            self.physics.velocity_x = 0
            return
        
        # === HANDLE ONGOING RANGE ATTACK (PRIORITY - like BOD cast) ===
        if self.is_range_attacking:
            self.physics.velocity_x = 0  # Don't move during range attack
            self.ai_state = 'range'
            
            # Fire projectile at spawn frame
            frame_idx = int(self.animator.frame_index)
            if not self.projectile_fired and frame_idx >= self.PROJECTILE_SPAWN_FRAME:
                self._fire_projectile()
                self.projectile_fired = True
            
            # Animation finished - end range attack
            if self.animator.is_animation_finished():
                self.is_range_attacking = False
                self.projectile_fired = False
                self.range_cooldown = self.RANGE_COOLDOWN  # Start 7s cooldown
                print(f"[GOBLIN] Range attack complete, cooldown started")
            return  # Exit early - don't run normal state machine
        
        # 1. STRICT LOCK: If melee attacking, freeze velocity and do nothing else
        if self.is_attacking:
            self.physics.velocity_x = 0
            return
        
        distance = self.get_distance_to_player()
        direction = self.get_direction_to_player()
        self.facing_right = direction > 0
        
        # === PRIORITY: RANGE ATTACK (like BOD spell) ===
        # Trigger BEFORE melee check - range has priority
        if (distance <= self.range_attack_range and 
            distance > self.attack_range and  # Not in melee range
            self.range_cooldown <= 0):
            # INTERRUPT melee attack if any
            if self.is_attacking:
                self.is_attacking = False
                print(f"[GOBLIN] Interrupting attack for range!")
            
            # START range attack animation
            self.is_range_attacking = True
            self.projectile_fired = False
            self.animator.reset_animation()
            self.physics.velocity_x = 0
            self.ai_state = 'range'
            print(f"[GOBLIN] Starting range attack!")
            return
        
        # === NORMAL STATE MACHINE ===
        
        # Too far - lose interest
        if distance > self.lose_interest_range:
            self.ai_state = self.STATE_IDLE
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
            self.physics.velocity_x = 0
            return
        
        # Default - chase
        self.ai_state = self.STATE_CHASE
        self.physics.velocity_x = direction * self.movement_speed
    
    def _fire_projectile(self):
        """Fire projectile during range animation - spawn in front of enemy."""
        direction = self.get_direction_to_player()
        
        # Spawn in front of enemy's bounding box
        if direction > 0:  # Facing right
            spawn_x = self.physics.rect.right + 5
        else:  # Facing left
            spawn_x = self.physics.rect.left - 5
        spawn_y = self.physics.rect.centery
        
        pm = ProjectileManager.get_instance()
        pm.spawn_projectile(
            x=spawn_x,
            y=spawn_y,
            direction=direction,
            speed=8,
            damage=12,
            sprite_path=GOBLIN_PROJECTILE_PATH,
            scale=2.0,
            max_distance=400,
            impact_start_frame=self.PROJECTILE_IMPACT_FRAME
        )
        print(f"[GOBLIN] Projectile fired at ({spawn_x}, {spawn_y})!")
    
    def take_damage(self, amount, apply_stun=False):
        """Override - IMMUNE during range attack (like BOD during cast)."""
        # Immune during range attack animation
        if self.is_range_attacking:
            print(f"[GOBLIN] IMMUNE during range attack!")
            return
        
        super().take_damage(amount, apply_stun=apply_stun)
