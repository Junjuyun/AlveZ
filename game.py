import math
import random
import sys
import pygame
from settings import (
    WIDTH, HEIGHT, FPS, WORLD_SIZE,
    COLOR_BG, COLOR_WHITE, COLOR_GRAY, COLOR_DARK_GRAY,
    COLOR_RED, COLOR_GREEN, COLOR_YELLOW,
    SCREEN_SHAKE_DECAY,
    STATE_MENU, STATE_PLAYING, STATE_LEVEL_UP, STATE_GAME_OVER,
    ENEMY_SPAWN_RATE, ENEMY_BASE_HP, ENEMY_BASE_SPEED,
    SPAWN_RATE_SCALE_INTERVAL, ENEMY_HP_SCALE_INTERVAL, ENEMY_SPEED_SCALE_INTERVAL,
    clamp, circle_collision,
)
from entities import Player, Enemy, ExperienceOrb, Particle
from entities import Bullet  # for type reference
from powerups import POWER_UP_IDS, apply_power_up, get_power_up_name, get_power_up_desc
from ui import Button

class Game:
    def __init__(self):
        pygame.init()
        # fullscreen 1920x1080
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
        pygame.display.set_caption("Starlight Eclipse")
        self.clock = pygame.time.Clock()

        # Fonts
        self.font_large = pygame.font.SysFont("consolas", 64)
        self.font_medium = pygame.font.SysFont("consolas", 32)
        self.font_small = pygame.font.SysFont("consolas", 20)

        # State
        self.state = STATE_MENU

        # Menu buttons
        self.btn_start = Button(
            (WIDTH // 2 - 150, HEIGHT // 2, 300, 60),
            "START",
            self.font_medium,
            COLOR_DARK_GRAY,
            COLOR_GRAY,
        )
        self.btn_quit = Button(
            (WIDTH // 2 - 150, HEIGHT // 2 + 80, 300, 60),
            "QUIT",
            self.font_medium,
            COLOR_DARK_GRAY,
            COLOR_GRAY,
        )

        # Game over buttons
        self.btn_restart = Button(
            (WIDTH // 2 - 150, HEIGHT // 2 + 40, 300, 60),
            "RESTART",
            self.font_medium,
            COLOR_DARK_GRAY,
            COLOR_GRAY,
        )
        self.btn_main_menu = Button(
            (WIDTH // 2 - 150, HEIGHT // 2 + 120, 300, 60),
            "MAIN MENU",
            self.font_medium,
            COLOR_DARK_GRAY,
            COLOR_GRAY,
        )

        # background starfield
        self.stars = [
            (random.uniform(-WORLD_SIZE / 2, WORLD_SIZE / 2),
             random.uniform(-WORLD_SIZE / 2, WORLD_SIZE / 2),
             random.randint(1, 3))
            for _ in range(1200)
        ]

        self.reset_game()

    def reset_game(self):
        self.player = Player(0, 0)
        self.bullets = []
        self.enemies = []
        self.orbs = []
        self.particles = []

        self.elapsed_time = 0.0
        self.spawn_timer = 0.0
        self.enemy_spawn_rate = ENEMY_SPAWN_RATE
        self.enemy_hp = ENEMY_BASE_HP
        self.enemy_speed = ENEMY_BASE_SPEED

        self.kills = 0
        self.screen_shake = 0.0
        self.level_up_options = []

        # Difficulty scaling timers
        self.spawn_scale_time = 0.0
        self.hp_scale_time = 0.0
        self.speed_scale_time = 0.0

    # =========
    # RUN LOOP
    # =========
    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                self.handle_event(event)

            self.update(dt)
            self.draw()

        pygame.quit()
        sys.exit()

    # =========
    # EVENTS
    # =========
    def handle_event(self, event):
        if self.state == STATE_MENU:
            self.handle_event_menu(event)
        elif self.state == STATE_PLAYING:
            self.handle_event_playing(event)
        elif self.state == STATE_LEVEL_UP:
            self.handle_event_level_up(event)
        elif self.state == STATE_GAME_OVER:
            self.handle_event_game_over(event)

    def handle_event_menu(self, event):
        if self.btn_start.is_clicked(event):
            self.reset_game()
            self.state = STATE_PLAYING
        elif self.btn_quit.is_clicked(event):
            pygame.event.post(pygame.event.Event(pygame.QUIT))

    def handle_event_playing(self, event):
        # shooting is handled in update via mouse held; nothing special here
        pass

    def handle_event_level_up(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            w = 260
            h = 120
            gap = 20
            total_w = 3 * w + 2 * gap
            start_x = WIDTH // 2 - total_w // 2
            y = HEIGHT // 2 - h // 2
            for i, p_id in enumerate(self.level_up_options):
                rect = pygame.Rect(start_x + i * (w + gap), y, w, h)
                if rect.collidepoint(mx, my):
                    apply_power_up(self.player, p_id)
                    self.state = STATE_PLAYING
                    break

    def handle_event_game_over(self, event):
        if self.btn_restart.is_clicked(event):
            self.reset_game()
            self.state = STATE_PLAYING
        elif self.btn_main_menu.is_clicked(event):
            self.state = STATE_MENU

    # =========
    # UPDATE
    # =========
    def update(self, dt):
        if self.state == STATE_MENU:
            return
        elif self.state == STATE_PLAYING:
            self.update_playing(dt)
        elif self.state == STATE_LEVEL_UP:
            for p in self.particles:
                p.update(dt)
            self.particles = [p for p in self.particles if p.alive()]
        elif self.state == STATE_GAME_OVER:
            for p in self.particles:
                p.update(dt)
            self.particles = [p for p in self.particles if p.alive()]

    def update_playing(self, dt):
        self.elapsed_time += dt

        keys = pygame.key.get_pressed()
        self.player.update(dt, keys)

        # camera follows player (player is always drawn at center)
        camera_offset = (self.player.x - WIDTH // 2, self.player.y - HEIGHT // 2)

        # shooting
        mouse_pressed = pygame.mouse.get_pressed()[0]
        if mouse_pressed and self.player.can_shoot():
            mx, my = pygame.mouse.get_pos()
            world_target = (camera_offset[0] + mx, camera_offset[1] + my)
            new_bullets = self.player.shoot(world_target)
            self.bullets.extend(new_bullets)

        # bullets
        for b in self.bullets:
            b.update(dt)
        self.bullets = [b for b in self.bullets if not b.offscreen(camera_offset)]

        # difficulty scaling
        self.spawn_scale_time += dt
        self.hp_scale_time += dt
        self.speed_scale_time += dt

        if self.spawn_scale_time >= SPAWN_RATE_SCALE_INTERVAL:
            self.spawn_scale_time -= SPAWN_RATE_SCALE_INTERVAL
            self.enemy_spawn_rate *= 1.2

        if self.hp_scale_time >= ENEMY_HP_SCALE_INTERVAL:
            self.hp_scale_time -= ENEMY_HP_SCALE_INTERVAL
            self.enemy_hp += 10

        if self.speed_scale_time >= ENEMY_SPEED_SCALE_INTERVAL:
            self.speed_scale_time -= ENEMY_SPEED_SCALE_INTERVAL
            self.enemy_speed += 0.4

        # enemy spawning
        self.spawn_timer += dt
        spawn_interval = 1.0 / self.enemy_spawn_rate
        while self.spawn_timer >= spawn_interval:
            self.spawn_timer -= spawn_interval
            self.spawn_enemy()

        # enemies
        for e in self.enemies:
            e.update(dt, (self.player.x, self.player.y))

        # orbs
        for o in self.orbs:
            o.update(dt, (self.player.x, self.player.y))

        # particles
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.alive()]

        # collisions: bullets vs enemies
        for b in list(self.bullets):
            for e in list(self.enemies):
                if circle_collision(b.x, b.y, b.radius, e.x, e.y, e.radius):
                    e.hp -= b.damage
                    if b.piercing and b.pierce_left > 0:
                        b.pierce_left -= 1
                    else:
                        if b in self.bullets:
                            self.bullets.remove(b)
                    if e.hp <= 0:
                        self.kills += 1
                        self.player.kills += 1
                        # xp orbs use player's current orb xp value
                        self.orbs.append(ExperienceOrb(e.x, e.y, self.player.orb_xp_value))
                        for _ in range(8):
                            self.particles.append(
                                Particle(e.x, e.y, COLOR_RED, 6)
                            )
                        if e in self.enemies:
                            self.enemies.remove(e)
                    break

        # collisions: player vs enemies
        for e in list(self.enemies):
            if circle_collision(
                self.player.x, self.player.y, self.player.radius,
                e.x, e.y, e.radius,
            ):
                self.player.take_damage(10)
                self.screen_shake = 10.0
                e.knockback((self.player.x, self.player.y), 40.0)
                if self.player.hp <= 0:
                    self.state = STATE_GAME_OVER

        # collisions: player vs xp orbs
        for o in list(self.orbs):
            if circle_collision(
                self.player.x, self.player.y, self.player.radius,
                o.x, o.y, o.radius,
            ):
                leveled = self.player.add_xp(o.xp)
                self.orbs.remove(o)
                if leveled:
                    self.roll_level_up()

        # screen shake decay
        if self.screen_shake > 0:
            self.screen_shake -= SCREEN_SHAKE_DECAY * dt * FPS
            if self.screen_shake < 0:
                self.screen_shake = 0

    def spawn_enemy(self):
        half = WORLD_SIZE / 2
        # spawn around player, but outside screen
        dist_min = 600
        dist_max = 900
        angle = random.uniform(0, 6.28318)
        r = random.uniform(dist_min, dist_max)
        x = self.player.x + r * math.cos(angle)
        y = self.player.y + r * math.sin(angle)
        x = clamp(x, -half, half)
        y = clamp(y, -half, half)
        e = Enemy(x, y, self.enemy_hp, self.enemy_speed)
        self.enemies.append(e)

    def roll_level_up(self):
        self.level_up_options = random.sample(POWER_UP_IDS, k=3)
        self.state = STATE_LEVEL_UP
        for _ in range(24):
            self.particles.append(
                Particle(self.player.x, self.player.y, COLOR_YELLOW, 6)
            )

    # =========
    # DRAW
    # =========
    def draw(self):
        self.screen.fill(COLOR_BG)

        if self.state == STATE_MENU:
            self.draw_menu()
        elif self.state in (STATE_PLAYING, STATE_LEVEL_UP, STATE_GAME_OVER):
            self.draw_game_world()
            self.draw_hud()
            if self.state == STATE_LEVEL_UP:
                self.draw_level_up_screen()
            if self.state == STATE_GAME_OVER:
                self.draw_game_over()

        pygame.display.flip()

    def get_camera_offset(self):
        # camera centers on player
        return (self.player.x - WIDTH // 2, self.player.y - HEIGHT // 2)

    def get_shake_offset(self):
        if self.screen_shake <= 0:
            return (0, 0)
        mag = self.screen_shake
        return (
            random.uniform(-mag, mag),
            random.uniform(-mag, mag),
        )

    def draw_background(self, camera_offset, shake):
        # simple starfield: draw stars relative to camera
        ox = camera_offset[0] + shake[0]
        oy = camera_offset[1] + shake[1]
        for sx, sy, r in self.stars:
            x = int(sx - ox)
            y = int(sy - oy)
            if -5 <= x <= WIDTH + 5 and -5 <= y <= HEIGHT + 5:
                pygame.draw.rect(self.screen, (15, 15, 35), (x, y, r, r))

    def draw_game_world(self):
        camera_offset = self.get_camera_offset()
        shake = self.get_shake_offset()
        combined_offset = (camera_offset[0] - shake[0], camera_offset[1] - shake[1])

        self.draw_background(camera_offset, shake)

        mouse_pos = pygame.mouse.get_pos()

        for o in self.orbs:
            o.draw(self.screen, combined_offset)

        for e in self.enemies:
            e.draw(self.screen, combined_offset)

        for b in self.bullets:
            b.draw(self.screen, combined_offset)

        self.player.draw(self.screen, combined_offset, mouse_pos)

        for p in self.particles:
            p.draw(self.screen, combined_offset)

    def draw_hud(self):
        # HP bar
        bar_w = 280
        bar_h = 22
        x = 20
        y = 20
        pygame.draw.rect(
            self.screen, COLOR_DARK_GRAY, (x, y, bar_w, bar_h), border_radius=4
        )
        hp_ratio = self.player.hp / self.player.max_hp
        pygame.draw.rect(
            self.screen,
            COLOR_RED,
            (x, y, int(bar_w * hp_ratio), bar_h),
            border_radius=4,
        )
        hp_text = self.font_small.render(
            f"HP: {int(self.player.hp)}/{self.player.max_hp}", True, COLOR_WHITE
        )
        self.screen.blit(hp_text, (x + 5, y - 18))

        # Level
        lvl_text = self.font_small.render(
            f"LVL: {self.player.level}", True, COLOR_WHITE
        )
        self.screen.blit(lvl_text, (x, y + bar_h + 8))

        # Time (top-center, endless)
        t = int(self.elapsed_time)
        m = t // 60
        s = t % 60
        timer_text = self.font_small.render(
            f"Survived: {m:02d}:{s:02d}", True, COLOR_WHITE
        )
        self.screen.blit(
            timer_text,
            (WIDTH // 2 - timer_text.get_width() // 2, 10),
        )

        # Kills (top-right)
        kills_text = self.font_small.render(
            f"Kills: {self.kills}", True, COLOR_WHITE
        )
        self.screen.blit(
            kills_text,
            (WIDTH - kills_text.get_width() - 20, 20),
        )

        # XP bar (bottom)
        bar_w = WIDTH - 260
        bar_h = 18
        x = 130
        y = HEIGHT - 40
        pygame.draw.rect(
            self.screen, COLOR_DARK_GRAY, (x, y, bar_w, bar_h), border_radius=4
        )
        xp_ratio = self.player.xp / max(1, self.player.xp_to_level)
        pygame.draw.rect(
            self.screen,
            COLOR_GREEN,
            (x, y, int(bar_w * xp_ratio), bar_h),
            border_radius=4,
        )
        xp_text = self.font_small.render(
            f"XP: {self.player.xp}/{self.player.xp_to_level}", True, COLOR_WHITE
        )
        self.screen.blit(
            xp_text,
            (x + bar_w // 2 - xp_text.get_width() // 2, y - 18),
        )

    def draw_menu(self):
        title = self.font_large.render("Starlight Eclipse", True, COLOR_WHITE)
        self.screen.blit(
            title,
            (WIDTH // 2 - title.get_width() // 2, HEIGHT // 3 - 40),
        )

        # removed old subtitle ("Python / Pygame Survivor Shooter")

        self.btn_start.draw(self.screen)
        self.btn_quit.draw(self.screen)

    def draw_level_up_screen(self):
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        title = self.font_large.render("LEVEL UP!", True, COLOR_YELLOW)
        self.screen.blit(
            title,
            (WIDTH // 2 - title.get_width() // 2, HEIGHT // 4),
        )

        w = 260
        h = 120
        gap = 20
        total_w = 3 * w + 2 * gap
        start_x = WIDTH // 2 - total_w // 2
        y = HEIGHT // 2 - h // 2

        mouse_pos = pygame.mouse.get_pos()

        for i, p_id in enumerate(self.level_up_options):
            rect = pygame.Rect(start_x + i * (w + gap), y, w, h)
            is_hover = rect.collidepoint(mouse_pos)
            color = COLOR_DARK_GRAY if not is_hover else COLOR_GRAY
            pygame.draw.rect(self.screen, color, rect, border_radius=8)
            name = get_power_up_name(p_id)
            desc = get_power_up_desc(p_id)
            t1 = self.font_small.render(name, True, COLOR_WHITE)
            t2 = self.font_small.render(desc, True, COLOR_WHITE)
            self.screen.blit(
                t1,
                (rect.centerx - t1.get_width() // 2, rect.y + 15),
            )
            self.screen.blit(
                t2,
                (rect.centerx - t2.get_width() // 2, rect.y + 50),
            )

    def draw_game_over(self):
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        text = "GAME OVER"
        color = COLOR_RED
        title = self.font_large.render(text, True, color)
        self.screen.blit(
            title,
            (WIDTH // 2 - title.get_width() // 2, HEIGHT // 4),
        )

        t = int(self.elapsed_time)
        m = t // 60
        s = t % 60
        stats = [
            f"Survival Time: {m:02d}:{s:02d}",
            f"Kills: {self.kills}",
            f"Level Reached: {self.player.level}",
        ]
        for i, line in enumerate(stats):
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
