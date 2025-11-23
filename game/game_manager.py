# game/game_manager.py
import pygame as pg
import sys
from game.settings import *
from game.entities.player import Player

class Game:
    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode(WINDOW_SIZE)
        pg.display.set_caption(TITLE)
        self.clock = pg.time.Clock()
        self.running = True
        
        # Spawn player
        self.player = Player(100, WINDOW_HEIGHT - 150)
        
        # Level Dummy (Lantai & Platform)
        self.platforms = [
            pg.Rect(0, WINDOW_HEIGHT - 40, WINDOW_WIDTH, 40), # Lantai
            pg.Rect(300, 500, 200, 20),
            pg.Rect(600, 400, 200, 20),
            pg.Rect(100, 300, 150, 20)
        ]

    def events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
                pg.quit()
                sys.exit()
            
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_F4:
                    # Toggle Fullscreen
                    is_fullscreen = self.screen.get_flags() & pg.FULLSCREEN
                    if is_fullscreen:
                        self.screen = pg.display.set_mode(WINDOW_SIZE)
                    else:
                        self.screen = pg.display.set_mode(WINDOW_SIZE, pg.FULLSCREEN)
                
                # Input Lompat
                if event.key == pg.K_SPACE or event.key == pg.K_w:
                    self.player.jump()

    def update(self):
        self.player.update(self.platforms)

    def draw(self):
        self.screen.fill(BG_COLOR)
        
        # Draw Platforms
        for plat in self.platforms:
            pg.draw.rect(self.screen, GRAY, plat)

        # Draw Player
        self.player.draw(self.screen)
        
        pg.display.flip()

    def run(self):
        while self.running:
            self.events()
            self.update()
            self.draw()
            self.clock.tick(FPS)