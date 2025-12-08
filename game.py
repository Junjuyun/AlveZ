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
from upgrade_system import UpgradeManager
from upgrade_trees import UPGRADES_BY_ID, ALL_TREES, get_tier3_upgrades, get_all_effects_for_tier3


# --- main game ---
class Game:
    def __init__(self):
        pygame.init()
        self.w, self.h = WIDTH, HEIGHT
        self.screen = pygame.display.set_mode((self.w, self.h))
        pygame.display.set_caption("Space Invaders")
        self.clock = pygame.time.Clock()

        # pixel font (bundled)
        font_path = os.path.join(os.path.dirname(__file__), "Assets", "UI", "Press_Start_2P", "PressStart2P-Regular.ttf")
        if os.path.isfile(font_path):
            self.font_large = pygame.font.Font(font_path, 64)
            self.font_medium = pygame.font.Font(font_path, 30)
            self.font_small = pygame.font.Font(font_path, 20)
            self.font_tiny = pygame.font.Font(font_path, 16)
            self.font_micro = pygame.font.Font(font_path, 12)  # Smaller font for descriptions
        else:
            self.font_large = pygame.font.SysFont("PressStart2P", 64)
            self.font_medium = pygame.font.SysFont("PressStart2P", 30)
            self.font_small = pygame.font.SysFont("PressStart2P", 20)
            self.font_tiny = pygame.font.SysFont("PressStart2P", 16)
            self.font_micro = pygame.font.SysFont("PressStart2P", 12)

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

        self.levelup_options = []  # List of upgrade IDs for level-up screen
        self.upgrade_manager = None  # Initialized in reset_game

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

        # test mode controls (renamed from dev mode)
        self.test_mode = False
        self.test_power_queue = []

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
        self.upgrade_manager = UpgradeManager(self.player)
        self.player.upgrade_manager = self.upgrade_manager  # Reference for combat checks
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
        self.view_zoom = 0.9  # Slightly zoomed out base view
        
        # New summon systems from upgrade trees
        self.ghosts = []  # Free-moving, touch damage
        self.drones = []  # Orbiting, shooting
        self.dragon = None
        self.magic_lenses = []
        self.magic_shields = []  # Orbiting shields
        self.magic_scythes = []
        self.magic_spears = []
        self.phantoms = []
        self.gale_active = False
        self.gale_timer = 0.0
        self.lightning_fx = []
        self.fireball_fx = []
        self.glare_flash_timer = 0.0

        if self.test_mode:
            self.player.level = 1
            self.player.xp = 0
            self.player.xp_to_level = XP_PER_LEVEL
            # In test mode, provide only Tier 3 upgrades
            tier3_list = get_tier3_upgrades()
            self.test_power_queue = [u.id for u in tier3_list]
        else:
            self.test_power_queue.clear()

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
                if self.test_mode:
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
                if self.test_mode:
                    self.roll_levelup()
                else:
                    self.state = STATE_PLAYING
            elif self.btn_main_menu.is_clicked(e):
                audio.play_sfx(audio.snd_menu_click)
                self.state = STATE_MENU
        elif self.state == STATE_LEVEL_UP:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                mx, my = e.pos
                w = 320
                h = 180
                gap = 24
                total_w = 3 * w + 2 * gap
                start_x = WIDTH // 2 - total_w // 2
                y = HEIGHT // 2 - h // 2
                
                # Check skip button first (test mode only)
                if self.test_mode:
                    skip_rect = pygame.Rect(WIDTH // 2 - 80, y + h + 30, 160, 40)
                    if skip_rect.collidepoint(mx, my):
                        audio.play_sfx(audio.snd_menu_click)
                        self.state = STATE_PLAYING
                        return
                
                for i, uid in enumerate(self.levelup_options):
                    rect = pygame.Rect(start_x + i * (w + gap), y, w, h)
                    if rect.collidepoint(mx, my):
                        self.apply_levelup_choice(uid)
                        if self.test_mode and self.test_power_queue:
                            self.roll_levelup()
                        else:
                            self.state = STATE_PLAYING
                        break
        elif self.state == STATE_EVOLUTION:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                mx, my = e.pos
                w = 320
                h = 180
                gap = 24
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

                # test mode toggle
                test_rect = self._test_toggle_rect()
                if test_rect.collidepoint(mx, my):
                    audio.play_sfx(audio.snd_menu_click)
                    self.test_mode = not self.test_mode
                    if self.test_mode:
                        # In test mode, provide ALL upgrades from new tree system
                        self.test_power_queue = list(UPGRADES_BY_ID.keys())
                    else:
                        self.test_power_queue.clear()
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
                if self.test_mode:
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
        
        # Update upgrade manager for timed effects
        is_moving = keys[pygame.K_w] or keys[pygame.K_s] or keys[pygame.K_a] or keys[pygame.K_d]
        self.upgrade_manager.update(dt, is_moving=is_moving, is_stationary=not is_moving)

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
        target_zoom = 0.75 if self.player.boosting else 0.9
        self.view_zoom += (target_zoom - self.view_zoom) * min(1.0, dt * 6.0)
        self.view_zoom = clamp(self.view_zoom, 0.65, 1.05)

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
        self._update_summons(dt)

        # shooting
        if pygame.mouse.get_pressed()[0] and self.player.can_shoot():
            mx, my = pygame.mouse.get_pos()
            # Adjust mouse position for zoom - screen center is player position
            center_x, center_y = self.w / 2, self.h / 2
            # Mouse offset from center, scaled by zoom
            offset_x = (mx - center_x) / self.view_zoom
            offset_y = (my - center_y) / self.view_zoom
            world_target = (self.player.x + offset_x, self.player.y + offset_y)
            
            # Check siege ammo save
            is_stationary = not (keys[pygame.K_w] or keys[pygame.K_s] or keys[pygame.K_a] or keys[pygame.K_d])
            if not self.upgrade_manager.check_siege_ammo_save(is_stationary):
                new_bullets = self.player.shoot(world_target)
            else:
                # Siege saved the ammo - still fire but don't consume
                new_bullets = self.player.shoot(world_target)
                self.player.ammo = min(self.player.mag_size, self.player.ammo + 1)
            
            self.bullets.extend(new_bullets)
            audio.play_sfx(audio.snd_shoot)
            
            # Trigger on_shot effects (lightning, fireball)
            shot_effects = self.upgrade_manager.on_shot()
            self._handle_shot_effects(shot_effects, world_target)
            
            # Check for empty mag effects
            if self.player.ammo <= 0:
                empty_effects = self.upgrade_manager.on_empty_mag()
                self._handle_empty_mag_effects(empty_effects)

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
            # Initialize bounce properties if needed
            bounce_count = getattr(self.player, "bounce_count", 0)
            if bounce_count > 0 and getattr(b, "bounces_left", None) is None:
                b.bounces_left = bounce_count
                b.bounced_enemies = set()  # Track which enemies we bounced off
        self.bullets = [b for b in self.bullets if not b.offscreen(cam) or getattr(b, "bounces_left", 0) > 0]

        if self.boost_effect_timer > 0:
            self.boost_effect_timer = max(0.0, self.boost_effect_timer - dt)
        
        if self.glare_flash_timer > 0:
            self.glare_flash_timer = max(0.0, self.glare_flash_timer - dt)

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

        # enemy-enemy separation to prevent stacking
        if len(self.enemies) > 1:
            for _ in range(2):  # a couple of relaxation passes
                for i in range(len(self.enemies)):
                    ei = self.enemies[i]
                    for j in range(i + 1, len(self.enemies)):
                        ej = self.enemies[j]
                        dx = ej.x - ei.x
                        dy = ej.y - ei.y
                        dist = math.hypot(dx, dy)
                        min_dist = ei.radius + ej.radius
                        if dist < 1e-4:
                            dx = random.uniform(-0.01, 0.01)
                            dy = random.uniform(-0.01, 0.01)
                            dist = math.hypot(dx, dy) or 1.0
                        if dist < min_dist:
                            overlap = (min_dist - dist)
                            nx, ny = dx / dist, dy / dist
                            # bosses resist being pushed; regulars share the shove
                            wi = 0.5
                            wj = 0.5
                            if getattr(ei, "kind", "") == "boss" and getattr(ej, "kind", "") != "boss":
                                wi, wj = 0.2, 0.8
                            elif getattr(ej, "kind", "") == "boss" and getattr(ei, "kind", "") != "boss":
                                wi, wj = 0.8, 0.2
                            push = overlap * 0.5
                            ei.x -= nx * push * wi
                            ei.y -= ny * push * wi
                            ej.x += nx * push * wj
                            ej.y += ny * push * wj

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
                was_cursed = getattr(en, "curse_timer", 0) > 0
                was_frozen = getattr(en, "ice_timer", 0) > 0
                self.kills += 1
                self.player.kills += 1
                self.upgrade_manager.on_kill(enemy_was_cursed=was_cursed, enemy_was_frozen=was_frozen)
                self.orbs.append(XPOrb(en.x, en.y, XP_PER_ORB))
                
                # Splinter on kill
                if self.player.splinter_on_kill:
                    self._spawn_splinter_bullets(en.x, en.y)
                
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
                    speed = 3.0 if en.kind != "boss" else 8.0  # Slower bullets
                    self.enemy_bullets.append({"x": en.x, "y": en.y, "vx": dx / l * speed, "vy": dy / l * speed, "r": 10 if en.kind == "boss" else 8, "dmg": 1})  # Bigger bullets

        # Summoner enemies spawn minions
        for en in self.enemies:
            base_kind = getattr(en, "kind", "").replace("elite_", "")
            if base_kind == "summoner":
                if not hasattr(en, "summon_cd"):
                    en.summon_cd = random.uniform(3.0, 5.0)
                en.summon_cd -= dt
                if en.summon_cd <= 0:
                    en.summon_cd = random.uniform(3.0, 5.0)
                    # Spawn 2-3 minions around this enemy
                    minion_count = random.randint(2, 3)
                    for _ in range(minion_count):
                        ang = random.uniform(0, math.tau)
                        mx = en.x + math.cos(ang) * 40
                        my = en.y + math.sin(ang) * 40
                        self.spawning_manager.spawn_minion(mx, my)

        # enemy bullets update/collisions
        for eb in list(self.enemy_bullets):
            eb["x"] += eb["vx"] * dt * FPS
            eb["y"] += eb["vy"] * dt * FPS
            
            # Check orbiting shield blocking
            blocked = False
            for shield in self.magic_shields:
                shield_x = shield.get("x", self.player.x)
                shield_y = shield.get("y", self.player.y)
                dist = math.hypot(eb["x"] - shield_x, eb["y"] - shield_y)
                
                if dist < 25:  # Shield hit radius
                    # Shield blocks the bullet
                    blocked = True
                    if eb in self.enemy_bullets:
                        self.enemy_bullets.remove(eb)
                    # Reflect if player has reflect upgrade
                    if getattr(self.player, "shield_reflect", False):
                        # Reflect bullet back
                        eb["vx"] = -eb["vx"] * 1.5
                        eb["vy"] = -eb["vy"] * 1.5
                    break
            if blocked:
                continue
            
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
                if en.hit_sources.get(getattr(b, "uid", None), 0.0) > 0:
                    continue
                if circle_collision(b.x, b.y, b.radius, en.x, en.y, en.radius):
                    if hasattr(b, "uid"):
                        en.hit_sources[b.uid] = 0.22
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
                    if getattr(en, "kind", "") == "boss":
                        push *= 0.25
                    en.x += dx / l * push
                    en.y += dy / l * push
                    if getattr(en, "kind", "") != "boss":
                        en.knockback_pause = 0.2
                        en.knockback_slow = 0.2
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
                    
                    # Execute check - auto-kill low HP enemies
                    if en.hp > 0 and hasattr(en, "max_hp") and en.max_hp > 0:
                        hp_ratio = en.hp / en.max_hp
                        if self.upgrade_manager.check_execute(hp_ratio):
                            en.hp = 0
                            self.damage_texts.append({"x": en.x, "y": en.y - 20, "val": "EXECUTE", "life": 0.6, "color": (255, 50, 50)})
                    
                    killed = en.hp <= 0
                    
                    # Bullet bouncing off enemies
                    bounces_left = getattr(b, "bounces_left", 0)
                    bounced_enemies = getattr(b, "bounced_enemies", set())
                    
                    should_remove_bullet = True
                    if bounces_left > 0 and id(en) not in bounced_enemies:
                        # Bounce to next enemy
                        bounced_enemies.add(id(en))
                        b.bounced_enemies = bounced_enemies
                        b.bounces_left -= 1
                        
                        # Apply bounce damage bonus
                        bonus = getattr(self.player, "bounce_damage_bonus", 0)
                        if bonus > 0:
                            b.damage = int(b.damage * (1 + bonus))
                        
                        # Find next target to bounce to
                        other_enemies = [e for e in self.enemies if id(e) not in bounced_enemies and e.hp > 0]
                        if other_enemies:
                            # Bounce homing - seek nearest enemy
                            if getattr(self.player, "bounce_homing", False):
                                closest = min(other_enemies, key=lambda e: (e.x - b.x) ** 2 + (e.y - b.y) ** 2)
                            else:
                                closest = random.choice(other_enemies)
                            ddx = closest.x - b.x
                            ddy = closest.y - b.y
                            dist = max(1, math.hypot(ddx, ddy))
                            speed = math.hypot(b.vx, b.vy)
                            b.vx = (ddx / dist) * speed
                            b.vy = (ddy / dist) * speed
                            should_remove_bullet = False
                    
                    if should_remove_bullet:
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
                        was_cursed = getattr(en, "curse_timer", 0) > 0
                        was_frozen = getattr(en, "ice_timer", 0) > 0
                        self.kills += 1
                        self.player.kills += 1
                        self.upgrade_manager.on_kill(enemy_was_cursed=was_cursed, enemy_was_frozen=was_frozen)
                        self.orbs.append(XPOrb(en.x, en.y, XP_PER_ORB))
                        
                        # Splinter on kill - spawn bullets from dead enemy
                        if self.player.splinter_on_kill:
                            self._spawn_splinter_bullets(en.x, en.y)
                        
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
                    # Check dodge
                    if self.upgrade_manager.check_dodge():
                        # Dodged! Add visual feedback
                        self.damage_texts.append({"x": self.player.x, "y": self.player.y - 20, "val": "DODGE", "life": 0.5, "color": (100, 200, 255)})
                        continue
                    self.player.take_damage(1)
                    self.upgrade_manager.on_hit()
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
                self.upgrade_manager.on_xp_pickup()
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
                if en.hit_sources.get(orb.get("uid"), 0.0) > 0:
                    continue
                dx = en.x - ox
                dy = en.y - oy
                if dx * dx + dy * dy <= (en.radius + radius) ** 2:
                    en.hp -= self.player.aura_orb_damage
                    en.flash_timer = 0.1
                    en.aura_iframes = 0.25
                    en.hit_sources[orb.get("uid")] = 0.2
                    if getattr(en, "kind", "") != "boss":
                        en.knockback_pause = 0.2
                        en.knockback_slow = 0.2
                    # knockback away from the player position
                    kx = en.x - self.player.x
                    ky = en.y - self.player.y
                    kl = math.hypot(kx, ky) or 1.0
                    push = self.player.aura_orb_knockback
                    if getattr(en, "kind", "") == "boss":
                        push *= 0.2
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

    def _update_summons(self, dt):
        """Update all summon systems: ghosts, dragon, magic weapons, gale, glare."""
        self._update_ghosts(dt)
        self._update_dragon(dt)
        self._update_magic_lenses(dt)
        self._update_magic_shields(dt)
        self._update_magic_scythes(dt)
        self._update_magic_spears(dt)
        self._update_gale(dt)
        self._update_glare(dt)
        self._update_lightning_fx(dt)
        self._update_fireball_fx(dt)

    def _update_ghosts(self, dt):
        """Update all ghost/drone/phantom systems."""
        self._update_free_ghosts(dt)  # Free-moving, touch damage
        self._update_orbit_drones(dt)  # Orbiting, shooting
        self._update_phantoms(dt)
    
    def _update_free_ghosts(self, dt):
        """Update ghost summons - chase and damage enemies on touch."""
        target_count = getattr(self.player, "ghost_count", 0)
        
        # Add ghosts with proper tracking data
        while len(self.ghosts) < target_count:
            self.ghosts.append({
                "x": self.player.x,
                "y": self.player.y,
                "vx": 0,
                "vy": 0,
                "target": None,
                "hit_cooldowns": {}  # Per-enemy cooldowns: {enemy_id: cooldown_time}
            })
        # Remove extra ghosts
        if len(self.ghosts) > target_count:
            self.ghosts = self.ghosts[:target_count]
        
        if not self.ghosts:
            return
        
        # Ghost stats
        ghost_speed = 200  # 2x enemy base speed (100), very fast
        vision_range = 400  # Full screen vision
        touch_radius = 20  # Collision radius
        hit_cooldown = 1.0  # 1 second cooldown per enemy
        
        base_dmg = getattr(self.player, "drone_damage", 0)
        if base_dmg <= 0:
            base_dmg = getattr(self.player, "ghost_damage", 0)
        if base_dmg <= 0:
            base_dmg = int(self.player.damage * 0.4)
        ghost_damage = int(base_dmg * getattr(self.player, "summon_damage_mult", 1.0))
        ghost_burn = getattr(self.player, "drone_burn", False) or getattr(self.player, "ghost_burn", False)
        ghost_poison = getattr(self.player, "drone_poison", False)
        
        for g in self.ghosts:
            # Update per-enemy cooldowns
            cooldowns = g.get("hit_cooldowns", {})
            for eid in list(cooldowns.keys()):
                cooldowns[eid] -= dt
                if cooldowns[eid] <= 0:
                    del cooldowns[eid]
            g["hit_cooldowns"] = cooldowns
            
            # Find closest enemy in vision range that's not on cooldown
            available_enemies = [
                e for e in self.enemies 
                if math.hypot(e.x - self.player.x, e.y - self.player.y) < vision_range
                and id(e) not in cooldowns
                and e.hp > 0
            ]
            
            target = None
            if available_enemies:
                target = min(available_enemies, key=lambda e: (e.x - g["x"]) ** 2 + (e.y - g["y"]) ** 2)
            
            # Movement - fluid chase or return to player
            if target:
                # Chase target smoothly
                dx = target.x - g["x"]
                dy = target.y - g["y"]
                dist = max(1, math.hypot(dx, dy))
                
                # Smooth acceleration toward target
                target_vx = (dx / dist) * ghost_speed
                target_vy = (dy / dist) * ghost_speed
                lerp = min(1.0, dt * 8.0)  # Smooth interpolation
                g["vx"] = g.get("vx", 0) * (1 - lerp) + target_vx * lerp
                g["vy"] = g.get("vy", 0) * (1 - lerp) + target_vy * lerp
                
                # Check collision with target
                if dist < touch_radius + target.radius:
                    # Damage enemy
                    target.hp -= ghost_damage
                    target.flash_timer = 0.15
                    self.damage_texts.append({"x": target.x, "y": target.y - 10, "val": int(ghost_damage), "life": 0.5, "color": (180, 220, 255)})
                    
                    # Apply status effects
                    if ghost_burn:
                        target.burn_timer = max(target.burn_timer, 2.0)
                        target.burn_dps = max(target.burn_dps, ghost_damage * 0.2)
                    if ghost_poison:
                        target.poison_timer = max(target.poison_timer, 3.0)
                        target.poison_dps = max(target.poison_dps, ghost_damage * 0.15)
                    
                    # Set cooldown for this enemy
                    g["hit_cooldowns"][id(target)] = hit_cooldown
            else:
                # No target - orbit around player
                dist_to_player = math.hypot(g["x"] - self.player.x, g["y"] - self.player.y)
                if dist_to_player > 60:
                    # Return to player
                    dx = self.player.x - g["x"]
                    dy = self.player.y - g["y"]
                    dist = max(1, math.hypot(dx, dy))
                    target_vx = (dx / dist) * ghost_speed * 0.5
                    target_vy = (dy / dist) * ghost_speed * 0.5
                    lerp = min(1.0, dt * 5.0)
                    g["vx"] = g.get("vx", 0) * (1 - lerp) + target_vx * lerp
                    g["vy"] = g.get("vy", 0) * (1 - lerp) + target_vy * lerp
                else:
                    # Near player - slow orbit
                    g["vx"] *= 0.9
                    g["vy"] *= 0.9
            
            # Apply movement
            g["x"] += g.get("vx", 0) * dt
            g["y"] += g.get("vy", 0) * dt
    
    def _update_phantoms(self, dt):
        """Update phantom summons - actively seek enemies while following player like dragon."""
        if not hasattr(self, "phantoms"):
            self.phantoms = []
        
        target_count = getattr(self.player, "phantom_count", 0)
        
        # Add phantoms
        while len(self.phantoms) < target_count:
            self.phantoms.append({
                "x": self.player.x + random.uniform(-50, 50),
                "y": self.player.y + random.uniform(-50, 50),
                "vx": 0,
                "vy": 0,
                "cd": 0,
                "max_dist": 700,  # Max distance from player before returning
                "chase_dist": 350  # Get very close to enemies to attack
            })
        if len(self.phantoms) > target_count:
            self.phantoms = self.phantoms[:target_count]
        
        if not self.phantoms:
            return
        
        phantom_speed = 200 * getattr(self.player, "phantom_speed", 1.0)
        phantom_damage = getattr(self.player, "phantom_damage", 15) * getattr(self.player, "summon_damage_mult", 1.0)
        phantom_slow = getattr(self.player, "phantom_slow", False)
        phantom_lifesteal = getattr(self.player, "phantom_lifesteal", False)
        vision_range = 400  # How far phantom can see enemies
        
        for p in self.phantoms:
            p["cd"] -= dt
            
            # Check distance to player
            dist_to_player = math.hypot(p["x"] - self.player.x, p["y"] - self.player.y)
            
            # Find enemy in vision range closest to phantom (active seeking)
            target_enemy = None
            dist_to_enemy = 9999
            if self.enemies:
                visible = [e for e in self.enemies if math.hypot(e.x - p["x"], e.y - p["y"]) < vision_range]
                if visible:
                    target_enemy = min(visible, key=lambda en: (en.x - p["x"]) ** 2 + (en.y - p["y"]) ** 2)
                    dist_to_enemy = math.hypot(target_enemy.x - p["x"], target_enemy.y - p["y"])
            
            # Decide movement - prioritize chasing enemies while staying tethered to player
            if dist_to_player > p["max_dist"]:
                # Too far from player - return urgently
                dx = self.player.x - p["x"]
                dy = self.player.y - p["y"]
                dist = max(1, math.hypot(dx, dy))
                p["vx"] = (dx / dist) * phantom_speed
                p["vy"] = (dy / dist) * phantom_speed
            elif target_enemy:
                # Actively chase enemy
                dx = target_enemy.x - p["x"]
                dy = target_enemy.y - p["y"]
                dist = max(1, math.hypot(dx, dy))
                chase_speed = phantom_speed if dist_to_player < p["max_dist"] - 80 else phantom_speed * 0.5
                p["vx"] = (dx / dist) * chase_speed
                p["vy"] = (dy / dist) * chase_speed
            else:
                # No enemy - float near player
                if dist_to_player > 60:
                    dx = self.player.x - p["x"]
                    dy = self.player.y - p["y"]
                    dist = max(1, math.hypot(dx, dy))
                    p["vx"] = (dx / dist) * phantom_speed * 0.3
                    p["vy"] = (dy / dist) * phantom_speed * 0.3
                else:
                    p["vx"] *= 0.9
                    p["vy"] *= 0.9
            
            # Apply movement
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            
            # Attack when close to enemy (touch damage)
            if p["cd"] <= 0 and target_enemy and dist_to_enemy < target_enemy.radius + 20:
                target_enemy.hp -= phantom_damage
                target_enemy.flash_timer = 0.15
                self.damage_texts.append({"x": target_enemy.x, "y": target_enemy.y - 10, "val": int(phantom_damage), "life": 0.5, "color": (200, 200, 255)})
                
                if phantom_slow:
                    target_enemy.ice_timer = max(target_enemy.ice_timer, 1.5)
                if phantom_lifesteal:
                    self.player.hearts = min(self.player.max_hearts, self.player.hearts + 1)
                
                p["cd"] = 0.8  # Attack cooldown
        
        # Phantom-to-phantom collision (push apart)
        phantom_radius = 15
        for i, p1 in enumerate(self.phantoms):
            for p2 in self.phantoms[i+1:]:
                dx = p2["x"] - p1["x"]
                dy = p2["y"] - p1["y"]
                dist = math.hypot(dx, dy)
                min_dist = phantom_radius * 2
                if dist < min_dist and dist > 0:
                    overlap = (min_dist - dist) / 2
                    nx, ny = dx / dist, dy / dist
                    p1["x"] -= nx * overlap
                    p1["y"] -= ny * overlap
                    p2["x"] += nx * overlap
                    p2["y"] += ny * overlap

    def _update_orbit_drones(self, dt):
        """Update orbiting drone summons - circle around player and shoot enemies."""
        target_count = getattr(self.player, "drone_count", 0)
        
        # Add drones with proper spacing
        while len(self.drones) < target_count:
            index = len(self.drones)
            base_angle = index * (math.tau / max(1, target_count))
            self.drones.append({
                "index": index,
                "angle": base_angle,
                "cd": random.uniform(0.3, 0.8),
                "x": self.player.x,
                "y": self.player.y
            })
        # Remove extra drones
        if len(self.drones) > target_count:
            self.drones = self.drones[:target_count]
        
        if not self.drones:
            return
        
        # Redistribute angles to keep even spacing
        for i, d in enumerate(self.drones):
            d["index"] = i
        
        # Find target
        target = None
        if self.enemies:
            visible_enemies = [e for e in self.enemies if math.hypot(e.x - self.player.x, e.y - self.player.y) < 400]
            if visible_enemies:
                target = min(visible_enemies, key=lambda en: (en.x - self.player.x) ** 2 + (en.y - self.player.y) ** 2)
        
        orbit_r = 80  # Orbit radius around player
        drone_damage = int(self.player.damage * 0.3 * getattr(self.player, "summon_damage_mult", 1.0))
        
        for d in self.drones:
            # Keep even spacing - rotate together
            base_offset = d["index"] * (math.tau / max(1, len(self.drones)))
            d["angle"] = (d.get("angle", 0) + dt * 2.0) % math.tau
            # Position at fixed offset for even distribution
            actual_angle = d["angle"] + base_offset
            d["x"] = self.player.x + math.cos(actual_angle) * orbit_r
            d["y"] = self.player.y + math.sin(actual_angle) * orbit_r
            d["cd"] -= dt
            
            # Shoot at target
            if target and d["cd"] <= 0:
                dx = target.x - d["x"]
                dy = target.y - d["y"]
                angle = math.atan2(dy, dx)
                bdx = math.cos(angle)
                bdy = math.sin(angle)
                b = Bullet(d["x"], d["y"], bdx, bdy, drone_damage, self.player.bullet_speed * 0.7)
                self.bullets.append(b)
                d["cd"] = 0.8 / getattr(self.player, "summon_attack_speed_mult", 1.0)

    def _update_dragon(self, dt):
        """Update dragon companion - free movement that follows player and chases enemies."""
        if not getattr(self.player, "dragon_active", False):
            self.dragon = None
            return
        
        if self.dragon is None:
            self.dragon = {
                "x": self.player.x + 60,
                "y": self.player.y,
                "vx": 0,
                "vy": 0,
                "cd": 0,
                "max_dist": 350,  # Max distance from player before following
                "chase_dist": 300  # How close dragon gets to enemies
            }
        
        d = self.dragon
        d["cd"] -= dt
        
        # Dragon movement AI
        dragon_speed = 180  # Pixels per second
        
        # Check distance to player
        dist_to_player = math.hypot(d["x"] - self.player.x, d["y"] - self.player.y)
        
        # Find enemy closest to the player (for more helpful targeting)
        target_enemy = None
        dist_to_enemy = 9999
        if self.enemies:
            target_enemy = min(self.enemies, key=lambda en: (en.x - self.player.x) ** 2 + (en.y - self.player.y) ** 2)
            dist_to_enemy = math.hypot(target_enemy.x - d["x"], target_enemy.y - d["y"])
        
        # Decide what to do
        if dist_to_player > d["max_dist"]:
            # Too far from player - return to player
            dx = self.player.x - d["x"]
            dy = self.player.y - d["y"]
            dist = max(1, math.hypot(dx, dy))
            d["vx"] = (dx / dist) * dragon_speed
            d["vy"] = (dy / dist) * dragon_speed
        elif target_enemy and dist_to_enemy > d["chase_dist"] and dist_to_player < d["max_dist"] - 50:
            # Enemy exists and we're not too far from player - chase enemy
            dx = target_enemy.x - d["x"]
            dy = target_enemy.y - d["y"]
            dist = max(1, math.hypot(dx, dy))
            d["vx"] = (dx / dist) * dragon_speed * 0.8
            d["vy"] = (dy / dist) * dragon_speed * 0.8
        elif target_enemy and dist_to_enemy <= d["chase_dist"]:
            # Close to enemy - hover and attack
            d["vx"] *= 0.9
            d["vy"] *= 0.9
        else:
            # Idle near player - gentle float
            angle_to_player = math.atan2(self.player.y - d["y"], self.player.x - d["x"])
            d["vx"] = math.cos(angle_to_player) * 30
            d["vy"] = math.sin(angle_to_player) * 30
        
        # Apply movement
        d["x"] += d["vx"] * dt
        d["y"] += d["vy"] * dt
        
        # Attack if close to enemy
        if d["cd"] <= 0 and target_enemy and dist_to_enemy < 300:
            dragon_damage = getattr(self.player, "dragon_damage", 20) * getattr(self.player, "summon_damage_mult", 1.0)
            # Dragon breathes fire - apply burn
            target_enemy.hp -= dragon_damage
            target_enemy.burn_timer = max(target_enemy.burn_timer, 3.0)
            target_enemy.burn_dps = max(target_enemy.burn_dps, dragon_damage * 0.3)
            target_enemy.flash_timer = 0.1
            self.damage_texts.append({"x": target_enemy.x, "y": target_enemy.y - 10, "val": int(dragon_damage), "life": 0.5, "color": (255, 100, 50)})
            self._spawn_status_fx(target_enemy.x, target_enemy.y, kind="fire")
            # Store fire breath target for visual
            d["fire_target"] = {"x": target_enemy.x, "y": target_enemy.y, "timer": 0.3}
            d["cd"] = 1.0 / getattr(self.player, "dragon_attack_speed", 1.0)
        
        # Update fire breath visual timer
        if "fire_target" in d:
            d["fire_target"]["timer"] -= dt
            if d["fire_target"]["timer"] <= 0:
                del d["fire_target"]

    def _update_magic_lenses(self, dt):
        """Update magic lens summons - orbit and multiply bullets passing through."""
        target_count = getattr(self.player, "lens_count", 0)
        
        # Initialize lenses with proper spacing
        while len(self.magic_lenses) < target_count:
            base_angle = len(self.magic_lenses) * (math.tau / max(1, target_count))
            self.magic_lenses.append({
                "angle": base_angle,
                "x": self.player.x,
                "y": self.player.y
            })
        if len(self.magic_lenses) > target_count:
            self.magic_lenses = self.magic_lenses[:target_count]
        
        if not self.magic_lenses:
            return
        
        # Lens orbits around player, facing opposite direction
        orbit_r = 100  # Closer to player
        lens_radius = 25  # Size of lens hit area
        orbit_speed = 1.2  # Radians per second for ALL lenses together
        
        # All lenses share the same rotation angle (orbit as a group)
        if not hasattr(self, "_lens_orbit_angle"):
            self._lens_orbit_angle = 0
        self._lens_orbit_angle = (self._lens_orbit_angle + dt * orbit_speed) % math.tau
        
        # Update lens positions - all orbit together with even spacing
        for i, lens in enumerate(self.magic_lenses):
            # Evenly distributed, all rotating together
            angle = self._lens_orbit_angle + i * (math.tau / max(1, len(self.magic_lenses)))
            lens["angle"] = angle  # Store for drawing
            lens["x"] = self.player.x + math.cos(angle) * orbit_r
            lens["y"] = self.player.y + math.sin(angle) * orbit_r
        
        # Check for bullets passing through lenses
        new_bullets = []
        for b in self.bullets:
            if getattr(b, "passed_through_lens", False):
                continue  # Already multiplied
            
            for lens in self.magic_lenses:
                dx = b.x - lens["x"]
                dy = b.y - lens["y"]
                dist = math.hypot(dx, dy)
                
                if dist < lens_radius:
                    # Bullet passes through lens - always multiply by 2 (one extra bullet)
                    b.passed_through_lens = True
                    
                    # Enlarge bullet if player has lens_enlarge upgrade (capped for size control)
                    lens_enlarge = min(getattr(self.player, "lens_enlarge", 1.0), 1.18)
                    if lens_enlarge > 1.0:
                        b.radius = max(1, int(b.radius * lens_enlarge))
                    
                    # Create ONE additional bullet with slight spread
                    spread_offset = 0.08
                    bullet_angle = math.atan2(b.vy, b.vx) + spread_offset
                    speed = math.hypot(b.vx, b.vy)
                    new_b = Bullet(
                        b.x, b.y,
                        math.cos(bullet_angle), math.sin(bullet_angle),
                        b.damage, speed,
                        status=b.status.copy() if hasattr(b, "status") else {}
                    )
                    new_b.radius = max(1, int(b.radius * lens_enlarge)) if lens_enlarge > 1.0 else b.radius
                    new_b.piercing = b.piercing
                    new_b.passed_through_lens = True
                    if hasattr(b, "pierce_left"):
                        new_b.pierce_left = b.pierce_left
                    new_bullets.append(new_b)
                    break
        
        self.bullets.extend(new_bullets)

    def _update_magic_shields(self, dt):
        """Update orbiting shield summons."""
        shield_hp = getattr(self.player, "shield_hp", 0)
        if shield_hp <= 0:
            self.magic_shields = []
            return
        
        shield_count = getattr(self.player, "shield_segments", 1)
        
        # Initialize shields with proper spacing
        while len(self.magic_shields) < shield_count:
            base_angle = len(self.magic_shields) * (math.tau / max(1, shield_count))
            self.magic_shields.append({
                "angle": base_angle,
                "x": self.player.x,
                "y": self.player.y
            })
        if len(self.magic_shields) > shield_count:
            self.magic_shields = self.magic_shields[:shield_count]
        
        # Shield orbit around player
        orbit_r = 80  # Orbit distance close to player
        orbit_speed = 1.5  # Radians per second for ALL shields together
        
        # All shields share the same rotation angle (orbit as a group)
        if not hasattr(self, "_shield_orbit_angle"):
            self._shield_orbit_angle = 0
        self._shield_orbit_angle = (self._shield_orbit_angle + dt * orbit_speed) % math.tau
        
        # Update shield positions - all orbit together with even spacing
        for i, shield in enumerate(self.magic_shields):
            angle = self._shield_orbit_angle + i * (math.tau / max(1, len(self.magic_shields)))
            shield["angle"] = angle  # Store for drawing
            shield["x"] = self.player.x + math.cos(angle) * orbit_r
            shield["y"] = self.player.y + math.sin(angle) * orbit_r

    def _update_magic_scythes(self, dt):
        """Update magic scythe summons - orbiting damage."""
        target_count = getattr(self.player, "scythe_count", 0)
        while len(self.magic_scythes) < target_count:
            base_angle = len(self.magic_scythes) * (math.tau / max(1, target_count))
            self.magic_scythes.append({
                "angle": base_angle,
                "cd": 0
            })
        if len(self.magic_scythes) > target_count:
            self.magic_scythes = self.magic_scythes[:target_count]
        
        if not self.magic_scythes:
            return
        
        orbit_r = 90
        scythe_damage = getattr(self.player, "scythe_damage", 40) * getattr(self.player, "summon_damage_mult", 1.0)
        
        for scythe in self.magic_scythes:
            scythe["angle"] += dt * 3.5
            scythe["cd"] -= dt
            sx = self.player.x + math.cos(scythe["angle"]) * orbit_r
            sy = self.player.y + math.sin(scythe["angle"]) * orbit_r
            scythe["x"] = sx
            scythe["y"] = sy
            
            if scythe["cd"] <= 0:
                # Check for enemy collisions
                for en in self.enemies:
                    dx = en.x - sx
                    dy = en.y - sy
                    if dx * dx + dy * dy < (en.radius + 25) ** 2:
                        en.hp -= scythe_damage
                        en.flash_timer = 0.1
                        self.damage_texts.append({"x": en.x, "y": en.y - 10, "val": int(scythe_damage), "life": 0.4, "color": (100, 255, 100)})
                        scythe["cd"] = 0.3
                        break

    def _update_magic_spears(self, dt):
        """Update magic spear summons - stabbing attacks."""
        target_count = getattr(self.player, "spear_count", 0)
        while len(self.magic_spears) < target_count:
            self.magic_spears.append({
                "angle": random.uniform(0, math.tau),
                "cd": random.uniform(0.3, 0.6),
                "state": "orbit",  # orbit or attack
                "target_x": 0,
                "target_y": 0
            })
        if len(self.magic_spears) > target_count:
            self.magic_spears = self.magic_spears[:target_count]
        
        if not self.magic_spears:
            return
        
        orbit_r = 70
        spear_damage = getattr(self.player, "spear_damage", 20) * getattr(self.player, "summon_damage_mult", 1.0)
        
        for spear in self.magic_spears:
            spear["cd"] -= dt
            spear["angle"] += dt * 1.5
            spear["x"] = self.player.x + math.cos(spear["angle"]) * orbit_r
            spear["y"] = self.player.y + math.sin(spear["angle"]) * orbit_r
            
            if spear["cd"] <= 0 and self.enemies:
                target = min(self.enemies, key=lambda en: (en.x - spear["x"]) ** 2 + (en.y - spear["y"]) ** 2)
                dist = math.hypot(target.x - spear["x"], target.y - spear["y"])
                if dist < 200:
                    target.hp -= spear_damage
                    target.flash_timer = 0.1
                    self.damage_texts.append({"x": target.x, "y": target.y - 10, "val": int(spear_damage), "life": 0.4, "color": (255, 200, 100)})
                    spear["cd"] = 0.8 / getattr(self.player, "summon_attack_speed_mult", 1.0)

    def _update_gale(self, dt):
        """Update gale AoE damage around player."""
        if self.upgrade_manager.should_gale_fire():
            gale_damage = getattr(self.player, "gale_damage", 20)
            gale_radius = 150
            if getattr(self.player, "gale_scales_speed", False):
                gale_damage *= (self.player.speed / 5.0)
            
            for en in self.enemies:
                dx = en.x - self.player.x
                dy = en.y - self.player.y
                dist_sq = dx * dx + dy * dy
                if dist_sq < gale_radius ** 2:
                    # Center bonus damage
                    if dist_sq < 50 ** 2 and getattr(self.player, "gale_center_damage_mult", 0) > 0:
                        dmg = gale_damage * self.player.gale_center_damage_mult
                    else:
                        dmg = gale_damage
                    en.hp -= dmg
                    en.flash_timer = 0.1
                    self.damage_texts.append({"x": en.x, "y": en.y - 10, "val": int(dmg), "life": 0.4, "color": (150, 200, 255)})

    def _update_glare(self, dt):
        """Update glare - full screen flash that damages all visible enemies."""
        if not self.upgrade_manager.should_glare_fire():
            return
        
        p = self.player
        glare_damage = getattr(p, "glare_damage", 20)
        glare_slow = getattr(p, "glare_slow", 0)
        glare_stun = getattr(p, "glare_stun", False)
        glare_stun_duration = getattr(p, "glare_stun_duration", 1.0)
        glare_execute = getattr(p, "glare_execute", 0)
        
        # Flash effect
        self.glare_flash_timer = 0.3
        
        # Damage all enemies on screen
        cam = self.get_camera()
        for en in self.enemies:
            # Check if enemy is on screen
            sx = en.x - cam[0]
            sy = en.y - cam[1]
            if 0 <= sx <= self.w and 0 <= sy <= self.h:
                # Execute check
                if glare_execute > 0 and en.hp / en.max_hp <= glare_execute:
                    en.hp = 0
                    self.damage_texts.append({"x": en.x, "y": en.y - 10, "val": "EXECUTE", "life": 0.6, "color": COLOR_RED})
                else:
                    en.hp -= glare_damage
                    en.flash_timer = 0.15
                    self.damage_texts.append({"x": en.x, "y": en.y - 10, "val": int(glare_damage), "life": 0.4, "color": (255, 255, 200)})
                
                # Apply slow
                if glare_slow > 0:
                    en.ice_timer = max(en.ice_timer, 2.0)
                
                # Apply stun
                if glare_stun:
                    en.knockback_pause = max(en.knockback_pause, glare_stun_duration)

    def _handle_shot_effects(self, effects: dict, target_pos: tuple):
        """Handle special effects triggered by shooting."""
        if "lightning" in effects:
            data = effects["lightning"]
            self._spawn_lightning(target_pos, data["damage"], data.get("area_mult", 1.0))
        
        if "fireball" in effects:
            data = effects["fireball"]
            self._spawn_fireball(target_pos, data["damage"])

    def _handle_empty_mag_effects(self, effects: dict):
        """Handle special effects triggered when magazine empties."""
        if "smite" in effects:
            data = effects["smite"]
            self._spawn_smite(data["damage"])
        
        if "fan_fire" in effects:
            data = effects["fan_fire"]
            self._spawn_fan_fire(data["count"], data["damage_ratio"])
        
        if "ice_shards" in effects:
            data = effects["ice_shards"]
            self._spawn_ice_shards(data["count"], data.get("freeze", True))

    def _spawn_lightning(self, target_pos, damage, area_mult=1.0):
        """Spawn a lightning strike at the target position."""
        tx, ty = target_pos
        radius = 80 * area_mult
        
        # Add visual effect
        self.lightning_fx.append({
            "x": tx, "y": ty,
            "radius": radius,
            "life": 0.3
        })
        
        # Damage enemies in radius
        for en in self.enemies:
            dx = en.x - tx
            dy = en.y - ty
            if dx * dx + dy * dy < radius ** 2:
                en.hp -= damage
                en.flash_timer = 0.15
                self.damage_texts.append({"x": en.x, "y": en.y - 10, "val": int(damage), "life": 0.5, "color": (255, 255, 100)})
                # Electro bug - chain to nearby enemies
                if getattr(self.player, "electro_bug", False):
                    chain_targets = getattr(self.player, "electro_bug_targets", 2)
                    chain_count = 0
                    for other in self.enemies:
                        if other is en or chain_count >= chain_targets:
                            break
                        odx = other.x - en.x
                        ody = other.y - en.y
                        if odx * odx + ody * ody < 100 ** 2:
                            other.hp -= damage * 0.5
                            other.flash_timer = 0.1
                            chain_count += 1

    def _spawn_fireball(self, target_pos, damage):
        """Spawn a fireball at the target position."""
        tx, ty = target_pos
        radius = 60
        
        self.fireball_fx.append({
            "x": tx, "y": ty,
            "radius": radius,
            "life": 0.4
        })
        
        for en in self.enemies:
            dx = en.x - tx
            dy = en.y - ty
            if dx * dx + dy * dy < radius ** 2:
                en.hp -= damage
                en.burn_timer = max(en.burn_timer, 3.0)
                en.burn_dps = max(en.burn_dps, damage * 0.3)
                en.flash_timer = 0.15
                self.damage_texts.append({"x": en.x, "y": en.y - 10, "val": int(damage), "life": 0.5, "color": (255, 100, 50)})
                self._spawn_status_fx(en.x, en.y, kind="fire")

    def _spawn_smite(self, damage):
        """Spawn holy smite damaging all nearby enemies."""
        radius = 200
        for en in self.enemies:
            dx = en.x - self.player.x
            dy = en.y - self.player.y
            if dx * dx + dy * dy < radius ** 2:
                en.hp -= damage
                en.flash_timer = 0.2
                self.damage_texts.append({"x": en.x, "y": en.y - 10, "val": int(damage), "life": 0.5, "color": (255, 255, 200)})

    def _spawn_fan_fire(self, count, damage_ratio):
        """Spawn a circle of bullets around the player."""
        damage = int(self.player.damage * damage_ratio)
        for i in range(count):
            angle = (math.tau / count) * i
            vx = math.cos(angle)
            vy = math.sin(angle)
            b = Bullet(self.player.x, self.player.y, vx, vy, damage, self.player.bullet_speed * 0.8, status=self.player.bullet_status.copy())
            self.bullets.append(b)

    def _spawn_ice_shards(self, count, freeze):
        """Spawn ice shards around the player."""
        damage = int(self.player.damage * 0.3)
        status = {"ice": True, "burn": False, "poison": False}
        for i in range(count):
            angle = (math.tau / count) * i
            vx = math.cos(angle)
            vy = math.sin(angle)
            b = Bullet(self.player.x, self.player.y, vx, vy, damage, self.player.bullet_speed * 0.6, status=status)
            self.bullets.append(b)

    def _spawn_splinter_bullets(self, x, y):
        """Spawn splinter bullets from a dead enemy position."""
        count = self.player.splinter_count
        damage = int(self.player.damage * self.player.splinter_damage_ratio)
        for i in range(count):
            angle = random.uniform(0, math.tau)
            vx = math.cos(angle)
            vy = math.sin(angle)
            b = Bullet(x, y, vx, vy, damage, self.player.bullet_speed * 0.7, status=self.player.bullet_status.copy())
            b.splinter = True  # Mark as splinter so they don't trigger more splinters
            self.bullets.append(b)

    def _update_lightning_fx(self, dt):
        """Update lightning visual effects."""
        for fx in list(self.lightning_fx):
            fx["life"] -= dt
            if fx["life"] <= 0:
                self.lightning_fx.remove(fx)

    def _update_fireball_fx(self, dt):
        """Update fireball visual effects."""
        for fx in list(self.fireball_fx):
            fx["life"] -= dt
            if fx["life"] <= 0:
                self.fireball_fx.remove(fx)

    def spawn_enemy(self):
        half = WORLD_SIZE / 2
        dmin, dmax = 600, 900
        ang = random.uniform(0, math.tau)
        r = random.uniform(dmin, dmax)
        x = self.player.x + math.cos(ang) * r
        y = self.player.y + math.sin(ang) * r
        x = clamp(x, -half, half)
        y = clamp(y, -half, half)

        # Gradual scaling based on elapsed time
        t = self.elapsed_time
        
        # Very gradual HP scaling: starts at 1.0, reaches 2.0 at 3 min, 3.0 at 6 min
        hp_scale = 1.0 + (t / 180.0)
        # Even more gradual speed scaling: starts at 1.0, reaches 1.3 at 3 min
        speed_scale = 1.0 + (t / 600.0)  # Much slower speed scaling

        # Timed boss - test mode: 10s, normal: 60s
        boss_interval = 10 if self.test_mode else 60
        if int(t // boss_interval) > self.bosses_spawned:
            self.bosses_spawned += 1
            kind = "boss"
            boss_stage = self.bosses_spawned
        else:
            # Gradual enemy type unlocking with weighted spawns
            # Start with mostly normals, slowly introduce others
            pool = ["normal"]
            weights = [1.0]
            
            # Fast enemies unlock at 45s, low chance initially
            if t >= 45:
                pool.append("fast")
                fast_weight = min(0.25, (t - 45) / 120)  # Ramps up over 2 min
                weights.append(fast_weight)
            
            # Tank enemies unlock at 90s
            if t >= 90:
                pool.append("tank")
                tank_weight = min(0.20, (t - 90) / 120)
                weights.append(tank_weight)
            
            # Sprinter enemies unlock at 150s (2.5 min) - was too early at 90s
            if t >= 150:
                pool.append("sprinter")
                sprinter_weight = min(0.15, (t - 150) / 180)  # Slow ramp
                weights.append(sprinter_weight)
            
            # Bruiser enemies unlock at 180s (3 min)
            if t >= 180:
                pool.append("bruiser")
                bruiser_weight = min(0.15, (t - 180) / 120)
                weights.append(bruiser_weight)
            
            # Shooter enemies unlock at 240s (4 min) - very rare at first
            if t >= 240:
                pool.append("shooter")
                shooter_weight = min(0.10, (t - 240) / 180)
                weights.append(shooter_weight)
            
            kind = random.choices(pool, weights=weights, k=1)[0]
            boss_stage = 0

        # Enemy stats with gradual scaling
        if kind == "tank":
            hp = int(ENEMY_BASE_HP * 2.5 * hp_scale)
            speed = ENEMY_BASE_SPEED * 0.6 * speed_scale
        elif kind == "fast":
            hp = int(ENEMY_BASE_HP * 0.6 * hp_scale)
            speed = ENEMY_BASE_SPEED * 1.5 * speed_scale
        elif kind == "sprinter":
            hp = int(ENEMY_BASE_HP * 0.5 * hp_scale)
            speed = ENEMY_BASE_SPEED * 1.8 * speed_scale  # Reduced from 2.4
        elif kind == "bruiser":
            hp = int(ENEMY_BASE_HP * 3.5 * hp_scale)
            speed = ENEMY_BASE_SPEED * 0.8 * speed_scale
        elif kind == "shooter":
            hp = int(ENEMY_BASE_HP * 1.2 * hp_scale)
            speed = ENEMY_BASE_SPEED * 0.9 * speed_scale
        elif kind == "boss":
            if boss_stage == 1:
                hp = int(ENEMY_BASE_HP * 12 * hp_scale)
                speed = ENEMY_BASE_SPEED * 1.0 * speed_scale
            elif boss_stage == 2:
                hp = int(ENEMY_BASE_HP * 16 * hp_scale)
                speed = ENEMY_BASE_SPEED * 1.2 * speed_scale
            else:
                hp = int(ENEMY_BASE_HP * 22 * hp_scale)
                speed = ENEMY_BASE_SPEED * 1.4 * speed_scale
        else:  # normal
            hp = int(ENEMY_BASE_HP * 1.0 * hp_scale)
            speed = ENEMY_BASE_SPEED * 1.0 * speed_scale

        self.enemies.append(Enemy(x, y, hp, speed, kind, boss_stage=boss_stage))

    def roll_levelup(self):
        """Roll available upgrades for level-up screen using the new upgrade tree system."""
        if self.test_mode and self.test_power_queue:
            # Test mode: cycle through all upgrades from upgrade trees
            self.levelup_options = self.test_power_queue[:3]
            self.test_power_queue = self.test_power_queue[3:]
        else:
            # Use new upgrade tree system
            available_upgrades = self.upgrade_manager.get_available_options(count=3)
            self.levelup_options = [u.id for u in available_upgrades]
        
        self.state = STATE_LEVEL_UP
        audio.play_sfx(audio.snd_level_up)
    
    def apply_levelup_choice(self, upgrade_id: str):
        """Apply the selected upgrade from level-up screen."""
        if upgrade_id in UPGRADES_BY_ID:
            # New upgrade tree system
            # In test mode with tier 3 upgrades, apply full tree
            upgrade = UPGRADES_BY_ID[upgrade_id]
            apply_full = self.test_mode and upgrade.tier == 3
            self.upgrade_manager.apply_upgrade(upgrade_id, apply_full_tree=apply_full)
        else:
            # Fall back to old powerup system for legacy support
            apply_powerup(self.player, upgrade_id)

    def roll_evolution(self):
        self.evolution_options = random.sample(EVOLUTIONS, k=min(3, len(EVOLUTIONS)))
        self.state = STATE_EVOLUTION
        audio.play_sfx(audio.snd_level_up)

    def _grant_test_power(self, pid: str):
        if not self.test_mode:
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
            self.draw_glare_flash_overlay()
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
        title = self.font_large.render("SPACE INVADERS", True, COLOR_WHITE)
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
        # Draw magic lenses - smooth arcs orbiting player facing outward
        for lens in self.magic_lenses:
            lx = int(lens.get("x", self.player.x) - cam[0])
            ly = int(lens.get("y", self.player.y) - cam[1])
            
            # Calculate angle from player to lens (so arc faces OUTWARD)
            # Note: pygame y-axis is flipped, so we negate dy for correct angle
            px = int(self.player.x - cam[0])
            py = int(self.player.y - cam[1])
            angle_outward = math.atan2(-(ly - py), lx - px)  # Negate y for pygame coords
            
            # Draw smooth arc facing outward (away from player) - 2x wider
            arc_size = 40  
            arc_rect = pygame.Rect(lx - arc_size // 2, ly - arc_size // 2, arc_size, arc_size)
            # Arc centered on the outward direction
            start_ang = angle_outward - math.pi * 0.35
            end_ang = angle_outward + math.pi * 0.35
            
            # Draw solid arc
            pygame.draw.arc(render_surf, (255, 100, 100), arc_rect, start_ang, end_ang, 4)
        # Draw magic scythes
        for scythe in self.magic_scythes:
            sx = int(scythe.get("x", self.player.x) - cam[0])
            sy = int(scythe.get("y", self.player.y) - cam[1])
            # Draw a curved scythe shape
            pygame.draw.arc(render_surf, (100, 255, 100), (sx - 15, sy - 15, 30, 30), 0, math.pi, 4)
        # Draw magic spears
        for spear in self.magic_spears:
            px = int(spear.get("x", self.player.x) - cam[0])
            py = int(spear.get("y", self.player.y) - cam[1])
            # Draw spear pointing outward from player
            ang = spear.get("angle", 0)
            end_x = px + int(math.cos(ang) * 20)
            end_y = py + int(math.sin(ang) * 20)
            pygame.draw.line(render_surf, (255, 200, 100), (px, py), (end_x, end_y), 4)
        # Draw lightning effects
        for fx in self.lightning_fx:
            lx = int(fx["x"] - cam[0])
            ly = int(fx["y"] - cam[1])
            alpha = int(255 * (fx["life"] / 0.3))
            r = int(fx["radius"])
            surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (255, 255, 100, alpha), (r, r), r)
            pygame.draw.circle(surf, (255, 255, 200, min(255, alpha + 50)), (r, r), r // 2)
            render_surf.blit(surf, (lx - r, ly - r))
        # Draw fireball effects
        for fx in self.fireball_fx:
            fx_x = int(fx["x"] - cam[0])
            fx_y = int(fx["y"] - cam[1])
            alpha = int(255 * (fx["life"] / 0.4))
            r = int(fx["radius"])
            surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (255, 100, 50, alpha), (r, r), r)
            pygame.draw.circle(surf, (255, 200, 100, min(255, alpha + 50)), (r, r), r // 2)
            render_surf.blit(surf, (fx_x - r, fx_y - r))
        for e in self.enemies:
            e.draw(render_surf, cam)
        # Draw drones/phantoms/dragon IN FRONT of enemies (higher z-index)
        # Draw ghosts as ghostly spirits (they touch to damage)
        for g in self.ghosts:
            gx = int(g.get("x", self.player.x) - cam[0])
            gy = int(g.get("y", self.player.y) - cam[1])
            # Ghost - spooky translucent look
            ghost_surf = pygame.Surface((30, 30), pygame.SRCALPHA)
            pygame.draw.circle(ghost_surf, (150, 200, 150, 120), (15, 12), 12)  # Green tint
            pygame.draw.circle(ghost_surf, (180, 230, 180, 160), (15, 12), 8)
            pygame.draw.circle(ghost_surf, (220, 255, 220, 200), (15, 10), 4)
            # Wispy tail
            for i in range(3):
                tail_x = 15 + (i - 1) * 4
                tail_y = 22 + i * 2
                pygame.draw.circle(ghost_surf, (150, 200, 150, 80 - i * 20), (tail_x, tail_y), 4 - i)
            render_surf.blit(ghost_surf, (gx - 15, gy - 15))
        # Draw orbiting drones (they orbit and shoot)
        for d in self.drones:
            dx_d = int(d.get("x", self.player.x) - cam[0])
            dy_d = int(d.get("y", self.player.y) - cam[1])
            # Drone body - metallic look
            pygame.draw.circle(render_surf, (80, 120, 160), (dx_d, dy_d), 12)
            pygame.draw.circle(render_surf, (140, 180, 220), (dx_d, dy_d), 8)
            pygame.draw.circle(render_surf, (200, 220, 255), (dx_d, dy_d), 4)
            # Drone wings
            pygame.draw.line(render_surf, (100, 140, 180), (dx_d - 12, dy_d), (dx_d - 20, dy_d - 5), 2)
            pygame.draw.line(render_surf, (100, 140, 180), (dx_d + 12, dy_d), (dx_d + 20, dy_d - 5), 2)
        for p in getattr(self, "phantoms", []):
            px = int(p.get("x", self.player.x) - cam[0])
            py = int(p.get("y", self.player.y) - cam[1])
            # Ghostly translucent appearance
            phantom_surf = pygame.Surface((30, 30), pygame.SRCALPHA)
            pygame.draw.circle(phantom_surf, (180, 180, 255, 100), (15, 12), 12)
            pygame.draw.circle(phantom_surf, (220, 220, 255, 150), (15, 12), 8)
            pygame.draw.circle(phantom_surf, (255, 255, 255, 180), (15, 10), 4)
            for i in range(3):
                tail_x = 15 + (i - 1) * 5
                tail_y = 22 + i * 2
                pygame.draw.circle(phantom_surf, (200, 200, 255, 80 - i * 20), (tail_x, tail_y), 4 - i)
            render_surf.blit(phantom_surf, (px - 15, py - 15))
        if self.dragon:
            dx = int(self.dragon["x"] - cam[0])
            dy = int(self.dragon["y"] - cam[1])
            # Draw fire breath if attacking
            if "fire_target" in self.dragon:
                ft = self.dragon["fire_target"]
                tx = int(ft["x"] - cam[0])
                ty = int(ft["y"] - cam[1])
                # Draw fire breath line with gradient
                for i in range(3):
                    width = 8 - i * 2
                    alpha = int(200 * (ft["timer"] / 0.3))
                    color = (255, 150 + i * 30, 50 + i * 40)
                    pygame.draw.line(render_surf, color, (dx, dy), (tx, ty), width)
                # Fire burst at target
                burst_r = int(15 * (ft["timer"] / 0.3))
                pygame.draw.circle(render_surf, (255, 200, 100), (tx, ty), burst_r)
            # Dragon body
            pygame.draw.circle(render_surf, (255, 80, 30), (dx, dy), 20)
            pygame.draw.circle(render_surf, (255, 150, 50), (dx, dy), 14)
            pygame.draw.circle(render_surf, (255, 220, 100), (dx, dy), 8)
            wing_pts_l = [(dx - 8, dy), (dx - 28, dy - 12), (dx - 20, dy + 8)]
            wing_pts_r = [(dx + 8, dy), (dx + 28, dy - 12), (dx + 20, dy + 8)]
            pygame.draw.polygon(render_surf, (255, 120, 40), wing_pts_l)
            pygame.draw.polygon(render_surf, (255, 120, 40), wing_pts_r)
            pygame.draw.circle(render_surf, (255, 255, 255), (dx - 5, dy - 4), 4)
            pygame.draw.circle(render_surf, (255, 255, 255), (dx + 5, dy - 4), 4)
            pygame.draw.circle(render_surf, (0, 0, 0), (dx - 5, dy - 4), 2)
            pygame.draw.circle(render_surf, (0, 0, 0), (dx + 5, dy - 4), 2)
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
        # Glare cone visual
        if getattr(self.player, "glare_dps", 0) > 0:
            mx, my = pygame.mouse.get_pos()
            glare_range = 300
            glare_cone = 0.5
            aim_dx = mx - render_w // 2
            aim_dy = my - render_h // 2
            aim_dist = math.hypot(aim_dx, aim_dy)
            if aim_dist > 1:
                aim_dx /= aim_dist
                aim_dy /= aim_dist
                # Draw semi-transparent cone
                glare_surf = pygame.Surface((render_w, render_h), pygame.SRCALPHA)
                px = render_w // 2
                py = render_h // 2
                # Calculate cone edges
                half_angle = math.acos(glare_cone)
                base_angle = math.atan2(aim_dy, aim_dx)
                left_angle = base_angle + half_angle
                right_angle = base_angle - half_angle
                # Draw cone as polygon
                points = [
                    (px, py),
                    (px + int(math.cos(left_angle) * glare_range), py + int(math.sin(left_angle) * glare_range)),
                    (px + int(aim_dx * glare_range), py + int(aim_dy * glare_range)),
                    (px + int(math.cos(right_angle) * glare_range), py + int(math.sin(right_angle) * glare_range))
                ]
                pygame.draw.polygon(glare_surf, (255, 220, 100, 50), points)
                pygame.draw.polygon(glare_surf, (255, 255, 200, 100), points, 2)
                render_surf.blit(glare_surf, (0, 0))
        
        # Calculate aim angle accounting for zoom
        mx, my = pygame.mouse.get_pos()
        # Convert screen mouse coords to render surface coords
        screen_center_x = self.w // 2
        screen_center_y = self.h // 2
        # Mouse offset from screen center, scaled to render surface
        aim_dx = (mx - screen_center_x) / zoom
        aim_dy = (my - screen_center_y) / zoom
        aim_angle = math.atan2(aim_dy, aim_dx)
        
        self.player.draw(render_surf, center=(render_w // 2, render_h // 2), aim_angle=aim_angle)
        
        # Draw orbiting shields (C-shaped barriers orbiting around player)
        for shield in self.magic_shields:
            sx = int(shield.get("x", self.player.x) - cam[0])
            sy = int(shield.get("y", self.player.y) - cam[1])
            
            # Calculate angle from player to shield (so arc faces OUTWARD)
            # Note: pygame y-axis is flipped, so we negate dy for correct angle
            px = int(self.player.x - cam[0])
            py = int(self.player.y - cam[1])
            angle_outward = math.atan2(-(sy - py), sx - px)  # Negate y for pygame coords
            
            # Draw smooth arc shield facing outward - 3x wider
            arc_size = 45  
            arc_rect = pygame.Rect(sx - arc_size // 2, sy - arc_size // 2, arc_size, arc_size)
            # Arc centered on the outward direction
            start_ang = angle_outward - math.pi * 0.4
            end_ang = angle_outward + math.pi * 0.4
            
            # Draw solid arc
            pygame.draw.arc(render_surf, (100, 180, 255), arc_rect, start_ang, end_ang, 5)
        
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

    def draw_glare_flash_overlay(self):
        """Draw full-screen white flash when glare fires."""
        if self.glare_flash_timer <= 0:
            return
        # Quick white flash that fades
        strength = min(1.0, self.glare_flash_timer / 0.15)
        alpha = int(180 * strength)
        overlay = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        overlay.fill((255, 255, 200, alpha))
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

    def _get_wrapped_lines(self, text, font, max_width):
        """Get list of lines after wrapping text to max_width."""
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            test_surf = font.render(test_line, True, (255, 255, 255))
            if test_surf.get_width() <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        return lines if lines else [""]

    def _draw_wrapped_text(self, text, font, center_x, start_y, max_width, color):
        """Draw text that wraps to multiple lines, centered."""
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            test_surf = font.render(test_line, True, color)
            if test_surf.get_width() <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        
        line_height = font.get_height() + 2
        for i, line in enumerate(lines):
            surf = font.render(line, True, color)
            x = center_x - surf.get_width() // 2
            y = start_y + i * line_height
            self.screen.blit(surf, (x, y))

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
        h = 180  # Taller to fit wrapped text
        gap = 24
        total_w = 3 * w + 2 * gap
        start_x = WIDTH // 2 - total_w // 2
        y = HEIGHT // 2 - h // 2
        mouse_pos = pygame.mouse.get_pos()
        for i, uid in enumerate(self.levelup_options):
            rect = pygame.Rect(start_x + i * (w + gap), y, w, h)
            is_hover = rect.collidepoint(mouse_pos)
            col = COLOR_DARK_GRAY if not is_hover else COLOR_GRAY
            pygame.draw.rect(self.screen, col, rect, border_radius=8)
            
            # Get upgrade info - try new system first, fall back to old
            if uid in UPGRADES_BY_ID:
                upgrade = UPGRADES_BY_ID[uid]
                name = upgrade.name
                desc = upgrade.description
                tier_text = f"T{upgrade.tier}" + (" ★" if upgrade.is_ultimate else "")
            else:
                name = powerup_name(uid)
                desc = powerup_desc(uid)
                tier_text = ""
            
            # Draw tier indicator at top-left corner
            if tier_text:
                tier_col = COLOR_YELLOW if "★" in tier_text else (180, 180, 200)
                t3 = self.font_tiny.render(tier_text, True, tier_col)
                self.screen.blit(t3, (rect.x + 8, rect.y + 8))
            
            # Calculate content height to center vertically
            t1 = self.font_small.render(name, True, COLOR_WHITE)
            name_h = t1.get_height()
            
            # Count description lines for height calculation
            desc_lines = self._get_wrapped_lines(desc, self.font_micro, w - 20)
            desc_line_h = self.font_micro.get_height() + 2
            desc_total_h = len(desc_lines) * desc_line_h
            
            # Total content height = name + gap + description
            content_h = name_h + 12 + desc_total_h
            content_start_y = rect.centery - content_h // 2
            
            # Draw name centered horizontally, positioned vertically
            self.screen.blit(t1, (rect.centerx - t1.get_width() // 2, content_start_y))
            
            # Draw wrapped description below name
            desc_y = content_start_y + name_h + 12
            max_width = w - 20
            self._draw_wrapped_text(desc, self.font_micro, rect.centerx, desc_y, max_width, (200, 200, 200))
        
        # Test mode skip button
        if self.test_mode:
            skip_rect = pygame.Rect(WIDTH // 2 - 80, y + h + 30, 160, 40)
            is_skip_hover = skip_rect.collidepoint(mouse_pos)
            skip_col = COLOR_GRAY if is_skip_hover else COLOR_DARK_GRAY
            pygame.draw.rect(self.screen, skip_col, skip_rect, border_radius=6)
            skip_text = self.font_small.render("SKIP", True, COLOR_WHITE)
            self.screen.blit(skip_text, (skip_rect.centerx - skip_text.get_width() // 2, 
                                          skip_rect.centery - skip_text.get_height() // 2))

    def draw_evolution(self):
        overlay = pygame.Surface((self.w, self.h))
        overlay.set_alpha(220)
        overlay.fill((12, 6, 24))
        self.screen.blit(overlay, (0, 0))
        title = self.font_large.render("ULTIMATE UPGRADE", True, COLOR_YELLOW)
        self.screen.blit(title, (self.w // 2 - title.get_width() // 2, self.h // 4))
        w = 320
        h = 180  # Taller to fit wrapped text
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
            
            # Draw "ULTIMATE" badge at top-left
            badge = self.font_tiny.render("★ ULTIMATE", True, COLOR_YELLOW)
            self.screen.blit(badge, (rect.x + 8, rect.y + 8))
            
            name = evolution_name(eid)
            desc = evolution_desc(eid)
            
            # Calculate content height to center vertically
            t1 = self.font_small.render(name, True, COLOR_WHITE)
            name_h = t1.get_height()
            
            # Count description lines for height calculation
            desc_lines = self._get_wrapped_lines(desc, self.font_micro, w - 20)
            desc_line_h = self.font_micro.get_height() + 2
            desc_total_h = len(desc_lines) * desc_line_h
            
            # Total content height = name + gap + description
            content_h = name_h + 12 + desc_total_h
            content_start_y = rect.centery - content_h // 2
            
            # Draw name centered horizontally, positioned vertically
            self.screen.blit(t1, (rect.centerx - t1.get_width() // 2, content_start_y))
            
            # Draw wrapped description below name
            desc_y = content_start_y + name_h + 12
            max_width = w - 20
            self._draw_wrapped_text(desc, self.font_micro, rect.centerx, desc_y, max_width, (200, 200, 200))

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

    def _test_toggle_rect(self):
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

        # test mode toggle aligned with back button
        test_rect = self._test_toggle_rect()
        toggle_col = COLOR_GREEN if self.test_mode else COLOR_DARK_GRAY
        pygame.draw.rect(self.screen, toggle_col, test_rect, border_radius=6)
        toggle_txt = self.font_small.render("TEST MODE", True, COLOR_WHITE)
        self.screen.blit(toggle_txt, (test_rect.centerx - toggle_txt.get_width() // 2, test_rect.centery - toggle_txt.get_height() // 2))

        self.btn_settings_back.draw(self.screen)
