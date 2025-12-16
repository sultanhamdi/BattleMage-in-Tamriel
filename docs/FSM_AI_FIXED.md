# FSM & AI Logic - Fixed Implementation

## 🎯 Masalah yang Diperbaiki

### 1. **State Management Confusion**
**Problem:** Ada konflik antara `self.state` (animasi) dan `self.ai_state` (AI logic)
- Base class menggunakan `self.state` untuk animasi
- Child class menggunakan `self.ai_state` untuk AI state machine
- Tidak sinkron antara keduanya

**Solution:**
- `self.ai_state` = AI logic state (idle, patrol, chase, attack, dll)
- `self.state` = Animation state (idle, walk, chase, attack, range, shield, dll)
- **KRUSIAL:** Set `self.state` di dalam `execute_ai_behavior()` untuk setiap AI state

### 2. **Duplicate Logic di Flying Eye**
**Problem:** Hover logic duplikat di update() dan execute_ai_behavior()

**Solution:** Hover motion sepenuhnya di dalam `execute_ai_behavior()`

### 3. **Animation State Not Set**
**Problem:** Child class tidak set `self.state`, menyebabkan animasi tidak jalan

**Solution:** Setiap AI state transition harus set `self.state` yang sesuai

---

## 🔄 State Management - Fixed Pattern

### Base FSM Structure:
```python
# Base Enemy (enemy.py)
STATE_IDLE = 'idle'
STATE_PATROL = 'patrol'
STATE_CHASE = 'chase'
STATE_ATTACK = 'attack'
STATE_HURT = 'hurt'
STATE_DIE = 'die'

# Update loop
def update(platforms):
    update_timers()
    update_ai_state()          # Update AI state machine
    x_velocity = execute_ai_behavior()  # Get velocity from AI
    physics.update(...)
```

### Child FSM Implementation:
```python
def execute_ai_behavior(self):
    # For EACH AI state, set BOTH:
    # 1. self.ai_state (AI logic)
    # 2. self.state (animation)
    
    if condition_idle:
        self.ai_state = self.STATE_IDLE
        self.state = 'idle'  # ← MUST SET
        x_velocity = 0
    
    elif condition_patrol:
        self.ai_state = self.STATE_PATROL
        self.state = 'walk'  # ← MUST SET
        x_velocity = self.do_patrol()
    
    elif condition_chase:
        self.ai_state = self.STATE_CHASE
        self.state = 'chase'  # ← MUST SET
        x_velocity = direction * speed
    
    elif condition_attack:
        self.ai_state = self.STATE_ATTACK
        self.do_attack()  # Sets self.state = 'attack'
        x_velocity = 0
    
    return x_velocity
```

---

## 🦇 Flying Eye - Fixed FSM

```python
def execute_ai_behavior(self):
    # Guard clause
    if not self.alive or not self.player_ref:
        self.state = 'idle'  # ← SET STATE
        self.physics.velocity_y = 0
        return 0
    
    # Range attack state
    if self.is_range_attacking:
        self.state = 'range'  # ← SET STATE
        # Hover during attack
        hover_y = sin(offset) * amplitude * 0.5
        self.physics.velocity_y = hover_y * 0.15
        # ... handle animation finish
        return 0
    
    # Get values
    distance = self.get_distance_to_player()
    direction = self.get_direction_to_player()
    hover_y_offset = sin(self.hover_offset) * HOVER_AMPLITUDE
    
    # IDLE state
    if distance > detection_range:
        self.ai_state = self.STATE_IDLE
        self.state = 'idle'  # ← SET STATE
        x_velocity = 0
        self.physics.velocity_y = hover_y_offset * 0.25
    
    # PATROL state
    elif distance > lose_interest_range:
        self.ai_state = self.STATE_PATROL
        self.state = 'walk'  # ← SET STATE
        x_velocity = self.do_patrol()
        self.physics.velocity_y = hover_y_offset * 0.2
    
    # CHASE state
    else:
        self.ai_state = self.STATE_CHASE
        self.state = 'chase'  # ← SET STATE
        self.facing_right = direction > 0
        x_velocity = direction * speed
        # Vertical movement + hover
        self.physics.velocity_y = calculate_vertical()
    
    return x_velocity
```

**Key Points:**
- ✅ `self.state` set untuk setiap AI state
- ✅ Hover motion integrated dalam behavior
- ✅ No duplicate logic
- ✅ Vertical velocity set di behavior, bukan di update()

---

## 👹 Goblin - Fixed FSM

