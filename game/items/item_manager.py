# Item Manager - Handles item pool and selection
import random
from game.items.item_data import ITEMS, get_all_item_ids

class ItemManager:
    def __init__(self):
        # Pool of available items (items not yet picked by player)
        self.available_pool = get_all_item_ids().copy()
        
        # Items the player has collected
        self.collected_items = []
        
    def reset(self):
        """Reset pool to full (for new game)"""
        self.available_pool = get_all_item_ids().copy()
        self.collected_items = []
        
    def get_random_choices(self, count=2):
        """
        Get random items from pool for player to choose from.
        Returns list of item IDs.
        """
        if len(self.available_pool) < count:
            # Not enough items left, return what's available
            return self.available_pool.copy()
        
        return random.sample(self.available_pool, count)
    
    def pick_item(self, item_id):
        """
        Player picks an item. Remove from pool and add to collected.
        Returns the item data or None if invalid.
        """
        if item_id not in self.available_pool:
            print(f"[ERROR] Item '{item_id}' not in pool!")
            return None
        
        # Remove from pool
        self.available_pool.remove(item_id)
        
        # Add to collected
        self.collected_items.append(item_id)
        
        item_data = ITEMS.get(item_id)
        print(f"[ITEM] Player picked: {item_data['name']}")
        
        return item_data
    
    def apply_item_to_player(self, player, item_id):
        """
        Apply item effects to player stats.
        Handles both flat bonuses and multipliers.
        """
        item_data = ITEMS.get(item_id)
        if not item_data:
            return False
        
        effects = item_data.get("effects", {})
        
        for stat, value in effects.items():
            # Handle multipliers (ends with _MULT)
            if stat.endswith("_MULT"):
                base_stat = stat.replace("_MULT", "")
                if hasattr(player, base_stat):
                    current = getattr(player, base_stat)
                    new_value = int(current * value)
                    setattr(player, base_stat, new_value)
                    print(f"  {base_stat}: {current} -> {new_value} (x{value})")
                    
            # Handle flat bonuses
            else:
                if hasattr(player, stat):
                    current = getattr(player, stat)
                    new_value = current + value
                    setattr(player, stat, new_value)
                    print(f"  {stat}: {current} -> {new_value} ({'+' if value >= 0 else ''}{value})")
                    
                    # Special case: if max_hp increased, also heal
                    if stat == "max_hp" and value > 0:
                        player.current_hp = min(player.current_hp + value, player.max_hp)
                        
                # Check physics component for gravity
                elif stat == "GRAVITY_MULT" and hasattr(player, 'physics'):
                    if hasattr(player.physics, 'gravity'):
                        current = player.physics.gravity
                        new_value = current * value
                        player.physics.gravity = new_value
                        print(f"  gravity: {current} -> {new_value} (x{value})")
        
        return True
    
    def get_pool_size(self):
        """Get remaining items in pool"""
        return len(self.available_pool)
    
    def get_collected_count(self):
        """Get number of items player has collected"""
        return len(self.collected_items)
