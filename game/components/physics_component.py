import pygame as pg
from game.settings import PLAYER_GRAVITY, PLAYER_JUMP_STRENGTH

class PhysicsComponent:
    def __init__(self, entity_rect):
        # Komponen ini "memegang" referensi ke rect milik si pemilik (Player)
        # Ini adalah inti dari Komposisi!
        self.rect = entity_rect 
        
        # Variabel fisika dipindahkan ke sini
        self.velocity = pg.Vector2(0, 0)
        self.gravity = PLAYER_GRAVITY
        self.jump_strength = PLAYER_JUMP_STRENGTH
        self.on_ground = False

    def apply_gravity(self):
        self.velocity.y += self.gravity
        if self.velocity.y > 15:
            self.velocity.y = 15

    def move_and_collide(self, platforms, x_velocity):
        # Pindahkan sumbu X dan cek tabrakan horizontal
        # Kita terima x_velocity dari si pemilik (Player)
        self.rect.x += x_velocity
        for platform in platforms:
            if self.rect.colliderect(platform):
                if x_velocity > 0: # Bergerak ke kanan
                    self.rect.right = platform.left
                if x_velocity < 0: # Bergerak ke kiri
                    self.rect.left = platform.right
        
        # Reset status on_ground sebelum cek vertikal
        self.on_ground = False
        
        # Pindahkan sumbu Y dan cek tabrakan vertikal
        self.rect.y += self.velocity.y
        for platform in platforms:
            if self.rect.colliderect(platform):
                if self.velocity.y > 0: # Bergerak ke bawah (jatuh)
                    self.rect.bottom = platform.top
                    self.velocity.y = 0 # Berhenti jatuh
                    self.on_ground = True # Tandai bahwa kita di tanah
                if self.velocity.y < 0: # Bergerak ke atas (lompat)
                    self.rect.top = platform.bottom
                    self.velocity.y = 0 # Hentikan momentum ke atas

    def jump(self):
        # Logika lompat tetap di sini
        if self.on_ground:
            self.velocity.y = self.jump_strength
            self.on_ground = False

    def update(self, platforms, x_velocity):
        # Fungsi update utama untuk fisika
        self.apply_gravity()
        self.move_and_collide(platforms, x_velocity)