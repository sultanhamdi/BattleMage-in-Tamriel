import pygame as pg
from game.entities.enemies.enemy import BaseEnemy

# Path aset lokal untuk Mushroom
MUSHROOM_ASSET_PATH = 'assets/graphics/enemies/grass_monster/Mushroom/'

class Mushroom(BaseEnemy):
    """
    Enemy Mushroom - Tipe: Ground Support/Range, Slow but Persistent.
    
    INHERITANCE CHAIN:
    pg.sprite.Sprite -> Entity -> BaseEnemy -> Mushroom
    
    KARAKTERISTIK MUSHROOM:
    - Ground enemy lambat (seperti tanaman)
    - Fokus pada range attack (spore/projectile)
    - HP menengah, damage rendah-menengah
    - Defensive playstyle
    
    ANIMASI YANG TERSEDIA:
    - idle: 4 frames
    - run: 8 frames (lambat, seperti bergoyang)
    - attack: 8 frames (melee)
    - attack2: 8 frames (alternatif)
    - range: 11 frames (spore attack)
    - projectile: 0 frames (empty)
    - take_hit: 4 frames
    - death: 4 frames
    
    SPECIAL BEHAVIOR:
    - Prefer stay in place dan range attack
    - Minimal movement (stationary defender)
    """
    
    def __init__(self, x, y):
        """
        Inisialisasi Mushroom pada posisi tertentu.
        
        Args:
            x, y: Posisi spawn Mushroom
        """
        # 1. TENTUKAN STATS KHUSUS MUSHROOM
        stats_hp = 70       # HP menengah (tanky untuk grass tier)
        stats_attack = 10   # Damage rendah
        stats_speed = 1.5   # Sangat lambat
        
        # Ukuran hitbox
        hitbox_width = 40
        hitbox_height = 45
        
        # Scale untuk sprite
        sprite_scale = 1.8
        
        # 2. PANGGIL CONSTRUCTOR PARENT (BaseEnemy)
        super().__init__(
            x=x, y=y,
            width=hitbox_width, height=hitbox_height,
            max_hp=stats_hp,
            attack_power=stats_attack,
            speed=stats_speed,
            asset_path=MUSHROOM_ASSET_PATH,
            scale=sprite_scale
        )
        
        # 3. OVERRIDE DETECTION RANGES
        self.detection_range = 300
        self.attack_range = 50
        self.range_attack_range = 280  # Long range spore
        
        # 4. COMBAT STATE
        self.projectile_cooldown = 0
        self.projectile_cooldown_max = 100  # Faster cooldown untuk range spam
        
        # 5. BEHAVIOR: Mushroom prefer tidak bergerak jauh dari spawn
        self.max_chase_distance = 150  # Tidak chase terlalu jauh
        
        # 6. SETUP ANIMASI
        self._setup_animations()
    
    def _setup_animations(self):
        """
        Load semua sprite animasi untuk Mushroom.
        
        Mapping folder:
        - idle -> idle
        - walk -> run
        - chase -> run
        - attack -> attack
        - range -> range
        - hurt -> take_hit
        - die -> death
        """
        animation_mapping = {
            'idle': 'idle',
            'walk': 'run',
            'chase': 'run',
            'attack': 'attack',
            'attack2': 'attack2',
            'range': 'range',
            'hurt': 'take_hit',
            'die': 'death',
        }
        
        self.animator.load_sprites(animation_mapping)
        
        # Set animation speed (mushroom bergerak lambat)
        self.animator.animation_speed = 0.12
    
    def update(self, dt):
        """
        Override update untuk mushroom behavior.
        """
        # Update projectile cooldown
        if self.projectile_cooldown > 0:
            self.projectile_cooldown -= 1
        
        # Panggil update parent
        super().update(dt)
        
        # Custom AI: Prefer range attack, minimal movement
        if self.ai_state == self.STATE_CHASE:
            distance = self.get_distance_to_player()
            distance_from_spawn = abs(self.physics.rect.x - self.spawn_x)
            
            # Jika terlalu jauh dari spawn, kembali
            if distance_from_spawn > self.max_chase_distance:
                # Balik ke spawn
                self.ai_state = self.STATE_PATROL
                return
            
            # Jika player dalam range, stop dan shoot
            if (distance <= self.range_attack_range and 
                self.projectile_cooldown <= 0):
                self.ai_state = 'range'
                self.animator.reset_animation()
    
    def _update_ai(self):
        """
        Override AI untuk handle range attack.
        """
        # Handle range attack state
        if self.ai_state == 'range':
            self.physics.velocity_x = 0
            
            # Tunggu animasi range selesai
            if self.animator.is_animation_finished():
                self.shoot_spore()
                self.projectile_cooldown = self.projectile_cooldown_max
                self.ai_state = self.STATE_IDLE  # Kembali idle, tidak chase
            return
        
        # Jalankan AI normal
        super()._update_ai()
    
    def shoot_spore(self):
        """
        Shoot spore projectile ke arah player.
        TODO: Implementasi projectile system.
        """
        # Placeholder
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
