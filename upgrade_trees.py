"""
Upgrade Trees System - Streamlined Version
===========================================
Clean upgrade system with:
- CANNONS: Multiple shooting cannons (Diep.io style)
- BULLETS: Shooting properties (damage, speed, fire rate, size)
- ELEMENTS: Fire, Ice, Poison effects
- ORBS: Aura orbs that orbit and deal damage
- DEFENSE: Shield, HP, Revive, Speed
- SUMMONS: Ghost, Dragon, Lenses
- VISION: Glare effect (full screen flash)

Each tree has 3 tiers:
- Tier 1: Base unlock
- Tier 2a/2b: Two upgrade paths
- Tier 3: Ultimate (combines effects of tier 1+2)
"""

from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class Upgrade:
    """Single upgrade node in a tree."""
    id: str
    name: str
    description: str
    tier: int  # 1, 2, or 3
    category: str
    tree_id: str
    requires: List[str] = field(default_factory=list)
    is_ultimate: bool = False
    effects: Dict[str, float] = field(default_factory=dict)


# ============================================================================
# CANNONS TREE - Multiple shooting cannons like Diep.io
# ============================================================================

CANNONS_TREE = {
    "tree_id": "cannons",
    "name": "Cannons",
    "category": "CANNONS",
    "icon": "🔫",
    "upgrades": [
        Upgrade(
            id="twin_cannons",
            name="Twin Cannons",
            description="Add a second cannon. Cannons fire alternately.",
            tier=1,
            category="CANNONS",
            tree_id="cannons",
            effects={"cannon_count": 2, "cannon_spread": 0.3}
        ),
        Upgrade(
            id="triple_cannons",
            name="Triple Cannons",
            description="Add rear cannon. 3 cannons total (2 front, 1 back).",
            tier=2,
            category="CANNONS",
            tree_id="cannons",
            requires=["twin_cannons"],
            effects={"cannon_count": 3, "has_rear_cannon": True}
        ),
        Upgrade(
            id="quad_cannons",
            name="Quad Cannons",
            description="4 cannons arranged in X pattern.",
            tier=2,
            category="CANNONS",
            tree_id="cannons",
            requires=["twin_cannons"],
            effects={"cannon_count": 4, "cannon_pattern": "cross"}
        ),
        Upgrade(
            id="octo_cannons",
            name="Octo Cannons",
            description="8 cannons firing in all directions!",
            tier=3,
            category="CANNONS",
            tree_id="cannons",
            requires=["triple_cannons", "quad_cannons"],
            is_ultimate=True,
            effects={"cannon_count": 8, "cannon_pattern": "octagon"}
        ),
    ]
}

# ============================================================================
# BULLET PROPERTIES - Damage, Speed, Fire Rate, Size
# ============================================================================

DAMAGE_TREE = {
    "tree_id": "damage",
    "name": "Bullet Damage",
    "category": "BULLETS",
    "icon": "💥",
    "upgrades": [
        Upgrade(
            id="power_shot",
            name="Power Shot",
            description="Bullet damage +40%",
            tier=1,
            category="BULLETS",
            tree_id="damage",
            effects={"damage_mult": 1.40}
        ),
        Upgrade(
            id="heavy_rounds",
            name="Heavy Rounds",
            description="Bullet damage +30%, bullet size +20%",
            tier=2,
            category="BULLETS",
            tree_id="damage",
            requires=["power_shot"],
            effects={"damage_mult": 1.30, "bullet_size_mult": 1.20}
        ),
        Upgrade(
            id="armor_piercing",
            name="Armor Piercing",
            description="Bullet damage +25%, pierce +1",
            tier=2,
            category="BULLETS",
            tree_id="damage",
            requires=["power_shot"],
            effects={"damage_mult": 1.25, "pierce_count": 1}
        ),
        Upgrade(
            id="devastator",
            name="Devastator",
            description="Bullet damage +50%, size +40%, pierce +2",
            tier=3,
            category="BULLETS",
            tree_id="damage",
            requires=["heavy_rounds", "armor_piercing"],
            is_ultimate=True,
            effects={"damage_mult": 1.50, "bullet_size_mult": 1.40, "pierce_count": 2}
        ),
    ]
}

