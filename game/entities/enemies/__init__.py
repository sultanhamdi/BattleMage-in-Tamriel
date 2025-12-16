# game/entities/enemies/__init__.py
"""
Package untuk semua Enemy classes.

HIERARKI INHERITANCE:
Entity (Parent)
└── BaseEnemy (Base class untuk enemy)
    ├── DUNGEON MONSTERS (Boss-tier, high difficulty)
    │   ├── DemonSlime (Boss, Tank, Area Attack)
    │   ├── BringerOfDeath (Boss, Caster, Melee+Spell)
    │   └── Skullwolf (Fast Melee, Pack Hunter)
    │
    ├── GRASS MONSTERS (Mid-tier, versatile)
    │   ├── FlyingEye (Flying, Range Attack)
    │   ├── Goblin (Melee+Range, Versatile)
    │   ├── Mushroom (Stationary, Range Spam)
    │   └── Skeleton (Melee+Range, Shield Defense)
    │
    └── ICE MONSTERS (Tank-tier, high defense)
        ├── Golem (Tank, Slow, High HP)
        └── Guardian (Elite, Balanced Stats)

USAGE:
    from game.entities.enemies import DemonSlime, Golem, FlyingEye
    
    # Spawn enemies
    demon = DemonSlime(x=200, y=300)
    golem = Golem(x=400, y=300)
    flying_eye = FlyingEye(x=600, y=200)
    
    # Set player reference untuk AI
    demon.set_player_reference(player)
"""

from game.entities.enemies.enemy import BaseEnemy

# Dungeon Monsters (Boss Tier)
from game.entities.enemies.demon_slime import DemonSlime
from game.entities.enemies.bringer_of_death import BringerOfDeath
from game.entities.enemies.skullwolf import Skullwolf

# Grass Monsters (Mid Tier)
from game.entities.enemies.flying_eye import FlyingEye
from game.entities.enemies.goblin import Goblin
from game.entities.enemies.mushroom import Mushroom
from game.entities.enemies.skeleton import Skeleton

# Ice Monsters (Tank Tier)
from game.entities.enemies.golem import Golem
from game.entities.enemies.guardian import Guardian

__all__ = [
    'BaseEnemy',
    # Dungeon Monsters
    'DemonSlime',
    'BringerOfDeath',
    'Skullwolf',
    # Grass Monsters
    'FlyingEye',
    'Goblin',
    'Mushroom',
    'Skeleton',
    # Ice Monsters
    'Golem',
    'Guardian',
]
