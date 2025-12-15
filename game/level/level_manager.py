import pygame as pg
import os
import xml.etree.ElementTree as ET
from game.settings import TILE_SIZE, SCALE, SCALED_TILE_SIZE, BACKGROUNDS, WINDOW_WIDTH, WINDOW_HEIGHT
import game.level.level1 as level1
import game.level.level2 as level2
import game.level.level3 as level3
import game.level.level4 as level4

THEMES = {
    'dungeon': 'assets/graphics/tilesets/dungeon.png',
    'snow': 'assets/graphics/tilesets/snow.png',
}

class LevelManager:
    def __init__(self, current_theme='dungeon'):
        self.tile_images = {}
        self.theme = current_theme
        self.tileset_img = None # Store raw tileset for TMX
        
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
        self.levels = [level1.level_data, level2.level_data, level3.level_data, level4.level_data]
        self.current_level_index = 0
        self.level_map = self.levels[self.current_level_index]

    def set_level(self, index):
        if 0 <= index < len(self.levels):
            self.current_level_index = index
            self.level_map = self.levels[index]
            
            # Dynamic Theme Switching
            # Level 1-3 (Index 0-2) -> Dungeon
            # Level 4+ (Index 3+) -> Snow
            target_theme = 'dungeon'
            if index >= 3:
                target_theme = 'snow'
                
            if self.theme != target_theme:
                print(f"[INFO] Switching theme to: {target_theme}")
                self.theme = target_theme
                self.load_assets()
            
            return True
        return False

    def load_assets(self):
        path = THEMES.get(self.theme)
        if not path or not os.path.exists(path):
            print(f"[ERROR] Tileset not found: {path}")
            return

        try:
            tileset = pg.image.load(path).convert_alpha()
            self.tileset_img = tileset # Store for TMX usage
            
            # Old ASCII Map Loading Logic
            for char, (col, row) in self.tile_map_coords.items():
                # Ambil potongan 16x16
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
            # Fallback color (Dark Blue for Snow, Dark Grey for Dungeon)
            if self.theme == 'snow':
                bg_surface.fill((20, 30, 45))
            else:
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

    def load_tmx(self, filepath):
        """Loads a Tiled .tmx file (XML format)"""
        print(f"[INFO] Loading TMX: {filepath}")
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()
            layer = root.find("layer")
            data = layer.find("data").text.strip()
            
            width = int(layer.get("width"))
            height = int(layer.get("height"))
            
            gid_list = [int(gid) for gid in data.replace("\n", "").split(",")]
            
            physics_rects = []
            visual_tiles = []
            spawn_point = (100, 100)
            finish_rect = None
            
            # Use 'snow.png' logic (256px wide => 16 columns)
            # Assumption: We are using self.tileset_img which should be loaded
            if not self.tileset_img:
                print("[ERROR] Tileset image not loaded for TMX!")
                return physics_rects, visual_tiles, spawn_point, finish_rect
                
            cols_in_tileset = self.tileset_img.get_width() // TILE_SIZE
            
            for index, gid in enumerate(gid_list):
                if gid == 0: continue # Empty tile
                
                # Calculate Grid Position
                x = (index % width) * SCALED_TILE_SIZE
                y = (index // width) * SCALED_TILE_SIZE
                
                # Tiled GIDs are 1-based, Python 0-based
                real_gid = gid - 1
                
                # Calculate Source Rect
                src_x = (real_gid % cols_in_tileset) * TILE_SIZE
                src_y = (real_gid // cols_in_tileset) * TILE_SIZE
                
                # Extract Tile Image
                tile_src_rect = (src_x, src_y, TILE_SIZE, TILE_SIZE)
                if src_x + TILE_SIZE <= self.tileset_img.get_width() and \
                   src_y + TILE_SIZE <= self.tileset_img.get_height():
                    
                    img = self.tileset_img.subsurface(tile_src_rect)
                    img = pg.transform.scale(img, (SCALED_TILE_SIZE, SCALED_TILE_SIZE))
                    
                    dst_rect = pg.Rect(x, y, SCALED_TILE_SIZE, SCALED_TILE_SIZE)
                    visual_tiles.append((img, dst_rect))
                    
                    # Assume ALL visible tiles are solid for now
                    physics_rects.append(dst_rect)
            
            # Parse Objects (Spawn & Finish)
            object_group = root.find("objectgroup")
            if object_group:
                for obj in object_group.findall("object"):
                    name = obj.get("name")
                    x = float(obj.get("x"))
                    y = float(obj.get("y"))
                    
                    # Convert to Game World Coordinates (Scale)
                    world_x = x * SCALE
                    world_y = y * SCALE
                    
                    if name in ["P", "Spawn"]:
                        spawn_point = (world_x, world_y)
                        print(f"[INFO] TMX Spawn Point found: {spawn_point}")
                        
                    elif name in ["F", "Finish"]:
                        # If object has width/height, use it. Otherwise default to 1 tile.
                        w = float(obj.get("width", TILE_SIZE)) * SCALE
                        h = float(obj.get("height", TILE_SIZE)) * SCALE
                        finish_rect = pg.Rect(world_x, world_y, w, h)
                        print(f"[INFO] TMX Finish Point found: {finish_rect}")

            return physics_rects, visual_tiles, spawn_point, finish_rect
            
        except Exception as e:
            print(f"[ERROR] Failed to load TMX: {e}")
            # Return defaults on failure, but try to return whatever we loaded if possible
            if 'physics_rects' in locals():
                return physics_rects, visual_tiles, spawn_point, finish_rect
            return [], [], (0,0), None

    def create_level(self):
        # Check if current map is TMX (String) or ASCII (List)
        if isinstance(self.level_map, str) and self.level_map.endswith('.tmx'):
            return self.load_tmx(self.level_map)
            
        # Legacy ASCII Loader
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