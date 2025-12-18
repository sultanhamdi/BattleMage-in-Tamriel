import pygame as pg
from game.settings import BLUE, SCALE
from game.entities.entities import Entity
from game.utils.player_animation_handler import PlayerAnimationHandler
from game.utils.audio.audio_manager import AudioManager

PLAYER_ASSET_PATH = 'assets/graphics/player/'

class Player(Entity): 
    def __init__(self, x, y, audio_manager):
        # stats
        stats_hp = 10000
        stats_attack = 25
        stats_speed = 8

        # parent
        super().__init__(
            x=x, y=y, 
            width=40, height=80,    # Hitbox
            max_hp=stats_hp, 
            attack_power=stats_attack, 
            speed=stats_speed
        )
        
        self.frame_width = 56   
        self.frame_height = 48  
        self.scale = SCALE 
        
        self.animator = PlayerAnimationHandler(PLAYER_ASSET_PATH, self.frame_width, self.frame_height, self.scale)
        self.animation_types = [
            'idle', 'run', 'jump', 'fall', 
            'attack1', 'attack2', 'attack3', 
            'death', 'hurt', 
            'crouch', 'crouch_attack', 'dash',
            'spin_attack', 'sustain_arcane'
        ]
        self.animator.load_sprites(self.animation_types)
        
        # Load Spin Effect (64x32)
        self.animator.load_custom_animation('spin_attack_effect', 64, 32)
        
        # Load Sustain Arcane Fire (72x32)
        self.animator.load_custom_animation('sustain_arcane_fire', 72, 32)

        # combo system
        self.combo_count = 1      
        self.combo_window = 1000  
        self.is_crouching = False # Flag status crouch

        # dash system
        self.DASH_SPEED = 15
        self.DASH_DURATION = 200 # ms
        self.DASH_COOLDOWN = 1000 # ms
        self.is_dashing = False
        self.dash_timer = 0
        self.last_dash_time = 0

        # spin attack system
        self.SPIN_COOLDOWN = 2000 # ms
        self.last_spin_time = 0

        # sustain arcane system
        self.ARCANE_COOLDOWN = 3000 # ms
        self.last_arcane_time = 0
        
        # audio system
        self.audio_manager = audio_manager

    def update_timers(self):
        current_time = pg.time.get_ticks()
        
        # Check player stun (from enemy spells like BOD tornado)
        if hasattr(self, 'is_stunned') and self.is_stunned:
            if current_time >= self.stun_end_time:
                self.is_stunned = False
                # Exit hurt state when stun ends
                if self.state == 'hurt':
                    self.state = 'idle'
                print(f"[STUN] Player recovered from stun!")
            else:
                # FORCE hurt state during stun (prevent other states)
                self.state = 'hurt'
                # Keep looping hurt animation during stun
                if self.animator.animation_finished:
                    self.animator.frame_index = 0  # Loop hurt animation
                    self.animator.animation_finished = False
                    print(f"[STUN] Looping hurt animation...")
        
        # Cek Invincibility
        if self.is_invincible:
            if current_time - self.last_hit_time > self.invincibility_duration:
                self.is_invincible = False

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
        if not self.alive: return 0
        
        # Disable input when hurt to ensure visual feedback
        if self.state == 'hurt':
            return 0
        
        # STUN CHECK - Block all input when stunned (e.g., from BOD spell)
        if hasattr(self, 'is_stunned') and self.is_stunned:
            return 0  # frozen - no movement
        
        keys = pg.key.get_pressed()
        x_velocity = 0
        
        # dash logic
        if self.is_dashing:
            direction = 1 if self.physics.facing_right else -1
            return self.DASH_SPEED * direction

        # Input Dash (W)
        if keys[pg.K_w] and self.alive:
            self.start_dash()

        # crouch logic
        if keys[pg.K_DOWN] and self.physics.on_ground:
            self.is_crouching = True
            x_velocity = 0 # can't move while crouching
        else:
            self.is_crouching = False
            
            # left right logic
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
        # Block if stunned (e.g., from BOD spell)
        if hasattr(self, 'is_stunned') and self.is_stunned:
            return
        
        # Jangan menyerang jika dash, spin, arcane, atau mati
        if self.is_dashing or self.state == 'spin_attack' or self.state == 'sustain_arcane' or not self.alive:
            return
        
        # Block if currently in middle of attack animation
        # Only allow combo if previous attack is almost done or finished
        if self.is_attacking and not self.animator.animation_finished:
            # Check if we're in the last 30% of animation frames
            # This allows chaining combos smoothly
            if self.animator.frame_index < 5:  # Most attacks have 8-10 frames, allow chain at frame 5+
                return

        current_time = pg.time.get_ticks()
        
        # LOGIKA CROUCH ATTACK
        if self.is_crouching:
            self.is_attacking = True
            self.last_attack_time = current_time
            
            self.animator.frame_index = 0
            self.animator.animation_finished = False
            
            self.state = 'crouch_attack'
            print("[ACTION] Player performs Crouch Attack")
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
        self.audio_manager.play_sfx(f'attack{self.combo_count}')
        print(f"[ACTION] Player Combo #{self.combo_count}")

    def spin_attack(self):
        # spin attack skill
        # Block if stunned
        if hasattr(self, 'is_stunned') and self.is_stunned:
            return
        
        if not self.alive or self.state == 'spin_attack':
            return

        current_time = pg.time.get_ticks()
        
        if current_time - self.last_spin_time > self.SPIN_COOLDOWN:
            self.state = 'spin_attack'
            self.last_spin_time = current_time
            
            self.animator.frame_index = 0
            self.animator.animation_finished = False
            self.audio_manager.play_sfx('spin_attack')
            print("[ACTION] Player performs Spin Attack!")

    def sustain_arcane(self):
        # sustain arcane skill
        # Block if stunned
        if hasattr(self, 'is_stunned') and self.is_stunned:
            return
        
        if not self.alive or self.state == 'sustain_arcane':
            return

        current_time = pg.time.get_ticks()
        
        if current_time - self.last_arcane_time > self.ARCANE_COOLDOWN:
            self.state = 'sustain_arcane'
            self.last_arcane_time = current_time
            
            self.animator.frame_index = 0
            self.animator.animation_finished = False
            self.audio_manager.play_sfx('sustain_arcane')
            print("[ACTION] Player performs Sustain Arcane!")

    def get_status(self, x_velocity):
        # state machine
        if not self.alive:
            self.state = 'death'
            return

        # STUN CHECK - Lock hurt state during stun (highest priority after death)
        if hasattr(self, 'is_stunned') and self.is_stunned:
            self.state = 'hurt'
            return  # Block ALL state changes during stun

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
        
        if self.is_invincible and self.state == 'hurt': 
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

    def jump(self):
        # Block if stunned
        if hasattr(self, 'is_stunned') and self.is_stunned:
            return
        
        # Tidak bisa lompat saat crouch atau attack
        if self.alive and not self.is_attacking and not self.is_crouching and self.state != 'spin_attack' and self.state != 'sustain_arcane':
            self.physics.jump()
            self.audio_manager.play_sfx('jump')

    def update(self, platforms):
        self.update_timers()
        x_vel = self.get_input()
        
        if self.alive:
            self.physics.update(platforms, x_vel)
        
        self.get_status(x_vel)
        
        # CRITICAL: Sync rect with physics
        self.rect = self.physics.rect

    def draw(self, surface, camera_offset):
        current_frame = self.animator.animate(self.state, 0.1, self.physics.facing_right)

        if current_frame:
            img_width = current_frame.get_width()
            img_height = current_frame.get_height()
            
            # Use physics.rect for accurate collision box position
            offset_x = (img_width - self.physics.rect.width) // 2
            offset_y = img_height - self.physics.rect.height
            
            draw_pos_x = self.physics.rect.x - camera_offset.x - offset_x
            draw_pos_y = self.physics.rect.y - camera_offset.y - offset_y
            
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