```python
def execute_ai_behavior(self):
    # Guard clause
    if not self.alive or not self.player_ref:
        self.state = 'idle'  # ← SET STATE
        return 0
    
    # Range attack state
    if self.is_range_attacking:
        self.state = 'range'  # ← SET STATE
        direction = self.get_direction_to_player()
        self.facing_right = direction > 0
        # ... handle animation finish
        return 0
    
    distance = self.get_distance_to_player()
    direction = self.get_direction_to_player()
    
    # IDLE state
    if distance > detection_range:
        self.ai_state = self.STATE_IDLE
        self.state = 'idle'  # ← SET STATE
        x_velocity = 0
    
    # PATROL state
    elif distance > lose_interest_range:
        self.ai_state = self.STATE_PATROL
        self.state = 'walk'  # ← SET STATE
        x_velocity = self.do_patrol()
    
    # RETREAT state
    elif distance < MIN_SAFE_DISTANCE:
        self.ai_state = 'retreat'
        self.state = 'walk'  # ← SET STATE (use walk animation)
        retreat_dir = -direction
        self.facing_right = direction > 0  # Face player!
        x_velocity = retreat_dir * speed * 1.2
    
    # CHASE state
    else:
        self.ai_state = self.STATE_CHASE
        self.state = 'chase'  # ← SET STATE
        self.facing_right = direction > 0
        x_velocity = direction * speed
    
    return x_velocity
```

**Key Points:**
- ✅ `self.state` set untuk setiap AI state
- ✅ Retreat uses 'walk' animation
- ✅ Face player while retreating
- ✅ Consistent direction update

---

## 🍄 Mushroom - Fixed FSM

```python
def execute_ai_behavior(self):
    # Guard clause
    if not self.alive or not self.player_ref:
        self.state = 'idle'  # ← SET STATE
        return 0
    
    # Spore attack state
    if self.is_spore_attacking:
        self.state = 'range'  # ← SET STATE (use range anim)
        direction = self.get_direction_to_player()
        self.facing_right = direction > 0
        # ... handle animation finish
        return 0
    
    distance = self.get_distance_to_player()
    dist_from_spawn = abs(self.rect.x - self.spawn_x)
    direction = self.get_direction_to_player()
    
    # RETURN TO SPAWN state
    if dist_from_spawn > TERRITORY_RADIUS:
        self.ai_state = 'return'
        self.state = 'walk'  # ← SET STATE
        if self.rect.x > self.spawn_x:
            self.facing_right = False
            x_velocity = -speed
        else:
            self.facing_right = True
            x_velocity = speed
    
    # IDLE state
    elif distance > detection_range:
        self.ai_state = self.STATE_IDLE
        self.state = 'idle'  # ← SET STATE
        x_velocity = 0
    
    # CHASE state
    elif distance < TERRITORY_RADIUS:
        self.ai_state = self.STATE_CHASE
        self.state = 'chase'  # ← SET STATE
        self.facing_right = direction > 0
        x_velocity = direction * speed
    
    return x_velocity
```

**Key Points:**
- ✅ `self.state` set untuk setiap AI state
- ✅ Spore attack uses 'range' animation
- ✅ Return to spawn uses 'walk' animation
- ✅ Territorial behavior maintained

---

## 💀 Skeleton - Fixed FSM

```python
def execute_ai_behavior(self):
    # Guard clause
    if not self.alive or not self.player_ref:
        self.state = 'idle'  # ← SET STATE
        return 0
    
    direction = self.get_direction_to_player()
    
    # SHIELD state
    if self.is_shielding:
        self.state = 'shield'  # ← SET STATE
        self.shield_active = True
        self.facing_right = direction > 0
        # ... handle animation finish
        return 0
    
    # RANGE ATTACK state
    if self.is_throwing:
        self.state = 'range'  # ← SET STATE
        self.facing_right = direction > 0
        # ... handle animation finish
        return 0
    
    distance = self.get_distance_to_player()
    
    # IDLE state
    if distance > detection_range:
        self.ai_state = self.STATE_IDLE
        self.state = 'idle'  # ← SET STATE
        self.shield_active = False
        x_velocity = 0
    
    # PATROL state
    elif distance > lose_interest_range:
        self.ai_state = self.STATE_PATROL
        self.state = 'walk'  # ← SET STATE
        self.shield_active = False
        x_velocity = self.do_patrol()
    
    # SHIELD or ATTACK state
    elif distance <= attack_range:
        if self.should_shield and not self.is_attacking:
            self.ai_state = 'shield'
            self.state = 'shield'  # ← SET STATE
            self.is_shielding = True
            # ... trigger shield
        else:
            self.ai_state = self.STATE_ATTACK
            self.do_attack()  # Sets self.state = 'attack'
            # ...
        x_velocity = 0
    
    # CHASE state
    else:
        self.ai_state = self.STATE_CHASE
        self.state = 'chase'  # ← SET STATE
        self.facing_right = direction > 0
        self.shield_active = False
        x_velocity = direction * speed
    
    return x_velocity
```

