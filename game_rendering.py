"""
Game Rendering Module - Handles all rendering logic
====================================================
Extracted from game.py to reduce file size and improve organization.
"""

import math
import pygame
from typing import Tuple, List, Optional, TYPE_CHECKING

from game_constants import (
    WIDTH, HEIGHT, COLOR_BG, COLOR_WHITE, COLOR_YELLOW, COLOR_RED,
    COLOR_GREEN, COLOR_DARK_GRAY, COLOR_GRAY, COLOR_PLAYER,
    clamp
)

if TYPE_CHECKING:
    from game import Game


class RenderManager:
    """Manages all rendering for the game."""
    
    def __init__(self, game: 'Game'):
        self.game = game
    
    @property
    def screen(self):
        return self.game.screen
    
    @property
    def player(self):
        return self.game.player
    
    def draw_background(self, cam: Tuple[float, float], target: pygame.Surface = None):
        """Draw space starfield background."""
        surface = target if target is not None else self.screen
        w, h = surface.get_size()
        ox, oy = cam
        
        for s in self.game.stars:
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
        
        # Shimmering flashes
        for f in list(self.game.star_flashes):
            fx = int(f["x"] - ox)
            fy = int(f["y"] - oy)
            if -5 <= fx <= w + 5 and -5 <= fy <= h + 5:
                alpha = int(255 * (f["life"] / f["life_max"]))
                flash_surf = pygame.Surface((f["r"] * 2, f["r"] * 2), pygame.SRCALPHA)
                pygame.draw.circle(flash_surf, (255, 255, 255, alpha), (f["r"], f["r"]), f["r"])
                surface.blit(flash_surf, (fx - f["r"], fy - f["r"]))
    
    def draw_particles(self, cam: Tuple[float, float], target: pygame.Surface):
        """Draw all particle effects."""
        # Boost particles
        for p in self.game.boost_particles:
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
            target.blit(surf, (int(sx - size * 1.3), int(sy - size * 1.3)))
        
        # Status particles
        for p in self.game.status_particles:
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
            
            target.blit(surf, (int(sx - size * 1.5), int(sy - size * 1.5)))
    
    def draw_aura_orbs(self, cam: Tuple[float, float], target: pygame.Surface):
        """Draw player's aura orbs."""
        if not self.player.aura_unlocked:
            return
        
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
            pygame.draw.circle(target, outer, (ox, oy), max(1, r + 3), width=2)
            pygame.draw.circle(target, inner, (ox, oy), r)
    
    def draw_minions(self, cam: Tuple[float, float], target: pygame.Surface):
        """Draw player's minions."""
        for m in self.game.minions:
            sx = int(m.get("x", self.player.x) - cam[0])
            sy = int(m.get("y", self.player.y) - cam[1])
            pygame.draw.circle(target, (180, 255, 255), (sx, sy), 10)
            pygame.draw.circle(target, (60, 180, 220), (sx, sy), 6)
    
    def draw_summons(self, cam: Tuple[float, float], target: pygame.Surface):
        """Draw player's summoned entities (ghosts, scythes, spears, dragon, etc.)."""
        p = self.player
        
        # Ghost
        if getattr(p, "ghost_count", 0) > 0:
            for ghost in getattr(p, "ghosts", []):
                gx = int(ghost.get("x", p.x) - cam[0])
                gy = int(ghost.get("y", p.y) - cam[1])
                # Ghost sprite - semi-transparent
                ghost_surf = pygame.Surface((30, 30), pygame.SRCALPHA)
                pygame.draw.ellipse(ghost_surf, (200, 200, 255, 150), (0, 5, 30, 25))
                pygame.draw.circle(ghost_surf, (255, 255, 255, 180), (15, 10), 8)
                pygame.draw.circle(ghost_surf, (50, 50, 80), (12, 9), 3)
                pygame.draw.circle(ghost_surf, (50, 50, 80), (18, 9), 3)
                target.blit(ghost_surf, (gx - 15, gy - 15))
        
        # Scythe
        if getattr(p, "scythe_count", 0) > 0:
            for scythe in getattr(p, "scythes", []):
                sx = int(scythe.get("x", p.x) - cam[0])
                sy = int(scythe.get("y", p.y) - cam[1])
                ang = scythe.get("angle", 0)
                
                # Draw rotating scythe
                length = 40
                end_x = sx + math.cos(ang) * length
                end_y = sy + math.sin(ang) * length
                pygame.draw.line(target, (80, 80, 100), (sx, sy), (int(end_x), int(end_y)), 3)
                
                # Blade
                blade_ang = ang + math.pi / 4
                blade_x = end_x + math.cos(blade_ang) * 20
                blade_y = end_y + math.sin(blade_ang) * 20
                pygame.draw.line(target, (180, 180, 200), (int(end_x), int(end_y)), (int(blade_x), int(blade_y)), 5)
        
        # Spear
        if getattr(p, "spear_count", 0) > 0:
            for spear in getattr(p, "spears", []):
                spx = int(spear.get("x", p.x) - cam[0])
                spy = int(spear.get("y", p.y) - cam[1])
                ang = spear.get("angle", 0)
                
                length = 50
                end_x = spx + math.cos(ang) * length
                end_y = spy + math.sin(ang) * length
                pygame.draw.line(target, (200, 180, 100), (spx, spy), (int(end_x), int(end_y)), 4)
                
                # Tip
                tip_length = 12
                tip_x = end_x + math.cos(ang) * tip_length
                tip_y = end_y + math.sin(ang) * tip_length
                pygame.draw.line(target, (255, 220, 150), (int(end_x), int(end_y)), (int(tip_x), int(tip_y)), 6)
        
        # Dragon
        if getattr(p, "dragon_active", False):
            dragon = getattr(p, "dragon", None)
            if dragon:
                dx = int(dragon.get("x", p.x + 80) - cam[0])
                dy = int(dragon.get("y", p.y) - cam[1])
                
                # Simple dragon sprite
                dragon_surf = pygame.Surface((50, 40), pygame.SRCALPHA)
                # Body
                pygame.draw.ellipse(dragon_surf, (180, 60, 60), (10, 10, 30, 20))
                # Head
                pygame.draw.circle(dragon_surf, (200, 80, 80), (40, 15), 10)
                # Wings
                pygame.draw.polygon(dragon_surf, (150, 40, 40, 200), [(15, 10), (0, 0), (20, 5)])
                pygame.draw.polygon(dragon_surf, (150, 40, 40, 200), [(15, 30), (0, 40), (20, 35)])
                # Eye
                pygame.draw.circle(dragon_surf, (255, 255, 100), (42, 13), 3)
                
                target.blit(dragon_surf, (dx - 25, dy - 20))
        
        # Lens - 2D C-shaped curves (rendered in game.py draw_game_world instead)
        # This is legacy code, lenses are now drawn in the main game loop
        
        # Electro Bug
        if getattr(p, "electro_bug", False):
            bug = getattr(p, "electro_bug_entity", None)
            if bug:
                bx = int(bug.get("x", p.x + 50) - cam[0])
                by = int(bug.get("y", p.y - 30) - cam[1])
                
                # Lightning bug
                bug_surf = pygame.Surface((20, 20), pygame.SRCALPHA)
                pygame.draw.circle(bug_surf, (255, 255, 100, 200), (10, 10), 8)
                pygame.draw.circle(bug_surf, (255, 255, 200), (10, 10), 4)
                
                target.blit(bug_surf, (bx - 10, by - 10))
    
    def draw_laser(self, cam: Tuple[float, float], target: pygame.Surface):
        """Draw laser beam."""
        if not self.player.laser_active or not self.game.laser_segment:
            return
        
        px, py, ex, ey = self.game.laser_segment
        start = (int(px - cam[0]), int(py - cam[1]))
        end = (int(ex - cam[0]), int(ey - cam[1]))
        
        pygame.draw.line(target, (255, 140, 70), start, end, 30)
        pygame.draw.line(target, (255, 230, 180), start, end, 12)
        
        # Start flash (burst)
        burst_r = 46
        flash = pygame.Surface((burst_r * 2, burst_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(flash, (255, 200, 140, 190), (burst_r, burst_r), burst_r)
        pygame.draw.circle(flash, (255, 255, 240, 230), (burst_r, burst_r), max(8, burst_r // 2))
        target.blit(flash, (start[0] - burst_r, start[1] - burst_r))
    
    def draw_death_fx(self, cam: Tuple[float, float], target: pygame.Surface = None):
        """Draw death particle effects."""
        surface = target if target is not None else self.screen
        for fx in self.game.death_fx:
            sx = int(fx["x"] - cam[0])
            sy = int(fx["y"] - cam[1])
            life_ratio = fx.get("life", 0) / max(0.001, fx.get("life_max", 1.0))
            r = max(4, int(fx.get("r_base", 12) * life_ratio))
            pygame.draw.circle(surface, COLOR_RED, (sx, sy), r)
    
    def draw_damage_texts(self, cam: Tuple[float, float], target: pygame.Surface = None):
        """Draw floating damage numbers."""
        surface = target if target is not None else self.screen
        for txt in self.game.damage_texts:
            sx = int(txt["x"] - cam[0])
            sy = int(txt["y"] - cam[1])
            alpha = int(255 * (txt["life"] / 0.6))
            color = txt.get("color", COLOR_YELLOW)
            surf = self.game.font_small.render(str(txt["val"]), True, color)
            surf.set_alpha(alpha)
            surface.blit(surf, (sx, sy))
    
    def draw_boost_overlay(self):
        """Draw boost effect overlay."""
        if self.game.boost_effect_timer <= 0:
            return
        
        strength = min(1.0, self.game.boost_effect_timer / 3.0)
        thickness = 90
        overlay = pygame.Surface((self.game.w, self.game.h), pygame.SRCALPHA)
        
        for i in range(thickness):
            alpha = int(140 * (1 - i / thickness) * strength)
            color = (80, 240, 220, alpha)
            pygame.draw.rect(overlay, color, (i, 0, 1, self.game.h))
            pygame.draw.rect(overlay, color, (self.game.w - i - 1, 0, 1, self.game.h))
        
        self.screen.blit(overlay, (0, 0))
    
    def draw_vision_overlay(self):
        """Draw vision/darkness overlay."""
        alpha = int(180 * max(0.0, min(1.0, self.game.vision_dim)))
        if alpha <= 0:
            return
        
        overlay = pygame.Surface((self.game.w, self.game.h), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (0, 0, 0, alpha), (0, 0, self.game.w, self.game.h))
        self.screen.blit(overlay, (0, 0))
    
    def draw_hud(self):
        """Draw the heads-up display."""
        from game_constants import STATE_PLAYING
        
        base_y = self.game.btn_pause.rect.y + 6
        
        # LVL label
        lvl_txt = self.game.font_small.render(f"LVL {self.player.level}", True, COLOR_WHITE)
        lvl_x = 16
        self.screen.blit(lvl_txt, (lvl_x, base_y))
        
        # Hearts
        x = lvl_x + lvl_txt.get_width() + 16
        spacing = 24
        for i in range(self.player.max_hearts):
            col = COLOR_RED if i < self.player.hearts else COLOR_DARK_GRAY
            cx = x + i * spacing
            cy = base_y + 2
            pygame.draw.polygon(self.screen, col, [(cx + 6, cy + 6), (cx, cy + 12), (cx + 6, cy + 18), (cx + 12, cy + 12)])
        
        # Soul Hearts (if any)
        soul_hearts = getattr(self.player, "soul_hearts", 0)
        if soul_hearts > 0:
            soul_x = x + self.player.max_hearts * spacing + 10
            for i in range(soul_hearts):
                cx = soul_x + i * spacing
                cy = base_y + 2
                pygame.draw.polygon(self.screen, (180, 100, 255), [(cx + 6, cy + 6), (cx, cy + 12), (cx + 6, cy + 18), (cx + 12, cy + 12)])
        
        # Shield indicator
        upgrade_mgr = getattr(self.player, "upgrade_manager", None)
        if upgrade_mgr and upgrade_mgr.shield_active:
            shield_txt = self.game.font_tiny.render("SHIELDED", True, (100, 200, 255))
            self.screen.blit(shield_txt, (lvl_x, base_y - 20))
        
        # XP bar
        bw2, bh2 = self.game.w - 200, 10
        x2, y2 = 100, self.game.h - 30
        pygame.draw.rect(self.screen, COLOR_DARK_GRAY, (x2, y2, bw2, bh2))
        xp_ratio = self.player.xp / max(1, self.player.xp_to_level)
        pygame.draw.rect(self.screen, COLOR_GREEN, (x2, y2, int(bw2 * xp_ratio), bh2))
        
        # Time
        t = int(self.game.elapsed_time)
        m, s = t // 60, t % 60
        timer_text = self.game.font_small.render(f"{m:02d}:{s:02d}", True, COLOR_WHITE)
        time_y = base_y
        self.screen.blit(timer_text, (self.game.w // 2 - timer_text.get_width() // 2, time_y))
        
        # Kills
        kills_txt = self.game.font_small.render(f"KILLS {self.game.kills}", True, COLOR_WHITE)
        kills_y = base_y
        kills_x = self.game.btn_pause.rect.x - kills_txt.get_width() - 14
        self.screen.blit(kills_txt, (kills_x, kills_y))
        
        if self.game.state == STATE_PLAYING:
            self.game.btn_pause.draw(self.screen)
        
        # Ammo
        ammo_y = base_y + 26
        if self.player.reload_timer > 0:
            ammo_txt = self.game.font_small.render("RELOADING...", True, COLOR_YELLOW)
        else:
            ammo_txt = self.game.font_small.render(f"AMMO {self.player.ammo}/{self.player.mag_size}", True, COLOR_WHITE)
        self.screen.blit(ammo_txt, (lvl_x, ammo_y))
        
        # Laser status
        laser_y = ammo_y + 22
        if self.player.laser_active:
            laser_txt = self.game.font_small.render("LASER ACTIVE", True, COLOR_GREEN)
        elif self.player.laser_cooldown > 0:
            laser_txt = self.game.font_small.render(f"LASER {int(self.player.laser_cooldown)}s", True, COLOR_WHITE)
        else:
            laser_txt = self.game.font_small.render("LASER READY", True, COLOR_GREEN)
        self.screen.blit(laser_txt, (lvl_x, laser_y))
        
        # Boost meter
        bar_h = 140
        bar_w = 16
        bar_x = self.game.w - 40
        bar_y = self.game.h - 40 - bar_h
        pygame.draw.rect(self.screen, COLOR_DARK_GRAY, (bar_x, bar_y, bar_w, bar_h))
        ratio = self.player.boost_meter / max(1, self.player.boost_meter_max)
        fill_h = int(bar_h * ratio)
        pygame.draw.rect(self.screen, (120, 240, 255), (bar_x, bar_y + (bar_h - fill_h), bar_w, fill_h))
        
        boost_color = (255, 160, 90) if self.player.boosting else COLOR_WHITE
        letters = "BOOST"
        lx = bar_x + bar_w + 6
        ly = bar_y
        for ch in letters:
            surf = self.game.font_tiny.render(ch, True, boost_color)
            self.screen.blit(surf, (lx, ly))
            ly += surf.get_height() + 2
        
        # Active upgrade effects indicators
        self._draw_active_effects(lvl_x, laser_y + 22)
    
    def _draw_active_effects(self, x: int, y: int):
        """Draw indicators for active temporary effects."""
        upgrade_mgr = getattr(self.player, "upgrade_manager", None)
        if not upgrade_mgr:
            return
        
        effects = []
        
        if upgrade_mgr.fresh_clip_timer > 0:
            effects.append(("FRESH CLIP", (255, 200, 100)))
        
        if upgrade_mgr.anger_timer > 0:
            effects.append(("ANGER", (255, 100, 100)))
        
        if upgrade_mgr.xp_fire_rate_timer > 0:
            effects.append(("EXCITED", (100, 255, 100)))
        
        if upgrade_mgr.wind_bonus_stacks > 0:
            effects.append((f"WIND x{upgrade_mgr.wind_bonus_stacks}", (200, 255, 200)))
        
        for i, (text, color) in enumerate(effects):
            txt = self.game.font_tiny.render(text, True, color)
            self.screen.blit(txt, (x, y + i * 18))
    
    def draw_upgrade_tree_panel(self):
        """Draw Diep.io style stat upgrade panel."""
        from upgrade_trees import STAT_UPGRADES
        
        panel_w = 200
        panel_h = len(STAT_UPGRADES) * 30 + 40
        panel_x = 10
        panel_y = self.game.h // 2 - panel_h // 2
        
        # Background
        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, (20, 20, 40, 200), (0, 0, panel_w, panel_h), border_radius=8)
        
        # Title
        title = self.game.font_tiny.render("STATS", True, COLOR_WHITE)
        panel_surf.blit(title, (panel_w // 2 - title.get_width() // 2, 8))
        
        # Stat bars
        upgrade_mgr = getattr(self.player, "upgrade_manager", None)
        y = 30
        
        for stat_id, stat_data in STAT_UPGRADES.items():
            current_level = upgrade_mgr.stat_levels.get(stat_id, 0) if upgrade_mgr else 0
            max_level = stat_data["max_level"]
            
            # Stat name
            name_txt = self.game.font_tiny.render(stat_data["name"][:12], True, COLOR_WHITE)
            panel_surf.blit(name_txt, (8, y))
            
            # Level pips
            pip_x = 120
            pip_w = 8
            pip_gap = 2
            for i in range(max_level):
                col = COLOR_GREEN if i < current_level else COLOR_DARK_GRAY
                pygame.draw.rect(panel_surf, col, (pip_x + i * (pip_w + pip_gap), y + 2, pip_w, 12))
            
            y += 25
        
        self.screen.blit(panel_surf, (panel_x, panel_y))
    
    def draw_upgrade_selection(self, options: list, selected_idx: int = -1):
        """Draw upgrade selection cards."""
        from upgrade_system import get_upgrade_name, get_upgrade_description, get_upgrade_tier
        
        # Overlay
        overlay = pygame.Surface((self.game.w, self.game.h))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # Title
        title = self.game.font_large.render("CHOOSE UPGRADE", True, COLOR_YELLOW)
        self.screen.blit(title, (self.game.w // 2 - title.get_width() // 2, self.game.h // 4))
        
        # Cards
        card_w = 300
        card_h = 180
        gap = 24
        total_w = len(options) * card_w + (len(options) - 1) * gap
        start_x = self.game.w // 2 - total_w // 2
        y = self.game.h // 2 - card_h // 2
        
        mouse_pos = pygame.mouse.get_pos()
        
        for i, upgrade in enumerate(options):
            rect = pygame.Rect(start_x + i * (card_w + gap), y, card_w, card_h)
            is_hover = rect.collidepoint(mouse_pos) or i == selected_idx
            
            # Tier color
            tier = upgrade.tier
            if tier == 3:
                border_col = (255, 200, 100)  # Ultimate
            elif tier == 2:
                border_col = (150, 150, 255)
            else:
                border_col = COLOR_GRAY
            
            # Card background
            bg_col = COLOR_GRAY if is_hover else COLOR_DARK_GRAY
            pygame.draw.rect(self.screen, bg_col, rect, border_radius=8)
            pygame.draw.rect(self.screen, border_col, rect, width=3, border_radius=8)
            
            # Tier badge
            tier_text = "ULTIMATE" if tier == 3 else f"TIER {tier}"
            tier_txt = self.game.font_tiny.render(tier_text, True, border_col)
            self.screen.blit(tier_txt, (rect.x + 10, rect.y + 10))
            
            # Category badge
            cat_txt = self.game.font_tiny.render(upgrade.category, True, COLOR_WHITE)
            self.screen.blit(cat_txt, (rect.right - cat_txt.get_width() - 10, rect.y + 10))
            
            # Name
            name = upgrade.name
            t1 = self.game.font_small.render(name, True, COLOR_WHITE)
            self.screen.blit(t1, (rect.centerx - t1.get_width() // 2, rect.y + 50))
            
            # Description (word wrap)
            desc = upgrade.description
            desc_lines = self._wrap_text(desc, self.game.font_tiny, card_w - 20)
            for j, line in enumerate(desc_lines[:3]):
                t2 = self.game.font_tiny.render(line, True, COLOR_WHITE)
                self.screen.blit(t2, (rect.centerx - t2.get_width() // 2, rect.y + 85 + j * 20))
    
    def _wrap_text(self, text: str, font: pygame.font.Font, max_width: int) -> List[str]:
        """Wrap text to fit within a width."""
        words = text.split(' ')
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            if font.size(test_line)[0] <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
