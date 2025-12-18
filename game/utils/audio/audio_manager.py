import pygame as pg
import os

class AudioManager:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AudioManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, '_initialized', False):
            return
            
        self._initialized = True
        
        # init mixer
        if not pg.mixer.get_init():
            pg.mixer.init()
            
        # music paths
        self.music_paths = {
            "dungeon": "assets/audio/music/dungeon.wav",
            "snow": "assets/audio/music/snow.wav",
            "grass": "assets/audio/music/grass.wav"
        }
        
        # Load SFX
        self.sfx = {}
        self.sfx_volume = 0.6
        sfx_files = {
            "attack1": "assets/audio/sfx/attack1.wav",
            "attack2": "assets/audio/sfx/attack2.wav",
            "attack3": "assets/audio/sfx/attack3.wav",
            "jump": "assets/audio/sfx/jump.wav",
            "land": "assets/audio/sfx/land.wav",
            "spin_attack": "assets/audio/sfx/spin_attack.wav",
            "sustain_arcane": "assets/audio/sfx/sustain_arcane.WAV",
            # Footsteps
            "dungeon_run": "assets/audio/sfx/dungeon_run.wav",
            "snow_run": "assets/audio/sfx/snow_run.wav",
            "grass_run": "assets/audio/sfx/grass_run.wav"
        }
        
        for name, path in sfx_files.items():
            if os.path.exists(path):
                try:
                    self.sfx[name] = pg.mixer.Sound(path)
                    self.sfx[name].set_volume(self.sfx_volume)
                    print(f"[AUDIO] Loaded SFX: {name}")
                except Exception as e:
                    print(f"[WARN] Failed to load SFX {name}: {e}")

        self.current_theme = None
        self.music_volume = 0.5
        self.music_enabled = True
        self.sfx_enabled = True
        pg.mixer.music.set_volume(self.music_volume)

    def toggle_music(self):
        self.music_enabled = not self.music_enabled
        if self.music_enabled:
            pg.mixer.music.set_volume(self.music_volume)
            if self.current_theme:
                pg.mixer.music.unpause()
            else:
                # Restart theme if stopped and we know what theme
                pass
        else:
            pg.mixer.music.set_volume(0)
            pg.mixer.music.pause()
        return self.music_enabled

    def toggle_sfx(self):
        self.sfx_enabled = not self.sfx_enabled
        # update all loaded sfx volume
        vol = self.sfx_volume if self.sfx_enabled else 0
        for sfx in self.sfx.values():
            sfx.set_volume(vol)
        return self.sfx_enabled

    def play_sfx(self, name):
        # play sound effect
        if self.sfx_enabled and name in self.sfx:
            self.sfx[name].play()

    def play_footstep(self):
        # play footstep based on theme
        # Tentukan SFX berdasarkan current_theme
        theme = self.current_theme if self.current_theme else "dungeon"
        
        # Mapping theme ke SFX key
        sfx_key = f"{theme}_run"
        
        # Check jika SFX ada, kalau tidak fallback ke dungeon
        if sfx_key not in self.sfx:
            sfx_key = "dungeon_run"
            
        if self.sfx_enabled and sfx_key in self.sfx:
            # Randomize pitch sedikit jika mau, tapi pygame mixer simple
            self.sfx[sfx_key].play()

    def play_theme_music(self, theme):
        # play music based on level theme
        # Mapping tema yang mungkin beda nama di Tiled (misal 'dungeon_bg' -> 'dungeon')
        theme_key = theme.lower()
        
        # Simplifikasi key matching
        if "dungeon" in theme_key:
            target_key = "dungeon"
        elif "snow" in theme_key or "ice" in theme_key:
            target_key = "snow"
        elif "grass" in theme_key or "forest" in theme_key:
            target_key = "grass"
        else:
            print(f"[AUDIO] Theme '{theme}' not recognized for music. Defaulting to Dungeon.")
            target_key = "dungeon"

        # Jangan restart jika lagu yang sama sudah main
        if self.current_theme == target_key and pg.mixer.music.get_busy():
            return

        path = self.music_paths.get(target_key)
        if path and os.path.exists(path):
            try:
                pg.mixer.music.load(path)
                pg.mixer.music.play(loops=-1, fade_ms=1000) # Loop selamanya, fade in 1 detik
                # set volume based on enabled state
                effective_vol = self.music_volume if self.music_enabled else 0
                pg.mixer.music.set_volume(effective_vol)
                
                self.current_theme = target_key
                print(f"[AUDIO] Now Playing: {target_key}")
            except Exception as e:
                print(f"[WARN] Failed to play music '{path}': {e}")
        else:
            print(f"[WARN] Music file not found: {path} (Base Theme: {theme})")

    def stop_music(self):
        pg.mixer.music.stop()
        self.current_theme = None
