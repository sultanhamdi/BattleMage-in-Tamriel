import pygame as pg
from game.components.physics import PhysicsComponent

class Entity(pg.sprite.Sprite):
    """
    Parent Class (Blueprint) untuk semua makhluk hidup (Player & Enemy).
    Hanya menangani Logika, Fisika, dan Data. Tidak menangani Gambar/Input.
    """
    def __init__(self, x, y, width, height, max_hp, attack_power, speed):
        super().__init__()
        
        # --- 1. KOMPONEN FISIKA & POSISI ---
        self.rect = pg.Rect(x, y, width, height)
        self.physics = PhysicsComponent(self.rect)
        
        # --- 2. STATS (Diterima dari Child) ---
        self.max_hp = max_hp
        self.current_hp = max_hp
        self.attack_power = attack_power
        self.movement_speed = speed 
        self.alive = True
        
        # --- 3. STATE ANIMASI (String) ---
        # Child class mengubah string ini, AnimationHandler membacanya.
        self.state = 'idle' 
        self.facing_right = True 
        
        # --- 4. SISTEM COMBAT (Cooldown & I-Frames) ---
        self.is_attacking = False
        self.attack_cooldown = 500 # ms (Jeda antar serangan)
        self.last_attack_time = 0
        
        self.is_invincible = False
        self.invincibility_duration = 1000 # ms (Kebal sesaat setelah kena hit)
        self.last_hit_time = 0

    def update_timers(self):
        """Mengurus perhitungan waktu cooldown dan efek status"""
        current_time = pg.time.get_ticks()
        
        # Reset Status Kebal (Invincible)
        if self.is_invincible:
            if current_time - self.last_hit_time > self.invincibility_duration:
                self.is_invincible = False

        # Reset Status Serang (Attack)
        if self.is_attacking:
            # Asumsi durasi animasi attack rata-rata 400ms
            # Jika sudah lewat, kembalikan ke idle agar bisa gerak lagi
            if current_time - self.last_attack_time > 400: 
                self.is_attacking = False
                if self.alive:
                    self.state = 'idle'

    def take_damage(self, amount):
        """Logika umum menerima damage"""
        if not self.alive or self.is_invincible:
            return

        self.current_hp -= amount
        self.is_invincible = True
        self.last_hit_time = pg.time.get_ticks()
        self.state = 'hurt' 
        
        print(f"[COMBAT] {type(self).__name__} took {amount} dmg. HP: {self.current_hp}/{self.max_hp}")

        if self.current_hp <= 0:
            self.die()

    def attack(self):
        """Mencoba menyerang (hanya set state, logika hitbox nanti di Child/GameScreen)"""
        current_time = pg.time.get_ticks()
        
        # Hanya bisa serang jika hidup dan cooldown selesai
        if not self.is_attacking and self.alive:
            if current_time - self.last_attack_time > self.attack_cooldown:
                self.is_attacking = True
                self.state = 'attack1'
                self.last_attack_time = current_time
                print(f"[ACTION] {type(self).__name__} Attacks!")
                return True
        return False

    def die(self):
        """Logika dasar kematian"""
        self.alive = False
        self.current_hp = 0
        self.state = 'death'
        print(f"[DEATH] {type(self).__name__} has died.")

    def update(self, platforms):
        """
        Wajib dipanggil oleh Child Class via super().update()
        untuk menjalankan timer cooldown.
        """
        self.update_timers()