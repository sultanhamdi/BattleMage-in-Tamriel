import pygame as pg
import sys
from game.settings import *
from game.entities.player import Player
from game.utils.camera import Camera
from game.level.level_manager import LevelManager

class Game:
    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode(WINDOW_SIZE)
        pg.display.set_caption(TITLE)
        self.clock = pg.time.Clock()
        self.running = True
        
        # Inisialisasi Kamera
        self.camera = Camera(WINDOW_WIDTH, WINDOW_HEIGHT)
        
        # Setup Level Manager
        self.level_manager = LevelManager(current_theme='dungeon')
        
        # Generate Rects, Gambar, dan Spawn Point dari Map
        self.platforms, self.visual_tiles, spawn_point, finish_rect = self.level_manager.create_level()
        
        # Hitung Ukuran Level (World Size)
        max_x = 0
        max_y = 0
        if self.visual_tiles:
            max_x = max(r.right for _, r in self.visual_tiles)
            max_y = max(r.bottom for _, r in self.visual_tiles)
        else:
            max_x = WINDOW_WIDTH
            max_y = WINDOW_HEIGHT
            
        # Tambahkan sedikit padding
        level_width = max(WINDOW_WIDTH, max_x)
        level_height = max(WINDOW_HEIGHT, max_y)
        self.camera.set_world_size(level_width, level_height)
        
        self.background = self.level_manager.create_world_background(level_width, level_height)
        self.void_image = self.level_manager.tile_images.get('#')
        
        # Spawn player
        self.player = Player(spawn_point[0], spawn_point[1])
        
        # Level Transition
        self.finish_rect = finish_rect
        self.transitioning = False
        self.fade_alpha = 0
        self.fade_speed = 5
        self.fade_surface = pg.Surface(WINDOW_SIZE)
        self.fade_surface.fill((0, 0, 0))
        self.fade_state = 'IN'

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
                
                if event.key == pg.K_UP or event.key == pg.K_SPACE:
                    self.player.jump()

    def update(self):
        # Update Player & Camera (Hanya jika tidak sedang transisi penuh)
        if not self.transitioning or (self.transitioning and self.fade_state == 'IN'):
            self.player.update(self.platforms)
            self.camera.follow(self.player.rect)
        
        # Cek Finish Point Trigger
        if self.finish_rect and not self.transitioning:
            if self.player.rect.colliderect(self.finish_rect):
                print("[EVENT] Player reached finish point! Starting transition...")
                self.transitioning = True
                self.fade_state = 'OUT' 

        # Handle Transition Fade
        if self.transitioning:
            if self.fade_state == 'OUT':
                self.fade_alpha += self.fade_speed
                if self.fade_alpha >= 255:
                    self.fade_alpha = 255
                    # Layar sudah hitam pekat, Ganti Level
                    self.change_level()
                    self.fade_state = 'IN'
            
            elif self.fade_state == 'IN':
                self.fade_alpha -= self.fade_speed
                if self.fade_alpha <= 0:
                    self.fade_alpha = 0
                    self.transitioning = False
                    
    def change_level(self):
        # Naikkan index level
        next_level_index = self.level_manager.current_level_index + 1
        
        # Cek apakah level selanjutnya ada
        if next_level_index < len(self.level_manager.levels):
            print(f"[INFO] Loading Level {next_level_index + 1}...")
            self.level_manager.set_level(next_level_index)
            
            # Re-Generate Level
            self.platforms, self.visual_tiles, spawn_point, finish_rect = self.level_manager.create_level()
            self.finish_rect = finish_rect
            
            # Re-Calculate Background Size
            max_x = 0
            max_y = 0
            if self.visual_tiles:
                max_x = max(r.right for _, r in self.visual_tiles)
                max_y = max(r.bottom for _, r in self.visual_tiles)
            else:
                max_x = WINDOW_WIDTH
                max_y = WINDOW_HEIGHT
            
            level_width = max(WINDOW_WIDTH, max_x)
            level_height = max(WINDOW_HEIGHT, max_y)
            self.camera.set_world_size(level_width, level_height)
            
            # Re-Create Background (World Size)
            self.background = self.level_manager.create_world_background(level_width, level_height)
            self.void_image = self.level_manager.tile_images.get('#')
            
            # Reset Player Position & Camera
            self.player.rect.topleft = spawn_point
            self.player.physics.pos.x = spawn_point[0]
            self.player.physics.pos.y = spawn_point[1]
            self.player.physics.velocity.xy = (0, 0)
            
            self.camera.follow(self.player.rect)
            
        else:
            print("[INFO] No more levels! Game Completed.")
            self.level_manager.set_level(0)
            self.change_level()

    def draw(self):
        # Draw Void Background (Infinite Wall)
        if self.void_image:
            # Hitung offset tile agar seamless
            tile_w = self.void_image.get_width()
            tile_h = self.void_image.get_height()
            
            start_x = -int(self.camera.offset.x) % tile_w
            start_y = -int(self.camera.offset.y) % tile_h
            
            # Gambar dengan buffer ekstra agar tidak putus saat scrolling
            for x in range(start_x - tile_w, WINDOW_WIDTH + tile_w, tile_w):
                for y in range(start_y - tile_h, WINDOW_HEIGHT + tile_h, tile_h):
                    self.screen.blit(self.void_image, (x, y))
        else:
            self.screen.fill(BG_COLOR)
        
        # Draw Level Background (Dungeon Image)
        bg_x = -self.camera.offset.x
        bg_y = -self.camera.offset.y
        self.screen.blit(self.background, (bg_x, bg_y))
        
        # Gambar Tileset
        for img, rect in self.visual_tiles:
            draw_pos_x = rect.x - self.camera.offset.x
            draw_pos_y = rect.y - self.camera.offset.y
            self.screen.blit(img, (draw_pos_x, draw_pos_y))

        # Gambar Player
        self.player.draw(self.screen, self.camera.offset)
        
        # Draw Fade Overlay
        if self.transitioning or self.fade_alpha > 0:
            self.fade_surface.set_alpha(self.fade_alpha)
            self.screen.blit(self.fade_surface, (0, 0))
        
        pg.display.flip()

    def run(self):
        while self.running:
            self.events()
            self.update()
            self.draw()
            self.clock.tick(FPS)