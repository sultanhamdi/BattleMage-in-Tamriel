import pygame as pg
import os

class EnemyAnimationHandler:
    """
    Handler Animasi untuk Enemy.
    
    PERBEDAAN dengan PlayerAnimationHandler:
    - Player: Sprite Sheet Vertikal (1 file .png = semua frame vertikal)
    - Enemy: Folder-based (1 folder = 1 animasi, file terpisah per frame)
    
    Contoh struktur folder enemy:
    assets/graphics/enemies/zombie/
    ├── idle/
    │   ├── idle_1.png
    │   ├── idle_2.png
    │   └── ...
    ├── attack/
    │   ├── hit_1.png
    │   └── ...
    └── walk/
        └── ...
    """
    
    def __init__(self, asset_path, scale=1):
        """
        Inisialisasi Handler Animasi Enemy.
        
        Args:
            asset_path: Path ke folder enemy (misal: 'assets/graphics/enemies/zombie/')
            scale: Faktor pembesaran sprite
        """
        self.animations = {}  # Dictionary: {'idle': [frame1, frame2, ...], 'attack': [...]}
        self.frame_index = 0
        self.animation_speed = 0.15
        self.current_animation = 'idle'
        self.path = asset_path
        self.scale = scale
        
        # Flag untuk memberi tahu Enemy bahwa animasi selesai
        # Berguna untuk animasi yang tidak loop (attack, die, appear)
        self.animation_finished = False
        
    def load_sprites(self, animation_mapping):
        """
        Memuat semua sprite dari folder-folder animasi.
        
        Args:
            animation_mapping: Dictionary yang memetakan nama state ke nama folder
                               Contoh: {'idle': 'idle', 'walk': 'walk', 'attack': 'attack'}
                               Atau: {'idle': 'idle-walk', 'walk': 'idle-walk'} (jika share folder)
        
        Kenapa pakai mapping?
        - Nama folder asset bisa berbeda-beda (idle-walk, walk-idle, dll)
        - Kita standarkan jadi nama state yang konsisten (idle, walk, attack, dll)
        """
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
        """
        Menjalankan animasi dan mengembalikan frame saat ini.
        
        Args:
            state: Nama state animasi ('idle', 'walk', 'attack', dll)
            speed: Kecepatan animasi (opsional, override default)
            facing_right: Arah hadap karakter
            
        Returns:
            Surface frame saat ini, atau None jika tidak ada frame
        """
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
            
            # Animasi ATTACK: Tandai selesai, reset ke 0
            elif 'attack' in state or 'hit' in state:
                self.animation_finished = True
                self.frame_index = 0
            
            # Animasi LOOP biasa (idle, walk)
            else:
                self.frame_index = 0
        
        # Ambil frame dengan index yang aman
        safe_index = int(self.frame_index)
        if safe_index >= len(frames):
            safe_index = len(frames) - 1
            
        image = frames[safe_index]
        
        # Flip jika menghadap kiri
        if not facing_right:
            image = pg.transform.flip(image, True, False)
        
        return image
    
    def reset_animation(self):
        """
        Reset animasi ke frame 0.
        Berguna saat memulai animasi baru (misal: mulai attack).
        """
        self.frame_index = 0
        self.animation_finished = False
    
    def get_current_frame_index(self):
        """Mengembalikan index frame saat ini (untuk debugging)."""
        return int(self.frame_index)
    
    def is_animation_finished(self):
        """Cek apakah animasi sudah selesai (untuk animasi non-loop)."""
        return self.animation_finished

