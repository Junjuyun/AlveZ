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
    def __init__(self, x, y, vx, vy, damage, speed, status=None):
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
        self.speed = speed
        base_r = ENEMY_RADIUS
        if kind == "boss":
            base_r = int(ENEMY_RADIUS * 2.2)
        elif kind == "bruiser":
            base_r = int(ENEMY_RADIUS * 1.4)
        elif kind == "sprinter":
            base_r = int(ENEMY_RADIUS * 0.9)
        self.radius = base_r
        self.kind = kind
        self.boss_stage = boss_stage
        self.flash_timer = 0.0
        self.hit_iframes = 0.0
        self.aura_iframes = 0.0
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
        if self.hit_iframes > 0:
            self.hit_iframes -= dt
        if self.aura_iframes > 0:
            self.aura_iframes -= dt
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
        speed_mult = 0.55 if self.ice_timer > 0 else 1.0
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
        if self.kind == "tank":
            col = COLOR_ENEMY_TANK
        elif self.kind == "fast":
            col = COLOR_ENEMY_FAST
        elif self.kind == "shooter":
            col = (180, 120, 255)
        elif self.kind == "sprinter":
            col = (255, 160, 160)
        elif self.kind == "bruiser":
            col = (200, 90, 60)
        elif self.kind == "boss":
            if self.boss_stage == 1:
                col = (255, 160, 60)
            elif self.boss_stage == 2:
                col = (255, 110, 110)
            else:
                col = (255, 90, 180)
        else:
            col = COLOR_ENEMY
        if self.flash_timer > 0:
            col = COLOR_WHITE
        pygame.draw.circle(surf, col, (sx, sy), self.radius)


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

        self.magnet_range = 160
        self.revives = 0

        self.pierce_mode = "none"

        # smoothed movement direction for visuals
        self.visual_dir = (0.0, -1.0)

        self.aura_radius = 0
        self.aura_dps = 0
        self.aura_unlocked = False
        self.aura_tier = 0
        self.aura_orb_radius = 110
        self.aura_orb_damage = 18
        self.aura_orb_speed = 1.6
        self.aura_orb_size = 12
        self.aura_orb_elements = []
        self.aura_orb_count = 0
        self.aura_orbs = []
        self.aura_elemental = False
        self.aura_orb_knockback = 38

        self.minion_count = 0
        self.minion_damage_mult = 1.0

        self.laser_cooldown_max = 30.0
        self.laser_cooldown = 0.0
        self.laser_duration = 5.0
        self.laser_timer = 0.0
        self.laser_active = False

        self.move_dir = (0.0, -1.0)

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
        if self.reload_timer > 0:
            self.reload_timer -= dt
            if self.reload_timer <= 0:
                self.ammo = self.mag_size

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
        tx, ty = target_world_pos
        dx = tx - self.x
        dy = ty - self.y
        base_angle = math.atan2(dy, dx)

        if self.bullet_count == 1:
            angles = [base_angle]
        else:
            total_spread = math.radians(self.spread_angle_deg) * (self.bullet_count - 1)
            start = base_angle - total_spread / 2
            step = total_spread / max(1, self.bullet_count - 1)
            angles = [start + i * step for i in range(self.bullet_count)]

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
            b.piercing = self.piercing
            if self.pierce_mode == "corpse":
                b.pierce_on_kill = True
                b.pierce_left = 1
            elif self.pierce_mode == "full":
                b.pierce_left = 999
                b.infinite_pierce = True
            bullets.append(b)

        if self.back_shot:
            back_angle = base_angle + math.pi
            extras = 1 + (1 if self.back_extra else 0)
            for i in range(extras):
                offset = math.radians(6 * (i - extras // 2)) if extras > 1 else 0
                vx = math.cos(back_angle + offset)
                vy = math.sin(back_angle + offset)
                b = Bullet(self.x, self.y, vx, vy, self.damage, self.bullet_speed, status=status.copy())
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

    def draw(self, surf, center=None):
        if center is None:
            px = WIDTH // 2
            py = HEIGHT // 2
        else:
            px, py = center
        mx, my = pygame.mouse.get_pos()
        ang = math.atan2(my - py, mx - px)
        ca = math.cos(ang)
        sa = math.sin(ang)
        mvx, mvy = self.visual_dir
        ml = math.hypot(mvx, mvy) or 1.0
        mvx, mvy = mvx / ml, mvy / ml
        mc = mvx
        ms = mvy
        r = self.radius
        if self.invuln > 0 and int(self.invuln * 15) % 2 == 0:
            return
        color = COLOR_WHITE if self.hit_flash > 0 else COLOR_PLAYER
        aim_side = (-sa, ca)
        move_side = (-ms, mc)

        # layer 1: movement-oriented butt triangle (smaller, no outline) and base circle
        tip = (px + mc * r * 0.88, py + ms * r * 0.88)
        base_left = (px - mc * r * 0.9 + move_side[0] * r * 0.95, py - ms * r * 0.9 + move_side[1] * r * 0.95)
        base_right = (px - mc * r * 0.9 - move_side[0] * r * 0.95, py - ms * r * 0.9 - move_side[1] * r * 0.95)
        pygame.draw.polygon(surf, (80, 120, 200), [tip, base_left, base_right])
        pygame.draw.circle(surf, (40, 60, 90), (px, py), int(r * 1.02))

        # layer 2: aim-oriented body and cannons (no cannon plate circle)
        pygame.draw.circle(surf, color, (px, py), r)

        def draw_barrels(count, direction, lateral_scale, color_main, color_trim):
            if count <= 0:
                return
            if count == 1:
                offsets = [0.0]
            elif count == 2:
                offsets = [-0.25, 0.25]
            elif count == 3:
                offsets = [-0.35, 0.0, 0.35]
            else:
                offsets = [-0.45, -0.15, 0.15, 0.45]
            barrel_base = r * 0.92
            barrel_len = r * 1.35
            barrel_w = max(4, int(r * 0.2))
            for off in offsets:
                base_x = px + aim_side[0] * r * off * lateral_scale + direction[0] * barrel_base
                base_y = py + aim_side[1] * r * off * lateral_scale + direction[1] * barrel_base
                tip_x = base_x + direction[0] * barrel_len
                tip_y = base_y + direction[1] * barrel_len
                pygame.draw.line(surf, color_main, (base_x, base_y), (tip_x, tip_y), barrel_w)
                pygame.draw.line(surf, color_trim, (base_x, base_y), (tip_x, tip_y), max(2, barrel_w // 2))

        forward_count = min(4, self.bullet_count)
        draw_barrels(forward_count, (ca, sa), 1.0, (230, 230, 240), (120, 200, 255))

        if self.back_shot:
            back_dir = (-ca, -sa)
            back_count = 1 + (1 if self.back_extra else 0)
            draw_barrels(back_count, back_dir, 0.7, (230, 210, 120), (255, 250, 200))

    def take_damage(self, hearts=1):
        if self.invuln > 0:
            return
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
            self.aura_orbs.append({"angle": ang, "element": elem, "x": 0.0, "y": 0.0, "cd": 0.0})
