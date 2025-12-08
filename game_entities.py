import math
import random
import pygame
from game_constants import (
    WIDTH,
    HEIGHT,
    FPS,
    WORLD_SIZE,
    PLAYER_RADIUS,
    ENEMY_RADIUS,
    BULLET_RADIUS,
    XP_RADIUS,
    GAS_RADIUS,
    ENEMY_BASE_HP,
    ENEMY_BASE_SPEED,
    XP_PER_LEVEL,
    XP_LEVEL_GROWTH,
    COLOR_PLAYER,
    COLOR_WHITE,
    clamp,
)


class Bullet:
    _uid = 0

    def __init__(self, x, y, vx, vy, damage, speed, status=None):
        Bullet._uid += 1
        self.uid = Bullet._uid
        self.x = x
        self.y = y
        l = math.hypot(vx, vy) or 1
        self.vx = vx / l * speed
        self.vy = vy / l * speed
        self.damage = damage
        self.radius = BULLET_RADIUS
        self.piercing = False
        self.pierce_left = 0
        self.pierce_on_kill = False
        self.status = status or {}
        self.target = None

    def update(self, dt):
        self.x += self.vx * dt * FPS
        self.y += self.vy * dt * FPS

    def draw(self, surf, cam):
        sx = int(self.x - cam[0])
        sy = int(self.y - cam[1])
        pygame.draw.circle(surf, (255, 240, 120), (sx, sy), self.radius)

    def offscreen(self, cam):
        sx = self.x - cam[0]
        sy = self.y - cam[1]
        m = 100
        return sx < -m or sx > WIDTH + m or sy < -m or sy > HEIGHT + m


class Enemy:
    def __init__(self, x, y, hp, speed, kind="normal", boss_stage=0):
        self.x = x
        self.y = y
        self.hp = hp
        self.max_hp = hp  # Store initial HP for execute checks
        self.speed = speed
        base_kind = kind.replace("elite_", "")
        base_r = ENEMY_RADIUS
        if base_kind == "boss":
            base_r = int(ENEMY_RADIUS * 2.2)
        elif base_kind == "bruiser":
            base_r = int(ENEMY_RADIUS * 1.4)
        elif base_kind == "sprinter":
            base_r = int(ENEMY_RADIUS * 0.9)
        elif base_kind == "charger":
            base_r = int(ENEMY_RADIUS * 1.2)
        elif base_kind == "summoner":
            base_r = int(ENEMY_RADIUS * 1.3)
        elif base_kind == "tank":
            base_r = int(ENEMY_RADIUS * 1.3)
        self.radius = base_r
        self.kind = kind
        self.boss_stage = boss_stage
        self.flash_timer = 0.0
        self.aura_iframes = 0.0
        self.hit_sources = {}
        self.knockback_pause = 0.0
        self.knockback_slow = 0.0
        self.charge_timer = 0.0  # For charger enemies
        self.summon_timer = 0.0  # For summoner enemies
        self.ice_timer = 0.0
        self.burn_timer = 0.0
        self.poison_timer = 0.0
        self.burn_dps = 0.0
        self.poison_dps = 0.0
        self.ice_dps = 0.0
        self.burn_tick = 0.0
        self.poison_tick = 0.0
        self.ice_tick = 0.0

    def update(self, dt, player_pos):
        if self.flash_timer > 0:
            self.flash_timer -= dt
        if self.aura_iframes > 0:
            self.aura_iframes -= dt
        if self.knockback_pause > 0:
            self.knockback_pause -= dt
        if self.knockback_slow > 0:
            self.knockback_slow -= dt
        if self.hit_sources:
            expired = []
            for k, v in self.hit_sources.items():
                nv = v - dt
                if nv <= 0:
                    expired.append(k)
                else:
                    self.hit_sources[k] = nv
            for k in expired:
                self.hit_sources.pop(k, None)
        if self.ice_timer > 0:
            self.ice_timer -= dt
        if self.burn_timer > 0:
            self.burn_timer -= dt
        if self.poison_timer > 0:
            self.poison_timer -= dt
        if self.ice_timer <= 0:
            self.ice_dps = 0.0
        if self.burn_timer <= 0:
            self.burn_dps = 0.0
        if self.poison_timer <= 0:
            self.poison_dps = 0.0
        px, py = player_pos
        dx = px - self.x
        dy = py - self.y
        l = math.hypot(dx, dy) or 1
        if self.knockback_pause > 0:
            return
        speed_mult = 1.0
        if self.ice_timer > 0:
            speed_mult *= 0.55
        if self.knockback_slow > 0:
            speed_mult *= 0.55
        
        # Special behavior for charger enemies
        base_kind = self.kind.replace("elite_", "")
        if base_kind == "charger":
            self.charge_timer -= dt
            if self.charge_timer <= 0:
                # Charging - move faster toward player
                speed_mult *= 3.0
                if self.charge_timer <= -0.5:  # Charge duration
                    self.charge_timer = 2.0  # Cooldown before next charge
            else:
                # Waiting to charge - slower movement
                speed_mult *= 0.3
        
        self.x += dx / l * self.speed * speed_mult * dt * FPS
        self.y += dy / l * self.speed * speed_mult * dt * FPS

    def draw(self, surf, cam):
        from game_constants import (
            COLOR_ENEMY_TANK,
            COLOR_ENEMY_FAST,
            COLOR_ENEMY,
        )

        sx = int(self.x - cam[0])
        sy = int(self.y - cam[1])
        base_kind = self.kind.replace("elite_", "")
        is_elite = self.kind.startswith("elite_")
        
        if base_kind == "tank":
            col = COLOR_ENEMY_TANK
        elif base_kind == "fast":
            col = COLOR_ENEMY_FAST
        elif base_kind == "shooter":
            col = (180, 120, 255)
        elif base_kind == "sprinter":
            col = (255, 160, 160)
        elif base_kind == "bruiser":
            col = (200, 90, 60)
        elif base_kind == "charger":
            col = (255, 200, 80)
        elif base_kind == "summoner":
            col = (120, 80, 180)
        elif base_kind == "boss":
            if self.boss_stage == 1:
                col = (255, 160, 60)
            elif self.boss_stage == 2:
                col = (255, 110, 110)
            else:
                col = (255, 90, 180)
        elif base_kind == "minion":
            col = (160, 100, 200)
        else:
            col = COLOR_ENEMY
        if self.flash_timer > 0:
            col = COLOR_WHITE
        pygame.draw.circle(surf, col, (sx, sy), self.radius)
        # Elite glow
        if is_elite and self.flash_timer <= 0:
            pygame.draw.circle(surf, (255, 255, 100), (sx, sy), self.radius + 4, width=2)


