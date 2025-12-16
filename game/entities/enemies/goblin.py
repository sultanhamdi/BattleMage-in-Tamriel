import pygame as pg
from game.entities.enemies.enemy import BaseEnemy

# Path aset lokal untuk Goblin
GOBLIN_ASSET_PATH = 'assets/graphics/enemies/grass_monster/Goblin/'

class Goblin(BaseEnemy):
    """
    Enemy Goblin - Tipe: Ground Melee/Range, Versatile Fighter.
    
    INHERITANCE CHAIN:
    pg.sprite.Sprite -> Entity -> BaseEnemy -> Goblin
    
    KARAKTERISTIK GOBLIN:
    - Ground enemy (menggunakan gravitasi)
    - Punya melee dan range attack
    - HP rendah-menengah, damage menengah
    - Agile dan versatile
    
    ANIMASI YANG TERSEDIA:
    - idle: 4 frames
    - run: 8 frames
    - attack: 8 frames (melee)
    - attack2: 8 frames (alternatif melee)
    - range: 12 frames (range attack animation)
    - projectile: 0 frames (empty, sprite terpisah)
    - take_hit: 4 frames
    - death: 4 frames
    
    SPECIAL BEHAVIOR:
    - Switch antara melee dan range attack based on distance
    - Lebih agile dari zombie
    """
    
    def __init__(self, x, y):
        """
        Inisialisasi Goblin pada posisi tertentu.
        
        Args:
            x, y: Posisi spawn Goblin
        """
        # 1. TENTUKAN STATS KHUSUS GOBLIN
        stats_hp = 55       # HP rendah-menengah
        stats_attack = 14   # Damage menengah
        stats_speed = 3.0   # Cukup cepat
        
        # Ukuran hitbox
        hitbox_width = 40
        hitbox_height = 50
        
        # Scale untuk sprite
        sprite_scale = 1.8
        
        # 2. PANGGIL CONSTRUCTOR PARENT (BaseEnemy)
        super().__init__(
            x=x, y=y,
            width=hitbox_width, height=hitbox_height,
            max_hp=stats_hp,
            attack_power=stats_attack,
            speed=stats_speed,
            asset_path=GOBLIN_ASSET_PATH,
            scale=sprite_scale
        )
        
        # 3. OVERRIDE DETECTION RANGES
        self.detection_range = 350
        self.attack_range = 55      # Melee range
        self.range_attack_range = 250  # Range untuk projectile
        
        # 4. COMBAT STATE
        self.projectile_cooldown = 0
        self.projectile_cooldown_max = 120  # 2 detik
        self.prefer_range = True  # Goblin prefer jarak jauh
        
        # 5. SETUP ANIMASI
        self._setup_animations()
    
    def _setup_animations(self):
        """
        Load semua sprite animasi untuk Goblin.
        
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
        
        # Set animation speed
        self.animator.animation_speed = 0.15
    
    def update(self, dt):
        """
        Override update untuk goblin behavior.
        """
        # Update projectile cooldown
        if self.projectile_cooldown > 0:
            self.projectile_cooldown -= 1
        
        # Panggil update parent
        super().update(dt)
        
        # Custom AI: Prefer range attack
        if self.ai_state == self.STATE_CHASE:
            distance = self.get_distance_to_player()
            
            # Jika player dalam range attack range dan cooldown ready
            if (distance <= self.range_attack_range and 
                distance > self.attack_range and 
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
                self.shoot_projectile()
                self.projectile_cooldown = self.projectile_cooldown_max
                self.ai_state = self.STATE_CHASE
            return
        
        # Jalankan AI normal
        super()._update_ai()
    
    def shoot_projectile(self):
        """
        Shoot projectile ke arah player.
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
