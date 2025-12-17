import pygame as pg
import os

class AudioManager:
    def __init__(self):
        # Inisialisasi Mixer jika belum
        if not pg.mixer.get_init():
            pg.mixer.init()
            
        # Path Music (Relative to main.py execution)
        self.music_paths = {
            "dungeon": "assets/audio/music/dungeon.wav",
            "snow": "assets/audio/music/snow.wav",
            "grass": "assets/audio/music/grass.wav"
        }
        
        self.current_theme = None
        self.music_volume = 0.5
        pg.mixer.music.set_volume(self.music_volume)

    def play_theme_music(self, theme):
        """Memainkan musik berdasarkan tema level"""
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
                self.current_theme = target_key
                print(f"[AUDIO] Now Playing: {target_key}")
            except Exception as e:
                print(f"[WARN] Failed to play music '{path}': {e}")
        else:
            print(f"[WARN] Music file not found: {path} (Base Theme: {theme})")

    def stop_music(self):
        pg.mixer.music.stop()
        self.current_theme = None
