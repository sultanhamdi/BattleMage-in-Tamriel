import pygame as pg

class Camera:
    def __init__(self, width, height):
        self.display_width = width
        self.display_height = height
        self.offset = pg.Vector2(0, 0)

    def follow(self, target_rect):
        """
        Mengupdate offset agar target (Player) selalu berada di tengah layar.
        """
        self.offset.x = target_rect.centerx - self.display_width // 2
        self.offset.y = target_rect.centery - self.display_height // 2