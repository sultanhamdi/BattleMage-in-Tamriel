import pygame as pg
from game.settings import PLAYER_SPEED
# Impor komponen baru kita
from game.components.physics_component import PhysicsComponent 

class Player:
    def __init__(self, x, y):
        # Player masih memiliki Rect-nya sendiri
        self.rect = pg.Rect(x, y, 32, 64) 
        self.color = (0, 100, 255) 
        
        # Player masih tahu seberapa cepat dia bisa bergerak
        self.movement_speed = PLAYER_SPEED
        
        # --- INI INTI PBO-NYA ---
        # Player "memiliki" sebuah PhysicsComponent
        # Kita berikan rect kita ke komponen itu
        self.physics = PhysicsComponent(self.rect)
        
        # TIDAK ADA LAGI self.velocity, self.gravity, dll. di sini!

    def get_input(self):
        keys = pg.key.get_pressed()
        
        # Player hanya memutuskan "kecepatan horizontal"
        x_velocity = 0
        if keys[pg.K_LEFT] or keys[pg.K_a]:
            x_velocity = -self.movement_speed
        if keys[pg.K_RIGHT] or keys[pg.K_d]:
            x_velocity = self.movement_speed
            
        return x_velocity

    def jump(self):
        # Player mendelegasikan tugas "lompat" ke komponen fisika
        self.physics.jump()

    def update(self, platforms):
        # Update() Player sekarang SANGAT BERSIH:
        
        # 1. Dapatkan input kecepatan horizontal
        x_vel = self.get_input()
        
        # 2. Suruh komponen fisika untuk bekerja
        self.physics.update(platforms, x_vel)
        
        # self.rect.x dan self.rect.y akan diperbarui secara otomatis
        # oleh self.physics karena kita memberinya self.rect

    def draw(self, screen):
        # Draw tetap sama
        pg.draw.rect(screen, self.color, self.rect)