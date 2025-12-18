# Item Data Definitions
from enum import Enum

class ItemType(Enum):
    ATTACK = "attack"
    DEFENSE = "defense"
    MOBILITY = "mobility"
    COOLDOWN = "cooldown"

# Item Definitions
# Each item has: id, name, type, icon, description, effects (dict of stat modifiers)
# Description is now FLAVOR text, as stats are auto-displayed by the UI.
ITEMS = {
    # ========== ATTACK ITEMS (4) ==========
    "arcane_gauntlet": {
        "name": "Arcane Gauntlet",
        "type": ItemType.ATTACK,
        "icon": "arcane_gauntlet.png",
        "description": "Glove pulsating with raw magic.",
        "effects": {
            "attack_power": 10
        }
    },
    "fury_rune": {
        "name": "Fury Rune",
        "type": ItemType.ATTACK,
        "icon": "fury_rune.png",
        "description": "Anger fuels your spells.",
        "effects": {
            "attack_power": 5,
            "SPIN_COOLDOWN_MULT": 0.9
        }
    },
    "combo_master_tome": {
        "name": "Combo Master Tome",
        "type": ItemType.ATTACK,
        "icon": "combo_master_tome.png",
        "description": "Ancient techniques for fluid combat.",
        "effects": {
            "combo_window": 300
        }
    },
    "swift_blade": {
        "name": "Swift Blade",
        "type": ItemType.ATTACK,
        "icon": "swift_blade.png",
        "description": "Strike faster than the eye can see.",
        "effects": {
            "attack_cooldown": -100
        }
    },

    # ========== DEFENSE ITEMS (3) ==========
    "life_crystal": {
        "name": "Life Crystal",
        "type": ItemType.DEFENSE,
        "icon": "life_crystal.png",
        "description": "Radiates a soothing aura.",
        "effects": {
            "max_hp": 25
        }
    },
    "guardian_amulet": {
        "name": "Guardian Amulet",
        "type": ItemType.DEFENSE,
        "icon": "guardian_amulet.png",
        "description": "Heavy protection at a cost.",
        "effects": {
            "max_hp": 50,
            "movement_speed": -1
        }
    },
    "phase_cloak": {
        "name": "Phase Cloak",
        "type": ItemType.DEFENSE,
        "icon": "phase_cloak.png",
        "description": "Stay in the ethereal plane longer.",
        "effects": {
            "invincibility_duration": 500
        }
    },

    # ========== MOBILITY ITEMS (4) ==========
    "wind_boots": {
        "name": "Wind Boots",
        "type": ItemType.MOBILITY,
        "icon": "wind_boots.png",
        "description": "Walk on air.",
        "effects": {
            "movement_speed": 2
        }
    },
    "dash_enhancer": {
        "name": "Dash Enhancer",
        "type": ItemType.MOBILITY,
        "icon": "dash_enhancer.png",
        "description": "Improved dash mechanics.",
        "effects": {
            "DASH_SPEED": 5,
            "DASH_DURATION": 50
        }
    },
    "flash_step": {
        "name": "Flash Step",
        "type": ItemType.MOBILITY,
        "icon": "flash_step.png",
        "description": "Blink through existence.",
        "effects": {
            "DASH_COOLDOWN": -300
        }
    },
    "featherfall_cape": {
        "name": "Featherfall Cape",
        "type": ItemType.MOBILITY,
        "icon": "featherfall_cape.png",
        "description": "Defy gravity.",
        "effects": {
            "GRAVITY_MULT": 0.85
        }
    },

    # ========== COOLDOWN ITEMS (3) ==========
    "arcane_accelerator": {
        "name": "Arcane Accelerator",
        "type": ItemType.COOLDOWN,
        "icon": "arcane_accelerator.png",
        "description": "Channel magic faster.",
        "effects": {
            "ARCANE_COOLDOWN": -500
        }
    },
    "whirlwind_catalyst": {
        "name": "Whirlwind Catalyst",
        "type": ItemType.COOLDOWN,
        "icon": "whirlwind_catalyst.png",
        "description": "Keep spinning.",
        "effects": {
            "SPIN_COOLDOWN": -400
        }
    },
    "chrono_shard": {
        "name": "Chrono Shard",
        "type": ItemType.COOLDOWN,
        "icon": "chrono_shard.png",
        "description": "Time bends around you.",
        "effects": {
            "DASH_COOLDOWN_MULT": 0.85,
            "SPIN_COOLDOWN_MULT": 0.85,
            "ARCANE_COOLDOWN_MULT": 0.85
        }
    },
}

def get_item(item_id):
    # get item data by id
    return ITEMS.get(item_id)

def get_all_item_ids():
    # get all item ids
    return list(ITEMS.keys())
