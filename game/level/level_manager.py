import pygame as pg
import os
from game.settings import TILE_SIZE, SCALE, SCALED_TILE_SIZE, BACKGROUNDS
import game.level.level1 as level1
import game.level.level2 as level2

THEMES = {
    'dungeon': 'assets/graphics/tilesets/dungeon.png',
}

class LevelManager:
    def __init__(self, current_theme='dungeon'):
        self.tile_images = {}
        self.theme = current_theme
        
        # Mapping Karakter : Koordinat Tileset (Col, Row)
        self.tile_map_coords = {
            'X': (1, 0), # Dinding Atas
            '#': (1, 1), # Dinding Tengah/Tiang
            '|': (1, 1), # Dinding Vertical (Reuse Tiang)
            '_': (1, 4), # Lantai
            '=': (3, 1), # Platform
        }
        
        self.load_assets()
        
        # Level Management
        self.levels = [level1.level_data, level2.level_data]
        self.current_level_index = 0
        self.level_map = self.levels[self.current_level_index]

    def set_level(self, index):
        if 0 <= index < len(self.levels):
            self.current_level_index = index
            self.level_map = self.levels[index]
            return True
        return False

    def load_assets(self):
        path = THEMES.get(self.theme)
        if not path or not os.path.exists(path):
            print(f"[ERROR] Tileset not found: {path}")
            return

        try:
            tileset = pg.image.load(path).convert_alpha()
            
            for char, (col, row) in self.tile_map_coords.items():
                rect_source = (col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                
                # Cek bounds
                if rect_source[0] + TILE_SIZE > tileset.get_width() or \
                   rect_source[1] + TILE_SIZE > tileset.get_height():
                    print(f"[WARNING] Tile coord ({col},{row}) out of bounds for {self.theme}")
                    continue
                    
                image = tileset.subsurface(rect_source)
                
                # Perbesar gambar
                image = pg.transform.scale(image, (SCALED_TILE_SIZE, SCALED_TILE_SIZE))
                
                self.tile_images[char] = image
            
            print(f"[INFO] Loaded {len(self.tile_images)} tiles for theme: {self.theme}")
            
        except Exception as e:
            print(f"[ERROR] Failed to load tileset: {e}")

    def create_world_background(self, width, height, tile_char=None):
        """
        Creates a world-sized background.
        If tile_char is provided (e.g. '#'), tiles that character's image.
        Otherwise, tiles the theme's background image (dungeon_bg.png).
        """
        bg_surface = pg.Surface((width, height))
        
        # Tile using a specific character (e.g. '#')
        if tile_char and tile_char in self.tile_images:
            tile_img = self.tile_images[tile_char]
            img_w = tile_img.get_width()
            img_h = tile_img.get_height()
            
            for x in range(0, width, img_w):
                for y in range(0, height, img_h):
                    bg_surface.blit(tile_img, (x, y))
            return bg_surface

        # Tile using theme background image
        bg_path = BACKGROUNDS.get(self.theme)
        
        if not bg_path or not os.path.exists(bg_path):
            bg_surface.fill((20, 20, 30))
            return bg_surface
            
        try:
            bg_image = pg.image.load(bg_path).convert()
            target_scale = (1280, 720) 
            bg_image = pg.transform.scale(bg_image, target_scale)
            
            # Tiling Loop
            for x in range(0, width, target_scale[0]):
                for y in range(0, height, target_scale[1]):
                    bg_surface.blit(bg_image, (x, y))
                    
            return bg_surface
        except Exception as e:
            print(f"[ERROR] Failed to create world background: {e}")
            bg_surface.fill((20, 20, 30))
            return bg_surface



    def create_level(self):
        physics_rects = []
        visual_tiles = []
        spawn_point = (100, 100) # Default spawn
        finish_rect = None       # Area transisi level

        for row_index, row in enumerate(self.level_map):
            for col_index, char in enumerate(row):
                x = col_index * SCALED_TILE_SIZE
                y = row_index * SCALED_TILE_SIZE
                
                if char == 'P':
                    spawn_point = (x, y)
                    
                elif char == 'F':
                    # Area Finish / Transition
                    finish_rect = pg.Rect(x, y, SCALED_TILE_SIZE, SCALED_TILE_SIZE)
                
                elif char in self.tile_images:
                    # Visual
                    img = self.tile_images[char]
                    rect = pg.Rect(x, y, SCALED_TILE_SIZE, SCALED_TILE_SIZE)
                    visual_tiles.append((img, rect))
                    
                    # Physics
                    if char in ['X', '#', '=', '_', '|']:
                        physics_rects.append(rect)
        
        return physics_rects, visual_tiles, spawn_point, finish_rect