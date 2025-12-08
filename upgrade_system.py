"""
Upgrade System - Simplified Version
====================================
Handles upgrade application and effect management.
"""

import math
import random
from typing import List, Dict, Set
from upgrade_trees import (
    Upgrade, UPGRADES_BY_ID, TREES_BY_ID, ALL_TREES,
    EVOLUTIONS, get_tier3_upgrades, get_all_effects_for_tier3,
    get_available_evolutions, CATEGORIES
)


class UpgradeManager:
    """Manages player's upgrade state and applies effects."""
    
    def __init__(self, player):
        self.player = player
        self.owned_upgrades: Set[str] = set()
        self.active_evolutions: List[dict] = []
        
        # Tracking counters
        self.kill_counter = 0
        self.curse_kills = 0
        self.kill_clip_stacks = 0
        
        # Timers
        self.dragon_age = 0.0
        self.regen_timer = 0.0
        self.glare_timer = 0.0
        self.lightning_timer = 0.0
        self.shield_regen_timer = 0.0
        self.orb_pulse_timer = 0.0
        self.dragon_growth_time = 0.0
        
        # State flags
        self.dragon_hatched = False
    
    def get_available_options(self, count: int = 3) -> List[Upgrade]:
        """Get random selection of available upgrades for level-up screen."""
        available = []
        for tree in ALL_TREES:
            for upgrade in tree["upgrades"]:
                if upgrade.id in self.owned_upgrades:
                    continue
                
                # Check explicit requirements first (cross-tree dependencies)
                if upgrade.requires:
                    if not all(req in self.owned_upgrades for req in upgrade.requires):
                        continue
                
                # Check tier requirements within the same tree
                if upgrade.tier == 1:
                    # Tier 1 with no explicit requires is always available
                    if not upgrade.requires:
                        available.append(upgrade)
                    else:
                        # Tier 1 with requires already passed the check above
                        available.append(upgrade)
                elif upgrade.tier == 2:
                    # Need tier 1 of same tree OR explicit requires satisfied
                    tier1_owned = any(
                        u.id in self.owned_upgrades 
                        for u in tree["upgrades"] if u.tier == 1
                    )
                    if tier1_owned or upgrade.requires:
                        available.append(upgrade)
                elif upgrade.tier == 3:
                    # Need at least one tier 2 of same tree OR explicit requires satisfied
                    tier2_owned = any(
                        u.id in self.owned_upgrades 
                        for u in tree["upgrades"] if u.tier == 2
                    )
                    if tier2_owned or upgrade.requires:
                        available.append(upgrade)
        
        if len(available) <= count:
            return available
        return random.sample(available, count)
    
    def get_tier3_options(self) -> List[Upgrade]:
        """Get all tier 3 upgrades for test mode."""
        return get_tier3_upgrades()
    
    def apply_upgrade(self, upgrade_id: str, apply_full_tree: bool = False) -> bool:
        """Apply an upgrade to the player. 
        If apply_full_tree=True, applies all effects from tier 1-3 (for test mode).
        """
        if upgrade_id in self.owned_upgrades:
            return False
        
        if upgrade_id not in UPGRADES_BY_ID:
            return False
        
        upgrade = UPGRADES_BY_ID[upgrade_id]
        
        if apply_full_tree:
            # Apply combined effects of entire tree
            effects = get_all_effects_for_tier3(upgrade)
            self._apply_effects(effects)
            # Mark all upgrades in tree as owned
            tree = TREES_BY_ID.get(upgrade.tree_id)
            if tree:
                for u in tree["upgrades"]:
                    self.owned_upgrades.add(u.id)
        else:
            # Normal application
            self._apply_effects(upgrade.effects)
            self.owned_upgrades.add(upgrade_id)
        
        # Check for available evolutions
        self._check_evolutions()
        return True
    
    def apply_evolution(self, evolution_id: str) -> bool:
        """Apply an evolution upgrade."""
        if evolution_id not in EVOLUTIONS:
            return False
        
        evo = EVOLUTIONS[evolution_id]
        self._apply_effects(evo["effects"])
        self.active_evolutions.append(evo)
        return True
    
    def _apply_effects(self, effects: dict):
        """Apply a dictionary of effects to the player."""
        p = self.player
        
        for key, value in effects.items():
            # ===== CANNONS =====
            if key == "cannon_count":
                p.cannon_count = max(getattr(p, "cannon_count", 1), int(value))
                p.bullet_count = p.cannon_count  # Sync shooting with visual cannons
            elif key == "cannon_spread":
                p.cannon_spread = value
            elif key == "has_rear_cannon":
                p.has_rear_cannon = True
            elif key == "cannon_pattern":
                p.cannon_pattern = value
            
            # ===== BULLET PROPERTIES =====
            elif key == "damage_mult":
                p.damage = int(p.damage * value)
            elif key == "bullet_speed_mult":
                p.bullet_speed *= value
            elif key == "fire_rate_mult":
                p.fire_rate *= value
                p.fire_cd = 1.0 / p.fire_rate
            elif key == "bullet_size_mult":
                p.bullet_size_mult = getattr(p, "bullet_size_mult", 1.0) * value
            elif key == "pierce_count":
                p.pierce_count = getattr(p, "pierce_count", 0) + int(value)
                p.piercing = True
            elif key == "bullet_count":
                p.bullet_count += int(value)
            elif key == "hitscan_range":
                p.hitscan_range = value
            elif key == "explosive_bullets":
                p.explosive_bullets = True
            elif key == "explosion_radius":
                p.explosion_radius = value
            elif key == "spray_mode":
                p.spray_mode = True
            elif key == "spread_angle":
                p.spread_angle_deg = value
            elif key == "homing_bullets":
                p.guided_shots = True
            elif key == "homing_strength":
                p.homing_strength = value
            
            # ===== BOUNCING =====
            elif key == "bounce_count":
                p.bounce_count = max(getattr(p, "bounce_count", 0), int(value))
            elif key == "bounce_damage_bonus":
                p.bounce_damage_bonus = getattr(p, "bounce_damage_bonus", 0) + value
            elif key == "bounce_homing":
                p.bounce_homing = True
            
            # ===== PLAYER STATS =====
            elif key == "move_speed_mult":
                p.speed *= value
                p.base_speed *= value
            elif key == "boost_recharge_mult":
                p.boost_recharge *= value
            elif key == "boost_invuln":
                p.boost_invuln = True
            elif key == "mag_size_bonus":
                p.mag_size += int(value)
                p.ammo = min(p.ammo + int(value), p.mag_size)
            elif key == "reload_speed_mult":
                p.reload_time /= value  # Faster reload = lower time
            elif key == "ammo_save_chance":
                p.ammo_save_chance = getattr(p, "ammo_save_chance", 0) + value
                p.homing_strength = value
            
            # ===== ELEMENTS =====
            elif key == "burn_chance":
                p.burn_chance = value
                p.bullet_status["burn"] = True
            elif key == "burn_dps":
                p.base_burn_dps = max(getattr(p, "base_burn_dps", 0), value)
            elif key == "burn_duration":
                p.burn_duration = value
            elif key == "burn_dps_mult":
                p.burn_bonus_mult *= value
            elif key == "burn_spread":
                p.burn_spread = True
            elif key == "burn_explosion":
                p.burn_explosion = True
            elif key == "explosion_damage":
                p.explosion_damage = value
            elif key == "burn_chain_explosions":
                p.burn_chain_explosions = value
            
            elif key == "freeze_chance":
                p.freeze_chance = value
                p.bullet_status["ice"] = True
            elif key == "slow_amount":
                p.slow_amount = value
            elif key == "freeze_duration":
                p.freeze_duration = value
            elif key == "frozen_damage_bonus":
                p.frozen_damage_bonus = getattr(p, "frozen_damage_bonus", 0) + value
            elif key == "shatter_on_death":
                p.shatter_on_death = True
            elif key == "shatter_damage":
                p.shatter_damage = value
            elif key == "deep_freeze":
                p.deep_freeze = True
            elif key == "shatter_chain":
                p.shatter_chain = value
            
            elif key == "poison_chance":
                p.poison_chance = value
                p.bullet_status["poison"] = True
            elif key == "poison_dps":
                p.base_poison_dps = max(getattr(p, "base_poison_dps", 0), value)
            elif key == "poison_duration":
                p.poison_duration = value
            elif key == "poison_spread":
                p.poison_spread = True
            elif key == "spread_radius":
                p.spread_radius = value
            elif key == "poison_weaken":
                p.poison_weaken = value
            elif key == "poison_infinite_spread":
                p.poison_infinite_spread = True
            elif key == "poison_death_explosion":
                p.poison_death_explosion = True
            
            # ===== ORBS =====
            elif key == "orb_count":
                p.aura_unlocked = True  # Enable aura orb system
                p.aura_orb_count = max(getattr(p, "aura_orb_count", 0), int(value))
                p.rebuild_aura_orbs()
            elif key == "orb_damage":
                p.aura_orb_damage = value
            elif key == "orb_radius":
                p.aura_orb_radius = value
            elif key == "orb_speed_mult":
                p.aura_orb_speed *= value
            elif key == "orb_damage_mult":
                p.aura_orb_damage = int(p.aura_orb_damage * value)
            elif key == "orb_burn":
                if "fire" not in p.aura_orb_elements:
                    p.aura_orb_elements.append("fire")
            elif key == "orb_burn_dps":
                p.orb_burn_dps = value
            elif key == "orb_freeze":
                if "ice" not in p.aura_orb_elements:
                    p.aura_orb_elements.append("ice")
            elif key == "orb_slow":
                p.orb_slow = value
            elif key == "orb_poison":
                if "poison" not in p.aura_orb_elements:
                    p.aura_orb_elements.append("poison")
            elif key == "orb_poison_dps":
                p.orb_poison_dps = value
            elif key == "orb_all_elements":
                p.aura_orb_elements = ["fire", "ice", "poison"]
            elif key == "orb_trail":
                p.orb_trail = True
            elif key == "orb_trail_damage":
                p.orb_trail_damage = value
            elif key == "orb_pulse":
                p.orb_pulse = True
            
            # ===== DEFENSE - SHIELD =====
            elif key == "shield_active":
                p.shield_active = True
                # Initialize shield HP to match segments if not set
                if getattr(p, "shield_hp", 0) == 0:
                    p.shield_hp = getattr(p, "shield_segments", 1)
            elif key == "shield_segments":
                p.shield_segments = max(getattr(p, "shield_segments", 0), int(value))
                # Update HP to match segments
                if getattr(p, "shield_hp", 0) < int(value):
                    p.shield_hp = int(value)
            elif key == "shield_radius":
                p.shield_radius = value
            elif key == "shield_hp":
                p.shield_hp = getattr(p, "shield_hp", 1) + int(value)
            elif key == "shield_reflect":
                p.shield_reflect = True
            elif key == "shield_regen":
                p.shield_regen = True
            elif key == "shield_regen_time":
                p.shield_regen_time = value
            
            # ===== DEFENSE - HEALTH =====
            elif key == "max_hp":
                p.max_hearts += int(value)
                p.hearts = p.max_hearts
            elif key == "hp_regen":
                p.hp_regen = True
            elif key == "regen_interval":
                p.regen_interval = value
            elif key == "revive":
                p.revives = max(p.revives, int(value))
            elif key == "revive_full_hp":
                p.revive_full_hp = True
            
            # ===== DEFENSE - SPEED =====
            elif key == "move_speed_mult":
                p.speed *= value
                p.base_speed = p.speed
            elif key == "dash_ability":
                p.dash_ability = True
            elif key == "dash_cooldown":
                p.dash_cooldown = value
            elif key == "dodge_chance":
                p.dodge_chance = getattr(p, "dodge_chance", 0) + value
            elif key == "dash_trail":
                p.dash_trail = True
            
            # ===== VISION - GLARE =====
            elif key == "glare_active":
                p.glare_active = True
            elif key == "glare_interval":
                p.glare_interval = value
            elif key == "glare_damage":
                p.glare_damage = value
            elif key == "glare_damage_mult":
                p.glare_damage = int(getattr(p, "glare_damage", 20) * value)
            elif key == "glare_slow":
                p.glare_slow = value
            elif key == "glare_stun":
                p.glare_stun = True
            elif key == "glare_stun_duration":
                p.glare_stun_duration = value
            elif key == "glare_execute":
                p.glare_execute = value
            
            # ===== SUMMONS - DRONES (was Ghost) =====
            elif key == "drone_count":
                p.drone_count = getattr(p, "drone_count", 0) + int(value)
            elif key == "drone_damage":
                p.drone_damage = max(getattr(p, "drone_damage", 0), value)
            elif key == "drone_pierce":
                p.drone_pierce = True
            elif key == "drone_burn":
                p.drone_burn = True
            elif key == "drone_poison":
                p.drone_poison = True
            elif key == "drone_rapid_fire":
                p.drone_rapid_fire = True
            elif key == "drone_all_elements":
                p.drone_all_elements = True
                p.drone_burn = True
                p.drone_poison = True
            # Legacy ghost support
            elif key == "ghost_count":
                p.ghost_count = getattr(p, "ghost_count", 0) + int(value)
            elif key == "ghost_damage":
                p.ghost_damage = max(getattr(p, "ghost_damage", 0), value)
            elif key == "ghost_pierce":
                p.ghost_piercing = True
            elif key == "ghost_burn":
                p.ghost_burn = True
            elif key == "ghost_poison":
                p.ghost_poison = True
            elif key == "ghost_rapid_fire":
                p.ghost_rapid_fire = True
            elif key == "ghost_all_elements":
                p.ghost_all_elements = True
            
            # ===== SUMMONS - PHANTOMS (new ghost type) =====
            elif key == "phantom_count":
                p.phantom_count = getattr(p, "phantom_count", 0) + int(value)
            elif key == "phantom_damage":
                p.phantom_damage = getattr(p, "phantom_damage", 0) + value
            elif key == "phantom_slow":
                p.phantom_slow = True
            elif key == "phantom_lifesteal":
                p.phantom_lifesteal = True
            elif key == "phantom_speed":
                p.phantom_speed = value
            
            # ===== SUMMONS - DRAGON =====
            elif key == "dragon_egg":
                p.has_dragon_egg = True
            elif key == "dragon_hatch_time":
                p.dragon_hatch_time = value
            elif key == "dragon_active":
                p.dragon_active = True
                self.dragon_hatched = True  # Also mark as hatched
            elif key == "dragon_damage":
                p.dragon_damage = max(getattr(p, "dragon_damage", 0), value)
            elif key == "dragon_fire_breath":
                p.dragon_fire_breath = True
            elif key == "dragon_burn_dps":
                p.dragon_burn_dps = value
            elif key == "dragon_growth":
                p.dragon_growth = True
            elif key == "dragon_damage_growth":
                p.dragon_damage_growth = value
            elif key == "elder_dragon":
                p.elder_dragon = True
            elif key == "dragon_size":
                p.dragon_size = value
            
            # ===== SUMMONS - LENS =====
            elif key == "lens_count":
                p.lens_count = max(getattr(p, "lens_count", 0), int(value))
            elif key == "lens_multiply":
                p.lens_multiply = value
            elif key == "lens_bullet_mult":
                p.lens_bullet_mult = max(getattr(p, "lens_bullet_mult", 1), int(value))
            elif key == "lens_damage_bonus":
                p.lens_damage_bonus = getattr(p, "lens_damage_bonus", 0) + value
            elif key == "lens_split":
                p.lens_split = max(getattr(p, "lens_split", 1), int(value))
            elif key == "lens_enlarge":
                p.lens_enlarge = max(getattr(p, "lens_enlarge", 1.0), float(value))
            
            # ===== EVOLUTIONS =====
            elif key == "lightning_active":
                p.lightning_active = True
            elif key == "lightning_interval":
                p.lightning_interval = value
            elif key == "lightning_damage":
                p.lightning_damage = value
            elif key == "lightning_chain":
                p.lightning_chain = value
            elif key == "summon_count_mult":
                p.ghost_count = int(p.ghost_count * value)
            elif key == "summon_damage_mult":
                p.summon_damage_mult = getattr(p, "summon_damage_mult", 1.0) * value
    
    def _check_evolutions(self):
        """Check if any evolutions are now available."""
        available = get_available_evolutions(list(self.owned_upgrades))
        # Store for UI to access
        self.available_evolutions = available
    
    def update(self, dt: float, is_moving: bool = False, is_stationary: bool = False):
        """Update timed effects."""
        p = self.player
        
        # Siege mode - 40% chance not to use ammo when stationary
        if is_stationary and getattr(p, "siege_mode", False):
            p.siege_active = True
        else:
            p.siege_active = False
        
        # Dragon hatching (instant if hatch_time is 0 or very small)
        if p.has_dragon_egg and not self.dragon_hatched:
            if p.dragon_hatch_time <= 0.1:
                # Instant hatch for elder dragon or test mode
                self.dragon_hatched = True
                p.dragon_active = True
            else:
                self.dragon_age += dt
                if self.dragon_age >= p.dragon_hatch_time:
                    self.dragon_hatched = True
                    p.dragon_active = True
        
        # Dragon growth
        if getattr(p, "dragon_growth", False) and self.dragon_hatched:
            growth_time = getattr(self, "dragon_growth_time", 0) + dt
            self.dragon_growth_time = growth_time
            if growth_time >= 60.0:  # Every 60 seconds
                p.dragon_damage += getattr(p, "dragon_damage_growth", 5)
                self.dragon_growth_time = 0
        
        # HP Regen
        if getattr(p, "hp_regen", False):
            self.regen_timer += dt
            interval = getattr(p, "regen_interval", 30.0)
            if self.regen_timer >= interval:
                self.regen_timer = 0
                if p.hearts < p.max_hearts:
                    p.hearts += 1
        
        # Glare timer
        if getattr(p, "glare_active", False):
            self.glare_timer += dt
        
        # Lightning timer
        if getattr(p, "lightning_active", False):
            self.lightning_timer += dt
        
        # Shield regen
        if getattr(p, "shield_regen", False):
            if getattr(p, "shield_hp", 0) < getattr(p, "shield_segments", 1):
                self.shield_regen_timer += dt
                if self.shield_regen_timer >= getattr(p, "shield_regen_time", 10.0):
                    self.shield_regen_timer = 0
                    p.shield_hp = getattr(p, "shield_hp", 0) + 1
    
    def should_glare_fire(self) -> bool:
        """Check if glare should fire this frame."""
        p = self.player
        if not getattr(p, "glare_active", False):
            return False
        interval = getattr(p, "glare_interval", 5.0)
        if self.glare_timer >= interval:
            self.glare_timer = 0
            return True
        return False
    
    def should_lightning_fire(self) -> bool:
        """Check if lightning should fire this frame."""
        p = self.player
        if not getattr(p, "lightning_active", False):
            return False
        interval = getattr(p, "lightning_interval", 2.0)
        if self.lightning_timer >= interval:
            self.lightning_timer = 0
            return True
        return False
    
    def should_gale_fire(self) -> bool:
        """Check if gale effect should trigger."""
        p = self.player
        return getattr(p, "gale_active", False)
    
    def check_siege_ammo_save(self, is_stationary: bool) -> bool:
        """Check if siege mode should save ammo (40% chance when stationary)."""
        import random
        p = self.player
        if is_stationary and getattr(p, "siege_mode", False):
            return random.random() < 0.4
        return False
    
    def on_shot(self) -> dict:
        """Called when player fires. Returns any triggered effects."""
        import random
        p = self.player
        effects = {}
        
        # Lightning on shot
        if getattr(p, "lightning_active", False) and self.should_lightning_fire():
            effects["lightning"] = {
                "damage": getattr(p, "lightning_damage", 15),
                "area_mult": getattr(p, "lightning_area_mult", 1.0)
            }
        
        return effects
    
    def on_empty_mag(self) -> dict:
        """Called when magazine empties. Returns any triggered effects."""
        p = self.player
        effects = {}
        
        # Smite on empty mag
        if getattr(p, "smite_active", False):
            effects["smite"] = {
                "damage": getattr(p, "smite_damage", 50)
            }
        
        return effects
    
    def check_execute(self, hp_ratio: float) -> bool:
        """Check if enemy should be executed based on HP ratio."""
        p = self.player
        execute_threshold = getattr(p, "execute_threshold", 0)
        return execute_threshold > 0 and hp_ratio <= execute_threshold
    
    def check_dodge(self) -> bool:
        """Check if player dodges an attack."""
        import random
        p = self.player
        dodge_chance = getattr(p, "dodge_chance", 0)
        return dodge_chance > 0 and random.random() < dodge_chance
    
    def on_kill(self, enemy=None, enemy_was_cursed: bool = False, enemy_was_frozen: bool = False):
        """Called when an enemy is killed."""
        import random
        p = self.player
        self.kill_counter += 1
        
        # Ritual: +1% damage per 10 curse kills
        if enemy_was_cursed and getattr(p, "ritual_active", False):
            self.curse_kills += 1
            if self.curse_kills % 10 == 0:
                p.damage_mult = getattr(p, "damage_mult", 1.0) + 0.01
        
        # Shatter: frozen enemies explode
        if enemy_was_frozen and getattr(p, "shatter_active", False) and enemy:
            # 7% HP damage explosion handled by game.py
            pass
        
        # Kill clip: +5% reload speed per kill
        if getattr(p, "kill_clip_active", False):
            self.kill_clip_stacks = min(getattr(self, "kill_clip_stacks", 0) + 1, 10)
        
        # Bloodsuckers: summon kills can drop healing
        if getattr(p, "bloodsuckers_active", False):
            if random.random() < 0.1:  # 10% chance
                pass  # Healing pickup spawned by game.py
    
    def on_hit(self):
        """Called when player takes damage."""
        p = self.player
        
        # Soul link: lose soul = enemies -80% HP
        if getattr(p, "soul_link_active", False):
            # Effect handled by game.py
            pass
    
    def on_xp_pickup(self):
        """Called when player picks up XP."""
        p = self.player
        
        # Excitement: +50% fire rate for 1s after XP pickup
        if getattr(p, "excitement_active", False):
            p.excitement_timer = 1.0
    
    def on_reload(self):
        """Called when player reloads."""
        p = self.player
        # Reset kill clip stacks on reload
        self.kill_clip_stacks = 0
