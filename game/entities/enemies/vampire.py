import pygame as pg
from game.entities.enemies.base_enemy import BaseEnemy

# Path aset lokal untuk Vampire
VAMPIRE_ASSET_PATH = 'assets/graphics/enemies/vampire/'

class Vampire(BaseEnemy):
    """
    Enemy Vampire - Tipe: Flying, Cepat, Lifesteal.
    
    INHERITANCE CHAIN:
    pg.sprite.Sprite -> Entity -> BaseEnemy -> Vampire
    
    KARAKTERISTIK VAMPIRE (dari GDD):
    - Cepat dan agresif
    - BISA TERBANG (abaikan gravitasi)
    - Punya lifesteal (menyerap HP player saat menyerang)
    - HP menengah
    - AI: Idle/Fly around -> Chase (terbang ke player) -> Attack (lifesteal)
    
    ANIMASI YANG TERSEDIA:
    - idle/walk (folder: walk-idle/) - Share folder
    - attack (folder: attack/)
    - appear/disappear (folder: disappear-appear/) - Share folder
    
    SPECIAL BEHAVIOR:
    - Vampire MENGABAIKAN GRAVITASI (terbang)
    - Vampire bisa bergerak VERTIKAL (naik/turun) mengejar player
    - Serangan vampire menyembuhkan dirinya sendiri (lifesteal)
    """
    
    def __init__(self, x, y):
        """
        Inisialisasi Vampire pada posisi tertentu.
        
        Args:
            x, y: Posisi spawn Vampire
        """
        # 1. TENTUKAN STATS KHUSUS VAMPIRE
        stats_hp = 75       # HP menengah
        stats_attack = 15   # Damage menengah
        stats_speed = 4     # Cepat (2x Zombie)
        
        # Ukuran hitbox
        hitbox_width = 40
        hitbox_height = 50
        
        # Scale untuk sprite (kecilkan agar proporsional dengan player)
        sprite_scale = 0.25
        
        # 2. PANGGIL CONSTRUCTOR PARENT (BaseEnemy)
        super().__init__(
            x=x, y=y,
            width=hitbox_width, height=hitbox_height,
            max_hp=stats_hp,
            attack_power=stats_attack,
            speed=stats_speed,
            asset_path=VAMPIRE_ASSET_PATH,
            scale=sprite_scale
        )
        
        # 3. SETUP ANIMASI
        # Mapping: state_name -> folder_name
        self.animation_mapping = {
            'idle': 'walk-idle',
            'walk': 'walk-idle',
            'fly': 'walk-idle',      # Pakai animasi yang sama untuk terbang
            'attack': 'attack',
            'appear': 'disappear-appear',
            'disappear': 'disappear-appear',
            'hurt': 'walk-idle'
        }
        self.animator.load_sprites(self.animation_mapping)
        
        # 4. AI SETTINGS KHUSUS VAMPIRE
        self.detection_range = 350      # Vampire bisa detect dari jauh
        self.attack_range = 40          # Range attack normal
        self.lose_interest_range = 450  # Vampire mengejar cukup jauh
        self.patrol_distance = 100      # Jarak patrol kecil
        
        # 5. LIFESTEAL SETTINGS
        self.lifesteal_percent = 0.5  # 50% damage dealt = HP recovered
        
        # 6. FLYING SETTINGS
        self.is_flying = True          # Flag untuk physics
        self.vertical_speed = 3        # Kecepatan naik/turun
        self.hover_offset = 0          # Untuk efek hover naik-turun
        self.hover_direction = 1       # 1 = naik, -1 = turun
        self.hover_range = 20          # Jarak hover
        
        # 7. SET DEFAULT STATE
        self.ai_state = self.STATE_IDLE
        self.state = 'idle'
    
    # ===========================================
    # SECTION: OVERRIDE PHYSICS (Flying)
    # ===========================================
    
    def update(self, platforms):
        """
        Override update untuk Vampire.
        Vampire mengabaikan gravitasi (terbang).
        """
        # 1. Update Timers
        self.update_timers()
        
        # 2. Update AI State
        self.update_ai_state()
        
        # 3. Execute AI Behavior & Get Velocities
        x_velocity, y_velocity = self.execute_ai_behavior_flying()
        
        # 4. Update Position TANPA Gravitasi (Custom Flying Physics)
        if self.alive:
            self.update_flying_physics(platforms, x_velocity, y_velocity)
            self.facing_right = self.physics.facing_right
    
    def update_flying_physics(self, platforms, x_velocity, y_velocity):
        """
        Custom physics untuk vampire yang terbang.
        Tidak pakai gravitasi, bisa bergerak vertikal.
        """
        # Update posisi horizontal
        self.physics.pos.x += x_velocity
        self.rect.x = round(self.physics.pos.x)
        
        # Update facing direction
        if x_velocity > 0:
            self.physics.facing_right = True
        elif x_velocity < 0:
            self.physics.facing_right = False
        
        # Collision horizontal
        for platform in platforms:
            if self.rect.colliderect(platform):
                if x_velocity > 0:
                    self.rect.right = platform.left
                elif x_velocity < 0:
                    self.rect.left = platform.right
                self.physics.pos.x = self.rect.x
        
        # Update posisi vertikal (VAMPIRE BISA TERBANG)
        self.physics.pos.y += y_velocity
        self.rect.y = round(self.physics.pos.y)
        
        # Collision vertikal
        for platform in platforms:
            if self.rect.colliderect(platform):
                if y_velocity > 0:
                    self.rect.bottom = platform.top
                elif y_velocity < 0:
                    self.rect.top = platform.bottom
                self.physics.pos.y = self.rect.y
    
    # ===========================================
    # SECTION: OVERRIDE AI BEHAVIOR (Flying)
    # ===========================================
    
    def execute_ai_behavior_flying(self):
        """
        Execute AI behavior dengan support vertical movement.
        Returns: (x_velocity, y_velocity)
        """
        x_velocity = 0
        y_velocity = 0
        
        if self.ai_state == self.STATE_IDLE:
            x_velocity = 0
            y_velocity = self.do_hover()  # Vampire hover saat idle
            self.state = 'idle'
        
        elif self.ai_state == self.STATE_PATROL:
            x_velocity = self.do_patrol()
            y_velocity = self.do_hover()
            self.state = 'fly'
        
        elif self.ai_state == self.STATE_CHASE:
            x_velocity, y_velocity = self.do_chase_flying()
            self.state = 'fly'
        
        elif self.ai_state == self.STATE_ATTACK:
            x_velocity = 0
            y_velocity = 0
            self.do_attack()
        
        elif self.ai_state == self.STATE_DIE:
            x_velocity = 0
            y_velocity = 2  # Jatuh saat mati
            self.state = 'disappear'
        
        return x_velocity, y_velocity
    
    def do_hover(self):
        """
        Efek hover naik-turun saat idle/patrol.
        Returns: y_velocity
        """
        # Update hover offset
        self.hover_offset += self.hover_direction * 0.5
        
        # Balik arah jika sudah mencapai batas
        if self.hover_offset >= self.hover_range:
            self.hover_direction = -1
        elif self.hover_offset <= -self.hover_range:
            self.hover_direction = 1
        
        return self.hover_direction * 0.5
    
    def do_chase_flying(self):
        """
        Chase player dengan kemampuan terbang.
        Vampire bisa mengejar secara horizontal DAN vertikal.
        
        Returns: (x_velocity, y_velocity)
        """
        if not self.player_ref:
            return 0, 0
        
        # Hitung arah ke player (X dan Y)
        dx = self.player_ref.rect.centerx - self.rect.centerx
        dy = self.player_ref.rect.centery - self.rect.centery
        
        # Normalize untuk diagonal movement yang smooth
        distance = max(1, (dx**2 + dy**2) ** 0.5)
        
        # Hitung velocity
        x_velocity = (dx / distance) * self.movement_speed
        y_velocity = (dy / distance) * self.vertical_speed
        
        # Update facing
        self.facing_right = dx > 0
        self.physics.facing_right = self.facing_right
        
        return x_velocity, y_velocity
    
    def update_ai_state(self):
        """
        Override AI state untuk Vampire.
        Sama dengan base tapi vampire lebih agresif.
        """
        if not self.alive:
            self.ai_state = self.STATE_DIE
            return
        
        if self.is_invincible and self.state == 'hurt':
            return
        
        distance = self.get_distance_to_player()
        
        # --- STATE: IDLE ---
        if self.ai_state == self.STATE_IDLE:
            if distance < self.detection_range:
                self.ai_state = self.STATE_CHASE
        
        # --- STATE: PATROL ---
        elif self.ai_state == self.STATE_PATROL:
            if distance < self.detection_range:
                self.ai_state = self.STATE_CHASE
        
        # --- STATE: CHASE ---
        elif self.ai_state == self.STATE_CHASE:
            if distance < self.attack_range:
                self.ai_state = self.STATE_ATTACK
            elif distance > self.lose_interest_range:
                self.ai_state = self.STATE_IDLE
        
        # --- STATE: ATTACK ---
        elif self.ai_state == self.STATE_ATTACK:
            if not self.is_attacking:
                if distance < self.attack_range:
                    self.ai_state = self.STATE_ATTACK
                else:
                    self.ai_state = self.STATE_CHASE
    
    # ===========================================
    # SECTION: OVERRIDE ATTACK (Lifesteal)
    # ===========================================
    
    def do_attack(self):
        """
        Override attack untuk Vampire.
        Serangan dengan LIFESTEAL - menyerap HP player.
        """
        if not self.is_attacking and self.alive:
            self.is_attacking = True
            self.last_attack_time = pg.time.get_ticks()
            self.state = 'attack'
            self.animator.reset_animation()
            
            # Deal damage ke player dan LIFESTEAL
            if self.player_ref and self.player_ref.alive:
                distance = self.get_distance_to_player()
                if distance < self.attack_range + 20:
                    # Deal damage
                    self.player_ref.take_damage(self.attack_power)
                    
                    # LIFESTEAL: Recover HP
                    heal_amount = int(self.attack_power * self.lifesteal_percent)
                    self.current_hp = min(self.max_hp, self.current_hp + heal_amount)
                    
                    print(f"[COMBAT] Vampire drains {self.attack_power} damage from Player!")
                    print(f"[LIFESTEAL] Vampire heals {heal_amount} HP! HP: {self.current_hp}/{self.max_hp}")

