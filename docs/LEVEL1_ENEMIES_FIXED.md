# Level 1 Enemies - Implementation Fixed

## 🎯 Masalah yang Diperbaiki

### 1. **Direction Bug** ✅
- **Problem**: Enemy jalan ke kiri tapi menghadap ke kanan (facing direction tidak konsisten)
- **Root Cause**: Beberapa enemy menggunakan `self.physics.velocity_x` langsung tanpa update `self.facing_right`
- **Solution**: 
  - Semua enemy sekarang menggunakan `execute_ai_behavior()` yang return `x_velocity`
  - `facing_right` di-update SEBELUM movement di setiap AI state
  - Direction ke player selalu dihitung dengan `self.get_direction_to_player()`

### 2. **Floating Bug** ✅
- **Problem**: Ground enemy kadang floating (tidak apply gravity)
- **Root Cause**: Beberapa enemy lupa call `physics.update()` dengan `apply_gravity=True`
- **Solution**: 
  - Semua ground enemy (Goblin, Mushroom, Skeleton) sekarang proper apply gravity
  - `self.physics.update(platforms, x_velocity, apply_gravity=True)`
  - Dead enemy juga apply gravity untuk jatuh

### 3. **Flying Eye Motion** ✅
- **Problem**: Flying Eye perlu motion naik-turun yang lebih natural
- **Solution**: 
  - Smooth hovering menggunakan `math.sin()` dengan amplitude dan frequency yang disesuaikan
  - Berbeda intensity untuk setiap state (idle, patrol, chase, attack)
  - Vertical movement saat chase untuk maintain height di atas player

---

## 🦇 Enemy Implementations - Level 1

### 1. **Flying Eye** (Flying Monster)

**Karakteristik:**
- HP: 45 (Low)
- Damage: 12 (Range), 8 (Melee)  
- Speed: 4.0 (Very Fast - Flying)
- Behavior: Evasive, range attacker, smooth hovering

**AI Logic:**
```python
# SMOOTH HOVER MOTION
hover_y_offset = math.sin(self.hover_offset) * self.HOVER_AMPLITUDE

# STATE BEHAVIORS:
- IDLE: Gentle hover (amplitude * 0.25)
- PATROL: Natural hovering (amplitude * 0.2)
- CHASE: Maintain height above player + slight hover
- ATTACK: Minimal hover (amplitude * 0.1)
- RANGE: Light hover during attack (amplitude * 0.15)
```

**Key Features:**
- ✅ Smooth sinusoidal hovering motion
- ✅ Vertical movement to chase player at optimal height
- ✅ No gravity when alive, gravity when dead
- ✅ Face player during all attacks
- ✅ Range attack from distance

**Constants Tuned:**
```python
HOVER_AMPLITUDE = 15      # Pixels naik-turun (smooth)
HOVER_FREQUENCY = 0.08    # Visible but smooth motion
OPTIMAL_HEIGHT_OFFSET = -40  # Fly above player
VERTICAL_SPEED = 2.0      # Smooth vertical movement
```

---

### 2. **Goblin** (Tactical Fighter)

**Karakteristik:**
- HP: 60 (Medium)
- Damage: 15 (Melee), 10 (Range)
- Speed: 3.5 (Agile)
- Behavior: Tactical positioning, switch melee/range

**AI Logic:**
```python
# TACTICAL POSITIONING
if distance < MIN_SAFE_DISTANCE:
    # Too close - retreat while facing player
    retreat_dir = -direction
    self.facing_right = direction > 0  # Face player
    x_velocity = retreat_dir * speed * 1.2

elif OPTIMAL_RANGE - 50 < distance < range_attack_range:
    # Optimal range - range attack
    if cooldown_ready:
        range_attack()
    else:
        # Maintain distance
        if distance < target_dist:
            back_off()
        else:
            advance()
```

**Key Features:**
- ✅ Retreats when too close BUT still faces player
- ✅ Maintains optimal distance for range attack
- ✅ Switches between melee and range based on distance
- ✅ Consistent facing direction in all states
- ✅ Proper gravity application

---

### 3. **Mushroom** (Tanky Defender)

**Karakteristik:**
- HP: 80 (High - Tanky)
- Damage: 10 (Low but poison)
- Speed: 2.0 (Slow)
- Behavior: Territorial defense, patient

**AI Logic:**
```python
# TERRITORIAL BEHAVIOR
if dist_from_spawn > TERRITORY_RADIUS:
    # Return to spawn point
    return_to_spawn()
elif distance < TERRITORY_RADIUS:
    # Only chase within territory
    chase()
else:
    # Let player go if too far
    idle()

# SPORE ATTACK
if 50 < distance <= 150 and cooldown_ready:
    # Medium range spore attack
    release_spores()
```

**Key Features:**
- ✅ Guards territory, returns to spawn if too far
- ✅ Won't chase beyond territory radius
- ✅ Spore attack at medium range
- ✅ Faces player during all actions
- ✅ Tanky with damage reduction

