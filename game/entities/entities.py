import pygame as pg
from game.components.physics import PhysicsComponent

class Entity(pg.sprite.Sprite):
    def __init__(self, x, y, width, height, max_hp, attack_power, speed):
        super().__init__()
        
        # rect & physics
        self.rect = pg.Rect(x, y, width, height)
        self.physics = PhysicsComponent(self.rect)
        
        # stats
        self.max_hp = max_hp
        self.current_hp = max_hp
        self.attack_power = attack_power
        self.movement_speed = speed 
        self.alive = True
        
        # state
        self.state = 'idle' 
        self.facing_right = True 
        
        # combat mechanics
        self.is_attacking = False
        self.attack_cooldown = 500 # ms
        self.last_attack_time = 0
        
        self.is_invincible = False
        self.invincibility_duration = 300 # ms 
        self.last_hit_time = 0

    def update_timers(self):
        current_time = pg.time.get_ticks()
        
        # Invincible
        if self.is_invincible:
            if current_time - self.last_hit_time > self.invincibility_duration:
                self.is_invincible = False

        # attack cooldown
        if self.is_attacking:
            if current_time - self.last_attack_time > 400: 
                self.is_attacking = False
                if self.alive:
                    self.state = 'idle'

    def take_damage(self, amount):
        if not self.alive or self.is_invincible:
            return

        self.current_hp -= amount
        self.is_invincible = True
        self.last_hit_time = pg.time.get_ticks()
        self.state = 'hurt' 
        
        print(f"[COMBAT] {type(self).__name__} took {amount} dmg. HP: {self.current_hp}/{self.max_hp}")

        if self.current_hp <= 0:
            self.die()

    def attack(self):
        current_time = pg.time.get_ticks()
        
        if not self.is_attacking and self.alive:
            if current_time - self.last_attack_time > self.attack_cooldown:
                self.is_attacking = True
                self.state = 'attack1'
                self.last_attack_time = current_time
                print(f"[ACTION] {type(self).__name__} Attacks!")
                return True
        return False

    def die(self):
        self.alive = False
        self.current_hp = 0
        self.state = 'death'
        print(f"[DEATH] {type(self).__name__} has died.")

    def update(self, platforms):
        self.update_timers()