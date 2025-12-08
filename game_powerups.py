"""
Game Powerups - Bridge between old powerup system and new Upgrade Trees
=========================================================================
Maintains backward compatibility while integrating with the new 20MTD-style 
upgrade tree system from upgrade_trees.py and upgrade_system.py.
"""

from game_constants import clamp

# Try to import new upgrade system
try:
    from upgrade_trees import UPGRADES_BY_ID, ALL_TREES, get_available_upgrades as get_tree_upgrades
    from upgrade_system import UpgradeManager
    NEW_SYSTEM_AVAILABLE = True
except ImportError:
    NEW_SYSTEM_AVAILABLE = False

# ============================================================================
# LEGACY POWERUP DEFINITIONS (For backward compatibility and dev mode)
# ============================================================================

POWERUPS = [
    # bullet count ramp
    "bullet_1",
    "bullet_2",
    "bullet_3",
    # fire line
    "fire_burn",
    "fire_sear",
    # movement/utility
    "move_1",
    "move_2",
    "mag_1",
    "mag_2",
    "vision_1",
    "vision_2",
    "hp_up",
    "revive",
    # penetration line
    "pierce_on_kill",
    "pierce_full",
    # extra effects
    "aura_1",
    "aura_2",
    "aura_3",
    "aura_elements",
    "minion_1",
    "minion_2",
    # NEW: Ice tree starters
    "ice_1",
    "ice_2",
    # NEW: Poison/Curse
    "poison_1",
    "curse_1",
    # NEW: Lightning
    "lightning_1",
    # NEW: Summons
    "ghost_1",
    "dragon_egg",
    "magic_lens",
    "magic_scythe",
    # NEW: Defense
    "shield_1",
    "dodge_1",
    "soul_heart_1",
]


EVOLUTIONS = [
    "laser_overclock",
    "burning_chain",
    "guided_shots",
    "aura_overload",
    "minion_legion",
    "pierce_mastery",
    # NEW: Ultimate evolutions mapped from upgrade trees
    "assassin",           # Fast Bullets ultimate
    "annihilation",       # Bullet Damage ultimate
    "bullet_hell",        # Fire Rate ultimate
    "storm",              # Multi Shots ultimate
    "siege",              # Reload ultimate
    "dragon_bond",        # Dragon ultimate
    "ghost_legion",       # Ghost ultimate
    "supernova",          # Magic Lens ultimate
    "soul_harvest",       # Magic Scythe ultimate
    "impaler",            # Magic Spear ultimate
    "army",               # Trainer ultimate
    "bloodlust",          # Frenzy ultimate
    "chain_lightning",    # Electromancy ultimate
    "shatter",            # Ice ultimate
    "inferno",            # Pyromancy ultimate
    "ritual",             # Dark Arts ultimate
    "divine_smite",       # Holy Arts ultimate
    "immortal",           # Health ultimate
    "bastion",            # Shield ultimate
    "phantom",            # Dodge ultimate
    "soul_link",          # Soul Heart ultimate
    "excitement",         # Magnet XP ultimate
    "in_the_wind",        # Speed Boost ultimate
    "oracle",             # Vision ultimate
    "tornado",            # Aero ultimate
]


# ============================================================================
# MAPPING: Legacy powerup IDs to new upgrade tree IDs
# ============================================================================

LEGACY_TO_TREE_MAP = {
    # Bullet/Damage
    "bullet_1": "double_shot",        # Multi Shots T1
    "bullet_2": "triple_shot",        # Multi Shots T2
    "bullet_3": "quad_shot",          # Multi Shots T2
    "fire_burn": "kindle",            # Pyromancy T1
    "fire_sear": "ignite",            # Pyromancy T2
    # Movement
    "move_1": "quick_step",           # Speed Boost T1
    "move_2": "sprint",               # Speed Boost T2
    # Magazine
    "mag_1": "extended_mag",          # Reload T1
    "mag_2": "rapid_reload",          # Reload T2
    # Vision/Magnet
    "vision_1": "magnetism",          # Magnet XP T1
    "vision_2": "attraction",         # Magnet XP T2
    # Pierce
    "pierce_on_kill": "penetration",  # Fast Bullets T2
    "pierce_full": "assassin",        # Fast Bullets T3
    # Aura → Maps to Electromancy
    "aura_1": "static",               # Electromancy T1
    "aura_2": "shock",                # Electromancy T2
    "aura_3": "electro_bug",          # Electromancy T2
    # Minions → Trainer
    "minion_1": "companion",          # Trainer T1
    "minion_2": "pack",               # Trainer T2
    # Ice
    "ice_1": "frost",                 # Ice T1
    "ice_2": "freeze",                # Ice T2
    # Poison/Curse
    "poison_1": "curse",              # Dark Arts T1
    "curse_1": "hex",                 # Dark Arts T2
    # Lightning
    "lightning_1": "static",          # Electromancy T1
    # Summons
    "ghost_1": "spirit",              # Ghost Friend T1
    "dragon_egg": "egg",              # Dragon T1
    "magic_lens": "lens",             # Magic Lens T1
    "magic_scythe": "scythe",         # Magic Scythe T1
    # Defense
    "shield_1": "barrier",            # Shield T1
    "dodge_1": "evasion",             # Dodge T1
    "soul_heart_1": "soul_container", # Soul Heart T1
    "hp_up": "vitality",              # Health T1
    "revive": "resilience",           # Health T2
}


