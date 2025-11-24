# game/settings.py

# Layar
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_SIZE = (WINDOW_WIDTH, WINDOW_HEIGHT)
FPS = 60
TITLE = "Battlemage In Tamriel"

# Warna (RGB)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
BLUE = (0, 0, 255)
BG_COLOR = (20, 20, 30) 

# Fisika 
GRAVITY = 0.8
# [PERBAIKAN] Naikkan dari -16 ke -22 agar bisa naik ke platform setinggi 180-200px
JUMP_STRENGTH = -22 
TERMINAL_VELOCITY = 15

# Player Stats
PLAYER_SPEED = 5

# Path Aset
PLAYER_ASSET_PATH = 'assets/graphics/player/'

TILE_SIZE = 48  # Ukuran tile di layar (16px * 3 Scale)
TILE_SCALE = 3  # Skala pembesaran
TILESET_PATH = 'assets/graphics/tilesets/dungeon.png'