import pygame as pg
import sys
from game.settings import *
from game.entities.player import Player
from game.utils.camera import Camera
from game.level.level_manager import LevelManager # Import LevelManager

class Game:
    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode(WINDOW_SIZE)
        pg.display.set_caption(TITLE)
        self.clock = pg.time.Clock()
        self.running = True
        
        # 1. Spawn player (Posisi sementara, nanti kita ambil dari map)
        self.player = Player(100, 100)
        
        # 2. Inisialisasi Kamera
        self.camera = Camera(WINDOW_WIDTH, WINDOW_HEIGHT)
        
        # 3. [BARU] Setup Level Manager
        self.level_manager = LevelManager(current_theme='dungeon')
        
        # Generate Rects dan Gambar dari Map Teks
        # self.platforms: Untuk collision (Fisika)
        # self.visual_tiles: Untuk digambar (Visual)
        self.platforms, self.visual_tiles = self.level_manager.create_level()

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
                
                if event.key == pg.K_SPACE or event.key == pg.K_w or event.key == pg.K_UP:
                    self.player.jump()

    def update(self):
        # Update Player (cek tabrakan dengan rects dari level manager)
        self.player.update(self.platforms)
        
        # Update Kamera
        self.camera.follow(self.player.rect)

    def draw(self):
        self.screen.fill(BG_COLOR)
        
        # [BARU] Gambar Tileset (Lantai Bergambar)
        for img, rect in self.visual_tiles:
            # Terapkan Offset Kamera
            draw_pos_x = rect.x - self.camera.offset.x
            draw_pos_y = rect.y - self.camera.offset.y
            self.screen.blit(img, (draw_pos_x, draw_pos_y))

        # Gambar Player
        self.player.draw(self.screen, self.camera.offset)
        
        pg.display.flip()

    def run(self):
        while self.running:
            self.events()
            self.update()
            self.draw()
            self.clock.tick(FPS)