# ============================================================================
# AVAILABLE POWERUPS FUNCTION
# ============================================================================

def available_powerups(player):
    """
    Get available powerups for the player.
    Uses new upgrade tree system if available, otherwise falls back to legacy.
    """
    # If player has upgrade_manager, use new system
    upgrade_mgr = getattr(player, "upgrade_manager", None)
    if upgrade_mgr and NEW_SYSTEM_AVAILABLE:
        # Return upgrade IDs from the new tree system
        available = upgrade_mgr.get_available_options(count=10)
        return [u.id for u in available]
    
    # Legacy fallback
    return _legacy_available_powerups(player)


def _legacy_available_powerups(player):
    """Original powerup availability logic."""
    opts = []

    # bullet progression
    if player.bullet_tier < 1:
        opts.append("bullet_1")
    elif player.bullet_tier < 2:
        opts.append("bullet_2")
    elif player.bullet_tier < 3:
        opts.append("bullet_3")

    # fire progression
    if player.fire_tier < 1:
        opts.append("fire_burn")
    elif player.fire_tier < 2:
        opts.append("fire_sear")

    # movement progression
    if player.move_tier < 1:
        opts.append("move_1")
    elif player.move_tier < 2:
        opts.append("move_2")

    # magazine progression
    if player.mag_tier < 1:
        opts.append("mag_1")
    elif player.mag_tier < 2:
        opts.append("mag_2")

    # vision progression
    if player.vision_tier < 1:
        opts.append("vision_1")
    elif player.vision_tier < 2:
        opts.append("vision_2")

    # pierce progression
    if player.pierce_tier < 1:
        opts.append("pierce_on_kill")
    elif player.pierce_tier < 2:
        opts.append("pierce_full")

    # aura progression
    if player.aura_tier < 1:
        opts.append("aura_1")
    elif player.aura_tier < 2:
        opts.append("aura_2")
    elif player.aura_tier < 3:
        opts.append("aura_3")
    elif player.aura_unlocked and not getattr(player, "aura_elemental", False):
        opts.append("aura_elements")

    # minion progression
    if player.minion_tier < 1:
        opts.append("minion_1")
    elif player.minion_tier < 2:
        opts.append("minion_2")

    # hearts can be taken multiple times, but bias to show when not overstacked
    if player.max_hearts < 12:
        opts.append("hp_up")

    # revive limited to one extra
    if player.revives < 1:
        opts.append("revive")

    return opts


# ============================================================================
# APPLY POWERUP FUNCTION
# ============================================================================

def apply_powerup(player, pid: str):
    """
    Apply a powerup to the player.
    First tries the new upgrade tree system, then falls back to legacy.
    """
    # Try new system first
    upgrade_mgr = getattr(player, "upgrade_manager", None)
    if upgrade_mgr and NEW_SYSTEM_AVAILABLE:
        # Check if this is a new tree upgrade ID
        if pid in UPGRADES_BY_ID:
            if upgrade_mgr.apply_upgrade(pid):
                return
        # Check if it's a legacy ID that maps to new system
        elif pid in LEGACY_TO_TREE_MAP:
            new_id = LEGACY_TO_TREE_MAP[pid]
            if new_id in UPGRADES_BY_ID:
                if upgrade_mgr.apply_upgrade(new_id):
                    return
    
    # Fall back to legacy application
    _legacy_apply_powerup(player, pid)


