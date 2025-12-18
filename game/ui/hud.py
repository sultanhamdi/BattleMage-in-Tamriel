import pygame as pg
import math
from game.settings import *

class HUD:
    def __init__(self, screen, player):
        self.screen = screen
        self.player = player
        
        # Design Constants
        self.BAR_LENGTH = 300
        self.BAR_HEIGHT = 20
        self.X_POS = 20
        self.Y_POS = 20
        
        # Colors
        self.COLOR_BG = (50, 50, 50)           # Dark Gray
        self.COLOR_BORDER = (255, 255, 255)    # White Border
        self.COLOR_HP = (220, 20, 60)          # Crimson Red
        self.COLOR_DELAY = (255, 255, 0)       # Yellow/White for delay effect
        
        # Logic for Delay Effect
        self.delayed_hp = self.player.current_hp
        self.transition_speed = 2 # Pixels per frame
        
        # Font (Load if possible, else default)
        try:
            self.font = pg.font.Font("assets/fonts/Pixelify_Sans/static/PixelifySans-Bold.ttf", 18)
        except:
            self.font = pg.font.SysFont("Arial", 18)

    def update(self):
        # Smoothly reduce delayed_hp to match current_hp
        if self.delayed_hp > self.player.current_hp:
            self.delayed_hp -= self.transition_speed
        elif self.delayed_hp < self.player.current_hp:
            self.delayed_hp = self.player.current_hp

        # 6. Draw Shine Effect
        # This call is now handled within the draw method on the bar_surf
        # self.draw_shine_effect()

    def draw_shine_effect(self, surface):
        # draw passing shine over bar
        current_time = pg.time.get_ticks()
        
        # Shine Cycle (every 3 seconds)
        cycle_duration = 3000
        shine_pos = (current_time % cycle_duration) / (cycle_duration / 2) # 0 to 2
        
        if shine_pos < 1.0: # Only draw during first half
            skew = 10
            shine_w = 40
            buffer_dist = 100 # Jarak entry dan out (gap)
            
            # Surface width is BAR_LENGTH + skew
            surf_w = self.BAR_LENGTH + skew
            
            # Total travel distance includes the buffer on both sides
            # Start: -shine_w - buffer
            # End: surf_w + buffer
            total_dist = surf_w + shine_w + (2 * buffer_dist)
            
            # Current X in local space
            # Offset by buffer to start "outside"
            x_local = (shine_pos * total_dist) - shine_w - buffer_dist
            
            # Draw Slanted White Shine
            shine_poly = [
                (x_local + skew, 0),                 # Top Left
                (x_local + skew + shine_w, 0),       # Top Right
                (x_local + shine_w, self.BAR_HEIGHT),# Bot Right
                (x_local, self.BAR_HEIGHT)           # Bot Left
            ]
            
            # Direct draw to surface (clipped)
            # Revert to Bright White Shine
            pg.draw.polygon(surface, (255, 255, 255, 150), shine_poly)

    def draw_slanted_rect(self, surface, color, x, y, w, h):
        # draw parallelogram
        skew = 10 
        points = [
            (x + skew, y),          # Top Left
            (x + w + skew, y),      # Top Right
            (x + w, y + h),         # Bottom Right
            (x, y + h)              # Bottom Left
        ]
        pg.draw.polygon(surface, color, points)

    def draw(self):
        # Override draw to use slanted style
        # Clamp HP
        hp_ratio = self.player.current_hp / self.player.max_hp
        delayed_ratio = self.delayed_hp / self.player.max_hp
        hp_ratio = max(0, min(1, hp_ratio))
        delayed_ratio = max(0, min(1, delayed_ratio))

        current_w = int(self.BAR_LENGTH * hp_ratio)
        delayed_w = int(self.BAR_LENGTH * delayed_ratio)
        
        # Create a surface for the bar (Width = Length + Skew, Height)
        skew = 10
        surf_w = self.BAR_LENGTH + skew
        bar_surf = pg.Surface((surf_w, self.BAR_HEIGHT), pg.SRCALPHA)

        # 1. Background (Dark) - Local coords (0,0)
        self.draw_slanted_rect(bar_surf, self.COLOR_BG, 0, 0, self.BAR_LENGTH, self.BAR_HEIGHT)
        
        # 2. Delayed (Yellow)
        if delayed_w > 0:
            self.draw_slanted_rect(bar_surf, self.COLOR_DELAY, 0, 0, delayed_w, self.BAR_HEIGHT)

        # 3. Current (Fixed Gradient: Maroon -> Dark Purple)
        if current_w > 0:
            start_color = (128, 0, 0)   # Maroon
            end_color = (75, 0, 130)    # Purple
            
            for i in range(current_w):
                t = i / self.BAR_LENGTH 
                r = int(start_color[0] + (end_color[0] - start_color[0]) * t)
                g = int(start_color[1] + (end_color[1] - start_color[1]) * t)
                b = int(start_color[2] + (end_color[2] - start_color[2]) * t)
                color = (r, g, b)
                
                # Local coords shift by skew at top? 
                # draw_slanted_rect logic: Top=x+skew, Bot=x
                # So here: p1=(skew+i, 0), p2=(i, h)
                p1 = (skew + i, 0)
                p2 = (i, self.BAR_HEIGHT)
                
                pg.draw.line(bar_surf, color, p1, p2, 1)

            # Core Glow Effect (Horizontal mid-line)
            # To make the dark bar look "glowing", we add a brighter core strip
            glow_h = 4
            glow_y = (self.BAR_HEIGHT - glow_h) // 2
            
            # Draw a horizontal strip with additive blending (simulated by brighter alpha overlay)
            # We can just draw a semi-transparent white-ish rect over the filled area
            # clipped by the slant.
            # Easiest way: Slanted rect with white/rose alpha
            glow_surf = pg.Surface((current_w + skew, glow_h), pg.SRCALPHA)
            # Slanted rect on glow surf
            self.draw_slanted_rect(glow_surf, (255, 255, 255, 50), 0, 0, current_w, glow_h)
            bar_surf.blit(glow_surf, (0, glow_y))
            
            # Top Highlight line for 3D effect
            pg.draw.line(bar_surf, (255, 100, 100), (skew, 0), (skew + current_w, 0), 1)

        # 4. Border - Draw on Surface
        border_pts = [
            (skew, 0),
            (self.BAR_LENGTH + skew - 1, 0),
            (self.BAR_LENGTH - 1, self.BAR_HEIGHT - 1),
            (0, self.BAR_HEIGHT - 1)
        ]
        pg.draw.polygon(bar_surf, (200, 200, 200), border_pts, 2) 
        
        # 6. Shine
        self.draw_shine_effect(bar_surf)
        
        # 7. Blit Bar Surface to Screen
        self.screen.blit(bar_surf, (self.X_POS, self.Y_POS))

        # 5. Text (Draw separately on screen to be crisp and on top)
        hp_text = f"{int(self.player.current_hp)}/{self.player.max_hp}"
        text_surf = self.font.render(hp_text, True, (255, 255, 255))
        self.screen.blit(text_surf, (self.X_POS + self.BAR_LENGTH + 20, self.Y_POS - 2))

