import pygame as pg
import sys
from game.settings import *
from game.entities.player import Player
from game.utils.camera import Camera
from game.level.level_manager import LevelManager

# Import Enemy Classes
from game.entities.enemies import Zombie, Golem, Vampire

# ===========================================
# KONFIGURASI ENEMY SPAWN
# ===========================================
# Format: (EnemyClass, x, y)
# Ubah list ini untuk mengatur jumlah dan posisi enemy
# Posisi dalam pixel (sesuaikan dengan layout level)

ENEMY_SPAWN_CONFIG = [
    # --- ZOMBIE (Patrol di platform) ---
    (Zombie, 400, 350),   # Zombie 1: Di platform tengah
    (Zombie, 700, 350),   # Zombie 2: Di platform kanan
    
    # --- GOLEM (Diam sampai player mendekat) ---
    (Golem, 900, 330),    # Golem: Di ujung kanan
    
    # --- VAMPIRE (Terbang) ---
    (Vampire, 500, 150),  # Vampire: Di udara
]

# ===========================================


class Game:
    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode(WINDOW_SIZE)
        pg.display.set_caption(TITLE)
        self.clock = pg.time.Clock()
        self.running = True
        
        # 1. Spawn player (Posisi sementara, nanti kita ambil dari map)
        self.player = Player(100, 100)
        
        # 2. Inisialisasi Kamera
        self.camera = Camera(WINDOW_WIDTH, WINDOW_HEIGHT)
        
        # 3. Setup Level Manager
        self.level_manager = LevelManager(current_theme='dungeon')
        
        # Generate Rects dan Gambar dari Map Teks
        # self.platforms: Untuk collision (Fisika)
        # self.visual_tiles: Untuk digambar (Visual)
        self.platforms, self.visual_tiles = self.level_manager.create_level()
        
        # 4. [BARU] Spawn Enemies dari Config
        self.enemies = []
        self.spawn_enemies()
        
        # 5. [BARU] Combat tracking - supaya 1 serangan = 1 hit
        self.player_hit_enemies = set()  # Set enemy yang sudah kena di serangan ini
        self.enemy_hit_player = set()    # Set enemy yang sudah hit player di serangan ini

    def spawn_enemies(self):
        """
        Spawn semua enemy berdasarkan ENEMY_SPAWN_CONFIG.
        Dipanggil sekali saat game init.
        """
        for EnemyClass, x, y in ENEMY_SPAWN_CONFIG:
            enemy = EnemyClass(x, y)
            enemy.set_player_reference(self.player)  # Untuk AI detection
            self.enemies.append(enemy)
            print(f"[SPAWN] {EnemyClass.__name__} at ({x}, {y})")
        
        print(f"[INFO] Total enemies spawned: {len(self.enemies)}")

    def events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
                pg.quit()
                sys.exit()
            
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_F4:
                    is_fullscreen = self.screen.get_flags() & pg.FULLSCREEN
                    if is_fullscreen:
                        self.screen = pg.display.set_mode(WINDOW_SIZE)
                    else:
                        self.screen = pg.display.set_mode(WINDOW_SIZE, pg.FULLSCREEN)
                
                if event.key == pg.K_SPACE or event.key == pg.K_w or event.key == pg.K_UP:
                    self.player.jump()

    def check_player_attack_collision(self):
        """
        Cek apakah serangan player mengenai enemy.
        Dipanggil setiap frame saat player sedang menyerang.
        """
        if not self.player.is_attacking or not self.player.alive:
            # Reset tracking saat tidak menyerang
            self.player_hit_enemies.clear()
            return
        
        # Buat attack hitbox berdasarkan posisi dan arah hadap player
        attack_width = 50
        attack_height = 60
        
        # Tentukan posisi hitbox berdasarkan arah hadap
        if self.player.physics.facing_right:
            attack_x = self.player.rect.right
        else:
            attack_x = self.player.rect.left - attack_width
        
        attack_y = self.player.rect.centery - attack_height // 2
        
        # Buat rectangle untuk attack hitbox
        attack_rect = pg.Rect(attack_x, attack_y, attack_width, attack_height)
        
        # Cek collision dengan semua enemy
        for enemy in self.enemies:
            if not enemy.alive:
                continue
            
            # Skip jika enemy sudah pernah kena di serangan ini
            if id(enemy) in self.player_hit_enemies:
                continue
            
            # Cek apakah attack hitbox mengenai enemy
            if attack_rect.colliderect(enemy.rect):
                enemy.take_damage(self.player.attack_power)
                self.player_hit_enemies.add(id(enemy))  # Tandai sudah kena
                print(f"[HIT] Player hits {type(enemy).__name__}!")

    def check_enemy_attack_collision(self):
        """
        Cek apakah serangan enemy mengenai player.
        """
        if not self.player.alive:
            return
        
        for enemy in self.enemies:
            if not enemy.alive or not enemy.is_attacking:
                # Reset tracking untuk enemy ini saat tidak menyerang
                self.enemy_hit_player.discard(id(enemy))
                continue
            
            # Skip jika enemy sudah hit player di serangan ini
            if id(enemy) in self.enemy_hit_player:
                continue
            
            # Buat attack hitbox untuk enemy
            attack_width = 40
            attack_height = 50
            
            if enemy.facing_right:
                attack_x = enemy.rect.right
            else:
                attack_x = enemy.rect.left - attack_width
            
            attack_y = enemy.rect.centery - attack_height // 2
            attack_rect = pg.Rect(attack_x, attack_y, attack_width, attack_height)
            
            # Cek collision dengan player
            if attack_rect.colliderect(self.player.rect):
                self.player.take_damage(enemy.attack_power)
                self.enemy_hit_player.add(id(enemy))  # Tandai sudah hit
                print(f"[HIT] {type(enemy).__name__} hits Player!")

    def remove_dead_enemies(self):
        """Hapus enemy yang sudah mati (setelah animasi death selesai)"""
        # Filter: Keep enemy yang masih alive ATAU masih ada animasi death
        self.enemies = [e for e in self.enemies if e.alive or (not e.alive and e.animator.frame_index < len(e.animator.animations.get('die', [])) - 1)]

    def update(self):
        # Update Player (cek tabrakan dengan rects dari level manager)
        self.player.update(self.platforms)
        
        # [BARU] Update semua Enemy
        for enemy in self.enemies:
            enemy.update(self.platforms)
        
        # [BARU] Cek Combat Collisions
        self.check_player_attack_collision()
        self.check_enemy_attack_collision()
        
        # [BARU] Cleanup dead enemies
        self.remove_dead_enemies()
        
        # Update Kamera
        self.camera.follow(self.player.rect)

    def draw(self):
        self.screen.fill(BG_COLOR)
        
        # Gambar Tileset (Lantai Bergambar)
        for img, rect in self.visual_tiles:
            # Terapkan Offset Kamera
            draw_pos_x = rect.x - self.camera.offset.x
            draw_pos_y = rect.y - self.camera.offset.y
            self.screen.blit(img, (draw_pos_x, draw_pos_y))

        # [BARU] Gambar semua Enemy
        for enemy in self.enemies:
            enemy.draw(self.screen, self.camera.offset)

        # Gambar Player
        self.player.draw(self.screen, self.camera.offset)
        
        pg.display.flip()

    def run(self):
        while self.running:
            self.events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
