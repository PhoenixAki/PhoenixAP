import asyncio
import copy
import logging
import math
import pkgutil
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, override

import orjson

import Utils
from BaseClasses import Item, ItemClassification, MultiWorld, Region, CollectionState
from Options import OptionError, OptionSet, NamedRange, Choice, Range
from rule_builder.rules import Has, Rule, True_, And, False_, HasAny
from worlds.AutoWorld import World, WebWorld
from worlds.LauncherComponents import icon_paths
from .data.consts import LEVEL_SHOP_LOOKUP, REALM_LEVEL_LOOKUP, REALM_LEVEL_LISTS, LoggingLevel, BOSS_IDS, DARK_GEM_IDS, \
    LIGHT_GEM_IDS, DRAGON_EGG_IDS, FIREWORK_IDS, SHOP_ITEM_IDS, LOCKED_CHEST_IDS, ELDER_ABILITY_IDS, BYRD_IDS, \
    BLINK_IDS, TURRET_IDS, SPARX_IDS, SHOP_PAD_LIST, LEVEL_TO_REALM
from .options import MovementRandomization, SpyroAHTOptions, StartingBreaths, spyro_options_groups

icon_paths['spyro_aht'] = f'ap:{__name__}/icons/dark_gem_icon.png'

minigame_locs = [
        "DV: Dragon Egg from Sgt. Byrd", "DV: Light Gem from Sgt. Byrd",
        "CD: Dragon Egg from Sgt. Byrd", "CD: Light Gem from Sgt. Byrd",
        "IC: Dragon Egg from Sgt. Byrd", "IC: Light Gem from Sgt. Byrd",
        "MM: Dragon Egg from Sgt. Byrd", "MM: Light Gem from Sgt. Byrd",
        "CS: Dragon Egg from Blink", "CS: Light Gem from Blink",
        "CR: Dragon Egg from Blink", "CR: Light Gem from Blink",
        "FV: Dragon Egg from Blink", "FV: Light Gem from Blink",
        "DM: Dragon Egg from Blink", "DM: Light Gem from Blink",
        "DF: Dragon Egg from Sparx", "DF: Light Gem from Sparx",
        "SR: Dragon Egg from Sparx", "SR: Light Gem from Sparx",
        "GG: Dragon Egg from Sparx", "GG: Light Gem from Sparx",
        "MFb: Dragon Egg from Sparx", "MFb: Light Gem from Sparx",
        "CS: Dragon Egg from Fredneck", "CS: Light Gem from Fredneck",
        "CR: Dragon Egg from Turtle Mother", "CR: Light Gem from Turtle Mother",
        "FV: Dragon Egg from Peggy", "FV: Light Gem from Peggy",
        "SB: Dragon Egg from Wally", "SB: Light Gem from Wally"
]

# used for UT custom sorting
id_lookup = {"Starter Checks": "A", "Moneybags": "B", "DV": "C", "CS": "D", "DF": "E", "CR": "F", "CD": "G", "SR": "H", "FV": "I", "GG": "J", "IC": "K", "SB": "L", "MM": "M", "MFt": "N", "MFb": "O", "DM": "P", "RL": "Q"}

###############WORLD CLASS HELPER FUNCTIONS###############
def _load_file(file: str) -> Any:
    return orjson.loads(pkgutil.get_data(__name__, "data/" + file).decode("utf-8")) # type: ignore


def create_item_groups(item_data) -> dict[str, set[str]]:
    item_groups = defaultdict(set)
    for item in item_data:
        item_groups[item['group']].add(item['name'])
        
    return item_groups


def _location_name_to_id(location_data) -> dict[str, int]:
    loc_name_to_id = {}
    for region in location_data.values():
        for location in region['locations']:
            loc_name_to_id[location['name']] = location['id']
            
    return loc_name_to_id
loc_names_to_ids = _location_name_to_id(_load_file("locations.json"))

def create_location_groups(location_data) -> dict[str, set[str]]:
    level_lookup = {
        "Starter Checks": "Starter Checks", "Moneybags": "Shop Items",
        "DV": "Dragon Village", "CS": "Crocovile Swamp", "DF": "Dragonfly Falls",
        "CR": "Coastal Remains", "CD": "Cloudy Domain", "SR": "Sunken Ruins",
        "FV": "Frostbite Village", "GG": "Gloomy Glacier", "IC": "Ice Citadel",
        "SB": "Stormy Beach", "MM": "Molten Mount", "MFt": "Magma Falls Top", "MFb": "Magma Falls Bottom", "DM": "Dark Mine", "RL": "Red's Laboratory",
    }
    
    loc_groups = defaultdict(set)
    for region in location_data.values():
        for location in region['locations']:
            abbreviation = location['name'].split(': ')[0]
            level = level_lookup[abbreviation]  # may be starter checks or shop items. Otherwise, guaranteed to be a level name
            realm = "N/A"  # only here to keep Python from a warning below. Only stays N/A for starter checks and shop items, and goes unused in those cases
            for realm_lookup in REALM_LEVEL_LISTS.keys():
                if level in REALM_LEVEL_LISTS[realm_lookup]:
                    realm = realm_lookup
                    break
            
            # level groups e.g. "Dragon Village", "Coastal Remains"
            loc_groups[level].add(location['name'])
            
            # the 5 main collectibles
            for key in [": Dark Gem", ": Dragon Egg", ": Light Gem", "Locked Chest", ": Firework"]:
                if key in location['name']:
                    key = key.replace(": ", "")
                    loc_groups[f"All {key}s"].add(location['name'])
                    loc_groups[f"{level} {key}s"].add(location['name'])
                    loc_groups[f"{realm} {key}s"].add(location['name'])
            # 3 of the 4 minigame types
            for key in ["from Sgt. Byrd", "from Blink", "from Sparx"]:
                if key in location['name']:
                    key = key.replace("from ", "")
                    loc_groups[f"{key} Minigames"].add(location['name'])
                    loc_groups[f"All Minigames"].add(location['name'])
                    loc_groups[f"{realm} Minigames"].add(location['name'])
            # turrets separate because the names don't say "Turret"        
            for npc in ["Fredneck", "Turtle Mother", "Peggy", "Wally"]:
                if f"from {npc}" in location['name']:
                    loc_groups["Turret Minigames"].add(location['name'])
                    loc_groups["All Minigames"].add(location['name'])
                    loc_groups[f"{realm} Minigames"].add(location['name'])
            # bosses
            if "Defeat" in location['name'] or "Breath from" in location['name']:  # bosses
                loc_groups["All Bosses"].add(location['name'])
            # light gem doors
            if "Light Gem door" in location['name']:
                loc_groups["Light Gem Doors"].add(location['name'])
                loc_groups[f"{level} Light Gem Door"].add(location['name'])
            # ball gadget checks (including the firework after it in CD since it requires Ball Gadget to reach)
            if region['name'] in ["CDBallGadget", "MFBallGadget"]:
                loc_groups["Ball Gadget"].add(location['name'])
                loc_groups["All Gadgets"].add(location['name'])
            # supercharge checks
            if "supercharge" in location['name'] or region['name'] in ["FVReturnFromIC", "ICUseSupercharge"]:
                loc_groups["Supercharge Gadget"].add(location['name'])
                loc_groups["All Gadgets"].add(location['name'])
            # invincibility checks
            if region['name'] in ["SRAfterSwim2", "SRDepthsUpper", "SRToxicSwim2", "SRToxicSwimAbove", "DMLGDoorPastGnorc", "RLNorthEast2"]:
                loc_groups["Invincibility Gadget"].add(location['name'])
                loc_groups["All Gadgets"].add(location['name'])
    return loc_groups


class SpyroAHTWeb(WebWorld):
    option_groups = spyro_options_groups

