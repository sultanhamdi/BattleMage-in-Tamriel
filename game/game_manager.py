import pygame as pg
import sys
from game.settings import *
from game.entities.player import Player
from game.utils.camera import Camera
from game.level.level_manager import LevelManager
from game.items.item_manager import ItemManager

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
        self.platforms, self.visual_tiles, spawn_point, finish_rect, self.bg_images = self.level_manager.create_level()
        
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
        
        # Use TMX background if available, otherwise fallback
        if not self.bg_images:
            self.background = self.level_manager.create_world_background(level_width, level_height)
        else:
            self.background = None
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
        
        # Item System
        self.item_manager = ItemManager()
        self.awaiting_item_selection = False
        self.current_item_choices = []  # [item_id, item_id]
        self.selected_item_index = 0    # For UI navigation (0 or 1)

    def events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
                pg.quit()
                sys.exit()
            
            if event.type == pg.KEYDOWN:
                # Handle Item Selection Input (Block other inputs)
                if self.awaiting_item_selection:
                    if event.key == pg.K_LEFT:
                        self.selected_item_index = 0
                    elif event.key == pg.K_RIGHT:
                        self.selected_item_index = 1
                    elif event.key == pg.K_1:
                        self.confirm_item_selection(0)
                    elif event.key == pg.K_2:
                        self.confirm_item_selection(1)
                    elif event.key == pg.K_RETURN or event.key == pg.K_SPACE:
                        self.confirm_item_selection(self.selected_item_index)
                    continue  # Block other inputs during item selection
                
                if event.key == pg.K_F4:
                    is_fullscreen = self.screen.get_flags() & pg.FULLSCREEN
                    if is_fullscreen:
                        self.screen = pg.display.set_mode(WINDOW_SIZE)
                    else:
                        self.screen = pg.display.set_mode(WINDOW_SIZE, pg.FULLSCREEN)
                
                if event.key == pg.K_UP or event.key == pg.K_SPACE:
                    self.player.jump()
                
                # Cheat: Press F to instantly finish level (for development)
                if event.key == pg.K_f:
                    if not self.transitioning:
                        print("[CHEAT] Skipping level...")
                        self.transitioning = True
                        self.fade_state = 'OUT'
    
    def confirm_item_selection(self, index):
        """Player confirms item selection"""
        if index < len(self.current_item_choices):
            item_id = self.current_item_choices[index]
            
            # Pick and apply item
            self.item_manager.pick_item(item_id)
            self.item_manager.apply_item_to_player(self.player, item_id)
            
            # Clear selection state
            self.awaiting_item_selection = False
            self.current_item_choices = []
            
            print(f"[ITEM] Applied: {item_id}")

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
            
            # Trigger Item Selection (if items available)
            if self.item_manager.get_pool_size() >= 2:
                self.current_item_choices = self.item_manager.get_random_choices(2)
                self.awaiting_item_selection = True
                self.selected_item_index = 0
                print(f"[ITEM] Choose: {self.current_item_choices}")
            
            self.level_manager.set_level(next_level_index)
            
            # Re-Generate Level
            self.platforms, self.visual_tiles, spawn_point, finish_rect, self.bg_images = self.level_manager.create_level()
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
            
            # Use TMX background if available, otherwise fallback
            if not self.bg_images:
                self.background = self.level_manager.create_world_background(level_width, level_height)
            else:
                self.background = None
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
        
        # Draw Level Background
        if self.bg_images:
            # Render TMX image layers
            for bg_data in self.bg_images:
                bg_img, offset_x, offset_y, repeat_x, repeat_y = bg_data
                
                img_w = bg_img.get_width()
                img_h = bg_img.get_height()
                
                if repeat_x or repeat_y:
                    # Tiling mode
                    start_x = int(offset_x - self.camera.offset.x) % img_w - img_w
                    start_y = int(offset_y - self.camera.offset.y) % img_h - img_h
                    
                    # Calculate tiling range
                    end_x = WINDOW_WIDTH + img_w if repeat_x else start_x + img_w
                    end_y = WINDOW_HEIGHT + img_h if repeat_y else start_y + img_h
                    step_x = img_w if repeat_x else img_w * 999  # Large step if no repeat
                    step_y = img_h if repeat_y else img_h * 999
                    
                    for x in range(start_x, int(end_x), step_x):
                        for y in range(start_y, int(end_y), step_y):
                            self.screen.blit(bg_img, (x, y))
                else:
                    # Single image mode
                    bg_x = offset_x - self.camera.offset.x
                    bg_y = offset_y - self.camera.offset.y
                    self.screen.blit(bg_img, (bg_x, bg_y))
        elif self.background:
            # Fallback to generated background
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