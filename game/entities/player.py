import pygame as pg
from game.settings import PLAYER_SPEED, PLAYER_ASSET_PATH, BLUE
from game.components.physics_component import PhysicsComponent
from game.utils.animation_handler import AnimationHandler

class Player:
    def __init__(self, x, y):
        # [DIMENSI PRESISI SESUAI ASET ANDA]
        self.frame_width = 56   
        self.frame_height = 48  
        
        self.scale = 3 # Diperbesar 3x
        
        # [HITBOX]
        # Ukuran fisik karakter di dunia game
        self.rect = pg.Rect(x, y, 40, 80) 
        
        self.physics = PhysicsComponent(self.rect)
        self.animator = AnimationHandler(PLAYER_ASSET_PATH, self.frame_width, self.frame_height, self.scale)

        self.animation_types = ['idle', 'run', 'jump', 'fall', 'attack1', 'death', 'hurt']
        self.animator.load_sprites(self.animation_types)
        
        self.status = 'idle'
        self.movement_speed = PLAYER_SPEED

    def get_input(self):
        keys = pg.key.get_pressed()
        x_velocity = 0
        if keys[pg.K_LEFT] or keys[pg.K_a]:
            x_velocity = -self.movement_speed
        if keys[pg.K_RIGHT] or keys[pg.K_d]:
            x_velocity = self.movement_speed
        return x_velocity

    # [PERBAIKAN] Fungsi sekarang menerima parameter kecepatan x
    def get_status(self, x_velocity):
        # Prioritas 1: Udara (Lompat/Jatuh)
        if self.physics.velocity.y < 0:
            self.status = 'jump'
        elif self.physics.velocity.y > 1:
            self.status = 'fall'
        
        # Prioritas 2: Tanah (Lari/Diam)
        else:
            # Jika ada input gerak DAN menapak tanah -> Run
            if x_velocity != 0 and self.physics.on_ground: 
                 self.status = 'run'
            # Jika tidak ada input gerak DAN menapak tanah -> Idle
            elif self.physics.on_ground: 
                 self.status = 'idle'

    def jump(self):
        self.physics.jump()

    def update(self, platforms):
        # 1. Ambil input
        x_vel = self.get_input()
        
        # 2. Update Fisika
        self.physics.update(platforms, x_vel)
        
        # 3. [PERBAIKAN] Update Status Animasi dengan mengirim data input
        self.get_status(x_vel)

    def draw(self, surface):
        current_frame = self.animator.animate(self.status, 0.1, self.physics.facing_right)

        if current_frame:
            # Hitung posisi gambar agar hitbox ada di tengah-tengah
            img_width = current_frame.get_width()
            img_height = current_frame.get_height()
            
            offset_x = (img_width - self.rect.width) // 2
            offset_y = img_height - self.rect.height
            
            # Gambar sprite di posisi yang sudah disesuaikan offset-nya
            surface.blit(current_frame, (self.rect.x - offset_x, self.rect.y - offset_y))
        else:
            # Fallback jika gambar gagal load
            color = BLUE
            if self.status == 'jump': color = (0, 255, 255)
            pg.draw.rect(surface, color, self.rect)