import pygame as pg
from game.entities.enemies.enemy import BaseEnemy

# Path aset lokal untuk Demon Slime
DEMON_SLIME_ASSET_PATH = 'assets/graphics/enemies/dungeon_monster/boss_demon_slime/'

class DemonSlime(BaseEnemy):
    """
    Enemy Demon Slime - Tipe: Boss, Tank, Serangan Area Besar (Cleave).
    
    INHERITANCE CHAIN:
    pg.sprite.Sprite -> Entity -> BaseEnemy -> DemonSlime
    
    KARAKTERISTIK DEMON SLIME:
    - Boss-tier enemy dengan HP sangat tinggi
    - Serangan "Cleave" dengan damage area besar
    - Lambat tapi damage tinggi
    - Punya animasi take_hit yang detail (5 frames)
    - Death animation yang panjang (22 frames)
    
    ANIMASI YANG TERSEDIA:
    - 01_demon_idle: 6 frames
    - 02_demon_walk: 12 frames
    - 03_demon_cleave: 15 frames (attack)
    - 04_demon_take_hit: 5 frames
    - 05_demon_death: 22 frames
    
    SPECIAL BEHAVIOR:
    - Cleave attack memiliki range lebih besar dari melee biasa
    - Serangan memiliki area damage
    """
    
    def __init__(self, x, y):
        """
        Inisialisasi Demon Slime pada posisi tertentu.
        
        Args:
            x, y: Posisi spawn Demon Slime
        """
        # 1. TENTUKAN STATS KHUSUS DEMON SLIME (BOSS TIER)
        stats_hp = 300      # HP sangat tinggi (boss)
        stats_attack = 40   # Damage sangat tinggi
        stats_speed = 1.8   # Lambat
        
        # Ukuran hitbox (Boss = lebih besar)
        hitbox_width = 80
        hitbox_height = 100
        
        # Scale untuk sprite (boss = besar)
        sprite_scale = 2.0
        
        # 2. PANGGIL CONSTRUCTOR PARENT (BaseEnemy)
        super().__init__(
            x=x, y=y,
            width=hitbox_width, height=hitbox_height,
            max_hp=stats_hp,
            attack_power=stats_attack,
            speed=stats_speed,
            asset_path=DEMON_SLIME_ASSET_PATH,
            scale=sprite_scale
        )
        
        # 3. OVERRIDE DETECTION RANGES (Boss lebih agresif)
        self.detection_range = 400
        self.attack_range = 80  # Cleave range lebih besar
        
        # 4. SETUP ANIMASI
        self._setup_animations()
    
    def _setup_animations(self):
        """
        Load semua sprite animasi untuk Demon Slime.
        
        Mapping folder:
        - idle -> 01_demon_idle
        - walk -> 02_demon_walk
        - attack -> 03_demon_cleave
        - hurt -> 04_demon_take_hit
        - die -> 05_demon_death
        """
        animation_mapping = {
            'idle': '01_demon_idle',
            'walk': '02_demon_walk',
            'attack': '03_demon_cleave',
            'hurt': '04_demon_take_hit',
            'die': '05_demon_death',
        }
        
        self.animator.load_sprites(animation_mapping)
        
        # Set animation speed untuk animasi tertentu
        # Death animation lebih lambat karena panjang (22 frames)
        self.death_animation_speed = 0.12
        self.attack_animation_speed = 0.10  # Cleave juga lebih lambat (15 frames)
    
    def update(self, dt):
        """
        Override update untuk behavior khusus Demon Slime.
        """
        # Panggil update parent dulu (AI logic, physics, dll)
        super().update(dt)
        
        # Custom behavior untuk Demon Slime bisa ditambahkan di sini
        # Misalnya: area damage saat cleave, screen shake, dll
    
    def render_sprite(self, camera):
        """
        Override render untuk animasi khusus (speed berbeda per state).
        """
        # Tentukan speed animasi berdasarkan state
        anim_speed = self.animator.animation_speed
        
        if self.ai_state == self.STATE_DIE:
            anim_speed = self.death_animation_speed
        elif self.ai_state == self.STATE_ATTACK:
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
    
    def perform_attack(self):
        """
        Override perform_attack untuk Cleave (area damage).
        Bisa diperluas untuk damage semua player dalam range.
        """
        super().perform_attack()
        
        # TODO: Implementasi area damage
        # Cek semua entity dalam radius attack_range
        # Apply damage ke semua yang kena
