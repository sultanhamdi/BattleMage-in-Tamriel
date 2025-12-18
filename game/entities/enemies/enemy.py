import pygame as pg
from game.entities.entities import Entity
from game.components.physics import PhysicsComponent
from game.utils.enemy_animation_handler import EnemyAnimationHandler

class BaseEnemy(Entity):
    """Parent class for all enemy types with AI state machine."""
    
    # AI States
    STATE_IDLE = 'idle'
    STATE_PATROL = 'patrol'
    STATE_CHASE = 'chase'
    STATE_ATTACK = 'attack'
    STATE_HURT = 'hurt'
    STATE_DIE = 'die'
    STATE_APPEAR = 'appear'
    
    # Attack timing - override in child classes
    HIT_FRAME = 3
    ATTACK_BOX_WIDTH = 60
    ATTACK_BOX_HEIGHT = 50
    
    def __init__(self, x, y, width, height, max_hp, attack_power, speed, asset_path, scale=1):
        super().__init__(x=x, y=y, width=width, height=height, max_hp=max_hp, attack_power=attack_power, speed=speed)
        
        self.animator = EnemyAnimationHandler(asset_path, scale)
        self.scale = scale
        self.ai_state = self.STATE_IDLE
        
        # Detection & combat ranges
        self.detection_range = 300
        self.attack_range = 50
        self.lose_interest_range = 400
        
        # Patrol settings
        self.patrol_speed = speed * 0.5
        self.patrol_direction = -1
        self.patrol_distance = 200
        self.spawn_x = x
        
        # References and flags
        self.player_ref = None
        self.facing_right = False
        self.has_gravity = True
        
        # Sprite offsets
        self.sprite_anchor_offset = 0
        self.sprite_offset_y = 0
        
        # Stun mechanic
        self.is_stunned = False
        self.stun_end_time = 0
        self.STUN_DURATION = 2000  # 2 seconds in milliseconds

    # ===========================================
    # SECTION: AI LOGIC (State Machine)
    # ===========================================
    
    def set_player_reference(self, player):
        """
        Set referensi ke Player untuk AI detection.
        Dipanggil dari GameManager saat spawn enemy.
        """
        self.player_ref = player
    
    def get_distance_to_player(self):
        """Return distance to player in pixels."""
        if not self.player_ref or not self.player_ref.alive:
            return float('inf')
        dx = self.player_ref.physics.rect.centerx - self.physics.rect.centerx
        dy = self.player_ref.physics.rect.centery - self.physics.rect.centery
        return (dx**2 + dy**2) ** 0.5
    
    def get_direction_to_player(self):
        """Return 1 if player is right, -1 if left, 0 if no player."""
        if not self.player_ref:
            return 0
        if self.player_ref.physics.rect.centerx > self.physics.rect.centerx:
            return 1
        elif self.player_ref.physics.rect.centerx < self.physics.rect.centerx:
            return -1
        return 0
    
    def update_ai_state(self):
        """Update AI state based on player distance and conditions."""
        # Jangan update AI jika mati
        if not self.alive:
            self.ai_state = self.STATE_DIE
            self.state = 'die'
            return
        
        # Jika sedang hurt, check if hurt state should end
        if self.state == 'hurt':
            # Cannot recover from hurt if still stunned
            if self.is_stunned:
                return  # Stay in hurt state, looping animation
            
            # Hurt ends when invincibility ends OR animation finishes
            if not self.is_invincible or self.animator.is_animation_finished():
                # Hurt finished, return to idle and continue AI
                self.state = 'idle'
                self.ai_state = self.STATE_IDLE
                print(f"[COMBAT] {type(self).__name__} recovered from hurt")
            else:
                return  # Still in hurt state, don't process AI
        
        # Get distance only if player exists
        if not self.player_ref:
            return
        
        distance = self.get_distance_to_player()
        
        # --- STATE: IDLE / PATROL ---
        if self.ai_state in [self.STATE_IDLE, self.STATE_PATROL]:
            # Deteksi player
            if distance < self.detection_range:
                self.ai_state = self.STATE_CHASE
                print(f"[AI] {type(self).__name__} detected player! Chasing...")
        
        # --- STATE: CHASE ---
        elif self.ai_state == self.STATE_CHASE:
            # Player dalam jangkauan attack
            if distance < self.attack_range:
                self.ai_state = self.STATE_ATTACK
            # Player terlalu jauh, kehilangan minat
            elif distance > self.lose_interest_range:
                self.ai_state = self.STATE_IDLE
                print(f"[AI] {type(self).__name__} lost interest in player")
        
        # --- STATE: ATTACK ---
        elif self.ai_state == self.STATE_ATTACK:
            # Kembali ke chase setelah attack selesai
            if not self.is_attacking:
                self.ai_state = self.STATE_CHASE
    
    def execute_ai_behavior(self):
        """
        Eksekusi behavior berdasarkan AI state.
        Returns: x_velocity untuk physics component.
        """
        x_velocity = 0
        
        if self.ai_state == self.STATE_IDLE:
            x_velocity = 0
            self.state = 'idle'
        
        elif self.ai_state == self.STATE_PATROL:
            x_velocity = self.do_patrol()
            self.state = 'walk'
        
        elif self.ai_state == self.STATE_CHASE:
            # Check if already at optimal attack distance - stop instead of getting closer
            distance = self.get_distance_to_player()
            if distance <= self.attack_range:
                # Already in range - stop and switch to attack
                x_velocity = 0
                self.state = 'idle'
            else:
                x_velocity = self.do_chase()
                self.state = 'walk'
        
        elif self.ai_state == self.STATE_ATTACK:
            x_velocity = 0  # Diam saat menyerang
            self.do_attack()
        
        elif self.ai_state == self.STATE_DIE:
            x_velocity = 0
            self.state = 'die'
        
        return x_velocity
    
    def do_patrol(self):
        """
        Logika patrol: Jalan bolak-balik dari titik spawn.
        Returns: x_velocity
        """
        # Cek batas patrol
        if self.rect.x > self.spawn_x + self.patrol_distance:
            self.patrol_direction = -1  # Balik kiri
        elif self.rect.x < self.spawn_x - self.patrol_distance:
            self.patrol_direction = 1   # Balik kanan
        
        # Update facing - TRUE = ke kanan, FALSE = ke kiri
        # patrol_direction: 1 = kanan, -1 = kiri
        self.facing_right = self.patrol_direction > 0
        
        return self.patrol_direction * self.patrol_speed
    
    def do_chase(self):
        """
        Logika chase: Kejar player.
        Returns: x_velocity
        """
        direction = self.get_direction_to_player()
        
        # Update facing - direction: 1 = player di kanan, -1 = player di kiri
        # facing_right = TRUE berarti sprite menghadap kanan
        # Only update facing if NOT currently attacking (prevents sprite jumping mid-attack)
        if not self.is_attacking:
            self.facing_right = direction > 0  # Face towards player
        
        return direction * self.movement_speed
    
    def do_attack(self):
        """
        Logika attack: Serang player jika tidak sedang menyerang.
        Child class bisa override untuk behavior spesifik.
        """
        if not self.is_attacking and self.alive:
            self.is_attacking = True
            self.last_attack_time = pg.time.get_ticks()
            self.state = 'attack'
            self.animator.reset_animation()
    
    def get_attack_hitbox(self):
        """
        Return attack hitbox rect based on facing direction.
        Child classes can override for custom hitbox shapes.
        
        Returns:
            pg.Rect: The attack hitbox rect
        """
        width = getattr(self, 'attack_box_width', self.ATTACK_BOX_WIDTH)
        height = getattr(self, 'attack_box_height', self.ATTACK_BOX_HEIGHT)
        
        if self.facing_right:
            x = self.physics.rect.right
        else:
            x = self.physics.rect.left - width
        
        y = self.physics.rect.centery - height // 2
        
        return pg.Rect(x, y, width, height)
    
    # ===========================================
    # SECTION: UPDATE & DRAW (Override Entity)
    # ===========================================
    
    def update_timers(self):
        """
        Override timer logic untuk Enemy.
        Mirip dengan Entity, tapi cek animation_finished untuk attack.
        """
        current_time = pg.time.get_ticks()
        
        # 1. Cek Invincibility (Hurt state)
        if self.is_invincible:
            # Check if stun is active
            if self.is_stunned:
                if current_time >= self.stun_end_time:
                    # Stun ended
                    self.is_stunned = False
                    print(f"[STUN] {type(self).__name__} recovered from stun!")
                else:
                    # Still stunned - loop hurt animation
                    if self.animator.is_animation_finished():
                        self.animator.reset_animation()  # Loop hurt animation
            
            # Normal invincibility check
            if current_time - self.last_hit_time > self.invincibility_duration:
                self.is_invincible = False
                # Exit hurt state ONLY if not stunned
                if self.state == 'hurt' and self.alive and not self.is_stunned:
                    self.state = 'idle'
                    self.ai_state = self.STATE_IDLE
                    print(f"[COMBAT] {type(self).__name__} recovered from hurt")
        
        # 2. Cek Attack Selesai (berdasarkan animasi)
        if self.is_attacking:
            if self.animator.is_animation_finished():
                self.is_attacking = False
                # Only reset animation_finished if ALIVE - don't touch death animation!
                if self.alive:
                    self.animator.animation_finished = False
                    self.state = 'idle'
    
    def update(self, platforms):
        """        Main update loop untuk Enemy.
        Dipanggil setiap frame dari GameManager.
        
        Args:
            platforms: List of Rect untuk collision detection
        """
        # 1. Update Timers
        self.update_timers()
        
        # 2. Update AI State
        self.update_ai_state()
        
        # 3. Execute AI Behavior & Get Velocity
        x_velocity = self.execute_ai_behavior()
        
        # 4. Update Physics - Apply gravity based on has_gravity flag
        if self.alive:
            self.physics.update(platforms, x_velocity, apply_gravity=self.has_gravity)
        else:
            # Even when dead, apply gravity to fall
            self.physics.update(platforms, 0, apply_gravity=self.has_gravity)
        
        # 5. Avoid overlapping with player (player = wall for enemy)
        self.avoid_player_collision()
        
        # 6. CRITICAL: Sync rect with physics.rect
        self.rect = self.physics.rect
    
    def avoid_player_collision(self):
        """
        Prevent enemy from walking INTO player.
        Only triggers when enemy is actively moving toward player.
        Player CAN walk through enemies freely (no correction when player moves).
        """
        if not self.player_ref or not self.player_ref.alive or not self.alive:
            return
        
        # Only correct if enemy has movement velocity (is actively moving)
        # Use getattr for Skullwolf which uses physics.velocity_x directly
        velocity_x = getattr(self.physics, 'velocity_x', self.physics.velocity.x if hasattr(self.physics, 'velocity') else 0)
        if velocity_x == 0:
            return  # Enemy not moving, player walked into them - no correction
        
        player_rect = self.player_ref.physics.rect
        enemy_rect = self.physics.rect
        
        # Gap to prevent touching
        GAP = 10
        
        if player_rect.colliderect(enemy_rect):
            # Enemy walked into player - back off based on movement direction
            if velocity_x > 0:
                # Enemy was moving RIGHT → stop at LEFT of player
                enemy_rect.right = player_rect.left - GAP
            else:
                # Enemy was moving LEFT → stop at RIGHT of player
                enemy_rect.left = player_rect.right + GAP
            
            # Stop movement (handle both velocity types)
            if hasattr(self.physics, 'velocity_x'):
                self.physics.velocity_x = 0
            if hasattr(self.physics, 'velocity'):
                self.physics.velocity.x = 0
            
            # Sync float position
            self.physics.pos.x = enemy_rect.x
    
    def draw(self, surface, camera_offset):
        """
        Render enemy ke layar.
        Uses same anchor pattern as Player: center horizontal, anchor at bottom.
        
        Args:
            surface: Pygame surface untuk digambar
            camera_offset: Vector2 offset kamera
        """
        # Ambil frame animasi saat ini
        current_frame = self.animator.animate(
            self.state, 
            self.animator.animation_speed, 
            self.facing_right
        )
        
        if current_frame:
            img_width = current_frame.get_width()
            img_height = current_frame.get_height()
            
            # ANCHOR PATTERN:
            # - Center sprite horizontally on hitbox
            # - Anchor at bottom (feet touch ground)
            offset_x = (img_width - self.physics.rect.width) // 2
            
            # Vertical Offset:
            # - Align Bottoms by default (img_height - rect.height)
            # - Apply manual offset (Positive sprite_offset_y = shift sprite UP visually)
            offset_y = (img_height - self.physics.rect.height) - self.sprite_offset_y
            
            # Apply sprite anchor offset for asymmetric sprites
            # When facing left (flipped), invert the anchor offset to prevent sprite jumping
            if self.sprite_anchor_offset != 0:
                if self.facing_right:
                    offset_x += self.sprite_anchor_offset
                else:
                    offset_x -= self.sprite_anchor_offset
            
            draw_pos_x = self.physics.rect.x - camera_offset.x - offset_x
            draw_pos_y = self.physics.rect.y - camera_offset.y - offset_y
            
            surface.blit(current_frame, (draw_pos_x, draw_pos_y))
        else:
            # Fallback: Gambar kotak merah jika tidak ada sprite
            print(f"[WARNING] No sprite for {type(self).__name__} state: {self.state}")
            color = (255, 0, 0)  # Merah untuk enemy
            draw_rect = self.physics.rect.copy()
            draw_rect.x -= camera_offset.x
            draw_rect.y -= camera_offset.y
            pg.draw.rect(surface, color, draw_rect)
    
    def render_sprite(self, camera):
        """
        NEW METHOD: Render enemy sprite with Camera object.
        Compatible with new child class implementations.
        
        Args:
            camera: Camera object with offset attributes
        """
        # NOTE: We intentionally DO NOT skip rendering dead enemies
        # The death animation should play and stay at the last frame
        
        # Ambil frame animasi (TANPA flip, kita flip manual)
        # Use self.state (visual state) not self.ai_state (logic state)
        animation_state = self.state
        
        sprite = self.animator.animate(
            state=animation_state,
            speed=self.animator.animation_speed,
            facing_right=True  # Selalu ambil versi kanan
        )
        
        # Fallback ke idle jika state tidak ditemukan
        if sprite is None:
            sprite = self.animator.animate(
                state='idle',
                speed=self.animator.animation_speed,
                facing_right=True
            )
        
        if sprite:
            # FLIP SPRITE jika facing left (asset default = facing RIGHT)
            if not self.facing_right:
                sprite = pg.transform.flip(sprite, True, False)
            
            # Hitung posisi render dengan offset camera
            render_x = self.physics.rect.x - camera.offset.x
            render_y = self.physics.rect.y - camera.offset.y
            
            # ANCHOR PATTERN (Match draw method):
            offset_x = (img_width - self.physics.rect.width) // 2
            offset_y = (img_height - self.physics.rect.height) - self.sprite_offset_y
            
            # Apply horizontal anchor offset
            if self.sprite_anchor_offset != 0:
                if self.facing_right:
                    offset_x += self.sprite_anchor_offset
                else:
                    offset_x -= self.sprite_anchor_offset
            
            camera.surface.blit(sprite, (render_x - offset_x, render_y - offset_y))
        else:
            # Fallback: Gambar kotak merah jika tidak ada sprite
            color = (255, 0, 0)
            draw_rect = self.physics.rect.copy()
            draw_rect.x -= camera.offset.x
            draw_rect.y -= camera.offset.y
            pg.draw.rect(camera.surface, color, draw_rect)
    
    # ===========================================
    # SECTION: COMBAT (Override dari Entity)
    # ===========================================
    
    def take_damage(self, amount, apply_stun=False):
        """
        Override take_damage untuk enemy.
        Tambahkan state hurt dan knockback.
        
        Args:
            amount: Damage amount
            apply_stun: If True, stun enemy for STUN_DURATION (arcane spell)
        """
        if not self.alive or self.is_invincible:
            return
        
        self.current_hp -= amount
        self.is_invincible = True
        self.last_hit_time = pg.time.get_ticks()
        self.state = 'hurt'
        self.ai_state = self.STATE_HURT
        
        # Apply stun if requested (arcane spell)
        if apply_stun:
            self.is_stunned = True
            self.stun_end_time = pg.time.get_ticks() + self.STUN_DURATION
            print(f"[STUN] {type(self).__name__} is STUNNED for {self.STUN_DURATION/1000}s!")
        
        # Reset animation untuk hurt
        self.animator.reset_animation()
        
        # Cancel any ongoing attacks
        self.is_attacking = False
        
        # Knockback effect (reduced to prevent launching enemies)
        if hasattr(self, 'player_ref') and self.player_ref:
            direction = self.get_direction_to_player()
            knockback_force = -direction * 1.5  # Reduced from 3 to 1.5
            self.physics.velocity_x = knockback_force
        
        print(f"[COMBAT] {type(self).__name__} took {amount} dmg. HP: {self.current_hp}/{self.max_hp}")
        
        if self.current_hp <= 0:
            self.die()
    
    def die(self):
        """
        Override die untuk enemy.
        Set AI state ke DIE.
        """
        self.alive = False
        self.current_hp = 0
        self.ai_state = self.STATE_DIE
        self.state = 'die'
        self.animator.reset_animation()
        print(f"[DEATH] {type(self).__name__} has died.")

