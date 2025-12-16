import pygame as pg
from game.entities.enemies.enemy import BaseEnemy

# Path aset lokal untuk Guardian
GUARDIAN_ASSET_PATH = 'assets/graphics/enemies/ice_monster/guardian/'

class Guardian(BaseEnemy):
    """
    Enemy Guardian - Tipe: Ice Elite, Balanced Fighter, Boss-Tier.
    
    INHERITANCE CHAIN:
    pg.sprite.Sprite -> Entity -> BaseEnemy -> Guardian
    
    KARAKTERISTIK GUARDIAN:
    - Elite ice monster (stronger than regular enemies)
    - Balanced stats: good HP, good damage, decent speed
    - Long attack and death animations (smooth and intimidating)
    - Boss or mini-boss tier enemy
    
    ANIMASI YANG TERSEDIA (ICE MONSTER):
    - idle: 6 frames
    - walk: 10 frames
    - attack: 14 frames (long, powerful animation)
    - hurt: 7 frames
    - death: 16 frames (epic death)
    
    SPECIAL BEHAVIOR:
    - Longer attack animation with higher damage
    - More aggressive AI than regular enemies
    - Elite-tier enemy suitable for boss fights
    """
    
    def __init__(self, x, y):
        """
        Inisialisasi Guardian pada posisi tertentu.
        
        Args:
            x, y: Posisi spawn Guardian
        """
        # 1. TENTUKAN STATS KHUSUS GUARDIAN (ELITE/BOSS TIER)
        stats_hp = 200      # HP tinggi (elite)
        stats_attack = 30   # Damage tinggi
        stats_speed = 2.2   # Lebih cepat dari Golem tapi lambat dari skeleton
        
        # Ukuran hitbox (Elite enemy, cukup besar)
        hitbox_width = 65
        hitbox_height = 85
        
        # Scale untuk sprite (elite = besar)
        sprite_scale = 2.2
        
        # 2. PANGGIL CONSTRUCTOR PARENT (BaseEnemy)
        super().__init__(
            x=x, y=y,
            width=hitbox_width, height=hitbox_height,
            max_hp=stats_hp,
            attack_power=stats_attack,
            speed=stats_speed,
            asset_path=GUARDIAN_ASSET_PATH,
            scale=sprite_scale
        )
        
        # 3. OVERRIDE DETECTION RANGES (Elite = more aggressive)
        self.detection_range = 400
        self.attack_range = 75
        self.lose_interest_range = 500  # Sangat persistent
        
        # 4. SETUP ANIMASI
        self._setup_animations()
    
    def _setup_animations(self):
        """
        Load semua sprite animasi untuk Guardian.
        
        Mapping folder:
        - idle -> idle
        - walk -> walk
        - chase -> walk
        - attack -> attack
        - hurt -> hurt
        - die -> death
        """
        animation_mapping = {
            'idle': 'idle',
            'walk': 'walk',
            'chase': 'walk',
            'attack': 'attack',
            'hurt': 'hurt',
            'die': 'death',
        }
        
        self.animator.load_sprites(animation_mapping)
        
        # Set animation speed
        self.animator.animation_speed = 0.14
        self.attack_animation_speed = 0.11  # Slower for long attack (14 frames)
        self.death_animation_speed = 0.10   # Slow epic death (16 frames)
    
    def update(self, dt):
        """
        Override update untuk Guardian behavior.
        """
        # Panggil update parent
        super().update(dt)
        
        # Custom behavior: Guardian lebih agresif
        # Bisa ditambahkan special moves atau patterns
    
    def render_sprite(self, camera):
        """
        Override render untuk animasi dengan speed berbeda per state.
        """
        # Tentukan speed animasi berdasarkan state
        anim_speed = self.animator.animation_speed
        
        if self.ai_state == self.STATE_ATTACK:
            anim_speed = self.attack_animation_speed
        elif self.ai_state == self.STATE_DIE:
            anim_speed = self.death_animation_speed
        
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
