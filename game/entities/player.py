import pygame as pg
from game.settings import BLUE, SCALE
from game.entities.entities import Entity
from game.utils.player_animation_handler import PlayerAnimationHandler

# Path aset lokal untuk player
PLAYER_ASSET_PATH = 'assets/graphics/player/'

class Player(Entity): 
    def __init__(self, x, y):
        # STATS
        stats_hp = 200
        stats_attack = 25
        stats_speed = 8

        # INIT PARENT
        super().__init__(
            x=x, y=y, 
            width=40, height=80,    # Ukuran Hitbox
            max_hp=stats_hp, 
            attack_power=stats_attack, 
            speed=stats_speed
        )
        
        # SETUP VISUAL
        self.frame_width = 56   
        self.frame_height = 48  
        self.scale = SCALE 
        
        self.animator = PlayerAnimationHandler(PLAYER_ASSET_PATH, self.frame_width, self.frame_height, self.scale)
        self.animation_types = [
            'idle', 'run', 'jump', 'fall', 
            'attack1', 'attack2', 'attack3', 
            'death', 'hurt', 'hurt2',
            'crouch', 'crouch_attack', 'dash',
            'spin_attack', 'sustain_arcane'
        ]
        self.animator.load_sprites(self.animation_types)
        
        # Load Spin Effect (64x32)
        self.animator.load_custom_animation('spin_attack_effect', 64, 32)
        
        # Load Sustain Arcane Fire (72x32)
        # Load Sustain Arcane Fire (72x32)
        self.animator.load_custom_animation('sustain_arcane_fire', 72, 32)
        
        self.audio_manager = None

        # SETUP SYSTEM
        self.combo_count = 1      
        self.combo_window = 1000  
        self.is_crouching = False # Flag status crouch

        # DASH SYSTEM
        self.DASH_SPEED = 15
        self.DASH_DURATION = 200 # ms
        self.DASH_COOLDOWN = 1000 # ms
        self.is_dashing = False
        self.dash_timer = 0
        self.last_dash_time = 0

        # SPIN ATTACK SYSTEM
        self.SPIN_COOLDOWN = 2000 # ms
        self.last_spin_time = 0

        # SUSTAIN ARCANE SYSTEM
        self.ARCANE_COOLDOWN = 3000 # ms
        self.last_arcane_time = 0

    def take_damage(self, amount):
        """Override take_damage untuk variasi animasi hurt"""
        if not self.alive or self.is_invincible:
            return

        # Panggil logic parent untuk perhitungan HP & Invincibility
        super().take_damage(amount)
        
        # Jika alive, pilih animasi hurt secara acak
        if self.alive:
            import random
            self.state = random.choice(['hurt', 'hurt2'])
            
            # Reset frame agar animasi mulai dari awal
            self.animator.frame_index = 0
            self.animator.animation_finished = False
            
            print(f"[COMBAT] Player animation: {self.state}")

    # ... (Skipping methods until get_status) ...

    def get_status(self, x_velocity):
        """State Machine"""
        if not self.alive:
            self.state = 'death'
            return

        # Prioritas 0: Dash
        if self.is_dashing:
            self.state = 'dash'
            return

        # Prioritas 0.5: Spin Attack & Sustain Arcane (Lock State)
        if self.state == 'spin_attack' or self.state == 'sustain_arcane':
            return

        # Prioritas 1: Attack
        if self.is_attacking:
            # Jika sedang crouch attack, biarkan state-nya tetap 'crouch_attack'
            if self.state == 'crouch_attack':
                return
            # Jika normal combo, update sesuai combo count
            self.state = f'attack{self.combo_count}'
            return
        
        # Prioritas 1.5: Hurt (Lock State selama invincibility/animasi)
        if self.is_invincible and (self.state == 'hurt' or self.state == 'hurt2'): 
            return

        # Prioritas 2: Udara
        if self.physics.velocity.y < 0:
            self.state = 'jump'
        elif self.physics.velocity.y > 1:
            self.state = 'fall'

        
        # Prioritas 3: Tanah
        else:
            if self.is_crouching:
                self.state = 'crouch'
            elif x_velocity != 0: 
                 self.state = 'run'
            else: 
                 self.state = 'idle'

    def update_timers(self):
        """Override Parent Timer Logic"""
        current_time = pg.time.get_ticks()
        
        # Cek Invincibility
        if self.is_invincible:
            if current_time - self.last_hit_time > self.invincibility_duration:
                self.is_invincible = False

        # LOGIKA FOOTSTEP (Saat lari)
        if self.state == 'run' and self.physics.on_ground:
            # Trigger footstep pada frame tertentu (misal frame 1 dan 4)
            # Frame index adalah float, jadi cek saat integer-nya berubah
            current_frame_idx = int(self.animator.frame_index)
            
            # Kita butuh properti untuk simpan last frame agar tidak spawn suara berkali-kali di frame yang sama
            if not hasattr(self, 'last_footstep_frame'):
                self.last_footstep_frame = -1
                
            if current_frame_idx != self.last_footstep_frame:
                # Asumsi animasi lari punya 6-8 frame. Trigger di frame 1 dan 4 agar ritmis
                if current_frame_idx % 3 == 0: 
                    if self.audio_manager:
                        self.audio_manager.play_footstep()
                
                self.last_footstep_frame = current_frame_idx
        else:
            # Reset jika tidak lari
            self.last_footstep_frame = -1

        # Cek Attack Selesai
        if self.is_attacking:
            if self.animator.animation_finished:
                self.is_attacking = False
                self.animator.animation_finished = False 
                if self.alive:
                    self.state = 'idle'

        # Cek Dash Selesai
        if self.is_dashing:
            if current_time - self.dash_timer > self.DASH_DURATION:
                self.is_dashing = False
                if self.alive:
                    self.state = 'idle'

        # Cek Spin Attack Selesai
        if self.state == 'spin_attack':
            if self.animator.animation_finished:
                self.state = 'idle'
                self.animator.animation_finished = False

        # Cek Sustain Arcane Selesai
        if self.state == 'sustain_arcane':
            if self.animator.animation_finished:
                self.state = 'idle'
                self.animator.animation_finished = False

    def get_input(self):
        """Mengambil input keyboard khusus Player"""
        if not self.alive: return 0

        keys = pg.key.get_pressed()
        x_velocity = 0
        
        # LOGIKA DASH
        # Jika sedang dash, abaikan input lain dan paksa gerak cepat
        if self.is_dashing:
            direction = 1 if self.physics.facing_right else -1
            return self.DASH_SPEED * direction

        # Input Dash (W)
        if keys[pg.K_w] and self.alive:
            self.start_dash()

        # LOGIKA CROUCH
        # Hanya bisa crouch jika di tanah
        if keys[pg.K_DOWN] and self.physics.on_ground:
            self.is_crouching = True
            x_velocity = 0 # Tidak bisa jalan saat crouch
        else:
            self.is_crouching = False
            
            # Gerak Kiri Kanan (Hanya jika TIDAK crouch)
            if keys[pg.K_LEFT]:
                x_velocity = -self.movement_speed
            if keys[pg.K_RIGHT]:
                x_velocity = self.movement_speed
            
        # Input Serangan (Tombol E)
        if keys[pg.K_e]:
            self.attack() 
            
        # Input Spin Attack (Tombol Q)
        if keys[pg.K_q]:
            self.spin_attack()
            
        # Input Sustain Arcane (Tombol R)
        if keys[pg.K_r]:
            self.sustain_arcane()
            
        return x_velocity

    def start_dash(self):
        """Memulai aksi Dash"""
        current_time = pg.time.get_ticks()
        
        # Cek Cooldown
        if current_time - self.last_dash_time > self.DASH_COOLDOWN:
            self.is_dashing = True
            self.dash_timer = current_time
            self.last_dash_time = current_time
            self.state = 'dash'
            
            # Reset animasi dash agar main dari awal
            self.animator.frame_index = 0
            self.animator.animation_finished = False
            
            print("[ACTION] Player Dashes!")

    def attack(self):
        """Logika Serangan (Combo & Crouch Attack)"""
        # Jangan menyerang jika sedang menyerang, dash, spin, arcane, atau mati
        if self.is_attacking or self.is_dashing or self.state == 'spin_attack' or self.state == 'sustain_arcane' or not self.alive:
            return

        current_time = pg.time.get_ticks()
        
        # LOGIKA CROUCH ATTACK
        if self.is_crouching:
            self.is_attacking = True
            self.last_attack_time = current_time
            
            # Reset animasi
            self.animator.frame_index = 0
            self.animator.animation_finished = False
            
            self.state = 'crouch_attack'
            print("[ACTION] Player performs Crouch Attack")
            
            if self.audio_manager:
                self.audio_manager.play_sfx('attack1') # Use attack1 sfx for crouch attack
            return

        # LOGIKA NORMAL COMBO
        time_since_last = current_time - self.last_attack_time

        if time_since_last < self.combo_window:
            self.combo_count += 1
        else:
            self.combo_count = 1 

        if self.combo_count > 3:
            self.combo_count = 1
            
        self.is_attacking = True
        self.last_attack_time = current_time
        
        self.animator.frame_index = 0
        self.animator.animation_finished = False
        
        self.state = f'attack{self.combo_count}' 
        print(f"[ACTION] Player Combo #{self.combo_count}")
        
        if self.audio_manager:
            self.audio_manager.play_sfx(self.state)

    def spin_attack(self):
        """Memulai Spin Attack"""
        if not self.alive or self.state == 'spin_attack':
            return

        current_time = pg.time.get_ticks()
        
        if current_time - self.last_spin_time > self.SPIN_COOLDOWN:
            self.state = 'spin_attack'
            self.last_spin_time = current_time
            
            self.animator.frame_index = 0
            self.animator.animation_finished = False
            
            print("[ACTION] Player performs Spin Attack!")
            
            if self.audio_manager:
                self.audio_manager.play_sfx('spin_attack')

    def sustain_arcane(self):
        """Memulai Sustain Arcane Attack"""
        if not self.alive or self.state == 'sustain_arcane':
            return

        current_time = pg.time.get_ticks()
        
        if current_time - self.last_arcane_time > self.ARCANE_COOLDOWN:
            self.state = 'sustain_arcane'
            self.last_arcane_time = current_time
            
            self.animator.frame_index = 0
            self.animator.animation_finished = False
            
            print("[ACTION] Player performs Sustain Arcane!")
            
            if self.audio_manager:
                self.audio_manager.play_sfx('sustain_arcane')



    def jump(self):
        # Tidak bisa lompat saat crouch atau attack
        if self.alive and not self.is_attacking and not self.is_crouching and self.state != 'spin_attack' and self.state != 'sustain_arcane':
            self.physics.jump()
            if self.audio_manager:
                self.audio_manager.play_sfx('jump')

    def update(self, platforms):
        self.update_timers()
        x_vel = self.get_input()
        
        if self.alive:
            self.physics.update(platforms, x_vel)
        
        self.get_status(x_vel)

    def draw(self, surface, camera_offset):
        current_frame = self.animator.animate(self.state, 0.1, self.physics.facing_right)

        if current_frame:
            img_width = current_frame.get_width()
            img_height = current_frame.get_height()
            
            offset_x = (img_width - self.rect.width) // 2
            offset_y = img_height - self.rect.height
            
            draw_pos_x = self.rect.x - camera_offset.x - offset_x
            draw_pos_y = self.rect.y - camera_offset.y - offset_y
            
            surface.blit(current_frame, (draw_pos_x, draw_pos_y))
            
            # DRAW OVERLAY EFFECT (SPIN ATTACK)
            if self.state == 'spin_attack':
                frame_idx = int(self.animator.frame_index)
                # Effect mulai di frame 5, durasi 7 frame
                if 5 <= frame_idx < 5 + 7:
                    effect_idx = frame_idx - 5
                    effect_frames = self.animator.animations.get('spin_attack_effect')
                    
                    if effect_frames and effect_idx < len(effect_frames):
                        effect_img = effect_frames[effect_idx]
                        if not self.physics.facing_right:
                            effect_img = pg.transform.flip(effect_img, True, False)
                            
                        # Center effect on player
                        eff_w = effect_img.get_width()
                        eff_h = effect_img.get_height()
                        
                        eff_x = self.rect.centerx - camera_offset.x - (eff_w // 2)
                        eff_y = self.rect.centery - camera_offset.y - (eff_h // 2)
                        
                        surface.blit(effect_img, (eff_x, eff_y))

            # DRAW OVERLAY EFFECT (SUSTAIN ARCANE)
            if self.state == 'sustain_arcane':
                frame_idx = int(self.animator.frame_index)
                
                effect_frames = self.animator.animations.get('sustain_arcane_fire')
                if effect_frames:
                    effect_idx = frame_idx % len(effect_frames)
                    
                    effect_img = effect_frames[effect_idx]
                    if not self.physics.facing_right:
                        effect_img = pg.transform.flip(effect_img, True, False)
                        
                    # Position effect in front of player (Long Ranged)
                    eff_w = effect_img.get_width()
                    eff_h = effect_img.get_height()
                    
                    # Hitbox width = 40, Visual width = 56. Diff = 16. Side = 8.
                    offset_dist = 8
                    
                    if self.physics.facing_right:
                        eff_x = self.rect.right - camera_offset.x + offset_dist
                    else:
                        eff_x = self.rect.left - camera_offset.x - eff_w - offset_dist
                        
                    eff_y = self.rect.centery - camera_offset.y - (eff_h // 2) - 10
                    
                    surface.blit(effect_img, (eff_x, eff_y))

        else:
            # Fallback
            color = BLUE
            draw_rect = self.rect.copy()
            draw_rect.x -= camera_offset.x
            draw_rect.y -= camera_offset.y
            pg.draw.rect(surface, color, draw_rect)