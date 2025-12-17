"""
Projectile System untuk enemy range attacks.

Projectile adalah entity sederhana yang:
1. Bergerak lurus ke arah tertentu
2. Mengecek collision dengan player
3. Menghilang setelah keluar screen atau hit player
"""

import pygame as pg


class Projectile:
    """Single projectile entity."""
    
    # Default projectile settings
    DEFAULT_HITBOX_SIZE = (20, 12)  # Width x Height for hitbox
    MAX_TRAVEL_DISTANCE = 500       # Maximum pixels before despawn
    MAX_LIFETIME = 300              # Maximum frames alive (5 seconds at 60fps)
    
    def __init__(self, x, y, direction, speed, damage, sprites=None, scale=1.0):
        """
        Initialize projectile.
        
        Args:
            x, y: Starting position
            direction: 1 for right, -1 for left
            speed: Movement speed in pixels per frame
            damage: Damage dealt on hit
            sprites: List of animation frames (optional)
            scale: Scale factor for sprites
        """
        self.start_x = float(x)
        self.start_y = float(y)
        self.x = float(x)
        self.y = float(y)
        self.direction = direction
        self.speed = speed
        self.damage = damage
        self.scale = scale
        
        # Animation
        self.sprites = sprites or []
        self.current_frame = 0
        self.animation_speed = 0.2  # Faster animation
        self.animation_timer = 0
        
        # Lifetime tracking
        self.lifetime = 0
        self.max_distance = self.MAX_TRAVEL_DISTANCE
        
        # Create rect for collision
        if self.sprites:
            self.image = self.sprites[0]
            # Use sprite size for hitbox
            self.rect = self.image.get_rect(center=(int(x), int(y)))
        else:
            # Default hitbox if no sprites
            hitbox_w, hitbox_h = self.DEFAULT_HITBOX_SIZE
            self.rect = pg.Rect(int(x) - hitbox_w // 2, int(y) - hitbox_h // 2, 
                               hitbox_w, hitbox_h)
            self.image = None
        
        self.alive = True
        self.hit_player = False
    
    def update(self):
        """Update projectile position and animation."""
        # Move
        self.x += self.direction * self.speed
        self.rect.centerx = int(self.x)
        
        # Lifetime counter
        self.lifetime += 1
        
        # Animate
        if self.sprites:
            self.animation_timer += self.animation_speed
            if self.animation_timer >= 1.0:
                self.animation_timer = 0
                self.current_frame = (self.current_frame + 1) % len(self.sprites)
                self.image = self.sprites[self.current_frame]
        
        # Check if exceeded max distance
        distance_traveled = abs(self.x - self.start_x)
        if distance_traveled > self.max_distance:
            self.alive = False
        
        # Check lifetime
        if self.lifetime > self.MAX_LIFETIME:
            self.alive = False
        
        # Bounds check (very generous for large levels)
        if self.x < -200 or self.x > 5000 or self.y < -200 or self.y > 5000:
            self.alive = False
    
    def check_collision(self, player):
        """Check collision with player."""
        if not self.alive or not player.alive:
            return False
        
        # Use physics rect for more accurate collision
        player_rect = player.physics.rect if hasattr(player, 'physics') else player.rect
        
        if self.rect.colliderect(player_rect):
            self.hit_player = True
            self.alive = False
            return True
        return False
    
    def draw(self, surface, camera_offset):
        """Draw projectile."""
        draw_x = self.rect.x - camera_offset.x
        draw_y = self.rect.y - camera_offset.y
        
        if self.image:
            # Flip if going left
            img = self.image
            if self.direction < 0:
                img = pg.transform.flip(img, True, False)
            surface.blit(img, (draw_x, draw_y))
        else:
            # Fallback: draw a glowing orb
            center_x = draw_x + self.rect.width // 2
            center_y = draw_y + self.rect.height // 2
            # Outer glow
            pg.draw.circle(surface, (255, 150, 100), (center_x, center_y), 10)
            # Inner bright
            pg.draw.circle(surface, (255, 220, 180), (center_x, center_y), 6)


class ProjectileManager:
    """Manages all projectiles in the game."""
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.projectiles = []
            cls._instance.sprite_cache = {}
        return cls._instance
    
    @classmethod
    def get_instance(cls):
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def clear(self):
        """Clear all projectiles (call on level change)."""
        self.projectiles = []
    
    def spawn_projectile(self, x, y, direction, speed=8, damage=10, 
                        sprite_path=None, scale=1.5, max_distance=None):
        """
        Spawn a new projectile.
        
        Args:
            x, y: Starting position
            direction: 1 for right, -1 for left
            speed: Movement speed (pixels per frame)
            damage: Damage on hit
            sprite_path: Path to projectile sprite folder
            scale: Sprite scale factor
            max_distance: Max travel distance before despawn (None = default)
        
        Returns:
            The created Projectile instance
        """
        sprites = []
        
        # Try to load sprites
        if sprite_path and sprite_path not in self.sprite_cache:
            try:
                import os
                if os.path.isdir(sprite_path):
                    files = sorted([f for f in os.listdir(sprite_path) 
                                   if f.endswith('.png')])
                    for filename in files:
                        img = pg.image.load(os.path.join(sprite_path, filename)).convert_alpha()
                        if scale != 1.0:
                            new_size = (int(img.get_width() * scale), 
                                       int(img.get_height() * scale))
                            img = pg.transform.scale(img, new_size)
                        sprites.append(img)
                    if sprites:
                        self.sprite_cache[sprite_path] = sprites
            except Exception as e:
                print(f"[PROJECTILE] Failed to load sprites from {sprite_path}: {e}")
        
        if sprite_path and sprite_path in self.sprite_cache:
            sprites = self.sprite_cache[sprite_path]
        
        projectile = Projectile(x, y, direction, speed, damage, sprites, scale)
        
        # Apply custom max distance if specified
        if max_distance is not None:
            projectile.max_distance = max_distance
        
        self.projectiles.append(projectile)
        return projectile
    
    def update(self, player):
        """
        Update all projectiles and check collisions.
        
        Args:
            player: Player instance for collision checking
        
        Returns:
            Total damage dealt to player this frame
        """
        total_damage = 0
        
        for projectile in self.projectiles[:]:  # Copy list for safe removal
            projectile.update()
            
            # Check collision with player
            if projectile.check_collision(player):
                total_damage += projectile.damage
                print(f"[PROJECTILE] Hit player for {projectile.damage} damage!")
            
            # Remove dead projectiles
            if not projectile.alive:
                self.projectiles.remove(projectile)
        
        return total_damage
    
    def draw(self, surface, camera_offset):
        """Draw all projectiles."""
        for projectile in self.projectiles:
            projectile.draw(surface, camera_offset)
    
    @property
    def count(self):
        """Number of active projectiles."""
        return len(self.projectiles)
