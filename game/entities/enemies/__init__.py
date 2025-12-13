# game/entities/enemies/__init__.py
"""
Package untuk semua Enemy classes.

HIERARKI INHERITANCE:
Entity (Parent)
└── BaseEnemy (Base class untuk enemy)
    ├── Zombie (Melee, Lambat, Patrol)
    ├── Golem (Tank, HP Tebal, Appear Animation)
    └── Vampire (Flying, Cepat, Lifesteal)

USAGE:
    from game.entities.enemies import Zombie, Golem, Vampire
    
    # Spawn enemy
    zombie = Zombie(x=200, y=300)
    golem = Golem(x=400, y=300)
    vampire = Vampire(x=600, y=200)
    
    # Set player reference untuk AI
    zombie.set_player_reference(player)
"""

from game.entities.enemies.base_enemy import BaseEnemy
from game.entities.enemies.zombie import Zombie
from game.entities.enemies.golem import Golem
from game.entities.enemies.vampire import Vampire

__all__ = ['BaseEnemy', 'Zombie', 'Golem', 'Vampire']
