# Enemy Spawn System - Panduan Lengkap

## Overview
Sistem spawn enemy di BattleMage in Tamriel mendukung 2 metode:
1. **Map-based Spawn** (BARU): Pakai huruf di `level_data` + config count
2. **Manual Spawn** (LAMA): Tulis koordinat manual

---

## Metode 1: Map-based Spawn (Recommended)

### Cara Kerja
1. Taruh huruf spawn di `level_data`: **Z** (Zombie), **V** (Vampire), **G** (Golem)
2. Set jumlah enemy per huruf di `enemy_spawn_config`

### Contoh - Level 1
```python
level_data = [
    "###############X################",
    "###############X################",
    "#########=#####X    #       Z   ",  # <- Z di sini
    "####=##########X____#___________",
    "######=####=###=P           V   ",  # <- V di sini
    "#=##=####=###=#X                ",
    "####=####=##=##X            G   ",  # <- G di sini
]

enemy_spawn_config = [
    ('Z', 3),  # Spawn 3 zombie di setiap huruf Z
    ('V', 1),  # Spawn 1 vampire di setiap huruf V
    ('G', 1),  # Spawn 1 golem di setiap huruf G
]
```

**Hasil**: 
- 3 zombie spawn di posisi Z (dengan spacing 30px)
- 1 vampire spawn di posisi V
- 1 golem spawn di posisi G

### Keuntungan
✅ Mudah visualisasi posisi enemy di map
✅ Bisa spawn banyak enemy di 1 titik (zombie horde!)
✅ Gampang edit langsung di ASCII map
✅ Koordinat otomatis dari posisi huruf

### Contoh Zombie Horde - Level 3
```python
level_data = [
    "###############X################",
    "#####X      ZZZZZZZZZZZZZ   X###",  # <- 13 huruf Z
]

enemy_spawn_config = [
    ('Z', 10),  # 10 zombie per huruf Z = 130 total zombie!
]
```

---

## Metode 2: Manual Spawn

### Cara Kerja
Langsung tulis koordinat (x, y) untuk setiap enemy

### Contoh
```python
enemy_spawn_config = [
    ('Zombie', 600, 600),   # Zombie di x=600, y=600
    ('Zombie', 900, 600),   # Zombie kedua
    ('Vampire', 1200, 400), # Vampire terbang
    ('Golem', 1800, 550),   # Golem boss
]
```

### Keuntungan
✅ Kontrol presisi posisi spawn
✅ Cocok untuk spawn individual/boss

---

## Enemy Types

| Huruf | Nama    | HP  | Damage | Special        |
|-------|---------|-----|--------|----------------|
| **Z** | Zombie  | 50  | 10     | Patrol & Chase |
| **V** | Vampire | 75  | 15     | Flying, Lifesteal |
| **G** | Golem   | 150 | 25     | Tank, Appear animation |

---

## Tips & Best Practices

### 1. Zombie Horde
```python
# Baris panjang Z untuk wave attack
"ZZZZZZZZZZZZZZZZZZZZZZZZ"

enemy_spawn_config = [
    ('Z', 5),  # 5 zombie per Z = massive horde!
]
```

### 2. Mixed Combat
```python
# Kombinasi huruf untuk challenge
"Z    V    Z    G"

enemy_spawn_config = [
    ('Z', 2),  # 2 zombie per Z = 4 total
    ('V', 1),  # 1 vampire
    ('G', 1),  # 1 golem boss
]
```

### 3. Boss Arena
```python
# Single boss dengan koordinat presisi
enemy_spawn_config = [
    ('Golem', 2500, 300),  # Boss tepat di center arena
]
```

---

## Spawn Spacing

Ketika spawn multiple enemies di 1 titik:
- Offset otomatis: **30 pixel** antar enemy
- Enemy ke-1: x
- Enemy ke-2: x + 30
- Enemy ke-3: x + 60
- dst...

Contoh:
```python
# Huruf Z di posisi x=1000
# Config: ('Z', 3)
# Hasil spawn:
# Zombie #1: x=1000
# Zombie #2: x=1030
# Zombie #3: x=1060
```

---

## Troubleshooting

### Q: Enemy tidak spawn?
**A:** Pastikan:
1. Huruf (Z/V/G) ada di `level_data`
2. `enemy_spawn_config` ada dan formatnya benar
3. Cek console log `[SPAWN]`

### Q: Mau spawn 100+ zombie?
**A:** Pakai metode map-based:
```python
# 50 huruf Z, masing-masing spawn 10
enemy_spawn_config = [('Z', 10)]  # = 500 zombie!
```

### Q: Mix kedua metode?
**A:** Tidak bisa! Pilih salah satu:
- Format `(huruf, count)` → map-based
- Format `(type, x, y)` → manual

---

## Examples

### Tutorial Level (Easy)
```python
enemy_spawn_config = [
    ('Z', 1),  # 1-2 zombie saja
]
```

### Normal Level (Medium)
```python
enemy_spawn_config = [
    ('Z', 2),  # 2 zombie per spawn
    ('V', 1),  # 1 vampire
]
```

### Hard Level (Apocalypse)
```python
enemy_spawn_config = [
    ('Z', 10),  # ZOMBIE HORDE!!!
    ('V', 2),   # Flying vampires
    ('G', 1),   # Tank golem
]
```
