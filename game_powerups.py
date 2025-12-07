from game_constants import clamp

# core progression powerups
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
]


EVOLUTIONS = [
    "laser_overclock",
    "burning_chain",
    "guided_shots",
    "aura_overload",
    "minion_legion",
    "pierce_mastery",
]


def available_powerups(player):
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


def apply_powerup(player, pid: str):
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
        player.aura_orb_radius = 120
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
        player.aura_orb_radius = 130
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
        player.aura_orb_radius = 138
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


def apply_evolution(player, eid: str):
    if eid == "laser_overclock":
        player.laser_duration += 2.0
        player.laser_cooldown_max = max(10.0, player.laser_cooldown_max - 6.0)
    elif eid == "burning_chain":
        player.bullet_status["burn"] = True
        player.burn_chain = True
    elif eid == "guided_shots":
        player.guided_shots = True
    elif eid == "aura_overload":
        player.aura_orb_radius += 16
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


def powerup_name(pid: str) -> str:
    names = {
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
    }
    return names[pid]


def powerup_desc(pid: str) -> str:
    desc = {
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
    }
    return desc[pid]


def evolution_name(eid: str) -> str:
    names = {
        "laser_overclock": "Laser Overclock",
        "burning_chain": "Chain Blaze",
        "guided_shots": "Guided Shots",
        "aura_overload": "Storm Core",
        "minion_legion": "Drone Legion",
        "pierce_mastery": "Pierce Mastery",
    }
    return names[eid]


def evolution_desc(eid: str) -> str:
    desc = {
        "laser_overclock": "+Laser duration, lower CD",
        "burning_chain": "Burn spreads on kill",
        "guided_shots": "Shots gently home",
        "aura_overload": "Bigger, stronger aura",
        "minion_legion": "+2 drones, stronger",
        "pierce_mastery": "Always pierce + speed",
    }
    return desc[eid]
