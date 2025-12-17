import pygame as pg
from game.entities.enemies.enemy import BaseEnemy

# Path aset lokal untuk Bringer of Death
BRINGER_ASSET_PATH = 'assets/graphics/enemies/dungeon_monster/bringer_of_death/'

class BringerOfDeath(BaseEnemy):
    """
    Enemy Bringer of Death - Elite Boss dengan Spell Casting.
    
    KARAKTERISTIK:
    - HP: 200 (Boss - Highest)
    - Damage: 30 (Attack), 40 (Spell)
    - Speed: 2.5 (Moderate)
    - Behavior: Spell caster, teleport, powerful magic attacks
    
    ANIMASI:
    Idle(8), Walk(8), Attack(10), Cast(10), Spell(16), Hurt(3), Death(10)
    
    SPECIAL ABILITY:
    - Spell Casting: Powerful magic attacks
    - Phase Shift: Different behavior based on HP
    - Elite Boss: Hardest enemy in dungeon
    """
    
    # AI CONSTANTS
    SPELL_RANGE = 600  # Wider range so spell can trigger even if player backs away
    SPELL_COOLDOWN = 600  # 10 seconds at 60 FPS
    MELEE_RANGE = 70
    PHASE2_HP_THRESHOLD = 0.6  # Phase 2 when HP < 60%
    PHASE3_HP_THRESHOLD = 0.3  # Phase 3 when HP < 30%
    CAST_TRIGGER_HITS = 5  # Number of hits needed to trigger cast (reduced from 6)
    
    def __init__(self, x, y):
        """Initialize Bringer of Death at position (x, y)."""
        super().__init__(
            x=x, y=y,
            # GAMEPLAY HITBOX: Generous coverage for big boss
            width=60, height=120,
            max_hp=200,
            attack_power=30,
            speed=2.5,
            asset_path=BRINGER_ASSET_PATH,
            scale=2.5  # Large boss
        )
        
        # Combat ranges - larger for big boss
        self.detection_range = 600
        self.attack_range = 90  # Slightly smaller range
        self.lose_interest_range = 1000  # Boss never forgets
        
        # Custom Attack Box Dimensions
        self.attack_box_width = 140  # Very long scythe reach
        self.attack_box_height = 100
        
        # Boss mechanics
        self.spell_cooldown = 0
        self.is_casting = False
        self.current_phase = 1
        
        # Cast trigger system
        self.hit_counter = 0  # Track consecutive hits received
        self.is_spell_ready = False  # Flag when ready to cast
        
        # GAMEPLAY HITBOX FIX: Sprite defaults face RIGHT, flipped when LEFT
        # Final perfect centering
        self.sprite_anchor_offset = -85
        
        # Custom Attack Box for massive scythe swing
        self.attack_box_width = 160  # Extended for very long scythe reach
        self.attack_box_height = 100
        
        self._setup_animations()
    
    def _setup_animations(self):
        """Load animasi Bringer of Death."""
        animation_mapping = {
            'idle': 'idle',
            'walk': 'walk',
            'chase': 'walk',
            'attack': 'attack',
            'cast': 'cast',
            'spell': 'spell',
            'hurt': 'hurt',
            'die': 'death',
        }
        self.animator.load_sprites(animation_mapping)
        self.animator.animation_speed = 0.10
    
    def update(self, platforms):
        """Update dengan phase mechanics."""
        # 1. Update Timers
        self.update_timers()
        
        # 2. Cooldown
        if self.spell_cooldown > 0:
            self.spell_cooldown -= 1
        
        # 3. Handle hurt state - CRITICAL FIX
        # Check both animation finished OR invincibility timer to prevent freezing
        current_time = pg.time.get_ticks()
        hurt_timeout = False
        if self.state == 'hurt':
            if current_time - self.last_hit_time > 800: # Max 0.8s in hurt state
                hurt_timeout = True
                
        if self.state == 'hurt' and (self.animator.is_animation_finished() or hurt_timeout):
            self.state = 'idle'
            self.ai_state = self.STATE_IDLE
            # Clear attack state just in case
            self.is_attacking = False
            self.animator.animation_finished = False
        
        # Exit cast state after spell VISUAL animation finishes (not just cast animation)
        if self.state == 'cast' and not self.is_casting:
            # Check if spell visual has finished playing (frame index reached end)
            current_frame = int(self.animator.frame_index)
            spell_frames = self.animator.animations.get('spell', [])
            print(f"[BOD SPELL EXIT CHECK] Frame {current_frame}/{len(spell_frames)}, checking completion...")
            
            # ONLY exit when spell frames fully complete (don't use is_animation_finished - too early!)
            if len(spell_frames) > 0 and current_frame >= len(spell_frames) - 1:
                self.state = 'idle'
                self.ai_state = self.STATE_CHASE  # Return to chasing
                self.animator.animation_finished = False
                self.spell_target_player = False  # Release curse
                print(f"[BRINGER] Spell complete at frame {current_frame}/{len(spell_frames)}, resuming chase!")
                print(f"🎯 [CURSE] Tornado dissipated, curse released!")
        
        # 4. Check phase transitions
        hp_ratio = self.current_hp / self.max_hp
        if hp_ratio < self.PHASE3_HP_THRESHOLD and self.current_phase < 3:
            self.current_phase = 3
            self.base_speed = self.movement_speed
            self.movement_speed = self.base_speed * 1.5
            print(f"[BRINGER] PHASE 3 - DESPERATE FURY!")
        elif hp_ratio < self.PHASE2_HP_THRESHOLD and self.current_phase < 2:
            self.current_phase = 2
            self.base_speed = self.movement_speed
            self.movement_speed = self.base_speed * 1.2
            print(f"[BRINGER] PHASE 2 - RISING POWER!")
        
        # 5. Run custom AI if not in hurt animation
        if self.state != 'hurt' and self.alive:
            # print(f"[BRINGER UPDATE] pos=({self.physics.rect.x},{self.physics.rect.y}) player_ref={'Yes' if self.player_ref else 'NONE'}")
            self._update_ai()
            
            # Map AI state to visual state (like Skullwolf does)
            if self.ai_state in [self.STATE_CHASE, self.STATE_PATROL]:
                self.state = 'walk'
            elif self.ai_state == self.STATE_ATTACK:
                self.state = 'attack'
            elif self.ai_state == 'cast':
                self.state = 'cast'
            elif self.ai_state == self.STATE_IDLE:
                self.state = 'idle'
        else:
             if not self.alive:
                 # Dead
                 pass
             elif self.state == 'hurt':
                 # In hurt animation, do nothing (handled by update_timers)
                 pass
        
        # 6. Update Physics
        if self.alive:
            self.physics.update(platforms, self.physics.velocity_x, apply_gravity=self.has_gravity)
        else:
            self.physics.update(platforms, 0, apply_gravity=self.has_gravity)
        
        # 7. Avoid player collision
        self.avoid_player_collision()
        
        # 8. Sync rect
        self.rect = self.physics.rect
    
    def _update_ai(self):
        """
        IMPROVED AI: Multi-phase boss behavior.
        """
        if not self.alive or not self.player_ref:
            return
        
        # Handle spell casting - PRIORITY, exit early to prevent other state changes
        if self.is_casting:
            # CAST STATE DEBUG - Print every frame during casting
            frame_idx = int(self.animator.frame_index)
            spell_frames = self.animator.animations.get('spell', [])
            print(f"🌪️ [BOD CASTING] Frame={frame_idx}/{len(spell_frames)} is_casting=True state={self.state}")
            
            # Force state to cast (prevent other logic from changing it)
            self.state = 'cast'
            self.ai_state = 'cast'
            self.physics.velocity_x = 0
            
            if self.animator.is_animation_finished():
                # Cast animation completed - trigger spell damage
                self.cast_spell()
                spell_cd = self.SPELL_COOLDOWN
                if self.current_phase >= 2:
                    spell_cd = int(spell_cd * 0.7)  # Faster spells in phase 2+
                self.spell_cooldown = spell_cd
                # STAY in cast state longer - spell visual needs to play
                # is_casting becomes False but state stays 'cast' for visual
                self.is_casting = False
                # AI will exit cast state after spell visual finishes (in update logic below)
                print(f"🌪️ [BOD SPELL TRIGGERED] Damage applied, staying in cast state for visual")
            return  # Exit early - don't run normal state machine during cast
        
        distance = self.get_distance_to_player()
        
        # STATE MACHINE - Phase-based behavior
        if distance > self.detection_range:
            # Patrol menacingly
            self.ai_state = self.STATE_PATROL
            self.physics.velocity_x = self.do_patrol()
        
        
        # DEBUG: Always print when spell ready flag is true
        if self.is_spell_ready:
            print(f"⚠️ [SPELL READY FLAG] TRUE! Checking conditions...")
            print(f"  distance={distance:.1f} <= SPELL_RANGE={self.SPELL_RANGE}? {distance <= self.SPELL_RANGE}")
            print(f"  spell_cooldown={self.spell_cooldown} <= 0? {self.spell_cooldown <= 0}")
        
        # PRIORITY: Cast spell if ready (before melee check!) - MUST BE 'if' not 'elif'!
        if distance <= self.SPELL_RANGE and self.spell_cooldown <= 0 and self.is_spell_ready:
            # SPELL CAST - only if hit counter reached threshold
            self.ai_state = 'cast'
            self.state = 'cast'  # Also set visual state
            self.is_casting = True
            self.is_spell_ready = False  # Consume spell ready flag
            self.hit_counter = 0  # Reset counter after casting
            self.spell_target_player = True  # CURSE: Lock spell onto player!
            self.animator.reset_animation()
            self.physics.velocity_x = 0
            spell_frames = self.animator.animations.get('spell', [])
            print(f"🌪️ [BRINGER] ENTERING CAST STATE! Total spell frames: {len(spell_frames)}")
            print(f"🎯 [CURSE] Tornado locked onto player! Cannot escape!")
            print(f"[BRINGER] SPELL CAST INITIATED! (Was hit {self.CAST_TRIGGER_HITS} times)")

            
            
        elif distance <= self.attack_range:
            # Check if player is stunned from our spell - wait patiently
            if hasattr(self.player_ref, 'is_stunned') and self.player_ref.is_stunned:
                # Player is suffering from our spell, enjoy the show
                self.ai_state = self.STATE_IDLE
                self.physics.velocity_x = 0
                print(f"[BOD] Player stunned, waiting patiently...")
            else:
                # Melee attack - only initiate attack if not already attacking
                self.ai_state = self.STATE_ATTACK
                if not self.is_attacking:
                    print(f"[BOD DEBUG] In attack range! Calling do_attack()")
                    self.do_attack()  # This sets is_attacking = True
                    print(f"[BOD DEBUG] After do_attack: is_attacking={self.is_attacking}, state={self.state}")
                self.physics.velocity_x = 0
            
        else:
            # Chase with phase-based aggression
            self.ai_state = self.STATE_CHASE
            chase_speed = self.do_chase()
            
            # Phase 3: More aggressive movement
            if self.current_phase >= 3:
                chase_speed *= 1.2
            
            self.physics.velocity_x = chase_speed
            # Ensure facing matches movement direction
            if self.physics.velocity_x != 0:
                self.facing_right = self.physics.velocity_x > 0
    
    def cast_spell(self):
        """Cast powerful spell with damage and knockback."""
        # Set attacking flag so collision detection works
        self.is_attacking = True
        self.last_attack_time = pg.time.get_ticks()
        
        # Spell damage (40 base + phase multiplier)
        spell_damage = 40
        damage_multiplier = 1.0 + (0.3 * self.current_phase)
        final_damage = int(spell_damage * damage_multiplier)
        
        # Store damage in custom attribute for game_manager to read
        self.spell_damage = final_damage
        self.spell_knockback = 15  # Strong knockback force
        
        # Reset hit counter and spell ready flag
        self.hit_counter = 0
        self.is_spell_ready = False
        
        print(f"[BRINGER] CASTS SPELL! Damage={final_damage} (Phase {self.current_phase})")
    
    def take_damage(self, amount, apply_stun=False):
        """Override take damage - boss resistance and cast trigger."""
        # Immune during cast animation
        if self.is_casting:
            print(f"[BRINGER] IMMUNE during cast!")
            return
        
        # High resistance
        reduced_damage = amount * 0.85
        super().take_damage(int(reduced_damage), apply_stun=apply_stun)
        
        # Increment hit counter for cast trigger
        if self.alive:
            self.hit_counter += 1
            print(f"[BRINGER] Hit counter: {self.hit_counter}/{self.CAST_TRIGGER_HITS}")
            
            # Ready to cast when threshold reached and cooldown ready
            if self.hit_counter >= self.CAST_TRIGGER_HITS and self.spell_cooldown <= 0:
                self.is_spell_ready = True
                print(f"[BRINGER] SPELL READY! Will cast on next opportunity.")
    
    def draw(self, surface, camera_offset):
        """Override draw to add spell animation overlay."""
        # Draw base enemy (call parent)
        super().draw(surface, camera_offset)
        
        # Draw spell effect overlay when casting
        if self.state == 'cast' and self.player_ref:
            # Get current frame for spell animation
            frame_idx = int(self.animator.frame_index)
            
            # Only show spell starting from frame 6 (after channeling)
            if frame_idx < 6:
                return  # Still channeling, no spell visible yet
            
            # Spell animation is in the 'spell' folder
            spell_frames = self.animator.animations.get('spell')
            
            if spell_frames and frame_idx < len(spell_frames):
                spell_img = spell_frames[frame_idx]
                
                # Flip if facing left
                if not self.facing_right:
                    spell_img = pg.transform.flip(spell_img, True, False)
                
                # Position spell effect ABOVE player's hitbox
                spell_w = spell_img.get_width()
                spell_h = spell_img.get_height()
                
                # Center spell horizontally on player
                spell_x = self.player_ref.physics.rect.centerx - (spell_w // 2) - camera_offset.x
                
                # Position ABOVE player's hitbox (raised 100px for tornado effect)
                spell_y = self.player_ref.physics.rect.centery - (spell_h // 2) - 100 - camera_offset.y
                
                surface.blit(spell_img, (spell_x, spell_y))
