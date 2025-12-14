# 🚀 Space Invaders: Cosmic Ranger

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Pygame](https://img.shields.io/badge/Pygame-2.0+-green.svg)
![Genre](https://img.shields.io/badge/Genre-Roguelike%20Survivor-purple.svg)
![Style](https://img.shields.io/badge/Style-Pixel%20Art-orange.svg)

\*A roguelike survival shooter inspired by **20 Minutes Till Dawn** and **Diep.io\***

**⚠️ SURVIVE THE VOID. UPGRADE YOUR ARSENAL. BECOME UNSTOPPABLE.**

</div>

---

## 📖 The Story

In the year 2847, humanity ventured beyond the known galaxies, seeking new frontiers. You are **Commander Vex**, a legendary **Cosmic Ranger** — humanity's last line of defense against the horrors lurking in the infinite darkness of deep space.

Your ship, the _Stardust Vanguard_, was ambushed during a routine patrol through the **Obsidian Nebula**. Now stranded in the heart of hostile territory, waves of alien monstrosities pour from dimensional rifts, hungry for destruction.

There is no escape. There is no backup. There is only **survival**.

Armed with experimental weaponry and the ability to absorb fallen enemy energy to evolve your combat systems, you must hold the line. Every second counts. Every upgrade matters. Every enemy killed brings you closer to unlocking your true potential — or your demise.

**How long can you survive the cosmic onslaught?**

---

## 🎮 Game Overview

**Space Invaders: Cosmic Ranger** is a fast-paced **roguelike bullet heaven** game where you:

- 🎯 **Shoot** endless waves of increasingly dangerous aliens
- ⬆️ **Level up** and choose powerful upgrades from branching skill trees
- 🔥 **Unlock** devastating ultimate abilities and summon companions
- ⏱️ **Survive** as long as possible against escalating hordes

---

## 👾 Enemy Compendium

### The Void Horde

| Enemy                | Codename | Threat Level | Description                                                            |
| -------------------- | -------- | ------------ | ---------------------------------------------------------------------- |
| 🔴 **Drifters**      | Normal   | ⭐           | Basic void creatures. Slow but relentless in pursuit.                  |
| 🟡 **Stalkers**      | Fast     | ⭐⭐         | Quick and agile hunters. Fragile but dangerous in swarms.              |
| 🟤 **Goliaths**      | Tank     | ⭐⭐⭐       | Hulking brutes with thick carapace. Slow but extremely durable.        |
| ⚡ **Blur Phantoms** | Sprinter | ⭐⭐         | Ultra-fast entities. One hit can take them down — if you can hit them. |
| 💀 **Devastators**   | Bruiser  | ⭐⭐⭐⭐     | Massive HP pools. These juggernauts take a beating.                    |
| 🔫 **Void Sentries** | Shooter  | ⭐⭐⭐⭐     | Ranged attackers. They shoot back.                                     |
| ⚡ **Riftchargers**  | Charger  | ⭐⭐⭐⭐     | Build up speed and charge at devastating velocity.                     |
| 👁️ **Hivemasters**   | Summoner | ⭐⭐⭐⭐⭐   | Spawn endless minions. Priority targets.                               |
| 👑 **Void Lords**    | Boss     | 💀💀💀       | Massive bosses with devastating attacks. Appear every 60 seconds.      |

### Elite Variants

After surviving long enough, **Elite versions** of enemies appear with golden auras — 2.5x HP and enhanced speed!

---

## ❤️ Health System

| Mechanic            | Description                                        |
| ------------------- | -------------------------------------------------- |
| **Hearts**          | You start with 4 hearts. Each hit removes 1 heart. |
| **Invulnerability** | 1 second of immunity after taking damage           |
| **Shield**          | Upgradable barrier that absorbs hits before HP     |
| **Revive**          | Second chance upgrades let you respawn on death    |
| **Regeneration**    | Some upgrades grant passive HP recovery            |

---

## 🔫 Combat Systems

### Shooting Mechanics

- **Auto-Fire**: Hold mouse to continuously shoot
- **Magazine System**: 12 bullets per mag, 1.2s reload
- **Manual Reload**: Press `R` to reload early
- **Aim Direction**: Bullets fire toward mouse cursor

### Cannon Configurations (Diep.io Style)

| Upgrade | Cannons | Pattern                 |
| ------- | ------- | ----------------------- |
| Base    | 1       | Single forward          |
| Twin    | 2       | Side-by-side            |
| Triple  | 3       | 2 front + 1 rear        |
| Quad    | 4       | X-pattern cross         |
| Octo    | 8       | All directions          |
| Deca    | 10      | Full circle (Evolution) |

### Status Effects

| Element       | Effect                                   |
| ------------- | ---------------------------------------- |
| 🔥 **Burn**   | Damage over time (3s, spreads on death)  |
| ❄️ **Freeze** | Slow enemies by 40-55%, bonus damage     |
| ☠️ **Poison** | Long DoT (5s), spreads to nearby enemies |
| ⚡ **Shock**  | Stun and chain lightning                 |

---

## ⬆️ Progression & Upgrades

### Leveling System

- Kill enemies → Collect XP orbs → Level up
- Every **2 levels**, choose from **3 random upgrades**
- Build your own synergistic loadout each run

### Upgrade Trees

#### 🔫 **CANNONS** - Multi-Barrel Destruction

```
Twin Cannons → Triple Cannons → OCTO CANNONS (Ultimate)
             → Quad Cannons  ↗
```

#### 💥 **DAMAGE** - Raw Power

```
Power Shot → Heavy Rounds    → DEVASTATOR (Ultimate)
          → Armor Piercing  ↗
```

#### 🚀 **SPEED** - Velocity & Precision

```
Swift Shot → Velocity → RAILGUN (Ultimate - Hitscan!)
          → Sniper  ↗
```

#### 🔥 **FIRE** - Burn Everything

```
Ignite → Inferno   → HELLFIRE (Ultimate - Chain Explosions)
      → Explosion ↗
```

#### ❄️ **ICE** - Freeze & Shatter

```
Chill → Frostbite → ABSOLUTE ZERO (Ultimate - 2x Damage to Frozen)
     → Shatter  ↗
```

#### ☠️ **POISON** - Spreading Death

```
Venom → Plague   → PANDEMIC (Ultimate - Infinite Spread)
     → Necrosis ↗
```

#### ⚪ **ORBS** - Orbiting Damage

```
Orbit (2 orbs) → Trinity (3)  → OCTO ORBS (8 orbs, 2x speed)
              → Quad Orbs (4) ↗
```

#### 🛡️ **DEFENSE** - Survive Longer

```
Barrier → Reinforced  → FORTRESS (3 shields, auto-regen)
       → Reflective ↗

Vitality → Regeneration → IMMORTAL (+3 HP, full revive)
        → Second Wind ↗
```

#### 👻 **SUMMONS** - Companions

```
Drone Deploy → Piercing Shots → DRONE SWARM (4 elemental drones)
            → Elemental Drones ↗

Phantom → Spectral Chill → PHANTOM ARMY (4 phantoms, lifesteal)
       → Soul Drain ↗

Dragon Egg → Fire Breath  → ELDER DRAGON (60 dmg, instant hatch)
          → Dragon Growth ↗

Magic Lens → Amplifier → KALEIDOSCOPE (3 lenses, 5x bullets)
          → Prism ↗
```

### 🌟 Evolutions (Boss Drops)

Special game-changing upgrades from defeating bosses:

| Evolution           | Effect                                        |
| ------------------- | --------------------------------------------- |
| **Guided Missiles** | Bullets home toward enemies                   |
| **Lightning Storm** | Periodic lightning strikes chain between foes |
| **Deca Cannon**     | 10 cannons firing in all directions           |
| **Orb Storm**       | 12 orbs with pulse wave attacks               |
| **Summon Army**     | Double all summon counts                      |

---

## ⚡ Special Abilities

### 💫 Laser Ultimate (Spacebar)

- **Cooldown**: 30 seconds
- **Duration**: 5 seconds
- **Damage**: 4x your bullet damage as DPS
- **Effect**: Massive beam that incinerates enemies in a line

### 💨 Boost (Hold Shift)

- **Speed**: 1.75x movement
- **Meter**: Drains while boosting, recharges when stopped
- **Camera**: Zooms out for better vision
- **Lock**: 1 second cooldown when meter empties

---

## 🕹️ Controls

| Key                   | Action         |
| --------------------- | -------------- |
| `WASD` / `Arrow Keys` | Move           |
| `Mouse`               | Aim            |
| `Left Click` (Hold)   | Shoot          |
| `R`                   | Reload         |
| `Spacebar`            | Activate Laser |
| `Shift` (Hold)        | Boost          |
| `ESC`                 | Pause          |

---

## ⚙️ Difficulty Scaling

The void grows hungrier over time:

| Time   | What Happens                    |
| ------ | ------------------------------- |
| 0:00   | Drifters only                   |
| 0:45   | Stalkers appear                 |
| 1:00   | **BOSS #1**                     |
| 1:30   | Goliaths appear                 |
| 2:00   | **BOSS #2**                     |
| 2:30   | Sprinters appear                |
| 3:00   | **BOSS #3+** (They shoot back!) |
| 4:00   | Void Sentries (ranged) appear   |
| 5:00   | Riftchargers appear             |
| 7:00   | Hivemasters (summoners) appear  |
| 10:00+ | Elite variants everywhere       |

**Enemy HP scales with time**: +100% HP every 3 minutes

---

## 🖥️ Requirements

- **Python** 3.8+
- **Pygame** 2.0+

### Installation

```bash
# Clone the repository
git clone https://github.com/Junjuyun/G.git

# Install dependencies
pip install pygame

# Run the game
python "game.py"

# Fullscreen note (Windows)
# The in-game FULLSCREEN toggle uses borderless-windowed fullscreen (scaled)
# to reduce alt-tab lag and improve OBS capture compatibility.
```

---

## 📁 Project Structure

```
├── Space Invaders.py    # Legacy entry point (optional)
├── game.py              # Main game loop & logic
├── game_entities.py     # Player, Enemy, Bullet classes
├── game_combat.py       # Combat calculations
├── game_spawning.py     # Enemy spawn logic
├── game_rendering.py    # Drawing & UI
├── game_powerups.py     # Powerup effects
├── game_ui.py           # UI components
├── upgrade_trees.py     # All upgrade definitions
├── upgrade_system.py    # Upgrade application logic
├── audio.py             # Sound management
├── settings.py          # Game settings
├── game_constants.py    # Constants & values
└── Assets/
    ├── Sounds/          # Sound effects
    └── UI/              # Fonts & UI assets
```

---

## 🎯 Tips for Survival

1. **Don't stop moving** — stationary targets die fast
2. **Prioritize Summoners** — they spawn infinite minions
3. **Build synergies** — Fire + Explosion = Chain reactions
4. **Collect XP orbs** — they magnetize to you when close
5. **Save your Laser** — use it when overwhelmed by bosses
6. **Boost strategically** — meter management is key
7. **Orbs are powerful** — they deal passive damage while you focus on dodging

---

## 🏆 High Score Goals

| Time Survived | Title             |
| ------------- | ----------------- |
| 1 minute      | Cadet             |
| 3 minutes     | Ranger            |
| 5 minutes     | Veteran           |
| 10 minutes    | Elite             |
| 15 minutes    | Legend            |
| 20+ minutes   | **Cosmic Ranger** |

---

## 📜 Credits

- **Game Design & Development**: Group Ayon
- **Inspiration**: 20 Minutes Till Dawn, Vampire Survivors, Diep.io
- **Engine**: Pygame
- **Font**: Press Start 2P (OFL License)

---

## 📄 License

This project is for educational and personal use.

---

<div align="center">

### 🌟 _"In the void, only the strongest evolve."_ 🌟

**[Play Now]** | **[Report Bug]** | **[Request Feature]**

</div>
