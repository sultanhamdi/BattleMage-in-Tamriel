import pygame as pg
import random
from game.settings import *

# ===========================================
# KONFIGURASI MAIN MENU
# ===========================================
MENU_BG_COLOR = (15, 12, 25)
MENU_TITLE_COLOR = (220, 180, 100)
MENU_TEXT_COLOR = (200, 200, 210)
MENU_HOVER_COLOR = (255, 220, 130)
MENU_SHADOW_COLOR = (0, 0, 0)
MENU_DISABLED_COLOR = (80, 80, 90)

TITLE_Y_POS = 120
MENU_START_Y = 300
MENU_ITEM_SPACING = 65
BUTTON_WIDTH = 320
BUTTON_HEIGHT = 55

# ===========================================


class MainMenu:
    """
    Main Menu dengan sub-menu dan mouse support.
    
    STRUCTURE:
    - Start -> Continue, New Game, Back
    - Guide -> Tutorial controls
    - Settings -> Coming soon
    - Quit
    """
    
    STATE_MAIN = "main"
    STATE_START = "start"
    STATE_GUIDE = "guide"
    STATE_SETTINGS = "settings"
    
    def __init__(self, screen):
        self.screen = screen
        self.clock = pg.time.Clock()
        self.running = True
        
        self.current_state = self.STATE_MAIN
        self.selected_index = 0
        self.has_save_game = False
        
        # Menu items: (label, action, enabled)
        self.main_menu = [
            ("Start", "start", True),
            ("Guide", "guide", True),
            ("Settings", "settings", True),
            ("Quit", "quit", True)
        ]
        
        self.start_menu = [
            ("Continue", "continue", False),  # Disabled tanpa save
            ("New Game", "new_game", True),
            ("Back", "back", True)
        ]
        
        self.settings_menu = [
            ("Music: ON", "music", True),
            ("SFX: ON", "sfx", True),
            ("Back", "back", True)
        ]
        
        self.guide_lines = [
            "=== CONTROLS ===",
            "",
            "[←] / [→]  -  Move",
            "[↑] / [SPACE]  -  Jump",
            "[↓]  -  Crouch",
            "[W]  -  Dash",
            "[E]  -  Attack (Combo x3)",
            "[Q]  -  Spin Attack",
            "[R]  -  Sustain Arcane",
            "[F4]  -  Fullscreen",
            "",
            "=== OBJECTIVE ===",
            "",
            "Defeat enemies and reach the finish!",
            "",
            "Press [ESC] or Click to return"
        ]
        
        # Fonts
        self.title_font = pg.font.Font(None, 90)
        self.menu_font = pg.font.Font(None, 48)
        self.small_font = pg.font.Font(None, 30)
        self.guide_font = pg.font.Font(None, 32)
        
        # Animation
        self.title_offset = 0
        self.title_dir = 1
        self.pulse = 0
        self.pulse_dir = 1
        
        # Particles
        self.particles = self._init_particles(40)
        
        # Button rects untuk mouse
        self.button_rects = []
    
    def _init_particles(self, count):
        return [{
            'x': random.randint(0, WINDOW_WIDTH),
            'y': random.randint(0, WINDOW_HEIGHT),
            'size': random.randint(2, 4),
            'speed': random.uniform(0.2, 0.5),
            'alpha': random.randint(30, 80),
            'color': (random.randint(80, 120), random.randint(60, 100), random.randint(100, 140))
        } for _ in range(count)]
    
    def _update_particles(self):
        for p in self.particles:
            p['y'] -= p['speed']
            if p['y'] < -5:
                p['y'] = WINDOW_HEIGHT + 5
                p['x'] = random.randint(0, WINDOW_WIDTH)
    
    def _draw_particles(self):
        for p in self.particles:
            surf = pg.Surface((p['size']*2, p['size']*2), pg.SRCALPHA)
            pg.draw.circle(surf, (*p['color'], p['alpha']), (p['size'], p['size']), p['size'])
            self.screen.blit(surf, (p['x'], p['y']))
    
    def _update_anims(self):
        self.title_offset += 0.05 * self.title_dir
        if abs(self.title_offset) > 4:
            self.title_dir *= -1
        self.pulse += 2 * self.pulse_dir
        if self.pulse > 25 or self.pulse < 0:
            self.pulse_dir *= -1
        self._update_particles()
    
    def _text_shadow(self, text, font, color, pos, offset=2):
        shadow = font.render(text, True, MENU_SHADOW_COLOR)
        self.screen.blit(shadow, shadow.get_rect(center=(pos[0]+offset, pos[1]+offset)))
        main = font.render(text, True, color)
        self.screen.blit(main, main.get_rect(center=pos))
    
    def _draw_button(self, text, y, selected, enabled=True):
        cx = WINDOW_WIDTH // 2
        rect = pg.Rect(cx - BUTTON_WIDTH//2, y - BUTTON_HEIGHT//2, BUTTON_WIDTH, BUTTON_HEIGHT)
        self.button_rects.append((rect, enabled))
        
        # Colors
        if not enabled:
            txt_col, bdr_col = MENU_DISABLED_COLOR, MENU_DISABLED_COLOR
        elif selected:
            txt_col, bdr_col = MENU_HOVER_COLOR, MENU_HOVER_COLOR
        else:
            txt_col, bdr_col = MENU_TEXT_COLOR, GRAY
        
        # Glow
        if selected and enabled:
            glow = pg.Surface((BUTTON_WIDTH+16, BUTTON_HEIGHT+16), pg.SRCALPHA)
            pg.draw.rect(glow, (*MENU_HOVER_COLOR[:3], 40 + self.pulse), (0,0,BUTTON_WIDTH+16,BUTTON_HEIGHT+16), border_radius=10)
            self.screen.blit(glow, (rect.x-8, rect.y-8))
        
        # Background
        bg = pg.Surface((BUTTON_WIDTH, BUTTON_HEIGHT), pg.SRCALPHA)
        pg.draw.rect(bg, (25, 22, 40, 200), (0, 0, BUTTON_WIDTH, BUTTON_HEIGHT), border_radius=8)
        self.screen.blit(bg, rect)
        
        # Border
        pg.draw.rect(self.screen, bdr_col, rect, 2, border_radius=8)
        
        # Text
        self._text_shadow(text, self.menu_font, txt_col, (cx, y))
        
        # Arrow
        if selected and enabled:
            pts = [(rect.left-25, y), (rect.left-40, y-10), (rect.left-40, y+10)]
            pg.draw.polygon(self.screen, MENU_HOVER_COLOR, pts)
    
    def _draw_title(self):
        y = TITLE_Y_POS + self.title_offset
        self._text_shadow("BATTLEMAGE", self.title_font, MENU_TITLE_COLOR, (WINDOW_WIDTH//2, y), 4)
        self._text_shadow("IN TAMRIEL", self.small_font, MENU_TEXT_COLOR, (WINDOW_WIDTH//2, y+50), 2)
        
        # Decorative line
        cy = TITLE_Y_POS + 90
        pg.draw.line(self.screen, (70, 55, 90), (WINDOW_WIDTH//2-200, cy), (WINDOW_WIDTH//2-40, cy), 2)
        pg.draw.line(self.screen, (70, 55, 90), (WINDOW_WIDTH//2+40, cy), (WINDOW_WIDTH//2+200, cy), 2)
        diamond = [(WINDOW_WIDTH//2, cy-7), (WINDOW_WIDTH//2+7, cy), (WINDOW_WIDTH//2, cy+7), (WINDOW_WIDTH//2-7, cy)]
        pg.draw.polygon(self.screen, MENU_TITLE_COLOR, diamond)
    
    def _draw_footer(self):
        ver = self.small_font.render("v0.1 - PBO Final Project", True, GRAY)
        self.screen.blit(ver, (15, WINDOW_HEIGHT-35))
        hint = self.small_font.render("Mouse Click / [W][S] Navigate / [ENTER] Select", True, GRAY)
        self.screen.blit(hint, hint.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT-35)))
    
    def _get_menu(self):
        if self.current_state == self.STATE_MAIN:
            return self.main_menu
        elif self.current_state == self.STATE_START:
            return self.start_menu
        elif self.current_state == self.STATE_SETTINGS:
            return self.settings_menu
        return []
    
    def _draw_menu_items(self, items, title=None):
        self.button_rects = []
        start_y = MENU_START_Y
        
        if title:
            self._text_shadow(title, self.menu_font, MENU_TEXT_COLOR, (WINDOW_WIDTH//2, start_y - 60), 2)
        
        for i, (label, action, enabled) in enumerate(items):
            y = start_y + i * MENU_ITEM_SPACING
            self._draw_button(label, y, i == self.selected_index, enabled)
    
    def _draw_guide(self):
        # Panel
        panel = pg.Rect(80, 130, WINDOW_WIDTH-160, WINDOW_HEIGHT-200)
        bg = pg.Surface((panel.width, panel.height), pg.SRCALPHA)
        pg.draw.rect(bg, (20, 18, 35, 240), (0, 0, panel.width, panel.height), border_radius=12)
        self.screen.blit(bg, panel)
        pg.draw.rect(self.screen, MENU_TITLE_COLOR, panel, 2, border_radius=12)
        
        # Title
        self._text_shadow("GUIDE", self.title_font, MENU_TITLE_COLOR, (WINDOW_WIDTH//2, 90), 3)
        
        # Content
        y = 180
        for line in self.guide_lines:
            if line.startswith("==="):
                color = MENU_TITLE_COLOR
            elif line == "":
                y += 10
                continue
            else:
                color = MENU_TEXT_COLOR
            txt = self.guide_font.render(line, True, color)
            self.screen.blit(txt, txt.get_rect(center=(WINDOW_WIDTH//2, y)))
            y += 35
    
    def draw(self):
        self.screen.fill(MENU_BG_COLOR)
        self._draw_particles()
        
        if self.current_state == self.STATE_GUIDE:
            self._draw_guide()
        else:
            self._draw_title()
            
            if self.current_state == self.STATE_MAIN:
                self._draw_menu_items(self.main_menu)
            elif self.current_state == self.STATE_START:
                self._draw_menu_items(self.start_menu, "- START GAME -")
            elif self.current_state == self.STATE_SETTINGS:
                self._draw_menu_items(self.settings_menu, "- SETTINGS -")
        
        self._draw_footer()
        pg.display.flip()
    
    def _select_item(self):
        items = self._get_menu()
        if not items or self.selected_index >= len(items):
            return None
        
        label, action, enabled = items[self.selected_index]
        if not enabled:
            return None
        
        # Handle actions
        if action == "start":
            self.current_state = self.STATE_START
            self.selected_index = 1  # New Game
        elif action == "guide":
            self.current_state = self.STATE_GUIDE
        elif action == "settings":
            self.current_state = self.STATE_SETTINGS
            self.selected_index = 2  # Back
        elif action == "back":
            self.current_state = self.STATE_MAIN
            self.selected_index = 0
        elif action == "new_game":
            return "new_game"
        elif action == "continue":
            return "continue"
        elif action == "quit":
            return "quit"
        elif action == "music":
            # Toggle (placeholder)
            self.settings_menu[0] = ("Music: OFF" if "ON" in label else "Music: ON", "music", True)
        elif action == "sfx":
            self.settings_menu[1] = ("SFX: OFF" if "ON" in label else "SFX: ON", "sfx", True)
        
        return None
    
    def handle_events(self):
        mouse_pos = pg.mouse.get_pos()
        
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return "quit"
            
            # Mouse hover
            if event.type == pg.MOUSEMOTION and self.current_state != self.STATE_GUIDE:
                for i, (rect, enabled) in enumerate(self.button_rects):
                    if rect.collidepoint(mouse_pos):
                        self.selected_index = i
                        break
            
            # Mouse click
            if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                if self.current_state == self.STATE_GUIDE:
                    self.current_state = self.STATE_MAIN
                    self.selected_index = 0
                else:
                    for i, (rect, enabled) in enumerate(self.button_rects):
                        if rect.collidepoint(mouse_pos) and enabled:
                            self.selected_index = i
                            result = self._select_item()
                            if result:
                                return result
                            break
            
            # Keyboard
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    if self.current_state != self.STATE_MAIN:
                        self.current_state = self.STATE_MAIN
                        self.selected_index = 0
                    else:
                        return "quit"
                
                if self.current_state != self.STATE_GUIDE:
                    items = self._get_menu()
                    if event.key in (pg.K_UP, pg.K_w):
                        self.selected_index = (self.selected_index - 1) % len(items)
                    elif event.key in (pg.K_DOWN, pg.K_s):
                        self.selected_index = (self.selected_index + 1) % len(items)
                    elif event.key in (pg.K_RETURN, pg.K_SPACE):
                        result = self._select_item()
                        if result:
                            return result
        
        return None
    
    def run(self):
        while self.running:
            action = self.handle_events()
            if action:
                return action
            self._update_anims()
            self.draw()
            self.clock.tick(FPS)
        return "quit"


if __name__ == "__main__":
    pg.init()
    screen = pg.display.set_mode(WINDOW_SIZE)
    pg.display.set_caption(TITLE)
    menu = MainMenu(screen)
    print(f"Result: {menu.run()}")
    pg.quit()
