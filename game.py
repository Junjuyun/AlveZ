import os
import math
import random
import sys
import pygame
from audio import audio

# === BASIC SETTINGS ===
WIDTH, HEIGHT = 1280, 720
FPS = 60

COLOR_BG = (5, 5, 20)
COLOR_WHITE = (240, 240, 240)
COLOR_GRAY = (120, 120, 150)
COLOR_DARK_GRAY = (40, 40, 70)
COLOR_PLAYER = (120, 190, 255)
COLOR_ENEMY = (235, 70, 70)
COLOR_ENEMY_TANK = (200, 80, 40)
COLOR_ENEMY_FAST = (240, 120, 120)
COLOR_XP = (90, 240, 140)
COLOR_GAS = (180, 255, 180)
COLOR_BULLET = (255, 240, 120)
COLOR_RED = (255, 80, 80)
COLOR_GREEN = (90, 230, 90)
COLOR_YELLOW = (255, 215, 120)

STATE_MENU = "MENU"
STATE_PLAYING = "PLAYING"
STATE_LEVEL_UP = "LEVEL_UP"
STATE_GAME_OVER = "GAME_OVER"
STATE_SETTINGS = "SETTINGS"
STATE_PAUSED = "PAUSED"
STATE_DEAD_ANIM = "DEAD_ANIM"

WORLD_SIZE = 20000
PLAYER_RADIUS = 18
ENEMY_RADIUS = 16
BULLET_RADIUS = 5
XP_RADIUS = 8
GAS_RADIUS = 10

ENEMY_BASE_HP = 30
ENEMY_BASE_SPEED = 2.0
ENEMY_SPAWN_RATE = 1.0

# Tweak XP to be slower early and slower later
XP_PER_ORB = 5           # less XP per orb
XP_PER_LEVEL = 40        # more XP to level 2
XP_LEVEL_GROWTH = 1.45   # each level needs ~45% more XP

SCREEN_SHAKE_DECAY = 3.0

# increase star density
STAR_COUNT = 12000

# powerup gating
POWERUP_FIRST = 1      # first level-up gives powerup
POWERUP_INTERVAL = 3   # thereafter every 3 levels

# resolutions for dropdown
WINDOW_SIZES = [(1280, 720), (1600, 900), (1920, 1080)]


def clamp(v, a, b):
    return max(a, min(b, v))


def circle_collision(x1, y1, r1, x2, y2, r2):
    dx = x1 - x2
    dy = y1 - y2
    return dx * dx + dy * dy <= (r1 + r2) ** 2


class Button:
    def __init__(self, rect, text, font, base_color, hover_color, active_color=None):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.base_color = base_color
        self.hover_color = hover_color
        self.active_color = active_color or hover_color

    def draw(self, surf):
        mouse_pos = pygame.mouse.get_pos()
        is_hover = self.rect.collidepoint(mouse_pos)
        is_pressed = is_hover and pygame.mouse.get_pressed()[0]
        color = self.active_color if is_pressed else (self.hover_color if is_hover else self.base_color)
        pygame.draw.rect(surf, color, self.rect, border_radius=8)
        label = self.font.render(self.text, True, COLOR_WHITE)
        surf.blit(
            label,
            (
                self.rect.centerx - label.get_width() // 2,
                self.rect.centery - label.get_height() // 2,
            ),
        )

    def is_clicked(self, event):
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
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
        self.status = status or {}

    def update(self, dt):
        self.x += self.vx * dt * FPS
        self.y += self.vy * dt * FPS

    def draw(self, surf, cam):
        sx = int(self.x - cam[0])
        sy = int(self.y - cam[1])
        pygame.draw.circle(surf, COLOR_BULLET, (sx, sy), self.radius)

    def offscreen(self, cam):
        sx = self.x - cam[0]
        sy = self.y - cam[1]
        m = 100
        return sx < -m or sx > WIDTH + m or sy < -m or sy > HEIGHT + m


class Enemy:
    # type: "normal", "tank", "fast"
    def __init__(self, x, y, hp, speed, kind="normal"):
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
        self.flash_timer = 0.0
        self.ice_timer = 0.0
        self.burn_timer = 0.0
        self.poison_timer = 0.0
        self.burn_dps = 0.0
        self.poison_dps = 0.0

    def update(self, dt, player_pos):
        if self.flash_timer > 0:
            self.flash_timer -= dt
        if self.ice_timer > 0:
            self.ice_timer -= dt
        if self.burn_timer > 0:
            self.burn_timer -= dt
            self.hp -= self.burn_dps * dt
        if self.poison_timer > 0:
            self.poison_timer -= dt
            self.hp -= self.poison_dps * dt
        px, py = player_pos
        dx = px - self.x
        dy = py - self.y
        l = math.hypot(dx, dy) or 1
        speed_mult = 0.55 if self.ice_timer > 0 else 1.0
        self.x += dx / l * self.speed * speed_mult * dt * FPS
        self.y += dy / l * self.speed * speed_mult * dt * FPS

    def draw(self, surf, cam):
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
            col = (255, 120, 40)
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

    def update(self, dt, player_pos):
        px, py = player_pos
        dx = px - self.x
        dy = py - self.y
        d = math.hypot(dx, dy) or 1
        if d < 160:
            speed = 6
            self.x += dx / d * speed * dt * FPS
            self.y += dy / d * speed * dt * FPS

    def draw(self, surf, cam):
        sx = int(self.x - cam[0])
        sy = int(self.y - cam[1])
        pygame.draw.circle(surf, COLOR_XP, (sx, sy), self.radius)


