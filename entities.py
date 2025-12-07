import math
import random
import pygame
from settings import (
    WIDTH, HEIGHT, FPS,
    COLOR_PLAYER, COLOR_ENEMY, COLOR_BULLET, COLOR_XP,
    PLAYER_RADIUS, ENEMY_RADIUS, BULLET_RADIUS, XP_RADIUS,
    PARTICLE_LIFETIME, WORLD_SIZE,
    PLAYER_BASE_SPEED, PLAYER_BASE_MAX_HP, PLAYER_BASE_FIRE_RATE,
    PLAYER_BASE_DAMAGE, PLAYER_BASE_BULLET_SPEED,
    XP_PER_ORB_BASE, XP_PER_LEVEL_BASE, XP_LEVEL_GROWTH, XP_PER_ORB_DECAY,
    clamp, circle_collision,
)


class Bullet:
    def __init__(self, x, y, vx, vy, damage, speed, piercing=False, radius=BULLET_RADIUS):
        self.x = x
        self.y = y
        length = math.hypot(vx, vy) or 1
        self.vx = vx / length * speed
        self.vy = vy / length * speed
        self.damage = damage
        self.piercing = piercing
        self.pierce_left = 1 if piercing else 0
        self.radius = radius

    def update(self, dt):
        self.x += self.vx * dt * FPS
        self.y += self.vy * dt * FPS

    def draw(self, surf, camera_offset):
        sx = int(self.x - camera_offset[0])
        sy = int(self.y - camera_offset[1])
        pygame.draw.circle(surf, COLOR_BULLET, (sx, sy), self.radius)

    def offscreen(self, camera_offset):
        sx = self.x - camera_offset[0]
        sy = self.y - camera_offset[1]
        margin = 100
        return (
            sx < -margin
            or sx > WIDTH + margin
            or sy < -margin
            or sy > HEIGHT + margin
        )


class Enemy:
    def __init__(self, x, y, hp, speed):
        self.x = x
        self.y = y
        self.hp = hp
        self.speed = speed
        self.radius = ENEMY_RADIUS
        self.spawn_time = 0.3
        self.alive_time = 0.0

    def update(self, dt, player_pos):
        self.alive_time += dt
        px, py = player_pos
        dx = px - self.x
        dy = py - self.y
        dist = math.hypot(dx, dy) or 1
        self.x += (dx / dist) * self.speed * dt * FPS
        self.y += (dy / dist) * self.speed * dt * FPS

    def draw(self, surf, camera_offset):
        alpha_factor = clamp(self.alive_time / self.spawn_time, 0.2, 1.0)
        color = (
            int(COLOR_ENEMY[0] * alpha_factor),
            int(COLOR_ENEMY[1] * alpha_factor),
            int(COLOR_ENEMY[2] * alpha_factor),
        )
        sx = int(self.x - camera_offset[0])
        sy = int(self.y - camera_offset[1])
        pygame.draw.circle(surf, color, (sx, sy), self.radius)

    def knockback(self, from_pos, force):
        dx = self.x - from_pos[0]
        dy = self.y - from_pos[1]
        dist = math.hypot(dx, dy) or 1
        self.x += (dx / dist) * force
        self.y += (dy / dist) * force


class ExperienceOrb:
    def __init__(self, x, y, xp):
        self.x = x
        self.y = y
        self.radius = XP_RADIUS
        self.xp = xp
        self.vx = 0.0
        self.vy = 0.0

    def update(self, dt, player_pos):
        px, py = player_pos
        dx = px - self.x
        dy = py - self.y
        dist = math.hypot(dx, dy) or 1
        if dist < 160:
            speed = 7.0
            self.vx = (dx / dist) * speed
            self.vy = (dy / dist) * speed
        else:
            self.vx *= 0.9
            self.vy *= 0.9
        self.x += self.vx * dt * FPS
        self.y += self.vy * dt * FPS

    def draw(self, surf, camera_offset):
        sx = int(self.x - camera_offset[0])
        sy = int(self.y - camera_offset[1])
        pygame.draw.circle(surf, COLOR_XP, (sx, sy), self.radius)


class Particle:
    def __init__(self, x, y, color, radius, lifetime=PARTICLE_LIFETIME):
        self.x = x
        self.y = y
        self.color = color
        self.radius = radius
        self.life = lifetime
        self.max_life = lifetime
        angle = random.uniform(0, math.tau)
        speed = random.uniform(1, 4)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed

    def update(self, dt):
        self.life -= dt
        self.x += self.vx * dt * FPS
        self.y += self.vy * dt * FPS

    def draw(self, surf, camera_offset):
        if self.life <= 0:
            return
        alpha_factor = clamp(self.life / self.max_life, 0, 1)
        color = (
            int(self.color[0] * alpha_factor),
            int(self.color[1] * alpha_factor),
            int(self.color[2] * alpha_factor),
        )
        sx = int(self.x - camera_offset[0])
        sy = int(self.y - camera_offset[1])
        pygame.draw.circle(
            surf,
            color,
            (sx, sy),
            max(1, int(self.radius * alpha_factor)),
        )

    def alive(self):
        return self.life > 0


