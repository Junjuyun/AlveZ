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
STAR_COUNT = 2600

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
    def __init__(self, rect, text, font, base_color, hover_color):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.base_color = base_color
        self.hover_color = hover_color

    def draw(self, surf):
        mouse_pos = pygame.mouse.get_pos()
        is_hover = self.rect.collidepoint(mouse_pos)
        color = self.hover_color if is_hover else self.base_color
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
    def __init__(self, x, y, vx, vy, damage, speed):
        self.x = x
        self.y = y
        l = math.hypot(vx, vy) or 1
        self.vx = vx / l * speed
        self.vy = vy / l * speed
        self.damage = damage
        self.radius = BULLET_RADIUS
        self.piercing = False
        self.pierce_left = 0

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
        self.radius = ENEMY_RADIUS
        self.kind = kind

    def update(self, dt, player_pos):
        px, py = player_pos
        dx = px - self.x
        dy = py - self.y
        l = math.hypot(dx, dy) or 1
        self.x += dx / l * self.speed * dt * FPS
        self.y += dy / l * self.speed * dt * FPS

    def draw(self, surf, cam):
        sx = int(self.x - cam[0])
        sy = int(self.y - cam[1])
        if self.kind == "tank":
            col = COLOR_ENEMY_TANK
        elif self.kind == "fast":
            col = COLOR_ENEMY_FAST
        else:
            col = COLOR_ENEMY
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

        # gas boost
        self.gas_timer = 0.0
        self.gas_speed_mult = 1.8
        self.gas_fire_mult = 1.7

        # progression
        self.level = 1
        self.xp = 0
        self.xp_to_level = XP_PER_LEVEL
        self.kills = 0

        self.level_ups_since_reward = 0
        self.invuln = 0.0  # seconds of i-frames

    @property
    def hp(self):
        return self.hearts

    @property
    def max_hp(self):
        return self.max_hearts

    def update(self, dt, keys):
        if self.invuln > 0:
            self.invuln -= dt

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
        return self.time_since_shot >= self.fire_cd

    def shoot(self, target_world_pos):
        self.time_since_shot = 0.0
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
        for a in angles:
            vx = math.cos(a)
            vy = math.sin(a)
            b = Bullet(self.x, self.y, vx, vy, self.damage, self.bullet_speed)
            b.piercing = self.piercing
            b.pierce_left = 1 if self.piercing else 0
            bullets.append(b)
        return bullets

    def draw(self, surf):
        px = WIDTH // 2
        py = HEIGHT // 2
        mx, my = pygame.mouse.get_pos()
        ang = math.atan2(my - py, mx - px)
        ca = math.cos(ang)
        sa = math.sin(ang)
        r = self.radius
        p1 = (px + ca * r, py + sa * r)
        p2 = (px - sa * r * 0.7, py + ca * r * 0.7)
        p3 = (px + sa * r * 0.7, py - ca * r * 0.7)
        pygame.draw.polygon(surf, COLOR_PLAYER, [p1, p2, p3])

    def take_damage(self, hearts=1):
        if self.invuln > 0:
            return
        self.hearts = clamp(self.hearts - hearts, 0, self.max_hearts)
        self.invuln = 1.0  # 1s i-frames after hit

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
    "damage",
    "speed",
    "fire_rate",
    "heart_container",
    "heal",
    "twin_shot",
    "triple_spread",
    "pierce",
]


def apply_powerup(player: Player, pid: str):
    if pid == "damage":
        player.damage += 5
    elif pid == "speed":
        player.base_speed += 0.5
        player.speed = player.base_speed
    elif pid == "fire_rate":
        player.fire_rate *= 1.15
        player.fire_cd = 1.0 / player.fire_rate
    elif pid == "heart_container":
        player.add_heart_container()
    elif pid == "heal":
        player.heal(2)
    elif pid == "twin_shot":
        player.bullet_count = max(player.bullet_count, 2)
        player.spread_angle_deg = max(player.spread_angle_deg, 10)
    elif pid == "triple_spread":
        player.bullet_count = max(player.bullet_count, 3)
        player.spread_angle_deg = max(player.spread_angle_deg, 18)
    elif pid == "pierce":
        player.piercing = True


