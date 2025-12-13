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
        self.patrol_direction = 1  # 1 = kanan, -1 = kiri
        self.patrol_distance = 200  # Jarak patrol dari titik spawn
        self.spawn_x = x  # Simpan posisi spawn untuk patrol
        
        # 6. REFERENCE KE PLAYER (akan di-set dari GameManager)
        self.player_ref = None
        
        # 7. FACING DIRECTION (untuk animasi)
        # Override dari physics component agar konsisten
        self.facing_right = True

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
        
        # Hitung jarak horizontal (untuk game platformer, biasanya cukup X)
        dx = self.player_ref.rect.centerx - self.rect.centerx
        dy = self.player_ref.rect.centery - self.rect.centery
        
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
        
        if self.player_ref.rect.centerx > self.rect.centerx:
            return 1  # Player di kanan
        elif self.player_ref.rect.centerx < self.rect.centerx:
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
        # Jangan update AI jika mati atau sedang hurt
        if not self.alive:
            self.ai_state = self.STATE_DIE
            return
        
        if self.is_invincible and self.state == 'hurt':
            return  # Tetap di state hurt sampai invincibility habis
        
        distance = self.get_distance_to_player()
        
        # --- STATE: IDLE / PATROL ---
        if self.ai_state in [self.STATE_IDLE, self.STATE_PATROL]:
            # Deteksi player
            if distance < self.detection_range:
                self.ai_state = self.STATE_CHASE
        
        # --- STATE: CHASE ---
        elif self.ai_state == self.STATE_CHASE:
            # Player dalam jangkauan attack
            if distance < self.attack_range:
                self.ai_state = self.STATE_ATTACK
            # Player terlalu jauh, kehilangan minat
            elif distance > self.lose_interest_range:
                self.ai_state = self.STATE_IDLE
        
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
        
        # Update facing
        self.facing_right = self.patrol_direction > 0
        self.physics.facing_right = self.facing_right
        
        return self.patrol_direction * self.patrol_speed
    
    def do_chase(self):
        """
        Logika chase: Kejar player.
        Returns: x_velocity
        """
        direction = self.get_direction_to_player()
        
        # Update facing
        self.facing_right = direction > 0
        self.physics.facing_right = self.facing_right
        
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
        
        # 1. Cek Invincibility
        if self.is_invincible:
            if current_time - self.last_hit_time > self.invincibility_duration:
                self.is_invincible = False
        
        # 2. Cek Attack Selesai (berdasarkan animasi)
        if self.is_attacking:
            if self.animator.is_animation_finished():
                self.is_attacking = False
                self.animator.animation_finished = False
                if self.alive:
                    self.state = 'idle'
    
    def update(self, platforms):
        """
        Main update loop untuk Enemy.
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
        
        # 4. Update Physics (jika masih hidup)
        if self.alive:
            self.physics.update(platforms, x_velocity)
            # Sync facing dari physics
            self.facing_right = self.physics.facing_right
    
    def draw(self, surface, camera_offset):
        """
        Render enemy ke layar.
        
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
            
            # Hitung offset agar gambar pas di tengah hitbox
            offset_x = (img_width - self.rect.width) // 2
            offset_y = img_height - self.rect.height
            
            draw_pos_x = self.rect.x - camera_offset.x - offset_x
            draw_pos_y = self.rect.y - camera_offset.y - offset_y
            
            surface.blit(current_frame, (draw_pos_x, draw_pos_y))
        else:
            # Fallback: Gambar kotak merah jika tidak ada sprite
            color = (255, 0, 0)  # Merah untuk enemy
            draw_rect = self.rect.copy()
            draw_rect.x -= camera_offset.x
            draw_rect.y -= camera_offset.y
            pg.draw.rect(surface, color, draw_rect)
    
    # ===========================================
    # SECTION: COMBAT (Override dari Entity)
    # ===========================================
    
    def take_damage(self, amount):
        """
        Override take_damage untuk enemy.
        Tambahkan state hurt.
        """
        if not self.alive or self.is_invincible:
            return
        
        self.current_hp -= amount
        self.is_invincible = True
        self.last_hit_time = pg.time.get_ticks()
        self.state = 'hurt'
        
        # Reset AI state sementara
        self.ai_state = self.STATE_IDLE
        
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