class SpyroAHTWorld(World):
    """
    Spyro: A Hero's Tail is a 3D platformer and collect-a-thon released in 2004 for the Xbox, Playstation 2 and GameCube.
    """
    ###############WORLD SETUP & INITIALIZATION###############
    game = "Spyro: A Hero's Tail"
    origin_region_name = "START"

    options_dataclass = SpyroAHTOptions
    options: SpyroAHTOptions
    web = SpyroAHTWeb()
    
    item_data = _load_file("items.json")
    item_name_to_id = {i['name']: i['id'] for i in item_data}
    item_name_groups = create_item_groups(item_data)
    
    location_data = _load_file("locations.json")
    location_name_to_id = _location_name_to_id(location_data)
    location_name_groups = create_location_groups(location_data)
    
    ut_can_gen_without_yaml = True

    def __init__(self, multiworld: MultiWorld, player: int):
        super().__init__(multiworld, player)
        self.multiworld.early_items[self.player]["Double Jump"] = 1

        self.light_gem_doors = [70, 20, 95, 45]
        self.boss_lairs = [10, 20, 30, 40]
        self.gadget_costs = [8, 24, 40]  # ball, invincibility, supercharge
        self.classifications = {i['name']: ItemClassification(i['classification']) for i in self.item_data}
        self.shop_costs = []
        self.filler_items: dict[str, list[str]] = {}
        self.goals_dict: dict[str, list[int]] = defaultdict(list[int])  # dict of enabled goal name -> list of location ids. Sent to client via slot data
    
    ###############HELPER METHODS + OVERRIDES###############
    def log(self, message, level: LoggingLevel):
        """Logs messages from generation."""
        if self.options.logging_level.value >= level:
            logging.info(f"[Spyro AHT] LOG-{level.name}: {message}")
    
    def create_item(self, name: str) -> Item:
        """Returns an Item object, given an item name."""
        self.log(f"Created item {name} with classification {self.classifications[name]} and ID {self.item_name_to_id[name]}.", LoggingLevel.MAXIMUM)
        return Item(name, self.classifications[name], self.item_name_to_id[name], self.player)
    
    def custom_ut_sort(self, region_label: str, location_label: str) -> str | int:
        """Sorts AHT locations in UT based on vanilla game level order -> alphabetical by region -> alphabetical by location."""
        level_acronym, rest_of_name = location_label.split(": ")
        level_id = id_lookup[level_acronym]
        return f"{level_id} {region_label} {rest_of_name}"

    def get_filler_item_name(self):
        """Override of World.get_filler_item_name which returns a random filler item name.
        Used whenever start_inventory_from_pool is used."""
        items = self.random.choice(list(self.filler_items.values()))
        random_choice = self.random.choice(items)
        self.log(f"Replacing a start_inventory_from_pool item with \"{random_choice}\".", LoggingLevel.HIGH)
        return random_choice
            
    def collect(self, state: "CollectionState", item: "Item") -> bool:
        """Override of World.collect which additionally handles gem events and shop unlocks."""
        name = self.collect_item(state, item)
        if name:
            if "Unlock" not in item.name:
                state.add_item(name, self.player)
                if "Gems" in item.name and "VictoryCon" not in item.name:  # gem events
                    gem_amount = int(item.name.split(" ")[0])
                    if "Blink minigames" in item.name:
                        state.add_item("Blink Gems", item.player, count=gem_amount)
                    elif "[enemy]" in item.name:
                        state.add_item("Non-Blink Enemies", item.player, count=gem_amount)
                    else:
                        state.add_item("Other Gems", item.player, count=gem_amount)
            else:  # handle shop unlocks separately
                choice = self.options.open_world_mode.value
                if choice == 2:  # randomized
                    state.add_item(item.name.replace(" Shop Unlock", ""), self.player)
                elif choice == 3 or choice == 4:  # progressive and reverse progressive
                    if "Depot" in item.name:  # a manually-unlocked starting realm shop. always collected before the rest
                        state.add_item(item.name.replace(" Shop Unlock", ""), self.player)
                    else:  # regular progressive or reverse progressive item
                        adjusted_name = item.name.replace("Progressive ", "")
                        level = adjusted_name.split(" - ")[0]
                        shops = LEVEL_SHOP_LOOKUP[level].copy()
                        if choice == 4: shops.reverse()
                        for shop in shops:
                            if not state.has(f"{level} - {shop}", self.player):
                                state.add_item(f"{level} - {shop}", self.player)
                                break
                elif choice == 5:  # full levels
                    if "Depot" in item.name:  # a manually-unlocked starting realm shop. always collected before the rest
                        state.add_item(item.name.replace(" Shop Unlock", ""), self.player)
                    else:
                        level = item.name.split(" - ")[0]
                        for shop in LEVEL_SHOP_LOOKUP[level]:
                            if not state.has(f"{level} - {shop}", self.player):
                                state.add_item(f"{level} - {shop}", self.player)
                elif choice == 6:  # full realms
                    realm = item.name.split(" - ")[0]
                    for level in REALM_LEVEL_LOOKUP[realm]:
                        for shop in LEVEL_SHOP_LOOKUP[level]:
                            if not state.has(f"{level} - {shop}", self.player):
                                state.add_item(f"{level} - {shop}", self.player)
            return True
        return False

    def remove(self, state: "CollectionState", item: "Item") -> bool:
        """Override of World.remove which additionally handles gem events and shop unlocks."""
        name = self.collect_item(state, item, True)
        if name:
            if "Unlock" not in item.name:
                state.remove_item(name, self.player)
                if "Gems" in item.name and "VictoryCon" not in item.name:  # gem events
                    gem_amount = int(item.name.split(" ")[0])
                    if "Blink minigames" in item.name:
                        state.remove_item("Blink Gems", item.player, count=gem_amount)
                    elif "[enemy]" in item.name:
                        state.remove_item("Non-Blink Enemies", item.player, count=gem_amount)
                    else:
                        state.remove_item("Other Gems", item.player, count=gem_amount)
            else:  # handle shop unlocks separately
                choice = self.options.open_world_mode.value
                if choice == 2:  # randomized
                    state.remove_item(item.name.replace(" Shop Unlock", ""), self.player)
                elif choice == 3 or choice == 4:  # progressive and reverse progressive
                    if "Depot" in item.name:  # a manually-unlocked starting realm shop. always collected before the rest
                        state.remove_item(item.name.replace(" Shop Unlock", ""), self.player)
                    else:  # regular progressive or reverse progressive item
                        adjusted_name = item.name.replace("Progressive ", "")
                        level = adjusted_name.split(" - ")[0]
                        shops = LEVEL_SHOP_LOOKUP[level].copy()
                        if choice == 4: shops.reverse()
                        for shop in shops:
                            if not state.has(f"{level} - {shop}", self.player):
                                state.remove_item(f"{level} - {shop}", self.player)
                                break
                elif choice == 5:  # full levels
                    if "Depot" in item.name:  # a manually-unlocked starting realm shop. always collected before the rest
                        state.remove_item(item.name.replace(" Shop Unlock", ""), self.player)
                    else:
                        level = item.name.split(" - ")[0]
                        for shop in LEVEL_SHOP_LOOKUP[level]:
                            if not state.has(f"{level} - {shop}", self.player):
                                state.remove_item(f"{level} - {shop}", self.player)
                elif choice == 6:  # full realms
                    realm = item.name.split(" - ")[0]
                    for level in REALM_LEVEL_LOOKUP[realm]:
                        for shop in LEVEL_SHOP_LOOKUP[level]:
                            if not state.has(f"{level} - {shop}", self.player):
                                state.remove_item(f"{level} - {shop}", self.player)
            return True
        return False
    
    ###############GENERATION PROCESS OVERRIDES###############
    def generate_early(self) -> None:
        passthrough = getattr(self.multiworld, "re_gen_passthrough", {})
        if isinstance(passthrough, dict) and self.game in passthrough:
            self._apply_slot_data(passthrough[self.game])
        
        self.log("Checking for common YAML option/setting issues, and setting up costs. All auto_corrections adjustments are done here.", LoggingLevel.LOW)
        
        if self.options.open_world_mode.value != 1 and self.options.starting_realms.value == {"Icy Wilderness"}:
            if self.options.shop_randomization.value == 0 and len(self.options.movement_randomization.value) == 0:
                if self.options.auto_corrections == 2:  # fix_major specific
                    self.log("Major Warning: Can't have Icy Wilderness as the only starting realm if shop randomization is disabled and all 3 movement abilities are unrandomized. Fixing by changing starting realm to Dragon Kingdom.", LoggingLevel.WARNING)
                    self.options.starting_realms.value = {"Icy Wilderness"}
                else:
                    raise OptionError("Can't have Icy Wilderness as the only starting realm if shop randomization is disabled and all 3 movement abilities are unrandomized. Fix this, or set auto_corrections to fix_major.")
            
        bad_condition = self.options.teleport_across_realms.value == 0 and self.options.open_world_mode.value != 0
        if bad_condition and self.options.auto_corrections.value >= 1:  # fix_minor
            self.log("Minor Warning: teleport_across_realms was disabled, but needs to be on when using open world mode to prevent possible softlocks. Fixing by enabling teleport_across_realms.", LoggingLevel.WARNING)
            self.options.teleport_across_realms.value = 1
        elif bad_condition:
            raise OptionError("teleport_across_realms was disabled, but needs to be on when using open world mode to prevent possible softlocks. Fix this, or set auto_corrections to at least fix_minor.")
        
        bad_condition = len(self.options.starting_breaths.value) > 1 and "None" in self.options.starting_breaths.value  # "none" alongside breath choices
        if bad_condition and self.options.auto_corrections.value >= 1:  # fix_minor
            self.log("Minor Warning: Starting breath list cannot contain breaths and \"None\". Fixing by removing the \"None\".", LoggingLevel.WARNING)
            self.options.starting_breaths.value.remove("None")
        elif bad_condition:
            raise OptionError("Starting breath list cannot contain breaths and \"None\". Fix this, or set auto_corrections to at least fix_minor.")
        
        self.check_breaths_and_realms(self.options.starting_breaths, ["Fire Breath", "Electric Breath", "Water Breath", "Ice Breath"], "breath")
        self.check_breaths_and_realms(self.options.starting_realms, ["Dragon Kingdom", "Lost Cities", "Icy Wilderness", "Volcanic Isle"], "realm")
        
        if self.options.trap_percentage.value < 100: self.check_filler_and_traps(self.options.filler_items, "Filler", "Shinies")
        if self.options.trap_percentage.value > 0: self.check_filler_and_traps(self.options.trap_items, "Trap", "Spam Call")
        
        self.check_lists(self.options.boss_goal, "boss_goal", "bosses")
        self.check_lists(self.options.elders_goal, "elders_goal", "elders")
        
        # minigames goal
        for key in self.options.minigames_goal.valid_keys:
            choice = self.options.minigames_goal.value[key]
            bad_condition = choice in ["0", "1", "2", "3", "4", "5", "6", "7", "8"]
            if bad_condition and self.options.auto_corrections.value >= 1:
                self.log(f"Minor Warning: \"{choice}\" was entered for {key} in minigames_goal, but should've been entered as a number (no quotes). Fixing by auto-converting \"{choice}\" to {int(choice)}.", LoggingLevel.WARNING)
                self.options.minigames_goal.value[key] = int(choice)
            elif bad_condition:
                raise OptionError(f"Minor Warning: \"{choice}\" was entered for {key} in minigames_goal, but should've been entered as a number (no quotes). Fix this, or set auto_corrections to at least fix_minor.")
            
            bad_condition = self.options.minigames_goal.value[key] not in [0, 1, 2, 3, 4, 5, 6, 7, 8, "random-on", "random-off"]
            if bad_condition and self.options.auto_corrections.value >= 1:
                self.log(f"Minor Warning: Invalid entry for {key} in minigames_goal. Must be a number 0-8, \"random-on\", or \"random-off\". Fixing by setting {key} to 0.", LoggingLevel.WARNING)
                self.options.minigames_goal.value[key] = 0
            elif bad_condition:
                raise OptionError(f"Minor Warning: Invalid entry for {key} in minigames_goal. Must be a number 0-8, \"random-on\", or \"random-off\". Fix this, or set auto_corrections to at least fix_minor.")
            
            # if here, it's a safe value. 0-8 is ignored and processed in handle_goaling. Just need to figure out random choice here
            if self.options.minigames_goal.value[key] == "random-on":
                self.options.minigames_goal.value[key] = self.random.randint(1, 8)
                self.log(f"\"random-on\" was requested for {key} for minigames_goal. {self.options.minigames_goal.value[key]} was chosen.", LoggingLevel.MEDIUM)
            elif self.options.minigames_goal.value[key] == "random-off":
                coin_flip = self.random.randint(0, 1)  # 0 = off, 1 = on (and do a new random spin of 1-8)
                if coin_flip == 1:
                    self.options.minigames_goal.value[key] = self.random.randint(1, 8)
                    self.log(f"\"random-off\" was requested for {key} for minigames_goal. 50% chance resulted in it being enabled with a requirement of {self.options.minigames_goal.value[key]}.", LoggingLevel.MEDIUM)
                elif coin_flip == 0:
                    self.options.minigames_goal.value[key] = 0
                    self.log(f"\"random-off\" was requested for {key} for minigames_goal. 50% chance resulted in it being disabled.", LoggingLevel.MEDIUM)
        
        # these 2 *could* be extracted to another helper checking method but eh. They're just slightly too different
        bad_condition = self.options.fireworks_goal.value > 0 and self.options.firework_checks.value == 0  # firework goal but no firework checks
        if bad_condition and self.options.auto_corrections.value >= 1:  # fix_minor
            self.log("Minor Warning: Fireworks was enabled as a goal, but firework_checks is disabled. Fixing by enabling firework_checks.", LoggingLevel.WARNING)
            self.options.firework_checks.value = 1
        elif bad_condition:
            raise OptionError("Fireworks was enabled as a goal, but firework_checks is disabled. Fix this, or set auto_corrections to at least fix_minor.")
        
        bad_condition = self.options.shop_items_goal.value > 0 and self.options.shop_randomization.value == 0
        if bad_condition and self.options.auto_corrections.value == 1:  # fix_minor specific
            self.log("Minor Warning: shop_items_goal was enabled as a goal, but shop_randomization is disabled. Fixing by disabling shop_items_goal.", LoggingLevel.WARNING)
            self.options.shop_items_goal.value = 0
        elif bad_condition and self.options.auto_corrections.value == 2:  # fix_major specific
            self.log("Major Warning: shop_items_goal was enabled as a goal, but shop_randomization is disabled. Fixing by enabling shop_randomization.", LoggingLevel.WARNING)
            self.options.shop_randomization.value = 1
        elif bad_condition:
            raise OptionError("shop_items_goal was enabled as a goal, but shop_randomization is disabled. Fix this, or set auto_corrections to at least fix_minor.")
        
        bad_condition = self.options.shop_items_goal.value > self.options.shop_item_count.value
        if bad_condition and self.options.auto_corrections.value >= 1:  # fix_minor
            self.log("Minor Warning: shop_items_goal was enabled as a goal, but is higher than shop_item_count. Fixing by lowering shop_items_goal to match shop_item_count.", LoggingLevel.WARNING)
            self.options.shop_items_goal.value = self.options.shop_item_count.value
        elif bad_condition:
            raise OptionError("shop_items_goal was enabled as a goal, but is higher than shop_item_count. Fix this, or set auto_corrections to at least fix_minor.")

        self.check_eggs_and_gems(self.options.light_gems_goal, "light_gems_goal", 85, 15, self.options.exclude_chest_items >= 2)
        self.check_eggs_and_gems(self.options.dragon_eggs_goal, "dragon_eggs_goal", 64, 16, self.options.exclude_chest_items.value in [1, 3])
        
        self.gadget_costs = self.setup_costs(self.options.randomize_gadget_costs, self.options.gadget_cost_min, self.options.gadget_cost_max, self.gadget_costs, "gadget")
        self.log(f"Gadget Costs: {", ".join(str(cost) for cost in self.gadget_costs)}.", LoggingLevel.MEDIUM)
        self.light_gem_doors = self.setup_costs(self.options.randomize_light_gem_door_costs, self.options.light_gem_door_cost_min, self.options.light_gem_door_cost_max, self.light_gem_doors, "Light Gem door")
        self.log(f"Light Gem Door Costs: {", ".join(str(cost) for cost in self.light_gem_doors)}.", LoggingLevel.MEDIUM)
        self.boss_lairs = self.setup_costs(self.options.randomize_boss_lair_door_costs, self.options.boss_lair_door_cost_min, self.options.boss_lair_door_cost_max, self.boss_lairs, "boss lair")
        
        # boss lair forcing
        self.log(f"Checking if boss lair costs need forcing via boss_lair_forcing.", LoggingLevel.LOW)
        lookup = ["Gnasty Gnorc", "Ineptune", "Red", "Mecha-Red"]
        forcing = self.options.boss_lair_forcing.value
        if forcing != 0:
            if 1 <= self.options.boss_lair_forcing.value <= 4: goal_boss_indices = [forcing - 1]
            else: goal_boss_indices = [lookup.index(boss) for boss in lookup if boss in self.options.boss_goal.value]
            non_goal_boss_indices = [index for index in [0, 1, 2, 3] if index not in goal_boss_indices]

            if len(goal_boss_indices) == 4: self.log("boss_lair_forcing is set to automatic, but all 4 bosses are part of goal. Skipping cost swapping.", LoggingLevel.HIGH)
            elif len(goal_boss_indices) == 0: self.log("boss_lair_forcing is set to automatic, but you have no goal bosses. Skipping cost swapping.", LoggingLevel.HIGH)
            else:
                for goal_boss_index in goal_boss_indices:
                    goal_boss_cost = self.boss_lairs[goal_boss_index]

                    # find highest-costing non-goal boss
                    highest_non_goal_index = non_goal_boss_indices[0]
                    for non_goal_boss_index in non_goal_boss_indices:
                        if self.boss_lairs[non_goal_boss_index] > self.boss_lairs[highest_non_goal_index]: highest_non_goal_index = non_goal_boss_index
                    highest_non_goal_cost = self.boss_lairs[highest_non_goal_index]

                    # swap if needed
                    if self.boss_lairs[goal_boss_index] < highest_non_goal_cost:
                        self.log(f"Swapping {lookup[goal_boss_index]}'s cost of {goal_boss_cost} and {lookup[highest_non_goal_index]}'s cost of {highest_non_goal_cost} as the former is smaller.", LoggingLevel.HIGH)
                        self.boss_lairs[goal_boss_index] = highest_non_goal_cost
                        self.boss_lairs[highest_non_goal_index] = goal_boss_cost
                    else:
                        self.log(f"Skipping swapping {lookup[goal_boss_index]}'s cost of {goal_boss_cost} and {lookup[highest_non_goal_index]}'s cost of {highest_non_goal_cost} as the former is already larger.", LoggingLevel.HIGH)
        self.log(f"Boss Lair Costs (in Dark Gems): Gnasty Gnorc requires {self.boss_lairs[0]}, Ineptune requires {self.boss_lairs[1]}, Red requires {self.boss_lairs[2]}, and Mecha-Red requires {self.boss_lairs[3]}.", LoggingLevel.MEDIUM)

    def _apply_slot_data(self, slot_data: dict[str, Any]) -> None:
        self._ut_active = True

        self.options.death_link.value = slot_data['death_link']
        self.options.death_link_amnesty.value = slot_data['death_link_amnesty']

        self.options.logging_level.value = slot_data['logging_level']
        self.options.auto_corrections.value = slot_data['auto_corrections']

        self.options.boss_goal.value = slot_data['boss_goal']
        self.options.dark_gems_goal.value = slot_data['dark_gems_goal']
        self.options.light_gems_goal.value = slot_data['light_gems_goal']
        self.options.dragon_eggs_goal.value = slot_data['dragon_eggs_goal']
        self.options.fireworks_goal.value = slot_data['fireworks_goal']
        self.options.shop_items_goal.value = slot_data['shop_items_goal']
        self.options.locked_chests_goal.value = slot_data['locked_chests_goal']
        self.options.elders_goal.value = slot_data['elders_goal']
        self.options.minigames_goal.value = slot_data['minigames_goal']
        self.options.exclude_chest_items.value = slot_data['exclude_chest_items']

        self.options.open_world_mode.value = slot_data['open_world_mode']
        self.options.firework_checks.value = slot_data['firework_checks']
        self.options.vanilla_minigame_rewards.value = slot_data['vanilla_minigame_rewards']
        self.options.trap_percentage.value = slot_data['trap_percentage']
        self.options.filler_items.value = slot_data['filler_items']
        self.options.trap_items.value = slot_data['trap_items']
        self.options.trap_length.value = slot_data['trap_length']

        self.options.starting_breaths.value = slot_data['starting_breaths']
        self.options.movement_randomization.value = slot_data['movement_randomization']
        self.options.starting_realms.value = slot_data['starting_realms']

        self.options.shop_randomization.value = slot_data['shop_randomization']
        self.options.key_rings.value = slot_data['key_rings']
        self.options.shop_item_count.value = slot_data['shop_item_count']
        self.options.shop_logic.value = slot_data['shop_logic']
        self.options.blink_gems.value = slot_data['blink_gems']
        self.options.non_blink_enemies.value = slot_data['non_blink_enemies']
        self.options.other_gems.value = slot_data['other_gems']
        self.options.double_gems.value = slot_data['double_gems']

        self.boss_lairs = slot_data['boss_lair_costs']
        self.light_gem_doors = slot_data['light_gem_door_costs']
        self.gadget_costs = slot_data['gadget_costs']

        self.options.pause_menu_patch.value = slot_data['pause_menu_patch']
        self.options.shop_pad_proximity_activation.value = slot_data['shop_pad_proximity_activation']
                
    def check_breaths_and_realms(self, option: OptionSet, choices: list, error_txt: str):
        if len(option.value) == 0:
            random_choice = self.random.choice(choices)
            self.log(f"Starting {error_txt} list is empty. {random_choice} was chosen at random.", LoggingLevel.MEDIUM)
            option.value.add(random_choice)
        
    def check_filler_and_traps(self, option: OptionSet, error_txt_1: str, error_txt_2: str):
        bad_condition = len(option.value) == 0  # empty list
        if bad_condition and self.options.auto_corrections.value >= 1:  # fix_minor
            self.log(f"Minor Warning: {error_txt_1} item list cannot be empty when {error_txt_1.lower()}s are enabled. Fixing by adding \"{error_txt_2}\".", LoggingLevel.WARNING)
            option.value.add(error_txt_2)
        elif bad_condition:
            raise OptionError(f"{error_txt_1} item list cannot be empty when {error_txt_1.lower()}s are enabled. Fix this, or set auto_corrections to at least fix_minor.")
    
    def check_lists(self, option: OptionSet, error_text_1: str, error_text_2: str):
        if "Random" in option.value:  # 3 cases to deal with here, all relate to having Random in the list
            choices = [choice for choice in option.valid_keys if choice in option.value and choice != "Random"]
            rand_count = 0
            if len(choices) == 0:  # random is the only thing in the list
                rand_count = self.random.randint(1, 4)
            elif 1 <= len(choices) <= 3:  # there's other things in the list
                rand_count = self.random.randint(1, 4 - len(choices))
            elif len(choices) == 4:
                if self.options.auto_corrections >= 1:  # fix_minor
                    self.log(f"Minor Warning: \"Random\" was entered into {error_text_1}, but all 4 {error_text_2} were chosen alongside it. Fixing by removing the \"Random\".", LoggingLevel.WARNING)
                    option.value.remove("Random")
                else:
                    raise OptionError(f"\"Random\" was entered into {error_text_1}, but all 4 {error_text_2} were chosen alongside it. Fix this, or set auto_corrections to at least fix_minor.")

            if rand_count > 0:
                option.value.remove("Random")
                available_choices = [choice for choice in option.valid_keys if choice not in choices and choice != "Random"]
                while rand_count > 0:
                    rand_choice = self.random.choice(available_choices)
                    option.value.add(rand_choice)
                    available_choices.remove(rand_choice)
                    rand_count -= 1
                self.log(f"\"Random\" was requested for {error_text_1}. Random choice(s): {", ".join(option.value)}.", LoggingLevel.MEDIUM)
                    
    def check_eggs_and_gems(self, option: Range, name: str, maximum: int, count: int, error: bool):
        bad_condition = option.value > maximum and error
        if bad_condition and self.options.auto_corrections.value >= 1:  # fix_minor
            self.log(f"Minor Warning: {name} was set higher than {maximum}, but {count} from chests are excluded from goals via exclude_chest_items. Fixing by lowering {name} by {count}.", LoggingLevel.WARNING)
            option.value -= count
        elif bad_condition:
            raise OptionError(f"{name} was set higher than {maximum}, but {count} from chests are excluded from goals via exclude_chest_items. Fix this, or set auto_corrections to at least fix_minor.")
    
    def setup_costs(self, option: Choice, opt_min: Range, opt_max: Range, costs: list[int], cost_type: str) -> list[int]:  # returns costs
        self.log(f"Setting up and checking for issues with {cost_type} costs.", LoggingLevel.LOW)
        if option.value == 0:  # default
            return costs
        if option.value == 2:  # shuffled
            self.random.shuffle(costs)
            return costs
        elif option.value == 1:  # randomized
            cost_min, cost_max = opt_min.value, opt_max.value
            rand_count = 3 if cost_type == "gadget" else 4
            bad_condition = opt_min > opt_max
            if bad_condition and self.options.auto_corrections.value >= 1:  # fix_minor
                self.log(f"Minor Warning: {opt_min.display_name} of {cost_min} is greater than {cost_max}. Fixing by swapping them.", LoggingLevel.WARNING)
                cost_min, cost_max = cost_max, cost_min
            elif bad_condition:
                raise OptionError(f"{opt_min.display_name} of {cost_min} is greater than {cost_max}. Fix this, or set auto_corrections to at least fix_minor.")
            return [self.random.randint(cost_min, cost_max) for _ in range(rand_count)]
        else:
            self.log("Something has gone TERRIBLY wrong if you are seeing this log message. Report to devs ASAP.", LoggingLevel.WARNING)
            return [0]  # something has gone VERY wrong, this should never happen and is only here to shush Python warnings
        
    def create_regions(self):
        self.log("Setting up regions and locations.", LoggingLevel.LOW)
        self.multiworld.regions.extend(Region(r['name'], self.player, self.multiworld) for r in self.location_data.values())
        self.log("Regions created.", LoggingLevel.HIGH)
        
        for region_name, region_data in self.location_data.items():
            for entrance in region_data['entrances']:
                region_from, region_to = entrance['name'].split(" -> ")
                rule = self.rule_from_dict(entrance['access_rule'])
                self.get_region(region_from).connect(self.get_region(region_to), f"{region_from} => {region_to}", rule)
                self.log(f"Connected region {region_from} to region {region_to} with rule {rule}.", LoggingLevel.MAXIMUM)
        self.log("Regions connected.", LoggingLevel.HIGH)

        for region_data in self.location_data.values():
            new_locations = {}
            for location_data in region_data['locations']:
                add = True
                for options in location_data.get('options', ()):
                    option = getattr(self.options, options['option'])
                    match options.get('operator', 'eq'):
                        case 'eq': add = add and option.value == options['value']
                        case 'ne': add = add and option.value != options['value']
                        case 'gt': add = add and option.value > options['value']
                        case 'ge': add = add and option.value >= options['value']
                        case 'lt': add = add and option.value < options['value']
                        case 'le': add = add and option.value <= options['value']
                if add:
                    new_locations[location_data['name']] = location_data['id']
                    self.log(f"Added location {location_data['name']} with id {location_data['id']} to region {region_data['name']}.", LoggingLevel.MAXIMUM)
            self.get_region(region_data['name']).add_locations(new_locations)
        self.log("Locations created.", LoggingLevel.HIGH)
        
        blink_exclusions, other_exclusions = self.setup_gem_logic()  # needs regions to be set up already
        self.setup_shop_prices(blink_exclusions, other_exclusions)  # needs knowledge of blink and other exclusions from setup_gem_logic
        
    def setup_gem_logic(self) -> tuple[int, int]:
        self.log("Checking if gem logic needs to be set up.", LoggingLevel.LOW)
        blink_exclusions, other_exclusions = 0, 0
        if self.options.shop_randomization.value == 1:
            self.log("Setting up gem logic events.", LoggingLevel.LOW)
            convert = {"1-1": 0, "1-2": 1, "2-1": 2, "2-2": 3, "3-1": 4, "3-2": 5, "4-1": 6, "4-2": 7}
            for reg, region_data in self.location_data.items():
                for gem_event in region_data["gem_events"]:
                    exclusion = False
                    for key in convert.keys():
                        if key in gem_event['name']:
                            if "Byrd minigames" in gem_event['name'] and minigame_locs[convert[key]] in self.options.exclude_locations.value:
                                self.log(f"Skipping Sgt. Byrd gem event {gem_event['name']} because its associated location {minigame_locs[convert[key]]} was excluded.", LoggingLevel.HIGH)
                                other_exclusions += int(gem_event['gem_amount'])
                                exclusion = True
                                break
                            elif "Blink minigames" in gem_event['name'] and minigame_locs[convert[key] + 8] in self.options.exclude_locations.value:
                                self.log(f"Skipping Blink gem event {gem_event['name']} because its associated location {minigame_locs[convert[key] + 8]} was excluded.", LoggingLevel.HIGH)
                                blink_exclusions += int(gem_event['gem_amount'])
                                exclusion = True
                                break
                            elif "Sparx minigames" in gem_event['name'] and minigame_locs[convert[key] + 16] in self.options.exclude_locations.value:
                                self.log(f"Skipping Sparx gem event {gem_event['name']} because its associated location {minigame_locs[convert[key] + 16]} was excluded.", LoggingLevel.HIGH)
                                other_exclusions += int(gem_event['gem_amount'])
                                exclusion = True
                                break
                    if not exclusion:
                        location_name = f"{reg}: {gem_event['name']}"
                        self.get_region(reg).add_event(location_name, gem_event['name'], rule=self.rule_from_dict(gem_event["access_rule"]), show_in_spoiler=False)
                        self.log(f"Created gem event with location name {location_name}, item name {gem_event['name']}, and rule {gem_event['access_rule']}.", LoggingLevel.MAXIMUM)
            return blink_exclusions, other_exclusions
        return 0, 0
    
    def setup_shop_prices(self, blink_exclusions, other_exclusions):
        # shop costs determined by multiple options. Doing after gem events in case of exclusions
        self.log("Setting up shop prices.", LoggingLevel.LOW)
        if self.options.shop_randomization.value == 1:
            blink = (20203 - blink_exclusions) * self.options.blink_gems.value / 100
            non_blink_enemies = 16353 * self.options.non_blink_enemies.value / 100
            other = (105357 - other_exclusions) * self.options.other_gems.value / 100
            gem_total = blink + non_blink_enemies + other
            base_price = gem_total / (self.options.shop_item_count.value - 1)
            self.log(f"blink_gems is {blink}, non_blink_enemies is {non_blink_enemies}, and other_gems is {other}. Base shop price is {base_price}.", LoggingLevel.MEDIUM)
            self.shop_costs.append(0)
    
            if self.options.shop_logic.value == 1:  # 1 = ordered, meaning incrementing prices
                for counter in range(self.options.shop_item_count.value - 1): self.shop_costs.append(int(base_price * (counter + 1)))
            else:  # 0 = unordered, meaning equal pricing
                for _ in range(self.options.shop_item_count.value - 1): self.shop_costs.append(int(base_price))
            self.log(f"Shop costs are: {", ".join(str(cost) for cost in self.shop_costs)}.", LoggingLevel.MEDIUM)
    
    def create_items(self) -> None:
        aht_items = []
        # 4 Elder Abilities
        for ability in ["Double Jump", "Pole Spin", "Wing Shield", "Wall Kick"]:
            aht_items.append(self.create_item(ability))
        
        # 4 Shop Items
        if self.options.shop_randomization.value == 1:
            for shop_item in ["Health Unit+", "Butterfly Jar", "Double Gems", "Shockwave"]:
                if shop_item == "Double Gems" and self.options.double_gems.value == 1:  # bit backwards. 0 = enabled, 1 = disabled
                    self.log("Skipping creating Double Gems as double_gems is disabled.", LoggingLevel.HIGH)
                    continue
                else: aht_items.append(self.create_item(shop_item))

        # 4 Breaths
        self.log("Setting up starting breath(s).", LoggingLevel.LOW)
        starter_placed = False
        for breath in ["Fire Breath", "Electric Breath", "Water Breath", "Ice Breath"]:
            if breath in self.options.starting_breaths.value and not starter_placed:
                self.log(f"Placing {breath} into Starter Checks: Breath.", LoggingLevel.HIGH)
                self.get_location("Starter Checks: Breath").place_locked_item(self.create_item(breath))
                starter_placed = True
            elif breath in self.options.starting_breaths.value:
                self.log(f"Placing {breath} into start inventory.", LoggingLevel.HIGH)
                self.push_precollected(self.create_item(breath))
            else:
                aht_items.append(self.create_item(breath))
        output = "none" if "None" in self.options.starting_breaths.value else ", ".join(self.options.starting_breaths.value)
        self.log(f"Starting breaths: {output}.", LoggingLevel.MEDIUM)
        
        # 3 Base Movement Abilities
        self.log("Setting up base movement abilities (glide, swim, and charge).", LoggingLevel.LOW)
        for movement in ["Glide", "Swim", "Charge"]:
            if movement not in self.options.movement_randomization.value:
                self.log(f"Placing {movement} into Starter Checks: {movement}.", LoggingLevel.HIGH)
                self.get_location(f"Starter Checks: {movement}").place_locked_item(self.create_item(movement))
            else:
                aht_items.append(self.create_item(movement))
        
        # Dark Gems & Light Gems
        for _ in range(40):
            aht_items.append(self.create_item("Dark Gem"))
            
        make_less_lgs = len(self.options.vanilla_minigame_rewards.value) * 4
        for _ in range(100-make_less_lgs):
            aht_items.append(self.create_item("Light Gem"))
        
        self.log("Checking if any minigames need vanilla rewards forced.", LoggingLevel.LOW)
        if len(self.options.vanilla_minigame_rewards.value) != 0:
            self.log(f"Minigame types which will have vanilla rewards forced: {", ".join(self.options.vanilla_minigame_rewards.value)}.", LoggingLevel.MEDIUM)
            npc_names = ["Sgt. Byrd"] * 8 + ["Blink"] * 8 + ["Sparx"] * 8 + ["Turret"] * 8
            for npc, minigame_loc in zip(npc_names, minigame_locs):
                if npc in self.options.vanilla_minigame_rewards.value:
                    item = "Dragon Egg" if "Dragon Egg" in minigame_loc else "Light Gem"
                    self.get_location(minigame_loc).place_locked_item(self.create_item(item))
        
        # Key Rings & Lockpicks
        if self.options.shop_randomization.value == 1 and self.options.key_rings.value == 1:
            for level in ["Dragon Village", "Crocovile Swamp", "Dragonfly Falls", "Coastal Remains", "Sunken Ruins", "Cloudy Domain", "Frostbite Village", "Gloomy Glacier", "Ice Citadel", "Stormy Beach", "Molten Mount", "Magma Falls", "Dark Mine", "Red's Laboratory"]:
                aht_items.append(self.create_item(f"{level} Key Ring"))
        elif self.options.shop_randomization.value == 1:
            for _ in range(52):
                aht_items.append(self.create_item("Lockpick"))
            
        # Starting Realms
        self.log("Setting up starting realms, access cards, and starting shop unlocks (if open world mode is enabled).", LoggingLevel.LOW)
        for realm in REALM_LEVEL_LISTS.keys():
            if self.options.open_world_mode.value == 1 and realm not in self.options.starting_realms.value:
                self.log(f"Adding {realm} to starting realm list due to full open world mode.", LoggingLevel.HIGH)
                self.options.starting_realms.value.add(realm)
            if realm in self.options.starting_realms.value:
                self.log(f"Placing {realm} Access Card into start inventory.", LoggingLevel.HIGH)
                self.push_precollected(self.create_item(f"{realm} Access Card"))
            elif self.options.open_world_mode.value == 0:  # non-starting realm access cards only exist if non-open world
                self.multiworld.itempool.append(self.create_item(f"{realm} Access Card"))
        self.log(f"Starting realm list: {", ".join(self.options.starting_realms.value)}.", LoggingLevel.MEDIUM)
        
        # Shop Unlocks (including pre-collecting ones in starting realms, depending on settings)
        if self.options.open_world_mode.value == 2:  # individual shop unlocks
            for shop in SHOP_PAD_LIST:
                realm = LEVEL_TO_REALM[shop.split(" - ")[0]]
                if self.options.pause_menu_patch.value == 0 and "Depot" in shop and realm in self.options.starting_realms.value:
                    self.log(f"Placing {shop} Shop Unlock into start inventory due to being in a starting realm.", LoggingLevel.HIGH)
                    self.push_precollected(self.create_item(f"{shop} Shop Unlock"))
                else:
                    aht_items.append(self.create_item(f"{shop} Shop Unlock"))
        elif self.options.open_world_mode.value in [3, 4]:  # 3 = progressive, 4 = reverse progressive
            for level in LEVEL_TO_REALM.keys():
                if level in ["Dragon Village", "Stormy Beach"]: count = 1
                elif level in ["Crocovile Swamp", "Dragonfly Falls", "Coastal Remains", "Cloudy Domain", "Sunken Ruins", "Frostbite Village", "Molten Mount", "Magma Falls", "Dark Mine"]: count = 3
                elif level in ["Ice Citadel", "Red's Laboratory"]: count = 4
                else: count = 0  # gloomy glacier
                
                if self.options.pause_menu_patch.value == 0 and LEVEL_TO_REALM[level] in self.options.starting_realms.value and count > 0:
                    self.log(f"Placing 1 Progressive {level} - Shop Unlock into start inventory due to being in a starting realm.", LoggingLevel.HIGH)
                    self.push_precollected(self.create_item(f"Progressive {level} - Shop Unlock"))
                    count -= 1
                
                for _ in range(count):
                    aht_items.append(self.create_item(f"Progressive {level} - Shop Unlock"))
        elif self.options.open_world_mode.value == 5:  # full levels
            for level in LEVEL_TO_REALM.keys():
                if level != "Gloomy Glacier": aht_items.append(self.create_item(f"{level} - Shop Unlock"))
        elif self.options.open_world_mode.value == 6:  # full realms
            for realm in REALM_LEVEL_LISTS.keys():
                aht_items.append(self.create_item(f"{realm} - Shop Unlock"))
        
        # Filler and Traps
        self.log("Setting up filler and trap items.", LoggingLevel.LOW)
        junk_count = len(self.multiworld.get_unfilled_locations(self.player)) - len(aht_items)
        trap_number = junk_count * (self.options.trap_percentage.value / 100)
        if 0 < trap_number < 1: trap_number = math.ceil(trap_number)
        else: trap_number = math.floor(trap_number)
        filler_number = junk_count - trap_number
        self.log(f"Number of fillers: {filler_number}. Number of traps: {trap_number}.", LoggingLevel.HIGH)
        
        output = "none" if len(self.options.trap_items.value) == 0 else ", ".join(self.options.trap_items.value)
        self.log(f"Enabled trap items: {output}.", LoggingLevel.MEDIUM)
        for _ in range(trap_number):
            choice = self.random.choice(list(self.options.trap_items.value))
            self.log(f"Created trap item {choice}.", LoggingLevel.MAXIMUM)
            aht_items.append(self.create_item(choice))

        # shinies have extra logic to force variety in the choices before duplicating
        self.filler_items, unchosen_shinies = self.setup_filler_list()
        output = "none" if len(self.filler_items.keys()) == 0 else ", ".join(self.filler_items.keys()) 
        self.log(f"Enabled filler categories: {output}.", LoggingLevel.MEDIUM)
        reset_shinies = copy.copy(unchosen_shinies)
        for _ in range(filler_number):
            category, items = self.random.choice(list(self.filler_items.items()))
            choice = self.random.choice(items)
            if category == "Shinies":
                if len(unchosen_shinies) == 0: unchosen_shinies = copy.copy(reset_shinies)
                while choice not in unchosen_shinies:
                    choice = self.random.choice(unchosen_shinies)
                unchosen_shinies.remove(choice)
            self.log(f"Created filler item {choice}.", LoggingLevel.MAXIMUM)
            aht_items.append(self.create_item(choice))
    
        self.multiworld.itempool.extend(aht_items)

    def setup_filler_list(self) -> tuple[dict[str, list], list[str]]:
        """Helper method which assembles a list of enabled filler item categories and the possible choices for each type."""
        all_filler_items = [item for item in self.item_data if item["group"] == "Filler"]
        enabled_filler_items: dict[str, list[str]] = {}
        shinies = []

        for category in ["Dragon Eggs", "Breath Bombs", "Gem Packs", "Shinies"]:
            if category in self.options.filler_items.value:
                enabled_filler_items[category] = []

        for filler_item in all_filler_items:
            if filler_item["name"] == "Gem Pack" and "Gem Packs" in enabled_filler_items.keys():
                enabled_filler_items["Gem Packs"].append(filler_item["name"])
            elif filler_item["name"] == "Dragon Egg" and "Dragon Eggs" in enabled_filler_items.keys():
                enabled_filler_items["Dragon Eggs"].append(filler_item["name"])
            elif "Bomb" in filler_item["name"] and "Breath Bombs" in enabled_filler_items.keys():
                enabled_filler_items["Breath Bombs"].append(filler_item["name"])
            elif filler_item.get("type", "") == "Shinies" and "Shinies" in enabled_filler_items.keys():
                enabled_filler_items["Shinies"].append(filler_item["name"])
                shinies.append(filler_item["name"])

        return enabled_filler_items, shinies
  
    def set_rules(self) -> None:
        self.log("Setting up location rules.", LoggingLevel.LOW)
        for r in self.location_data.values():
            for l in r['locations']:
                try:
                    loc = self.get_location(l['name'])
                except KeyError:
                    continue
                self.set_rule(loc, self.rule_from_dict(l['access_rule']))

        self.handle_goaling()  # must be done here because setting up the victorycon events requires location rules to be set up first
    
    def handle_goaling(self):
        self.log("Processing goal choices.", LoggingLevel.LOW)
        victory_cons = defaultdict(tuple[str])
        enabled_goals = []

        goal_info = [
            ["Gnasty Gnorc", BOSS_IDS[0:2]], ["Ineptune", BOSS_IDS[2:4]], ["Red", BOSS_IDS[4:6]], ["Mecha-Red", [BOSS_IDS[6]]],
            ["Dark Gems", DARK_GEM_IDS], ["Light Gems", LIGHT_GEM_IDS], ["Dragon Eggs", DRAGON_EGG_IDS], ["Fireworks", FIREWORK_IDS],
            ["Shop Items", SHOP_ITEM_IDS[:self.options.shop_item_count.value]], ["Locked Chests", LOCKED_CHEST_IDS], ["Elder Tomas", [ELDER_ABILITY_IDS[0]]],
            ["Elder Magnus", [ELDER_ABILITY_IDS[1]]], ["Elder Titan", [ELDER_ABILITY_IDS[2]]], ["Elder Astor", [ELDER_ABILITY_IDS[3]]],
            ["Blink", BLINK_IDS], ["Sgt. Byrd", BYRD_IDS], ["Sparx", SPARX_IDS], ["Turret", TURRET_IDS]
        ]
        # shrink light gem/dragon egg ID lists if needed. The last 15/16 IDs of each are the chest ones
        if self.options.exclude_chest_items.value >= 2:  # 2 = exclude light gems, 3 = exclude both
            goal_info[5][1] = goal_info[5][1][:-15]
        if self.options.exclude_chest_items.value in [1, 3]:  # 1 = exclude eggs, 3 = exclude both
            goal_info[6][1] = goal_info[6][1][:-16]
        amounts = {
            "Gnasty Gnorc": 2, "Ineptune": 2, "Red": 2, "Mecha-Red": 1, "Dark Gems": self.options.dark_gems_goal.value,
            "Light Gems": self.options.light_gems_goal.value, "Dragon Eggs": self.options.dragon_eggs_goal.value,
            "Fireworks": self.options.fireworks_goal.value, "Shop Items": self.options.shop_items_goal.value, "Locked Chests": self.options.locked_chests_goal.value,
            "Elder Tomas": 1, "Elder Magnus": 1, "Elder Titan": 1, "Elder Astor": 1, "Blink": self.options.minigames_goal.value["Blink"],
            "Sgt. Byrd": self.options.minigames_goal.value["Sgt. Byrd"], "Sparx": self.options.minigames_goal.value["Sparx"], "Turret": self.options.minigames_goal.value["Turret"]
        }
        lookup_methods = [
            "Gnasty Gnorc" in self.options.boss_goal.value, "Ineptune" in self.options.boss_goal.value, "Red" in self.options.boss_goal.value,
            "Mecha-Red" in self.options.boss_goal.value, amounts["Dark Gems"] > 0, amounts["Light Gems"] > 0, amounts["Dragon Eggs"] > 0, amounts["Fireworks"] > 0,
            amounts["Shop Items"] > 0, amounts["Locked Chests"] > 0, "Elder Tomas" in self.options.elders_goal.value, "Elder Magnus" in self.options.elders_goal.value,
            "Elder Titan" in self.options.elders_goal.value, "Elder Astor" in self.options.elders_goal.value, self.options.minigames_goal["Blink"] > 0,
            self.options.minigames_goal.value["Sgt. Byrd"] > 0, self.options.minigames_goal.value["Sparx"] > 0, self.options.minigames_goal.value["Turret"] > 0
        ]
        for counter, (goal_name, id_list) in enumerate(goal_info):
            ind_count = 1
            if not lookup_methods[counter]:
                continue
            for loc_id in id_list:
                loc_name = self.location_id_to_name[loc_id]
                loc = self.get_location(loc_name)
                loc.parent_region.add_event(f"{loc.name} Victory{ind_count}", f"VictoryCon{goal_name.replace(" ", "")}{ind_count}", rule=loc.access_rule, show_in_spoiler=False)
                victory_cons[goal_name] += (f"VictoryCon{goal_name.replace(" ", "")}{ind_count}",)
                self.goals_dict[goal_name].append(loc_id)
                self.log(f"Added VictoryCon{goal_name.replace(" ", "")}{ind_count} event for {loc.name}.", LoggingLevel.MAXIMUM)
                ind_count += 1
                if goal_name not in enabled_goals: enabled_goals.append(goal_name)
            self.log(f"Set up {ind_count - 1} goal events for goal \"{goal_name}\".", LoggingLevel.HIGH)
        bad_condition = len(enabled_goals) == 0
        if bad_condition and self.options.auto_corrections.value == 2:  # fix_major exclusive
            self.log("No enabled goals were detected. Seeds must have at least 1 goal. Fixing by enabling Mecha-Red as a goal.", LoggingLevel.WARNING)
            loc = self.get_location(self.location_id_to_name[BOSS_IDS[-1]])
            loc.parent_region.add_event(f"{loc.name} Victory1", "VictoryConMecha-Red1", rule=loc.access_rule, show_in_spoiler=False)
            victory_cons["Mecha-Red"] += ("VictoryConMecha-Red1",)
            enabled_goals.append("Mecha-Red")
        elif bad_condition:
            raise OptionError("No enabled goals were detected. Seeds must have at least 1 goal. Fix this, or set auto_corrections to fix_major to have this automatically fixed.")
        enabled_with_amounts = [f"{goal} ({amounts[goal]} checks)" for goal in enabled_goals]
        self.log(f"Final goal list: {", ".join(enabled_with_amounts)}.", LoggingLevel.MEDIUM)

        def check_for_goal(state: CollectionState) -> bool:
            for goal in enabled_goals:
                events = victory_cons[goal]
                amount = amounts[goal]
                if state.has_from_list(events, self.player, amount):
                    continue
                else:
                    return False
            return True

        self.multiworld.completion_condition[self.player] = lambda state: check_for_goal(state)
    
    def fill_slot_data(self):
        self.log("Filling slot data.", LoggingLevel.LOW)
        slot_data: dict[str, Any] = {
            "death_link": self.options.death_link.value,
            "death_link_amnesty": self.options.death_link_amnesty.value,
            
            "logging_level": self.options.logging_level.value,
            "auto_corrections": self.options.auto_corrections.value,
            
            "goals_dict": self.goals_dict,  # used by client to easily have goal info
            "boss_goal": self.options.boss_goal.value,
            "dark_gems_goal": self.options.dark_gems_goal.value,
            "light_gems_goal": self.options.light_gems_goal.value,
            "dragon_eggs_goal": self.options.dragon_eggs_goal.value,
            "fireworks_goal": self.options.fireworks_goal.value,
            "shop_items_goal": self.options.shop_items_goal.value,
            "locked_chests_goal": self.options.locked_chests_goal.value,
            "elders_goal": self.options.elders_goal.value,
            "minigames_goal": self.options.minigames_goal.value,
            "exclude_chest_items": self.options.exclude_chest_items.value,
            
            "open_world_mode": self.options.open_world_mode.value,
            "firework_checks": self.options.firework_checks.value,
            "vanilla_minigame_rewards": self.options.vanilla_minigame_rewards.value,
            "trap_percentage": self.options.trap_percentage.value,
            "filler_items": self.options.filler_items.value,
            "trap_items": self.options.trap_items.value,
            "trap_length": self.options.trap_length.value,

            "starting_breaths": self.options.starting_breaths.value,
            "movement_randomization": self.options.movement_randomization.value,
            "starting_realms": self.options.starting_realms.value,

            "shop_randomization": self.options.shop_randomization.value,
            "key_rings": self.options.key_rings.value,
            "shop_item_count": self.options.shop_item_count.value,
            "shop_logic": self.options.shop_logic.value,
            "blink_gems": self.options.blink_gems.value,
            "non_blink_enemies": self.options.non_blink_enemies.value,
            "other_gems": self.options.other_gems.value,
            "double_gems": self.options.double_gems.value,
            "shop_costs": self.shop_costs,

            "randomize_boss_lair_doors": self.options.randomize_boss_lair_door_costs.value,
            "boss_lair_costs": self.boss_lairs,
            "boss_lair_forcing": self.options.boss_lair_forcing.value,
            "randomize_light_gem_door_costs": self.options.randomize_light_gem_door_costs.value,
            "light_gem_door_costs": self.light_gem_doors,
            "randomize_gadget_costs": self.options.randomize_gadget_costs.value,
            "gadget_costs": self.gadget_costs,

            "pause_menu_patch": self.options.pause_menu_patch.value,
            "shop_pad_proximity_activation": self.options.shop_pad_proximity_activation.value,
            "hint_minigame_rewards": self.options.hint_minigame_rewards.value,
            "hint_boss_rewards": self.options.hint_boss_rewards.value,
            "hint_shop_items": self.options.hint_shop_items.value,
            "hide_shop_item_names": self.options.hide_shop_item_names.value,
            "easy_bosses": self.options.easy_bosses.value,
            "skip_cutscenes": self.options.skip_cutscenes.value,
            "skip_elevators": self.options.skip_elevators.value,
            "teleport_across_realms": self.options.teleport_across_realms.value,
        }
        
        return slot_data
    
    @staticmethod
    def interpret_slot_data(slot_data: dict[str, Any]) -> dict[str, Any]:
        return slot_data

