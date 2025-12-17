
import pygame as pg
import os
import sys

# Setup path
sys.path.append(os.getcwd())
from game.utils.enemy_animation_handler import EnemyAnimationHandler

pg.init()
pg.display.set_mode((100, 100))

print("--- VERIFYING DEMON SLIME ASSETS ---")
path = 'assets/graphics/enemies/dungeon_monster/boss_demon_slime/'
handler = EnemyAnimationHandler(path, scale=1)
mapping = {
    'attack': 'attack', 
    'idle': 'idle'
}

handler.load_sprites(mapping)

print(f"Path: {path}")
print(f"Animations: {handler.animations.keys()}")
if 'attack' in handler.animations:
    print(f"Attack Frames: {len(handler.animations['attack'])}")
else:
    print("Attack animation NOT FOUND")

print("--- END VERIFICATION ---")
