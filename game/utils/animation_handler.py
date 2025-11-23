import pygame as pg
import os

class AnimationHandler:
    def __init__(self, asset_path, frame_width, frame_height, scale=1):
        self.animations = {} 
        self.frame_index = 0
        self.animation_speed = 0.15
        self.current_animation = 'idle'
        self.path = asset_path
        self.width = frame_width
        self.height = frame_height
        self.scale = scale
        
    def load_sprites(self, animation_types):
        """Memuat sprite sheet strip (VERTIKAL) dengan Pengecekan Error"""
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

                # [FITUR SAFETY] Cek apakah gambar lebih kecil dari settingan kode
                if sheet_w < self.width:
                    print(f"[ERROR SIZE] Gambar '{anim}.png' (Lebar: {sheet_w}px) lebih kecil dari setting Player ({self.width}px).")
                    print("-> SOLUSI: Ubah 'self.original_size' di player.py menjadi 32.")
                    continue # Skip file ini agar game tidak crash

                # Hitung jumlah frame vertikal
                num_frames = int(sheet_h / self.height)

                for i in range(num_frames):
                    # Potong frame
                    image = sheet.subsurface((0, i * self.height, self.width, self.height))
                    
                    # Resize
                    if self.scale != 1:
                        image = pg.transform.scale(image, (int(self.width * self.scale), int(self.height * self.scale)))
                    self.animations[anim].append(image)
            
            print("[INFO] Aset dimuat.")
        except Exception as e:
            print(f"[CRITICAL ERROR] {e}")

    def animate(self, state, dt, facing_right):
        if state != self.current_animation:
            self.current_animation = state
            self.frame_index = 0

        self.frame_index += self.animation_speed
        frames = self.animations.get(state, [])

        if not frames:
            return None 

        if self.frame_index >= len(frames):
            self.frame_index = 0

        image = frames[int(self.frame_index)]
        if not facing_right:
            image = pg.transform.flip(image, True, False)  
        return image