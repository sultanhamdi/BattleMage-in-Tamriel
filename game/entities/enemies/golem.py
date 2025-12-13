import pygame as pg
from game.entities.enemies.base_enemy import BaseEnemy

# Path aset lokal untuk Golem
GOLEM_ASSET_PATH = 'assets/graphics/enemies/golem/'

class Golem(BaseEnemy):
    """
    Enemy Golem - Tipe: Tank, Lambat, HP Tebal, Serangan Berat.
    
    INHERITANCE CHAIN:
    pg.sprite.Sprite -> Entity -> BaseEnemy -> Golem
    
    KARAKTERISTIK GOLEM (dari GDD):
    - Sangat lambat tapi HP sangat tebal
    - Serangan area berat (damage tinggi)
    - Punya animasi "appear" saat pertama kali detect player
    - AI: Idle sampai player datang -> Appear -> Chase -> Attack
    
    ANIMASI YANG TERSEDIA:
    - idle/walk (folder: idle-walk/) - Share folder
    - attack (folder: attack/)
    - die (folder: die/)
    - appear (folder: appear/)
    
    SPECIAL BEHAVIOR:
    - Golem mulai dalam state IDLE (diam seperti batu)
    - Saat player mendekat, Golem "bangun" (APPEAR animation)
    - Setelah appear selesai, baru chase player
    """
    
    def __init__(self, x, y):
        """
        Inisialisasi Golem pada posisi tertentu.
        
        Args:
            x, y: Posisi spawn Golem
        """
        # 1. TENTUKAN STATS KHUSUS GOLEM
        stats_hp = 150      # HP sangat tebal (3x Zombie)
        stats_attack = 25   # Damage tinggi (2.5x Zombie)
        stats_speed = 1.5   # Sangat lambat
        
        # Ukuran hitbox (Golem lebih besar)
        hitbox_width = 60
        hitbox_height = 80
        
        # Scale untuk sprite (Golem = Tank, lebih besar dari enemy lain)
        sprite_scale = 0.35
        
        # 2. PANGGIL CONSTRUCTOR PARENT (BaseEnemy)
        super().__init__(
            x=x, y=y,
            width=hitbox_width, height=hitbox_height,
            max_hp=stats_hp,
            attack_power=stats_attack,
            speed=stats_speed,
            asset_path=GOLEM_ASSET_PATH,
            scale=sprite_scale
        )
        
        # 3. SETUP ANIMASI
        # Mapping: state_name -> folder_name
        # Note: idle dan walk share folder 'idle-walk'
        self.animation_mapping = {
            'idle': 'idle-walk',
            'walk': 'idle-walk',
            'attack': 'attack',
            'die': 'die',
            'appear': 'appear',
            'hurt': 'idle-walk'  # Pakai idle untuk hurt
        }
        self.animator.load_sprites(self.animation_mapping)
        
        # 4. AI SETTINGS KHUSUS GOLEM
        self.detection_range = 200      # Golem detect dari jarak dekat (dia besar jadi player gampang liat)
        self.attack_range = 70          # Range lebih besar (tangan golem panjang)
        self.lose_interest_range = 300  # Golem tidak mengejar jauh (malas)
        self.patrol_distance = 0        # Golem TIDAK patrol (diam di tempat)
        
        # 5. SPECIAL STATE: HAS APPEARED
        # Golem perlu "bangun" dulu sebelum bisa bergerak
        self.has_appeared = False
        
        # 6. SET DEFAULT STATE
        # Golem mulai dalam state IDLE (tidur)
        self.ai_state = self.STATE_IDLE
        self.state = 'idle'
    
    # ===========================================
    # SECTION: OVERRIDE AI STATE MACHINE
    # ===========================================
    
    def update_ai_state(self):
        """
        Override AI state untuk Golem.
        Golem punya state tambahan: APPEAR (bangun dari tidur).
        
        STATE TRANSITIONS:
        IDLE -> APPEAR (player terdeteksi, golem belum bangun)
        APPEAR -> CHASE (animasi appear selesai)
        CHASE -> ATTACK (player dalam jangkauan)
        ATTACK -> CHASE (setelah attack selesai)
        """
        if not self.alive:
            self.ai_state = self.STATE_DIE
            return
        
        # Skip jika sedang hurt
        if self.is_invincible and self.state == 'hurt':
            return
        
        distance = self.get_distance_to_player()
        
        # --- STATE: IDLE (Golem Tidur) ---
        if self.ai_state == self.STATE_IDLE:
            if distance < self.detection_range:
                # Player mendekat!
                if not self.has_appeared:
                    # Golem belum bangun, mainkan animasi appear
                    self.ai_state = self.STATE_APPEAR
                    self.state = 'appear'
                    self.animator.reset_animation()
                    print(f"[AI] Golem detected player! Starting APPEAR animation...")
                else:
                    # Sudah pernah bangun, langsung chase
                    self.ai_state = self.STATE_CHASE
        
        # --- STATE: APPEAR (Golem Bangun) ---
        elif self.ai_state == self.STATE_APPEAR:
            # Tunggu animasi appear selesai
            if self.animator.is_animation_finished():
                self.has_appeared = True
                self.ai_state = self.STATE_CHASE
                print(f"[AI] Golem APPEAR complete! Now chasing...")
        
        # --- STATE: CHASE ---
        elif self.ai_state == self.STATE_CHASE:
            if distance < self.attack_range:
                self.ai_state = self.STATE_ATTACK
            elif distance > self.lose_interest_range:
                # Golem kembali idle tapi tetap "bangun" (tidak perlu appear lagi)
                self.ai_state = self.STATE_IDLE
        
        # --- STATE: ATTACK ---
        elif self.ai_state == self.STATE_ATTACK:
            if not self.is_attacking:
                if distance < self.attack_range:
                    # Serang lagi
                    self.ai_state = self.STATE_ATTACK
                else:
                    self.ai_state = self.STATE_CHASE
    
    def execute_ai_behavior(self):
        """
        Override execute behavior untuk Golem.
        Tambahkan handling untuk state APPEAR.
        """
        x_velocity = 0
        
        if self.ai_state == self.STATE_IDLE:
            x_velocity = 0
            self.state = 'idle'
        
        elif self.ai_state == self.STATE_APPEAR:
            # Golem diam saat animasi appear
            x_velocity = 0
            self.state = 'appear'
        
        elif self.ai_state == self.STATE_CHASE:
            x_velocity = self.do_chase()
            self.state = 'walk'
        
        elif self.ai_state == self.STATE_ATTACK:
            x_velocity = 0
            self.do_attack()
        
        elif self.ai_state == self.STATE_DIE:
            x_velocity = 0
            self.state = 'die'
        
        return x_velocity
    
    def do_chase(self):
        """
        Override chase untuk Golem.
        Golem chase sangat lambat tapi mengintimidasi.
        """
        direction = self.get_direction_to_player()
        
        # Update facing direction
        self.facing_right = direction > 0
        self.physics.facing_right = self.facing_right
        
        # Golem sangat lambat
        return direction * self.movement_speed
    
    def do_attack(self):
        """
        Override attack untuk Golem.
        Serangan berat dengan damage tinggi.
        """
        if not self.is_attacking and self.alive:
            self.is_attacking = True
            self.last_attack_time = pg.time.get_ticks()
            self.state = 'attack'
            self.animator.reset_animation()
            
            # Deal damage ke player jika dalam range
            if self.player_ref and self.player_ref.alive:
                distance = self.get_distance_to_player()
                if distance < self.attack_range + 30:  # Range lebih besar untuk golem
                    self.player_ref.take_damage(self.attack_power)
                    print(f"[COMBAT] Golem SMASH! Deals {self.attack_power} damage to Player!")
    
    # ===========================================
    # SECTION: OVERRIDE DAMAGE (Golem lebih tahan)
    # ===========================================
    
    def take_damage(self, amount):
        """
        Override take_damage untuk Golem.
        Golem punya damage reduction (armor).
        """
        if not self.alive or self.is_invincible:
            return
        
        # Golem punya 20% damage reduction
        reduced_damage = int(amount * 0.8)
        
        self.current_hp -= reduced_damage
        self.is_invincible = True
        self.last_hit_time = pg.time.get_ticks()
        
        # Golem tidak flinch (tidak masuk state hurt kecuali HP rendah)
        if self.current_hp < self.max_hp * 0.3:  # HP di bawah 30%
            self.state = 'hurt'
            self.ai_state = self.STATE_IDLE
        
        print(f"[COMBAT] Golem took {reduced_damage} dmg (reduced from {amount}). HP: {self.current_hp}/{self.max_hp}")
        
        if self.current_hp <= 0:
            self.die()

