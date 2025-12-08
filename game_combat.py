"""
Game Combat Module - Handles all combat-related logic
======================================================
Extracted from game.py to reduce file size and improve organization.
"""

import math
import random
from typing import List, Tuple, Optional, TYPE_CHECKING

from game_constants import (
    FPS, WORLD_SIZE, XP_PER_ORB, COLOR_YELLOW,
    circle_collision, clamp
)
from game_entities import Bullet, XPOrb, GasPickup, EvolutionPickup

if TYPE_CHECKING:
    from game import Game


class CombatManager:
    """Manages all combat-related logic for the game."""
    
    def __init__(self, game: 'Game'):
        self.game = game
    
    @property
    def player(self):
        return self.game.player
    
    @property
    def enemies(self):
        return self.game.enemies
    
    @property
    def bullets(self):
        return self.game.bullets
    
    def update_bullets(self, dt: float, cam: Tuple[float, float]):
        """Update all player bullets."""
        for b in self.bullets:
            b.update(dt)
        
        # Remove offscreen bullets
        self.game.bullets = [b for b in self.bullets if not b.offscreen(cam)]
    
    def update_enemy_bullets(self, dt: float):
        """Update and handle enemy bullet collisions."""
        for eb in list(self.game.enemy_bullets):
            eb["x"] += eb["vx"] * dt * FPS
            eb["y"] += eb["vy"] * dt * FPS
            
            # Check collision with player
            if circle_collision(
                self.player.x, self.player.y, self.player.radius,
                eb["x"], eb["y"], eb["r"]
            ):
                # Check dodge
                upgrade_mgr = getattr(self.player, "upgrade_manager", None)
                if upgrade_mgr and upgrade_mgr.check_dodge():
                    # Dodged - remove bullet but no damage
                    pass
                elif self.player.invuln <= 0:
                    self.player.take_damage(1)
                    self.player.hit_flash = 0.2
                    if upgrade_mgr:
                        upgrade_mgr.on_hit()
                
                if eb in self.game.enemy_bullets:
                    self.game.enemy_bullets.remove(eb)
                continue
            
            # Remove far bullets
            if abs(eb["x"] - self.player.x) > 2000 or abs(eb["y"] - self.player.y) > 2000:
                self.game.enemy_bullets.remove(eb)
    
    def update_guided_shots(self):
        """Update homing behavior for guided shots."""
        if not self.player.guided_shots or not self.enemies:
            return
        
        for b in self.bullets:
            if getattr(b, "guidance_disabled", False):
                continue
            
            if not getattr(b, "target", None) or b.target not in self.enemies:
                if not self.enemies:
                    break
                b.target = min(
                    self.enemies,
                    key=lambda en: (en.x - b.x) ** 2 + (en.y - b.y) ** 2
                )
            
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
    
    def process_bullet_enemy_collisions(self):
        """Handle collisions between player bullets and enemies."""
        from audio import audio
        
        for b in list(self.bullets):
            for en in list(self.enemies):
                # Skip if recently hit by this bullet
                if en.hit_sources.get(getattr(b, "uid", None), 0.0) > 0:
                    continue
                
                if not circle_collision(b.x, b.y, b.radius, en.x, en.y, en.radius):
                    continue
                
                # Mark hit
                if hasattr(b, "uid"):
                    en.hit_sources[b.uid] = 0.22
                
                b.guidance_disabled = True
                b.target = None
                
                # Calculate damage
                upgrade_mgr = getattr(self.player, "upgrade_manager", None)
                damage_mult = upgrade_mgr.get_current_damage_mult() if upgrade_mgr else 1.0
                base_damage = int(b.damage * damage_mult)
                
                extra_damage = 0
                status_color = COLOR_YELLOW
                
                # Apply base damage
                en.hp -= base_damage
                en.flash_timer = 0.15
                
                # Knockback
                dx = en.x - b.x
                dy = en.y - b.y
                l = math.hypot(dx, dy) or 1
                knockback_mult = getattr(self.player, "knockback_mult", 1.0)
                push = 12 * knockback_mult
                if getattr(en, "kind", "") == "boss":
                    push *= 0.25
                en.x += dx / l * push
                en.y += dy / l * push
                
                if getattr(en, "kind", "") != "boss":
                    en.knockback_pause = 0.2
                    en.knockback_slow = 0.2
                
                # Status effects
                self._apply_bullet_status_effects(b, en, extra_damage, status_color)
                
                # Check execute
                if upgrade_mgr:
                    max_hp = getattr(en, "max_hp", en.hp + base_damage)
                    hp_ratio = en.hp / max(1, max_hp)
                    if upgrade_mgr.check_execute(hp_ratio):
                        en.hp = 0
                
                # Damage text
                total_damage = base_damage + extra_damage
                self.game.damage_texts.append({
                    "x": en.x + random.uniform(-6, 6),
                    "y": en.y - 10,
                    "val": total_damage,
                    "life": 0.6,
                    "color": status_color
                })
                
                killed = en.hp <= 0
                
                # Handle bullet piercing
                self._handle_bullet_pierce(b, killed)
                
                # Handle enemy death
                if killed:
                    self._handle_enemy_death(en, enemy_was_cursed=en.curse_timer > 0 if hasattr(en, "curse_timer") else False)
                    audio.play_sfx(audio.snd_enemy_death)
                
                break
    
    def _apply_bullet_status_effects(self, b: Bullet, en, extra_damage: int, status_color: Tuple):
        """Apply status effects from bullet to enemy."""
        p = self.player
        
        # Ice
        if b.status.get("ice"):
            if en.ice_timer > 0:
                extra_damage += p.ice_bonus_damage
                status_color = (150, 200, 255)
            
            # Check freeze chance
            freeze_chance = getattr(p, "freeze_chance", 0)
            if freeze_chance > 0 and random.random() < freeze_chance:
                is_boss = getattr(en, "kind", "") == "boss"
                duration = getattr(p, "freeze_boss_duration", 0.3) if is_boss else getattr(p, "freeze_duration", 1.5)
                en.frozen_timer = max(getattr(en, "frozen_timer", 0), duration)
            
            en.ice_timer = max(en.ice_timer, 2.0)
            en.ice_dps = max(en.ice_dps, p.ice_bonus_damage * 0.8)
            self.game._spawn_status_fx(en.x, en.y, kind="ice")
        
        # Burn
        if b.status.get("burn"):
            status_color = (255, 120, 90)
            if en.burn_timer > 0 and p.burn_sear_bonus > 0:
                extra_damage += int(b.damage * p.burn_sear_bonus)
            
            en.burn_timer = max(en.burn_timer, 3.0)
            base_burn = getattr(p, "base_burn_dps", 0)
            burn_dps = max(base_burn, p.damage * 0.26 * p.burn_bonus_mult)
            en.burn_dps = max(en.burn_dps, burn_dps)
            self.game._spawn_status_fx(en.x, en.y, kind="fire")
        
        # Poison
        if b.status.get("poison"):
            status_color = (180, 130, 255)
            if en.poison_timer > 0:
                extra_damage += int(b.damage * 0.2 * p.poison_bonus_mult)
            
            en.poison_timer = max(en.poison_timer, 5.0)
            en.poison_dps = max(en.poison_dps, p.damage * 0.22 * p.poison_bonus_mult)
            self.game._spawn_status_fx(en.x, en.y, kind="poison")
        
        # Curse
        curse_chance = getattr(p, "curse_chance", 0)
        if curse_chance > 0 and random.random() < curse_chance:
            if not hasattr(en, "curse_timer"):
                en.curse_timer = 0
                en.curse_damage = 0
            
            delay = getattr(p, "curse_delay", 0.75)
            curse_mult = getattr(p, "curse_damage_mult", 2.0)
            bonus = getattr(p, "curse_bonus_damage", 0)
            
            en.curse_timer = delay
            en.curse_damage = int(b.damage * curse_mult + b.damage * bonus)
            
            # Curse vulnerability
            if getattr(en, "cursed", False) and getattr(p, "curse_vulnerability", 0) > 0:
                extra_damage += int(b.damage * p.curse_vulnerability)
            
            en.cursed = True
        
        if extra_damage > 0:
            en.hp -= extra_damage
    
    def _handle_bullet_pierce(self, b: Bullet, killed: bool):
        """Handle bullet piercing logic."""
        if b.piercing:
            if b.pierce_on_kill:
                if killed:
                    b.pierce_left -= 1
                    if b.pierce_left < 0 and b in self.bullets:
                        self.game.bullets.remove(b)
                else:
                    if b in self.bullets:
                        self.game.bullets.remove(b)
            else:
                if b.pierce_left > 0:
                    b.pierce_left -= 1
                else:
                    if b in self.bullets:
                        self.game.bullets.remove(b)
        else:
            if b in self.bullets:
                self.game.bullets.remove(b)
    
    def _handle_enemy_death(self, en, enemy_was_cursed: bool = False, enemy_was_frozen: bool = False):
        """Handle enemy death - drops, effects, etc."""
        from audio import audio
        
        self.game.kills += 1
        self.player.kills += 1
        
        # Upgrade manager tracking
        upgrade_mgr = getattr(self.player, "upgrade_manager", None)
        if upgrade_mgr:
            upgrade_mgr.on_kill(
                enemy_was_cursed=enemy_was_cursed,
                enemy_was_frozen=getattr(en, "frozen_timer", 0) > 0
            )
        
        # Drop XP
        self.game.orbs.append(XPOrb(en.x, en.y, XP_PER_ORB))
        
        # Chance for gas pickup
        if random.random() < 0.05:
            self.game.gas_pickups.append(GasPickup(en.x, en.y))
        
        # Splinter on kill
        if getattr(self.player, "splinter_on_kill", False):
            self._spawn_splinter_bullets(en)
        
        # Shatter (frozen enemy explosion)
        if getattr(en, "frozen_timer", 0) > 0:
            shatter_ratio = getattr(self.player, "shatter_damage_ratio", 0)
            if shatter_ratio > 0:
                max_hp = getattr(en, "max_hp", 100)
                shatter_damage = int(max_hp * shatter_ratio)
                self._apply_area_damage(en.x, en.y, 80, shatter_damage, exclude=en)
        
        # Burn chain
        if self.player.burn_chain:
            for other in self.enemies:
                if other is en:
                    continue
                dx = other.x - en.x
                dy = other.y - en.y
                if dx * dx + dy * dy <= 140 * 140:
                    other.burn_timer = max(other.burn_timer, 3.0)
                    other.burn_dps = max(other.burn_dps, self.player.damage * 0.2 * self.player.burn_bonus_mult)
        
        # Boss drops
        if getattr(en, "kind", "") == "boss":
            self.game._spawn_evolution_pickup(en.x, en.y)
            audio.play_sfx(audio.snd_boss_explosion)
        
        # Death FX
        self.game._spawn_enemy_pop(en.x, en.y)
        
        # Remove from list
        if en in self.enemies:
            self.game.enemies.remove(en)
    
    def _spawn_splinter_bullets(self, en):
        """Spawn splinter bullets when enemy dies."""
        count = getattr(self.player, "splinter_count", 3)
        damage_ratio = getattr(self.player, "splinter_damage_ratio", 0.10)
        damage = int(self.player.damage * damage_ratio)
        
        for i in range(count):
            ang = math.tau * i / count + random.uniform(-0.2, 0.2)
            vx = math.cos(ang)
            vy = math.sin(ang)
            b = Bullet(
                en.x, en.y, vx, vy, damage,
                self.player.bullet_speed * 0.8,
                status=self.player.bullet_status.copy()
            )
            b.piercing = False
            self.game.bullets.append(b)
    
    def _apply_area_damage(self, x: float, y: float, radius: float, damage: int, exclude=None):
        """Apply damage to all enemies in an area."""
        rad_sq = radius * radius
        for en in list(self.enemies):
            if en is exclude:
                continue
            dx = en.x - x
            dy = en.y - y
            if dx * dx + dy * dy <= rad_sq:
                en.hp -= damage
                en.flash_timer = 0.1
                
                self.game.damage_texts.append({
                    "x": en.x + random.uniform(-4, 4),
                    "y": en.y - 8,
                    "val": damage,
                    "life": 0.5,
                    "color": (255, 200, 100)
                })
    
    def process_player_enemy_collisions(self):
        """Handle collisions between player and enemies."""
        from audio import audio
        from game_constants import STATE_DEAD_ANIM
        
        for en in list(self.enemies):
            if not circle_collision(
                self.player.x, self.player.y, self.player.radius,
                en.x, en.y, en.radius
            ):
                continue
            
            # Check dodge
            upgrade_mgr = getattr(self.player, "upgrade_manager", None)
            if upgrade_mgr and upgrade_mgr.check_dodge():
                continue
            
            if self.player.invuln <= 0:
                # Apply body damage to enemy if player has it
                body_damage = getattr(self.player, "body_damage", 0)
                if body_damage > 0:
                    en.hp -= body_damage
                    en.flash_timer = 0.1
                    if en.hp <= 0:
                        self._handle_enemy_death(en)
                
                self.player.take_damage(1)
                audio.play_sfx(audio.snd_player_hit)
                
                if upgrade_mgr:
                    upgrade_mgr.on_hit()
                
                # Knockback both
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
                    self.game._spawn_death_fx(self.player.x, self.player.y)
                    self.game.death_timer = 1.0
                    self.game.state = STATE_DEAD_ANIM
                    return True  # Player died
        
        return False  # Player alive
    
    def process_dot_damage(self, dt: float):
        """Process damage over time effects on enemies."""
        tick = 0.35
        
        for en in list(self.enemies):
            # Burn
            if en.burn_timer > 0 and en.burn_dps > 0:
                en.burn_tick += dt
                while en.burn_tick >= tick:
                    en.burn_tick -= tick
                    dmg = en.burn_dps * tick
                    en.hp -= dmg
                    
                    self.game.damage_texts.append({
                        "x": en.x + random.uniform(-4, 4),
                        "y": en.y - 8,
                        "val": max(1, int(dmg + 0.5)),
                        "life": 0.5,
                        "color": (255, 110, 80)
                    })
                    self.game._spawn_status_fx(en.x, en.y, kind="fire")
                    
                    # Soothing Warmth - chance to heal from burn
                    heal_chance = getattr(self.player, "burn_heal_chance", 0)
                    if heal_chance > 0 and random.random() < heal_chance:
                        self.player.heal(1)
            
            # Poison
            if en.poison_timer > 0 and en.poison_dps > 0:
                en.poison_tick += dt
                while en.poison_tick >= tick:
                    en.poison_tick -= tick
                    dmg = en.poison_dps * tick
                    en.hp -= dmg
                    
                    self.game.damage_texts.append({
                        "x": en.x + random.uniform(-4, 4),
                        "y": en.y - 8,
                        "val": max(1, int(dmg + 0.5)),
                        "life": 0.5,
                        "color": (140, 255, 160)
                    })
                    self.game._spawn_status_fx(en.x, en.y, kind="poison")
            
            # Ice
            if en.ice_timer > 0 and en.ice_dps > 0:
                en.ice_tick += dt
                while en.ice_tick >= tick:
                    en.ice_tick -= tick
                    dmg = en.ice_dps * tick
                    en.hp -= dmg
                    
                    self.game.damage_texts.append({
                        "x": en.x + random.uniform(-4, 4),
                        "y": en.y - 8,
                        "val": max(1, int(dmg + 0.5)),
                        "life": 0.5,
                        "color": (170, 210, 255)
                    })
                    self.game._spawn_status_fx(en.x, en.y, kind="ice")
            
            # Curse detonation
            if hasattr(en, "curse_timer") and en.curse_timer > 0:
                en.curse_timer -= dt
                if en.curse_timer <= 0:
                    en.hp -= getattr(en, "curse_damage", 0)
                    en.flash_timer = 0.15
                    
                    self.game.damage_texts.append({
                        "x": en.x,
                        "y": en.y - 12,
                        "val": getattr(en, "curse_damage", 0),
                        "life": 0.6,
                        "color": (180, 100, 255)
                    })
    
    def process_dot_deaths(self):
        """Handle deaths from DoT effects."""
        for en in list(self.enemies):
            if en.hp <= 0:
                enemy_was_cursed = getattr(en, "cursed", False)
                self._handle_enemy_death(en, enemy_was_cursed=enemy_was_cursed)
    
    def update_aura_damage(self, dt: float):
        """Apply aura damage around the player."""
        if self.player.aura_radius <= 0 or self.player.aura_dps <= 0:
            return
        
        rad_sq = self.player.aura_radius * self.player.aura_radius
        for en in self.enemies:
            dx = en.x - self.player.x
            dy = en.y - self.player.y
            if dx * dx + dy * dy <= rad_sq:
                en.hp -= self.player.aura_dps * dt
                if random.random() < 0.15:
                    self.game._emit_status_particle(en, "fire")
    
    def fire_lightning(self, damage: int, area_mult: float = 1.0, targets: int = 1):
        """Fire lightning at nearest enemies."""
        if not self.enemies:
            return
        
        # Sort by distance
        sorted_enemies = sorted(
            self.enemies,
            key=lambda en: (en.x - self.player.x) ** 2 + (en.y - self.player.y) ** 2
        )
        
        for i in range(min(targets, len(sorted_enemies))):
            en = sorted_enemies[i]
            en.hp -= damage
            en.flash_timer = 0.1
            
            self.game.damage_texts.append({
                "x": en.x,
                "y": en.y - 10,
                "val": damage,
                "life": 0.5,
                "color": (255, 255, 100)
            })
            
            # Lightning visual effect
            self._spawn_lightning_fx(self.player.x, self.player.y, en.x, en.y)
            
            # Area damage
            if area_mult > 1.0:
                area_radius = 50 * area_mult
                area_damage = int(damage * 0.5)
                self._apply_area_damage(en.x, en.y, area_radius, area_damage, exclude=en)
    
    def _spawn_lightning_fx(self, x1: float, y1: float, x2: float, y2: float):
        """Spawn lightning visual effect between two points."""
        # Add lightning particles along the line
        steps = 8
        for i in range(steps):
            t = i / max(1, steps - 1)
            px = x1 + (x2 - x1) * t + random.uniform(-10, 10)
            py = y1 + (y2 - y1) * t + random.uniform(-10, 10)
            
            self.game.status_particles.append({
                "x": px,
                "y": py,
                "vx": random.uniform(-5, 5),
                "vy": random.uniform(-5, 5),
                "life": 0.0,
                "life_max": 0.15,
                "color": (255, 255, 150),
                "kind": "spark",
                "size": random.uniform(3, 5)
            })
    
    def fire_gale(self, direction: Tuple[float, float] = None):
        """Fire a gale attack."""
        p = self.player
        damage = getattr(p, "gale_damage", 20)
        
        # Scale with speed if applicable
        if getattr(p, "gale_scales_speed", False):
            speed_mult = p.speed / 5.0
            damage = int(damage * speed_mult)
        
        # Center damage multiplier
        center_mult = getattr(p, "gale_center_damage_mult", 1.0)
        
        # Apply to nearby enemies
        gale_radius = 150
        center_radius = 60
        
        for en in self.enemies:
            dx = en.x - p.x
            dy = en.y - p.y
            dist = math.hypot(dx, dy)
            
            if dist <= gale_radius:
                final_damage = damage
                if dist <= center_radius and center_mult > 1.0:
                    final_damage = int(damage * center_mult)
                
                en.hp -= final_damage
                en.flash_timer = 0.05
                
                # Push away
                if dist > 1:
                    push = 25
                    en.x += dx / dist * push
                    en.y += dy / dist * push
                
                self.game.damage_texts.append({
                    "x": en.x,
                    "y": en.y - 8,
                    "val": final_damage,
                    "life": 0.4,
                    "color": (200, 255, 200)
                })
    
    def fire_smite(self, damage: int):
        """Fire smite attack at nearby enemies."""
        smite_radius = 200
        
        for en in self.enemies:
            dx = en.x - self.player.x
            dy = en.y - self.player.y
            if dx * dx + dy * dy <= smite_radius * smite_radius:
                en.hp -= damage
                en.flash_timer = 0.15
                
                self.game.damage_texts.append({
                    "x": en.x,
                    "y": en.y - 10,
                    "val": damage,
                    "life": 0.5,
                    "color": (255, 255, 200)
                })
                
                # Smite visual
                self.game.status_particles.append({
                    "x": en.x,
                    "y": en.y - 20,
                    "vx": 0,
                    "vy": -15,
                    "life": 0.0,
                    "life_max": 0.3,
                    "color": (255, 255, 200),
                    "kind": "spark",
                    "size": 8
                })
    
    def fire_fan_fire(self, count: int, damage_ratio: float):
        """Fire bullets in a circle (fan fire)."""
        damage = int(self.player.damage * damage_ratio)
        
        for i in range(count):
            ang = math.tau * i / count
            vx = math.cos(ang)
            vy = math.sin(ang)
            
            b = Bullet(
                self.player.x, self.player.y,
                vx, vy, damage, self.player.bullet_speed,
                status=self.player.bullet_status.copy()
            )
            b.piercing = self.player.piercing
            if self.player.pierce_mode == "corpse":
                b.pierce_on_kill = True
                b.pierce_left = 1
            elif self.player.pierce_mode == "full":
                b.pierce_left = 999
            
            self.game.bullets.append(b)
    
    def fire_ice_shards(self, count: int, freeze: bool = True):
        """Fire ice shards in a spread."""
        damage = int(self.player.damage * 0.5)
        
        # Shoot towards mouse direction with spread
        mx, my = self.game.get_mouse_world_pos()
        base_ang = math.atan2(my - self.player.y, mx - self.player.x)
        
        spread = math.radians(45)
        for i in range(count):
            if count == 1:
                ang = base_ang
            else:
                ang = base_ang - spread / 2 + spread * i / (count - 1)
            
            vx = math.cos(ang)
            vy = math.sin(ang)
            
            status = {"ice": True, "burn": False, "poison": False}
            b = Bullet(
                self.player.x, self.player.y,
                vx, vy, damage, self.player.bullet_speed * 1.2,
                status=status
            )
            b.piercing = True
            b.pierce_left = 2
            b.is_ice_shard = True
            
            self.game.bullets.append(b)
    
    def update_glare_damage(self, dt: float):
        """Apply glare damage to enemies in vision range."""
        upgrade_mgr = getattr(self.player, "upgrade_manager", None)
        if not upgrade_mgr:
            return
        
        damage = upgrade_mgr.get_glare_damage_this_frame(dt)
        if damage <= 0:
            return
        
        vision_range = getattr(self.player, "vision_range", 400)
        range_sq = vision_range * vision_range
        
        for en in self.enemies:
            dx = en.x - self.player.x
            dy = en.y - self.player.y
            if dx * dx + dy * dy <= range_sq:
                en.hp -= damage
                
                # Apply on-hit effects if glare_on_hit
                if getattr(self.player, "glare_on_hit", False):
                    # Apply status from bullet_status
                    if self.player.bullet_status.get("burn"):
                        en.burn_timer = max(en.burn_timer, 1.0)
                        en.burn_dps = max(en.burn_dps, self.player.damage * 0.1)
                    if self.player.bullet_status.get("ice"):
                        en.ice_timer = max(en.ice_timer, 1.0)
                    if self.player.bullet_status.get("poison"):
                        en.poison_timer = max(en.poison_timer, 1.0)