SPEED_TREE = {
    "tree_id": "bullet_speed",
    "name": "Bullet Speed",
    "category": "BULLETS",
    "icon": "⚡",
    "upgrades": [
        Upgrade(
            id="swift_shot",
            name="Swift Shot",
            description="Bullet speed +35%",
            tier=1,
            category="BULLETS",
            tree_id="bullet_speed",
            effects={"bullet_speed_mult": 1.35}
        ),
        Upgrade(
            id="velocity",
            name="Velocity",
            description="Bullet speed +30%, fire rate +10%",
            tier=2,
            category="BULLETS",
            tree_id="bullet_speed",
            requires=["swift_shot"],
            effects={"bullet_speed_mult": 1.30, "fire_rate_mult": 1.10}
        ),
        Upgrade(
            id="sniper",
            name="Sniper",
            description="Bullet speed +40%, damage +15%",
            tier=2,
            category="BULLETS",
            tree_id="bullet_speed",
            requires=["swift_shot"],
            effects={"bullet_speed_mult": 1.40, "damage_mult": 1.15}
        ),
        Upgrade(
            id="railgun",
            name="Railgun",
            description="Bullet speed +60%, instant hit at close range",
            tier=3,
            category="BULLETS",
            tree_id="bullet_speed",
            requires=["velocity", "sniper"],
            is_ultimate=True,
            effects={"bullet_speed_mult": 1.60, "hitscan_range": 200}
        ),
    ]
}

FIRE_RATE_TREE = {
    "tree_id": "fire_rate",
    "name": "Fire Rate",
    "category": "BULLETS",
    "icon": "🔥",
    "upgrades": [
        Upgrade(
            id="rapid_fire",
            name="Rapid Fire",
            description="Fire rate +30%",
            tier=1,
            category="BULLETS",
            tree_id="fire_rate",
            effects={"fire_rate_mult": 1.30}
        ),
        Upgrade(
            id="trigger_happy",
            name="Trigger Happy",
            description="Fire rate +25%, move speed +10%",
            tier=2,
            category="BULLETS",
            tree_id="fire_rate",
            requires=["rapid_fire"],
            effects={"fire_rate_mult": 1.25, "move_speed_mult": 1.10}
        ),
        Upgrade(
            id="bullet_storm",
            name="Bullet Storm",
            description="Fire rate +20%, +1 bullet per shot",
            tier=2,
            category="BULLETS",
            tree_id="fire_rate",
            requires=["rapid_fire"],
            effects={"fire_rate_mult": 1.20, "bullet_count": 1}
        ),
        Upgrade(
            id="minigun",
            name="Minigun",
            description="Fire rate +50%, bullets spray in cone",
            tier=3,
            category="BULLETS",
            tree_id="fire_rate",
            requires=["trigger_happy", "bullet_storm"],
            is_ultimate=True,
            effects={"fire_rate_mult": 1.50, "spray_mode": True, "spread_angle": 25}
        ),
    ]
}

BULLET_SIZE_TREE = {
    "tree_id": "bullet_size",
    "name": "Bullet Size",
    "category": "BULLETS",
    "icon": "⚫",
    "upgrades": [
        Upgrade(
            id="big_bullets",
            name="Big Bullets",
            description="Bullet size +20%, damage +10%",
            tier=1,
            category="BULLETS",
            tree_id="bullet_size",
            effects={"bullet_size_mult": 1.20, "damage_mult": 1.10}
        ),
        Upgrade(
            id="cannonballs",
            name="Cannonballs",
            description="Bullet size +15%, damage +20%",
            tier=2,
            category="BULLETS",
            tree_id="bullet_size",
            requires=["big_bullets"],
            effects={"bullet_size_mult": 1.15, "damage_mult": 1.20}
        ),
        Upgrade(
            id="explosive_rounds",
            name="Explosive Rounds",
            description="Bullets explode on hit, dealing area damage",
            tier=2,
            category="BULLETS",
            tree_id="bullet_size",
            requires=["big_bullets"],
            effects={"explosive_bullets": True, "explosion_radius": 50}
        ),
        Upgrade(
            id="meteor",
            name="Meteor",
            description="Massive bullets that pierce and explode",
            tier=3,
            category="BULLETS",
            tree_id="bullet_size",
            requires=["cannonballs", "explosive_rounds"],
            is_ultimate=True,
            effects={"bullet_size_mult": 1.50, "explosive_bullets": True, "explosion_radius": 80, "pierce_count": 3}
        ),
    ]
}

# ============================================================================
# ELEMENTS - Fire, Ice, Poison
# ============================================================================

