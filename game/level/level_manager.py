import pygame as pg
from game.settings import TILE_SIZE, TILE_SCALE, TILESET_PATH

class LevelManager:
    def __init__(self):
        self.tile_images = {}
        self.load_assets()
        
        # Ini adalah Peta Level kita!
        # X = Lantai/Dinding
        # P = Posisi Awal Player (Nanti kita implementasikan spawn point)
        # Spasi = Kosong/Udara
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
            " XXXXXXXXXXXXXXXXXXXXXXXX   ", # Lantai Dasar
            " XXXXXXXXXXXXXXXXXXXXXXXX   ",
        ]

    def load_assets(self):
        """Memuat dan memotong tileset"""
        try:
            # Load gambar utuh
            tileset = pg.image.load(TILESET_PATH).convert_alpha()
            
            # --- POTONG GAMBAR (SLICING) ---
            # Tileset 0x72 biasanya ukurannya 16x16 per kotak.
            # Mari kita ambil gambar "Bata Gelap" yang umum.
            # Koordinat biasanya: x=16, y=16 (Baris ke-2, Kolom ke-2 biasanya bata tengah)
            # Anda bisa bereksperimen mengganti rect ini (x, y, 16, 16) untuk ganti gambar
            
            # Ambil potongan 16x16
            rect_source = (16, 16, 16, 16) 
            image = tileset.subsurface(rect_source)
            
            # Perbesar gambar (Scale)
            image = pg.transform.scale(image, (TILE_SIZE, TILE_SIZE))
            
            # Simpan dengan kunci 'X'
            self.tile_images['X'] = image
            
            print("[INFO] Tileset loaded.")
        except Exception as e:
            print(f"[ERROR] Gagal load tileset: {e}")
            # Fallback: Bikin kotak merah kalau gambar gagal load
            fallback = pg.Surface((TILE_SIZE, TILE_SIZE))
            fallback.fill((150, 50, 50))
            self.tile_images['X'] = fallback

    def create_level(self):
        """
        Menerjemahkan Array Teks menjadi Rect (Fisika) dan Gambar (Visual)
        """
        physics_rects = []
        visual_tiles = [] # List tuple: (image, (x, y))

        for row_index, row in enumerate(self.level_map):
            for col_index, char in enumerate(row):
                
                # Hitung posisi pixel di layar
                x = col_index * TILE_SIZE
                y = row_index * TILE_SIZE
                
                if char == 'X':
                    # 1. Buat Rect untuk Fisika
                    rect = pg.Rect(x, y, TILE_SIZE, TILE_SIZE)
                    physics_rects.append(rect)
                    
                    # 2. Simpan Gambar untuk Visual
                    img = self.tile_images.get('X')
                    if img:
                        visual_tiles.append((img, rect))
        
        return physics_rects, visual_tiles