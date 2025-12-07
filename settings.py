import math

# Window / display
WIDTH, HEIGHT = 1280, 720  # default windowed
FPS = 60

# Display modes
DISPLAY_MODE_WINDOWED = "WINDOWED"
DISPLAY_MODE_FULLSCREEN = "FULLSCREEN"
DISPLAY_MODE_BORDERLESS = "BORDERLESS"

# Colors
COLOR_BG = (5, 5, 15)
COLOR_PLAYER = (120, 190, 255)
COLOR_ENEMY = (235, 70, 70)
COLOR_BULLET = (255, 240, 120)
COLOR_XP = (90, 240, 140)
COLOR_WHITE = (240, 240, 240)
COLOR_GRAY = (110, 110, 140)
COLOR_DARK_GRAY = (35, 35, 60)
COLOR_RED = (255, 80, 80)
COLOR_GREEN = (90, 230, 90)
COLOR_YELLOW = (255, 215, 120)

# Game states
STATE_MENU = "MENU"
STATE_PLAYING = "PLAYING"
STATE_LEVEL_UP = "LEVEL_UP"
STATE_GAME_OVER = "GAME_OVER"

# Player base stats
PLAYER_BASE_SPEED = 5.0
PLAYER_BASE_MAX_HP = 100
PLAYER_BASE_FIRE_RATE = 5.0  # bullets per second
PLAYER_BASE_DAMAGE = 10
PLAYER_BASE_BULLET_SPEED = 11.0

# Enemy base stats
ENEMY_BASE_HP = 30
ENEMY_BASE_SPEED = 2.0
ENEMY_SPAWN_RATE = 1.2  # per second

# XP / leveling
XP_PER_ORB_BASE = 10
XP_PER_LEVEL_BASE = 100
XP_LEVEL_GROWTH = 1.25  # each level needs 25% more
XP_PER_ORB_DECAY = 0.03  # xp per orb reduces as level grows

# Difficulty scaling times (seconds)
SPAWN_RATE_SCALE_INTERVAL = 25
ENEMY_HP_SCALE_INTERVAL = 45
ENEMY_SPEED_SCALE_INTERVAL = 60

# Endless: no target time, death only.
# World / map
WORLD_SIZE = 20000  # virtual map is WORLD_SIZE x WORLD_SIZE
PLAYER_RADIUS = 18
ENEMY_RADIUS = 16
BULLET_RADIUS = 5
XP_RADIUS = 8

KNOCKBACK_FORCE = 40.0
SCREEN_SHAKE_DECAY = 3.0  # per second
PARTICLE_LIFETIME = 0.4

# Utility
def clamp(value, mn, mx):
    return max(mn, min(mx, value))

def distance_sq(a, b):
    dx = a[0] - b[0]
    dy = a[1] - b[1]
    return dx * dx + dy * dy

def circle_collision(x1, y1, r1, x2, y2, r2):
    return distance_sq((x1, y1), (x2, y2)) <= (r1 + r2) ** 2

def vec_from_angle(angle):
    return math.cos(angle), math.sin(angle)

# Audio defaults
MASTER_VOLUME_DEFAULT = 0.8
MUSIC_VOLUME_DEFAULT = 0.5
SFX_VOLUME_DEFAULT = 0.8
