# Item Data Definitions
from enum import Enum

class ItemType(Enum):
    ATTACK = "attack"
    DEFENSE = "defense"
    MOBILITY = "mobility"
    COOLDOWN = "cooldown"

# Item Definitions
# Each item has: id, name, type, icon, description, effects (dict of stat modifiers)
ITEMS = {
    # ========== ATTACK ITEMS (4) ==========
    "arcane_gauntlet": {
        "name": "Arcane Gauntlet",
        "type": ItemType.ATTACK,
        "icon": "arcane_gauntlet.png",
        "description": "+10 Attack Power",
        "effects": {
            "attack_power": 10  # Flat bonus
        }
    },
    "fury_rune": {
        "name": "Fury Rune",
        "type": ItemType.ATTACK,
        "icon": "fury_rune.png",
        "description": "+5 Attack, -10% Spin Cooldown",
        "effects": {
            "attack_power": 5,
            "SPIN_COOLDOWN_MULT": 0.9  # Multiplier (90% = -10%)
        }
    },
    "combo_master_tome": {
        "name": "Combo Master Tome",
        "type": ItemType.ATTACK,
        "icon": "combo_master_tome.png",
        "description": "+300ms Combo Window",
        "effects": {
            "combo_window": 300  # Flat bonus in ms
        }
    },
    "swift_blade": {
        "name": "Swift Blade",
        "type": ItemType.ATTACK,
        "icon": "swift_blade.png",
        "description": "-100ms Attack Cooldown",
        "effects": {
            "attack_cooldown": -100  # Flat reduction in ms
        }
    },

    # ========== DEFENSE ITEMS (3) ==========
    "life_crystal": {
        "name": "Life Crystal",
        "type": ItemType.DEFENSE,
        "icon": "life_crystal.png",
        "description": "+25 Max HP",
        "effects": {
            "max_hp": 25  # Flat bonus
        }
    },
    "guardian_amulet": {
        "name": "Guardian Amulet",
        "type": ItemType.DEFENSE,
        "icon": "guardian_amulet.png",
        "description": "+50 Max HP, -1 Speed",
        "effects": {
            "max_hp": 50,
            "movement_speed": -1
        }
    },
    "phase_cloak": {
        "name": "Phase Cloak",
        "type": ItemType.DEFENSE,
        "icon": "phase_cloak.png",
        "description": "+500ms Invincibility Duration",
        "effects": {
            "invincibility_duration": 500  # Flat bonus in ms
        }
    },

    # ========== MOBILITY ITEMS (4) ==========
    "wind_boots": {
        "name": "Wind Boots",
        "type": ItemType.MOBILITY,
        "icon": "wind_boots.png",
        "description": "+2 Movement Speed",
        "effects": {
            "movement_speed": 2  # Flat bonus
        }
    },
    "dash_enhancer": {
        "name": "Dash Enhancer",
        "type": ItemType.MOBILITY,
        "icon": "dash_enhancer.png",
        "description": "+5 Dash Speed, +50ms Dash Duration",
        "effects": {
            "DASH_SPEED": 5,
            "DASH_DURATION": 50
        }
    },
    "flash_step": {
        "name": "Flash Step",
        "type": ItemType.MOBILITY,
        "icon": "flash_step.png",
        "description": "-300ms Dash Cooldown",
        "effects": {
            "DASH_COOLDOWN": -300  # Flat reduction
        }
    },
    "featherfall_cape": {
        "name": "Featherfall Cape",
        "type": ItemType.MOBILITY,
        "icon": "featherfall_cape.png",
        "description": "-15% Gravity",
        "effects": {
            "GRAVITY_MULT": 0.85  # Multiplier
        }
    },

    # ========== COOLDOWN ITEMS (3) ==========
    "arcane_accelerator": {
        "name": "Arcane Accelerator",
        "type": ItemType.COOLDOWN,
        "icon": "arcane_accelerator.png",
        "description": "-500ms Arcane Cooldown",
        "effects": {
            "ARCANE_COOLDOWN": -500  # Flat reduction
        }
    },
    "whirlwind_catalyst": {
        "name": "Whirlwind Catalyst",
        "type": ItemType.COOLDOWN,
        "icon": "whirlwind_catalyst.png",
        "description": "-400ms Spin Cooldown",
        "effects": {
            "SPIN_COOLDOWN": -400  # Flat reduction
        }
    },
    "chrono_shard": {
        "name": "Chrono Shard",
        "type": ItemType.COOLDOWN,
        "icon": "chrono_shard.png",
        "description": "-15% ALL Cooldowns",
        "effects": {
            "DASH_COOLDOWN_MULT": 0.85,
            "SPIN_COOLDOWN_MULT": 0.85,
            "ARCANE_COOLDOWN_MULT": 0.85
        }
    },
}

def get_item(item_id):
    """Get item data by ID"""
    return ITEMS.get(item_id)

def get_all_item_ids():
    """Get list of all item IDs"""
    return list(ITEMS.keys())
