import pygame as pg
# Impor variabel baru dari settings.py
from .settings import FPS, WINDOW_SIZE, FULLSCREEN_SIZE 

class Game:
    def __init__(self):
        pg.init()
        # Mulai game dalam mode WINDOWED
        self.screen = pg.display.set_mode(WINDOW_SIZE) 
        pg.display.set_caption("Nama Game Anda")
        
        self.clock = pg.time.Clock()
        self.running = True
        
        # Tambahkan variabel pelacak status
        self.fullscreen = False 

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
            
            # Tambahkan event handler untuk tombol
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_F4: # Jika tombol 'F' ditekan
                    self.toggle_fullscreen() # Panggil fungsi pengalih

    def update(self):
        pass 

    def draw(self):
        self.screen.fill((0, 0, 0)) 
        pg.display.flip()
        
    # --- FUNGSI BARU ---
    def toggle_fullscreen(self):
        # Balikkan status
        self.fullscreen = not self.fullscreen
        
        if self.fullscreen:
            # Jika True, ubah ke fullscreen
            self.screen = pg.display.set_mode(FULLSCREEN_SIZE, pg.FULLSCREEN)
        else:
            # Jika False, kembali ke windowed
            self.screen = pg.display.set_mode(WINDOW_SIZE)