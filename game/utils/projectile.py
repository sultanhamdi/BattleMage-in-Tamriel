"""Projectile system for enemy range attacks."""

import pygame as pg


class Projectile:
    """Single projectile entity with impact animation support."""
    
    # Default projectile settings
    DEFAULT_HITBOX_SIZE = (20, 12)  # Width x Height for hitbox
    MAX_TRAVEL_DISTANCE = 500       # Maximum pixels before despawn
    MAX_LIFETIME = 300              # Maximum frames alive (5 seconds at 60fps)
    
    def __init__(self, x, y, direction, speed, damage, sprites=None, scale=1.0, 
                 impact_start_frame=None):
        """
        Initialize projectile.
        
        Args:
            x, y: Starting position
            direction: 1 for right, -1 for left
            speed: Movement speed in pixels per frame
            damage: Damage dealt on hit
            sprites: List of animation frames (optional)
            scale: Scale factor for sprites
            impact_start_frame: Frame index where impact animation starts (None = no impact anim)
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
        self.animation_speed = 0.2  # Animation speed
        self.animation_timer = 0
        
        # Impact animation support
        self.impact_start_frame = impact_start_frame  # Frame where impact starts
        self.is_impacting = False  # True when playing impact animation
        self.impact_finished = False  # True when impact anim done
        
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
        self.hit_wall = False
    
    def trigger_impact(self):
        """Trigger impact animation (call when hitting player/wall)."""
        if self.impact_start_frame is not None and not self.is_impacting:
            self.is_impacting = True
            self.current_frame = self.impact_start_frame
            self.speed = 0  # Stop moving
            print(f"[PROJECTILE] Impact triggered at frame {self.impact_start_frame}")
    
    def update(self, platforms=None):
        """Update projectile position and animation."""
        # If impacting, just play impact animation then die
        if self.is_impacting:
            self._update_impact_animation()
            return
        
        # Move
        self.x += self.direction * self.speed
        self.rect.centerx = int(self.x)
        
        # Lifetime counter
        self.lifetime += 1
        
        # Check wall collision (skip first 10 frames to clear spawn area)
        if platforms and self.lifetime > 10:
            self._check_wall_collision(platforms)
        
        # Animate (only non-impact frames)
        if self.sprites and not self.is_impacting:
            self.animation_timer += self.animation_speed
            if self.animation_timer >= 1.0:
                self.animation_timer = 0
                # Loop only through flight frames (before impact)
                max_flight_frame = self.impact_start_frame - 1 if self.impact_start_frame else len(self.sprites) - 1
                next_frame = self.current_frame + 1
                if next_frame > max_flight_frame:
                    next_frame = 0  # Loop back
                self.current_frame = next_frame
                if self.current_frame < len(self.sprites):
                    self.image = self.sprites[self.current_frame]
        
        # Check if exceeded max distance
        distance_traveled = abs(self.x - self.start_x)
        if distance_traveled > self.max_distance:
            # Trigger impact or die
            if self.impact_start_frame:
                self.trigger_impact()
            else:
                self.alive = False
        
        # Check lifetime
        if self.lifetime > self.MAX_LIFETIME:
            self.alive = False
        
        # Bounds check (very generous for large levels)
        if self.x < -200 or self.x > 5000 or self.y < -200 or self.y > 5000:
            self.alive = False
    
    def _update_impact_animation(self):
        """Play impact animation frames then die."""
        self.animation_timer += self.animation_speed
        if self.animation_timer >= 1.0:
            self.animation_timer = 0
            self.current_frame += 1
            
            if self.current_frame >= len(self.sprites):
                # Impact animation done
                self.alive = False
                self.impact_finished = True
            else:
                self.image = self.sprites[self.current_frame]
    
    def _check_wall_collision(self, platforms):
        """Check if projectile hit a wall/tile."""
        # Get front edge of projectile based on direction
        if self.direction > 0:
            front_x = self.rect.right
        else:
            front_x = self.rect.left
        
        # Check collision with any platform
        check_rect = pg.Rect(front_x - 2, self.rect.y, 4, self.rect.height)
        
        for platform in platforms:
            platform_rect = platform.rect if hasattr(platform, 'rect') else platform
            if check_rect.colliderect(platform_rect):
                self.hit_wall = True
                self.trigger_impact()
                break
    
    def check_collision(self, player):
        """Check collision with player."""
        if not self.alive or not player.alive or self.is_impacting:
            return False
        
        # Use physics rect for more accurate collision
        player_rect = player.physics.rect if hasattr(player, 'physics') else player.rect
        
        if self.rect.colliderect(player_rect):
            self.hit_player = True
            self.trigger_impact()
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
                        sprite_path=None, scale=1.5, max_distance=None,
                        impact_start_frame=None):
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
            impact_start_frame: Frame where impact animation starts
        
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
        
        projectile = Projectile(x, y, direction, speed, damage, sprites, scale, 
                                impact_start_frame=impact_start_frame)
        
        # Apply custom max distance if specified
        if max_distance is not None:
            projectile.max_distance = max_distance
        
        self.projectiles.append(projectile)
        return projectile
    
    def update(self, player, platforms=None):
        """
        Update all projectiles and check collisions.
        
        Args:
            player: Player instance for collision checking
            platforms: List of platform tiles for wall collision
        
        Returns:
            Total damage dealt to player this frame
        """
        total_damage = 0
        
        for projectile in self.projectiles[:]:  # Copy list for safe removal
            projectile.update(platforms)
            
            # Check collision with player
            if projectile.check_collision(player):
                total_damage += projectile.damage
            
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

