import pygame as pg
import os

# Path Aset (Sesuaikan jika berbeda)
PLAYER_ASSET_PATH = 'assets/graphics/player/'

class PlayerAnimationHandler:
    def __init__(self, asset_path, frame_width, frame_height, scale=1):
        self.animations = {} 
        self.frame_index = 0
        self.animation_speed = 0.15
        self.current_animation = 'idle'
        self.path = asset_path
        self.width = frame_width
        self.height = frame_height
        self.scale = scale
        
        # Flag untuk memberi tahu Player.py bahwa animasi selesai
        self.animation_finished = False
        
    def load_sprites(self, animation_types):
        """Memuat sprite sheet strip (VERTIKAL)"""
        try:
            for anim in animation_types:
                full_path = f"{self.path}/{anim}.png"
                if not os.path.exists(full_path):
                    print(f"[WARNING] File tidak ada: {anim}.png")
                    self.animations[anim] = [] 
                    continue

                sheet = pg.image.load(full_path).convert_alpha()
                self.animations[anim] = []
                
                sheet_w = sheet.get_width()
                sheet_h = sheet.get_height()

                if sheet_w < self.width:
                    continue 

                num_frames = int(sheet_h / self.height)

                for i in range(num_frames):
                    image = sheet.subsurface((0, i * self.height, self.width, self.height))
                    if self.scale != 1:
                        image = pg.transform.scale(image, (int(self.width * self.scale), int(self.height * self.scale)))
                    self.animations[anim].append(image)
            
            print("[INFO] Aset Player dimuat.")
        except Exception as e:
            print(f"[CRITICAL ERROR] {e}")

    def animate(self, state, dt, facing_right):
        # Reset index jika ganti state animasi
        if state != self.current_animation:
            self.current_animation = state
            self.frame_index = 0
            self.animation_finished = False

        # Jalankan timer animasi
        self.frame_index += self.animation_speed
        frames = self.animations.get(state, [])

        if not frames:
            return None 

        # --- [PERBAIKAN LOGIKA LOOPING] ---
        if self.frame_index >= len(frames):
            if state == 'death':
                # KHUSUS DEATH: Jangan reset ke 0! Tahan di frame terakhir.
                self.animation_finished = True
                self.frame_index = len(frames) - 1 
            
            elif 'attack' in state:
                # KHUSUS ATTACK: Tandai selesai, reset ke 0 (siap untuk combo berikutnya)
                self.animation_finished = True
                self.frame_index = 0
                
            else:
                # IDLE/RUN/JUMP: Looping biasa
                self.frame_index = 0
                
        # Ambil gambar berdasarkan index yang aman
        safe_index = int(self.frame_index)
        # Double check agar index tidak crash (misal float rounding error)
        if safe_index >= len(frames): 
            safe_index = len(frames) - 1
            
        image = frames[safe_index]
        
        if not facing_right:
            image = pg.transform.flip(image, True, False)  
            
        return image