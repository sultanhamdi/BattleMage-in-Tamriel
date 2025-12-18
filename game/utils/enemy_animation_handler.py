import pygame as pg
import os

class EnemyAnimationHandler:
    # animation handler for enemy - folder-based sprites
    
    def __init__(self, asset_path, scale=1):
        self.animations = {}  # Dictionary: {'idle': [frame1, frame2, ...], 'attack': [...]}
        self.frame_index = 0
        self.animation_speed = 0.15
        self.current_animation = 'idle'
        self.path = asset_path
        self.scale = scale
        self.current_frame = 0  # Integer frame index for state checking
        
        # animation finished flag
        self.animation_finished = False
        
    def load_sprites(self, animation_mapping):
        # load all sprites from animation folders
        try:
            for state_name, folder_name in animation_mapping.items():
                folder_path = os.path.join(self.path, folder_name)
                
                # Cek apakah folder ada
                if not os.path.exists(folder_path):
                    print(f"[WARNING] Folder tidak ada: {folder_path}")
                    self.animations[state_name] = []
                    continue
                
                # Load semua file gambar di folder (sorted biar urut)
                frames = []
                files = sorted(os.listdir(folder_path))
                
                for filename in files:
                    # Hanya load file gambar
                    if filename.endswith(('.png', '.jpg', '.jpeg')):
                        file_path = os.path.join(folder_path, filename)
                        image = pg.image.load(file_path).convert_alpha()
                        
                        # Scale jika diperlukan
                        if self.scale != 1:
                            new_width = int(image.get_width() * self.scale)
                            new_height = int(image.get_height() * self.scale)
                            image = pg.transform.scale(image, (new_width, new_height))
                        
                        frames.append(image)
                
                self.animations[state_name] = frames
                
            print(f"[INFO] Aset Enemy dimuat dari: {self.path}")
            
        except Exception as e:
            print(f"[CRITICAL ERROR] Gagal load aset enemy: {e}")
    
    def animate(self, state, speed=None, facing_right=True):
        # run animation and return current frame
        # Override speed jika diberikan
        anim_speed = speed if speed is not None else self.animation_speed
        
        # Reset index jika ganti state animasi
        if state != self.current_animation:
            self.current_animation = state
            self.frame_index = 0
            self.animation_finished = False
        
        # Ambil list frame untuk state ini
        frames = self.animations.get(state, [])
        
        if not frames:
            return None
        
        # Jalankan timer animasi
        self.frame_index += anim_speed
        
        # --- LOGIKA LOOPING / NON-LOOPING ---
        if self.frame_index >= len(frames):
            # Animasi yang TIDAK loop (tahan di frame terakhir)
            if state in ['die', 'death', 'appear', 'disappear']:
                self.animation_finished = True
                self.frame_index = len(frames) - 1
            
            # Animasi ATTACK & HURT: Tandai selesai, reset ke 0
            elif 'attack' in state or 'hit' in state or 'hurt' in state or 'cast' in state or 'spell' in state or state in ['take_hit', 'damaged']:
                self.animation_finished = True
                self.frame_index = 0
            
            # Animasi LOOP biasa (idle, walk, run, chase)
            else:
                self.frame_index = 0
        
        # Ambil frame dengan index yang aman
        safe_index = int(self.frame_index)
        if safe_index >= len(frames):
            safe_index = len(frames) - 1
        
        # Update current_frame property
        self.current_frame = safe_index
            
        image = frames[safe_index]
        
        # Sprite default menghadap KANAN, flip jika menghadap KIRI
        if not facing_right:
            image = pg.transform.flip(image, True, False)
        
        return image
    
    def reset_animation(self):
        # reset animation to frame 0
        self.frame_index = 0
        self.animation_finished = False
    
    def get_current_frame_index(self):
        # get current frame index
        return int(self.frame_index)
    
    def is_animation_finished(self):
        # check if animation finished
        return self.animation_finished