def _legacy_apply_powerup(player, pid: str):
    """Original powerup application logic."""
    if pid == "bullet_1":
        player.bullet_count = max(player.bullet_count, 2)
        player.bullet_tier = max(player.bullet_tier, 1)
    elif pid == "bullet_2":
        player.bullet_count = max(player.bullet_count, 3)
        player.bullet_tier = max(player.bullet_tier, 2)
    elif pid == "bullet_3":
        player.bullet_count = max(player.bullet_count, 5)
        player.bullet_tier = max(player.bullet_tier, 3)
    elif pid == "fire_burn":
        player.bullet_status["burn"] = True
        player.burn_bonus_mult = max(player.burn_bonus_mult, 1.0)
        player.fire_tier = max(player.fire_tier, 1)
    elif pid == "fire_sear":
        player.bullet_status["burn"] = True
        player.burn_bonus_mult = max(player.burn_bonus_mult, 1.4)
        player.burn_sear_bonus = max(player.burn_sear_bonus, 0.25)
        player.fire_tier = max(player.fire_tier, 2)
    elif pid == "move_1":
        player.base_speed *= 1.12
        player.speed = player.base_speed
        player.move_tier = max(player.move_tier, 1)
    elif pid == "move_2":
        player.base_speed *= 1.18
        player.speed = player.base_speed
        player.move_tier = max(player.move_tier, 2)
    elif pid == "mag_1":
        player.mag_size += 4
        player.ammo = player.mag_size
        player.mag_tier = max(player.mag_tier, 1)
    elif pid == "mag_2":
        player.mag_size += 6
        player.reload_time = max(0.7, player.reload_time - 0.25)
        player.ammo = player.mag_size
        player.mag_tier = max(player.mag_tier, 2)
    elif pid == "vision_1":
        player.magnet_range += 40
        player.vision_tier = max(player.vision_tier, 1)
    elif pid == "vision_2":
        player.magnet_range += 80
        player.vision_tier = max(player.vision_tier, 2)
    elif pid == "hp_up":
        player.add_heart_container()
    elif pid == "revive":
        player.revives = max(1, player.revives + 1)
    elif pid == "pierce_on_kill":
        player.pierce_mode = "corpse"
        player.piercing = True
        player.pierce_tier = max(player.pierce_tier, 1)
    elif pid == "pierce_full":
        player.pierce_mode = "full"
        player.piercing = True
        player.pierce_tier = max(player.pierce_tier, 2)
    elif pid == "aura_1":
        player.aura_unlocked = True
        player.aura_tier = max(player.aura_tier, 1)
        player.aura_orb_radius = 200
        player.aura_orb_damage = 18
        player.aura_orb_speed = 1.7
        player.aura_orb_size = 12
        player.aura_orb_elements = ["shock"]
        player.aura_orb_count = max(player.aura_orb_count, 2)
        if hasattr(player, "rebuild_aura_orbs"):
            player.rebuild_aura_orbs()
    elif pid == "aura_2":
        player.aura_unlocked = True
        player.aura_tier = max(player.aura_tier, 2)
        player.aura_orb_radius = 220
        player.aura_orb_damage = max(player.aura_orb_damage, 22)
        player.aura_orb_speed = max(player.aura_orb_speed, 1.9)
        player.aura_orb_size = 12
        player.aura_orb_elements = ["shock", "fire"]
        player.aura_orb_count = max(player.aura_orb_count, 4)
        if hasattr(player, "rebuild_aura_orbs"):
            player.rebuild_aura_orbs()
    elif pid == "aura_3":
        player.aura_unlocked = True
        player.aura_tier = max(player.aura_tier, 3)
        player.aura_orb_radius = 240
        player.aura_orb_damage = max(player.aura_orb_damage, 28)
        player.aura_orb_speed = max(player.aura_orb_speed, 2.2)
        player.aura_orb_size = 13
        player.aura_orb_elements = ["shock", "fire", "ice", "poison"]
        player.aura_orb_count = max(player.aura_orb_count, 6)
        if hasattr(player, "rebuild_aura_orbs"):
            player.rebuild_aura_orbs()
    elif pid == "aura_elements":
        player.aura_unlocked = True
        player.aura_elemental = True
        player.aura_orb_elements = ["fire", "ice", "poison"]
        player.aura_orb_damage = max(player.aura_orb_damage, 32)
        if hasattr(player, "rebuild_aura_orbs"):
            player.rebuild_aura_orbs()
    elif pid == "minion_1":
        player.minion_count = max(player.minion_count, 1)
        player.minion_tier = max(player.minion_tier, 1)
    elif pid == "minion_2":
        player.minion_count = max(player.minion_count, 3)
        player.minion_tier = max(player.minion_tier, 2)
    # NEW: Ice powers
    elif pid == "ice_1":
        player.bullet_status["ice"] = True
        player.freeze_chance = 0.15
    elif pid == "ice_2":
        player.bullet_status["ice"] = True
        player.freeze_chance = 0.25
        player.freeze_duration = 1.5
    # NEW: Curse/Poison
    elif pid == "poison_1":
        player.bullet_status["poison"] = True
        player.poison_bonus_mult = 1.0
    elif pid == "curse_1":
        player.curse_chance = 0.20
        player.curse_delay = 3.0
        player.curse_bonus_damage = 0.30
    # NEW: Lightning
    elif pid == "lightning_1":
        player.lightning_interval = 8
        player.lightning_damage = 22
    # NEW: Summons
    elif pid == "ghost_1":
        player.ghost_count = max(player.ghost_count, 1)
    elif pid == "dragon_egg":
        player.has_dragon_egg = True
        player.dragon_hatch_time = 180.0
    elif pid == "magic_lens":
        player.lens_count = max(player.lens_count, 1)
    elif pid == "magic_scythe":
        player.scythe_count = max(player.scythe_count, 1)
        player.scythe_damage = 40
    # NEW: Defense
    elif pid == "shield_1":
        player.shield_max_hits = 2
        player.shield_hits = 2
        player.shield_regen_time = 120.0
    elif pid == "dodge_1":
        player.dodge_chance = 0.08
    elif pid == "soul_heart_1":
        player.soul_hearts = max(player.soul_hearts, 1)
        player.soul_heart_max = 3


