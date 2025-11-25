import pygame as pg
from game.settings import BLUE
from game.entities.entities import Entity # Import Parent Class
from game.utils.player_animation_handler import PlayerAnimationHandler

# Path aset lokal untuk player
PLAYER_ASSET_PATH = 'assets/graphics/player/'

class Player(Entity): 
    def __init__(self, x, y):
        # 1. TENTUKAN STATS KHUSUS PLAYER DI SINI
        stats_hp = 100
        stats_attack = 25
        stats_speed = 5

        # 2. INIT PARENT
        # Kirim stats di atas ke Parent Class (Entity)
        super().__init__(
            x=x, y=y, 
            width=40, height=80,    # Ukuran Hitbox Fisika
            max_hp=stats_hp, 
            attack_power=stats_attack, 
            speed=stats_speed
        )
        
        # 3. SETUP VISUAL (Tugas Child)
        self.frame_width = 56   
        self.frame_height = 48  
        self.scale = 3 
        
        self.animator = PlayerAnimationHandler(PLAYER_ASSET_PATH, self.frame_width, self.frame_height, self.scale)
        
        # Memuat semua jenis animasi termasuk combo attack
        self.animation_types = ['idle', 'run', 'jump', 'fall', 'attack1', 'attack2', 'attack3', 'death', 'hurt']
        self.animator.load_sprites(self.animation_types)

        # 4. SETUP COMBO SYSTEM
        self.combo_count = 1      # Melacak urutan serangan (1 -> 2 -> 3)
        self.combo_window = 1000  # Waktu toleransi (ms) untuk lanjut ke combo berikutnya

    def update_timers(self):
        """
        [OVERRIDE PARENT] 
        Kita ganti logika timer parent khusus untuk Player.
        PENTING: Player selesai menyerang BUKAN berdasarkan waktu (400ms),
        tapi berdasarkan selesainya animasi dari AnimationHandler.
        """
        current_time = pg.time.get_ticks()
        
        # 1. Cek Invincibility (Sama seperti parent)
        if self.is_invincible:
            if current_time - self.last_hit_time > self.invincibility_duration:
                self.is_invincible = False

        # 2. [BARU] Cek Attack Selesai Berdasarkan Animasi
        # Ini mencegah animasi terpotong di tengah jalan
        if self.is_attacking:
            # Cek ke animator: "Apakah animasi attack sudah kelar?"
            # Pastikan di player_animation_handler.py ada variabel self.animation_finished
            if self.animator.animation_finished:
                self.is_attacking = False
                self.animator.animation_finished = False # Reset flag
                
                # Jika animasi selesai, kembali ke idle jika masih hidup
                if self.alive:
                    self.state = 'idle'

    def get_input(self):
        """Mengambil input keyboard khusus Player"""
        if not self.alive: return 0

        keys = pg.key.get_pressed()
        x_velocity = 0
        
        # Gerak Kiri Kanan
        if keys[pg.K_LEFT] or keys[pg.K_a]:
            x_velocity = -self.movement_speed
        if keys[pg.K_RIGHT] or keys[pg.K_d]:
            x_velocity = self.movement_speed
            
        # Input Serangan (Tombol J)
        if keys[pg.K_j]:
            self.attack() 
            
        return x_velocity

    def attack(self):
        """
        Override method attack() milik Parent untuk logika Combo.
        """
        # Jangan menyerang jika sedang menyerang (tunggu animasi selesai) atau mati
        if self.is_attacking or not self.alive:
            return

        current_time = pg.time.get_ticks()
        time_since_last = current_time - self.last_attack_time

        # --- LOGIKA COMBO ---
        # Jika waktu antar serangan masih dalam toleransi window, lanjut combo
        if time_since_last < self.combo_window:
            self.combo_count += 1
        else:
            self.combo_count = 1 # Reset ke serangan pertama jika terlalu lama

        # Jika combo melebihi 3, reset balik ke 1
        if self.combo_count > 3:
            self.combo_count = 1
            
        # Set State Parent
        self.is_attacking = True
        self.last_attack_time = current_time
        
        # Reset animator agar animasi mulai dari frame 0 lagi (PENTING)
        self.animator.frame_index = 0
        self.animator.animation_finished = False
        
        # Tentukan animasi berdasarkan combo_count
        self.state = f'attack{self.combo_count}' 
        
        print(f"[ACTION] Player performs Combo #{self.combo_count} ({self.state})")

    def get_status(self, x_velocity):
        """Menentukan State Animasi berdasarkan kondisi Fisika & Combat"""
        if not self.alive:
            self.state = 'death'
            return

        # Prioritas 1: Attack (Pastikan nama state sesuai combo)
        if self.is_attacking:
            self.state = f'attack{self.combo_count}'
            return
        
        if self.is_invincible and self.state == 'hurt': 
            return

        # Prioritas 2: Udara (Fisika)
        if self.physics.velocity.y < 0:
            self.state = 'jump'
        elif self.physics.velocity.y > 1:
            self.state = 'fall'
        
        # Prioritas 3: Tanah
        else:
            if x_velocity != 0 and self.physics.on_ground: 
                 self.state = 'run'
            elif self.physics.on_ground: 
                 self.state = 'idle'

    def jump(self):
        # Override jump untuk memastikan tidak lompat saat serang/mati
        if self.alive and not self.is_attacking:
            self.physics.jump()

    def update(self, platforms):
        # 1. Panggil update_timers milik PLAYER (yang sudah di-override)
        # Jangan panggil super().update() karena kita ingin pakai logika timer kita sendiri
        self.update_timers()
        
        # 2. Logika Gerak Child
        x_vel = self.get_input()
        
        if self.alive:
            # Update Fisika (Komponen milik Parent)
            self.physics.update(platforms, x_vel)
        
        # 3. Update State Animasi
        self.get_status(x_vel)

    def draw(self, surface, camera_offset):
        # 4. Render (Logika gambar Child menggunakan Animator)
        current_frame = self.animator.animate(self.state, 0.1, self.physics.facing_right)

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
            # Fallback (Kotak Biru)
            color = BLUE
            draw_rect = self.rect.copy()
            draw_rect.x -= camera_offset.x
            draw_rect.y -= camera_offset.y
            pg.draw.rect(surface, color, draw_rect)