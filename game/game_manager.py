import pygame as pg
# Impor variabel baru dari settings.py
from .settings import FPS, WINDOW_SIZE, FULLSCREEN_SIZE 
from .entities.player import Player # <--- 1. IMPORT PLAYER

class Game:
    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode(WINDOW_SIZE) 
        pg.display.set_caption("Nama Game Anda")
        
        self.clock = pg.time.Clock()
        self.running = True
        self.fullscreen = False 
        
        # <--- 2. BUAT OBJEK PLAYER
        # (100, 100) adalah posisi x, y awal
        self.player = Player(100, 100) 

        # <--- 1. BUAT LANTAI SEDERHANA
        # Ini adalah sebuah 'list' berisi semua objek yang bisa dipijak
        # Kita buat satu lantai besar di Y=600 dengan tinggi 100
        self.platforms = [
            pg.Rect(0, 600, WINDOW_SIZE[0], 100) # (x, y, lebar, tinggi)
        ]

    def run(self):
        while self.running:
            self.events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

    def events(self):
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.running = False
                
                # Cek jika ada tombol DITEKAN
                if event.type == pg.KEYDOWN:
                    
                    # Opsi 1: Toggle Fullscreen
                    if event.key == pg.K_F4: 
                        self.toggle_fullscreen()
                    
                    # Opsi 2: Lompat (Gunakan ELIF)
                    elif event.key == pg.K_SPACE or event.key == pg.K_w or event.key == pg.K_UP:
                        self.player.jump()


    def update(self):
        # <--- 3. PANGGIL UPDATE PLAYER
        self.player.update(self.platforms) 

    def draw(self):
        self.screen.fill((0, 0, 0)) # Isi layar dengan warna hitam
        
        # <--- 4. PANGGIL DRAW PLAYER
        self.player.draw(self.screen)
        for platform in self.platforms:
            pg.draw.rect(self.screen, (100, 100, 100), platform)
        pg.display.flip()
        
    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.screen = pg.display.set_mode(FULLSCREEN_SIZE, pg.FULLSCREEN)
        else:
            self.screen = pg.display.set_mode(WINDOW_SIZE)
        pass