# ============================================================================
# APPLY EVOLUTION FUNCTION
# ============================================================================

def apply_evolution(player, eid: str):
    """
    Apply an evolution to the player.
    Evolutions are ultimate-tier upgrades from the tree system.
    """
    # Try new system first for tree ultimates
    upgrade_mgr = getattr(player, "upgrade_manager", None)
    if upgrade_mgr and NEW_SYSTEM_AVAILABLE:
        if eid in UPGRADES_BY_ID:
            if upgrade_mgr.apply_upgrade(eid):
                return
    
    # Fall back to legacy evolutions
    _legacy_apply_evolution(player, eid)


def _legacy_apply_evolution(player, eid: str):
    """Original evolution application logic."""
    if eid == "laser_overclock":
        player.laser_duration += 2.0
        player.laser_cooldown_max = max(10.0, player.laser_cooldown_max - 6.0)
    elif eid == "burning_chain":
        player.bullet_status["burn"] = True
        player.burn_chain = True
    elif eid == "guided_shots":
        player.guided_shots = True
    elif eid == "aura_overload":
        player.aura_orb_radius += 30
        player.aura_orb_damage *= 1.25
        player.aura_orb_speed += 0.5
        player.aura_orb_size = max(player.aura_orb_size, 14)
        player.aura_orb_count = max(player.aura_orb_count, (player.aura_tier or 1) + 1)
        if hasattr(player, "rebuild_aura_orbs"):
            player.rebuild_aura_orbs()
    elif eid == "minion_legion":
        player.minion_count += 2
        player.minion_damage_mult *= 1.35
    elif eid == "pierce_mastery":
        player.pierce_mode = "full"
        player.piercing = True
        player.bullet_speed *= 1.2


# ============================================================================
# NAME AND DESCRIPTION FUNCTIONS
# ============================================================================

