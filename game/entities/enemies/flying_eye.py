import pygame as pg
import math
from game.entities.enemies.enemy import BaseEnemy

# Path aset lokal untuk Flying Eye
FLYING_EYE_ASSET_PATH = 'assets/graphics/enemies/grass_monster/Flying eye/'

class FlyingEye(BaseEnemy):
    """
    Enemy Flying Eye - Tipe: Flying, Range Attack, Agile.
    
    INHERITANCE CHAIN:
    pg.sprite.Sprite -> Entity -> BaseEnemy -> FlyingEye
    
    KARAKTERISTIK FLYING EYE:
    - Terbang (mengabaikan gravitasi seperti Vampire)
    - Punya 2 tipe attack: melee (attack) dan range (range + projectile)
    - HP rendah tapi evasive (terbang naik-turun)
    - Bisa bergerak vertikal
    
    ANIMASI YANG TERSEDIA:
    - flight: 8 frames (idle + movement)
    - attack: 8 frames (melee)
    - attack2: 8 frames (alternatif attack)
    - range: 6 frames (range attack animation)
    - projectile: 0 frames (empty, mungkin sprite terpisah)
    - take_hit: 4 frames
    - death: 4 frames
    
    SPECIAL BEHAVIOR:
    - Mengabaikan gravitasi (flying)
    - Bergerak vertikal mengejar player
    - Prefer range attack
    """
    
    def __init__(self, x, y):
        """
        Inisialisasi Flying Eye pada posisi tertentu.
        
        Args:
            x, y: Posisi spawn Flying Eye
        """
        # 1. TENTUKAN STATS KHUSUS FLYING EYE
        stats_hp = 45       # HP rendah
        stats_attack = 12   # Damage rendah (karena bisa range)
        stats_speed = 3.5   # Cepat (flying)
        
        # Ukuran hitbox (flying enemy biasanya kecil)
        hitbox_width = 35
        hitbox_height = 35
        
        # Scale untuk sprite
        sprite_scale = 1.8
        
        # 2. PANGGIL CONSTRUCTOR PARENT (BaseEnemy)
        super().__init__(
            x=x, y=y,
            width=hitbox_width, height=hitbox_height,
            max_hp=stats_hp,
            attack_power=stats_attack,
            speed=stats_speed,
            asset_path=FLYING_EYE_ASSET_PATH,
            scale=sprite_scale
        )
        
        # 3. OVERRIDE DETECTION RANGES
        self.detection_range = 400
        self.attack_range = 50      # Melee range
        self.range_attack_range = 300  # Range untuk projectile
        
        # 4. FLYING BEHAVIOR
        self.can_fly = True
        self.has_gravity = False  # DISABLE GRAVITY FOR FLYING
        self.hover_amplitude = 10  # Naik-turun saat hover
        self.hover_speed = 0.05
        self.hover_offset = 0
        
        # 5. COMBAT STATE
        self.projectile_cooldown = 0
        self.projectile_cooldown_max = 90  # 1.5 detik
        
        # 6. SETUP ANIMASI
        self._setup_animations()
    
    def _setup_animations(self):
        """
        Load semua sprite animasi untuk Flying Eye.
        
        Mapping folder:
        - idle -> flight
        - walk -> flight
        - chase -> flight
        - attack -> attack
        - range -> range
        - hurt -> take_hit
        - die -> death
        """
        animation_mapping = {
            'idle': 'flight',
            'walk': 'flight',
            'chase': 'flight',
            'attack': 'attack',
            'attack2': 'attack2',
            'range': 'range',
            'hurt': 'take_hit',
            'die': 'death',
        }
        
        self.animator.load_sprites(animation_mapping)
        
        # Set animation speed
        self.animator.animation_speed = 0.15
    
    def update(self, dt):
        """
        Override update untuk flying behavior.
        """
        # Update projectile cooldown
        if self.projectile_cooldown > 0:
            self.projectile_cooldown -= 1
        
        # DISABLE GRAVITY (flying enemy)
        self.physics.apply_gravity = False
        
        # Hover effect saat idle
        if self.ai_state == self.STATE_IDLE:
            self.hover_offset += self.hover_speed
            hover_y = math.sin(self.hover_offset) * self.hover_amplitude
            self.physics.rect.y += hover_y
        
        # Panggil update parent
        super().update(dt)
        
        # Custom AI: Prefer range attack jika player dalam range
        if self.ai_state == self.STATE_CHASE:
            distance = self.get_distance_to_player()
            
            # Jika player dalam range attack range
            if distance <= self.range_attack_range and distance > self.attack_range:
                if self.projectile_cooldown <= 0:
                    self.ai_state = 'range'
                    self.animator.reset_animation()
    
    def _update_ai(self):
        """
        Override AI untuk handle flying movement (vertical).
        """
        # Handle range attack state
        if self.ai_state == 'range':
            self.physics.velocity_x = 0
            
            # Tunggu animasi range selesai
            if self.animator.is_animation_finished():
                self.shoot_projectile()
                self.projectile_cooldown = self.projectile_cooldown_max
                self.ai_state = self.STATE_CHASE
            return
        
        # Jalankan AI normal
        super()._update_ai()
        
        # Tambahan: Flying movement vertikal mengejar player
        if self.ai_state == self.STATE_CHASE and self.player_ref:
            # Hitung perbedaan Y dengan player
            y_diff = self.player_ref.physics.rect.centery - self.physics.rect.centery
            
            # Bergerak vertikal ke arah player
            if abs(y_diff) > 20:
                vertical_speed = 2
                if y_diff > 0:
                    self.physics.velocity_y = vertical_speed
                else:
                    self.physics.velocity_y = -vertical_speed
            else:
                self.physics.velocity_y = 0
    
    def shoot_projectile(self):
        """
        Shoot projectile ke arah player.
        TODO: Implementasi projectile system.
        """
        # Placeholder untuk projectile spawn
        pass
    
    def render_sprite(self, camera):
        """
        Override render untuk animasi.
        """
        # Dapatkan frame animasi
        sprite = self.animator.animate(
            state=self.ai_state,
            speed=self.animator.animation_speed,
            facing_right=self.facing_right
        )
        
        if sprite:
            # Hitung posisi render dengan offset camera
            render_x = self.physics.rect.x - camera.offset_x
            render_y = self.physics.rect.y - camera.offset_y
            
            # Center sprite di hitbox
            sprite_offset_x = (sprite.get_width() - self.physics.rect.width) // 2
            sprite_offset_y = (sprite.get_height() - self.physics.rect.height) // 2
            
            camera.surface.blit(sprite, (render_x - sprite_offset_x, render_y - sprite_offset_y))