FIRE_TREE = {
    "tree_id": "fire",
    "name": "Pyromancy",
    "category": "ELEMENTS",
    "icon": "🔥",
    "upgrades": [
        Upgrade(
            id="ignite",
            name="Ignite",
            description="Bullets inflict Burn (4 dps for 3s)",
            tier=1,
            category="ELEMENTS",
            tree_id="fire",
            effects={"burn_chance": 1.0, "burn_dps": 4, "burn_duration": 3.0}
        ),
        Upgrade(
            id="inferno",
            name="Inferno",
            description="Burn damage +50%, spreads to nearby enemies",
            tier=2,
            category="ELEMENTS",
            tree_id="fire",
            requires=["ignite"],
            effects={"burn_dps_mult": 1.50, "burn_spread": True}
        ),
        Upgrade(
            id="explosion",
            name="Explosion",
            description="Burning enemies explode on death",
            tier=2,
            category="ELEMENTS",
            tree_id="fire",
            requires=["ignite"],
            effects={"burn_explosion": True, "explosion_damage": 30}
        ),
        Upgrade(
            id="hellfire",
            name="Hellfire",
            description="Burn deals 10 dps, explosions chain to 3 enemies",
            tier=3,
            category="ELEMENTS",
            tree_id="fire",
            requires=["inferno", "explosion"],
            is_ultimate=True,
            effects={"burn_dps": 10, "burn_chain_explosions": 3}
        ),
    ]
}

ICE_TREE = {
    "tree_id": "ice",
    "name": "Cryomancy",
    "category": "ELEMENTS",
    "icon": "❄️",
    "upgrades": [
        Upgrade(
            id="chill",
            name="Chill",
            description="Bullets slow enemies by 40% for 2s",
            tier=1,
            category="ELEMENTS",
            tree_id="ice",
            effects={"freeze_chance": 1.0, "slow_amount": 0.40, "freeze_duration": 2.0}
        ),
        Upgrade(
            id="frostbite",
            name="Frostbite",
            description="Frozen enemies take +30% damage",
            tier=2,
            category="ELEMENTS",
            tree_id="ice",
            requires=["chill"],
            effects={"frozen_damage_bonus": 0.30}
        ),
        Upgrade(
            id="shatter",
            name="Shatter",
            description="Frozen enemies shatter on death, damaging nearby",
            tier=2,
            category="ELEMENTS",
            tree_id="ice",
            requires=["chill"],
            effects={"shatter_on_death": True, "shatter_damage": 25}
        ),
        Upgrade(
            id="absolute_zero",
            name="Absolute Zero",
            description="Enemies freeze solid, take 2x damage, shatter chains",
            tier=3,
            category="ELEMENTS",
            tree_id="ice",
            requires=["frostbite", "shatter"],
            is_ultimate=True,
            effects={"deep_freeze": True, "frozen_damage_bonus": 1.0, "shatter_chain": 3}
        ),
    ]
}

POISON_TREE = {
    "tree_id": "poison",
    "name": "Toxicology",
    "category": "ELEMENTS",
    "icon": "💜",
    "upgrades": [
        Upgrade(
            id="venom",
            name="Venom",
            description="Bullets inflict Poison (3 dps for 5s)",
            tier=1,
            category="ELEMENTS",
            tree_id="poison",
            effects={"poison_chance": 1.0, "poison_dps": 3, "poison_duration": 5.0}
        ),
        Upgrade(
            id="plague",
            name="Plague",
            description="Poison spreads to nearby enemies",
            tier=2,
            category="ELEMENTS",
            tree_id="poison",
            requires=["venom"],
            effects={"poison_spread": True, "spread_radius": 80}
        ),
        Upgrade(
            id="necrosis",
            name="Necrosis",
            description="Poisoned enemies deal -30% damage",
            tier=2,
            category="ELEMENTS",
            tree_id="poison",
            requires=["venom"],
            effects={"poison_weaken": 0.30}
        ),
        Upgrade(
            id="pandemic",
            name="Pandemic",
            description="Poison deals 8 dps, infinite spread, enemies explode",
            tier=3,
            category="ELEMENTS",
            tree_id="poison",
            requires=["plague", "necrosis"],
            is_ultimate=True,
            effects={"poison_dps": 8, "poison_infinite_spread": True, "poison_death_explosion": True}
        ),
    ]
}

# ============================================================================
# AURA ORBS - Orbiting damage orbs
# ============================================================================

