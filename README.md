# 🚀 Space Invaders: Cosmic Ranger

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Pygame](https://img.shields.io/badge/Pygame-2.0+-green.svg)
![Genre](https://img.shields.io/badge/Genre-Roguelike%20Survivor-purple.svg)

> **A roguelike bullet heaven shooter inspired by 20 Minutes Till Dawn and Diep.io**

**Survive waves of alien hordes. Evolve your arsenal. Become unstoppable.**

---

## 🎮 Overview

You are **Commander Vex**, humanity's last defense against an endless alien invasion in deep space. Your ship is stranded, backup is impossible, and dimensional rifts pour endless enemies toward you.

**Survive as long as you can.** Kill enemies, collect XP, level up, and choose powerful upgrades to create devastating synergies. Each run is unique. Each death is permanent.

---

## ✨ Features

- **Roguelike Progression**: Level up and select from 3 random upgrades every 2 levels
- **Deep Upgrade Trees**: 50+ upgrades across 9 skill trees with branching paths
- **Diep.io-Style Cannons**: Evolve from 1 to 10 barrels firing in all directions
- **Elemental Combat**: Fire, Ice, Poison, and Shock with unique status effects
- **Boss Battles**: Face massive Void Lords every 60 seconds
- **Companion Summons**: Deploy drones, phantoms, dragons, and magical lenses
- **Dynamic Difficulty**: Enemies scale in variety, speed, and HP over time
- **Ultimate Abilities**: Devastating laser beam with 30-second cooldown

---

## 🕹️ Controls

| Input               | Action         |
| ------------------- | -------------- |
| `WASD` / Arrow Keys | Move           |
| Mouse + Left Click  | Aim & Shoot    |
| `R`                 | Manual Reload  |
| `Spacebar`          | Laser Ultimate |
| `Shift`             | Speed Boost    |
| `ESC`               | Pause          |

---

## 💾 Enemy Types

| Enemy                | Threat     | Behavior                    |
| -------------------- | ---------- | --------------------------- |
| 🔴 **Drifters**      | ⭐         | Basic slow pursuers         |
| 🟡 **Stalkers**      | ⭐⭐       | Fast, fragile swarmers      |
| 🟤 **Goliaths**      | ⭐⭐⭐     | Slow, heavily armored tanks |
| ⚡ **Blur Phantoms** | ⭐⭐       | Ultra-fast glass cannons    |
| 💀 **Devastators**   | ⭐⭐⭐⭐   | Massive HP juggernauts      |
| 🔫 **Void Sentries** | ⭐⭐⭐⭐   | Ranged shooters             |
| ⚡ **Riftchargers**  | ⭐⭐⭐⭐   | Build speed then charge     |
| 👁️ **Hivemasters**   | ⭐⭐⭐⭐⭐ | Spawn endless minions       |
| 👑 **Void Lords**    | 💀💀💀     | Boss enemies (every 60s)    |

**Elite Variants** appear later with 2.5x HP and golden auras.

---

## ⬆️ Upgrade System

### Skill Trees

**🔫 Cannons**: Twin → Triple/Quad → **Octo** (Ultimate)  
**💥 Damage**: Power Shot → Heavy/Piercing → **Devastator**  
**🚀 Speed**: Swift Shot → Velocity/Sniper → **Railgun** (Hitscan)  
**🔥 Fire**: Ignite → Inferno/Explosion → **Hellfire** (Chain explosions)  
**❄️ Ice**: Chill → Frostbite/Shatter → **Absolute Zero** (2x damage)  
**☠️ Poison**: Venom → Plague/Necrosis → **Pandemic** (Infinite spread)  
**⚪ Orbs**: Orbit → Trinity/Quad → **Octo Orbs** (8 orbs, 2x speed)  
**🛡️ Defense**: Barrier/Vitality → Shields/Regen → **Fortress/Immortal**  
**👻 Summons**: Drones/Phantoms/Dragons/Lenses → Ultimate variants

### Boss Evolution Drops

- **Guided Missiles**: Homing bullets
- **Lightning Storm**: Chain lightning strikes
- **Deca Cannon**: 10-barrel devastation
- **Orb Storm**: 12 orbs with pulse waves
- **Summon Army**: Double all summon counts

---

## ⚔️ Combat Systems

**Magazine System**: 12 bullets, 1.2s reload  
**Auto-Fire**: Hold mouse to shoot continuously  
**Status Effects**: Burn (DoT + spread), Freeze (slow + bonus damage), Poison (long DoT), Shock (stun + chain)  
**Laser Ultimate**: 5-second beam dealing 4x bullet damage/sec

**Health**: 4 hearts, 1-second invulnerability after hits, upgradable shields and revives

---

## 📈 Difficulty Timeline

| Time   | Event                     |
| ------ | ------------------------- |
| 0:45   | Stalkers spawn            |
| 1:00   | First Boss                |
| 1:30   | Goliaths spawn            |
| 2:30   | Sprinters spawn           |
| 4:00   | Void Sentries spawn       |
| 5:00   | Riftchargers spawn        |
| 7:00   | Hivemasters spawn         |
| 10:00+ | Elite variants everywhere |

Enemy HP increases by 100% every 3 minutes.

---

## ⚙️ Installation

```bash
# Clone repository
git clone https://github.com/Junjuyun/G.git

# Install dependencies
pip install pygame

# Run game
python "Space Invaders.py"
```

**Requirements**: Python 3.8+, Pygame 2.0+

---

## 🎯 Survival Tips

1. Keep moving—stationary targets die fast
2. Kill Summoners first—they spawn infinite enemies
3. Build synergies—Fire + Explosion = chain reactions
4. Collect XP orbs—they magnetize when close
5. Save Laser for bosses or emergencies
6. Manage Boost meter carefully
7. Orbs provide passive damage while you dodge

---

## 🏆 Rankings

| Survival Time | Rank              |
| ------------- | ----------------- |
| 1 min         | Cadet             |
| 3 min         | Ranger            |
| 5 min         | Veteran           |
| 10 min        | Elite             |
| 15 min        | Legend            |
| 20+ min       | **Cosmic Ranger** |

---

## 📁 Project Structure

```
├── Space Invaders.py    # Entry point
├── game.py              # Main game loop
├── game_entities.py     # Player, Enemy, Bullet classes
├── game_combat.py       # Combat calculations
├── game_spawning.py     # Enemy spawning
├── game_rendering.py    # Drawing & UI
├── upgrade_trees.py     # Upgrade definitions
├── upgrade_system.py    # Upgrade logic
└── Assets/
    ├── Sounds/          # Audio files
    └── UI/              # Fonts & UI
```

---

## 📜 Credits

**Developer**: Group Ayon  
**Inspired by**: 20 Minutes Till Dawn, Vampire Survivors, Diep.io  
**Engine**: Pygame  
**Font**: Press Start 2P

---

<div align="center">

### 🌟 _"In the void, only the strongest evolve."_ 🌟

</div>
