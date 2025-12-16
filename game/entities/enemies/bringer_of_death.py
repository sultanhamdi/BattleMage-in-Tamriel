import pygame as pg
from game.entities.enemies.enemy import BaseEnemy

# Path aset lokal untuk Bringer of Death
BRINGER_OF_DEATH_ASSET_PATH = 'assets/graphics/enemies/dungeon_monster/bringer_of_death/'

class BringerOfDeath(BaseEnemy):
    """
    Enemy Bringer of Death - Tipe: Boss, Caster, Range Attack dengan Spell.
    
    INHERITANCE CHAIN:
    pg.sprite.Sprite -> Entity -> BaseEnemy -> BringerOfDeath
    
    KARAKTERISTIK BRINGER OF DEATH:
    - Boss-tier enemy dengan kemampuan cast spell
    - Bisa melee attack dan range spell attack
    - HP tinggi, damage tinggi
    - Punya 2 tipe attack: Attack (melee) dan Cast+Spell (range)
    
    ANIMASI YANG TERSEDIA:
    - Idle: 8 frames
    - Walk: 8 frames
    - Attack: 10 frames (melee)
    - Cast: 9 frames (casting animation)
    - Spell: 16 frames (projectile/spell effect)
    - Hurt: 3 frames
    - Death: 10 frames
    
    SPECIAL BEHAVIOR:
    - Bisa berganti antara melee attack dan spell cast
    - Saat Cast, akan spawn Spell projectile
    - Lebih prefer range attack jika player jauh
    """
    
    def __init__(self, x, y):
        """
        Inisialisasi Bringer of Death pada posisi tertentu.
        
        Args:
            x, y: Posisi spawn Bringer of Death
        """
        # 1. TENTUKAN STATS KHUSUS BRINGER OF DEATH (BOSS TIER)
        stats_hp = 250      # HP tinggi (boss)
        stats_attack = 35   # Damage tinggi
        stats_speed = 2.5   # Lebih cepat dari Demon Slime
        
        # Ukuran hitbox (Boss tier)
        hitbox_width = 70
        hitbox_height = 90
        
        # Scale untuk sprite
        sprite_scale = 2.5
        
        # 2. PANGGIL CONSTRUCTOR PARENT (BaseEnemy)
        super().__init__(
            x=x, y=y,
            width=hitbox_width, height=hitbox_height,
            max_hp=stats_hp,
            attack_power=stats_attack,
            speed=stats_speed,
            asset_path=BRINGER_OF_DEATH_ASSET_PATH,
            scale=sprite_scale
        )
        
        # 3. OVERRIDE DETECTION RANGES (Boss lebih agresif, lebih suka range)
        self.detection_range = 500
        self.attack_range = 60      # Melee range
        self.spell_cast_range = 350 # Range untuk cast spell
        
        # 4. COMBAT STATE
        self.is_casting = False
        self.spell_cooldown = 0
        self.spell_cooldown_max = 120  # 2 detik (60 FPS)
        
        # 5. SETUP ANIMASI
        self._setup_animations()
    
    def _setup_animations(self):
        """
        Load semua sprite animasi untuk Bringer of Death.
        
        Mapping folder (case-sensitive!):
        - idle -> Idle
        - walk -> Walk
        - attack -> Attack
        - cast -> Cast
        - spell -> Spell
        - hurt -> Hurt
        - die -> Death
        """
        animation_mapping = {
            'idle': 'Idle',
            'walk': 'Walk',
            'attack': 'Attack',
            'cast': 'Cast',
            'spell': 'Spell',
            'hurt': 'Hurt',
            'die': 'Death',
        }
        
        self.animator.load_sprites(animation_mapping)
        
        # Set animation speed
        self.cast_animation_speed = 0.12
        self.spell_animation_speed = 0.15
    
    def update(self, dt):
        """
        Override update untuk behavior khusus Bringer of Death.
        """
        # Update spell cooldown
        if self.spell_cooldown > 0:
            self.spell_cooldown -= 1
        
        # Panggil update parent (AI logic, physics, dll)
        super().update(dt)
        
        # Custom AI: Prefer spell cast jika player dalam range dan cooldown ready
        if self.ai_state == self.STATE_CHASE:
            distance = self.get_distance_to_player()
            
            # Jika player dalam spell range tapi di luar melee range
            if distance <= self.spell_cast_range and distance > self.attack_range:
                if self.spell_cooldown <= 0 and not self.is_casting:
                    self.ai_state = 'cast'  # Custom state untuk casting
                    self.is_casting = True
                    self.animator.reset_animation()
    
    def handle_ai_cast(self):
        """
        Handle AI state saat casting spell.
        """
        # Stop movement saat casting
        self.physics.velocity_x = 0
        
        # Tunggu animasi cast selesai
        if self.animator.is_animation_finished():
            # Spawn spell projectile
            self.spawn_spell()
            
            # Mulai cooldown
            self.spell_cooldown = self.spell_cooldown_max
            self.is_casting = False
            
            # Kembali ke chase
            self.ai_state = self.STATE_CHASE
    
    def spawn_spell(self):
        """
        Spawn projectile spell ke arah player.
        TODO: Implementasi projectile system.
        """
        # Placeholder untuk spell spawn logic
        # Nanti bisa ditambahkan projectile entity
        pass
    
    def render_sprite(self, camera):
        """
        Override render untuk animasi khusus.
        """
        # Tentukan state animasi
        anim_state = self.ai_state
        
        # Jika lagi casting, gunakan animasi cast
        if self.is_casting:
            anim_state = 'cast'
        
        # Tentukan speed animasi berdasarkan state
        anim_speed = self.animator.animation_speed
        
        if anim_state == 'cast':
            anim_speed = self.cast_animation_speed
        elif anim_state == 'spell':
            anim_speed = self.spell_animation_speed
        
        # Dapatkan frame animasi
        sprite = self.animator.animate(
            state=anim_state,
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
    
    def _update_ai(self):
        """
        Override AI update untuk handle cast state.
        """
        # Jika lagi casting, handle cast logic
        if self.is_casting:
            self.handle_ai_cast()
            return
        
        # Kalau tidak casting, jalankan AI normal
        super()._update_ai()
