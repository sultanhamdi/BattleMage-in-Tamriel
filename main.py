import pygame as pg
from game.game_manager import Game

if __name__ == '__main__':
    g = Game()
    g.run()
    pg.quit()