ORBS_TREE = {
    "tree_id": "orbs",
    "name": "Aura Orbs",
    "category": "ORBS",
    "icon": "⚪",
    "upgrades": [
        Upgrade(
            id="orbit",
            name="Orbit",
            description="2 orbs orbit you, dealing damage on contact",
            tier=1,
            category="ORBS",
            tree_id="orbs",
            effects={"orb_count": 2, "orb_damage": 15, "orb_radius": 200}
        ),
        Upgrade(
            id="trinity",
            name="Trinity",
            description="3 orbs total, faster rotation",
            tier=2,
            category="ORBS",
            tree_id="orbs",
            requires=["orbit"],
            effects={"orb_count": 3, "orb_speed_mult": 1.50}
        ),
        Upgrade(
            id="quad_orbs",
            name="Quad Orbs",
            description="4 orbs, increased damage",
            tier=2,
            category="ORBS",
            tree_id="orbs",
            requires=["orbit"],
            effects={"orb_count": 4, "orb_damage_mult": 1.30}
        ),
        Upgrade(
            id="octo_orbs",
            name="Octo Orbs",
            description="8 orbs surrounding you, 2x rotation speed",
            tier=3,
            category="ORBS",
            tree_id="orbs",
            requires=["trinity", "quad_orbs"],
            is_ultimate=True,
            effects={"orb_count": 8, "orb_speed_mult": 2.0, "orb_damage_mult": 1.50}
        ),
    ]
}

ELEMENTAL_ORBS_TREE = {
    "tree_id": "elemental_orbs",
    "name": "Elemental Orbs",
    "category": "ORBS",
    "icon": "🔮",
    "upgrades": [
        Upgrade(
            id="fire_orb",
            name="Fire Orb",
            description="Orbs inflict Burn on contact",
            tier=1,
            category="ORBS",
            tree_id="elemental_orbs",
            requires=["orbit"],
            effects={"orb_burn": True, "orb_burn_dps": 5}
        ),
        Upgrade(
            id="ice_orb",
            name="Ice Orb",
            description="Orbs slow enemies on contact",
            tier=2,
            category="ORBS",
            tree_id="elemental_orbs",
            requires=["fire_orb"],
            effects={"orb_freeze": True, "orb_slow": 0.50}
        ),
        Upgrade(
            id="poison_orb",
            name="Poison Orb",
            description="Orbs inflict Poison on contact",
            tier=2,
            category="ORBS",
            tree_id="elemental_orbs",
            requires=["fire_orb"],
            effects={"orb_poison": True, "orb_poison_dps": 4}
        ),
        Upgrade(
            id="chaos_orbs",
            name="Chaos Orbs",
            description="Orbs apply all elements, leave damaging trail",
            tier=3,
            category="ORBS",
            tree_id="elemental_orbs",
            requires=["ice_orb", "poison_orb"],
            is_ultimate=True,
            effects={"orb_all_elements": True, "orb_trail": True, "orb_trail_damage": 8}
        ),
    ]
}

# ============================================================================
# DEFENSE - Shield, HP, Revive, Speed
# ============================================================================

SHIELD_TREE = {
    "tree_id": "shield",
    "name": "Shield",
    "category": "DEFENSE",
    "icon": "🛡️",
    "upgrades": [
        Upgrade(
            id="barrier",
            name="Barrier",
            description="Orbiting shield blocks enemy projectiles",
            tier=1,
            category="DEFENSE",
            tree_id="shield",
            effects={"shield_active": True, "shield_segments": 1, "shield_radius": 50}
        ),
        Upgrade(
            id="reinforced",
            name="Reinforced",
            description="Shield blocks 2 more hits before breaking",
            tier=2,
            category="DEFENSE",
            tree_id="shield",
            requires=["barrier"],
            effects={"shield_hp": 2}
        ),
        Upgrade(
            id="reflective",
            name="Reflective",
            description="Shield reflects projectiles back at enemies",
            tier=2,
            category="DEFENSE",
            tree_id="shield",
            requires=["barrier"],
            effects={"shield_reflect": True}
        ),
        Upgrade(
            id="fortress",
            name="Fortress",
            description="3 shield segments, auto-regenerate, reflect damage",
            tier=3,
            category="DEFENSE",
            tree_id="shield",
            requires=["reinforced", "reflective"],
            is_ultimate=True,
            effects={"shield_segments": 3, "shield_regen": True, "shield_regen_time": 10.0}
        ),
    ]
}

