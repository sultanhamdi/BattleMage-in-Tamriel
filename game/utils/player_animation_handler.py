import pygame as pg
import os

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
        self.animation_finished = False
        
    def load_sprites(self, animation_types):
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

    def load_custom_animation(self, name, custom_width, custom_height):
        # load animation with custom frame size
        full_path = f"{self.path}/{name}.png"
        if not os.path.exists(full_path):
            print(f"[WARNING] File tidak ada: {name}.png")
            self.animations[name] = [] 
            return

        try:
            sheet = pg.image.load(full_path).convert_alpha()
            self.animations[name] = []
            
            sheet_w = sheet.get_width()
            sheet_h = sheet.get_height()

            # Hitung jumlah frame berdasarkan tinggi custom
            num_frames = int(sheet_h / custom_height)

            for i in range(num_frames):
                # Potong sesuai ukuran custom
                image = sheet.subsurface((0, i * custom_height, custom_width, custom_height))
                
                # Scale sesuai global scale
                if self.scale != 1:
                    image = pg.transform.scale(image, (int(custom_width * self.scale), int(custom_height * self.scale)))
                self.animations[name].append(image)
            print(f"[INFO] Custom Animation '{name}' dimuat ({custom_width}x{custom_height}).")
            
        except Exception as e:
            print(f"[ERROR] Gagal load custom animation {name}: {e}")

    def animate(self, state, dt, facing_right):
        if state != self.current_animation:
            self.current_animation = state
            self.frame_index = 0
            self.animation_finished = False

        # Jalankan timer animasi
        self.frame_index += self.animation_speed
        frames = self.animations.get(state, [])

        if not frames:
            return None 
        if self.frame_index >= len(frames):
            
            # Animasi Sekali Putar (Freeze di frame terakhir)
            if state in ['death', 'crouch', 'crouch_attack', 'dash', 'spin_attack', 'sustain_arcane']:
                self.animation_finished = True
                self.frame_index = len(frames) - 1 
            
            # Animasi Sekali Putar (Reset ke 0 untuk Combo)
            elif 'attack' in state:
                self.animation_finished = True
                self.frame_index = 0
                
            # Looping Terus (Idle, Run, Jump, Fall)
            else:
                self.frame_index = 0
            
        safe_index = int(self.frame_index)
        # Clamp index agar tidak out of bounds
        if safe_index >= len(frames): 
            safe_index = len(frames) - 1
            
        # Ambil gambar
        image = frames[safe_index]

        if not facing_right:
            image = pg.transform.flip(image, True, False)  
        
        return image