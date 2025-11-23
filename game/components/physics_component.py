import pygame as pg
from game.settings import GRAVITY, TERMINAL_VELOCITY, JUMP_STRENGTH

class PhysicsComponent:
    def __init__(self, rect):
        self.rect = rect
        self.velocity = pg.Vector2(0, 0)
        self.on_ground = False
        self.facing_right = True
        
        # [PERBAIKAN] Simpan posisi akurat (float) terpisah dari rect
        # Ini penting agar nilai koma (0.8) tidak hilang saat gerak lambat
        self.pos = pg.Vector2(rect.x, rect.y)

    def apply_gravity(self):
        self.velocity.y += GRAVITY
        if self.velocity.y > TERMINAL_VELOCITY:
            self.velocity.y = TERMINAL_VELOCITY

    def move_and_collide(self, platforms, x_velocity):
        # 1. Gerakan Horizontal
        self.pos.x += x_velocity
        self.rect.x = round(self.pos.x) # Update rect visual dari posisi float
        
        # Update arah hadap (untuk animasi)
        if x_velocity > 0:
            self.facing_right = True
        elif x_velocity < 0:
            self.facing_right = False

        for platform in platforms:
            if self.rect.colliderect(platform):
                if x_velocity > 0: # Ke Kanan
                    self.rect.right = platform.left
                if x_velocity < 0: # Ke Kiri
                    self.rect.left = platform.right
                # Sinkronkan kembali posisi float agar tidak tembus
                self.pos.x = self.rect.x
        
        # 2. Gerakan Vertikal
        self.on_ground = False 
        self.pos.y += self.velocity.y
        self.rect.y = round(self.pos.y) # Update rect visual dari posisi float

        for platform in platforms:
            if self.rect.colliderect(platform):
                if self.velocity.y > 0: # Jatuh ke lantai
                    self.rect.bottom = platform.top
                    self.velocity.y = 0
                    self.on_ground = True
                if self.velocity.y < 0: # Mentok atap
                    self.rect.top = platform.bottom
                    self.velocity.y = 0
                
                # Sinkronkan kembali posisi float ke posisi rect yang baru (setelah tabrakan)
                self.pos.y = self.rect.y

    def jump(self):
        if self.on_ground:
            self.velocity.y = JUMP_STRENGTH
            self.on_ground = False

    def update(self, platforms, x_velocity):
        self.apply_gravity()
        self.move_and_collide(platforms, x_velocity)