###############LOGIC RULES###############
@dataclass
class BossLairRule(Rule[SpyroAHTWorld], game="Spyro: A Hero's Tail"):
    index: int

    @override
    def _instantiate(self, world: SpyroAHTWorld) -> Rule.Resolved:
        return Has("Dark Gem", world.boss_lairs[self.index]).resolve(world)


@dataclass
class LGDoorRule(Rule[SpyroAHTWorld], game="Spyro: A Hero's Tail"):
    index: int

    @override
    def _instantiate(self, world: SpyroAHTWorld) -> Rule.Resolved:
        return Has("Light Gem", world.light_gem_doors[self.index]).resolve(world)


@dataclass
class BallGadget(Rule[SpyroAHTWorld], game="Spyro: A Hero's Tail"):
    @override
    def _instantiate(self, world: SpyroAHTWorld) -> Rule.Resolved:
        return Has("Light Gem", world.gadget_costs[0]).resolve(world)


@dataclass
class InvincibilityGadget(Rule[SpyroAHTWorld], game="Spyro: A Hero's Tail"):
    @override
    def _instantiate(self, world: SpyroAHTWorld) -> Rule.Resolved:
        return Has("Light Gem", world.gadget_costs[1]).resolve(world)


@dataclass
class SuperchargeGadget(Rule[SpyroAHTWorld], game="Spyro: A Hero's Tail"):
    @override
    def _instantiate(self, world: SpyroAHTWorld) -> Rule.Resolved:
        return And(Has("Light Gem", world.gadget_costs[2]), Has("Charge")).resolve(world)


