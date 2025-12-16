# Level 1 Enemies - Behavior Diagrams

## 🦇 Flying Eye - State Machine

```
                    ┌──────────────┐
                    │   SPAWNED    │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
         ┌──────────┤     IDLE     ├──────────┐
         │          │ (hover gently)│          │
         │          └──────┬───────┘          │
         │                 │ detect player    │
         │                 ▼                  │
         │          ┌─────────────┐           │
         │    ┌────►│    CHASE    ├────┐      │
         │    │     │(hover + move)│    │      │
         │    │     └──────┬──────┘    │      │
         │    │            │           │      │
         │    │   ┌────────┼────────┐  │      │
         │    │   │        │        │  │      │
too far │    │ in range   │   melee│  │      │ too far
         │    │   │        │  range │  │      │
         │    │   ▼        ▼        ▼  │      │
         │    │ ┌────┐  ┌────┐  ┌────┐│      │
         └────┼─┤RANGE├──┤ATTACK├──┤... ├┘      │
              │ └────┘  └────┘  └────┘        │
              │                               │
              └───────────────────────────────┘
                   
HOVER MOTION: sin(offset) * amplitude
- IDLE: amplitude * 0.25
- PATROL: amplitude * 0.2
- CHASE: amplitude * 0.2 + vertical_movement
- ATTACK: amplitude * 0.1
```

**Direction Update Points:**
- ✅ Before CHASE movement
- ✅ Before RANGE attack
- ✅ Before ATTACK

---

## 👹 Goblin - Tactical Positioning

```
                    Player Detected
                          │
         ┌────────────────┼────────────────┐
         │                │                │
    distance < 60    60 < d < 280     d > 280
         │                │                │
         ▼                ▼                ▼
    ┌────────┐      ┌──────────┐     ┌────────┐
    │RETREAT │      │  CHASE   │     │ PATROL │
    │(back + │      │   to     │     │        │
    │ face)  │      │ optimal  │     │        │
    └────────┘      └──────────┘     └────────┘
         │                │                
         │         ┌──────┴──────┐         
         │         │             │         
         │    at optimal    at melee      
         │         │             │         
         │         ▼             ▼         
         │    ┌────────┐    ┌────────┐    
         └───►│ RANGE  │    │ MELEE  │    
              │ ATTACK │    │ ATTACK │    
              └────────┘    └────────┘    
              
OPTIMAL_RANGE: 180px
MIN_SAFE_DISTANCE: 60px

Retreat Behavior:
  movement_dir = -player_direction (move away)
  facing_dir = player_direction (face toward)
```

**Direction Update Points:**
- ✅ Before RETREAT (face player while backing)
- ✅ Before CHASE
- ✅ Before RANGE attack
- ✅ Before MELEE attack

---

## 🍄 Mushroom - Territory Guard

```
         ┌─────────────────────────────────┐
         │    TERRITORY (250px radius)     │
         │                                 │
         │    Spawn ──────► [MUSHROOM]     │
         │      │              │           │
         │      │    player    │           │
         │      │    enters    │           │
         │      │      │       │           │
         │      ▼      ▼       ▼           │
         │   ┌──────────────────┐          │
         │   │      CHASE       │          │
         │   │   (in territory) │          │
         │   └────────┬─────────┘          │
         │            │                    │
         │     ┌──────┼──────┐             │
         │     │      │      │             │
         │  melee   spore  too far        │
         │     │      │      │             │
         │     ▼      ▼      ▼             │
         │  ┌────┐ ┌────┐ ┌────┐           │
         │  │MELEE│SPORE │IDLE│           │
         │  └────┘ └────┘ └────┘           │
         └─────────────────────────────────┘
                     │
                too far from spawn
                     │
                     ▼
              ┌──────────────┐
              │   RETURN TO  │
              │    SPAWN     │
              └──────────────┘

TERRITORY_RADIUS: 250px
SPORE_RANGE: 50-150px

Return to Spawn:
  if dist_from_spawn > TERRITORY_RADIUS:
      move toward spawn_x
```

**Direction Update Points:**
- ✅ Before CHASE
- ✅ Before MELEE attack
- ✅ Before SPORE attack
- ✅ During RETURN (face spawn direction)

---

## 💀 Skeleton - Shield Defense