def powerup_name(pid: str) -> str:
    """Get display name for a powerup ID."""
    # Try new system first
    if NEW_SYSTEM_AVAILABLE and pid in UPGRADES_BY_ID:
        return UPGRADES_BY_ID[pid].name
    
    # Complete names dictionary (legacy + all tree upgrades)
    names = {
        # === LEGACY POWERUPS ===
        "bullet_1": "Shooter I",
        "bullet_2": "Shooter II",
        "bullet_3": "Shooter III",
        "fire_burn": "Inferno I",
        "fire_sear": "Inferno II",
        "move_1": "Thrusters I",
        "move_2": "Thrusters II",
        "mag_1": "Mag Extension",
        "mag_2": "Rapid Reload",
        "vision_1": "Wide Vision",
        "vision_2": "Far Reach",
        "hp_up": "Extra Heart",
        "revive": "Revive Core",
        "pierce_on_kill": "Pierce (On Kill)",
        "pierce_full": "Pierce (Always)",
        "aura_1": "Static Field I",
        "aura_2": "Static Field II",
        "aura_3": "Static Field III",
        "aura_elements": "Elemental Field",
        "minion_1": "Drone Buddy",
        "minion_2": "Drone Wing",
        "ice_1": "Frost Touch",
        "ice_2": "Deep Freeze",
        "poison_1": "Toxic Rounds",
        "curse_1": "Hex Mark",
        "lightning_1": "Static Charge",
        "ghost_1": "Ghost Friend",
        "dragon_egg": "Dragon Egg",
        "magic_lens": "Magic Lens",
        "magic_scythe": "Magic Scythe",
        "shield_1": "Energy Shield",
        "dodge_1": "Quick Reflexes",
        "soul_heart_1": "Soul Container",
        
        # === DAMAGE & GUNS TREES ===
        # Fast Bullets Tree
        "take_aim": "Take Aim",
        "penetration": "Penetration",
        "sniper": "Sniper",
        "assassin": "Assassin",
        # Bullet Damage Tree
        "power_shot": "Power Shot",
        "big_shot": "Big Shot",
        "splinter": "Splinter",
        "reaper_rounds": "Reaper Rounds",
        # Fire Rate Tree
        "rapid_fire": "Rapid Fire",
        "light_bullets": "Light Bullets",
        "rubber_bullets": "Rubber Bullets",
        "siege": "Siege",
        # Multi Shots Tree
        "double_shot": "Double Shot",
        "fan_fire": "Fan Fire",
        "split_fire": "Split Fire",
        "fusillade": "Fusillade",
        # Reload Tree
        "quick_hands": "Quick Hands",
        "armed_and_ready": "Armed and Ready",
        "fresh_clip": "Fresh Clip",
        "kill_clip": "Kill Clip",
        
        # === SUMMONS TREES ===
        # Dragon Tree
        "dragon_egg": "Dragon Egg",
        "aged_dragon": "Aged Dragon",
        "trained_dragon": "Trained Dragon",
        "dragon_bond": "Dragon Bond",
        # Ghost Friend Tree
        "ghost_friend": "Ghost Friend",
        "best_friends": "Best Friends",
        "ghost_wizard": "Ghost Wizard",
        "vengeful_ghost": "Vengeful Ghost",
        # Magic Lens Tree
        "magic_lens": "Magic Lens",
        "igniting_lens": "Igniting Lens",
        "refraction": "Refraction",
        "focal_point": "Focal Point",
        # Magic Scythe Tree
        "magic_scythe": "Magic Scythe",
        "shadowblade": "Shadowblade",
        "windcutter": "Windcutter",
        "scythe_mastery": "Scythe Mastery",
        # Magic Spear Tree
        "magic_spear": "Magic Spear",
        "holy_spear": "Holy Spear",
        "soul_drain": "Soul Drain",
        "soul_knight": "Soul Knight",
        # Trainer Tree
        "trainer": "Trainer",
        "pulsing_summons": "Pulsing Summons",
        "feed_the_beasts": "Feed the Beasts",
        "bloodsuckers": "Bloodsuckers",
        # Frenzy Tree
        "frenzy": "Frenzy",
        "hellspawns": "Hellspawns",
        "thunderspawns": "Thunderspawns",
        "culling": "Culling",
        
        # === STATUS EFFECTS TREES ===
        # Electromancy Tree
        "electro_mage": "Electro Mage",
        "electro_bug": "Electro Bug",
        "energized": "Energized",
        "electro_mastery": "Electro Mastery",
        # Ice Tree
        "frost_mage": "Frost Mage",
        "frostbite": "Frostbite",
        "ice_shard": "Ice Shard",
        "shatter": "Shatter",
        # Pyromancy Tree
        "pyro_mage": "Pyro Mage",
        "fire_starter": "Fire Starter",
        "intense_burn": "Intense Burn",
        "soothing_warmth": "Soothing Warmth",
        # Dark Arts Tree
        "dark_arts": "Dark Arts",
        "doom": "Doom",
        "wither": "Wither",
        "ritual": "Ritual",
        # Holy Arts Tree
        "holy_arts": "Holy Arts",
        "holy_might": "Holy Might",
        "justice": "Justice",
        "angelic": "Angelic",
        
        # === DEFENSE TREES ===
        # Health Tree
        "vitality": "Vitality",
        "anger_point": "Anger Point",
        "giant": "Giant",
        "regeneration": "Regeneration",
        # Shield Tree
        "holy_shield": "Holy Shield",
        "divine_blessing": "Divine Blessing",
        "divine_wrath": "Divine Wrath",
        "stalwart_shield": "Stalwart Shield",
        # Dodge Tree
        "evasive": "Evasive",
        "nimble": "Nimble",
        "tiny": "Tiny",
        "reflex": "Reflex",
        # Soul Heart Tree
        "soul_shield": "Soul Shield",
        "soul_expand": "Soul Expand",
        "soul_powered": "Soul Powered",
        "soul_link": "Soul Link",
        
        # === GENERAL TREES ===
        # Magnet XP Tree
        "magnetism": "Magnetism",
        "recharge": "Recharge",
        "watch_and_learn": "Watch & Learn",
        "excitement": "Excitement",
        # Speed Boost Tree
        "haste": "Haste",
        "blazing_speed": "Blazing Speed",
        "run_and_gun": "Run and Gun",
        "in_the_wind": "In the Wind",
        # Vision Tree
        "glare": "Glare",
        "intense_glare": "Intense Glare",
        "sight_magic": "Sight Magic",
        "saccade": "Saccade",
        # Aero Tree
        "aero_magic": "Aero Magic",
        "windborne": "Windborne",
        "eye_of_storm": "Eye of the Storm",
        "aero_mastery": "Aero Mastery",
    }
    return names.get(pid, pid.replace("_", " ").title())


