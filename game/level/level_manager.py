import pygame as pg
import os
from game.settings import TILE_SIZE, SCALE, SCALED_TILE_SIZE, BACKGROUNDS
import game.level.level1 as level1

THEMES = {
    'dungeon': 'assets/graphics/tilesets/dungeon.png',
    'grass':   'assets/graphics/tilesets/grass.png',
    'ice':     'assets/graphics/tilesets/ice.png',
    'snow':    'assets/graphics/tilesets/snow.png',
}

class LevelManager:
    def __init__(self, current_theme='dungeon'):
        self.tile_images = {}
        self.theme = current_theme
        
        # Mapping Karakter -> Koordinat Tileset (Col, Row)
        self.tile_map_coords = {
            'X': (1, 0), # Dinding Atas
            '#': (1, 1), # Dinding Tengah/Tiang
            '_': (1, 4), # Lantai
            '=': (3, 1), # Platform
        }
        
        self.load_assets()
        
        # Load Level 1 Data
        self.level_map = level1.level_data

    def load_assets(self):
        path = THEMES.get(self.theme)
        if not path or not os.path.exists(path):
            print(f"[ERROR] Tileset not found: {path}")
            return

        try:
            tileset = pg.image.load(path).convert_alpha()
            
            for char, (col, row) in self.tile_map_coords.items():
                # Ambil potongan 16x16
                rect_source = (col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                
                # Cek bounds
                if rect_source[0] + TILE_SIZE > tileset.get_width() or \
                   rect_source[1] + TILE_SIZE > tileset.get_height():
                    print(f"[WARNING] Tile coord ({col},{row}) out of bounds for {self.theme}")
                    continue
                    
                image = tileset.subsurface(rect_source)
                
                # Perbesar gambar (16x16 -> 48x48)
                image = pg.transform.scale(image, (SCALED_TILE_SIZE, SCALED_TILE_SIZE))
                
                self.tile_images[char] = image
            
            print(f"[INFO] Loaded {len(self.tile_images)} tiles for theme: {self.theme}")
            
        except Exception as e:
            print(f"[ERROR] Failed to load tileset: {e}")

    def create_world_background(self, width, height):
        """Creates a world-sized background by tiling the theme's bg image"""
        bg_surface = pg.Surface((width, height))
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

        for row_index, row in enumerate(self.level_map):
            for col_index, char in enumerate(row):
                x = col_index * SCALED_TILE_SIZE
                y = row_index * SCALED_TILE_SIZE
                
                if char == 'P':
                    spawn_point = (x, y)
                
                elif char in self.tile_images:
                    # Visual
                    img = self.tile_images[char]
                    rect = pg.Rect(x, y, SCALED_TILE_SIZE, SCALED_TILE_SIZE)
                    visual_tiles.append((img, rect))
                    
                    # Physics (Hanya dinding dan platform yang solid)
                    if char in ['X', '#', '=', '_']:
                        physics_rects.append(rect)
        
        return physics_rects, visual_tiles, spawn_point