class GasPickup:
    def __init__(self, x, y, duration=3.0):
        self.x = x
        self.y = y
        self.radius = GAS_RADIUS
        self.duration = duration  # seconds buff length

    def draw(self, surf, cam):
        sx = int(self.x - cam[0])
        sy = int(self.y - cam[1])
        pygame.draw.circle(surf, COLOR_GAS, (sx, sy), self.radius, width=2)
        pygame.draw.circle(surf, COLOR_GAS, (sx, sy), self.radius // 2)


class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = PLAYER_RADIUS

        # hearts: 4 hearts by default
        self.hearts = 4
        self.max_hearts = 4

        self.speed = 5.0
        self.base_speed = self.speed
        self.fire_rate = 5.0
        self.fire_cd = 1.0 / self.fire_rate
        self.time_since_shot = 0.0
        self.bullet_speed = 11.0
        self.damage = 10

        # firing pattern
        self.bullet_count = 1
        self.spread_angle_deg = 8.0
        self.piercing = False
        self.back_shot = False
        self.back_extra = False
        self.bullet_status = {"ice": False, "burn": False, "poison": False}

        # gas boost
        self.gas_timer = 0.0
        self.gas_speed_mult = 1.8
        self.gas_fire_mult = 1.7

        # progression
        self.level = 1
        self.xp = 0
        self.xp_to_level = XP_PER_LEVEL
        self.kills = 0

        # ammo
        self.mag_size = 12
        self.ammo = self.mag_size
        self.reload_time = 1.2
        self.reload_timer = 0.0

        self.level_ups_since_reward = 0
        self.invuln = 0.0  # seconds of i-frames
        self.hit_flash = 0.0

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

        # gas buff timer
        if self.gas_timer > 0:
            self.gas_timer -= dt
            if self.gas_timer <= 0:
                # reset stats when gas ends
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
        l = math.hypot(vx, vy) or 1
        if vx or vy:
            self.x += vx / l * self.speed * dt * FPS
            self.y += vy / l * self.speed * dt * FPS
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
            b.pierce_left = 1 if self.piercing else 0
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
                b.pierce_left = 1 if self.piercing else 0
                bullets.append(b)
        if self.ammo <= 0:
            self.reload_timer = self.reload_time
        return bullets

    def draw(self, surf):
        px = WIDTH // 2
        py = HEIGHT // 2
        mx, my = pygame.mouse.get_pos()
        ang = math.atan2(my - py, mx - px)
        ca = math.cos(ang)
        sa = math.sin(ang)
        r = self.radius
        if self.invuln > 0 and int(self.invuln * 15) % 2 == 0:
            return  # blink while invulnerable
        color = COLOR_WHITE if self.hit_flash > 0 else COLOR_PLAYER
        p1 = (px + ca * r, py + sa * r)
        p2 = (px - sa * r * 0.7, py + ca * r * 0.7)
        p3 = (px + sa * r * 0.7, py - ca * r * 0.7)
        pygame.draw.polygon(surf, color, [p1, p2, p3])

    def take_damage(self, hearts=1):
        if self.invuln > 0:
            return
        self.hearts = clamp(self.hearts - hearts, 0, self.max_hearts)
        self.invuln = 1.0  # 1s i-frames after hit
        self.hit_flash = 0.2

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
            # progressively slower leveling
            self.xp_to_level = int(self.xp_to_level * XP_LEVEL_GROWTH)
            leveled = True
        return leveled

    def apply_gas(self, duration):
        self.gas_timer = duration
        self.speed = self.base_speed * self.gas_speed_mult
        self.fire_rate = 5.0 * self.gas_fire_mult
        self.fire_cd = 1.0 / self.fire_rate


POWERUPS = [
    "bullet_2",
    "bullet_3",
    "bullet_4",
    "bullet_5",
    "bullet_6",
    "backshot",
    "backshot_plus",
    "pierce",
    "damage_up",
    "move_10",
    "move_15",
    "move_20",
    "hp_up",
    "ice_rounds",
    "burn_rounds",
    "poison_rounds",
]


def apply_powerup(player: Player, pid: str):
    if pid == "bullet_2":
        player.bullet_count = max(player.bullet_count, 2)
    elif pid == "bullet_3":
        player.bullet_count = max(player.bullet_count, 3)
    elif pid == "bullet_4":
        player.bullet_count = max(player.bullet_count, 4)
    elif pid == "bullet_5":
        player.bullet_count = max(player.bullet_count, 5)
    elif pid == "bullet_6":
        player.bullet_count = max(player.bullet_count, 6)
    elif pid == "backshot":
        player.back_shot = True
    elif pid == "backshot_plus":
        player.back_shot = True
        player.back_extra = True
    elif pid == "pierce":
        player.piercing = True
    elif pid == "damage_up":
        player.damage += 6
    elif pid == "move_10":
        player.base_speed *= 1.10
        player.speed = player.base_speed
    elif pid == "move_15":
        player.base_speed *= 1.15
        player.speed = player.base_speed
    elif pid == "move_20":
        player.base_speed *= 1.20
        player.speed = player.base_speed
    elif pid == "hp_up":
        player.add_heart_container()
    elif pid == "ice_rounds":
        player.bullet_status["ice"] = True
    elif pid == "burn_rounds":
        player.bullet_status["burn"] = True
    elif pid == "poison_rounds":
        player.bullet_status["poison"] = True


def powerup_name(pid: str) -> str:
    names = {
        "bullet_2": "Double Shot",
        "bullet_3": "Triple Shot",
        "bullet_4": "Quad Shot",
        "bullet_5": "Penta Shot",
        "bullet_6": "Hexa Shot",
        "backshot": "Rear Gun",
        "backshot_plus": "Rear Barrage",
        "pierce": "Piercing Rounds",
        "damage_up": "Overcharged Rounds",
        "move_10": "Thrusters I",
        "move_15": "Thrusters II",
        "move_20": "Thrusters III",
        "hp_up": "Extra Heart",
        "ice_rounds": "Cryo Rounds",
        "burn_rounds": "Incendiary",
        "poison_rounds": "Toxic Rounds",
    }
    return names[pid]


def powerup_desc(pid: str) -> str:
    desc = {
        "bullet_2": "+1 projectile",
        "bullet_3": "+2 projectiles",
        "bullet_4": "+3 projectiles",
        "bullet_5": "+4 projectiles",
        "bullet_6": "+5 projectiles",
        "backshot": "Shoot one backward",
        "backshot_plus": "Shoot two backward",
        "pierce": "Bullets pierce one enemy",
        "damage_up": "+6 bullet damage",
        "move_10": "+10% move speed",
        "move_15": "+15% move speed",
        "move_20": "+20% move speed",
        "hp_up": "+1 max heart",
        "ice_rounds": "Slow enemies on hit",
        "burn_rounds": "Apply burn DoT",
        "poison_rounds": "Apply poison DoT",
    }
    return desc[pid]


# --- main game ---
class Game:
    def __init__(self):
        pygame.init()
        self.w, self.h = WIDTH, HEIGHT
        self.screen = pygame.display.set_mode((self.w, self.h))
        pygame.display.set_caption("Starlight Eclipse")
        self.clock = pygame.time.Clock()

        # pixel font (bundled)
        font_path = os.path.join(os.path.dirname(__file__), "Assets", "UI", "Press_Start_2P", "PressStart2P-Regular.ttf")
        if os.path.isfile(font_path):
            self.font_large = pygame.font.Font(font_path, 64)
            self.font_medium = pygame.font.Font(font_path, 30)
            self.font_small = pygame.font.Font(font_path, 20)
            self.font_tiny = pygame.font.Font(font_path, 16)
        else:
            self.font_large = pygame.font.SysFont("PressStart2P", 64)
            self.font_medium = pygame.font.SysFont("PressStart2P", 30)
            self.font_small = pygame.font.SysFont("PressStart2P", 20)
            self.font_tiny = pygame.font.SysFont("PressStart2P", 16)

        self.state = STATE_MENU

        # Buttons now drawn without rounded corners (pixel look)
        self.btn_start = Button(
            (self.w // 2 - 150, self.h // 2 - 50, 300, 44),
            "START",
            self.font_medium,
            COLOR_DARK_GRAY,
            COLOR_GRAY,
        )
        self.btn_settings = Button(
            (self.w // 2 - 150, self.h // 2 + 5, 300, 44),
            "SETTINGS",
            self.font_medium,
            COLOR_DARK_GRAY,
            COLOR_GRAY,
        )
        self.btn_quit = Button(
            (self.w // 2 - 150, self.h // 2 + 60, 300, 44),
            "QUIT",
            self.font_medium,
            COLOR_DARK_GRAY,
            COLOR_GRAY,
        )

        self.btn_restart = Button(
            (self.w // 2 - 150, self.h // 2 + 50, 300, 44),
            "RESTART",
            self.font_medium,
            COLOR_DARK_GRAY,
            COLOR_GRAY,
        )
        self.btn_main_menu = Button(
            (self.w // 2 - 150, self.h // 2 + 100, 300, 44),
            "MAIN MENU",
            self.font_medium,
            COLOR_DARK_GRAY,
            COLOR_GRAY,
        )

        # Pause icon button (small square in top-right)
        self.btn_pause = Button(
            (self.w - 70, 16, 50, 32),
            "||",
            self.font_small,
            COLOR_DARK_GRAY,
            COLOR_GRAY,
            COLOR_WHITE,
        )

        # Pause overlay actions
        self.btn_pause_reset = Button(
            (self.w // 2 - 110, self.h // 2 + 24, 220, 44),
            "RESET",
            self.font_medium,
            COLOR_DARK_GRAY,
            COLOR_GRAY,
            COLOR_WHITE,
        )
        self.btn_pause_quit = Button(
            (self.w // 2 - 110, self.h // 2 + 74, 220, 44),
            "QUIT",
            self.font_medium,
            COLOR_DARK_GRAY,
            COLOR_GRAY,
            COLOR_WHITE,
        )
        self.btn_pause_resume = Button(
            (self.w // 2 - 110, self.h // 2 - 26, 220, 44),
            "RESUME",
            self.font_medium,
            COLOR_DARK_GRAY,
            COLOR_GRAY,
            COLOR_WHITE,
        )

        self.btn_settings_back = Button(
            (self.w // 2 - 100, self.h // 2 + 120, 200, 44),
            "BACK",
            self.font_medium,
            COLOR_DARK_GRAY,
            COLOR_GRAY,
        )

        # starfield
        def rand_star_pos():
            sx = clamp(random.gauss(0, WORLD_SIZE / 5), -WORLD_SIZE / 2, WORLD_SIZE / 2)
            sy = clamp(random.gauss(0, WORLD_SIZE / 5), -WORLD_SIZE / 2, WORLD_SIZE / 2)
            return sx, sy

        self.stars = [
            {
                "x": rand_star_pos()[0],
                "y": rand_star_pos()[1],
                "r": random.randint(1, 4),
                "blink": random.uniform(0, 1.0),
                "blink_speed": random.uniform(0.8, 1.6),
                "shape": random.choice(["dot", "diamond", "wide"]),
            }
            for _ in range(STAR_COUNT)
        ]
        self.star_flashes = []

        self.levelup_options = []

        # audio volumes (used by external audio module)
        self.music_volume = 0.5
        self.sfx_volume = 0.8
        audio.set_music_volume(self.music_volume)
        audio.set_sfx_volume(self.sfx_volume)

        # music state tracking
        self.current_music_tag = None
        self.game_over_audio_triggered = False
        self.defeat_music_timer = None

        # settings sliders
        slider_w = 300
        slider_h = 12
        base_y = self.h // 2 - 10
        self.slider_bg_rect = pygame.Rect(self.w // 2 - slider_w // 2, base_y, slider_w, slider_h)
        self.slider_sfx_rect = pygame.Rect(self.w // 2 - slider_w // 2, base_y + 40, slider_w, slider_h)
        # pause overlay sliders
        p_slider_w = 260
        p_slider_h = 10
        p_base_y = self.h // 2 + 110
        self.pause_music_rect = pygame.Rect(self.w // 2 - p_slider_w // 2, p_base_y, p_slider_w, p_slider_h)
        self.pause_sfx_rect = pygame.Rect(self.w // 2 - p_slider_w // 2, p_base_y + 28, p_slider_w, p_slider_h)
        self.fullscreen = False
        self.window_size_index = 0
        self.show_size_dropdown = False

        btn_y = self.h // 4 + 80
        self.btn_window_dropdown = Button(
            (self.w // 2 - 220, btn_y, 200, 44),
            "WINDOWED ▼",
            self.font_small,
            COLOR_DARK_GRAY,
            COLOR_GRAY,
            COLOR_WHITE,
        )
        self.btn_fullscreen = Button(
            (self.w // 2 + 20, btn_y, 200, 44),
            "FULLSCREEN",
            self.font_small,
            COLOR_DARK_GRAY,
            COLOR_GRAY,
            COLOR_WHITE,
        )

        self.reset_game()
        self._load_audio_assets()
        self._update_music(0)

    def _load_audio_assets(self):
        base = os.path.join(os.path.dirname(__file__), "Assets", "Sounds")

        def load(name):
            path = os.path.join(base, name)
            return pygame.mixer.Sound(path) if os.path.isfile(path) else None

        def music_path(name):
            path = os.path.join(base, name)
            return path if os.path.isfile(path) else None

        audio.snd_player_death = load("player-death.mp3")
        audio.snd_player_hit = load("player-hit.mp3")
        audio.snd_enemy_death = load("enemy-death.mp3")
        audio.snd_shoot = load("shooting.mp3")
        audio.snd_level_up = load("level-up.mp3")
        audio.snd_pause = load("pause.mp3")
        audio.snd_unpause = load("unpause.mp3")
        audio.snd_game_over = load("game-over.mp3")

        audio.music_menu = music_path("menu-bg.mp3")
        audio.music_ingame = music_path("ingame-bg.mp3")
        audio.music_defeat = music_path("defeat-bg.wav")

    def reset_game(self):
        self.player = Player(0, 0)
        self.bullets = []
        self.enemies = []
        self.orbs = []
        self.gas_pickups = []
        self.enemy_bullets = []
        self.elapsed_time = 0.0
        self.spawn_timer = 0.0
        self.enemy_spawn_rate = ENEMY_SPAWN_RATE
        self.enemy_hp = ENEMY_BASE_HP
        self.enemy_speed = ENEMY_BASE_SPEED
        self.kills = 0
        self.screen_shake = 0.0

        self.death_fx = []
        self.death_timer = 0.0
        self.game_over_audio_triggered = False
        self.defeat_music_timer = None
        self.boost_effect_timer = 0.0
        self.damage_texts = []
        self.bosses_spawned = 0

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False
                if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    if self.state == STATE_PLAYING:
                        self.state = STATE_PAUSED
                    elif self.state == STATE_PAUSED:
                        self.state = STATE_PLAYING
                    else:
                        running = False
                self.handle_event(e)
            self.update(dt)
            self.draw()
        pygame.quit()
        sys.exit()

    def _rebuild_ui(self):
        self.btn_start = Button((self.w // 2 - 150, self.h // 2 - 50, 300, 44), "START", self.font_medium, COLOR_DARK_GRAY, COLOR_GRAY)
        self.btn_settings = Button((self.w // 2 - 150, self.h // 2 + 5, 300, 44), "SETTINGS", self.font_medium, COLOR_DARK_GRAY, COLOR_GRAY)
        self.btn_quit = Button((self.w // 2 - 150, self.h // 2 + 60, 300, 44), "QUIT", self.font_medium, COLOR_DARK_GRAY, COLOR_GRAY)
        self.btn_restart = Button((self.w // 2 - 150, self.h // 2 + 50, 300, 44), "RESTART", self.font_medium, COLOR_DARK_GRAY, COLOR_GRAY)
        self.btn_main_menu = Button((self.w // 2 - 150, self.h // 2 + 100, 300, 44), "MAIN MENU", self.font_medium, COLOR_DARK_GRAY, COLOR_GRAY)
        self.btn_pause = Button((self.w - 70, 16, 50, 32), "||", self.font_small, COLOR_DARK_GRAY, COLOR_GRAY, COLOR_WHITE)
        self.btn_pause_reset = Button((self.w // 2 - 110, self.h // 2 + 24, 220, 44), "RESET", self.font_medium, COLOR_DARK_GRAY, COLOR_GRAY, COLOR_WHITE)
        self.btn_pause_quit = Button((self.w // 2 - 110, self.h // 2 + 74, 220, 44), "QUIT", self.font_medium, COLOR_DARK_GRAY, COLOR_GRAY, COLOR_WHITE)
        self.btn_pause_resume = Button((self.w // 2 - 110, self.h // 2 - 26, 220, 44), "RESUME", self.font_medium, COLOR_DARK_GRAY, COLOR_GRAY, COLOR_WHITE)
        self.btn_settings_back = Button((self.w // 2 - 100, self.h // 2 + 120, 200, 44), "BACK", self.font_medium, COLOR_DARK_GRAY, COLOR_GRAY)
        btn_y = self.h // 4 + 80
        self.btn_window_dropdown = Button((self.w // 2 - 220, btn_y, 200, 44), "WINDOWED ▼", self.font_small, COLOR_DARK_GRAY, COLOR_GRAY, COLOR_WHITE)
        self.btn_fullscreen = Button((self.w // 2 + 20, btn_y, 200, 44), "FULLSCREEN", self.font_small, COLOR_DARK_GRAY, COLOR_GRAY, COLOR_WHITE)
        p_slider_w = 260
        p_slider_h = 10
        p_base_y = self.h // 2 + 110
        self.pause_music_rect = pygame.Rect(self.w // 2 - p_slider_w // 2, p_base_y, p_slider_w, p_slider_h)
        self.pause_sfx_rect = pygame.Rect(self.w // 2 - p_slider_w // 2, p_base_y + 28, p_slider_w, p_slider_h)

    def _apply_display_mode(self):
        global WIDTH, HEIGHT
        WIDTH, HEIGHT = self.w, self.h
        flags = pygame.FULLSCREEN if self.fullscreen else 0
        self.screen = pygame.display.set_mode((self.w, self.h), flags)
        self._rebuild_ui()
        # update sliders position
        slider_w = 300
        slider_h = 12
        base_y = self.h // 2 - 10
        self.slider_bg_rect.update(self.w // 2 - slider_w // 2, base_y, slider_w, slider_h)
        self.slider_sfx_rect.update(self.w // 2 - slider_w // 2, base_y + 40, slider_w, slider_h)
        btn_y = self.h // 4 + 80
        self.btn_window_dropdown.rect.update(self.w // 2 - 220, btn_y, 200, 44)
        self.btn_fullscreen.rect.update(self.w // 2 + 20, btn_y, 200, 44)

    def handle_event(self, e):
        if self.state == STATE_MENU:
            if self.btn_start.is_clicked(e):
                self.reset_game()
                self.state = STATE_PLAYING
            elif self.btn_settings.is_clicked(e):
                self.state = STATE_SETTINGS
            elif self.btn_quit.is_clicked(e):
                pygame.event.post(pygame.event.Event(pygame.QUIT))
        elif self.state == STATE_GAME_OVER:
            if self.btn_restart.is_clicked(e):
                self.reset_game()
                self.state = STATE_PLAYING
            elif self.btn_main_menu.is_clicked(e):
                self.state = STATE_MENU
        elif self.state == STATE_LEVEL_UP:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                mx, my = e.pos
                w = 260
                h = 120
                gap = 20
                total_w = 3 * w + 2 * gap
                start_x = WIDTH // 2 - total_w // 2
                y = HEIGHT // 2 - h // 2
                for i, pid in enumerate(self.levelup_options):
                    rect = pygame.Rect(start_x + i * (w + gap), y, w, h)
                    if rect.collidepoint(mx, my):
                        apply_powerup(self.player, pid)
                        self.state = STATE_PLAYING
                        break
        elif self.state == STATE_SETTINGS:
            if self.btn_settings_back.is_clicked(e):
                self.state = STATE_MENU
                self.show_size_dropdown = False
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                mx, my = e.pos
                # BG volume slider
                if self.slider_bg_rect.collidepoint(mx, my):
                    t = (mx - self.slider_bg_rect.x) / self.slider_bg_rect.width
                    self.music_volume = clamp(t, 0.0, 1.0)
                    audio.set_music_volume(self.music_volume)
                # SFX volume slider
                if self.slider_sfx_rect.collidepoint(mx, my):
                    t = (mx - self.slider_sfx_rect.x) / self.slider_sfx_rect.width
                    self.sfx_volume = clamp(t, 0.0, 1.0)
                    audio.set_sfx_volume(self.sfx_volume)
                if self.btn_fullscreen.is_clicked(e):
                    self.fullscreen = not self.fullscreen
                    self.show_size_dropdown = False
                    self._apply_display_mode()
                elif self.btn_window_dropdown.is_clicked(e):
                    self.show_size_dropdown = not self.show_size_dropdown
                elif self.show_size_dropdown:
                    # check dropdown options
                    drop_rect = self._dropdown_rect()
                    if drop_rect.collidepoint(mx, my):
                        option_h = 34
                        idx = (my - drop_rect.y) // option_h
                        if 0 <= idx < len(WINDOW_SIZES):
                            self.window_size_index = idx
                            self.w, self.h = WINDOW_SIZES[self.window_size_index]
                            self.fullscreen = False
                            self.show_size_dropdown = False
                            self._apply_display_mode()
                    else:
                        self.show_size_dropdown = False
        elif self.state == STATE_PLAYING:
            if self.btn_pause.is_clicked(e):
                audio.play_sfx(audio.snd_pause)
                self.state = STATE_PAUSED
        elif self.state == STATE_PAUSED:
            if self.btn_pause_resume.is_clicked(e):
                audio.play_sfx(audio.snd_unpause)
                self.state = STATE_PLAYING
            elif self.btn_pause_reset.is_clicked(e):
                self.reset_game()
                audio.play_sfx(audio.snd_unpause)
                self.state = STATE_PLAYING
            elif self.btn_pause_quit.is_clicked(e):
                audio.play_sfx(audio.snd_unpause)
                self.state = STATE_MENU
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                mx, my = e.pos
                if self.pause_music_rect.collidepoint(mx, my):
                    t = (mx - self.pause_music_rect.x) / self.pause_music_rect.width
                    self.music_volume = clamp(t, 0.0, 1.0)
                    audio.set_music_volume(self.music_volume)
                elif self.pause_sfx_rect.collidepoint(mx, my):
                    t = (mx - self.pause_sfx_rect.x) / self.pause_sfx_rect.width
                    self.sfx_volume = clamp(t, 0.0, 1.0)
                    audio.set_sfx_volume(self.sfx_volume)
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                # click anywhere else to resume
                audio.play_sfx(audio.snd_unpause)
                self.state = STATE_PLAYING
        elif self.state == STATE_DEAD_ANIM:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                self.state = STATE_GAME_OVER

    def update(self, dt):
        self._update_starfield(dt)

        if self.state == STATE_PLAYING:
            self.update_playing(dt)
        elif self.state == STATE_DEAD_ANIM:
            self.death_timer -= dt
            self._update_death_fx(dt)
            if self.death_timer <= 0:
                self.state = STATE_GAME_OVER

        self._update_music(dt)

    def _update_death_fx(self, dt):
        for fx in list(self.death_fx):
            fx["x"] += fx["vx"] * dt * FPS
            fx["y"] += fx["vy"] * dt * FPS
            fx["life"] -= dt
            if fx["life"] <= 0:
                self.death_fx.remove(fx)

    def _update_starfield(self, dt):
        # decay active flashes
        for f in list(self.star_flashes):
            f["life"] -= dt
            if f["life"] <= 0:
                self.star_flashes.remove(f)

        # spawn new flash occasionally
        if random.random() < 0.12 and self.stars:
            star = random.choice(self.stars)
            radius = random.randint(2, 4)
            life = random.uniform(0.25, 0.65)
            self.star_flashes.append({"x": star["x"], "y": star["y"], "r": radius, "life": life, "life_max": life})

        # star blink progress
        for s in self.stars:
            s["blink"] += dt * s["blink_speed"]
            if s["blink"] > 1:
                s["blink"] -= 1

    def _update_music(self, dt):
        # menu + settings music
        if self.state in (STATE_MENU, STATE_SETTINGS):
            self.game_over_audio_triggered = False
            self.defeat_music_timer = None
            if self.current_music_tag != "menu":
                audio.play_music_file(audio.music_menu, loop=-1)
                self.current_music_tag = "menu"
            return

        # in-game music (includes paused + level-up overlay)
        if self.state in (STATE_PLAYING, STATE_LEVEL_UP, STATE_PAUSED):
            self.game_over_audio_triggered = False
            self.defeat_music_timer = None
            if self.current_music_tag != "ingame":
                audio.play_music_file(audio.music_ingame, loop=-1)
                self.current_music_tag = "ingame"
            return

        # death anim: stop music to let death/game-over audio breathe
        if self.state == STATE_DEAD_ANIM:
            if self.current_music_tag is not None:
                audio.stop_music()
                self.current_music_tag = None
            return

        # game over: play stinger, then loop defeat music
        if self.state == STATE_GAME_OVER:
            if not self.game_over_audio_triggered:
                audio.stop_music()
                audio.play_sfx(audio.snd_game_over)
                if audio.snd_game_over:
                    self.defeat_music_timer = audio.snd_game_over.get_length()
                else:
                    self.defeat_music_timer = 0.0
                self.game_over_audio_triggered = True

            if self.defeat_music_timer is not None:
                self.defeat_music_timer -= dt
                if self.defeat_music_timer <= 0:
                    audio.play_defeat_music()
                    self.current_music_tag = "defeat"
                    self.defeat_music_timer = None
            return

    def update_playing(self, dt):
        self.elapsed_time += dt
        keys = pygame.key.get_pressed()
        self.player.update(dt, keys)

        cam = (self.player.x - WIDTH // 2, self.player.y - HEIGHT // 2)

        # shooting
        if pygame.mouse.get_pressed()[0] and self.player.can_shoot():
            mx, my = pygame.mouse.get_pos()
            world_target = (cam[0] + mx, cam[1] + my)
            new_bullets = self.player.shoot(world_target)
            self.bullets.extend(new_bullets)
            audio.play_sfx(audio.snd_shoot)

        for b in self.bullets:
            b.update(dt)
        self.bullets = [b for b in self.bullets if not b.offscreen(cam)]

        if self.boost_effect_timer > 0:
            self.boost_effect_timer = max(0.0, self.boost_effect_timer - dt)

        # damage texts
        for txt in list(self.damage_texts):
            txt["life"] -= dt
            txt["y"] -= 20 * dt
            if txt["life"] <= 0:
                self.damage_texts.remove(txt)

        # spawn progression: unlock variants over time
        self.spawn_timer += dt
        # scale spawn rate every 30s
        self.enemy_spawn_rate = ENEMY_SPAWN_RATE + 0.25 * int(self.elapsed_time // 30)
        interval = 1.0 / self.enemy_spawn_rate
        while self.spawn_timer >= interval:
            self.spawn_timer -= interval
            self.spawn_enemy()

        for e in self.enemies:
            e.update(dt, (self.player.x, self.player.y))
        for o in self.orbs:
            o.update(dt, (self.player.x, self.player.y))

        # DoT deaths
        for en in list(self.enemies):
            if en.hp <= 0:
                self.kills += 1
                self.player.kills += 1
                self.orbs.append(XPOrb(en.x, en.y, XP_PER_ORB))
                if random.random() < 0.05:
                    self.gas_pickups.append(GasPickup(en.x, en.y))
                self.enemies.remove(en)

        # enemy shooting
        for en in self.enemies:
            if getattr(en, "kind", "") in ("shooter", "boss", "elite_shooter"):
                if not hasattr(en, "shoot_cd"):
                    en.shoot_cd = random.uniform(1.0, 2.4)
                en.shoot_cd -= dt
                if en.shoot_cd <= 0:
                    en.shoot_cd = random.uniform(1.0, 2.0) if en.kind != "boss" else random.uniform(0.6, 1.2)
                    dx = self.player.x - en.x
                    dy = self.player.y - en.y
                    l = math.hypot(dx, dy) or 1
                    speed = 9.0 if en.kind != "boss" else 12.0
                    self.enemy_bullets.append({"x": en.x, "y": en.y, "vx": dx / l * speed, "vy": dy / l * speed, "r": 6 if en.kind == "boss" else 4, "dmg": 1})

        # enemy bullets update/collisions
        for eb in list(self.enemy_bullets):
            eb["x"] += eb["vx"] * dt * FPS
            eb["y"] += eb["vy"] * dt * FPS
            if circle_collision(self.player.x, self.player.y, self.player.radius, eb["x"], eb["y"], eb["r"]):
                if self.player.invuln <= 0:
                    self.player.take_damage(1)
                    self.player.hit_flash = 0.2
                if eb in self.enemy_bullets:
                    self.enemy_bullets.remove(eb)
                continue
            if abs(eb["x"] - self.player.x) > 2000 or abs(eb["y"] - self.player.y) > 2000:
                self.enemy_bullets.remove(eb)

        # bullet-enemy
        for b in list(self.bullets):
            for en in list(self.enemies):
                if circle_collision(b.x, b.y, b.radius, en.x, en.y, en.radius):
                    en.hp -= b.damage
                    en.flash_timer = 0.15
                    dx = en.x - b.x
                    dy = en.y - b.y
                    l = math.hypot(dx, dy) or 1
                    push = 12
                    en.x += dx / l * push
                    en.y += dy / l * push
                    self.damage_texts.append({"x": en.x + random.uniform(-6, 6), "y": en.y - 10, "val": b.damage, "life": 0.6})
                    # apply status effects
                    if b.status.get("ice"):
                        en.ice_timer = max(en.ice_timer, 1.2)
                    if b.status.get("burn"):
                        en.burn_timer = max(en.burn_timer, 2.5)
                        en.burn_dps = max(en.burn_dps, self.player.damage * 0.35)
                    if b.status.get("poison"):
                        en.poison_timer = max(en.poison_timer, 3.5)
                        en.poison_dps = max(en.poison_dps, self.player.damage * 0.25)
                    if b.piercing and b.pierce_left > 0:
                        b.pierce_left -= 1
                    else:
                        if b in self.bullets:
                            self.bullets.remove(b)
                    if en.hp <= 0:
                        self.kills += 1
                        self.player.kills += 1
                        self.orbs.append(XPOrb(en.x, en.y, XP_PER_ORB))
                        # chance to drop gas
                        if random.random() < 0.05:
                            self.gas_pickups.append(GasPickup(en.x, en.y))
                        self.enemies.remove(en)
                        audio.play_sfx(audio.snd_enemy_death)
                    break

        # player-enemy with knockback/pop & i-frames
        for en in list(self.enemies):
            if circle_collision(self.player.x, self.player.y, self.player.radius, en.x, en.y, en.radius):
                if self.player.invuln <= 0:
                    self.player.take_damage(1)
                    audio.play_sfx(audio.snd_player_hit)
                    # knockback both
                    dx = self.player.x - en.x
                    dy = self.player.y - en.y
                    l = math.hypot(dx, dy) or 1
                    push = 40
                    self.player.x += dx / l * push
                    self.player.y += dy / l * push
                    en.x -= dx / l * push
                    en.y -= dy / l * push
                    self.player.hit_flash = 0.2
                    if self.player.hp <= 0:
                        audio.play_sfx(audio.snd_player_death)
                        self._spawn_death_fx(self.player.x, self.player.y)
                        self.death_timer = 1.0
                        self.state = STATE_DEAD_ANIM
                        return

        # player-xp (add pickup sfx)
        for o in list(self.orbs):
            if circle_collision(self.player.x, self.player.y, self.player.radius, o.x, o.y, o.radius):
                leveled = self.player.add_xp(o.xp)
                self.orbs.remove(o)
                if leveled:
                    # level-up gating
                    if self.player.level_ups_since_reward == POWERUP_FIRST or self.player.level_ups_since_reward >= POWERUP_INTERVAL:
                        self.player.level_ups_since_reward = 0
                        self.roll_levelup()

        # gas pickup collision
        for g in list(self.gas_pickups):
            if circle_collision(self.player.x, self.player.y, self.player.radius, g.x, g.y, g.radius):
                self.player.apply_gas(g.duration)
                self.boost_effect_timer = max(self.boost_effect_timer, g.duration)
                self.gas_pickups.remove(g)

    def _spawn_death_fx(self, x, y):
        self.death_fx.clear()
        for _ in range(120):
            ang = random.uniform(0, math.tau)
            spd = random.uniform(140, 320)
            self.death_fx.append({
                "x": x, "y": y,
                "vx": math.cos(ang) * spd,
                "vy": math.sin(ang) * spd,
                "life": random.uniform(0.5, 1.2),
            })

    def spawn_enemy(self):
        half = WORLD_SIZE / 2
        dmin, dmax = 600, 900
        ang = random.uniform(0, math.tau)
        r = random.uniform(dmin, dmax)
        x = self.player.x + math.cos(ang) * r
        y = self.player.y + math.sin(ang) * r
        x = clamp(x, -half, half)
        y = clamp(y, -half, half)

        # choose enemy type based on elapsed time
        t = self.elapsed_time
        hp_scale = 1.0 + (t / 90.0)
        speed_scale = 1.0 + (t / 180.0)

        # timed boss every minute
        if int(t // 60) > self.bosses_spawned:
            self.bosses_spawned += 1
            kind = "boss"
        else:
            pool = ["normal", "fast", "tank"]
            weights = [0.45, 0.25, 0.2]
            if t > 45:
                pool.append("shooter")
                weights.append(0.15)
            if t > 90:
                pool.append("sprinter")
                weights.append(0.15)
            if t > 120:
                pool.append("bruiser")
                weights.append(0.2)
            kind = random.choices(pool, weights=weights, k=1)[0]

        if kind == "tank":
            hp = int(ENEMY_BASE_HP * 3 * hp_scale)
            speed = ENEMY_BASE_SPEED * 0.7 * speed_scale
        elif kind == "fast":
            hp = int(ENEMY_BASE_HP * 0.7 * hp_scale)
            speed = ENEMY_BASE_SPEED * 1.8 * speed_scale
        elif kind == "sprinter":
            hp = int(ENEMY_BASE_HP * 0.8 * hp_scale)
            speed = ENEMY_BASE_SPEED * 2.4 * speed_scale
        elif kind == "bruiser":
            hp = int(ENEMY_BASE_HP * 4.0 * hp_scale)
            speed = ENEMY_BASE_SPEED * 0.9 * speed_scale
        elif kind == "shooter":
            hp = int(ENEMY_BASE_HP * 1.4 * hp_scale)
            speed = ENEMY_BASE_SPEED * 1.0 * speed_scale
        elif kind == "boss":
            hp = int(ENEMY_BASE_HP * 10 * hp_scale)
            speed = ENEMY_BASE_SPEED * 1.4 * speed_scale
        else:
            hp = int(ENEMY_BASE_HP * 1.0 * hp_scale)
            speed = ENEMY_BASE_SPEED * 1.0 * speed_scale

        self.enemies.append(Enemy(x, y, hp, speed, kind))

    def roll_levelup(self):
        self.levelup_options = random.sample(POWERUPS, k=3)
        self.state = STATE_LEVEL_UP
        audio.play_sfx(audio.snd_level_up)

    def get_camera(self):
        return (self.player.x - WIDTH // 2, self.player.y - HEIGHT // 2)

    def draw_background(self, cam):
        # Properly draw space starfield behind everything
        ox, oy = cam
        for s in self.stars:
            x = int(s["x"] - ox)
            y = int(s["y"] - oy)
            if -5 <= x <= self.w + 5 and -5 <= y <= self.h + 5:
                phase = s["blink"]
                intensity = 0.5 + 0.5 * math.sin(phase * math.tau)
                base_col = (200, 200, 255) if s["r"] == 1 else (140, 140, 200)
                col = tuple(min(255, int(c * (0.7 + 0.6 * intensity))) for c in base_col)
                if s["shape"] == "diamond":
                    pts = [
                        (x, y - s["r"]),
                        (x + s["r"] + 1, y),
                        (x, y + s["r"] + 1),
                        (x - s["r"] - 1, y),
                    ]
                    pygame.draw.polygon(self.screen, col, pts)
                elif s["shape"] == "wide":
                    pygame.draw.rect(self.screen, col, (x, y, s["r"] + 3, s["r"]))
                else:
                    pygame.draw.rect(self.screen, col, (x, y, s["r"], s["r"]))
        # shimmering pops
        for f in list(self.star_flashes):
            fx = int(f["x"] - ox)
            fy = int(f["y"] - oy)
            if -5 <= fx <= self.w + 5 and -5 <= fy <= self.h + 5:
                alpha = int(255 * (f["life"] / f["life_max"]))
                flash_surf = pygame.Surface((f["r"] * 2, f["r"] * 2), pygame.SRCALPHA)
                pygame.draw.circle(flash_surf, (255, 255, 255, alpha), (f["r"], f["r"]), f["r"])
                self.screen.blit(flash_surf, (fx - f["r"], fy - f["r"]))

    def draw(self):
        self.screen.fill(COLOR_BG)
        if self.state == STATE_MENU:
            self.draw_menu()
        elif self.state in (STATE_PLAYING, STATE_LEVEL_UP, STATE_GAME_OVER, STATE_PAUSED, STATE_DEAD_ANIM):
            self.draw_game_world()
            self.draw_boost_overlay()
            self.draw_hud()
            if self.state == STATE_LEVEL_UP:
                self.draw_levelup()
            if self.state == STATE_GAME_OVER:
                self.draw_game_over()
            if self.state == STATE_PAUSED:
                self.draw_pause_overlay()
        elif self.state == STATE_SETTINGS:
            self.draw_settings()
        pygame.display.flip()

    def draw_menu(self):
        cam = (0, 0)
        self.draw_background(cam)
        title = self.font_large.render("STARLIGHT ECLIPSE", True, COLOR_WHITE)
        self.screen.blit(title, (self.w // 2 - title.get_width() // 2, self.h // 3 - 40))
        self.btn_start.draw(self.screen)
        self.btn_settings.draw(self.screen)
        self.btn_quit.draw(self.screen)

    def draw_game_world(self):
        cam = self.get_camera()
        self.draw_background(cam)

        for o in self.orbs:
            o.draw(self.screen, cam)
        for g in self.gas_pickups:
            g.draw(self.screen, cam)
        for e in self.enemies:
            e.draw(self.screen, cam)
        for b in self.bullets:
            b.draw(self.screen, cam)
        for eb in self.enemy_bullets:
            sx = int(eb["x"] - cam[0])
            sy = int(eb["y"] - cam[1])
            pygame.draw.circle(self.screen, COLOR_RED, (sx, sy), eb["r"])
        self.player.draw(self.screen)
        self._draw_death_fx(cam)
        self._draw_damage_texts(cam)

    def draw_boost_overlay(self):
        if self.boost_effect_timer <= 0:
            return
        strength = min(1.0, self.boost_effect_timer / 3.0)
        thickness = 90
        overlay = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        for i in range(thickness):
            alpha = int(140 * (1 - i / thickness) * strength)
            color = (80, 240, 220, alpha)
            pygame.draw.rect(overlay, color, (i, 0, 1, self.h))
            pygame.draw.rect(overlay, color, (self.w - i - 1, 0, 1, self.h))
        self.screen.blit(overlay, (0, 0))

    def _draw_death_fx(self, cam):
        for fx in self.death_fx:
            sx = int(fx["x"] - cam[0])
            sy = int(fx["y"] - cam[1])
            r = max(2, int(7 * fx["life"]))
            pygame.draw.circle(self.screen, COLOR_RED, (sx, sy), r)

    def _draw_damage_texts(self, cam):
        for txt in self.damage_texts:
            sx = int(txt["x"] - cam[0])
            sy = int(txt["y"] - cam[1])
            alpha = int(255 * (txt["life"] / 0.6))
            surf = self.font_small.render(str(txt["val"]), True, COLOR_YELLOW)
            surf.set_alpha(alpha)
            self.screen.blit(surf, (sx, sy))

    def draw_hud(self):
        base_y = self.btn_pause.rect.y + 6
        # LVL label on left of HP
        lvl_txt = self.font_small.render(f"LVL {self.player.level}", True, COLOR_WHITE)
        lvl_x = 16
        self.screen.blit(lvl_txt, (lvl_x, base_y))
        # hearts aligned to pause row
        x = lvl_x + lvl_txt.get_width() + 16
        spacing = 24
        for i in range(self.player.max_hearts):
            col = COLOR_RED if i < self.player.hearts else COLOR_DARK_GRAY
            cx = x + i * spacing
            cy = base_y + 2
            pygame.draw.polygon(self.screen, col, [(cx + 6, cy + 6), (cx, cy + 12), (cx + 6, cy + 18), (cx + 12, cy + 12)])
        # xp bar
        bw2, bh2 = self.w - 200, 10
        x2, y2 = 100, self.h - 30
        pygame.draw.rect(self.screen, COLOR_DARK_GRAY, (x2, y2, bw2, bh2))
        xp_ratio = self.player.xp / max(1, self.player.xp_to_level)
        pygame.draw.rect(self.screen, COLOR_GREEN, (x2, y2, int(bw2 * xp_ratio), bh2))
        # time
        t = int(self.elapsed_time)
        m, s = t // 60, t % 60
        timer_text = self.font_small.render(f"{m:02d}:{s:02d}", True, COLOR_WHITE)
        time_y = base_y
        self.screen.blit(timer_text, (self.w // 2 - timer_text.get_width() // 2, time_y))
        # kills aligned with pause button row
        kills_txt = self.font_small.render(f"KILLS {self.kills}", True, COLOR_WHITE)
        kills_y = base_y
        kills_x = self.btn_pause.rect.x - kills_txt.get_width() - 14
        self.screen.blit(kills_txt, (kills_x, kills_y))
        if self.state == STATE_PLAYING:
            self.btn_pause.draw(self.screen)

        # ammo row under HP
        ammo_y = base_y + 26
        if self.player.reload_timer > 0:
            ammo_txt = self.font_small.render("RELOADING...", True, COLOR_YELLOW)
        else:
            ammo_txt = self.font_small.render(f"AMMO {self.player.ammo}/{self.player.mag_size}", True, COLOR_WHITE)
        self.screen.blit(ammo_txt, (lvl_x, ammo_y))

    def draw_levelup(self):
        overlay = pygame.Surface((self.w, self.h))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        title = self.font_large.render("LEVEL UP", True, COLOR_YELLOW)
        self.screen.blit(title, (self.w // 2 - title.get_width() // 2, self.h // 4))
        w = 320
        h = 150
        gap = 24
        total_w = 3 * w + 2 * gap
        start_x = WIDTH // 2 - total_w // 2
        y = HEIGHT // 2 - h // 2
        mouse_pos = pygame.mouse.get_pos()
        for i, pid in enumerate(self.levelup_options):
            rect = pygame.Rect(start_x + i * (w + gap), y, w, h)
            is_hover = rect.collidepoint(mouse_pos)
            col = COLOR_DARK_GRAY if not is_hover else COLOR_GRAY
            pygame.draw.rect(self.screen, col, rect, border_radius=8)
            name = powerup_name(pid)
            desc = powerup_desc(pid)
            t1 = self.font_small.render(name, True, COLOR_WHITE)
            t2 = self.font_tiny.render(desc, True, COLOR_WHITE)
            self.screen.blit(
                t1,
                (rect.centerx - t1.get_width() // 2, rect.y + rect.height // 2 - t1.get_height()),
            )
            self.screen.blit(
                t2,
                (rect.centerx - t2.get_width() // 2, rect.y + rect.height // 2 + 4),
            )

    def draw_game_over(self):
        overlay = pygame.Surface((self.w, self.h))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        title = self.font_large.render("GAME OVER", True, COLOR_RED)
        self.screen.blit(title, (self.w // 2 - title.get_width() // 2, self.h // 4))

        t = int(self.elapsed_time)
        m, s = t // 60, t % 60
        lines = [
            f"Time: {m:02d}:{s:02d}",
            f"Kills: {self.kills}",
            f"Level: {self.player.level}",
        ]
        for i, line in enumerate(lines):
            tx = self.font_medium.render(line, True, COLOR_WHITE)
            self.screen.blit(
                tx,
                (
                    WIDTH // 2 - tx.get_width() // 2,
                    HEIGHT // 3 + 60 + i * 40,
                ),
            )

        self.btn_restart.draw(self.screen)
        self.btn_main_menu.draw(self.screen)

    def draw_pause_overlay(self):
        overlay = pygame.Surface((self.w, self.h))
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        t = self.font_large.render("PAUSED", True, COLOR_WHITE)
        title_y = self.h // 2 - t.get_height() - 40
        self.screen.blit(t, (self.w // 2 - t.get_width() // 2, title_y))
        # buttons under the label
        self.btn_pause_resume.draw(self.screen)
        self.btn_pause_reset.draw(self.screen)
        self.btn_pause_quit.draw(self.screen)
        # volume sliders in pause
        label_music = self.font_small.render("MUSIC", True, COLOR_WHITE)
        self.screen.blit(label_music, (self.pause_music_rect.x, self.pause_music_rect.y - 16))
        pygame.draw.rect(self.screen, COLOR_DARK_GRAY, self.pause_music_rect)
        filled_m = int(self.pause_music_rect.width * self.music_volume)
        pygame.draw.rect(self.screen, COLOR_GREEN, (self.pause_music_rect.x, self.pause_music_rect.y, filled_m, self.pause_music_rect.height))

        label_sfx = self.font_small.render("SFX", True, COLOR_WHITE)
        self.screen.blit(label_sfx, (self.pause_sfx_rect.x, self.pause_sfx_rect.y - 16))
        pygame.draw.rect(self.screen, COLOR_DARK_GRAY, self.pause_sfx_rect)
        filled_s = int(self.pause_sfx_rect.width * self.sfx_volume)
        pygame.draw.rect(self.screen, COLOR_GREEN, (self.pause_sfx_rect.x, self.pause_sfx_rect.y, filled_s, self.pause_sfx_rect.height))

    def _dropdown_rect(self):
        option_h = 34
        total_h = option_h * len(WINDOW_SIZES)
        return pygame.Rect(self.btn_window_dropdown.rect.x, self.btn_window_dropdown.rect.bottom + 6, self.btn_window_dropdown.rect.width, total_h)

    def draw_settings(self):
        cam = (0, 0)
        self.draw_background(cam)
        overlay = pygame.Surface((self.w, self.h))
        overlay.set_alpha(220)
        overlay.fill((10, 10, 30))
        self.screen.blit(overlay, (0, 0))
        title = self.font_large.render("SETTINGS", True, COLOR_WHITE)
        self.screen.blit(title, (self.w // 2 - title.get_width() // 2, self.h // 4))
        # BG music slider
        label_bg = self.font_small.render("BG MUSIC", True, COLOR_WHITE)
        self.screen.blit(
            label_bg,
            (self.slider_bg_rect.x, self.slider_bg_rect.y - 18),
        )
        pygame.draw.rect(self.screen, COLOR_DARK_GRAY, self.slider_bg_rect)
        filled_w = int(self.slider_bg_rect.width * self.music_volume)
        pygame.draw.rect(
            self.screen,
            COLOR_GREEN,
            (self.slider_bg_rect.x, self.slider_bg_rect.y, filled_w, self.slider_bg_rect.height),
        )

        # SFX slider
        label_sfx = self.font_small.render("SFX", True, COLOR_WHITE)
        self.screen.blit(
            label_sfx,
            (self.slider_sfx_rect.x, self.slider_sfx_rect.y - 18),
        )
        pygame.draw.rect(self.screen, COLOR_DARK_GRAY, self.slider_sfx_rect)
        filled_w2 = int(self.slider_sfx_rect.width * self.sfx_volume)
        pygame.draw.rect(
            self.screen,
            COLOR_GREEN,
            (self.slider_sfx_rect.x, self.slider_sfx_rect.y, filled_w2, self.slider_sfx_rect.height),
        )

        # windowed dropdown + fullscreen button under title
        self.btn_window_dropdown.text = f"WINDOWED {'▲' if self.show_size_dropdown else '▼'}"
        self.btn_fullscreen.text = "FULLSCREEN"
        # simple active tint when fullscreen
        self.btn_fullscreen.base_color = COLOR_GRAY if self.fullscreen else COLOR_DARK_GRAY
        self.btn_fullscreen.hover_color = COLOR_WHITE if self.fullscreen else COLOR_GRAY
        self.btn_window_dropdown.draw(self.screen)
        self.btn_fullscreen.draw(self.screen)
        if self.show_size_dropdown:
            drop_rect = self._dropdown_rect()
            option_h = 34
            for i, (w, h) in enumerate(WINDOW_SIZES):
                r = pygame.Rect(drop_rect.x, drop_rect.y + i * option_h, drop_rect.width, option_h)
                is_selected = i == self.window_size_index and not self.fullscreen
                col = COLOR_GRAY if is_selected else COLOR_DARK_GRAY
                pygame.draw.rect(self.screen, col, r, border_radius=6)
                txt = self.font_small.render(f"{w}x{h}", True, COLOR_WHITE)
                self.screen.blit(txt, (r.x + 10, r.y + r.height // 2 - txt.get_height() // 2))

        self.btn_settings_back.draw(self.screen)