def powerup_desc(pid: str) -> str:
    """Get description for a powerup ID."""
    # Try new system first
    if NEW_SYSTEM_AVAILABLE and pid in UPGRADES_BY_ID:
        desc = UPGRADES_BY_ID[pid].description
        # Truncate if too long
        return desc[:45] + "..." if len(desc) > 45 else desc
    
    # Complete descriptions dictionary (legacy + all tree upgrades)
    desc = {
        # === LEGACY POWERUPS ===
        "bullet_1": "+1 bullet",
        "bullet_2": "+2 bullets",
        "bullet_3": "+4 bullets",
        "fire_burn": "Bullets ignite foes",
        "fire_sear": "Burns harder; bonus vs burning",
        "move_1": "+12% move speed",
        "move_2": "+18% move speed",
        "mag_1": "+4 magazine size",
        "mag_2": "+6 mag, faster reload",
        "vision_1": "+40 pickup magnet",
        "vision_2": "+80 pickup magnet",
        "hp_up": "+1 max heart",
        "revive": "+1 revive charge",
        "pierce_on_kill": "Bullets pass through kills",
        "pierce_full": "Bullets pierce regardless",
        "aura_1": "2 shock orbs orbit",
        "aura_2": "4 orbs, adds fire",
        "aura_3": "6 orbs, mixed",
        "aura_elements": "Orbs become fire/ice/poison",
        "minion_1": "Gain 1 drone",
        "minion_2": "Gain 3 drones",
        "ice_1": "15% freeze chance",
        "ice_2": "25% freeze, longer duration",
        "poison_1": "Bullets poison enemies",
        "curse_1": "20% curse chance, delayed dmg",
        "lightning_1": "Lightning every 8 shots",
        "ghost_1": "Summon a ghost ally",
        "shield_1": "Block 2 hits, regenerates",
        "dodge_1": "8% dodge chance",
        "soul_heart_1": "Gain 1 soul heart",
        
        # === DAMAGE & GUNS TREES ===
        # Fast Bullets Tree
        "take_aim": "Bullet Speed +30%, Spread -15%",
        "penetration": "Bullet Speed +15%, Pierce +1",
        "sniper": "Bullet Speed +25%, Damage +15%",
        "assassin": "Auto-kill enemies below 20% HP",
        # Bullet Damage Tree
        "power_shot": "Damage +40%, Knockback +20%",
        "big_shot": "Damage +45%, Bullet Size +40%",
        "splinter": "Enemies explode into 3 bullets",
        "reaper_rounds": "Dmg +20%, Pierce +1, pierce kills",
        # Fire Rate Tree
        "rapid_fire": "Fire Rate +25%",
        "light_bullets": "Fire Rate +15%, Ammo +1, Speed +15%",
        "rubber_bullets": "Bullet Bounce +1, Fire Rate +10%",
        "siege": "40% no ammo use when standing",
        # Multi Shots Tree
        "double_shot": "Projectiles +1, Spread +10°",
        "fan_fire": "Last ammo shoots 10 bullets",
        "split_fire": "Shoot bullet behind you",
        "fusillade": "+1 bullet, doubles base projectiles",
        # Reload Tree
        "quick_hands": "Reload +20%, Fire Rate +5%",
        "armed_and_ready": "Reload +10%, Max Ammo +2",
        "fresh_clip": "+50% Damage 1s after reload",
        "kill_clip": "+5% Reload per kill",
        
        # === SUMMONS TREES ===
        # Dragon Tree
        "dragon_egg": "Hatches Dragon in 3 minutes",
        "aged_dragon": "Dragon +15 dmg every 60s",
        "trained_dragon": "Dragon +10% attack speed/60s",
        "dragon_bond": "Bullets +10% Dragon damage",
        # Ghost Friend Tree
        "ghost_friend": "Ghost shoots piercing shots (8)",
        "best_friends": "Ghost scales with Fire Rate",
        "ghost_wizard": "Ghost inflicts Burn (6 dps)",
        "vengeful_ghost": "Ghost shoots +1 projectile",
        # Magic Lens Tree
        "magic_lens": "Lens gives +30% damage/size",
        "igniting_lens": "Lens bullets inflict Burn",
        "refraction": "Lens bullets +2 bounce",
        "focal_point": "All lens effects doubled",
        # Magic Scythe Tree
        "magic_scythe": "Summon scythe (40 damage)",
        "shadowblade": "Scythe inflicts Curse +15%",
        "windcutter": "Speed +10%, scales scythe",
        "scythe_mastery": "Scythe scales with Bullet Dmg",
        # Magic Spear Tree
        "magic_spear": "Summon 2 spears (20 damage)",
        "holy_spear": "Spear +10 damage per Max HP",
        "soul_drain": "500th summon kill = Soul Heart",
        "soul_knight": "Spear +15 dmg per Soul Heart",
        # Trainer Tree
        "trainer": "Summon Damage +30%",
        "pulsing_summons": "Summons pulse 50 AoE damage",
        "feed_the_beasts": "+1% Summon Dmg per 15 kills",
        "bloodsuckers": "Summon kills drop healing",
        # Frenzy Tree
        "frenzy": "Summon Attack Speed +30%",
        "hellspawns": "Summons inflict Burn (3 dps)",
        "thunderspawns": "30% summon Lightning (22)",
        "culling": "15% chance instant-kill",
        
        # === STATUS EFFECTS TREES ===
        # Electromancy Tree
        "electro_mage": "Every 2nd shot = Lightning",
        "electro_bug": "Bug strikes 2 with Lightning",
        "energized": "20% Lightning refills 3 ammo",
        "electro_mastery": "Lightning +12 dmg, +75% area",
        # Ice Tree
        "frost_mage": "35% Freeze (1.5s, 0.3s boss)",
        "frostbite": "Frozen lose 15% HP (1% boss)",
        "ice_shard": "Last ammo = 3 ice shards",
        "shatter": "Frozen explode (7% HP damage)",
        # Pyromancy Tree
        "pyro_mage": "50% Burn chance (3 dps)",
        "fire_starter": "Every 5th shot = Fireball",
        "intense_burn": "Burn Damage +35%",
        "soothing_warmth": "0.05% Burn heals you",
        # Dark Arts Tree
        "dark_arts": "35% Curse (200% delayed dmg)",
        "doom": "Curse +100% Bullet Damage",
        "wither": "Cursed take +30% damage",
        "ritual": "+1% Damage per 10 Curse kills",
        # Holy Arts Tree
        "holy_arts": "Last ammo = Smite (20 dmg)",
        "holy_might": "Smite +10 per current HP",
        "justice": "+1 Max HP per 500 Smite kills",
        "angelic": "500 Smite kills heals 1 HP",
        
        # === DEFENSE TREES ===
        # Health Tree
        "vitality": "Max HP +1",
        "anger_point": "+75% Dmg/Fire 30s when hit",
        "giant": "Max HP +2, Size +25%",
        "regeneration": "Heal 1 HP every 90s",
        # Shield Tree
        "holy_shield": "Shield blocks 1 hit (2m regen)",
        "divine_blessing": "+25% Reload/Speed w/ shield",
        "divine_wrath": "Lightning/1s w/ shield",
        "stalwart_shield": "Shield regens in 1 min",
        # Dodge Tree
        "evasive": "Dodge +20%",
        "nimble": "Dodge +10%, Speed +10%",
        "tiny": "Dodge +5%, Size -25%",
        "reflex": "Speed +15%, Dodge scales w/ Speed",
        # Soul Heart Tree
        "soul_shield": "Soul Heart +1 every 90s (max 3)",
        "soul_expand": "Soul Heart, max +2",
        "soul_powered": "+10% Damage per Soul Heart",
        "soul_link": "Lose Soul = enemies -80% HP",
        
        # === GENERAL TREES ===
        # Magnet XP Tree
        "magnetism": "Pickup Range +50%",
        "recharge": "10% XP refills 1 ammo",
        "watch_and_learn": "Pickup +30%, Vision +25%",
        "excitement": "+50% Fire Rate 1s after XP",
        # Speed Boost Tree
        "haste": "Move Speed +20%, Fire Rate +5%",
        "blazing_speed": "Speed +10%, Burn while running",
        "run_and_gun": "Walk Speed +100%",
        "in_the_wind": "+10% Dmg/Speed per 10s (max 40%)",
        # Vision Tree
        "glare": "Vision +25%, enemies take 15 dps",
        "intense_glare": "Vision +25%, Glare dmg x2",
        "sight_magic": "Glare applies on-hit effects",
        "saccade": "Vision +25%, Glare ticks 2x",
        # Aero Tree
        "aero_magic": "Gale every 2s (20 dmg/0.5s)",
        "windborne": "Speed +15%, Gale scales",
        "eye_of_storm": "Gale 2x dmg nearby, +5 dmg",
        "aero_mastery": "Gale damage +15",
    }
    return desc.get(pid, "No description")