HEALTH_TREE = {
    "tree_id": "health",
    "name": "Health",
    "category": "DEFENSE",
    "icon": "❤️",
    "upgrades": [
        Upgrade(
            id="vitality",
            name="Vitality",
            description="+2 Max HP",
            tier=1,
            category="DEFENSE",
            tree_id="health",
            effects={"max_hp": 2}
        ),
        Upgrade(
            id="regeneration",
            name="Regeneration",
            description="Regenerate 1 HP every 30 seconds",
            tier=2,
            category="DEFENSE",
            tree_id="health",
            requires=["vitality"],
            effects={"hp_regen": True, "regen_interval": 30.0}
        ),
        Upgrade(
            id="second_wind",
            name="Second Wind",
            description="Revive once with 1 HP when killed",
            tier=2,
            category="DEFENSE",
            tree_id="health",
            requires=["vitality"],
            effects={"revive": 1}
        ),
        Upgrade(
            id="immortal",
            name="Immortal",
            description="+3 HP, revive with full HP, constant regen",
            tier=3,
            category="DEFENSE",
            tree_id="health",
            requires=["regeneration", "second_wind"],
            is_ultimate=True,
            effects={"max_hp": 3, "revive": 1, "revive_full_hp": True, "regen_interval": 15.0}
        ),
    ]
}

SPEED_BOOST_TREE = {
    "tree_id": "speed_boost",
    "name": "Speed",
    "category": "DEFENSE",
    "icon": "🏃",
    "upgrades": [
        Upgrade(
            id="swift",
            name="Swift",
            description="Move speed +25%",
            tier=1,
            category="DEFENSE",
            tree_id="speed_boost",
            effects={"move_speed_mult": 1.25}
        ),
        Upgrade(
            id="dash",
            name="Dash",
            description="Press SHIFT to dash, 3s cooldown",
            tier=2,
            category="DEFENSE",
            tree_id="speed_boost",
            requires=["swift"],
            effects={"dash_ability": True, "dash_cooldown": 3.0}
        ),
        Upgrade(
            id="dodge",
            name="Dodge",
            description="15% chance to dodge attacks",
            tier=2,
            category="DEFENSE",
            tree_id="speed_boost",
            requires=["swift"],
            effects={"dodge_chance": 0.15}
        ),
        Upgrade(
            id="phantom",
            name="Phantom",
            description="50% speed, 25% dodge, dash leaves damaging trail",
            tier=3,
            category="DEFENSE",
            tree_id="speed_boost",
            requires=["dash", "dodge"],
            is_ultimate=True,
            effects={"move_speed_mult": 1.50, "dodge_chance": 0.25, "dash_trail": True}
        ),
    ]
}

# ============================================================================
# VISION - Glare effect (full screen flash)
# ============================================================================

VISION_TREE = {
    "tree_id": "vision",
    "name": "Vision",
    "category": "VISION",
    "icon": "👁️",
    "upgrades": [
        Upgrade(
            id="glare",
            name="Glare",
            description="Screen flashes every 5s, damaging all visible enemies",
            tier=1,
            category="VISION",
            tree_id="vision",
            effects={"glare_active": True, "glare_interval": 5.0, "glare_damage": 20}
        ),
        Upgrade(
            id="piercing_gaze",
            name="Piercing Gaze",
            description="Glare damage +50%, slows enemies",
            tier=2,
            category="VISION",
            tree_id="vision",
            requires=["glare"],
            effects={"glare_damage_mult": 1.50, "glare_slow": 0.40}
        ),
        Upgrade(
            id="blinding",
            name="Blinding",
            description="Glare stuns enemies for 1s",
            tier=2,
            category="VISION",
            tree_id="vision",
            requires=["glare"],
            effects={"glare_stun": True, "glare_stun_duration": 1.0}
        ),
        Upgrade(
            id="death_stare",
            name="Death Stare",
            description="Glare every 3s, executes enemies below 30% HP",
            tier=3,
            category="VISION",
            tree_id="vision",
            requires=["piercing_gaze", "blinding"],
            is_ultimate=True,
            effects={"glare_interval": 3.0, "glare_execute": 0.30, "glare_damage_mult": 2.0}
        ),
    ]
}

# ============================================================================
# SUMMONS - Ghost, Dragon, Lens
# ============================================================================

