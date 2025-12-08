"""
Game Spawning Module - Handles enemy spawning and progression
==============================================================
Extracted from game.py to reduce file size and improve organization.
"""

import math
import random
from typing import TYPE_CHECKING

from game_constants import (
    WORLD_SIZE, ENEMY_BASE_HP, ENEMY_BASE_SPEED, ENEMY_SPAWN_RATE,
    clamp
)
from game_entities import Enemy

if TYPE_CHECKING:
    from game import Game


class SpawnManager:
    """Manages enemy spawning and difficulty progression."""
    
    def __init__(self, game: 'Game'):
        self.game = game
        self.spawn_timer = 0.0
        self.enemy_spawn_rate = ENEMY_SPAWN_RATE
        self.bosses_spawned = 0
        
        # Wave-based spawning (optional enhancement)
        self.wave_number = 0
        self.enemies_in_wave = 0
        self.wave_active = False
        
        # Elite spawning
        self.elite_spawn_chance = 0.0
    
    @property
    def player(self):
        return self.game.player
    
    @property
    def enemies(self):
        return self.game.enemies
    
    @property
    def elapsed_time(self):
        return self.game.elapsed_time
    
    def update(self, dt: float):
        """Update spawning logic."""
        self.spawn_timer += dt
        
        # Scale spawn rate every 30s
        self.enemy_spawn_rate = ENEMY_SPAWN_RATE + 0.25 * int(self.elapsed_time // 30)
        
        # Elite spawn chance increases over time
        self.elite_spawn_chance = min(0.15, self.elapsed_time / 600)  # Max 15% at 10 min
        
        interval = 1.0 / self.enemy_spawn_rate
        while self.spawn_timer >= interval:
            self.spawn_timer -= interval
            self.spawn_enemy()
    
    def spawn_enemy(self):
        """Spawn a single enemy."""
        half = WORLD_SIZE / 2
        dmin, dmax = 600, 900
        ang = random.uniform(0, math.tau)
        r = random.uniform(dmin, dmax)
        x = self.player.x + math.cos(ang) * r
        y = self.player.y + math.sin(ang) * r
        x = clamp(x, -half, half)
        y = clamp(y, -half, half)
        
        # Choose enemy type based on elapsed time
        t = self.elapsed_time
        hp_scale = 1.0 + (t / 90.0)
        speed_scale = 1.0 + (t / 180.0)
        
        # Timed boss every minute
        if int(t // 60) > self.bosses_spawned:
            self.bosses_spawned += 1
            kind = "boss"
            boss_stage = self.bosses_spawned
        else:
            kind, boss_stage = self._choose_enemy_type(t)
        
        # Check for elite variant
        is_elite = random.random() < self.elite_spawn_chance and kind not in ("boss",)
        
        hp, speed = self._get_enemy_stats(kind, boss_stage, hp_scale, speed_scale)
        
        if is_elite:
            hp = int(hp * 2.5)
            speed *= 1.15
            kind = f"elite_{kind}"
        
        enemy = Enemy(x, y, hp, speed, kind, boss_stage=boss_stage)
        enemy.max_hp = hp  # Track max HP for percentage calculations
        self.game.enemies.append(enemy)
    
    def _choose_enemy_type(self, t: float) -> tuple:
        """Choose enemy type based on elapsed time."""
        pool = ["normal", "fast", "tank"]
        weights = [0.45, 0.25, 0.2]
        
        if t >= 180:  # 3 minutes
            pool.append("shooter")
            weights.append(0.15)
        
        if t > 90:  # 1.5 minutes
            pool.append("sprinter")
            weights.append(0.15)
        
        if t > 120:  # 2 minutes
            pool.append("bruiser")
            weights.append(0.2)
        
        if t > 300:  # 5 minutes
            pool.append("charger")
            weights.append(0.1)
        
        if t > 420:  # 7 minutes
            pool.append("summoner")
            weights.append(0.08)
        
        kind = random.choices(pool, weights=weights, k=1)[0]
        return kind, 0
    
    def _get_enemy_stats(self, kind: str, boss_stage: int, hp_scale: float, speed_scale: float) -> tuple:
        """Get HP and speed for an enemy type."""
        # Remove elite prefix for stat lookup
        base_kind = kind.replace("elite_", "")
        
        if base_kind == "tank":
            hp = int(ENEMY_BASE_HP * 3 * hp_scale)
            speed = ENEMY_BASE_SPEED * 0.7 * speed_scale
        elif base_kind == "fast":
            hp = int(ENEMY_BASE_HP * 0.7 * hp_scale)
            speed = ENEMY_BASE_SPEED * 1.8 * speed_scale
        elif base_kind == "sprinter":
            hp = int(ENEMY_BASE_HP * 0.8 * hp_scale)
            speed = ENEMY_BASE_SPEED * 2.4 * speed_scale
        elif base_kind == "bruiser":
            hp = int(ENEMY_BASE_HP * 4.0 * hp_scale)
            speed = ENEMY_BASE_SPEED * 0.9 * speed_scale
        elif base_kind == "shooter":
            hp = int(ENEMY_BASE_HP * 1.4 * hp_scale)
            speed = ENEMY_BASE_SPEED * 1.0 * speed_scale
        elif base_kind == "charger":
            hp = int(ENEMY_BASE_HP * 2.0 * hp_scale)
            speed = ENEMY_BASE_SPEED * 1.5 * speed_scale
        elif base_kind == "summoner":
            hp = int(ENEMY_BASE_HP * 2.5 * hp_scale)
            speed = ENEMY_BASE_SPEED * 0.6 * speed_scale
        elif base_kind == "boss":
            if boss_stage == 1:
                hp = int(ENEMY_BASE_HP * 14 * hp_scale)
                speed = ENEMY_BASE_SPEED * 1.2 * speed_scale
            elif boss_stage == 2:
                hp = int(ENEMY_BASE_HP * 18 * hp_scale)
                speed = ENEMY_BASE_SPEED * 1.45 * speed_scale
            else:
                hp = int(ENEMY_BASE_HP * 24 * hp_scale)
                speed = ENEMY_BASE_SPEED * 1.6 * speed_scale
        else:  # normal
            hp = int(ENEMY_BASE_HP * 1.0 * hp_scale)
            speed = ENEMY_BASE_SPEED * 1.0 * speed_scale
        
        return hp, speed
    
    def spawn_minion(self, x: float, y: float, parent_kind: str = "summoner"):
        """Spawn a minion enemy (from summoner enemies)."""
        hp = int(ENEMY_BASE_HP * 0.3)
        speed = ENEMY_BASE_SPEED * 1.2
        
        enemy = Enemy(x, y, hp, speed, "minion", boss_stage=0)
        enemy.max_hp = hp
        self.game.enemies.append(enemy)
    
    def spawn_wave(self, enemy_count: int, enemy_type: str = None):
        """Spawn a wave of enemies."""
        self.wave_number += 1
        self.wave_active = True
        self.enemies_in_wave = enemy_count
        
        for _ in range(enemy_count):
            # Spawn in a ring around player
            ang = random.uniform(0, math.tau)
            r = random.uniform(700, 1000)
            x = self.player.x + math.cos(ang) * r
            y = self.player.y + math.sin(ang) * r
            
            half = WORLD_SIZE / 2
            x = clamp(x, -half, half)
            y = clamp(y, -half, half)
            
            kind = enemy_type or "normal"
            t = self.elapsed_time
            hp_scale = 1.0 + (t / 90.0)
            speed_scale = 1.0 + (t / 180.0)
            
            hp, speed = self._get_enemy_stats(kind, 0, hp_scale, speed_scale)
            enemy = Enemy(x, y, hp, speed, kind)
            enemy.max_hp = hp
            self.game.enemies.append(enemy)
    
    def update_enemy_separation(self):
        """Prevent enemies from stacking on each other."""
        if len(self.enemies) <= 1:
            return
        
        for _ in range(2):  # Relaxation passes
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
                        
                        # Bosses resist being pushed
                        wi, wj = 0.5, 0.5
                        if getattr(ei, "kind", "") == "boss" and getattr(ej, "kind", "") != "boss":
                            wi, wj = 0.2, 0.8
                        elif getattr(ej, "kind", "") == "boss" and getattr(ei, "kind", "") != "boss":
                            wi, wj = 0.8, 0.2
                        
                        push = overlap * 0.5
                        ei.x -= nx * push * wi
                        ei.y -= ny * push * wi
                        ej.x += nx * push * wj
                        ej.y += ny * push * wj
    
    def update_enemies(self, dt: float):
        """Update all enemies."""
        for e in self.enemies:
            e.update(dt, (self.player.x, self.player.y))
        
        # Handle special enemy behaviors
        for en in self.enemies:
            # Shooter enemies
            can_shoot = (
                getattr(en, "kind", "") in ("shooter", "elite_shooter") or
                (getattr(en, "kind", "") == "boss" and getattr(en, "boss_stage", 0) >= 3)
            )
            
            if can_shoot:
                self._update_shooter(en, dt)
            
            # Charger behavior
            if "charger" in getattr(en, "kind", ""):
                self._update_charger(en, dt)
            
            # Summoner behavior
            if "summoner" in getattr(en, "kind", ""):
                self._update_summoner(en, dt)
    
    def _update_shooter(self, en, dt: float):
        """Update shooter enemy behavior."""
        from game_constants import FPS
        
        if not hasattr(en, "shoot_cd"):
            en.shoot_cd = random.uniform(1.0, 2.4)
        
        en.shoot_cd -= dt
        if en.shoot_cd <= 0:
            is_boss = en.kind == "boss"
            en.shoot_cd = random.uniform(0.6, 1.2) if is_boss else random.uniform(1.0, 2.0)
            
            dx = self.player.x - en.x
            dy = self.player.y - en.y
            l = math.hypot(dx, dy) or 1
            speed = 12.0 if is_boss else 5.0
            
            self.game.enemy_bullets.append({
                "x": en.x,
                "y": en.y,
                "vx": dx / l * speed,
                "vy": dy / l * speed,
                "r": 6 if is_boss else 4,
                "dmg": 1
            })
    
    def _update_charger(self, en, dt: float):
        """Update charger enemy behavior (charges at player)."""
        if not hasattr(en, "charge_cd"):
            en.charge_cd = random.uniform(3.0, 5.0)
            en.charging = False
            en.charge_duration = 0.0
        
        if en.charging:
            en.charge_duration -= dt
            if en.charge_duration <= 0:
                en.charging = False
                en.speed = ENEMY_BASE_SPEED * 1.5
        else:
            en.charge_cd -= dt
            if en.charge_cd <= 0:
                # Start charge
                en.charging = True
                en.charge_duration = 0.8
                en.speed = ENEMY_BASE_SPEED * 4.0
                en.charge_cd = random.uniform(3.0, 5.0)
    
    def _update_summoner(self, en, dt: float):
        """Update summoner enemy behavior (spawns minions)."""
        if not hasattr(en, "summon_cd"):
            en.summon_cd = random.uniform(4.0, 6.0)
        
        en.summon_cd -= dt
        if en.summon_cd <= 0:
            en.summon_cd = random.uniform(4.0, 6.0)
            
            # Spawn 2-3 minions around the summoner
            count = random.randint(2, 3)
            for _ in range(count):
                ang = random.uniform(0, math.tau)
                r = random.uniform(30, 50)
                x = en.x + math.cos(ang) * r
                y = en.y + math.sin(ang) * r
                self.spawn_minion(x, y)
    
    def get_difficulty_info(self) -> dict:
        """Get current difficulty information."""
        t = self.elapsed_time
        return {
            "time": t,
            "spawn_rate": self.enemy_spawn_rate,
            "hp_scale": 1.0 + (t / 90.0),
            "speed_scale": 1.0 + (t / 180.0),
            "bosses_spawned": self.bosses_spawned,
            "elite_chance": self.elite_spawn_chance,
            "enemy_count": len(self.enemies),
        }
