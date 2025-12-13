import pygame as pg
from game.settings import WINDOW_SIZE, TITLE
from game.screens.main_menu import MainMenu
from game.game_manager import Game

def main():
    """
    Entry point utama game.
    Flow: Main Menu -> Game -> (Loop back to menu atau Quit)
    """
    pg.init()
    screen = pg.display.set_mode(WINDOW_SIZE)
    pg.display.set_caption(TITLE)
    
    running = True
    
    while running:
        # 1. Tampilkan Main Menu
        menu = MainMenu(screen)
        action = menu.run()
        
        # 2. Handle menu action
        if action == "new_game":
            # Mulai game baru
            game = Game()
            game.run()
            # Setelah game selesai, kembali ke menu
            
        elif action == "continue":
            # TODO: Load saved game
            print("[INFO] Continue - Loading save... (Not implemented)")
            game = Game()
            game.run()
            
        elif action == "quit":
            running = False
    
    pg.quit()


if __name__ == '__main__':
    main()
    g = Game()
    g.run()
    pg.quit()