@dataclass
class LockedChestRule(Rule[SpyroAHTWorld], game="Spyro: A Hero's Tail"):
    level: str

    @override
    def _instantiate(self, world: SpyroAHTWorld) -> Rule.Resolved:
        if world.options.shop_randomization.value == 1:
            if world.options.key_rings.value == 1:
                if self.level == "Reds Laboratory": self.level = "Red's Laboratory"  # fixing from formatting in local data not having apostraphes
                return Has(f"{self.level} Key Ring", 1).resolve(world)
            else:
                return Has(f"Lockpick", 52).resolve(world)
        else:  # always true when shops are unrandomized
            return True_().resolve(world)
    
    
@dataclass
class ShopCheckRule(Rule[SpyroAHTWorld], game="Spyro: A Hero's Tail"):
    index: int
    
    @override
    def _instantiate(self, world: SpyroAHTWorld) -> Rule.Resolved:
        blink_scaling = world.options.blink_gems.value / 100
        non_blink_enemy_scaling = world.options.non_blink_enemies.value / 100
        other_scaling = world.options.other_gems.value / 100
        # cost is the cost itself if shop is ordered (shop logic == 1). Otherwise, emulate that logic by summing the cost of items so far
        cost = world.shop_costs[self.index] if world.options.shop_logic.value == 1 else sum(world.shop_costs[:self.index+1])
        return self.Resolved(cost, blink_scaling, non_blink_enemy_scaling, other_scaling, player=world.player)

    class Resolved(Rule.Resolved):
        item_cost: int  # PyCharm, why do you complain about thiiiiiiiiiiiiiis it works
        blink_scaling: float
        non_blink_enemy_scaling: float
        other_scaling: float
        
        @override
        def _evaluate(self, state: CollectionState) -> bool:
            blink_gems = state.count("Blink Gems", self.player)
            non_blink_enemies = state.count("Non-Blink Enemies", self.player)
            other = state.count("Other Gems", self.player)
            in_logic_gems = (blink_gems * self.blink_scaling) + (non_blink_enemies * self.non_blink_enemy_scaling) + (other * self.other_scaling)
            return in_logic_gems >= self.item_cost
    

