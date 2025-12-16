# Testing Guide - Level 1 Enemies

## 🎯 Cara Testing

### Setup
1. Run game: `python main.py`
2. Masuk ke Level 1
3. Perhatikan behavior setiap enemy

---

## 🦇 Flying Eye - Flying Monster

### ✅ Yang Harus Dilihat:

**1. Smooth Hovering Motion**
- [ ] Flying Eye terlihat naik-turun secara smooth (seperti ngambang)
- [ ] Motion terlihat natural, tidak patah-patah
- [ ] Saat idle, hover lebih gentle
- [ ] Saat chase, hover tetap ada tapi juga bergerak vertikal

**2. Direction Consistency**
- [ ] Saat player di kiri, Flying Eye menghadap kiri
- [ ] Saat player di kanan, Flying Eye menghadap kanan
- [ ] Saat range attack, menghadap ke player

**3. Vertical Movement**
- [ ] Flying Eye terbang di atas player (sekitar 40 pixel)
- [ ] Saat chase, naik/turun untuk maintain height
- [ ] Tidak stuck di ceiling atau floor

**4. Death**
- [ ] Saat mati, jatuh ke bawah (gravity applied)
- [ ] Tidak floating setelah mati

### Testing Steps:
```
1. Dekati Flying Eye dari kiri -> harus hadap kiri
2. Pindah ke kanan -> harus hadap kanan
3. Perhatikan motion naik-turun saat dia idle
4. Perhatikan dia maintain height saat chase
5. Kill dia -> harus jatuh
```

---

## 👹 Goblin - Tactical Fighter

### ✅ Yang Harus Dilihat:

**1. Direction Consistency**
- [ ] Selalu menghadap player saat chase
- [ ] Saat mundur (retreat), tetap menghadap player
- [ ] Saat attack (melee/range), menghadap player

**2. Tactical Positioning**
- [ ] Jika terlalu dekat (< 60px), mundur sambil tetap hadap player
- [ ] Jika di optimal range (130-230px), range attack
- [ ] Jika terlalu jauh, chase

**3. No Floating**
- [ ] Selalu di ground, tidak floating
- [ ] Jatuh jika tidak ada platform
- [ ] Tidak stuck di udara

**4. Attack Switching**
- [ ] Melee attack saat dekat
- [ ] Range attack saat medium distance
- [ ] Maintain distance saat cooldown

### Testing Steps:
```
1. Dekati Goblin -> harus melee attack
2. Mundur sedikit -> harus retreat sambil hadap player
3. Mundur lebih jauh -> harus range attack
4. Perhatikan tidak floating saat bergerak
```

---

## 🍄 Mushroom - Tanky Defender

### ✅ Yang Harus Dilihat:

**1. Territorial Behavior**
- [ ] Hanya chase dalam radius territory (250px from spawn)
- [ ] Jika terlalu jauh dari spawn, kembali ke spawn
- [ ] Tidak chase player terlalu jauh

**2. Direction Consistency**
- [ ] Menghadap player saat chase
- [ ] Menghadap player saat spore attack
- [ ] Menghadap spawn saat return to spawn

**3. No Floating**
- [ ] Selalu di ground
- [ ] Tidak floating saat bergerak

**4. Spore Attack**
- [ ] Spore attack di medium range (50-150px)
- [ ] Menghadap player saat spore attack
- [ ] Ada cooldown antara spore attacks

### Testing Steps:
```
1. Dekati Mushroom -> harus chase
2. Mundur jauh -> tetap chase dalam territory
3. Lure keluar territory -> harus return to spawn
4. Test spore attack di medium distance
5. Perhatikan slow movement (speed 2.0)
```

---

## 💀 Skeleton - Defensive Fighter

### ✅ Yang Harus Dilihat:

**1. Shield Behavior**
- [ ] Raise shield saat HP < 30%
- [ ] Menghadap player saat shield
- [ ] Shield mengurangi damage

**2. Direction Consistency**
- [ ] Menghadap player saat chase
- [ ] Menghadap player saat attack
- [ ] Menghadap player saat throw bone

**3. No Floating**
- [ ] Selalu di ground
- [ ] Tidak floating

**4. Attack Variety**
- [ ] Melee attack saat dekat
- [ ] Bone throw saat medium distance
- [ ] Shield saat low HP

### Testing Steps:
```
1. Dekati Skeleton -> harus melee attack
2. Mundur sedikit -> harus throw bone
3. Damage sampai HP < 30% -> harus raise shield
4. Perhatikan shield reduces damage
5. Perhatikan tidak floating
```

---

## 🐛 Common Issues to Check

### Direction Bug Check:
```
Problem: Enemy jalan kiri tapi hadap kanan
Test: Dekati dari berbagai arah, perhatikan facing
Expected: Selalu menghadap ke arah player
```

### Floating Bug Check:
```
Problem: Ground enemy floating di udara
Test: Perhatikan enemy saat bergerak, saat idle
Expected: Selalu on ground (kecuali Flying Eye)
```

### Flying Eye Hover Check:
```
Problem: Flying Eye tidak ada motion naik-turun
Test: Perhatikan saat idle dan patrol
Expected: Terlihat smooth sinusoidal motion
```

---

## 📊 Testing Checklist Summary

### All Enemies:
- [ ] No syntax errors
- [ ] Game runs without crash
- [ ] Enemies spawn correctly in Level 1

### Flying Eye:
- [ ] ✅ Smooth hovering motion
- [ ] ✅ Consistent direction
- [ ] ✅ Vertical chase movement
- [ ] ✅ Falls when dead

### Goblin:
- [ ] ✅ Tactical retreat (face player)
- [ ] ✅ Consistent direction
- [ ] ✅ No floating
- [ ] ✅ Attack switching

### Mushroom:
- [ ] ✅ Territorial behavior
- [ ] ✅ Returns to spawn
- [ ] ✅ No floating
- [ ] ✅ Spore attack

### Skeleton:
- [ ] ✅ Shield when low HP
- [ ] ✅ Consistent direction
- [ ] ✅ No floating
- [ ] ✅ Bone throw

---

## 🎮 In-Game Commands (If Available)

```python
# Spawn specific enemy for testing
spawn_enemy('flying_eye', x, y)
spawn_enemy('goblin', x, y)
spawn_enemy('mushroom', x, y)
spawn_enemy('skeleton', x, y)

# Damage enemy to test shield
enemy.take_damage(50)  # Skeleton should shield at 30% HP

# Check enemy state
print(f"State: {enemy.ai_state}")
print(f"Facing: {enemy.facing_right}")
print(f"Position: {enemy.rect.x}, {enemy.rect.y}")
```

---

## 📝 Notes

**Flying Eye Hover Settings:**
- Amplitude: 15 pixels
- Frequency: 0.08
- Should be visible but smooth

**Direction Logic:**
```python
# Standard pattern for all enemies
direction = self.get_direction_to_player()
self.facing_right = direction > 0  # +1 = right, -1 = left
```

**Gravity Logic:**
```python
# Ground enemies
self.physics.update(platforms, x_velocity, apply_gravity=True)

# Flying Eye (when alive)
self.physics.update(platforms, x_velocity, apply_gravity=False)

# Flying Eye (when dead)
self.physics.update(platforms, 0, apply_gravity=True)
```

---

**Happy Testing! 🎉**

Jika menemukan bug, cek:
1. Console output untuk error messages
2. Enemy `ai_state` dan `facing_right`
3. `physics.velocity_y` untuk floating issues
4. Animation state untuk direction issues