**Key Points:**
- ✅ `self.state` set untuk setiap AI state
- ✅ Shield has dedicated 'shield' state
- ✅ Range attack uses 'range' state
- ✅ Shield deactivated when not shielding

---

## 📊 State Mapping Summary

| AI State | Animation State | Notes |
|----------|----------------|-------|
| STATE_IDLE | 'idle' | Standing still |
| STATE_PATROL | 'walk' | Patrolling area |
| STATE_CHASE | 'chase' or 'walk' | Chasing player |
| STATE_ATTACK | 'attack' | Melee attack (set by do_attack()) |
| 'range' | 'range' | Range attack |
| 'retreat' | 'walk' | Retreating (Goblin) |
| 'return' | 'walk' | Return to spawn (Mushroom) |
| 'shield' | 'shield' | Shield defense (Skeleton) |
| 'spore' | 'range' | Spore attack (Mushroom) |

---

## 🔑 Key Rules

### 1. **Always Set Both States**
```python
# ✅ CORRECT
self.ai_state = self.STATE_CHASE
self.state = 'chase'

# ❌ WRONG - Missing animation state
self.ai_state = self.STATE_CHASE
# self.state not set!
```

### 2. **Set State Before Animation**
```python
# ✅ CORRECT
if condition:
    self.ai_state = 'range'
    self.state = 'range'
    self.is_range_attacking = True
    self.animator.reset_animation()  # After state set

# ❌ WRONG - State set after reset
if condition:
    self.is_range_attacking = True
    self.animator.reset_animation()
    self.state = 'range'  # Too late!
```

### 3. **Guard Clauses Return Early**
```python
# ✅ CORRECT
if not self.alive or not self.player_ref:
    self.state = 'idle'  # Set state
    return 0  # Return early

# ❌ WRONG - No state set
if not self.alive:
    return 0  # State undefined!
```

### 4. **Flying Enemy Vertical Movement**
```python
# ✅ CORRECT - Set in execute_ai_behavior()
def execute_ai_behavior(self):
    # ... calculate hover
    self.physics.velocity_y = hover_y_offset * intensity
    return x_velocity

def update(self, platforms):
    x_velocity = self.execute_ai_behavior()
    self.physics.update(platforms, x_velocity, apply_gravity=False)

# ❌ WRONG - Set in update()
def update(self, platforms):
    hover_y = sin(offset) * amplitude
    self.physics.velocity_y = hover_y  # Don't do this!
    x_velocity = self.execute_ai_behavior()
```

---

## 🎯 Testing FSM

### Check Animation State Sync:
```python
# Add debug in execute_ai_behavior()
print(f"AI State: {self.ai_state}, Anim State: {self.state}")

# Should match:
# AI State: chase, Anim State: chase
# AI State: idle, Anim State: idle
# AI State: range, Anim State: range
```

### Check State Transitions:
```python
# Watch state changes
IDLE → CHASE (player detected)
CHASE → ATTACK (in range)
ATTACK → CHASE (attack finished)
CHASE → IDLE (player too far)
```

### Check Flying Eye Hover:
```python
# Should see smooth sinusoidal motion
# velocity_y should change every frame
# Different intensity per state
```

---

## ✅ Implementation Checklist

### All Enemies:
- [x] `self.state` set di setiap AI state
- [x] Guard clauses return early dengan state set
- [x] Animation state sync dengan AI state
- [x] Direction update before movement
- [x] Proper gravity handling

### Flying Eye:
- [x] Hover motion di execute_ai_behavior()
- [x] No duplicate hover logic
- [x] Vertical velocity properly managed
- [x] Different hover intensity per state

### Goblin:
- [x] Retreat state uses 'walk' animation
- [x] Face player while retreating
- [x] Range attack state properly set

### Mushroom:
- [x] Spore attack uses 'range' animation
- [x] Return to spawn uses 'walk' animation
- [x] Territorial behavior maintained

### Skeleton:
- [x] Shield state properly set
- [x] Shield active flag managed
- [x] Range attack state properly set

---

**FSM & AI Logic: ✅ FIXED AND SYNCHRONIZED**
