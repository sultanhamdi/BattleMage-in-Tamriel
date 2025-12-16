import pygame as pg
from game.entities.enemies.enemy import BaseEnemy

# Path aset lokal untuk Skeleton
SKELETON_ASSET_PATH = 'assets/graphics/enemies/grass_monster/Skeleton/'

class Skeleton(BaseEnemy):
    """
    Enemy Skeleton - Tipe: Ground Melee/Defense, Shield User.
    
    INHERITANCE CHAIN:
    pg.sprite.Sprite -> Entity -> BaseEnemy -> Skeleton
    
    KARAKTERISTIK SKELETON:
    - Ground enemy dengan shield (defense tinggi)
    - Melee dan range attack
    - HP menengah, damage menengah
    - Punya shield animation (block/defense)
    
    ANIMASI YANG TERSEDIA:
    - idle: 4 frames
    - walk: 4 frames
    - attack: 8 frames (melee)
    - attack2: 8 frames (alternatif)
    - range: 6 frames (range attack)
    - shield: 4 frames (blocking/defense)
    - projectile: 0 frames (empty)
    - take_hit: 4 frames
    - death: 4 frames
    
    SPECIAL BEHAVIOR:
    - Bisa block attack dengan shield (reduce damage)
    - Defensive playstyle
    - Shield animation triggered saat menerima damage
    """
    
    def __init__(self, x, y):
        """
        Inisialisasi Skeleton pada posisi tertentu.
        
        Args:
            x, y: Posisi spawn Skeleton
        """
        # 1. TENTUKAN STATS KHUSUS SKELETON
        stats_hp = 80       # HP menengah-tinggi (karena shield)
        stats_attack = 16   # Damage menengah
        stats_speed = 2.2   # Lambat (armor + shield)
        
        # Ukuran hitbox
        hitbox_width = 45
        hitbox_height = 55
        
        # Scale untuk sprite
        sprite_scale = 1.8
        
        # 2. PANGGIL CONSTRUCTOR PARENT (BaseEnemy)
        super().__init__(
            x=x, y=y,
            width=hitbox_width, height=hitbox_height,
            max_hp=stats_hp,
            attack_power=stats_attack,
            speed=stats_speed,
            asset_path=SKELETON_ASSET_PATH,
            scale=sprite_scale
        )
        
        # 3. OVERRIDE DETECTION RANGES
        self.detection_range = 320
        self.attack_range = 60
        self.range_attack_range = 220
        
        # 4. SHIELD MECHANICS
        self.is_shielding = False
        self.shield_chance = 0.3  # 30% chance untuk shield saat kena damage
        self.shield_damage_reduction = 0.5  # Reduce 50% damage saat shield
        
        # 5. COMBAT STATE
        self.projectile_cooldown = 0
        self.projectile_cooldown_max = 150
        
        # 6. SETUP ANIMASI
        self._setup_animations()
    
    def _setup_animations(self):
        """
        Load semua sprite animasi untuk Skeleton.
        
        Mapping folder:
        - idle -> idle
        - walk -> walk
        - chase -> walk
        - attack -> attack
        - range -> range
        - shield -> shield
        - hurt -> take_hit
        - die -> death
        """
        animation_mapping = {
            'idle': 'idle',
            'walk': 'walk',
            'chase': 'walk',
            'attack': 'attack',
            'attack2': 'attack2',
            'range': 'range',
            'shield': 'shield',
            'hurt': 'take_hit',
            'die': 'death',
        }
        
        self.animator.load_sprites(animation_mapping)
        
        # Set animation speed
        self.animator.animation_speed = 0.15
    
    def update(self, dt):
        """
        Override update untuk skeleton behavior.
        """
        # Update projectile cooldown
        if self.projectile_cooldown > 0:
            self.projectile_cooldown -= 1
        
        # Handle shield state
        if self.is_shielding:
            # Tunggu animasi shield selesai
            if self.animator.is_animation_finished():
                self.is_shielding = False
                self.ai_state = self.STATE_CHASE
        
        # Panggil update parent
        super().update(dt)
        
        # Custom AI: Occasional range attack
        if self.ai_state == self.STATE_CHASE:
            distance = self.get_distance_to_player()
            
            # Range attack saat player agak jauh
            if (distance <= self.range_attack_range and 
                distance > self.attack_range and 
                self.projectile_cooldown <= 0):
                self.ai_state = 'range'
                self.animator.reset_animation()
    
    def _update_ai(self):
        """
        Override AI untuk handle range attack dan shield.
        """
        # Handle shield state
        if self.is_shielding:
            self.physics.velocity_x = 0
            return
        
        # Handle range attack state
        if self.ai_state == 'range':
            self.physics.velocity_x = 0
            
            if self.animator.is_animation_finished():
                self.shoot_projectile()
                self.projectile_cooldown = self.projectile_cooldown_max
                self.ai_state = self.STATE_CHASE
            return
        
        # Jalankan AI normal
        super()._update_ai()
    
    def take_damage(self, damage):
        """
        Override take_damage untuk shield mechanics.
        """
        # Random chance untuk shield
        import random
        if random.random() < self.shield_chance and not self.is_shielding:
            # Activate shield
            self.is_shielding = True
            self.ai_state = 'shield'
            self.animator.reset_animation()
            
            # Reduce damage
            damage = int(damage * self.shield_damage_reduction)
        
        # Apply damage normal
        super().take_damage(damage)
    
    def shoot_projectile(self):
        """
        Shoot projectile (bone throw).
        TODO: Implementasi projectile system.
        """
        # Placeholder
        pass
    
    def render_sprite(self, camera):
        """
        Override render untuk animasi.
        """
        # Jika lagi shield, paksa animasi shield
        anim_state = self.ai_state
        if self.is_shielding:
            anim_state = 'shield'
        
        # Dapatkan frame animasi
        sprite = self.animator.animate(
            state=anim_state,
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
