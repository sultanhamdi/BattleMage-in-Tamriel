import pygame as pg
from game.entities.enemies.enemy import BaseEnemy

# Path aset lokal untuk Golem (ICE MONSTER)
GOLEM_ASSET_PATH = 'assets/graphics/enemies/ice_monster/golem/'

class Golem(BaseEnemy):
    """
    Enemy Golem - Tipe: Ice Tank, Lambat, HP Tebal, Serangan Berat.
    
    INHERITANCE CHAIN:
    pg.sprite.Sprite -> Entity -> BaseEnemy -> Golem
    
    KARAKTERISTIK GOLEM:
    - Ice monster tank dengan HP sangat tebal
    - Serangan berat dengan damage tinggi
    - Sangat lambat tapi intimidating
    - AI: Patrol -> Chase -> Attack
    
    ANIMASI YANG TERSEDIA (ICE MONSTER):
    - idle: 8 frames
    - walk: 10 frames
    - attack: 11 frames
    - hurt: 4 frames
    - die: 13 frames
    
    SPECIAL BEHAVIOR:
    - High HP and damage (tank role)
    - Slow movement
    - Damage reduction (armor)
    """
    
    def __init__(self, x, y):
        """
        Inisialisasi Golem pada posisi tertentu.
        
        Args:
            x, y: Posisi spawn Golem
        """
        # 1. TENTUKAN STATS KHUSUS GOLEM
        stats_hp = 150      # HP sangat tebal
        stats_attack = 25   # Damage tinggi
        stats_speed = 1.5   # Sangat lambat
        
        # Ukuran hitbox (Golem lebih besar)
        hitbox_width = 60
        hitbox_height = 80
        
        # Scale untuk sprite
        sprite_scale = 2.0
        
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
        
        # 3. OVERRIDE DETECTION RANGES
        self.detection_range = 250
        self.attack_range = 70
        self.lose_interest_range = 350
        
        # 4. DAMAGE REDUCTION (Armor)
        self.damage_reduction = 0.8  # 20% damage reduction
        
        # 5. SETUP ANIMASI
        self._setup_animations()
    
    def _setup_animations(self):
        """
        Load semua sprite animasi untuk Golem (Ice Monster).
        
        Mapping folder:
        - idle -> idle
        - walk -> walk
        - chase -> walk
        - attack -> attack
        - hurt -> hurt
        - die -> die
        """
        animation_mapping = {
            'idle': 'idle',
            'walk': 'walk',
            'chase': 'walk',
            'attack': 'attack',
            'hurt': 'hurt',
            'die': 'die',
        }
        
        self.animator.load_sprites(animation_mapping)
        
        # Set animation speed
        self.animator.animation_speed = 0.12  # Slow and heavy
        self.attack_animation_speed = 0.10
    
    def update(self, dt):
        """
        Override update untuk Golem behavior.
        """
        super().update(dt)
    
    def take_damage(self, amount):
        """
        Override take_damage untuk damage reduction.
        """
        # Apply damage reduction
        reduced_damage = int(amount * self.damage_reduction)
        super().take_damage(reduced_damage)
    
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

