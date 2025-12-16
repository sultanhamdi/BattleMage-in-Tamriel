import pygame as pg
import os
import xml.etree.ElementTree as ET
from game.settings import TILE_SIZE, SCALE, SCALED_TILE_SIZE, BACKGROUNDS, WINDOW_WIDTH, WINDOW_HEIGHT
import game.level.level1 as level1
import game.level.level2 as level2
import game.level.level3 as level3
import game.level.level4 as level4
import game.level.level5 as level5
import game.level.level6 as level6

THEMES = {
    'dungeon': 'assets/graphics/tilesets/dungeon.png',
    'snow': 'assets/graphics/tilesets/snow.png',
    'grass': 'assets/graphics/tilesets/grass.png',
}

class LevelManager:
    def __init__(self, current_theme='dungeon'):
        self.tile_images = {}
        self.theme = current_theme
        self.tileset_img = None
        
        self.load_assets()
        
        # Level Management
        self.levels = [level1.level_data, level2.level_data, level3.level_data, level4.level_data, level5.level_data, level6.level_data]
        self.current_level_index = 0
        self.level_map = self.levels[self.current_level_index]

    def set_level(self, index):
        if 0 <= index < len(self.levels):
            self.current_level_index = index
            self.level_map = self.levels[index]
            
            # Dynamic Theme Switching
            # Level 1-3 (Index 0-2) -> Dungeon
            # Level 4-5 (Index 3-4) -> Snow
            # Level 6+ (Index 5+) -> Grass
            target_theme = 'dungeon'
            if index >= 5:
                target_theme = 'grass'
            elif index >= 3:
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
            self.tileset_img = tileset
            print(f"[INFO] Loaded tileset for theme: {self.theme}")
            
        except Exception as e:
            print(f"[ERROR] Failed to load tileset: {e}")

    def create_world_background(self, width, height, tile_char=None):
        """
        Creates a world-sized background.
        Tiles the theme's background image.
        """
        bg_surface = pg.Surface((width, height))

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
            
            physics_rects = []
            visual_tiles = []
            spawn_point = (100, 100)
            finish_rect = None
            background_images = []  # List of (image, offset_x, offset_y)
            
            # Get TMX directory for relative paths (using absolute path)
            tmx_abs_path = os.path.abspath(filepath)
            tmx_dir = os.path.dirname(tmx_abs_path)
            
            # Parse Image Layers (Background)
            for imagelayer in root.findall("imagelayer"):
                img_elem = imagelayer.find("image")
                if img_elem is not None:
                    source = img_elem.get("source")
                    # Resolve relative path from TMX location
                    img_path = os.path.normpath(os.path.join(tmx_dir, source))
                    
                    offset_x = float(imagelayer.get("offsetx", 0)) * SCALE
                    offset_y = float(imagelayer.get("offsety", 0)) * SCALE
                    
                    # Check if tiling is enabled
                    repeat_x = imagelayer.get("repeatx") == "1"
                    repeat_y = imagelayer.get("repeaty") == "1"
                    
                    if os.path.exists(img_path):
                        try:
                            bg_img = pg.image.load(img_path).convert()
                            # Scale to match game scale
                            new_w = int(bg_img.get_width() * SCALE)
                            new_h = int(bg_img.get_height() * SCALE)
                            bg_img = pg.transform.scale(bg_img, (new_w, new_h))
                            background_images.append((bg_img, offset_x, offset_y, repeat_x, repeat_y))
                            print(f"[INFO] Loaded image layer: {source} (repeat: x={repeat_x}, y={repeat_y})")
                        except Exception as e:
                            print(f"[WARNING] Failed to load image layer {source}: {e}")
                    else:
                        print(f"[WARNING] Image layer not found: {img_path}")
            
            # Check tileset is loaded
            if not self.tileset_img:
                print("[ERROR] Tileset image not loaded for TMX!")
                return physics_rects, visual_tiles, spawn_point, finish_rect, background_images
            
            # Iterate through ALL layers
            for layer in root.findall("layer"):
                layer_name = layer.get("name")
                data = layer.find("data").text.strip()
                
                width_layer = int(layer.get("width"))
                
                gid_list = [int(gid) for gid in data.replace("\n", "").split(",")]
                
                cols_in_tileset = self.tileset_img.get_width() // TILE_SIZE
                rows_in_tileset = self.tileset_img.get_height() // TILE_SIZE
                total_tiles = cols_in_tileset * rows_in_tileset

                for index, gid in enumerate(gid_list):
                    if gid == 0: continue # Empty tile
                    
                    # Calculate Grid Position
                    x = (index % width_layer) * SCALED_TILE_SIZE
                    y = (index // width_layer) * SCALED_TILE_SIZE
                    
                    # Tiled GIDs are 1-based, Python 0-based
                    # Handle duplicate tilesets by wrapping GID
                    real_gid = (gid - 1) % total_tiles
                    
                    # Calculate Source Rect
                    src_x = (real_gid % cols_in_tileset) * TILE_SIZE
                    src_y = (real_gid // cols_in_tileset) * TILE_SIZE
                    
                    # Extract Tile Image
                    tile_src_rect = (src_x, src_y, TILE_SIZE, TILE_SIZE)
                    
                    # Boundary Check for tileset image
                    if src_x + TILE_SIZE <= self.tileset_img.get_width() and \
                       src_y + TILE_SIZE <= self.tileset_img.get_height():
                        
                        img = self.tileset_img.subsurface(tile_src_rect)
                        img = pg.transform.scale(img, (SCALED_TILE_SIZE, SCALED_TILE_SIZE))
                        
                        dst_rect = pg.Rect(x, y, SCALED_TILE_SIZE, SCALED_TILE_SIZE)
                        visual_tiles.append((img, dst_rect))
                        
                        # Collision Logic: Only "Solid" layer has physics
                        if layer_name == "Solid":
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

            return physics_rects, visual_tiles, spawn_point, finish_rect, background_images
            
        except Exception as e:
            print(f"[ERROR] Failed to load TMX: {e}")
            if 'physics_rects' in locals():
                return physics_rects, visual_tiles, spawn_point, finish_rect, background_images
            return [], [], (0,0), None, []

    def create_level(self):
        """Load current level from TMX file"""
        return self.load_tmx(self.level_map)