def evolution_name(eid: str) -> str:
    """Get display name for an evolution ID."""
    # Try new system first
    if NEW_SYSTEM_AVAILABLE and eid in UPGRADES_BY_ID:
        return UPGRADES_BY_ID[eid].name
    
    # Complete evolution names (legacy + all tree ultimates)
    names = {
        # Legacy evolutions
        "laser_overclock": "Laser Overclock",
        "burning_chain": "Chain Blaze",
        "guided_shots": "Guided Shots",
        "aura_overload": "Storm Core",
        "minion_legion": "Drone Legion",
        "pierce_mastery": "Pierce Mastery",
        
        # === TREE ULTIMATES (Tier 3) ===
        # Damage & Guns
        "assassin": "Assassin",
        "reaper_rounds": "Reaper Rounds",
        "siege": "Siege",
        "fusillade": "Fusillade",
        "kill_clip": "Kill Clip",
        
        # Summons
        "dragon_bond": "Dragon Bond",
        "vengeful_ghost": "Vengeful Ghost",
        "focal_point": "Focal Point",
        "scythe_mastery": "Scythe Mastery",
        "soul_knight": "Soul Knight",
        "bloodsuckers": "Bloodsuckers",
        "culling": "Culling",
        
        # Status Effects
        "electro_mastery": "Electro Mastery",
        "shatter": "Shatter",
        "soothing_warmth": "Soothing Warmth",
        "ritual": "Ritual",
        "angelic": "Angelic",
        
        # Defense
        "regeneration": "Regeneration",
        "stalwart_shield": "Stalwart Shield",
        "reflex": "Reflex",
        "soul_link": "Soul Link",
        
        # General
        "excitement": "Excitement",
        "in_the_wind": "In the Wind",
        "saccade": "Saccade",
        "aero_mastery": "Aero Mastery",
    }
    return names.get(eid, eid.replace("_", " ").title())


