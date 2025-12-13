import pygame as pg
from game.entities.enemies.base_enemy import BaseEnemy

# Path aset lokal untuk Zombie
ZOMBIE_ASSET_PATH = 'assets/graphics/enemies/zombie/'

class Zombie(BaseEnemy):
    """
    Enemy Zombie - Tipe: Melee, Lambat, Jumlah Banyak.
    
    INHERITANCE CHAIN:
    pg.sprite.Sprite -> Entity -> BaseEnemy -> Zombie
    
    KARAKTERISTIK ZOMBIE (dari GDD):
    - Lambat tapi agresif
    - Serangan melee (jarak dekat)
    - HP rendah-menengah
    - AI: Patrol bolak-balik, chase player saat terdeteksi
    
    ANIMASI YANG TERSEDIA:
    - idle (folder: idle/)
    - walk (folder: walk/)
    - attack (folder: attack/)
    - die (folder: die/)
    - appear (folder: appear/)
    """
    
    def __init__(self, x, y):
        """
        Inisialisasi Zombie pada posisi tertentu.
        
        Args:
            x, y: Posisi spawn Zombie
        """
        # 1. TENTUKAN STATS KHUSUS ZOMBIE
        stats_hp = 50       # HP rendah
        stats_attack = 10   # Damage rendah
        stats_speed = 2     # Lambat (Player speed = 8)
        
        # Ukuran hitbox (sesuaikan dengan sprite)
        hitbox_width = 40
        hitbox_height = 64
        
        # Scale untuk sprite (kecilkan agar proporsional dengan player)
        sprite_scale = 0.2
        
        # 2. PANGGIL CONSTRUCTOR PARENT (BaseEnemy)
        super().__init__(
            x=x, y=y,
            width=hitbox_width, height=hitbox_height,
            max_hp=stats_hp,
            attack_power=stats_attack,
            speed=stats_speed,
            asset_path=ZOMBIE_ASSET_PATH,
            scale=sprite_scale
        )
        
        # 3. SETUP ANIMASI
        # Mapping: state_name -> folder_name
        self.animation_mapping = {
            'idle': 'idle',
            'walk': 'walk',
            'attack': 'attack',
            'die': 'die',
            'appear': 'appear',
            'hurt': 'idle'  # Pakai idle untuk hurt (tidak ada aset khusus)
        }
        self.animator.load_sprites(self.animation_mapping)
        
        # 4. AI SETTINGS KHUSUS ZOMBIE
        self.detection_range = 250      # Zombie bisa deteksi dari jarak ini
        self.attack_range = 45          # Jarak untuk menyerang
        self.lose_interest_range = 350  # Berhenti mengejar jika terlalu jauh
        self.patrol_distance = 150      # Jarak patrol dari spawn point
        self.patrol_speed = stats_speed * 0.5  # Patrol lebih lambat
        
        # 5. SET DEFAULT STATE
        # Zombie mulai dengan patrol (lebih dinamis dari idle)
        self.ai_state = self.STATE_PATROL
        self.state = 'walk'
    
    # ===========================================
    # SECTION: OVERRIDE BEHAVIORS
    # ===========================================
    
    def do_chase(self):
        """
        Override chase untuk Zombie.
        Zombie chase dengan kecepatan lebih lambat dari enemy lain.
        
        Returns: x_velocity
        """
        direction = self.get_direction_to_player()
        
        # Update facing direction
        self.facing_right = direction > 0
        self.physics.facing_right = self.facing_right
        
        # Zombie chase speed = movement_speed (sudah lambat dari stats)
        return direction * self.movement_speed
    
    def do_attack(self):
        """
        Override attack untuk Zombie.
        Serangan melee sederhana.
        """
        if not self.is_attacking and self.alive:
            self.is_attacking = True
            self.last_attack_time = pg.time.get_ticks()
            self.state = 'attack'
            self.animator.reset_animation()
            
            # Deal damage ke player jika dalam range
            if self.player_ref and self.player_ref.alive:
                distance = self.get_distance_to_player()
                if distance < self.attack_range + 20:  # Sedikit toleransi
                    self.player_ref.take_damage(self.attack_power)
                    print(f"[COMBAT] Zombie deals {self.attack_power} damage to Player!")
    
    def update_ai_state(self):
        """
        Override AI state untuk Zombie.
        Zombie akan patrol ketika idle, bukan diam di tempat.
        """
        if not self.alive:
            self.ai_state = self.STATE_DIE
            return
        
        # Skip jika sedang hurt
        if self.is_invincible and self.state == 'hurt':
            return
        
        distance = self.get_distance_to_player()
        
        # --- STATE: IDLE (Zombie ubah jadi patrol) ---
        if self.ai_state == self.STATE_IDLE:
            # Zombie selalu patrol, tidak idle diam
            self.ai_state = self.STATE_PATROL
        
        # --- STATE: PATROL ---
        elif self.ai_state == self.STATE_PATROL:
            if distance < self.detection_range:
                self.ai_state = self.STATE_CHASE
        
        # --- STATE: CHASE ---
        elif self.ai_state == self.STATE_CHASE:
            if distance < self.attack_range:
                self.ai_state = self.STATE_ATTACK
            elif distance > self.lose_interest_range:
                self.ai_state = self.STATE_PATROL
        
        # --- STATE: ATTACK ---
        elif self.ai_state == self.STATE_ATTACK:
            if not self.is_attacking:
                # Setelah serang, cek lagi posisi player
                if distance < self.attack_range:
                    self.ai_state = self.STATE_ATTACK
                else:
                    self.ai_state = self.STATE_CHASE