DRONE_TREE = {
    "tree_id": "drone",
    "name": "Combat Drones",
    "category": "SUMMONS",
    "icon": "🤖",
    "upgrades": [
        Upgrade(
            id="drone_deploy",
            name="Drone Deploy",
            description="Summon a combat drone that orbits and shoots enemies",
            tier=1,
            category="SUMMONS",
            tree_id="drone",
            effects={"drone_count": 1, "drone_damage": 10}
        ),
        Upgrade(
            id="drone_piercing",
            name="Piercing Shots",
            description="Drone bullets pierce enemies, +1 drone",
            tier=2,
            category="SUMMONS",
            tree_id="drone",
            requires=["drone_deploy"],
            effects={"drone_count": 1, "drone_pierce": True}
        ),
        Upgrade(
            id="drone_elemental",
            name="Elemental Drones",
            description="Drones apply Burn and Poison on hit",
            tier=2,
            category="SUMMONS",
            tree_id="drone",
            requires=["drone_deploy"],
            effects={"drone_burn": True, "drone_poison": True}
        ),
        Upgrade(
            id="drone_swarm",
            name="Drone Swarm",
            description="4 drones total, rapid fire, all elements",
            tier=3,
            category="SUMMONS",
            tree_id="drone",
            requires=["drone_piercing", "drone_elemental"],
            is_ultimate=True,
            effects={"drone_count": 4, "drone_rapid_fire": True, "drone_all_elements": True}
        ),
    ]
}

# New Ghost tree - phases through enemies and damages them
GHOST_TREE = {
    "tree_id": "ghost",
    "name": "Phantom",
    "category": "SUMMONS",
    "icon": "👻",
    "upgrades": [
        Upgrade(
            id="phantom",
            name="Phantom",
            description="Summon a ghost that phases through enemies, damaging them",
            tier=1,
            category="SUMMONS",
            tree_id="ghost",
            effects={"phantom_count": 1, "phantom_damage": 15}
        ),
        Upgrade(
            id="phantom_chill",
            name="Spectral Chill",
            description="Phantoms slow enemies they pass through, +1 phantom",
            tier=2,
            category="SUMMONS",
            tree_id="ghost",
            requires=["phantom"],
            effects={"phantom_count": 1, "phantom_slow": True}
        ),
        Upgrade(
            id="phantom_drain",
            name="Soul Drain",
            description="Phantoms steal HP from enemies they pass through",
            tier=2,
            category="SUMMONS",
            tree_id="ghost",
            requires=["phantom"],
            effects={"phantom_lifesteal": True, "phantom_damage": 10}
        ),
        Upgrade(
            id="phantom_army",
            name="Phantom Army",
            description="4 phantoms that phase rapidly, heal you on contact",
            tier=3,
            category="SUMMONS",
            tree_id="ghost",
            requires=["phantom_chill", "phantom_drain"],
            is_ultimate=True,
            effects={"phantom_count": 4, "phantom_speed": 2.0, "phantom_lifesteal": True}
        ),
    ]
}

DRAGON_TREE = {
    "tree_id": "dragon",
    "name": "Dragon",
    "category": "SUMMONS",
    "icon": "🐉",
    "upgrades": [
        Upgrade(
            id="dragon_egg",
            name="Dragon Egg",
            description="After 2 minutes, a dragon hatches and fights for you",
            tier=1,
            category="SUMMONS",
            tree_id="dragon",
            effects={"dragon_egg": True, "dragon_hatch_time": 120.0, "dragon_damage": 25}
        ),
        Upgrade(
            id="fire_breath",
            name="Fire Breath",
            description="Dragon breathes fire, burning enemies",
            tier=2,
            category="SUMMONS",
            tree_id="dragon",
            requires=["dragon_egg"],
            effects={"dragon_fire_breath": True, "dragon_burn_dps": 8}
        ),
        Upgrade(
            id="dragon_growth",
            name="Dragon Growth",
            description="Dragon grows stronger over time",
            tier=2,
            category="SUMMONS",
            tree_id="dragon",
            requires=["dragon_egg"],
            effects={"dragon_growth": True, "dragon_damage_growth": 5}
        ),
        Upgrade(
            id="elder_dragon",
            name="Elder Dragon",
            description="Summon a massive elder dragon that breathes fire dealing 60 damage",
            tier=3,
            category="SUMMONS",
            tree_id="dragon",
            requires=["fire_breath", "dragon_growth"],
            is_ultimate=True,
            effects={"elder_dragon": True, "dragon_egg": True, "dragon_active": True, "dragon_hatch_time": 0.0, "dragon_damage": 60, "dragon_size": 2.0}
        ),
    ]
}

