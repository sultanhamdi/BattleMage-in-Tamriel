import pygame as pg

class Camera:
    def __init__(self, width, height):
        self.display_width = width
        self.display_height = height
        self.world_width = width
        self.world_height = height
        self.offset = pg.Vector2(0, 0)
        
    def set_world_size(self, width, height):
        self.world_width = width
        self.world_height = height

    def follow(self, target_rect):
        # update offset to keep target centered
        self.offset.x = target_rect.centerx - self.display_width // 2
        self.offset.y = target_rect.centery - self.display_height // 2
        
        # clamp x
        self.offset.x = max(0, self.offset.x) 
        self.offset.x = min(self.offset.x, self.world_width - self.display_width)
        
        # Clamp Y
        self.offset.y = max(0, self.offset.y)
        self.offset.y = min(self.offset.y, self.world_height - self.display_height)