class Player:
    def __init__(self, x, y):
        # world position
        self.x = x
        self.y = y
        self.radius = PLAYER_RADIUS
        self.max_hp = PLAYER_BASE_MAX_HP
        self.hp = self.max_hp

        self.base_speed = PLAYER_BASE_SPEED
        self.speed = self.base_speed

        self.fire_rate = PLAYER_BASE_FIRE_RATE
        self.fire_cooldown = 1.0 / self.fire_rate
        self.time_since_shot = 0.0

        self.damage = PLAYER_BASE_DAMAGE
        self.bullet_speed = PLAYER_BASE_BULLET_SPEED

        # firing pattern
        self.bullet_piercing = False
        self.bullet_size_multiplier = 1.0
        self.bullet_count = 1        # Twin / triple shot etc.
        self.spread_angle_deg = 8.0  # spread when bullet_count > 1

        # movement / regen
        self.regen_rate = 0.0
        self.regen_accum = 0.0

        # dash (optional: can be upgraded later)
        self.dash_cooldown = 0.0
        self.dash_ready = True
        self.dash_strength = 0.0

        # progression
        self.level = 1
        self.xp = 0
        self.xp_to_level = XP_PER_LEVEL_BASE
        self.kills = 0
        self.orb_xp_value = XP_PER_ORB_BASE

    def update(self, dt, keys):
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
        length = math.hypot(vx, vy) or 1
        if vx or vy:
            self.x += (vx / length) * self.speed * dt * FPS
            self.y += (vy / length) * self.speed * dt * FPS

        # keep within large world bounds
        half = WORLD_SIZE / 2
        self.x = clamp(self.x, -half, half)
        self.y = clamp(self.y, -half, half)

        # regen
        if self.regen_rate > 0 and 0 < self.hp < self.max_hp:
            self.regen_accum += self.regen_rate * dt
            if self.regen_accum >= 1.0:
                amount = int(self.regen_accum)
                self.hp = clamp(self.hp + amount, 0, self.max_hp)
                self.regen_accum -= amount

        self.time_since_shot += dt

    def can_shoot(self):
        return self.time_since_shot >= self.fire_cooldown

    def shoot(self, target_world_pos):
        self.time_since_shot = 0.0
        tx, ty = target_world_pos
        dx = tx - self.x
        dy = ty - self.y
        base_angle = math.atan2(dy, dx)
        bullets = []

        if self.bullet_count == 1:
            angles = [base_angle]
        else:
            total_spread = math.radians(self.spread_angle_deg) * (self.bullet_count - 1)
            start_angle = base_angle - total_spread / 2
            angles = [start_angle + i * (total_spread / max(1, self.bullet_count - 1))
                      for i in range(self.bullet_count)]

        for ang in angles:
            vx = math.cos(ang)
            vy = math.sin(ang)
            b = Bullet(
                self.x,
                self.y,
                vx,
                vy,
                self.damage,
                self.bullet_speed,
                piercing=self.bullet_piercing,
                radius=int(BULLET_RADIUS * self.bullet_size_multiplier),
            )
            bullets.append(b)
        return bullets

    def draw(self, surf, camera_offset, mouse_pos_screen):
        mx, my = mouse_pos_screen
        # player is always at center of screen
        px = WIDTH // 2
        py = HEIGHT // 2
        angle = math.atan2(my - py, mx - px)
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        r = self.radius

        p1 = (px + cos_a * r, py + sin_a * r)
        p2 = (px - sin_a * r * 0.7, py + cos_a * r * 0.7)
        p3 = (px + sin_a * r * 0.7, py - cos_a * r * 0.7)
        pygame.draw.polygon(surf, COLOR_PLAYER, [p1, p2, p3])

    def take_damage(self, amount):
        self.hp = clamp(self.hp - amount, 0, self.max_hp)

    def add_xp(self, amount):
        self.xp += amount
        leveled_up = False
        while self.xp >= self.xp_to_level:
            self.xp -= self.xp_to_level
            self.level += 1
            leveled_up = True
            # increase requirement and reduce orb value
            self.xp_to_level = int(self.xp_to_level * XP_LEVEL_GROWTH)
            self.orb_xp_value = max(2, int(self.orb_xp_value * (1.0 - XP_PER_ORB_DECAY)))
        return leveled_up