LENS_TREE = {
    "tree_id": "lens",
    "name": "Magic Lens",
    "category": "SUMMONS",
    "icon": "🔮",
    "upgrades": [
        Upgrade(
            id="lens",
            name="Magic Lens",
            description="Orbiting lens doubles your bullets (2x)",
            tier=1,
            category="SUMMONS",
            tree_id="lens",
            effects={"lens_count": 1, "lens_bullet_mult": 2}
        ),
        Upgrade(
            id="amplifier",
            name="Amplifier",
            description="Lens triples bullets (3x) + 30% damage",
            tier=2,
            category="SUMMONS",
            tree_id="lens",
            requires=["lens"],
            effects={"lens_bullet_mult": 3, "damage_mult": 1.3}
        ),
        Upgrade(
            id="prism",
            name="Prism",
            description="2 lenses orbit you, 3x bullets",
            tier=2,
            category="SUMMONS",
            tree_id="lens",
            requires=["lens"],
            effects={"lens_count": 2, "lens_bullet_mult": 3}
        ),
        Upgrade(
            id="magnifying_lens",
            name="Magnifying Lens",
            description="Bullets grow 10% larger when passing through lens",
            tier=2,
            category="SUMMONS",
            tree_id="lens",
            requires=["lens"],
            effects={"lens_enlarge": 1.10}
        ),
        Upgrade(
            id="kaleidoscope",
            name="Kaleidoscope",
            description="3 lenses, 5x bullets, +50% damage, +15% bullet size",
            tier=3,
            category="SUMMONS",
            tree_id="lens",
            requires=["amplifier", "prism", "magnifying_lens"],
            is_ultimate=True,
            effects={"lens_count": 3, "lens_bullet_mult": 5, "damage_mult": 1.5, "lens_enlarge": 1.15}
        ),
    ]
}

# ============================================================================
# EVOLUTIONS - Special powerful upgrades
# ============================================================================

EVOLUTIONS = {
    "guided_shots": {
        "id": "guided_shots",
        "name": "Guided Missiles",
        "description": "Bullets home in on enemies, seeking targets automatically",
        "category": "EVOLUTION",
        "effects": {"homing_bullets": True, "homing_strength": 0.15},
        "requires_upgrades": ["sniper", "velocity"]
    },
    "lightning_storm": {
        "id": "lightning_storm", 
        "name": "Lightning Storm",
        "description": "Lightning strikes random enemies every 2s, chains to 3 targets",
        "category": "EVOLUTION",
        "effects": {"lightning_active": True, "lightning_interval": 2.0, "lightning_damage": 35, "lightning_chain": 3},
        "requires_upgrades": ["rapid_fire", "power_shot"]
    },
    "deca_cannon": {
        "id": "deca_cannon",
        "name": "Deca Cannon",
        "description": "10 cannons firing in all directions with increased damage",
        "category": "EVOLUTION",
        "effects": {"cannon_count": 10, "damage_mult": 1.30},
        "requires_upgrades": ["octo_cannons"]
    },
    "orb_storm": {
        "id": "orb_storm",
        "name": "Orb Storm",
        "description": "12 orbs with 3x rotation speed, pulsing damage waves",
        "category": "EVOLUTION",
        "effects": {"orb_count": 12, "orb_speed_mult": 3.0, "orb_pulse": True},
        "requires_upgrades": ["octo_orbs"]
    },
    "summon_army": {
        "id": "summon_army",
        "name": "Summon Army",
        "description": "Double all summon counts, +50% summon damage",
        "category": "EVOLUTION",
        "effects": {"summon_count_mult": 2, "summon_damage_mult": 1.50},
        "requires_upgrades": ["phantom_army", "elder_dragon"]
    },
}

# ============================================================================
# BASE STATS - Movement, Ammo, etc
# ============================================================================

MOBILITY_TREE = {
    "tree_id": "mobility",
    "name": "Mobility",
    "category": "PLAYER",
    "icon": "🏃",
    "upgrades": [
        Upgrade(
            id="swift_feet",
            name="Swift Feet",
            description="Movement speed +20%",
            tier=1,
            category="PLAYER",
            tree_id="mobility",
            effects={"move_speed_mult": 1.20}
        ),
        Upgrade(
            id="agility",
            name="Agility",
            description="Movement speed +15%, boost recharge +25%",
            tier=2,
            category="PLAYER",
            tree_id="mobility",
            requires=["swift_feet"],
            effects={"move_speed_mult": 1.15, "boost_recharge_mult": 1.25}
        ),
        Upgrade(
            id="supersonic",
            name="Supersonic",
            description="Movement speed +25%, become partially invulnerable while boosting",
            tier=3,
            category="PLAYER",
            tree_id="mobility",
            requires=["agility"],
            is_ultimate=True,
            effects={"move_speed_mult": 1.25, "boost_invuln": True}
        ),
    ]
}

