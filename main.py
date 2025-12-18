import pygame as pg
from game.settings import WINDOW_SIZE, TITLE
from game.screens.main_menu import MainMenu
from game.game_manager import Game

def main():
    pg.init()
    screen = pg.display.set_mode(WINDOW_SIZE)
    pg.display.set_caption(TITLE)
    
    running = True
    
    while running:
        # Main Menu
        menu = MainMenu(screen)
        action = menu.run()
        
        # Handle menu action
        if action == "new_game":
            # Mulai game baru
            game = Game()
            game.run()
        
            
        elif action == "continue":
            # Load saved game
            print("[INFO] Continue - Loading save... (Not implemented)")
            game = Game()
            game.run()
            
        elif action == "quit":
            running = False
    
    pg.quit()


if __name__ == '__main__':
    main()