def evolution_desc(eid: str) -> str:
    """Get description for an evolution ID."""
    # Try new system first
    if NEW_SYSTEM_AVAILABLE and eid in UPGRADES_BY_ID:
        desc = UPGRADES_BY_ID[eid].description
        return desc[:60] + "..." if len(desc) > 60 else desc
    
    # Complete evolution descriptions (legacy + all tree ultimates)
    desc = {
        # Legacy evolutions
        "laser_overclock": "Your laser beam lasts 50% longer and recharges 30% faster",
        "burning_chain": "When a burning enemy dies, nearby enemies catch fire too",
        "guided_shots": "Your bullets gently curve toward the nearest enemy",
        "aura_overload": "Your damage aura grows 40% larger and deals double damage",
        "minion_legion": "Gain 2 more combat drones that deal 25% more damage",
        "pierce_mastery": "Bullets always pierce through enemies and move 20% faster",
        
        # === TREE ULTIMATES (Tier 3) ===
        # Cannons
        "octo_cannon": "8 cannons shoot in all directions simultaneously - total area denial",
        
        # Damage & Guns
        "assassin": "Enemies below 20% HP are instantly killed - perfect for finishing off bosses",
        "railgun": "Bullet speed +60%, bullets hit instantly at close range like a hitscan weapon",
        "bullet_storm": "Fire rate doubled, damage +20%, bullets spread wider but hit everything",
        "meteor": "Massive bullets that pierce 3 enemies and explode dealing area damage",
        "pinball": "Bullets bounce between 5 enemies, seeking new targets after each hit",
        
        # Elements
        "inferno": "Burn damage +50%, burn spread to 3 nearby enemies, ignite on crit",
        "absolute_zero": "Freeze lasts 50% longer, frozen enemies take +40% damage",
        "pandemic": "Poison spreads to 5 enemies, damage +60%, stacks 3 times on same enemy",
        
        # Orbs
        "chaos_orbs": "Orbiting orbs deal fire/ice/poison damage, +30% orbit speed",
        "elemental_storm": "All orbs deal all 3 elements at once with increased damage",
        
        # Defense
        "fortress": "3 shield segments protect you, auto-regenerate when broken, reflect projectiles",
        "regeneration": "Gain +2 max HP and slowly regenerate 1 HP every 90 seconds",
        "supersonic": "Move 25% faster and gain brief invulnerability while boosting",
        
        # Vision
        "omniscience": "+50% vision range, enemies glow, see through walls briefly",
        
        # Summons - Drones
        "drone_swarm": "4 combat drones orbit you, rapid fire, apply burn and poison on hit",
        "phantom_army": "4 phantoms phase through enemies constantly, healing you on contact",
        
        # Summons - Dragon
        "elder_dragon": "Massive elder dragon companion - 60 damage fire breath, flies freely",
        
        # Summons - Lens
        "kaleidoscope": "3 lenses orbit you, bullets passing through multiply x5, +50% damage",
        
        # Player stats
        "reflex_master": "Move 15% faster, 12% chance to dodge any attack completely",
        "bottomless_clip": "+8 magazine size, 15% chance your shots don't consume ammo",
    }
    
    # If not found, try to generate a description from the upgrade itself
    if NEW_SYSTEM_AVAILABLE and eid in UPGRADES_BY_ID:
        return UPGRADES_BY_ID[eid].description
    
    return desc.get(eid, f"Ultimate upgrade - powerful endgame ability")


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_all_tree_upgrades():
    """Get all upgrades from the new tree system."""
    if not NEW_SYSTEM_AVAILABLE:
        return []
    return list(UPGRADES_BY_ID.values())


def get_upgrades_by_category(category: str):
    """Get all upgrades in a category from the new tree system."""
    if not NEW_SYSTEM_AVAILABLE:
        return []
    return [u for u in UPGRADES_BY_ID.values() if u.category == category]


def get_tree_ultimates():
    """Get all ultimate (tier 3) upgrades."""
    if not NEW_SYSTEM_AVAILABLE:
        return []
    return [u for u in UPGRADES_BY_ID.values() if u.is_ultimate]


def is_new_system_active():
    """Check if the new upgrade tree system is available."""
    return NEW_SYSTEM_AVAILABLE