AMMO_TREE = {
    "tree_id": "ammo",
    "name": "Ammunition",
    "category": "PLAYER",
    "icon": "🎯",
    "upgrades": [
        Upgrade(
            id="extended_mag",
            name="Extended Mag",
            description="Magazine size +4",
            tier=1,
            category="PLAYER",
            tree_id="ammo",
            effects={"mag_size_bonus": 4}
        ),
        Upgrade(
            id="quick_reload",
            name="Quick Reload",
            description="Reload speed +30%, mag size +2",
            tier=2,
            category="PLAYER",
            tree_id="ammo",
            requires=["extended_mag"],
            effects={"reload_speed_mult": 1.30, "mag_size_bonus": 2}
        ),
        Upgrade(
            id="bottomless",
            name="Bottomless Clip",
            description="Magazine size +8, 15% chance to not consume ammo",
            tier=3,
            category="PLAYER",
            tree_id="ammo",
            requires=["quick_reload"],
            is_ultimate=True,
            effects={"mag_size_bonus": 8, "ammo_save_chance": 0.15}
        ),
    ]
}

# ============================================================================
# AGGREGATE ALL TREES
# ============================================================================

ALL_TREES = [
    # Cannons
    CANNONS_TREE,
    # Bullet properties
    DAMAGE_TREE,
    SPEED_TREE,
    FIRE_RATE_TREE,
    BULLET_SIZE_TREE,
    # Elements
    FIRE_TREE,
    ICE_TREE,
    POISON_TREE,
    # Orbs
    ORBS_TREE,
    ELEMENTAL_ORBS_TREE,
    # Defense
    SHIELD_TREE,
    HEALTH_TREE,
    SPEED_BOOST_TREE,
    # Vision
    VISION_TREE,
    # Summons
    DRONE_TREE,
    GHOST_TREE,
    DRAGON_TREE,
    LENS_TREE,
    # Player base stats
    MOBILITY_TREE,
    AMMO_TREE,
]

# Build lookup dictionaries
TREES_BY_ID = {tree["tree_id"]: tree for tree in ALL_TREES}
UPGRADES_BY_ID = {}
for tree in ALL_TREES:
    for upgrade in tree["upgrades"]:
        UPGRADES_BY_ID[upgrade.id] = upgrade

# Categories for UI organization
CATEGORIES = {
    "CANNONS": ["cannons"],
    "BULLETS": ["damage", "bullet_speed", "fire_rate", "bullet_size"],
    "ELEMENTS": ["fire", "ice", "poison"],
    "ORBS": ["orbs", "elemental_orbs"],
    "DEFENSE": ["shield", "health", "speed_boost"],
    "VISION": ["vision"],
    "SUMMONS": ["ghost", "dragon", "lens"],
}

def get_tier3_upgrades():
    """Get all tier 3 upgrades for test mode selection."""
    tier3 = []
    for tree in ALL_TREES:
        for upgrade in tree["upgrades"]:
            if upgrade.tier == 3:
                tier3.append(upgrade)
    return tier3

def get_all_effects_for_tier3(tier3_upgrade):
    """Get combined effects of tier 1, 2, and 3 when selecting a tier 3."""
    tree = TREES_BY_ID.get(tier3_upgrade.tree_id)
    if not tree:
        return tier3_upgrade.effects.copy()
    
    combined = {}
    for upgrade in tree["upgrades"]:
        for key, value in upgrade.effects.items():
            if key in combined:
                # Combine effects intelligently
                if isinstance(value, bool):
                    combined[key] = combined[key] or value
                elif isinstance(value, (int, float)):
                    if "mult" in key:
                        # Multiplicative stacking
                        combined[key] = combined[key] * value
                    elif "count" in key or "damage" in key or "dps" in key:
                        # Take the higher value
                        combined[key] = max(combined[key], value)
                    else:
                        # Additive
                        combined[key] = combined[key] + value
                else:
                    combined[key] = value
            else:
                combined[key] = value
    return combined

def get_available_evolutions(owned_upgrades: list):
    """Check which evolutions are available based on owned upgrades."""
    available = []
    for evo_id, evo in EVOLUTIONS.items():
        required = evo.get("requires_upgrades", [])
        if all(req in owned_upgrades for req in required):
            available.append(evo)
    return available