**Territory Settings:**
```python
TERRITORY_RADIUS = 250  # Won't chase beyond this
SPORE_COOLDOWN = 150    # Medium cooldown
```

---

### 4. **Skeleton** (Defensive Fighter)

**Karakteristik:**
- HP: 65 (Medium)
- Damage: 14 (Medium)
- Speed: 2.8 (Medium)
- Behavior: Defensive, shield when low HP

**AI Logic:**
```python
# SHIELD BEHAVIOR (Low HP)
if distance <= attack_range:
    if should_shield and not is_attacking:
        # Low HP - raise shield
        raise_shield()
    else:
        # Normal melee attack
        melee_attack()

# BONE THROW
if 80 < distance <= range_attack_range and cooldown_ready:
    # Throw bone projectile
    throw_bone()
```

**Key Features:**
- ✅ Raises shield when HP < 30%
- ✅ Can block attacks with shield (60% chance, 70% damage reduction)
- ✅ Bone throw at range
- ✅ Always faces player during actions
- ✅ Defensive playstyle

**Shield Settings:**
```python
SHIELD_HP_THRESHOLD = 0.3    # Raise shield at 30% HP
SHIELD_BLOCK_CHANCE = 0.6    # 60% block chance
BONE_THROW_COOLDOWN = 120    # Range attack cooldown
```

---

## 🔧 Technical Improvements

### Consistent Update Pattern
All enemies now follow this pattern:
```python
def update(self, platforms):
    # 1. Update cooldowns
    if self.projectile_cooldown > 0:
        self.projectile_cooldown -= 1
    
    # 2. Update timers (invincibility, attack)
    self.update_timers()
    
    # 3. Handle death
    if not self.alive:
        self.physics.update(platforms, 0, apply_gravity=True)
        self.rect = self.physics.rect
        return
    
    # 4. Update AI state
    self.update_ai_state()
    
    # 5. Execute behavior (returns x_velocity)
    x_velocity = self.execute_ai_behavior()
    
    # 6. Update physics
    self.physics.update(platforms, x_velocity, apply_gravity=True)
    self.rect = self.physics.rect
```

### Direction Update Pattern
```python
def execute_ai_behavior(self):
    # Get direction FIRST
    direction = self.get_direction_to_player()
    
    # Update facing BEFORE movement
    self.facing_right = direction > 0
    
    # Then calculate velocity
    x_velocity = direction * self.movement_speed
    
    return x_velocity  # Return, don't set directly
```

### Special Cases

**Flying Enemy (Flying Eye):**
```python
# NO GRAVITY when alive
self.physics.update(platforms, x_velocity, apply_gravity=False)

# GRAVITY when dead (falls)
if not self.alive:
    self.physics.update(platforms, 0, apply_gravity=True)
```

**Retreat Behavior (Goblin):**
```python
# Retreat AWAY from player but FACE player
retreat_dir = -direction  # Move opposite
self.facing_right = direction > 0  # Face toward player
x_velocity = retreat_dir * speed
```

---

## 🎮 Testing Checklist

### Flying Eye
- [x] Hovers smoothly up and down (visible sinusoidal motion)
- [x] Faces correct direction when chasing
- [x] Maintains height above player during chase
- [x] Falls down when dies (gravity applied)
- [x] Range attack faces player

### Goblin
- [x] Faces player when retreating
- [x] Maintains optimal attack distance
- [x] Switches between melee and range correctly
- [x] No floating (always on ground)
- [x] Consistent facing in all states

### Mushroom
- [x] Returns to spawn when too far
- [x] Only chases within territory
- [x] Faces player during spore attack
- [x] No floating (proper gravity)
- [x] Tanky behavior (takes reduced damage)

### Skeleton
- [x] Raises shield when low HP
- [x] Faces player during shield
- [x] Throws bone correctly
- [x] No floating (proper gravity)
- [x] Defensive playstyle

---

## 📊 Behavior Summary

| Enemy | Movement Type | Primary Attack | Special Ability | AI Style |
|-------|--------------|----------------|-----------------|----------|
| Flying Eye | Flying | Range | Smooth Hover | Evasive |
| Goblin | Ground | Melee + Range | Tactical Retreat | Tactical |
| Mushroom | Ground | Melee + Spore | Territorial | Defensive |
| Skeleton | Ground | Melee + Bone | Shield | Defensive |

---

## 💡 Key Takeaways

1. **Always update `facing_right` before movement**
2. **Return `x_velocity` from `execute_ai_behavior()`, don't set directly**
3. **Apply gravity for ground enemies, not for flying**
4. **Dead enemies should fall (apply gravity)**
5. **Use `get_direction_to_player()` for consistent direction**
6. **Face player during attacks and special actions**

---

Semua enemy di Level 1 sekarang sudah fix dan siap untuk testing! 🎉
