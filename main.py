import pygame as pg
from game.game_manager import Game

if __name__ == '__main__':
    # 1. Buat objek game
    g = Game()
    
    # 2. Jalankan game loop-nya
    g.run()
    
    # 3. Keluar saat game loop selesai
    pg.quit()