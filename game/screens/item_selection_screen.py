# Item Selection Screen
# Handles the UI for choosing rewards between levels

import pygame as pg

class ItemSelectionScreen:
    def __init__(self, screen, window_width, window_height):
        self.screen = screen
        self.window_width = window_width
        self.window_height = window_height
        self.item_icons = {} # Cache for loaded icons
        
        # Load Background Image
        self.background_img = None
        try:
            bg_path = "assets/graphics/ui/item_menu_bg.png"
            loaded_bg = pg.image.load(bg_path).convert()
            self.background_img = pg.transform.scale(loaded_bg, (window_width, window_height))
            # Darken the background slightly for better readability
            self.background_img.set_alpha(200) 
        except Exception as e:
            print(f"[WARN] Failed to load item menu bg: {e}")

    def render(self, item_manager, choice_ids, selected_index):
        """Draw the selection UI overlay"""
        # Background
        if self.background_img:
            self.screen.blit(self.background_img, (0, 0))
        else:
            overlay = pg.Surface((self.window_width, self.window_height))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(200)
            self.screen.blit(overlay, (0, 0))
        
        # Helper to get font from assets
        def get_pixel_font(size, bold=False):
            try:
                # Use absolute path relative to main.py execution or relative assets
                # Assuming assets is in current directory
                if bold:
                    return pg.font.Font("assets/fonts/Pixelify_Sans/static/PixelifySans-Bold.ttf", size)
                else:
                    return pg.font.Font("assets/fonts/Pixelify_Sans/static/PixelifySans-Regular.ttf", size)
            except Exception as e:
                # Fallback
                return pg.font.SysFont("consolas", size, bold=bold)

        # Title
        font_title = get_pixel_font(48, bold=True)
        title_surf = font_title.render("CHOOSE YOUR REWARD", True, (255, 215, 0)) # Gold color
        title_rect = title_surf.get_rect(center=(self.window_width // 2, 100))
        self.screen.blit(title_surf, title_rect)
        
        # Calculate positions
        center_x = self.window_width // 2
        card_width = 300
        card_height = 400
        spacing = 50
        
        start_x_left = center_x - card_width - (spacing // 2)
        start_x_right = center_x + (spacing // 2)
        card_y = (self.window_height - card_height) // 2
        
        # Draw Cards
        if len(choice_ids) >= 2:
            self._draw_card(item_manager, choice_ids[0], selected_index == 0, start_x_left, card_y, card_width, card_height)
            self._draw_card(item_manager, choice_ids[1], selected_index == 1, start_x_right, card_y, card_width, card_height)

    def _draw_card(self, item_manager, item_id, is_selected, x, y, width, height):
        item_data = item_manager.get_item_info(item_id)
        if not item_data: return
        
        # Helper to get font from assets (local scope)
        def get_pixel_font(size, bold=False):
            try:
                if bold:
                    return pg.font.Font("assets/fonts/Pixelify_Sans/static/PixelifySans-Bold.ttf", size)
                else:
                    return pg.font.Font("assets/fonts/Pixelify_Sans/static/PixelifySans-Regular.ttf", size)
            except Exception:
                return pg.font.SysFont("consolas", size, bold=bold)

        # Dynamic Colors based on Item Type
        # Get type string (safely handle Enum or String)
        itype = item_data.get('type')
        if hasattr(itype, 'value'): itype = itype.value
        
        # Default Theme (Grey)
        theme_bg = (40, 40, 50)
        theme_border = (100, 100, 100)
        theme_title = (200, 200, 200)
        
        if itype == "attack":     # Red Theme
            theme_bg = (60, 20, 20)
            theme_border = (180, 50, 50)
            theme_title = (255, 150, 150)
        elif itype == "defense":  # Blue Theme
            theme_bg = (20, 30, 60)
            theme_border = (50, 80, 180)
            theme_title = (150, 180, 255)
        elif itype == "mobility": # Green Theme
            theme_bg = (20, 50, 30)
            theme_border = (50, 160, 80)
            theme_title = (150, 255, 180)
        elif itype == "cooldown": # Purple Theme
            theme_bg = (45, 20, 60)
            theme_border = (140, 60, 180)
            theme_title = (220, 150, 255)

        # Selection States
        if is_selected:
            # Brighten BG slightly
            bg_color = (min(theme_bg[0]+30, 255), min(theme_bg[1]+30, 255), min(theme_bg[2]+30, 255))
            # Gold border for selection
            border_color = (255, 223, 0)
            border_width = 4
            
            # Pulse Animation
            offset_y = -10
        else:
            bg_color = theme_bg
            border_color = theme_border
            border_width = 2
            offset_y = 0

        # Colors for text
        COLOR_TEXT_TITLE = (255, 255, 255) # Keep White for readability, or use theme_title
        COLOR_TEXT_DESC = (200, 200, 200)
        COLOR_STAT_POSITIVE = (120, 255, 120)
        COLOR_STAT_NEGATIVE = (255, 120, 120)

        rect = pg.Rect(x, y + offset_y, width, height)
        
        # Card Background & Shadow
        shadow_rect = rect.copy()
        shadow_rect.move_ip(5, 5)
        pg.draw.rect(self.screen, (10, 10, 10), shadow_rect, border_radius=15) # Shadow
        
        pg.draw.rect(self.screen, bg_color, rect, border_radius=15)
        pg.draw.rect(self.screen, border_color, rect, border_width, border_radius=15)
        
        # Icon Background Circle (Darker shade of theme)
        circle_color = (max(0, bg_color[0]-20), max(0, bg_color[1]-20), max(0, bg_color[2]-20))
        icon_center_x = x + width // 2
        icon_center_y = y + offset_y + 80
        pg.draw.circle(self.screen, circle_color, (icon_center_x, icon_center_y), 40)
        pg.draw.circle(self.screen, border_color, (icon_center_x, icon_center_y), 40, 2) # Ring matches border
        
        # Icon
        icon_path = f"assets/graphics/items/{item_data['icon']}"
        try:
            if item_id not in self.item_icons:
                loaded_img = pg.image.load(icon_path).convert_alpha()
                self.item_icons[item_id] = pg.transform.scale(loaded_img, (64, 64))
            
            icon_img = self.item_icons[item_id]
            icon_rect = icon_img.get_rect(center=(icon_center_x, icon_center_y))
            self.screen.blit(icon_img, icon_rect)
        except Exception:
            pg.draw.rect(self.screen, (255, 0, 255), (icon_center_x - 32, icon_center_y - 32, 64, 64))
        
        # Name (Using Pixel Font)
        font_name = get_pixel_font(28, bold=True)
        name_surf = font_name.render(item_data['name'], True, COLOR_TEXT_TITLE)
        
        # Scale down if too wide
        if name_surf.get_width() > width - 20:
             font_name = get_pixel_font(20, bold=True)
             name_surf = font_name.render(item_data['name'], True, COLOR_TEXT_TITLE)
             
        name_rect = name_surf.get_rect(center=(x + width//2, y + offset_y + 150))
        self.screen.blit(name_surf, name_rect)
        
        # Description Separator
        pg.draw.line(self.screen, border_color, (x + 40, y + offset_y + 175), (x + width - 40, y + offset_y + 175), 1)
        
        # Description (Using Pixel Font Regular) with WORD WRAP
        font_desc = get_pixel_font(18, bold=False)
        desc_text = item_data['description']
        
        # Word Wrap Logic
        words = desc_text.split(' ')
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            # Check width (card width - padding)
            if font_desc.size(test_line)[0] < width - 40:
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
        lines.append(' '.join(current_line))
        
        # Render Lines
        desc_y = y + offset_y + 195
        for line in lines:
            desc_surf = font_desc.render(line, True, COLOR_TEXT_DESC)
            desc_rect = desc_surf.get_rect(center=(x + width//2, desc_y))
            self.screen.blit(desc_surf, desc_rect)
            desc_y += 20 # Line height
        
        # Formatted Stats (Adjust Y based on description length)
        # Ensure stats start below description but reasonably spaced
        y_stat = max(y + offset_y + 250, desc_y + 10)
        font_stats = get_pixel_font(18, bold=True)
        
        for k, v in item_data['effects'].items():
            text, is_positive = self._format_stat(k, v)
            color = COLOR_STAT_POSITIVE if is_positive else COLOR_STAT_NEGATIVE
            
            stat_surf = font_stats.render(text, True, color)
            stat_rect = stat_surf.get_rect(center=(x + width//2, y_stat))
            self.screen.blit(stat_surf, stat_rect)
            y_stat += 25

        # Selection Hint
        if is_selected:
            hint_font = pg.font.SysFont("arial", 16, bold=True)
            hint_surf = hint_font.render("[ ENTER TO SELECT ]", True, (255, 215, 0))
            hint_rect = hint_surf.get_rect(center=(x + width//2, y + offset_y + height - 30))
            self.screen.blit(hint_surf, hint_rect)

    def _format_stat(self, key, value):
        """Convert internal stat keys to readable text"""
        # Dictionary mapping for cleaner names
        LABELS = {
            "attack_power": "Attack",
            "max_hp": "Max HP",
            "movement_speed": "Speed",
            "attack_cooldown": "Atk Cooldown",
            "invincibility_duration": "I-Frames",
            "combo_window": "Combo Time",
            "DASH_SPEED": "Dash Speed",
            "DASH_DURATION": "Dash Time",
            "DASH_COOLDOWN": "Dash CD",
            "SPIN_COOLDOWN": "Spin CD",
            "ARCANE_COOLDOWN": "Arcane CD",
            "GRAVITY_MULT": "Gravity"
        }
        
        label = LABELS.get(key, key.replace("_", " ").title())
        is_positive = True
        
        # Handle logic for display values
        # Multipliers (e.g. 0.85 means -15% cooldown, which is positive for player)
        if key.endswith("_MULT"):
            label = key.replace("_MULT", "").replace("_", " ").title()
            percentage = round((1.0 - value) * 100)
            
            if "COOLDOWN" in key or "GRAVITY" in key:
                # Reduced cooldown/gravity is GOOD
                text = f"{label}: -{percentage}%"
                is_positive = True
            else:
                # Reduced damage/speed is BAD
                text = f"{label}: -{percentage}%"
                is_positive = False
                
        # Handle Flat Values
        else:
            prefix = "+" if value > 0 else ""
            suffix = ""
            
            # Time stats usually in ms
            if "COOLDOWN" in key or "DURATION" in key or "window" in key:
                val_sec = value / 1000.0
                text = f"{label}: {prefix}{val_sec}s"
                
                # Reduced cooldown (negative value) is GOOD
                if "COOLDOWN" in key:
                    is_positive = value < 0
                else:
                    is_positive = value > 0
            else:
                text = f"{label}: {prefix}{value}{suffix}"
                is_positive = value > 0
                
        return text, is_positive