def powerup_name(pid: str) -> str:
    names = {
        "damage": "Overcharged Rounds",
        "speed": "Thrusters",
        "fire_rate": "Rapid Fire",
        "heart_container": "Extra Heart",
        "heal": "Heal",
        "twin_shot": "Twin Shot",
        "triple_spread": "Triple Spread",
        "pierce": "Piercing Bullets",
    }
    return names[pid]


def powerup_desc(pid: str) -> str:
    desc = {
        "damage": "+5 bullet damage",
        "speed": "+0.5 move speed",
        "fire_rate": "Shoot faster",
        "heart_container": "+1 max heart, full heal",
        "heal": "Restore 2 hearts",
        "twin_shot": "Fire 2 bullets",
        "triple_spread": "Fire 3 bullets in a spread",
        "pierce": "Bullets pierce one enemy",
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

        # larger pixel font
        try:
            self.font_large = pygame.font.SysFont("PressStart2P", 48)
            self.font_medium = pygame.font.SysFont("PressStart2P", 24)
            self.font_small = pygame.font.SysFont("PressStart2P", 16)
        except Exception:
            self.font_large = pygame.font.SysFont("consolas", 48)
            self.font_medium = pygame.font.SysFont("consolas", 24)
            self.font_small = pygame.font.SysFont("consolas", 16)

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
        )

        self.btn_settings_back = Button(
            (self.w // 2 - 100, self.h // 2 + 120, 200, 44),
            "BACK",
            self.font_medium,
            COLOR_DARK_GRAY,
            COLOR_GRAY,
        )

        # starfield
        self.stars = [
            (
                random.uniform(-WORLD_SIZE / 2, WORLD_SIZE / 2),
                random.uniform(-WORLD_SIZE / 2, WORLD_SIZE / 2),
                random.randint(1, 4),
            )
            for _ in range(STAR_COUNT)
        ]

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
        self.fullscreen = False
        self.window_size_index = 0

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
        self.btn_pause = Button((self.w - 70, 16, 50, 32), "||", self.font_small, COLOR_DARK_GRAY, COLOR_GRAY)
        self.btn_settings_back = Button((self.w // 2 - 100, self.h // 2 + 120, 200, 44), "BACK", self.font_medium, COLOR_DARK_GRAY, COLOR_GRAY)

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
                # fullscreen toggle
                if mx < self.w // 2 - 110 and my > self.h // 2 + 70:
                    self.fullscreen = not self.fullscreen
                    self._apply_display_mode()
                # window size dropdown (simple cycle)
                if mx > self.w // 2 + 30 and my > self.h // 2 + 70:
                    self.window_size_index = (self.window_size_index + 1) % len(WINDOW_SIZES)
                    self.w, self.h = WINDOW_SIZES[self.window_size_index]
                    self._apply_display_mode()
        elif self.state == STATE_PLAYING:
            if self.btn_pause.is_clicked(e):
                audio.play_sfx(audio.snd_pause)
                self.state = STATE_PAUSED
        elif self.state == STATE_PAUSED:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                audio.play_sfx(audio.snd_unpause)
                self.state = STATE_PLAYING
        elif self.state == STATE_DEAD_ANIM:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                self.state = STATE_GAME_OVER

    def update(self, dt):
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

        # spawn progression: unlock variants over time
        self.spawn_timer += dt
        interval = 1.0 / self.enemy_spawn_rate
        while self.spawn_timer >= interval:
            self.spawn_timer -= interval
            self.spawn_enemy()

        for e in self.enemies:
            e.update(dt, (self.player.x, self.player.y))
        for o in self.orbs:
            o.update(dt, (self.player.x, self.player.y))

        # bullet-enemy
        for b in list(self.bullets):
            for en in list(self.enemies):
                if circle_collision(b.x, b.y, b.radius, en.x, en.y, en.radius):
                    en.hp -= b.damage
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

    def _spawn_death_fx(self, x, y):
        self.death_fx.clear()
        for _ in range(40):
            ang = random.uniform(0, math.tau)
            spd = random.uniform(80, 180)
            self.death_fx.append({
                "x": x, "y": y,
                "vx": math.cos(ang) * spd,
                "vy": math.sin(ang) * spd,
                "life": random.uniform(0.4, 0.8),
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
        if t < 60:
            kind = "normal"
        elif t < 120:
            kind = random.choices(
                ["normal", "fast"], weights=[0.7, 0.3]
            )[0]
        else:
            kind = random.choices(
                ["normal", "fast", "tank"], weights=[0.5, 0.3, 0.2]
            )[0]

        if kind == "tank":
            hp = int(ENEMY_BASE_HP * 3)
            speed = ENEMY_BASE_SPEED * 0.7
        elif kind == "fast":
            hp = int(ENEMY_BASE_HP * 0.7)
            speed = ENEMY_BASE_SPEED * 1.8
        else:
            hp = ENEMY_BASE_HP
            speed = ENEMY_BASE_SPEED

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
        for sx, sy, r in self.stars:
            x = int(sx - ox)
            y = int(sy - oy)
            if -5 <= x <= self.w + 5 and -5 <= y <= self.h + 5:
                color = (200, 200, 255) if r == 1 else (120, 120, 180)
                pygame.draw.rect(self.screen, color, (x, y, r, r))

    def draw(self):
        self.screen.fill(COLOR_BG)
        if self.state == STATE_MENU:
            self.draw_menu()
        elif self.state in (STATE_PLAYING, STATE_LEVEL_UP, STATE_GAME_OVER, STATE_PAUSED, STATE_DEAD_ANIM):
            self.draw_game_world()
            self.draw_hud()
            if self.state == STATE_LEVEL_UP:
                self.draw_levelup()
            if self.state == STATE_GAME_OVER:
                self.draw_game_over()
            if self.state in (STATE_PAUSED, STATE_DEAD_ANIM):
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
        self.player.draw(self.screen)
        self._draw_death_fx(cam)

    def _draw_death_fx(self, cam):
        for fx in self.death_fx:
            sx = int(fx["x"] - cam[0])
            sy = int(fx["y"] - cam[1])
            r = max(1, int(4 * fx["life"]))
            pygame.draw.circle(self.screen, COLOR_RED, (sx, sy), r)

    def draw_hud(self):
        # hearts at top-left
        x = 16
        y = 14
        spacing = 24
        for i in range(self.player.max_hearts):
            col = COLOR_RED if i < self.player.hearts else COLOR_DARK_GRAY
            cx = x + i * spacing
            pygame.draw.polygon(self.screen, col, [(cx + 6, y + 6), (cx, y + 12), (cx + 6, y + 18), (cx + 12, y + 12)])
        lvl_txt = self.font_small.render(f"LVL {self.player.level}", True, COLOR_WHITE)
        self.screen.blit(lvl_txt, (16, y + 30))
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
        self.screen.blit(timer_text, (self.w // 2 - timer_text.get_width() // 2, 8))
        # kills aligned with pause button
        kills_txt = self.font_small.render(f"KILLS {self.kills}", True, COLOR_WHITE)
        self.screen.blit(kills_txt, (self.btn_pause.rect.x - kills_txt.get_width() - 10, self.btn_pause.rect.y + 6))
        if self.state == STATE_PLAYING:
            self.btn_pause.draw(self.screen)

    def draw_levelup(self):
        overlay = pygame.Surface((self.w, self.h))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        title = self.font_large.render("LEVEL UP", True, COLOR_YELLOW)
        self.screen.blit(title, (self.w // 2 - title.get_width() // 2, self.h // 4))
        w = 260
        h = 120
        gap = 20
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
            t2 = self.font_small.render(desc, True, COLOR_WHITE)
            self.screen.blit(
                t1,
                (rect.centerx - t1.get_width() // 2, rect.y + 16),
            )
            self.screen.blit(
                t2,
                (rect.centerx - t2.get_width() // 2, rect.y + 52),
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
        self.screen.blit(t, (self.w // 2 - t.get_width() // 2, self.h // 2 - t.get_height() // 2))

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

        # fullscreen/window toggle indicators
        fs_label = self.font_small.render(f"MODE: {'FULL' if self.fullscreen else 'WINDOWED'}", True, COLOR_WHITE)
        self.screen.blit(fs_label, (self.w // 2 - fs_label.get_width() // 2, self.h // 2 + 60))
        size_label = self.font_small.render(f"SIZE: {self.w}x{self.h}", True, COLOR_WHITE)
        self.screen.blit(size_label, (self.w // 2 - size_label.get_width() // 2, self.h // 2 + 80))

        self.btn_settings_back.draw(self.screen)
