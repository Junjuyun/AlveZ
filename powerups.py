from settings import clamp

# =========================
# POWER-UPS
# =========================
POWER_UP_IDS = [
    "fire_rate",
    "damage",
    "move_speed",
    "max_health",
    "regen",
    "piercing",
    "bullet_speed",
    "bullet_size",
    "twin_shot",
    "triple_spread",
    "haste",
]


def apply_power_up(player, power_id):
    if power_id == "fire_rate":
        player.fire_rate *= 1.15
        player.fire_cooldown = 1.0 / player.fire_rate
    elif power_id == "damage":
        player.damage += 6
    elif power_id == "move_speed":
        player.speed += 0.6
    elif power_id == "max_health":
        player.max_hp += 20
        player.hp = clamp(player.hp + 20, 0, player.max_hp)
    elif power_id == "regen":
        player.regen_rate += 1.0
    elif power_id == "piercing":
        player.bullet_piercing = True
    elif power_id == "bullet_speed":
        player.bullet_speed *= 1.2
    elif power_id == "bullet_size":
        player.bullet_size_multiplier *= 1.25
    elif power_id == "twin_shot":
        # at least 2 bullets
        player.bullet_count = max(player.bullet_count, 2)
        player.spread_angle_deg = max(player.spread_angle_deg, 10.0)
    elif power_id == "triple_spread":
        player.bullet_count = max(player.bullet_count, 3)
        player.spread_angle_deg = max(player.spread_angle_deg, 18.0)
    elif power_id == "haste":
        player.speed += 0.8
        player.fire_rate *= 1.1
        player.fire_cooldown = 1.0 / player.fire_rate


def get_power_up_name(power_id):
    names = {
        "fire_rate": "Rapid Fire",
        "damage": "Overcharged Rounds",
        "move_speed": "Thrusters",
        "max_health": "Reinforced Hull",
        "regen": "Nanobot Repair",
        "piercing": "Piercing Shots",
        "bullet_speed": "Railgun",
        "bullet_size": "Heavy Shells",
        "twin_shot": "Twin Cannons",
        "triple_spread": "Triple Spread",
        "haste": "Temporal Haste",
    }
    return names[power_id]


def get_power_up_desc(power_id):
    desc = {
        "fire_rate": "- Fire faster",
        "damage": "- +6 bullet damage",
        "move_speed": "- +0.6 move speed",
        "max_health": "- +20 max HP & heal",
        "regen": "- Regenerate HP over time",
        "piercing": "- Bullets pierce one enemy",
        "bullet_speed": "- Bullets travel faster",
        "bullet_size": "- Larger bullets / hitbox",
        "twin_shot": "- Fire 2 bullets in a small spread",
        "triple_spread": "- Fire 3 bullets in wide spread",
        "haste": "- Faster move & fire",
    }
    return desc[power_id]