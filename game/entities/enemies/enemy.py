import pygame as pg
from game.entities.entities import Entity
from game.utils.enemy_animation_handler import EnemyAnimationHandler

class BaseEnemy(Entity):
    """
    Parent Class (Blueprint) untuk semua jenis Enemy.
    Mewarisi dari Entity dan menambahkan logika AI.
    
    INHERITANCE CHAIN:
    pg.sprite.Sprite -> Entity -> BaseEnemy -> Zombie/Vampire/Golem
    
    FITUR YANG DITAMBAHKAN:
    1. AI State Machine (IDLE, PATROL, CHASE, ATTACK)
    2. Player Detection (jarak untuk mendeteksi player)
    3. Patrol Logic (bolak-balik dalam area tertentu)
    4. Chase Logic (mengejar player)
    
    Child class (Zombie, Vampire, Golem) akan:
    - Override stats (HP, damage, speed)
    - Override behavior tertentu (misal: Vampire bisa terbang)
    - Setup animasi sendiri
    """
    
    # --- KONSTANTA AI STATE ---
    STATE_IDLE = 'idle'
    STATE_PATROL = 'patrol'
    STATE_CHASE = 'chase'
    STATE_ATTACK = 'attack'
    STATE_HURT = 'hurt'
    STATE_DIE = 'die'
    STATE_APPEAR = 'appear'  # Khusus Golem
    
    def __init__(self, x, y, width, height, max_hp, attack_power, speed, asset_path, scale=1):
        """
        Inisialisasi Base Enemy.
        
        Args:
            x, y: Posisi spawn
            width, height: Ukuran hitbox fisika
            max_hp: HP maksimal
            attack_power: Damage serangan
            speed: Kecepatan gerak
            asset_path: Path ke folder asset enemy
            scale: Skala pembesaran sprite
        """
        # 1. PANGGIL CONSTRUCTOR PARENT (Entity)
        super().__init__(
            x=x, y=y,
            width=width, height=height,
            max_hp=max_hp,
            attack_power=attack_power,
            speed=speed
        )
        
        # 2. SETUP ANIMATOR (Tugas Child untuk load sprites)
        self.animator = EnemyAnimationHandler(asset_path, scale)
        self.scale = scale
        
        # 3. AI STATE MACHINE
        self.ai_state = self.STATE_IDLE
        
        # 4. DETECTION & COMBAT RANGES
        self.detection_range = 300  # Jarak deteksi player (pixel)
        self.attack_range = 50      # Jarak untuk menyerang (pixel)
        self.lose_interest_range = 400  # Jarak untuk berhenti mengejar
        
        # 5. PATROL SETTINGS
        self.patrol_speed = speed * 0.5  # Patrol lebih lambat dari chase
        self.patrol_direction = -1  # 1 = kanan, -1 = kiri (START LEFT)
        self.patrol_distance = 200  # Jarak patrol dari titik spawn
        self.spawn_x = x  # Simpan posisi spawn untuk patrol
        
        # 6. REFERENCE KE PLAYER (akan di-set dari GameManager)
        self.player_ref = None
        
        # 7. FACING DIRECTION (untuk animasi)
        # Override dari physics component agar konsisten
        self.facing_right = False  # START FACING LEFT (sprites default kanan)
        
        # 8. GRAVITY FLAG (child class bisa disable untuk flying)
        self.has_gravity = True  # Most enemies need gravity

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
        """
        Hitung jarak ke player.
        Returns: Jarak dalam pixel, atau float('inf') jika tidak ada player.
        """
        if not self.player_ref or not self.player_ref.alive:
            return float('inf')
        
        # USE PHYSICS.RECT for accurate positions
        dx = self.player_ref.physics.rect.centerx - self.physics.rect.centerx
        dy = self.player_ref.physics.rect.centery - self.physics.rect.centery
        
        # Euclidean distance
        distance = (dx**2 + dy**2) ** 0.5
        return distance
    
    def get_direction_to_player(self):
        """
        Tentukan arah ke player.
        Returns: 1 jika player di kanan, -1 jika di kiri, 0 jika tidak ada player.
        """
        if not self.player_ref:
            return 0
        
        # USE PHYSICS.RECT for accurate positions
        if self.player_ref.physics.rect.centerx > self.physics.rect.centerx:
            return 1  # Player di kanan
        elif self.player_ref.physics.rect.centerx < self.physics.rect.centerx:
            return -1  # Player di kiri
        return 0
    
    def update_ai_state(self):
        """
        Update AI State berdasarkan kondisi.
        Ini adalah LOGIKA DASAR yang bisa di-override oleh child class.
        
        STATE TRANSITIONS:
        IDLE -> CHASE (player terdeteksi)
        CHASE -> ATTACK (player dalam jangkauan)
        CHASE -> IDLE (player terlalu jauh)
        ATTACK -> CHASE (setelah attack selesai)
        """
        # Jangan update AI jika mati
        if not self.alive:
            self.ai_state = self.STATE_DIE
            self.state = 'die'
            return
        
        # Jika sedang hurt, tunggu sampai invincibility habis
        if self.is_invincible and self.state == 'hurt':
            # Check if hurt animation should finish
            if not self.is_invincible:
                # Hurt finished, return to previous state
                self.state = 'idle'
                self.ai_state = self.STATE_IDLE
            return  # Don't process other states while hurt
        
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
            x_velocity = self.do_chase()
            self.state = 'walk'
        
        elif self.ai_state == self.STATE_ATTACK:
            x_velocity = 0  # Diam saat menyerang
            self.do_attack()
        
        elif self.ai_state == self.STATE_DIE:
            x_velocity = 0
            self.state = 'die'
        
        return x_velocity
    
    # ===========================================
    # SECTION: AI BEHAVIORS (bisa di-override)
    # ===========================================
    
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
        
        # Update facing - TRUE = ke kanan, FALSE = ke kiri
        # direction: 1 = kanan, -1 = kiri
        self.facing_right = direction > 0
        
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
            print(f"[ACTION] {type(self).__name__} Attacks!")
    
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
            if current_time - self.last_hit_time > self.invincibility_duration:
                self.is_invincible = False
                # Exit hurt state
                if self.state == 'hurt' and self.alive:
                    self.state = 'idle'
                    self.ai_state = self.STATE_IDLE
                    print(f"[COMBAT] {type(self).__name__} recovered from hurt")
        
        # 2. Cek Attack Selesai (berdasarkan animasi)
        if self.is_attacking:
            if self.animator.is_animation_finished():
                self.is_attacking = False
                self.animator.animation_finished = False
                if self.alive:
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
        
        # 4. Update Physics - ALWAYS APPLY GRAVITY for ground enemies
        if self.alive:
            self.physics.update(platforms, x_velocity, apply_gravity=True)
        else:
            # Even when dead, apply gravity to fall
            self.physics.update(platforms, 0, apply_gravity=True)
        
        # 5. CRITICAL: Sync rect with physics.rect
        self.rect = self.physics.rect
    
    def draw(self, surface, camera_offset):
        """
        Render enemy ke layar.
        
        Args:
            surface: Pygame surface untuk digambar
            camera_offset: Vector2 offset kamera
        """
        # Don't render if dead and animation finished
        if not self.alive and self.animator.is_animation_finished():
            return
        
        # Ambil frame animasi saat ini
        current_frame = self.animator.animate(
            self.state, 
            self.animator.animation_speed, 
            self.facing_right
        )
        
        if current_frame:
            img_width = current_frame.get_width()
            img_height = current_frame.get_height()
            
            # Hitung offset agar gambar pas di tengah hitbox
            offset_x = (img_width - self.physics.rect.width) // 2
            offset_y = img_height - self.physics.rect.height
            
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
        if not self.alive and self.animator.is_animation_finished():
            return  # Jangan render jika mati dan animasi selesai
        
        # Ambil frame animasi (TANPA flip, kita flip manual)
        sprite = self.animator.animate(
            state=self.ai_state,
            speed=self.animator.animation_speed,
            facing_right=True  # Selalu ambil versi kanan
        )
        
        if sprite:
            # FLIP SPRITE jika facing left
            if not self.facing_right:
                sprite = pg.transform.flip(sprite, True, False)
            
            # Hitung posisi render dengan offset camera
            render_x = self.physics.rect.x - camera.offset.x
            render_y = self.physics.rect.y - camera.offset.y
            
            # Center sprite di hitbox
            sprite_offset_x = (sprite.get_width() - self.physics.rect.width) // 2
            sprite_offset_y = (sprite.get_height() - self.physics.rect.height) // 2
            
            camera.surface.blit(sprite, (render_x - sprite_offset_x, render_y - sprite_offset_y))
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
    
    def take_damage(self, amount):
        """
        Override take_damage untuk enemy.
        Tambahkan state hurt dan knockback.
        """
        if not self.alive or self.is_invincible:
            return
        
        self.current_hp -= amount
        self.is_invincible = True
        self.last_hit_time = pg.time.get_ticks()
        self.state = 'hurt'
        self.ai_state = self.STATE_HURT
        
        # Reset animation untuk hurt
        self.animator.reset_animation()
        
        # Cancel any ongoing attacks
        self.is_attacking = False
        
        # Knockback effect (optional)
        if hasattr(self, 'player_ref') and self.player_ref:
            direction = self.get_direction_to_player()
            knockback_force = -direction * 3  # Push away from player
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

