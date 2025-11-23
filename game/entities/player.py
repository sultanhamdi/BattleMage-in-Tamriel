import pygame as pg
from game.settings import PLAYER_SPEED, PLAYER_ASSET_PATH, BLUE
from game.components.physics_component import PhysicsComponent
from game.utils.animation_handler import AnimationHandler

class Player:
    def __init__(self, x, y):
        # [DIMENSI PRESISI SESUAI ASET ANDA]
        # Idle/Run: 56x... (Tinggi frame 48px)
        self.frame_width = 56   
        self.frame_height = 48  
        self.scale = 3 
        
        # [HITBOX]
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

    def get_status(self, x_velocity):
        # Prioritas 1: Udara
        if self.physics.velocity.y < 0:
            self.status = 'jump'
        elif self.physics.velocity.y > 1:
            self.status = 'fall'
        # Prioritas 2: Tanah
        else:
            if x_velocity != 0 and self.physics.on_ground: 
                 self.status = 'run'
            elif self.physics.on_ground: 
                 self.status = 'idle'

    def jump(self):
        self.physics.jump()

    def update(self, platforms):
        x_vel = self.get_input()
        self.physics.update(platforms, x_vel)
        self.get_status(x_vel)

    # [UPDATE KAMERA] Menerima parameter camera_offset
    def draw(self, surface, camera_offset):
        current_frame = self.animator.animate(self.status, 0.1, self.physics.facing_right)

        if current_frame:
            img_width = current_frame.get_width()
            img_height = current_frame.get_height()
            
            # Hitung offset agar gambar pas di tengah hitbox
            offset_x = (img_width - self.rect.width) // 2
            offset_y = img_height - self.rect.height
            
            # [LOGIKA KAMERA]
            # Posisi Gambar = Posisi Asli - Posisi Kamera - Offset Gambar
            draw_pos_x = self.rect.x - camera_offset.x - offset_x
            draw_pos_y = self.rect.y - camera_offset.y - offset_y
            
            surface.blit(current_frame, (draw_pos_x, draw_pos_y))
        else:
            # Fallback (Kotak Biru) juga harus kena efek kamera
            color = BLUE
            if self.status == 'jump': color = (0, 255, 255)
            
            draw_rect = self.rect.copy()
            draw_rect.x -= camera_offset.x
            draw_rect.y -= camera_offset.y
            pg.draw.rect(surface, color, draw_rect)