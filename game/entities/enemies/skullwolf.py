import pygame as pg
from game.entities.enemies.enemy import BaseEnemy

# Path aset lokal untuk Skullwolf
SKULLWOLF_ASSET_PATH = 'assets/graphics/enemies/dungeon_monster/Skullwolf/'

class Skullwolf(BaseEnemy):
    """
    Enemy Skullwolf - Tipe: Fast Melee, Agresif, Pack Hunter.
    
    INHERITANCE CHAIN:
    pg.sprite.Sprite -> Entity -> BaseEnemy -> Skullwolf
    
    KARAKTERISTIK SKULLWOLF:
    - Cepat dan agresif (wolf behavior)
    - HP rendah-menengah tapi damage menengah
    - Cocok untuk spawn dalam jumlah banyak (pack)
    - Animasi sederhana tapi smooth
    
    ANIMASI YANG TERSEDIA:
    - idle: 6 frames
    - attack: 5 frames
    - hurt: 4 frames
    - death: 7 frames
    
    SPECIAL BEHAVIOR:
    - Lebih cepat dari enemy biasa
    - Detection range lebih besar (pack hunter)
    - Tidak ada walk animation (langsung dari idle ke chase/run)
    """
    
    def __init__(self, x, y):
        """
        Inisialisasi Skullwolf pada posisi tertentu.
        
        Args:
            x, y: Posisi spawn Skullwolf
        """
        # 1. TENTUKAN STATS KHUSUS SKULLWOLF
        stats_hp = 60       # HP rendah-menengah
        stats_attack = 18   # Damage menengah
        stats_speed = 4.5   # Cepat (wolf)
        
        # Ukuran hitbox
        hitbox_width = 50
        hitbox_height = 45
        
        # Scale untuk sprite
        sprite_scale = 2.0
        
        # 2. PANGGIL CONSTRUCTOR PARENT (BaseEnemy)
        super().__init__(
            x=x, y=y,
            width=hitbox_width, height=hitbox_height,
            max_hp=stats_hp,
            attack_power=stats_attack,
            speed=stats_speed,
            asset_path=SKULLWOLF_ASSET_PATH,
            scale=sprite_scale
        )
        
        # 3. OVERRIDE DETECTION RANGES (Pack hunter = deteksi jauh)
        self.detection_range = 450
        self.attack_range = 50
        self.lose_interest_range = 600  # Lebih persistent
        
        # 4. SETUP ANIMASI
        self._setup_animations()
    
    def _setup_animations(self):
        """
        Load semua sprite animasi untuk Skullwolf.
        
        Mapping folder:
        - idle -> idle
        - walk -> idle (no walk animation, use idle for movement)
        - attack -> attack
        - hurt -> hurt
        - die -> death
        """
        animation_mapping = {
            'idle': 'idle',
            'walk': 'idle',  # No walk animation, gunakan idle
            'chase': 'idle', # Gunakan idle untuk chase juga
            'attack': 'attack',
            'hurt': 'hurt',
            'die': 'death',
        }
        
        self.animator.load_sprites(animation_mapping)
        
        # Set animation speed (wolf bergerak cepat, animasi juga cepat)
        self.animator.animation_speed = 0.18
        self.attack_animation_speed = 0.20
    
    def update(self, dt):
        """
        Override update untuk behavior khusus Skullwolf.
        """
        # Panggil update parent dulu (AI logic, physics, dll)
        super().update(dt)
        
        # Custom behavior: Skullwolf selalu agresif, tidak patrol
        # Bisa ditambahkan pack behavior (berkumpul dengan skullwolf lain)
    
    def render_sprite(self, camera):
        """
        Override render untuk animasi.
        """
        # Tentukan speed animasi berdasarkan state
        anim_speed = self.animator.animation_speed
        
        if self.ai_state == self.STATE_ATTACK:
            anim_speed = self.attack_animation_speed
        
        # Dapatkan frame animasi
        sprite = self.animator.animate(
            state=self.ai_state,
            speed=anim_speed,
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
    
    def _handle_ai_patrol(self):
        """
        Override patrol: Skullwolf tidak patrol, langsung idle.
        """
        # Skullwolf hanya idle, tidak bolak-balik
        self.ai_state = self.STATE_IDLE
        self.physics.velocity_x = 0
