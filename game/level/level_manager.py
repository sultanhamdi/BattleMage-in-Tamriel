import pygame as pg

TILE_SIZE = 48  # Ukuran tile di layar (16px * 3 Scale)
TILE_SCALE = 3  # Skala pembesaran
THEMES = {
    'dungeon': 'assets/graphics/tilesets/dungeon.png',
    'grass':   'assets/graphics/tilesets/grass.png',
    'ice':     'assets/graphics/tilesets/ice.png',
    'snow':    'assets/graphics/tilesets/snow.png',
    # Tambahkan lainnya di sini
}

class LevelManager:
    # [UBAH] Tambahkan parameter 'current_theme'
    def __init__(self, current_theme='dungeon'):
        self.tile_images = {}
        self.theme = current_theme # Simpan tema yang dipilih
        self.load_assets()
        
        # Peta Level (Bisa diganti-ganti nanti)
        self.level_map = [
            "                            ",
            "                            ",
            "                            ",
            "                            ",
            "           XXXXXX           ",
            "                            ",
            "      XXX        XXX        ",
            "                            ",
            " XXX                  XXX   ",
            "XXXXXXXXXXXXXXXXXXXXXXXXXXX",
            "XXXXXXXXXXXXXXXXXXXXXXXXXXX",
        ]

    def load_assets(self):
        """Memuat tileset berdasarkan TEMA yang dipilih"""
        # Ambil path dari dictionary THEMES di settings.py
        path = THEMES.get(self.theme)
        
        if not path:
            print(f"[ERROR] Tema '{self.theme}' tidak ditemukan di settings.py!")
            return

        try:
            # Load gambar sesuai tema
            tileset = pg.image.load(path).convert_alpha()
            
            # --- LOGIKA PEMOTONGAN (SLICING) ---
            # Kita asumsikan semua tileset punya layout yang mirip (standar 0x72)
            # Ambil kotak tengah (biasanya x=16, y=16 aman untuk semua tileset ini)
            rect_source = (16, 16, 16, 16) 
            image = tileset.subsurface(rect_source)
            
            # Perbesar gambar
            image = pg.transform.scale(image, (TILE_SIZE, TILE_SIZE))
            
            self.tile_images['X'] = image
            print(f"[INFO] Sukses memuat tema: {self.theme}")
            
        except Exception as e:
            print(f"[ERROR] Gagal load tileset {path}: {e}")
            fallback = pg.Surface((TILE_SIZE, TILE_SIZE))
            fallback.fill((150, 50, 50))
            self.tile_images['X'] = fallback

    def create_level(self):
        physics_rects = []
        visual_tiles = []

        for row_index, row in enumerate(self.level_map):
            for col_index, char in enumerate(row):
                x = col_index * TILE_SIZE
                y = row_index * TILE_SIZE
                
                if char == 'X':
                    rect = pg.Rect(x, y, TILE_SIZE, TILE_SIZE)
                    physics_rects.append(rect)
                    
                    img = self.tile_images.get('X')
                    if img:
                        visual_tiles.append((img, rect))
        
        return physics_rects, visual_tiles