```
         HP > 30%                HP < 30%
              │                      │
              ▼                      ▼
       ┌────────────┐         ┌────────────┐
       │   NORMAL   │         │  DEFENSIVE │
       │    MODE    │         │    MODE    │
       └──────┬─────┘         └──────┬─────┘
              │                      │
     ┌────────┼────────┐    ┌────────┼────────┐
     │        │        │    │        │        │
  melee    range   chase shield    range   chase
     │        │        │    │        │        │
     ▼        ▼        ▼    ▼        ▼        ▼
  ┌────┐  ┌────┐  ┌────┐ ┌────┐ ┌────┐ ┌────┐
  │MELEE│ │BONE│  │... │ │SHIELD│BONE│  │... │
  │ATK │  │THROW│ │    │ │BLOCK│THROW│ │    │
  └────┘  └────┘  └────┘ └────┘ └────┘ └────┘

SHIELD_HP_THRESHOLD: 30%
SHIELD_BLOCK_CHANCE: 60%
DAMAGE_REDUCTION: 70%

Shield Logic:
  if hp_ratio < 0.3 and distance <= attack_range:
      if not is_attacking:
          raise_shield()
      else:
          normal_attack()
```

**Direction Update Points:**
- ✅ During SHIELD (face player)
- ✅ Before BONE THROW
- ✅ Before MELEE attack
- ✅ During CHASE

---

## 🎯 Direction Update Pattern (All Enemies)

```python
def execute_ai_behavior(self):
    # STEP 1: Get direction
    direction = self.get_direction_to_player()
    # direction = +1 (right) or -1 (left)
    
    # STEP 2: Update facing BEFORE action
    self.facing_right = direction > 0
    
    # STEP 3: Calculate movement
    x_velocity = direction * self.movement_speed
    
    # STEP 4: Return velocity
    return x_velocity  # NOT self.physics.velocity_x = ...
```

---

## 🌊 Flying Eye Hover Motion

```
Height
  ^
  │     /\      /\      /\      /\
  │    /  \    /  \    /  \    /  \
  │───/────\──/────\──/────\──/────\─── Base Height
  │  /      \/      \/      \/      \
  │ /                                 
  └────────────────────────────────────> Time

Formula: y_offset = sin(time) * amplitude

Amplitude per state:
  IDLE:   15 * 0.25 = 3.75px  (subtle)
  PATROL: 15 * 0.20 = 3.00px  (natural)
  CHASE:  15 * 0.20 = 3.00px  (+ vertical movement)
  ATTACK: 15 * 0.10 = 1.50px  (very stable)

Frequency: 0.08 (visible but smooth)
```

---

## 📊 Combat Ranges Visualization

```
Flying Eye:
  ├─ Detection: 400px ───────────────────────┤
  ├─ Range Attack: 320px ────────────────┤
  ├─ Attack: 50px ─┤

Goblin:
  ├─ Detection: 350px ──────────────────────┤
  ├─ Range Attack: 280px ────────────────┤
  ├─ Optimal Range: 180px ──────────┤
  ├─ Attack: 55px ──┤
  ├─ Min Safe: 60px ──┤ (retreat zone)

Mushroom:
  ├─ Territory: 250px ─────────────────┤
  ├─ Detection: 280px ──────────────────┤
  ├─ Spore: 50-150px ──────┤
  ├─ Attack: 55px ──┤

Skeleton:
  ├─ Detection: 320px ───────────────────┤
  ├─ Range Attack: 260px ─────────────┤
  ├─ Attack: 55px ──┤
```

---

## 🔄 Physics Update Flow

### Ground Enemies (Goblin, Mushroom, Skeleton):
```
┌─────────────────────────────────────┐
│  execute_ai_behavior()              │
│  └─> returns x_velocity             │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  self.physics.update(               │
│      platforms,                     │
│      x_velocity,  ◄── from AI       │
│      apply_gravity=True ◄── IMPORTANT│
│  )                                  │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Physics applies:                   │
│  - Gravity (down)                   │
│  - x_velocity (left/right)          │
│  - Collision with platforms         │
└─────────────────────────────────────┘
```

### Flying Enemy (Flying Eye):
```
┌─────────────────────────────────────┐
│  execute_ai_behavior()              │
│  └─> returns x_velocity             │
│  └─> sets physics.velocity_y        │
│      (for hover + vertical chase)   │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  self.physics.update(               │
│      platforms,                     │
│      x_velocity,  ◄── from AI       │
│      apply_gravity=False ◄── FLYING │
│  )                                  │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Physics applies:                   │
│  - NO Gravity                       │
│  - x_velocity (left/right)          │
│  - velocity_y (up/down + hover)     │
│  - Collision with platforms         │
└─────────────────────────────────────┘

When dead:
  apply_gravity=True ──> Falls down
```

---

## ⚙️ Key Differences Summary

| Aspect | Flying Eye | Ground Enemies |
|--------|-----------|----------------|
| Gravity | False (alive) | True (always) |
| Vertical | Manual control | Gravity only |
| Hover | Yes (sinusoidal) | No |
| Death | Falls (gravity) | Normal |
| Direction | Before all actions | Before all actions |

---

**Visual Guide Complete! 🎨**
