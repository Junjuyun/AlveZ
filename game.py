import os
import math
import random
import sys
import pygame
from audio import audio
from game_constants import *
from game_entities import Bullet, Enemy, XPOrb, GasPickup, EvolutionPickup, Player
from game_powerups import POWERUPS, EVOLUTIONS, apply_powerup, apply_evolution, powerup_name, powerup_desc, evolution_name, evolution_desc, available_powerups
from game_ui import Button


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
        self.slider_sfx_rect = pygame.Rect(self.w // 2 - slider_w // 2, base_y + 60, slider_w, slider_h)
        # pause overlay sliders
        p_slider_w = 260
        p_slider_h = 10
        p_base_y = self.h // 2 + 110
        self.pause_music_rect = pygame.Rect(self.w // 2 - p_slider_w // 2, p_base_y, p_slider_w, p_slider_h)
        self.pause_sfx_rect = pygame.Rect(self.w // 2 - p_slider_w // 2, p_base_y + 28, p_slider_w, p_slider_h)
        self.fullscreen = False
        self.window_size_index = 0
        self.show_size_dropdown = False

        # dev mode controls
        self.dev_mode = False
        self.dev_power_queue = []

        btn_y = self.h // 4 + 80
        self.btn_window_dropdown = Button(
            (self.w // 2 - 220, btn_y, 200, 44),
            "WINDOWED ???",
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
        audio.snd_boss_explosion = load("boss-explosion.wav")
        audio.snd_menu_click = load("main-menu-click.wav")
        audio.snd_pickup_boost = load("pickup-boost.wav")
        audio.snd_pickup_boss = load("pickup-from-boss.wav")

        audio.music_menu = music_path("menu-bg.mp3")
        audio.music_ingame = music_path("ingame-bg.mp3")
        audio.music_defeat = music_path("defeat-bg.wav")

    def reset_game(self):
        self.player = Player(0, 0)
        self.bullets = []
        self.enemies = []
        self.orbs = []
        self.gas_pickups = []
        self.evolution_pickups = []
        self.minions = []
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
        self.boost_dir = (0.0, -1.0)
        self.prev_boosting = False
        self.status_particles = []
        self.boost_particles = []
        self.damage_texts = []
        self.laser_segment = None
        self.evolution_options = []
        self.bosses_spawned = 0
        self.vision_dim = 0.22
        self.view_zoom = 1.0

        if self.dev_mode:
            self.player.level = 40
            self.player.xp = 0
            self.player.xp_to_level = XP_PER_LEVEL
            self.dev_power_queue = list(POWERUPS)
        else:
            self.dev_power_queue.clear()

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
        self.btn_window_dropdown = Button((self.w // 2 - 220, btn_y, 200, 44), "WINDOWED ???", self.font_small, COLOR_DARK_GRAY, COLOR_GRAY, COLOR_WHITE)
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
        self.slider_sfx_rect.update(self.w // 2 - slider_w // 2, base_y + 60, slider_w, slider_h)
        btn_y = self.h // 4 + 80
        self.btn_window_dropdown.rect.update(self.w // 2 - 220, btn_y, 200, 44)
        self.btn_fullscreen.rect.update(self.w // 2 + 20, btn_y, 200, 44)

    def _layout_pause_sliders(self):
        p_slider_w = 220
        p_slider_h = 10
        title_y = self.h // 2 - self.font_large.get_height() - 120
        start_y = title_y + self.font_large.get_height() + 40
        self.pause_music_rect.update(self.w // 2 - p_slider_w // 2, start_y, p_slider_w, p_slider_h)
        self.pause_sfx_rect.update(self.w // 2 - p_slider_w // 2, start_y + 50, p_slider_w, p_slider_h)
        btn_base_y = start_y + 90
        self.btn_pause_resume.rect.update(self.w // 2 - 110, btn_base_y, 220, 44)
        self.btn_pause_reset.rect.update(self.w // 2 - 110, btn_base_y + 50, 220, 44)
        self.btn_pause_quit.rect.update(self.w // 2 - 110, btn_base_y + 100, 220, 44)
        return title_y

    def handle_event(self, e):
        if self.state == STATE_MENU:
            if self.btn_start.is_clicked(e):
                audio.play_sfx(audio.snd_menu_click)
                self.reset_game()
                if self.dev_mode:
                    self.roll_levelup()
                else:
                    self.state = STATE_PLAYING
            elif self.btn_settings.is_clicked(e):
                audio.play_sfx(audio.snd_menu_click)
                self.state = STATE_SETTINGS
            elif self.btn_quit.is_clicked(e):
                audio.play_sfx(audio.snd_menu_click)
                pygame.event.post(pygame.event.Event(pygame.QUIT))
        elif self.state == STATE_GAME_OVER:
            if self.btn_restart.is_clicked(e):
                audio.play_sfx(audio.snd_menu_click)
                self.reset_game()
                if self.dev_mode:
                    self.roll_levelup()
                else:
                    self.state = STATE_PLAYING
            elif self.btn_main_menu.is_clicked(e):
                audio.play_sfx(audio.snd_menu_click)
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
                        if self.dev_mode and self.dev_power_queue:
                            self.roll_levelup()
                        else:
                            self.state = STATE_PLAYING
                        break
        elif self.state == STATE_EVOLUTION:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                mx, my = e.pos
                w = 260
                h = 120
                gap = 20
                total_w = 3 * w + 2 * gap
                start_x = WIDTH // 2 - total_w // 2
                y = HEIGHT // 2 - h // 2
                for i, eid in enumerate(self.evolution_options):
                    rect = pygame.Rect(start_x + i * (w + gap), y, w, h)
                    if rect.collidepoint(mx, my):
                        apply_evolution(self.player, eid)
                        self.state = STATE_PLAYING
                        break
        elif self.state == STATE_SETTINGS:
            if self.btn_settings_back.is_clicked(e):
                audio.play_sfx(audio.snd_menu_click)
                self.state = STATE_MENU
                self.show_size_dropdown = False
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                mx, my = e.pos
                # BG volume slider
                if self.slider_bg_rect.collidepoint(mx, my):
                    audio.play_sfx(audio.snd_menu_click)
                    t = (mx - self.slider_bg_rect.x) / self.slider_bg_rect.width
                    self.music_volume = clamp(t, 0.0, 1.0)
                    audio.set_music_volume(self.music_volume)
                # SFX volume slider
                if self.slider_sfx_rect.collidepoint(mx, my):
                    audio.play_sfx(audio.snd_menu_click)
                    t = (mx - self.slider_sfx_rect.x) / self.slider_sfx_rect.width
                    self.sfx_volume = clamp(t, 0.0, 1.0)
                    audio.set_sfx_volume(self.sfx_volume)
                if self.btn_fullscreen.is_clicked(e):
                    audio.play_sfx(audio.snd_menu_click)
                    self.fullscreen = not self.fullscreen
                    self.show_size_dropdown = False
                    self._apply_display_mode()
                elif self.btn_window_dropdown.is_clicked(e):
                    audio.play_sfx(audio.snd_menu_click)
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
                            audio.play_sfx(audio.snd_menu_click)
                    else:
                        self.show_size_dropdown = False

                # dev toggle
                dev_rect = self._dev_toggle_rect()
                if dev_rect.collidepoint(mx, my):
                    audio.play_sfx(audio.snd_menu_click)
                    self.dev_mode = not self.dev_mode
                    if self.dev_mode:
                        self.dev_power_queue = list(POWERUPS)
                    else:
                        self.dev_power_queue.clear()
        elif self.state == STATE_PLAYING:
            if e.type == pygame.KEYDOWN and e.key == pygame.K_r:
                self.player.start_reload()
            if self.btn_pause.is_clicked(e):
                audio.play_sfx(audio.snd_pause)
                self.state = STATE_PAUSED
        elif self.state == STATE_PAUSED:
            self._layout_pause_sliders()
            if self.btn_pause_resume.is_clicked(e):
                audio.play_sfx(audio.snd_unpause)
                self.state = STATE_PLAYING
            elif self.btn_pause_reset.is_clicked(e):
                self.reset_game()
                audio.play_sfx(audio.snd_unpause)
                if self.dev_mode:
                    self.roll_levelup()
                else:
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
        if self.state in (STATE_PLAYING, STATE_LEVEL_UP, STATE_PAUSED, STATE_EVOLUTION):
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

        # manage laser ultimate timers
        if self.player.laser_cooldown > 0:
            self.player.laser_cooldown = max(0.0, self.player.laser_cooldown - dt)
        if self.player.laser_active:
            self.player.laser_timer -= dt
            if self.player.laser_timer <= 0:
                self.player.laser_active = False
                self.player.laser_cooldown = self.player.laser_cooldown_max
        elif keys[pygame.K_SPACE] and self.player.laser_cooldown <= 0:
            self.player.laser_active = True
            self.player.laser_timer = self.player.laser_duration
            self.laser_segment = None

        # smooth zooming while boosting so the world shrinks slightly
        target_zoom = 0.82 if self.player.boosting else 1.0
        self.view_zoom += (target_zoom - self.view_zoom) * min(1.0, dt * 6.0)
        self.view_zoom = clamp(self.view_zoom, 0.7, 1.1)

        view_half_w = (self.w / max(0.1, self.view_zoom)) * 0.5
        view_half_h = (self.h / max(0.1, self.view_zoom)) * 0.5
        cam = (self.player.x - view_half_w, self.player.y - view_half_h)

        # reset boost trail direction on boost start to current movement
        if self.player.boosting and not self.prev_boosting:
            mdx, mdy = self.player.move_dir
            if abs(mdx) > 0.01 or abs(mdy) > 0.01:
                ml = math.hypot(mdx, mdy) or 1.0
                self.boost_dir = (mdx / ml, mdy / ml)
        self.prev_boosting = self.player.boosting

        # boost trail particles
        if self.player.boosting:
            target_dx, target_dy = self.player.move_dir
            if abs(target_dx) < 0.01 and abs(target_dy) < 0.01:
                target_dx, target_dy = self.boost_dir
            lerp = 0.25
            mdx = self.boost_dir[0] * (1 - lerp) + target_dx * lerp
            mdy = self.boost_dir[1] * (1 - lerp) + target_dy * lerp
            mag = math.hypot(mdx, mdy) or 1.0
            mdx, mdy = mdx / mag, mdy / mag
            self.boost_dir = (mdx, mdy)

            back_ang = math.atan2(mdy, mdx) + math.pi
            for _ in range(12):
                offset_ang = back_ang + random.uniform(-0.18, 0.18)
                spd = random.uniform(28, 70)
                size = random.uniform(self.player.radius * 0.5, self.player.radius * 0.9)
                self.boost_particles.append({
                    "x": self.player.x - mdx * self.player.radius * 1.02,
                    "y": self.player.y - mdy * self.player.radius * 1.02,
                    "vx": math.cos(offset_ang) * spd,
                    "vy": math.sin(offset_ang) * spd,
                    "life": random.uniform(0.05, 0.09),
                    "life_max": 0.09,
                    "color": (140, 240, 255),
                    "rot": random.uniform(0, math.tau),
                    "rot_speed": random.uniform(-9.0, 9.0),
                    "size": size,
                })

            # ease vision dimmer while boosting
            target_dim = 0.08 if self.player.boosting else 0.22
            self.vision_dim += (target_dim - self.vision_dim) * dt * 5.0

        # update particles
        for p in list(self.boost_particles):
            p["life"] -= dt
            p["x"] += p["vx"] * dt * FPS
            p["y"] += p["vy"] * dt * FPS
            p["vx"] *= 0.72
            p["vy"] *= 0.72
            p["rot"] = p.get("rot", 0.0) + p.get("rot_speed", 0.0) * dt
            if p["life"] <= 0:
                self.boost_particles.remove(p)
        for p in list(self.status_particles):
            p["life"] += dt
            p["x"] += p["vx"] * dt * FPS
            p["y"] += p["vy"] * dt * FPS
            p["vx"] *= 0.9
            p["vy"] *= 0.9
            if p["life"] >= p.get("life_max", 0.6):
                self.status_particles.remove(p)

        self._update_minions(dt)
        self._update_aura_orbs(dt)

        # shooting
        if pygame.mouse.get_pressed()[0] and self.player.can_shoot():
            mx, my = pygame.mouse.get_pos()
            world_target = (cam[0] + mx, cam[1] + my)
            new_bullets = self.player.shoot(world_target)
            self.bullets.extend(new_bullets)
            audio.play_sfx(audio.snd_shoot)

        if self.player.guided_shots and self.enemies:
            for b in self.bullets:
                if getattr(b, "guidance_disabled", False):
                    continue
                if not getattr(b, "target", None) or b.target not in self.enemies:
                    if not self.enemies:
                        break
                    b.target = min(self.enemies, key=lambda en: (en.x - b.x) ** 2 + (en.y - b.y) ** 2)
                tgt = b.target
                if not tgt or tgt not in self.enemies:
                    b.target = None
                    continue
                dx = tgt.x - b.x
                dy = tgt.y - b.y
                l = math.hypot(dx, dy)
                if l < 1.0:
                    ang = random.uniform(0, math.tau)
                    dx, dy = math.cos(ang), math.sin(ang)
                    l = 1.0
                base_speed = max(math.hypot(b.vx, b.vy), self.player.bullet_speed)
                desired_vx = dx / l
                desired_vy = dy / l
                # steer direction smoothly but keep constant speed
                cur_speed = math.hypot(b.vx, b.vy)
                if cur_speed > 0.01:
                    cur_vx = b.vx / cur_speed
                    cur_vy = b.vy / cur_speed
                else:
                    cur_vx = desired_vx
                    cur_vy = desired_vy
                steer = 0.32
                mixed_vx = cur_vx * (1 - steer) + desired_vx * steer
                mixed_vy = cur_vy * (1 - steer) + desired_vy * steer
                norm = math.hypot(mixed_vx, mixed_vy) or 1.0
                b.vx = mixed_vx / norm * base_speed
                b.vy = mixed_vy / norm * base_speed

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
            o.update(dt, self.player)

        # aura damage around the player
        if self.player.aura_radius > 0 and self.player.aura_dps > 0:
            rad_sq = self.player.aura_radius * self.player.aura_radius
            for en in self.enemies:
                dx = en.x - self.player.x
                dy = en.y - self.player.y
                if dx * dx + dy * dy <= rad_sq:
                    en.hp -= self.player.aura_dps * dt
                    if random.random() < 0.15:
                        self._emit_status_particle(en, "fire")

        self._apply_laser_damage(dt, cam)

        # ambient status particles while effects are active
        for en in self.enemies:
            if en.burn_timer > 0 and random.random() < 0.55:
                self._emit_status_particle(en, "fire")
            if en.poison_timer > 0 and random.random() < 0.55:
                self._emit_status_particle(en, "poison")
            if en.ice_timer > 0 and random.random() < 0.5:
                self._emit_status_particle(en, "ice")

        # DoT ticks with floating numbers and FX
        tick = 0.35
        for en in list(self.enemies):
            if en.burn_timer > 0 and en.burn_dps > 0:
                en.burn_tick += dt
                while en.burn_tick >= tick:
                    en.burn_tick -= tick
                    dmg = en.burn_dps * tick
                    en.hp -= dmg
                    self.damage_texts.append({"x": en.x + random.uniform(-4, 4), "y": en.y - 8, "val": max(1, int(dmg + 0.5)), "life": 0.5, "color": (255, 110, 80)})
                    self._spawn_status_fx(en.x, en.y, kind="fire")
            if en.poison_timer > 0 and en.poison_dps > 0:
                en.poison_tick += dt
                while en.poison_tick >= tick:
                    en.poison_tick -= tick
                    dmg = en.poison_dps * tick
                    en.hp -= dmg
                    self.damage_texts.append({"x": en.x + random.uniform(-4, 4), "y": en.y - 8, "val": max(1, int(dmg + 0.5)), "life": 0.5, "color": (140, 255, 160)})
                    self._spawn_status_fx(en.x, en.y, kind="poison")
            if en.ice_timer > 0 and en.ice_dps > 0:
                en.ice_tick += dt
                while en.ice_tick >= tick:
                    en.ice_tick -= tick
                    dmg = en.ice_dps * tick
                    en.hp -= dmg
                    self.damage_texts.append({"x": en.x + random.uniform(-4, 4), "y": en.y - 8, "val": max(1, int(dmg + 0.5)), "life": 0.5, "color": (170, 210, 255)})
                    self._spawn_status_fx(en.x, en.y, kind="ice")

        # DoT deaths
        for en in list(self.enemies):
            if en.hp <= 0:
                self.kills += 1
                self.player.kills += 1
                self.orbs.append(XPOrb(en.x, en.y, XP_PER_ORB))
                if random.random() < 0.05:
                    self.gas_pickups.append(GasPickup(en.x, en.y))
                if self.player.burn_chain:
                    for other in self.enemies:
                        if other is en:
                            continue
                        dx = other.x - en.x
                        dy = other.y - en.y
                        if dx * dx + dy * dy <= 140 * 140:
                            other.burn_timer = max(other.burn_timer, 3.0)
                            other.burn_dps = max(other.burn_dps, self.player.damage * 0.2 * self.player.burn_bonus_mult)
                if getattr(en, "kind", "") == "boss":
                    self._spawn_evolution_pickup(en.x, en.y)
                self._spawn_enemy_pop(en.x, en.y)
                self.enemies.remove(en)

        # enemy shooting
        for en in self.enemies:
            can_shoot = (getattr(en, "kind", "") in ("shooter", "elite_shooter")) or (getattr(en, "kind", "") == "boss" and getattr(en, "boss_stage", 0) >= 3)
            if can_shoot:
                if not hasattr(en, "shoot_cd"):
                    en.shoot_cd = random.uniform(1.0, 2.4)
                en.shoot_cd -= dt
                if en.shoot_cd <= 0:
                    en.shoot_cd = random.uniform(1.0, 2.0) if en.kind != "boss" else random.uniform(0.6, 1.2)
                    dx = self.player.x - en.x
                    dy = self.player.y - en.y
                    l = math.hypot(dx, dy) or 1
                    speed = 5.0 if en.kind != "boss" else 7.0
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
                if getattr(en, "hit_iframes", 0.0) > 0:
                    continue
                if circle_collision(b.x, b.y, b.radius, en.x, en.y, en.radius):
                    en.hit_iframes = 0.15
                    b.guidance_disabled = True
                    b.target = None
                    extra_damage = 0
                    status_color = COLOR_YELLOW
                    en.hp -= b.damage
                    en.flash_timer = 0.15
                    dx = en.x - b.x
                    dy = en.y - b.y
                    l = math.hypot(dx, dy) or 1
                    push = 12
                    en.x += dx / l * push
                    en.y += dy / l * push
                    # status bonus damage
                    if b.status.get("ice") and en.ice_timer > 0:
                        extra_damage += self.player.ice_bonus_damage
                        status_color = (150, 200, 255)
                    if b.status.get("burn"):
                        status_color = (255, 120, 90)
                        if en.burn_timer > 0 and self.player.burn_sear_bonus > 0:
                            extra_damage += int(b.damage * self.player.burn_sear_bonus)
                    if b.status.get("poison"):
                        status_color = (180, 130, 255)
                        if en.poison_timer > 0:
                            extra_damage += int(b.damage * 0.2 * self.player.poison_bonus_mult)
                    if extra_damage > 0:
                        en.hp -= extra_damage
                    self.damage_texts.append({"x": en.x + random.uniform(-6, 6), "y": en.y - 10, "val": b.damage + extra_damage, "life": 0.6, "color": status_color})
                    # apply status effects
                    if b.status.get("ice"):
                        en.ice_timer = max(en.ice_timer, 2.0)
                        en.ice_dps = max(en.ice_dps, self.player.ice_bonus_damage * 0.8)
                        self._spawn_status_fx(en.x, en.y, kind="ice")
                    if b.status.get("burn"):
                        en.burn_timer = max(en.burn_timer, 3.0)
                        en.burn_dps = max(en.burn_dps, self.player.damage * 0.26 * self.player.burn_bonus_mult)
                        self._spawn_status_fx(en.x, en.y, kind="fire")
                    if b.status.get("poison"):
                        en.poison_timer = max(en.poison_timer, 5.0)
                        en.poison_dps = max(en.poison_dps, self.player.damage * 0.22 * self.player.poison_bonus_mult)
                        self._spawn_status_fx(en.x, en.y, kind="poison")
                    killed = en.hp <= 0

                    if b.piercing:
                        if b.pierce_on_kill:
                            if killed:
                                b.pierce_left -= 1
                                if b.pierce_left < 0 and b in self.bullets:
                                    self.bullets.remove(b)
                            else:
                                if b in self.bullets:
                                    self.bullets.remove(b)
                        else:
                            if b.pierce_left > 0:
                                b.pierce_left -= 1
                            else:
                                if b in self.bullets:
                                    self.bullets.remove(b)
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
                        if self.player.burn_chain:
                            for other in self.enemies:
                                if other is en:
                                    continue
                                dx = other.x - en.x
                                dy = other.y - en.y
                                if dx * dx + dy * dy <= 140 * 140:
                                    other.burn_timer = max(other.burn_timer, 3.0)
                                    other.burn_dps = max(other.burn_dps, self.player.damage * 0.2 * self.player.burn_bonus_mult)
                        if getattr(en, "kind", "") == "boss":
                            self._spawn_evolution_pickup(en.x, en.y)
                            audio.play_sfx(audio.snd_boss_explosion)
                        self._spawn_enemy_pop(en.x, en.y)
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
                audio.play_sfx(audio.snd_pickup_boost)
                self.gas_pickups.remove(g)

        # evolution pickup collision
        for ev in list(self.evolution_pickups):
            if circle_collision(self.player.x, self.player.y, self.player.radius, ev.x, ev.y, ev.radius):
                self.evolution_pickups.remove(ev)
                audio.play_sfx(audio.snd_pickup_boss)
                self.roll_evolution()

    def _spawn_death_fx(self, x, y):
        self.death_fx.clear()
        for _ in range(140):
            ang = random.uniform(0, math.tau)
            spd = random.uniform(35, 110)
            life_max = random.uniform(1.6, 2.4)
            self.death_fx.append({
                "x": x,
                "y": y,
                "vx": math.cos(ang) * spd,
                "vy": math.sin(ang) * spd,
                "life": life_max,
                "life_max": life_max,
                "r_base": random.uniform(10, 22),
            })

    def _spawn_evolution_pickup(self, x, y):
        self.evolution_pickups.append(EvolutionPickup(x, y))

    def _spawn_status_fx(self, x, y, kind="fire", radius=10):
        # small burst on hit; ambient handled separately per-frame
        if kind == "fire":
            color = (255, 110, 80)
            vy_range = (-10, -4)
            size_range = (2.0, 3.2)
            life_range = (0.24, 0.36)
        elif kind == "ice":
            color = (170, 210, 255)
            vy_range = (-3, 3)
            size_range = (1.8, 3.0)
            life_range = (0.22, 0.32)
        else:  # poison
            color = (140, 255, 160)
            vy_range = (3, 7)
            size_range = (2.0, 3.4)
            life_range = (0.26, 0.38)

        count = 8
        for _ in range(count):
            ang = random.uniform(0, math.tau)
            r = random.uniform(0, radius * 0.6)
            base_x = x + math.cos(ang) * r
            base_y = y + math.sin(ang) * r
            vx = random.uniform(-6, 6)
            vy = random.uniform(*vy_range)
            self.status_particles.append({
                "x": base_x,
                "y": base_y,
                "vx": vx,
                "vy": vy,
                "life": 0.0,
                "life_max": random.uniform(*life_range),
                "color": color,
                "kind": kind,
                "size": random.uniform(*size_range),
            })

    def _emit_status_particle(self, en, kind: str):
        rad = getattr(en, "radius", 10)
        ang = random.uniform(0, math.tau)
        r = random.uniform(0, rad * 0.7)
        px = en.x + math.cos(ang) * r
        py = en.y + math.sin(ang) * r

        if kind == "fire":
            color = (255, 110, 80)
            vx = random.uniform(-4, 4)
            vy = random.uniform(-7, -3)
            size = random.uniform(1.6, 2.4)
            life_max = random.uniform(0.18, 0.26)
        elif kind == "ice":
            color = (170, 210, 255)
            vx = random.uniform(-3, 3)
            vy = random.uniform(-3, 3)
            size = random.uniform(1.5, 2.4)
            life_max = random.uniform(0.18, 0.26)
        else:  # poison
            color = (140, 255, 160)
            vx = random.uniform(-3, 3)
            vy = random.uniform(3, 7)
            size = random.uniform(1.6, 2.4)
            life_max = random.uniform(0.18, 0.26)

        self.status_particles.append({
            "x": px,
            "y": py,
            "vx": vx,
            "vy": vy,
            "life": 0.0,
            "life_max": life_max,
            "color": color,
            "kind": kind,
            "size": size,
        })

    def _spawn_enemy_pop(self, x, y):
        # gentle, tiny pop on enemy death
        count = 24
        for _ in range(count):
            ang = random.uniform(0, math.tau)
            spd = random.uniform(3, 5)
            dist = random.uniform(10, 15)
            size = random.uniform(2.5, 5.0)
            life_max = random.uniform(0.35, 0.65)
            self.status_particles.append({
                "x": x + math.cos(ang) * dist,
                "y": y + math.sin(ang) * dist,
                "vx": math.cos(ang) * spd,
                "vy": math.sin(ang) * spd,
                "life": 0.0,
                "life_max": life_max,
                "color": (255, 0, 0),
                "kind": "pop",
                "size": size,
            })

    def _apply_laser_damage(self, dt, cam):
        if not self.player.laser_active:
            self.laser_segment = None
            return

        mx, my = pygame.mouse.get_pos()
        target = (cam[0] + mx, cam[1] + my)
        px, py = self.player.x, self.player.y
        dx = target[0] - px
        dy = target[1] - py
        dist = math.hypot(dx, dy) or 1.0
        dir_x = dx / dist
        dir_y = dy / dist
        length = 900
        end_x = px + dir_x * length
        end_y = py + dir_y * length
        self.laser_segment = (px, py, end_x, end_y)

        width = 42 * 3
        dps = self.player.damage * 4.0

        def point_segment_dist_sq(x0, y0, x1, y1, x2, y2):
            # distance from point (x0,y0) to segment (x1,y1)-(x2,y2)
            pxv = x2 - x1
            pyv = y2 - y1
            l2 = pxv * pxv + pyv * pyv or 1.0
            t = ((x0 - x1) * pxv + (y0 - y1) * pyv) / l2
            t = max(0.0, min(1.0, t))
            proj_x = x1 + t * pxv
            proj_y = y1 + t * pyv
            dxp = x0 - proj_x
            dyp = y0 - proj_y
            return dxp * dxp + dyp * dyp

        for en in self.enemies:
            if point_segment_dist_sq(en.x, en.y, px, py, end_x, end_y) <= width * width:
                en.hp -= dps * dt
                en.flash_timer = 0.05
                en.burn_timer = max(en.burn_timer, 2.0)
                en.burn_dps = max(en.burn_dps, self.player.damage * 0.18 * self.player.burn_bonus_mult)

    def _update_minions(self, dt):
        # maintain desired minion count
        while len(self.minions) < self.player.minion_count:
            self.minions.append({"angle": random.uniform(0, math.tau), "cd": random.uniform(0.2, 0.8)})
        if len(self.minions) > self.player.minion_count:
            self.minions = self.minions[: self.player.minion_count]

        # pick closest enemy for targeting
        target = None
        if self.enemies:
            target = min(self.enemies, key=lambda en: (en.x - self.player.x) ** 2 + (en.y - self.player.y) ** 2)

        orbit_r = 70
        for m in self.minions:
            m["angle"] += dt * 1.6
            m["cd"] -= dt
            m["x"] = self.player.x + math.cos(m["angle"]) * orbit_r
            m["y"] = self.player.y + math.sin(m["angle"]) * orbit_r
            if target and m["cd"] <= 0:
                dx = target.x - m["x"]
                dy = target.y - m["y"]
                b = Bullet(m["x"], m["y"], dx, dy, int(self.player.damage * 0.6 * self.player.minion_damage_mult), self.player.bullet_speed * 0.9, status=self.player.bullet_status.copy())
                b.piercing = False
                self.bullets.append(b)
                m["cd"] = 0.9

    def _update_aura_orbs(self, dt):
        if not self.player.aura_unlocked or self.player.aura_orb_count <= 0:
            return
        if len(self.player.aura_orbs) != self.player.aura_orb_count:
            self.player.rebuild_aura_orbs()

        orbit_r = self.player.aura_orb_radius
        speed = self.player.aura_orb_speed
        hit_r = max(12, self.player.aura_orb_size + 6)

        # advance orbit positions and cooldowns
        for orb in self.player.aura_orbs:
            orb["angle"] = (orb.get("angle", 0.0) + dt * speed) % math.tau
            ox = self.player.x + math.cos(orb["angle"]) * orbit_r
            oy = self.player.y + math.sin(orb["angle"]) * orbit_r
            orb["x"], orb["y"] = ox, oy
            if orb.get("cd", 0) > 0:
                orb["cd"] = max(0.0, orb["cd"] - dt)

        # collisions
        for orb in self.player.aura_orbs:
            if orb.get("cd", 0) > 0:
                continue
            ox, oy = orb.get("x", self.player.x), orb.get("y", self.player.y)
            radius = hit_r
            for en in list(self.enemies):
                if getattr(en, "aura_iframes", 0) > 0:
                    continue
                dx = en.x - ox
                dy = en.y - oy
                if dx * dx + dy * dy <= (en.radius + radius) ** 2:
                    en.hp -= self.player.aura_orb_damage
                    en.flash_timer = 0.1
                    en.aura_iframes = 0.25
                    # knockback away from the player position
                    kx = en.x - self.player.x
                    ky = en.y - self.player.y
                    kl = math.hypot(kx, ky) or 1.0
                    push = self.player.aura_orb_knockback
                    en.x += kx / kl * push
                    en.y += ky / kl * push

                    elem = orb.get("element", "shock")
                    if elem == "fire":
                        en.burn_timer = max(en.burn_timer, 3.0)
                        en.burn_dps = max(en.burn_dps, self.player.damage * 0.26 * self.player.burn_bonus_mult)
                        self._spawn_status_fx(en.x, en.y, kind="fire")
                    elif elem == "ice":
                        en.ice_timer = max(en.ice_timer, 2.0)
                        en.ice_dps = max(en.ice_dps, self.player.ice_bonus_damage * 0.8)
                        self._spawn_status_fx(en.x, en.y, kind="ice")
                    elif elem == "poison":
                        en.poison_timer = max(en.poison_timer, 5.0)
                        en.poison_dps = max(en.poison_dps, self.player.damage * 0.22 * self.player.poison_bonus_mult)
                        self._spawn_status_fx(en.x, en.y, kind="poison")

                    dmg_col = {
                        "fire": (255, 140, 110),
                        "ice": (170, 210, 255),
                        "poison": (160, 255, 170),
                    }.get(elem, COLOR_YELLOW)
                    self.damage_texts.append({"x": en.x, "y": en.y - 10, "val": int(self.player.aura_orb_damage), "life": 0.5, "color": dmg_col})
                    orb["cd"] = 0.2
                    break

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
            boss_stage = self.bosses_spawned
        else:
            pool = ["normal", "fast", "tank"]
            weights = [0.45, 0.25, 0.2]
            if t >= 180:
                pool.append("shooter")
                weights.append(0.15)
            if t > 90:
                pool.append("sprinter")
                weights.append(0.15)
            if t > 120:
                pool.append("bruiser")
                weights.append(0.2)
            kind = random.choices(pool, weights=weights, k=1)[0]
            boss_stage = 0

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
            if boss_stage == 1:
                hp = int(ENEMY_BASE_HP * 14 * hp_scale)
                speed = ENEMY_BASE_SPEED * 1.2 * speed_scale
            elif boss_stage == 2:
                hp = int(ENEMY_BASE_HP * 18 * hp_scale)
                speed = ENEMY_BASE_SPEED * 1.45 * speed_scale
            else:
                hp = int(ENEMY_BASE_HP * 24 * hp_scale)
                speed = ENEMY_BASE_SPEED * 1.6 * speed_scale
        else:
            hp = int(ENEMY_BASE_HP * 1.0 * hp_scale)
            speed = ENEMY_BASE_SPEED * 1.0 * speed_scale

        self.enemies.append(Enemy(x, y, hp, speed, kind, boss_stage=boss_stage))

    def roll_levelup(self):
        if self.dev_mode and self.dev_power_queue:
            self.levelup_options = self.dev_power_queue[:3]
            self.dev_power_queue = self.dev_power_queue[3:]
        else:
            pool = available_powerups(self.player)
            if len(pool) >= 3:
                self.levelup_options = random.sample(pool, k=3)
            elif pool:
                # allow duplicates if few options remain
                self.levelup_options = random.choices(pool, k=min(3, len(pool)))
            else:
                self.levelup_options = []
        self.state = STATE_LEVEL_UP
        audio.play_sfx(audio.snd_level_up)

    def roll_evolution(self):
        self.evolution_options = random.sample(EVOLUTIONS, k=min(3, len(EVOLUTIONS)))
        self.state = STATE_EVOLUTION
        audio.play_sfx(audio.snd_level_up)

    def _grant_dev_power(self, pid: str):
        if not self.dev_mode:
            return
        if hasattr(self, "player") and self.player:
            apply_powerup(self.player, pid)

    def get_camera(self):
        return (self.player.x - WIDTH // 2, self.player.y - HEIGHT // 2)

    def draw_background(self, cam, target=None):
        # Properly draw space starfield behind everything
        surface = target if target is not None else self.screen
        w, h = surface.get_size()
        ox, oy = cam
        for s in self.stars:
            x = int(s["x"] - ox)
            y = int(s["y"] - oy)
            if -5 <= x <= w + 5 and -5 <= y <= h + 5:
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
                    pygame.draw.polygon(surface, col, pts)
                elif s["shape"] == "wide":
                    pygame.draw.rect(surface, col, (x, y, s["r"] + 3, s["r"]))
                else:
                    pygame.draw.rect(surface, col, (x, y, s["r"], s["r"]))
        # shimmering pops
        for f in list(self.star_flashes):
            fx = int(f["x"] - ox)
            fy = int(f["y"] - oy)
            if -5 <= fx <= w + 5 and -5 <= fy <= h + 5:
                alpha = int(255 * (f["life"] / f["life_max"]))
                flash_surf = pygame.Surface((f["r"] * 2, f["r"] * 2), pygame.SRCALPHA)
                pygame.draw.circle(flash_surf, (255, 255, 255, alpha), (f["r"], f["r"]), f["r"])
                surface.blit(flash_surf, (fx - f["r"], fy - f["r"]))

    def draw(self):
        self.screen.fill(COLOR_BG)
        if self.state == STATE_MENU:
            self.draw_menu()
        elif self.state in (STATE_PLAYING, STATE_LEVEL_UP, STATE_EVOLUTION, STATE_GAME_OVER, STATE_PAUSED, STATE_DEAD_ANIM):
            self.draw_game_world()
            self.draw_boost_overlay()
            self.draw_vision_overlay()
            self.draw_hud()
            if self.state == STATE_LEVEL_UP:
                self.draw_levelup()
            if self.state == STATE_EVOLUTION:
                self.draw_evolution()
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
        # render world to a zoomable surface so boosting shrinks the view
        zoom = clamp(self.view_zoom, 0.7, 1.1)
        render_w = int(self.w / zoom)
        render_h = int(self.h / zoom)
        render_surf = pygame.Surface((render_w, render_h))
        render_surf.fill(COLOR_BG)

        cam = (self.player.x - render_w // 2, self.player.y - render_h // 2)
        self.draw_background(cam, target=render_surf)

        # particles first so entities draw above
        for p in self.boost_particles:
            sx = int(p["x"] - cam[0])
            sy = int(p["y"] - cam[1])
            life_max = p.get("life_max", 0.35)
            alpha = int(255 * max(0, min(1, p["life"] / life_max)))
            size = p.get("size", 6)
            rot = p.get("rot", 0.0)
            surf = pygame.Surface((int(size * 2.6), int(size * 2.6)), pygame.SRCALPHA)
            cx = size * 1.3
            cy = size * 1.3
            star_pts = []
            for i in range(8):
                ang = rot + math.tau * i / 8
                r = size if i % 2 == 0 else size * 0.55
                star_pts.append((cx + math.cos(ang) * r, cy + math.sin(ang) * r))
            pygame.draw.polygon(surf, (*p["color"], alpha), star_pts)
            render_surf.blit(surf, (int(sx - size * 1.3), int(sy - size * 1.3)))
        for p in self.status_particles:
            sx = int(p["x"] - cam[0])
            sy = int(p["y"] - cam[1])
            life_max = p.get("life_max", 0.6)
            t = max(0.0, min(1.0, p["life"] / life_max))
            fade = 1.0 - abs(t * 2 - 1)
            alpha = int(220 * fade)
            size = p.get("size", 5)
            kind = p.get("kind", "spark")
            color = p.get("color", (255, 255, 255))
            surf = pygame.Surface((int(size * 3), int(size * 3)), pygame.SRCALPHA)
            cx = int(size * 1.5)
            cy = int(size * 1.5)
            if kind == "pop":
                alpha = int(230 * (1 - t) ** 0.8)
                pygame.draw.circle(surf, (*color, alpha), (cx, cy), int(size))
            elif kind == "fire":
                pygame.draw.rect(surf, (*color, alpha), (cx - size * 0.4, cy - size, size * 0.8, size * 1.6))
            elif kind == "ice":
                pts = []
                for i in range(6):
                    ang = math.tau * i / 6
                    r = size if i % 2 == 0 else size * 0.45
                    pts.append((int(cx + math.cos(ang) * r), int(cy + math.sin(ang) * r)))
                pygame.draw.polygon(surf, (*color, alpha), pts)
            elif kind == "poison":
                pygame.draw.circle(surf, (*color, alpha), (cx, cy), int(size))
                pygame.draw.circle(surf, (*color, max(0, alpha - 60)), (cx, cy), max(1, int(size * 0.5)))
            else:
                pygame.draw.circle(surf, (*color, alpha), (cx, cy), int(size))
            render_surf.blit(surf, (int(sx - size * 1.5), int(sy - size * 1.5)))

        # aura orbs
        if self.player.aura_unlocked:
            for orb in self.player.aura_orbs:
                ox = int(orb.get("x", self.player.x) - cam[0])
                oy = int(orb.get("y", self.player.y) - cam[1])
                elem = orb.get("element", "shock")
                if elem == "fire":
                    inner = (255, 150, 90)
                    outer = (255, 220, 160)
                elif elem == "ice":
                    inner = (150, 210, 255)
                    outer = (210, 240, 255)
                elif elem == "poison":
                    inner = (160, 255, 190)
                    outer = (210, 255, 220)
                else:
                    inner = (200, 220, 255)
                    outer = (255, 255, 255)
                r = self.player.aura_orb_size
                pygame.draw.circle(render_surf, outer, (ox, oy), max(1, r + 3), width=2)
                pygame.draw.circle(render_surf, inner, (ox, oy), r)

        for o in self.orbs:
            o.draw(render_surf, cam)
        for g in self.gas_pickups:
            g.draw(render_surf, cam)
        for ev in self.evolution_pickups:
            ev.draw(render_surf, cam)
        for m in self.minions:
            sx = int(m.get("x", self.player.x) - cam[0])
            sy = int(m.get("y", self.player.y) - cam[1])
            pygame.draw.circle(render_surf, (180, 255, 255), (sx, sy), 10)
            pygame.draw.circle(render_surf, (60, 180, 220), (sx, sy), 6)
        for e in self.enemies:
            e.draw(render_surf, cam)
        for b in self.bullets:
            b.draw(render_surf, cam)
        for eb in self.enemy_bullets:
            sx = int(eb["x"] - cam[0])
            sy = int(eb["y"] - cam[1])
            pygame.draw.circle(render_surf, COLOR_RED, (sx, sy), eb["r"])
        # laser beam visual
        if self.player.laser_active and self.laser_segment:
            px, py, ex, ey = self.laser_segment
            start = (int(px - cam[0]), int(py - cam[1]))
            end = (int(ex - cam[0]), int(ey - cam[1]))
            pygame.draw.line(render_surf, (255, 140, 70), start, end, 30)
            pygame.draw.line(render_surf, (255, 230, 180), start, end, 12)
            # start flash (kamehameha-style burst)
            burst_r = 46
            flash = pygame.Surface((burst_r * 2, burst_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(flash, (255, 200, 140, 190), (burst_r, burst_r), burst_r)
            pygame.draw.circle(flash, (255, 255, 240, 230), (burst_r, burst_r), max(8, burst_r // 2))
            render_surf.blit(flash, (start[0] - burst_r, start[1] - burst_r))
        self.player.draw(render_surf, center=(render_w // 2, render_h // 2))
        self._draw_death_fx(cam, target=render_surf)
        self._draw_damage_texts(cam, target=render_surf)

        # scale the rendered world back to the screen at the desired zoom
        scaled = pygame.transform.smoothscale(render_surf, (self.w, self.h))
        self.screen.blit(scaled, (0, 0))

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

    def draw_vision_overlay(self):
        alpha = int(180 * max(0.0, min(1.0, self.vision_dim)))
        if alpha <= 0:
            return
        overlay = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (0, 0, 0, alpha), (0, 0, self.w, self.h))
        self.screen.blit(overlay, (0, 0))

    def _draw_death_fx(self, cam, target=None):
        surface = target if target is not None else self.screen
        for fx in self.death_fx:
            sx = int(fx["x"] - cam[0])
            sy = int(fx["y"] - cam[1])
            life_ratio = fx.get("life", 0) / max(0.001, fx.get("life_max", 1.0))
            r = max(4, int(fx.get("r_base", 12) * life_ratio))
            pygame.draw.circle(surface, COLOR_RED, (sx, sy), r)

    def _draw_damage_texts(self, cam, target=None):
        surface = target if target is not None else self.screen
        for txt in self.damage_texts:
            sx = int(txt["x"] - cam[0])
            sy = int(txt["y"] - cam[1])
            alpha = int(255 * (txt["life"] / 0.6))
            color = txt.get("color", COLOR_YELLOW)
            surf = self.font_small.render(str(txt["val"]), True, color)
            surf.set_alpha(alpha)
            surface.blit(surf, (sx, sy))

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

        laser_y = ammo_y + 22
        if self.player.laser_active:
            laser_txt = self.font_small.render("LASER ACTIVE", True, COLOR_GREEN)
        elif self.player.laser_cooldown > 0:
            laser_txt = self.font_small.render(f"LASER {int(self.player.laser_cooldown)}s", True, COLOR_WHITE)
        else:
            laser_txt = self.font_small.render("LASER READY", True, COLOR_GREEN)
        self.screen.blit(laser_txt, (lvl_x, laser_y))

        # boost meter bottom-right vertical bar
        bar_h = 140
        bar_w = 16
        bar_x = self.w - 40
        bar_y = self.h - 40 - bar_h
        pygame.draw.rect(self.screen, COLOR_DARK_GRAY, (bar_x, bar_y, bar_w, bar_h))
        ratio = self.player.boost_meter / max(1, self.player.boost_meter_max)
        fill_h = int(bar_h * ratio)
        pygame.draw.rect(self.screen, (120, 240, 255), (bar_x, bar_y + (bar_h - fill_h), bar_w, fill_h))
        boost_color = (255, 160, 90) if self.player.boosting else COLOR_WHITE
        letters = "BOOST"
        lx = bar_x + bar_w + 6
        ly = bar_y
        for ch in letters:
            surf = self.font_tiny.render(ch, True, boost_color)
            self.screen.blit(surf, (lx, ly))
            ly += surf.get_height() + 2

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

    def draw_evolution(self):
        overlay = pygame.Surface((self.w, self.h))
        overlay.set_alpha(220)
        overlay.fill((12, 6, 24))
        self.screen.blit(overlay, (0, 0))
        title = self.font_large.render("EVOLUTION", True, COLOR_YELLOW)
        self.screen.blit(title, (self.w // 2 - title.get_width() // 2, self.h // 4))
        w = 320
        h = 150
        gap = 24
        total_w = 3 * w + 2 * gap
        start_x = WIDTH // 2 - total_w // 2
        y = HEIGHT // 2 - h // 2
        mouse_pos = pygame.mouse.get_pos()
        for i, eid in enumerate(self.evolution_options):
            rect = pygame.Rect(start_x + i * (w + gap), y, w, h)
            is_hover = rect.collidepoint(mouse_pos)
            col = COLOR_DARK_GRAY if not is_hover else COLOR_GRAY
            pygame.draw.rect(self.screen, col, rect, border_radius=8)
            name = evolution_name(eid)
            desc = evolution_desc(eid)
            t1 = self.font_small.render(name, True, COLOR_WHITE)
            t2 = self.font_tiny.render(desc, True, COLOR_WHITE)
            self.screen.blit(t1, (rect.centerx - t1.get_width() // 2, rect.y + rect.height // 2 - t1.get_height()))
            self.screen.blit(t2, (rect.centerx - t2.get_width() // 2, rect.y + rect.height // 2 + 4))

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
        # add breathing room before buttons
        btn_offset_y = HEIGHT // 3 + 60 + len(lines) * 40 + 40
        self.btn_restart.rect.centerx = self.w // 2
        self.btn_main_menu.rect.centerx = self.w // 2
        self.btn_restart.rect.y = btn_offset_y
        self.btn_main_menu.rect.y = btn_offset_y + 60
        self.btn_restart.draw(self.screen)
        self.btn_main_menu.draw(self.screen)

    def draw_pause_overlay(self):
        overlay = pygame.Surface((self.w, self.h))
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        t = self.font_large.render("PAUSED", True, COLOR_WHITE)
        title_y = self._layout_pause_sliders()
        self.screen.blit(t, (self.w // 2 - t.get_width() // 2, title_y))
        # volume sliders in pause (immediately under label)
        label_music = self.font_small.render("MUSIC", True, COLOR_WHITE)
        # add breathing room above the slider so text isn't glued to the bar
        self.screen.blit(label_music, (self.pause_music_rect.x, self.pause_music_rect.y - 28))
        pygame.draw.rect(self.screen, COLOR_DARK_GRAY, self.pause_music_rect)
        filled_m = int(self.pause_music_rect.width * self.music_volume)
        pygame.draw.rect(self.screen, COLOR_GREEN, (self.pause_music_rect.x, self.pause_music_rect.y, filled_m, self.pause_music_rect.height))

        label_sfx = self.font_small.render("SFX", True, COLOR_WHITE)
        self.screen.blit(label_sfx, (self.pause_sfx_rect.x, self.pause_sfx_rect.y - 28))
        pygame.draw.rect(self.screen, COLOR_DARK_GRAY, self.pause_sfx_rect)
        filled_s = int(self.pause_sfx_rect.width * self.sfx_volume)
        pygame.draw.rect(self.screen, COLOR_GREEN, (self.pause_sfx_rect.x, self.pause_sfx_rect.y, filled_s, self.pause_sfx_rect.height))
        # buttons under sliders
        self.btn_pause_resume.draw(self.screen)
        self.btn_pause_reset.draw(self.screen)
        self.btn_pause_quit.draw(self.screen)

    def _dropdown_rect(self):
        option_h = 34
        total_h = option_h * len(WINDOW_SIZES)
        return pygame.Rect(self.btn_window_dropdown.rect.x, self.btn_window_dropdown.rect.bottom + 6, self.btn_window_dropdown.rect.width, total_h)

    def _dev_toggle_rect(self):
        back = self.btn_settings_back.rect
        w, h = 180, 32
        x = back.centerx - w // 2
        y = back.y - h - 12
        return pygame.Rect(x, y, w, h)

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
            (self.slider_bg_rect.x, self.slider_bg_rect.y - 30),
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
            (self.slider_sfx_rect.x, self.slider_sfx_rect.y - 30),
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

        # dev toggle aligned with back button
        dev_rect = self._dev_toggle_rect()
        toggle_col = COLOR_GREEN if self.dev_mode else COLOR_DARK_GRAY
        pygame.draw.rect(self.screen, toggle_col, dev_rect, border_radius=6)
        toggle_txt = self.font_small.render("DEBUG", True, COLOR_WHITE)
        self.screen.blit(toggle_txt, (dev_rect.x + 12, dev_rect.y + 6))
        status_txt = self.font_tiny.render("ON" if self.dev_mode else "OFF", True, COLOR_WHITE)
        self.screen.blit(status_txt, (dev_rect.right - status_txt.get_width() - 10, dev_rect.y + 8))

        self.btn_settings_back.draw(self.screen)