@dataclass
class OpenWorldRule(Rule[SpyroAHTWorld], game="Spyro: A Hero's Tail"):
    shop_names: list[str]
    
    def _instantiate(self, world: SpyroAHTWorld) -> Rule.Resolved:
        if world.options.open_world_mode.value == 0:  # non-open world mode
            return False_().resolve(world)
        elif world.options.open_world_mode.value == 1:  # fully unlocked shops
            return True_().resolve(world)
        
        return HasAny(*self.shop_names).resolve(world)


@dataclass
class RealmAccessRule(Rule[SpyroAHTWorld], game="Spyro: A Hero's Tail"):
    access_card: str
    
    def _instantiate(self, world: SpyroAHTWorld) -> Rule.Resolved:
        # all option combinations can safely at least attempt to check for access card
        items = [self.access_card]
        
        # non-full open world mode settings look for shop unlocks in addition to access card
        if world.options.open_world_mode.value > 1:
            realm_levels = REALM_LEVEL_LOOKUP[self.access_card.replace(" Access Card", "")]
            if world.options.pause_menu_patch.value == 0:
                # "open shop" pause menu only cares about Depot shop for that realm
                level = realm_levels[0]
                shop = LEVEL_SHOP_LOOKUP[level][0]  # in this case, index 0 is always the depot
                items.append(f"{level} - {shop}")
            else:
                # "teleport to hub" pause menu cares about *any* shop in that realm
                for level in REALM_LEVEL_LOOKUP[self.access_card.replace(" Access Card", "")]:
                    for shop in LEVEL_SHOP_LOOKUP[level]:
                        items.append(f"{level} - {shop}")
        
        return HasAny(*items).resolve(world)
            

###############CLIENT###############
def _run_client(*args: str):
    import colorama
    from CommonClient import server_loop, gui_enabled, get_base_parser
    Utils.init_logging("Spyro: A Hero's Tail Client")

    async def _main(connect: str | None, password: str | None):
        from .context import SpyroAHTContext, tracker_loaded
        ctx = SpyroAHTContext(connect, password)
        ctx.server_task = asyncio.create_task(server_loop(ctx), name="ServerLoop")
        if tracker_loaded:
            ctx.run_generator()
        if gui_enabled:
            ctx.run_gui()
        ctx.run_cli()
        await asyncio.sleep(1)

        await ctx.exit_event.wait()
        ctx.watcher_event.set()
        ctx.server_address = None
        await ctx.shutdown()
    
    parser = get_base_parser()
    parsed_args = parser.parse_args(args)
    colorama.init()
    asyncio.run(_main(parsed_args.connect, parsed_args.password))
    colorama.deinit()

def run_client():
    from multiprocessing import Process
    Process(target=_run_client,name="SpyroAHTClient").start()

from worlds.LauncherComponents import Component, components
components.append(Component("Spyro AHT Client", func=run_client, icon='spyro_aht'))