class XPOrb:
    def __init__(self, x, y, xp):
        self.x = x
        self.y = y
        self.radius = XP_RADIUS
        self.xp = xp

    def update(self, dt, player):
        px, py = player.x, player.y
        dx = px - self.x
        dy = py - self.y
        d = math.hypot(dx, dy) or 1
        magnet = getattr(player, "magnet_range", 160)
        if d < magnet:
            speed = clamp(8 + (magnet - d) * 0.06, 10, 26)
            self.x += dx / d * speed * dt * FPS
            self.y += dy / d * speed * dt * FPS

    def draw(self, surf, cam):
        from game_constants import COLOR_XP

        sx = int(self.x - cam[0])
        sy = int(self.y - cam[1])
        pygame.draw.circle(surf, COLOR_XP, (sx, sy), self.radius)


class GasPickup:
    def __init__(self, x, y, duration=3.0):
        self.x = x
        self.y = y
        self.radius = GAS_RADIUS
        self.duration = duration

    def draw(self, surf, cam):
        from game_constants import COLOR_GAS

        sx = int(self.x - cam[0])
        sy = int(self.y - cam[1])
        pygame.draw.circle(surf, COLOR_GAS, (sx, sy), self.radius, width=2)
        pygame.draw.circle(surf, COLOR_GAS, (sx, sy), self.radius // 2)


class EvolutionPickup:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = GAS_RADIUS + 4

    def draw(self, surf, cam):
        sx = int(self.x - cam[0])
        sy = int(self.y - cam[1])
        pygame.draw.circle(surf, (255, 200, 90), (sx, sy), self.radius, width=3)
        pygame.draw.circle(surf, (255, 120, 50), (sx, sy), max(1, self.radius - 6), width=0)


class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = PLAYER_RADIUS
        self.base_radius = PLAYER_RADIUS  # For size multiplier effects

        self.hearts = 4
        self.max_hearts = 4

        self.speed = 5.0
        self.base_speed = self.speed
        self.fire_rate = 5.0
        self.fire_cd = 1.0 / self.fire_rate
        self.time_since_shot = 0.0
        self.bullet_speed = 11.0
        self.damage = 10

        self.bullet_count = 1
        self.spread_angle_deg = 8.0
        self.piercing = False
        self.back_shot = False
        self.back_extra = False
        self.bullet_status = {"ice": False, "burn": False, "poison": False}
        self.bullet_tier = 0
        self.fire_tier = 0
        self.move_tier = 0
        self.mag_tier = 0
        self.vision_tier = 0
        self.pierce_tier = 0
        self.minion_tier = 0

        self.ice_bonus_damage = 0
        self.burn_bonus_mult = 1.0
        self.poison_bonus_mult = 1.0
        self.burn_sear_bonus = 0.0
        self.burn_chain = False
        self.guided_shots = False

        self.gas_timer = 0.0
        self.gas_speed_mult = 1.8
        self.gas_fire_mult = 1.7

        self.boost_meter_max = 120.0
        self.boost_meter = self.boost_meter_max
        self.boost_recharge = 30.0
        self.boost_drain = 55.0
        self.boost_mult = 1.75
        self.boosting = False
        self.boost_refill_delay = 0.0
        self.boost_empty_lock = 0.0

        self.level = 1
        self.xp = 0
        self.xp_to_level = XP_PER_LEVEL
        self.kills = 0

        self.mag_size = 12
        self.ammo = self.mag_size
        self.reload_time = 1.2
        self.reload_timer = 0.0

        self.level_ups_since_reward = 0
        self.invuln = 0.0
        self.hit_flash = 0.0
        self.shoot_shrink = 0.0  # Impact effect when shooting

        self.magnet_range = 160
        self.revives = 0

        self.pierce_mode = "none"
        self.pierce_count = 0

        # smoothed movement direction for visuals
        self.visual_dir = (0.0, -1.0)

        self.aura_radius = 0
        self.aura_dps = 0
        self.aura_unlocked = False
        self.aura_tier = 0
        self.aura_orb_radius = 260  # Distance from player center (visible orbit)
        self.aura_orb_damage = 18
        self.aura_orb_speed = 1.6
        self.aura_orb_size = 12
        self.aura_orb_elements = []
        self.aura_orb_count = 0
        self.aura_orbs = []
        self.aura_elemental = False
        self.aura_orb_knockback = 38

        # Phantom defaults to avoid missing-attribute crashes
        self.phantom_count = 0
        self.phantom_damage = 15
        self.phantom_speed = 1.0
        self.phantom_slow = False
        self.phantom_lifesteal = False

        self.minion_count = 0
        self.minion_damage_mult = 1.0

        self.laser_cooldown_max = 30.0
        self.laser_cooldown = 0.0
        self.laser_duration = 5.0
        self.laser_timer = 0.0
        self.laser_active = False

        self.move_dir = (0.0, -1.0)
        
        # ===== NEW UPGRADE SYSTEM ATTRIBUTES =====
        
        # Bullet modifiers
        self.bullet_size_mult = 1.0
        self.knockback_mult = 1.0
        self.bullet_bounce = 0
        self.splinter_on_kill = False
        self.splinter_count = 3
        self.splinter_damage_ratio = 0.10
        
        # Character modifiers
        self.size_mult = 1.0
        self.vision_range = 400
        self.walk_speed_mult = 1.0
        
        # Defense - Soul Hearts
        self.soul_hearts = 0
        self.soul_heart_max = 3
        self.soul_heart_regen = 0
        self.soul_heart_damage_bonus = 0
        self.soul_link_damage = 0
        
        # Defense - Shield
        self.shield_max_hits = 0
        self.shield_hits = 0
        self.shield_regen_time = 120.0
        self.shield_reload_bonus = 0
        self.shield_speed_bonus = 0
        self.shield_lightning_interval = 0
        
        # Defense - Dodge
        self.dodge_chance = 0.0
        self.dodge_scales_speed = False
        
        # Defense - Body damage
        self.body_damage = 0
        
        # Regen
        self.regen_rate = 0.0
        self.regen_accum = 0.0
        self.regen_interval = 0
        self.regen_amount = 0
        
        # Summons - Ghosts
        self.ghost_count = 0
        self.ghost_piercing = False
        self.ghost_burn = False
        
        # Summons - Dragon
        self.has_dragon_egg = False
        self.dragon_hatch_time = 180.0
        self.dragon_active = False
        self.dragon_damage = 20
        self.dragon_attack_speed = 1.0
        
        # Summons - Lenses (Holy Lens)
        self.lens_count = 0
        self.lens_bullet_mult = 1  # Multiplies bullets when lenses are active
        
        # Summons - Scythes
        self.scythe_count = 0
        self.scythe_damage = 40
        
        # Summons - Spears
        self.spear_count = 0
        self.spear_damage = 20
        
        # Summons - Glare
        self.glare_dps = 0
        self.glare_damage_mult = 1.0
        self.glare_on_hit = False
        self.glare_tick_mult = 1.0
        
        # Summons multipliers
        self.summon_damage_mult = 1.0
        self.summon_attack_speed_mult = 1.0
        self.summon_damage_per_kills = 0
        self.summon_kills_interval = 15
        
        # Status Effects - Ice
        self.freeze_chance = 0
        self.freeze_duration = 0
        self.freeze_boss_duration = 0.3
        self.freeze_hp_loss = 0
        self.freeze_boss_hp_loss = 0.01
        self.ice_shard_count = 0
        self.ice_shard_freeze = True
        self.shatter_damage_ratio = 0
        
        # Status Effects - Burn
        self.burn_chance = 0
        self.base_burn_dps = 0
        self.run_burn = False
        
        # Status Effects - Curse
        self.curse_chance = 0
        self.curse_damage_mult = 1.0
        self.curse_delay = 0
        self.curse_bonus_damage = 0
        self.curse_vulnerability = 0
        self.curse_kill_damage_bonus = 0
        self.curse_kills_interval = 10
        
        # Status Effects - Lightning (Electro Mage)
        self.lightning_interval = 0
        self.lightning_damage = 22
        self.lightning_area_mult = 1.0
        self.electro_bug = False
        self.electro_bug_targets = 2
        
        # Status Effects - Fire Starter
        self.fireball_interval = 0
        self.fireball_damage = 40
        
        # Status Effects - Wind (Gale)
        self.gale_interval = 0
        self.gale_damage = 20
        self.gale_tick = 0.5
        self.gale_scales_speed = False
        self.gale_center_damage_mult = 1.0
        
        # Status Effects - Wind Bonus
        self.wind_interval = 0
        self.wind_bonus_per_interval = 0.10
        self.wind_max_bonus = 0.40
        
        # Holy Arts - Smite
        self.smite_on_empty = False
        self.smite_damage = 20
        self.smite_hp_scaling = 0
        self.smite_kill_hp_bonus = 0
        self.smite_kills_interval = 500
        self.smite_hp_bonus_max = 3
        self.smite_kill_heal = 0
        self.smite_heal_interval = 500
        
        # Ammo upgrades
        self.execute_threshold = 0
        self.siege_ammo_save = 0
        self.fan_fire_count = 0
        self.fan_fire_damage_ratio = 0.15
        
        # Reload upgrades
        self.fresh_clip_damage = 0
        self.fresh_clip_duration = 1.0
        self.kill_clip_bonus = 0
        self.kill_clip_stacks = 0
        
        # Damage boosts
        self.anger_damage_mult = 0
        self.anger_fire_rate_mult = 1.75
        self.anger_duration = 30.0
        
        # XP pickups
        self.xp_ammo_chance = 0
        self.xp_ammo_refill = 1
        self.xp_fire_rate_bonus = 0
        self.xp_fire_rate_duration = 1.0

    @property
    def hp(self):
        return self.hearts

    @property
    def max_hp(self):
        return self.max_hearts

    def update(self, dt, keys):
        if self.invuln > 0:
            self.invuln -= dt
        if self.hit_flash > 0:
            self.hit_flash -= dt
        if self.shoot_shrink > 0:
            self.shoot_shrink = max(0, self.shoot_shrink - dt * 2)  # Quick recovery
        if self.reload_timer > 0:
            was_reloading = True
            self.reload_timer -= dt
            if self.reload_timer <= 0:
                self.ammo = self.mag_size
                # Notify upgrade manager of reload completion
                if hasattr(self, "upgrade_manager") and self.upgrade_manager:
                    self.upgrade_manager.on_reload()
        else:
            was_reloading = False

        if self.gas_timer > 0:
            self.gas_timer -= dt
            if self.gas_timer <= 0:
                self.speed = self.base_speed
                self.fire_rate = 5.0
                self.fire_cd = 1.0 / self.fire_rate

        vx = 0
        vy = 0
        if keys[pygame.K_w]:
            vy -= 1
        if keys[pygame.K_s]:
            vy += 1
        if keys[pygame.K_a]:
            vx -= 1
        if keys[pygame.K_d]:
            vx += 1

        boost_pressed = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        was_boosting = self.boosting
        if self.boost_refill_delay > 0:
            self.boost_refill_delay -= dt
        if self.boost_empty_lock > 0:
            self.boost_empty_lock -= dt

        can_boost = boost_pressed and self.boost_meter > 0.1 and self.boost_empty_lock <= 0
        self.boosting = can_boost
        if self.boosting:
            self.boost_meter = max(0.0, self.boost_meter - self.boost_drain * dt)
            if self.boost_meter <= 0.01:
                self.boost_empty_lock = 1.0  # 1s lockout when drained
                self.boosting = False
                self.boost_refill_delay = max(self.boost_refill_delay, 1.0)
        else:
            if was_boosting:
                self.boost_refill_delay = max(self.boost_refill_delay, 0.4)
            if self.boost_refill_delay <= 0 and self.boost_empty_lock <= 0 and self.boost_meter < self.boost_meter_max:
                self.boost_meter = clamp(self.boost_meter + self.boost_recharge * dt, 0.0, self.boost_meter_max)

        l = math.hypot(vx, vy) or 1
        if vx or vy:
            self.move_dir = (vx / l, vy / l)
            effective_speed = self.speed * (self.boost_mult if self.boosting else 1.0)
            self.x += vx / l * effective_speed * dt * FPS
            self.y += vy / l * effective_speed * dt * FPS
            # ease visual direction toward input for smoother rendering
            lerp = min(1.0, dt * 8.0)
            self.visual_dir = (
                self.visual_dir[0] * (1 - lerp) + self.move_dir[0] * lerp,
                self.visual_dir[1] * (1 - lerp) + self.move_dir[1] * lerp,
            )
            vl = math.hypot(*self.visual_dir) or 1.0
            self.visual_dir = (self.visual_dir[0] / vl, self.visual_dir[1] / vl)
        half = WORLD_SIZE / 2
        self.x = clamp(self.x, -half, half)
        self.y = clamp(self.y, -half, half)
        self.time_since_shot += dt

    def can_shoot(self):
        return self.time_since_shot >= self.fire_cd and self.ammo > 0 and self.reload_timer <= 0

    def shoot(self, target_world_pos):
        self.time_since_shot = 0.0
        self.ammo = max(0, self.ammo - 1)
        self.shoot_shrink = 0.08  # Trigger impact shrink effect
        tx, ty = target_world_pos
        dx = tx - self.x
        dy = ty - self.y
        base_angle = math.atan2(dy, dx)
        
        # Get cannon configuration for Diep.io style directional shooting
        cannon_count = max(1, int(getattr(self, "cannon_count", 1)))
        cannon_pattern = getattr(self, "cannon_pattern", "forward")
        has_rear = getattr(self, "has_rear_cannon", False)
        
        # Calculate firing angles based on cannon configuration
        angles = []
        if cannon_count == 1:
            angles = [base_angle]
        elif cannon_count == 2:
            # Twin cannons side by side
            spread = 0.15
            angles = [base_angle - spread, base_angle + spread]
        elif cannon_count == 3:
            if has_rear:
                angles = [base_angle - 0.12, base_angle + 0.12, base_angle + math.pi]
            else:
                angles = [base_angle - 0.2, base_angle, base_angle + 0.2]
        elif cannon_count == 4:
            if cannon_pattern == "cross":
                # X pattern - 4 directions
                angles = [base_angle + i * math.pi / 2 for i in range(4)]
            else:
                # 4 front spread
                angles = [base_angle + (i - 1.5) * 0.15 for i in range(4)]
        elif cannon_count >= 8:
            # Octagon - shoot in all 8 directions
            angles = [base_angle + i * (math.tau / cannon_count) for i in range(cannon_count)]
        else:
            # 5-7 cannons: spread evenly in front
            total_spread = 0.8
            for i in range(cannon_count):
                offset = (i - (cannon_count - 1) / 2) * (total_spread / max(1, cannon_count - 1))
                angles.append(base_angle + offset)

        bullets = []
        status = {
            "ice": self.bullet_status["ice"],
            "burn": self.bullet_status["burn"],
            "poison": self.bullet_status["poison"],
        }
        
        for a in angles:
            vx = math.cos(a)
            vy = math.sin(a)
            b = Bullet(self.x, self.y, vx, vy, self.damage, self.bullet_speed, status=status.copy())
            # Apply bullet size multiplier
            b.radius = int(BULLET_RADIUS * self.bullet_size_mult)
            b.piercing = self.piercing
            if self.pierce_mode == "corpse":
                b.pierce_on_kill = True
                b.pierce_left = 1
            elif self.pierce_mode == "full":
                b.pierce_left = 999
                b.infinite_pierce = True
            b.passed_through_lens = False  # Track if bullet already passed through lens
            bullets.append(b)

        if self.back_shot:
            back_angle = base_angle + math.pi
            extras = 1 + (1 if self.back_extra else 0)
            for i in range(extras):
                offset = math.radians(6 * (i - extras // 2)) if extras > 1 else 0
                vx = math.cos(back_angle + offset)
                vy = math.sin(back_angle + offset)
                b = Bullet(self.x, self.y, vx, vy, self.damage, self.bullet_speed, status=status.copy())
                b.radius = int(BULLET_RADIUS * self.bullet_size_mult)
                b.piercing = self.piercing
                if self.pierce_mode == "corpse":
                    b.pierce_on_kill = True
                    b.pierce_left = 1
                elif self.pierce_mode == "full":
                    b.pierce_left = 999
                    b.infinite_pierce = True
                bullets.append(b)
        if self.ammo <= 0:
            self.reload_timer = self.reload_time
        return bullets

    def start_reload(self):
        # manual reload when not already reloading and magazine isn't full
        if self.reload_timer > 0:
            return
        if self.ammo >= self.mag_size:
            return
        self.reload_timer = self.reload_time
        self.ammo = 0
        self.time_since_shot = 0.0

    def draw(self, surf, center=None, aim_angle=None):
        if center is None:
            px = WIDTH // 2
            py = HEIGHT // 2
        else:
            px, py = center
        
        # Use provided aim_angle or calculate from raw mouse (may be inaccurate with zoom)
        if aim_angle is not None:
            ang = aim_angle
        else:
            mx, my = pygame.mouse.get_pos()
            ang = math.atan2(my - py, mx - px)
        
        # Apply shoot shrink effect for impact feel
        shrink_amt = getattr(self, "shoot_shrink", 0) * 0.15  # Max 15% shrink
        r = int(self.radius * (1.0 - shrink_amt))
        
        if self.invuln > 0 and int(self.invuln * 15) % 2 == 0:
            return
        color = COLOR_WHITE if self.hit_flash > 0 else COLOR_PLAYER
        
        # Get cannon count from upgrades
        cannon_count = max(1, int(getattr(self, "cannon_count", 1)))
        cannon_pattern = getattr(self, "cannon_pattern", "forward")
        has_rear = getattr(self, "has_rear_cannon", False)
        
        # Draw cannons FIRST (behind player body) - Diep.io style rectangles
        self._draw_cannons(surf, px, py, ang, r, cannon_count, cannon_pattern, has_rear)
        
        # Draw exhaust triangle following movement direction (like boost particles)
        # UPSIDE DOWN: tip on body, base pointing outward behind movement
        vdx, vdy = getattr(self, 'visual_dir', (0, -1))
        exhaust_ang = math.atan2(-vdy, -vdx)  # Opposite of movement direction
        # Tip is deeper inside the body
        tip_x = px + math.cos(exhaust_ang) * r * 0.4
        tip_y = py + math.sin(exhaust_ang) * r * 0.4
        # Base is closer in (less sticking out)
        exhaust_len = r * 1.4  # How far base extends
        base_spread = 0.60  # Angle spread for base corners
        left_x = px + math.cos(exhaust_ang + base_spread) * exhaust_len
        left_y = py + math.sin(exhaust_ang + base_spread) * exhaust_len
        right_x = px + math.cos(exhaust_ang - base_spread) * exhaust_len
        right_y = py + math.sin(exhaust_ang - base_spread) * exhaust_len
        pygame.draw.polygon(surf, (80, 80, 100), [(tip_x, tip_y), (left_x, left_y), (right_x, right_y)])
        
        # Draw player body (circle with outline) - ON TOP of exhaust
        pygame.draw.circle(surf, (60, 60, 80), (px, py), r + 3)  # Dark outline
        pygame.draw.circle(surf, color, (px, py), r)  # Main body
        
        # Draw shield if active - C-shaped barrier facing mouse direction
        shield_segments = getattr(self, "shield_segments", 0)
        shield_hp = getattr(self, "shield_hp", 0)
        if shield_segments > 0 and shield_hp > 0:
            shield_radius = getattr(self, "shield_radius", 2.2) * r
            # Draw a wide C-shaped shield facing the mouse
            # Arc spans about 200 degrees for wide coverage
            arc_span = math.pi * 1.1  # ~200 degrees - much wider
            
            # Draw shield as thick curved bar (not 3D arc)
            num_segments = 20
            points_outer = []
            points_inner = []
            shield_thickness = 8
            
            for i in range(num_segments + 1):
                t = i / num_segments
                seg_angle = ang - arc_span / 2 + t * arc_span
                # Outer edge
                ox = px + math.cos(seg_angle) * (shield_radius + shield_thickness / 2)
                oy = py + math.sin(seg_angle) * (shield_radius + shield_thickness / 2)
                points_outer.append((ox, oy))
                # Inner edge
                ix = px + math.cos(seg_angle) * (shield_radius - shield_thickness / 2)
                iy = py + math.sin(seg_angle) * (shield_radius - shield_thickness / 2)
                points_inner.append((ix, iy))
            
            # Combine into polygon
            shield_poly = points_outer + points_inner[::-1]
            
            # Color based on shield HP
            if shield_hp >= shield_segments:
                fill_col = (0, 180, 255)  # Full - cyan
                edge_col = (100, 220, 255)
            elif shield_hp >= shield_segments // 2:
                fill_col = (80, 150, 220)  # Half - light blue
                edge_col = (130, 190, 255)
            else:
                fill_col = (220, 130, 0)  # Low - orange warning
                edge_col = (255, 180, 50)
            
            # Draw filled shield
            if len(shield_poly) >= 3:
                pygame.draw.polygon(surf, fill_col, shield_poly)
                # Draw edge highlight
                pygame.draw.lines(surf, edge_col, False, points_outer, 2)
                pygame.draw.lines(surf, edge_col, False, points_inner, 2)
    
    def _draw_cannons(self, surf, px, py, base_angle, r, count, pattern, has_rear):
        """Draw Diep.io style rectangular cannons."""
        barrel_len = r * 1.4
        barrel_w = max(8, int(r * 0.35))
        
        # Barrel color (dark gray with lighter inner)
        barrel_color = (100, 100, 110)
        barrel_outline = (60, 60, 70)
        
        def draw_single_barrel(angle, length_mult=1.0, width_mult=1.0):
            """Draw a single rectangular barrel."""
            blen = barrel_len * length_mult
            bw = barrel_w * width_mult
            
            # Calculate barrel rectangle corners
            ca, sa = math.cos(angle), math.sin(angle)
            perp_x, perp_y = -sa, ca  # Perpendicular direction
            
            # Barrel starts from edge of player body
            start_x = px + ca * r * 0.6
            start_y = py + sa * r * 0.6
            end_x = px + ca * (r + blen)
            end_y = py + sa * (r + blen)
            
            # Rectangle corners
            half_w = bw / 2
            corners = [
                (start_x + perp_x * half_w, start_y + perp_y * half_w),
                (start_x - perp_x * half_w, start_y - perp_y * half_w),
                (end_x - perp_x * half_w, end_y - perp_y * half_w),
                (end_x + perp_x * half_w, end_y + perp_y * half_w),
            ]
            
            # Draw barrel
            pygame.draw.polygon(surf, barrel_outline, corners)
            # Inner lighter part
            inner_corners = [
                (start_x + perp_x * half_w * 0.6, start_y + perp_y * half_w * 0.6),
                (start_x - perp_x * half_w * 0.6, start_y - perp_y * half_w * 0.6),
                (end_x - perp_x * half_w * 0.6, end_y - perp_y * half_w * 0.6),
                (end_x + perp_x * half_w * 0.6, end_y + perp_y * half_w * 0.6),
            ]
            pygame.draw.polygon(surf, barrel_color, inner_corners)
        
        if count == 1:
            # Single cannon pointing at mouse
            draw_single_barrel(base_angle)
        elif count == 2:
            # Twin cannons side by side
            spread = 0.15
            draw_single_barrel(base_angle - spread)
            draw_single_barrel(base_angle + spread)
        elif count == 3:
            if has_rear:
                # 2 front, 1 back
                draw_single_barrel(base_angle - 0.12)
                draw_single_barrel(base_angle + 0.12)
                draw_single_barrel(base_angle + math.pi, 0.8, 0.8)
            else:
                # 3 front in spread
                draw_single_barrel(base_angle - 0.2)
                draw_single_barrel(base_angle)
                draw_single_barrel(base_angle + 0.2)
        elif count == 4:
            if pattern == "cross":
                # X pattern (4 directions at 90 degrees)
                for i in range(4):
                    draw_single_barrel(base_angle + i * math.pi / 2)
            else:
                # 4 front spread
                for i in range(4):
                    offset = (i - 1.5) * 0.15
                    draw_single_barrel(base_angle + offset)
        elif count >= 8:
            # Octagon - 8 cannons in all directions
            for i in range(count):
                angle = base_angle + i * (math.tau / count)
                draw_single_barrel(angle, 0.9, 0.85)
        else:
            # 5-7 cannons: spread evenly in front
            total_spread = 0.8
            for i in range(count):
                offset = (i - (count - 1) / 2) * (total_spread / max(1, count - 1))
                draw_single_barrel(base_angle + offset)

    def take_damage(self, hearts=1):
        if self.invuln > 0:
            return
        
        # Shield absorbs damage first
        shield_hp = getattr(self, "shield_hp", 0)
        if shield_hp > 0:
            self.shield_hp = shield_hp - 1
            self.invuln = 0.5  # Brief invuln after shield hit
            self.hit_flash = 0.15
            return  # Shield absorbed the hit
        
        self.hearts = clamp(self.hearts - hearts, 0, self.max_hearts)
        self.invuln = 1.0
        self.hit_flash = 0.2
        if self.hearts <= 0 and self.revives > 0:
            # consume revive and stand back up with half health
            self.revives -= 1
            self.hearts = max(1, self.max_hearts // 2)
            self.invuln = 2.0

    def heal(self, hearts=1):
        self.hearts = clamp(self.hearts + hearts, 0, self.max_hearts)

    def add_heart_container(self):
        self.max_hearts += 1
        self.hearts = self.max_hearts

    def add_xp(self, amt):
        self.xp += amt
        leveled = False
        while self.xp >= self.xp_to_level:
            self.xp -= self.xp_to_level
            self.level += 1
            self.level_ups_since_reward += 1
            self.xp_to_level = int(self.xp_to_level * XP_LEVEL_GROWTH)
            leveled = True
        return leveled

    def apply_gas(self, duration):
        self.gas_timer = duration
        self.speed = self.base_speed * self.gas_speed_mult
        self.fire_rate = 5.0 * self.gas_fire_mult
        self.fire_cd = 1.0 / self.fire_rate

    def rebuild_aura_orbs(self):
        # evenly redistribute aura orb angles when the set changes
        self.aura_orbs = []
        if self.aura_orb_count <= 0:
            return
        elements = self.aura_orb_elements or ["shock"]
        for i in range(self.aura_orb_count):
            ang = math.tau * i / self.aura_orb_count
            elem = elements[i % len(elements)]
            self.aura_orbs.append({"angle": ang, "element": elem, "x": 0.0, "y": 0.0, "cd": 0.0, "uid": i + 1})
