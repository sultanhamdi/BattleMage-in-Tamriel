import pygame as pg
import sys
from game.settings import *
from game.entities.player import Player
from game.utils.camera import Camera # Import Kamera

class Game:
    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode(WINDOW_SIZE)
        pg.display.set_caption(TITLE)
        self.clock = pg.time.Clock()
        self.running = True
        
        # 1. Spawn player
        self.player = Player(100, WINDOW_HEIGHT - 150)
        
        # 2. Inisialisasi Kamera
        self.camera = Camera(WINDOW_WIDTH, WINDOW_HEIGHT)
        
        # 3. Level Dummy (Ditambah platform jauh di X=1200++ untuk tes scroll)
        self.platforms = [
            # Lantai awal
            pg.Rect(0, WINDOW_HEIGHT - 40, WINDOW_WIDTH, 40), 
            # Platform lompatan awal
            pg.Rect(300, 500, 200, 20),
            pg.Rect(600, 400, 200, 20),
            pg.Rect(100, 300, 150, 20),
            # [BARU] Platform Jauh (Coba jalan ke kanan untuk menemukannya)
            pg.Rect(1200, 500, 200, 20), 
            pg.Rect(1500, 400, 200, 20),
            pg.Rect(1800, 600, 500, 40), # Lantai jauh
        ]

    def events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
                pg.quit()
                sys.exit()
            
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_F4:
                    is_fullscreen = self.screen.get_flags() & pg.FULLSCREEN
                    if is_fullscreen:
                        self.screen = pg.display.set_mode(WINDOW_SIZE)
                    else:
                        self.screen = pg.display.set_mode(WINDOW_SIZE, pg.FULLSCREEN)
                
                if event.key == pg.K_SPACE or event.key == pg.K_w:
                    self.player.jump()

    def update(self):
        # Update Player
        self.player.update(self.platforms)
        
        # [KAMERA] Update posisi kamera mengikuti player
        self.camera.follow(self.player.rect)

    def draw(self):
        self.screen.fill(BG_COLOR)
        
        # [KAMERA] Gambar Platform dengan Offset
        for plat in self.platforms:
            # Buat salinan rect visual yang sudah digeser kamera
            draw_plat = plat.copy()
            draw_plat.x -= self.camera.offset.x
            draw_plat.y -= self.camera.offset.y
            pg.draw.rect(self.screen, GRAY, draw_plat)

        # [KAMERA] Gambar Player dengan Offset
        # Kita kirim data offset kamera ke fungsi draw player
        self.player.draw(self.screen, self.camera.offset)
        
        pg.display.flip()

    def run(self):
        while self.running:
            self.events()
            self.update()
            self.draw()
            self.clock.tick(FPS)