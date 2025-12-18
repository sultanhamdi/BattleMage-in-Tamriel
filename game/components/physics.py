import pygame as pg

# physics constants
GRAVITY = 0.8
JUMP_STRENGTH = -22 
TERMINAL_VELOCITY = 15

class PhysicsComponent:
    def __init__(self, rect):
        self.rect = rect
        self.velocity = pg.Vector2(0, 0)
        self.on_ground = False
        self.facing_right = True
        
        # float position for accurate movement
        self.pos = pg.Vector2(rect.x, rect.y)

    def apply_gravity(self):
        self.velocity.y += GRAVITY
        if self.velocity.y > TERMINAL_VELOCITY:
            self.velocity.y = TERMINAL_VELOCITY

    def move_and_collide(self, platforms, x_velocity):
        # store old position
        old_x = self.rect.x
        old_y = self.rect.y
        
        # 1. Gerakan Horizontal
        self.pos.x += x_velocity
        self.rect.x = round(self.pos.x) # Update rect visual dari posisi float
        
        # prevent glitch teleports
        MAX_DELTA = 200
        delta_x = self.rect.x - old_x
        if abs(delta_x) > MAX_DELTA:
            # Revert to safe position
            self.rect.x = old_x
            self.pos.x = float(old_x)
        
        # update facing direction
        if x_velocity > 0:
            self.facing_right = True
        elif x_velocity < 0:
            self.facing_right = False

        for platform in platforms:
            if self.rect.colliderect(platform):
                if x_velocity > 0: # Ke Kanan
                    self.rect.right = platform.left
                if x_velocity < 0: # Ke Kiri
                    self.rect.left = platform.right
                # sync float position
                self.pos.x = self.rect.x
        
        # 2. Gerakan Vertikal
        self.on_ground = False 
        self.pos.y += self.velocity.y
        self.rect.y = round(self.pos.y) # Update rect visual dari posisi float
        
        # clamp y delta
        delta_y = self.rect.y - old_y
        if abs(delta_y) > MAX_DELTA:
            self.rect.y = old_y
            self.pos.y = float(old_y)
            self.velocity.y = 0

        for platform in platforms:
            if self.rect.colliderect(platform):
                if self.velocity.y > 0: # Jatuh ke lantai
                    self.rect.bottom = platform.top
                    self.velocity.y = 0
                    self.on_ground = True
                if self.velocity.y < 0: # Mentok atap
                    self.rect.top = platform.bottom
                    self.velocity.y = 0
                
                # sync float position after collision
                self.pos.y = self.rect.y

    def jump(self):
        if self.on_ground:
            self.velocity.y = JUMP_STRENGTH
            self.on_ground = False

    def update(self, platforms, x_velocity, apply_gravity=True):
        if apply_gravity:
            self.apply_gravity()
        self.move_and_collide(platforms, x_velocity)