import asyncio
import pkgutil
import logging
import copy
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, TextIO, override

import orjson

import Utils
from BaseClasses import Item, ItemClassification, MultiWorld, Region, CollectionState
from Options import OptionError
from rule_builder.rules import Has, Rule, True_, And, False_, HasAny, HasAll
from worlds.AutoWorld import World, WebWorld
from worlds.LauncherComponents import icon_paths
from .options import MovementRandomization, SpyroAHTOptions, StartingBreaths, spyro_options_groups
from .data.consts import LEVEL_SHOP_LOOKUP, REALM_LEVEL_LOOKUP, REALM_LEVEL_LISTS, LoggingLevel

icon_paths['spyro_aht'] = f'ap:{__name__}/icons/dark_gem_icon.png'

minigame_locs = [
        "DV: Dragon Egg from Sgt. Byrd", "DV: Light Gem from Sgt. Byrd",
        "CD: Dragon Egg atop tower from Sgt. Byrd", "CD: Light Gem atop tower from Sgt. Byrd",
        "IC: Dragon Egg opposite drawbridge from Sgt. Byrd", "IC: Light Gem opposite drawbridge from Sgt. Byrd",
        "MM: Dragon Egg from Sgt. Byrd", "MM: Light Gem from Sgt. Byrd",
        "CS: Dragon Egg near Elder's tree from Blink", "CS: Light Gem near Elder's tree from Blink",
        "CR: Dragon Egg in west area from Blink", "CR: Light Gem in west area from Blink",
        "FV: Dragon Egg approaching icy camp from Blink", "FV: Light Gem approaching icy camp from Blink",
        "DM: Dragon Egg after turret room from Blink", "DM: Light Gem after turret room from Blink",
        "DF: Dragon Egg near elder statue from Sparx", "DF: Light Gem near elder statue from Sparx",
        "SR: Dragon Egg in depths from Sparx", "SR: Light Gem in depths from Sparx",
        "GG: Dragon Egg after spinning bones from Sparx", "GG: Light Gem after spinning bones from Sparx",
        "MFb: Dragon Egg after fire imp room from Sparx", "MFb: Light Gem after fire imp room from Sparx",
        "CS: Dragon Egg from Fredneck", "CS: Light Gem from Fredneck",
        "CR: Dragon Egg from southern beach Turtle Mother", "CR: Light Gem from southern beach Turtle Mother",
        "FV: Dragon Egg after electric gate from Peggy", "FV: Light Gem after electric gate from Peggy",
        "SB: Dragon Egg in upper Stormy Beach from Wally", "SB: Light Gem in upper Stormy Beach from Wally"
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
        "Starter Checks": "Starter Checks",
        "DV": "Dragon Village",
        "CS": "Crocovile Swamp",
        "DF": "Dragonfly Falls",
        "CR": "Coastal Remains",
        "CD": "Cloudy Domain",
        "SR": "Sunken Ruins",
        "FV": "Frostbite Village",
        "GG": "Gloomy Glacier",
        "IC": "Ice Citadel",
        "SB": "Stormy Beach",
        "MM": "Molten Mount",
        "MFt": "Magma Falls Top",
        "MFb": "Magma Falls Bottom",
        "DM": "Dark Mine",
        "RL": "Red's Laboratory",
        "Moneybags": "Shop Items"
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
                    
            loc_groups[level_lookup[abbreviation]].add(location['name'])
            
            if "Defeat" in location['name'] or "Breath from" in location['name']:  # bosses
                loc_groups["All Bosses"].add(location['name'])
            if ": Dark Gem" in location['name']:
                loc_groups["All Dark Gems"].add(location['name'])
                loc_groups[f"{level} Dark Gems"].add(location['name'])
                loc_groups[f"{realm} Dark Gems"].add(location['name'])
            if ": Dragon Egg" in location['name']:
                loc_groups["All Dragon Eggs"].add(location['name'])
                loc_groups[f"{level} Dragon Eggs"].add(location['name'])
                loc_groups[f"{realm} Dragon Eggs"].add(location['name'])
            if ": Light Gem" in location['name']:
                loc_groups["All Light Gems"].add(location['name'])
                loc_groups[f"{level} Light Gems"].add(location['name'])
                loc_groups[f"{realm} Light Gems"].add(location['name'])
            if "Locked Chest" in location['name']:
                loc_groups["All Locked Chests"].add(location['name'])
                loc_groups[f"{level} Locked Chests"].add(location['name'])
                loc_groups[f"{realm} Locked Chests"].add(location['name'])
            if ": Firework" in location['name']:
                loc_groups["All Fireworks"].add(location['name'])
                loc_groups[f"{level} Fireworks"].add(location['name'])
                loc_groups[f"{realm} Fireworks"].add(location['name'])
            if "Sgt. Byrd" in location['name']:
                loc_groups["Sgt. Byrd Minigames"].add(location['name'])
                loc_groups["All Minigames"].add(location['name'])
                loc_groups[f"{realm} Minigames"].add(location['name'])
            if "Blink" in location['name']:
                loc_groups["Blink Minigames"].add(location['name'])
                loc_groups["All Minigames"].add(location['name'])
                loc_groups[f"{realm} Minigames"].add(location['name'])
            if "Sparx" in location['name']:
                loc_groups["Sparx Minigames"].add(location['name'])
                loc_groups["All Minigames"].add(location['name'])
                loc_groups[f"{realm} Minigames"].add(location['name'])
            if "Fredneck" in location['name'] or "Turtle Mother" in location['name'] or "Peggy" in location['name'] or "Wally" in location['name']:
                loc_groups["Turret Minigames"].add(location['name'])
                loc_groups["All Minigames"].add(location['name'])
                loc_groups[f"{realm} Minigames"].add(location['name'])
    return loc_groups


class SpyroAHTWeb(WebWorld):
    option_groups = spyro_options_groups

class SpyroAHTWorld(World):
    """
    Spyro: A Hero's Tail is a 3D platformer and collect-a-thon released in 2004 for the Xbox, Playstation 2 and GameCube.
    """
    game = "Spyro: A Hero's Tail"
    origin_region_name = "START"

    options_dataclass = SpyroAHTOptions
    options: SpyroAHTOptions # type: ignore
    web = SpyroAHTWeb()
    
    item_data = _load_file("items.json")
    item_name_to_id = {i['name']: i['id'] for i in item_data}
    item_name_groups = create_item_groups(item_data)
    
    location_data = _load_file("locations.json")
    location_name_to_id = _location_name_to_id(location_data)
    location_name_groups = create_location_groups(location_data)
    
    ut_can_gen_without_yaml = True
    
    def log(self, message, level: LoggingLevel):
        if self.options.logging_level.value >= level:
            logging.info(f"[Spyro AHT] LOG-{level.name}: {message}")

    def __init__(self, multiworld: MultiWorld, player: int):
        super().__init__(multiworld, player)
        self.multiworld.early_items[self.player]["Double Jump"] = 1
        
        self._lg_doors = [70, 20, 95, 45]
        self._boss_lairs = [10, 20, 30, 40]
        self._gadget_costs = [8, 24, 40]  # ball, invincibility, supercharge
        self._starting_realms = []
        self._starting_breaths = []
        self._classifications = {i['name']: ItemClassification(i['classification']) for i in _load_file("items.json")}
        self.shop_costs = []
        self.filler_items: dict[str, list[str]] = {}

        # tracks IDs of all locations that are part of a goal but are excluded. Sent to client via slot data
        self.excluded_goal_ids = {"Gnasty Gnorc": [], "Ineptune": [], "Red": [], "Mecha-Red": [],
            "Fireworks": [], "Dark Gems": [], "Dragon Eggs": [], "Light Gems": [], "Locked Chests": [], "Shop Items": []
        }

    def get_filler_item_name(self):
        """Override of World.get_filler_item_name which returns a random filler item name.
        Used whenever start_inventory_from_pool is used."""
        items = self.random.choice(list(self.filler_items.values()))
        random_choice = self.random.choice(items)
        self.log(f"Replacing a start_inventory_from_pool item with \"{random_choice}\".", LoggingLevel.HIGH)
        return random_choice
            
    def collect(self, state: "CollectionState", item: "Item") -> bool:
        """Override of World.collect which additionally handles gem events."""
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
        """Override of World.remove which additionally handles gem events."""
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

    def generate_early(self) -> None:
        passthrough = getattr(self.multiworld, "re_gen_passthrough", {})
        if isinstance(passthrough, dict) and self.game in passthrough:
            self._apply_slot_data(passthrough[self.game])
        
        auto_corrections = self.options.auto_corrections.value  # storing locally as micro-optimization compared to checking option
        self.log("Checking for common YAML issues with starting breaths and realms, filler items, and goals.", LoggingLevel.LOW)
        
        bad_condition = len(self.options.starting_breaths.value) > 1 and "None" in self.options.starting_breaths.value  # "none" alongside breath choices
        if bad_condition and auto_corrections:
            self.log("Starting breath list cannot contain breaths and \"None\". Fixing by removing the \"None\".", LoggingLevel.WARNING)
            self.options.starting_breaths.value.remove("None")
        elif bad_condition:
            raise OptionError("Starting breath list cannot contain breaths and \"None\". Automatic fixing is available via auto_corrections.")
        
        if len(self.options.starting_breaths.value) == 0:
            random_breath = self.random.choice(["Fire", "Electric", "Water", "Ice"])
            self.log(f"Starting breath list is empty. {random_breath} Breath was chosen at random.", LoggingLevel.MEDIUM)
            self.options.starting_breaths.value.add(random_breath)
        
        if len(self.options.starting_realms.value) == 0:
            random_realm = self.random.choice(["Dragon Kingdom", "Lost Cities", "Icy Wilderness", "Volcanic Isle"])
            self.log(f"Starting realm list is empty. {random_realm} was chosen at random.", LoggingLevel.MEDIUM)
            self.options.starting_realms.value.add(random_realm)
        
        bad_condition = len(self.options.filler_items.value) == 0  # empty filler list
        if bad_condition and auto_corrections:
            self.log("Filler item list cannot be empty. Fixing by adding \"Generics\".", LoggingLevel.WARNING)
            self.options.filler_items.value.add("Generics")
        elif bad_condition:
            raise OptionError("Filler item list cannot be empty. Automatic fixing is available via auto_corrections.")

        bad_condition = len(self.options.goal.value) < 1  # no goals
        if bad_condition and auto_corrections:
            self.log("Goal list cannot be empty. Fixing by adding 1 \"Random\" to the list.", LoggingLevel.WARNING)
            self.options.goal.value.append("Random")
        elif bad_condition:
            raise OptionError("Goal list cannot be empty. Automatic fixing is available via auto_corrections.")
            
        if len(self.options.goal.value) > len(self.options.goal.valid_keys)-1 and auto_corrections:  # too many goals
            removed = []  # logging
            while len(self.options.goal.value) > len(self.options.goal.valid_keys)-1:
                to_remove = self.random.choice(self.options.goal.value)
                removed.append(to_remove)
                self.options.goal.value.remove(to_remove)
            self.log(f"Goal list can't have more than {len(self.options.goal.valid_keys)-1} entries. Fixed by removing {removed} at random to shrink the list.", LoggingLevel.WARNING)
        elif len(self.options.goal.value) > len(self.options.goal.valid_keys)-1:
            raise OptionError(f"Goal list can't have more than {len(self.options.goal.valid_keys)-1} entries. Automatic fixing is available via auto_corrections.")
        
        # this is disgustingly long, but it grabs all non-random and non-excluded goals which are not already chosen by the player
        random_choices = [goal for goal in self.options.goal.valid_keys if goal != "Random" and goal not in self.options.exclude_from_random_goal.value and goal not in self.options.goal.value]
        random_count = self.options.goal.value.count("Random")
        if random_count > len(random_choices):
            # fix (or halt) specifically for if random_choices list is empty
            if len(random_choices) == 0:
                if auto_corrections:
                    self.log("Random goal(s) were requested, but no goals are available for random selection. Fixing by skipping random choices.", LoggingLevel.WARNING)
                    random_count = 0
                else:
                    raise OptionError("Random goal(s) were requested, but no goals are available for random selection. Automatic fixing is available via auto_corrections.")

            if random_count > 0 and auto_corrections:
                removed = []
                while random_count > len(random_choices):
                    to_remove = self.random.choice(random_choices)
                    removed.append(to_remove)
                    random_choices.remove(to_remove)
                self.log(f"Too many excluded-from-random goals to support {random_count} random choice(s). Fixed by removing {removed} at random from the list of exclusions.", LoggingLevel.WARNING)
            elif random_count > 0 and not self.options.auto_corrections:
                raise OptionError(f"Too many excluded-from-random goals to support {random_count} random choice(s). Automatic fixing is available via auto_corrections.")
        
        converted_goal_set = set(self.options.goal.value)
        if "Random" in converted_goal_set:
            converted_goal_set.remove("Random")

        for _ in range(random_count):
            random_goal = self.random.choice(random_choices)
            converted_goal_set.add(random_goal)
            random_choices.remove(random_goal)
        
        bad_condition = "Fireworks" in converted_goal_set and not self.options.firework_checks.value
        if bad_condition and auto_corrections:
            self.log("Fireworks is a goal but firework_checks is disabled. Fixing by enabling firework_checks.", LoggingLevel.WARNING)
            self.options.firework_checks.value = 1
        elif bad_condition:
            raise OptionError("Fireworks is a goal but firework_checks is disabled. Automatic fixing is available via auto_corrections.")
            
        bad_condition = "Shop Items" in converted_goal_set and not self.options.shop_randomization.value
        if bad_condition and auto_corrections:
            self.log("Shop Items is a goal but shop_randomization is disabled. Fixing by enabling shop_randomization.", LoggingLevel.WARNING)
            self.options.shop_randomization.value = 1
        elif bad_condition:
            raise OptionError("Shop Items is a goal but shop_randomization is disabled. Automatic fixing is available via auto_corrections.")
                
        self.options.goal.value = converted_goal_set
        
    def _apply_slot_data(self, slot_data: dict[str, Any]) -> None:
        self._ut_active = True
        
        self.options.death_link.value = slot_data['death_link']
        self.options.death_link_amnesty.value = slot_data['death_link_amnesty']
        
        self.options.logging_level.value = slot_data['logging_level']
        self.options.auto_corrections.value = slot_data['auto_corrections']
        
        self.options.goal.value = slot_data['goal']
        self.options.exclude_from_random_goal.value = slot_data['exclude_from_random_goal']
        self.options.open_world_mode.value = slot_data['open_world_mode']
        self.options.firework_checks.value = slot_data['firework_checks']
        self.options.vanilla_minigame_rewards.value = slot_data['vanilla_minigame_rewards']
        self.options.filler_items.value = slot_data['filler_items']
        
        self.options.starting_breaths.value = slot_data['starting_breaths']
        self.options.movement_randomization.value = slot_data['movement_randomization']
        self.options.starting_realms.value = slot_data['starting_realms']
        
        self.options.shop_randomization.value = slot_data['shop_randomization']
        self.options.key_rings.value = slot_data['key_rings']
        self.options.gem_logic.value = slot_data['gem_logic']
        self.options.blink_gems.value = slot_data['blink_gems']
        self.options.non_blink_enemies.value = slot_data['non_blink_enemies']
        self.options.other_gems.value = slot_data['other_gems']
        self.options.double_gems.value = slot_data['double_gems']
        
        self._boss_lairs = slot_data['boss_lair_costs']
        self._lg_doors = slot_data['light_gem_door_costs']
        self._gadget_costs = slot_data['gadget_costs']
        
        self.options.pause_menu_patch.value = slot_data['pause_menu_patch']
        self.options.shop_pad_proximity_activation.value = slot_data['shop_pad_proximity_activation']
        self.excluded_goal_ids = slot_data['excluded_goal_ids']
    
    def custom_ut_sort(self, region_label: str, location_label: str) -> str | int:
        level_acronym, rest_of_name = location_label.split(": ")
        level_id = id_lookup[level_acronym]
        return f"{level_id} {region_label} {rest_of_name}"

    def handle_goaling(self):
        self.log("Processing goal choices.", LoggingLevel.LOW)
        # convert goal names to searchable form for location matching
        # in an ideal world, everything would be named in such a way that this isn't necessary, but...¯\_(ツ)_/¯
            # TODO: do something about it then, boy!
        convert = {"Fireworks": ": Firework", "Dragon Eggs": ": Dragon Egg", "Dark Gems": ": Dark Gem",
                   "Light Gems": ": Light Gem", "Gnasty Gnorc": "Defeat Gnasty Gnorc", "Ineptune": "Defeat Ineptune",
                   "Red": "Defeat Red", "Mecha-Red": "Defeat Mecha-Red", "Locked Chests": "Locked Chest", "Shop Items": "Shop Item"}
        victory_cons = []

        # a bit ugly to have triple nested loop, but I don't think it's avoidable
        # needs to be "for every location in every region, check every enabled goal for matches" which is just inherently triple-nested
        count = 1
        shop_item_count = 18 if self.options.key_rings else 56
        for reg, region_data in _load_file("locations.json").items():
            for location in region_data["locations"]:
                for goal in self.options.goal.value:
                    if convert[goal] in location["name"]:
                        if "Shop Item" in location["name"] and int(location["name"][-2:]) > shop_item_count:
                            continue  # skip shop items 19-56 if key rings are enabled
                        if location['name'] in self.options.exclude_locations.value:
                            self.log(f"{goal} is a goal, but {location['name']} is excluded, so it will not be required for goal.", LoggingLevel.HIGH)
                            self.excluded_goal_ids[goal].append(location['id'])
                            continue
                        self.get_region(reg).add_event(f"{location['name']} Victory{count}", f"VictoryCon{count}", rule=self.rule_from_dict(location['access_rule']))
                        victory_cons.append(f"VictoryCon{count}")
                        self.log(f"Added VictoryCon{count} event for {location['name']}.", LoggingLevel.MAXIMUM)
                        count += 1
        
        # handle cases where the player excluded all locations for a given goal
        counts = {"Gnasty Gnorc": 1, "Ineptune": 1, "Red": 1, "Mecha-Red": 1, "Fireworks": 22, "Dragon Eggs": 80, "Dark Gems": 40, "Light Gems": 100, "Locked Chests": 52, "Shop Items": shop_item_count}
        found_valid_goal = False
        to_remove = []
        for goal in self.options.goal.value:
            if len(self.excluded_goal_ids[goal]) == counts[goal]:
                self.log(f"All locations that belong to the {goal} goal were excluded. {goal} has been removed from the goal list.", LoggingLevel.WARNING)
                to_remove.append(goal)
            elif not found_valid_goal:
                found_valid_goal = True
        self.options.goal.value = [goal for goal in self.options.goal.value if goal not in to_remove]
        
        if not found_valid_goal and self.options.auto_corrections:
            self.log(f"All locations for all selected goals were excluded. Fixing by forcing Mecha-Red as the only goal.", LoggingLevel.WARNING)
            loc = self.get_location("RL: Defeat Mecha-Red")
            loc.parent_region.add_event(f"RL: Defeat Mecha-Red Victory1", "VictoryCon1", rule=HasAll('Double Jump', 'Fire Breath', 'Electric Breath'))  # hardcoded because no access to the json here
            victory_cons.append(f"VictoryCon1")
            count += 1
            self.options.goal.value = ["Mecha-Red"]
        elif not found_valid_goal:
            raise OptionError("All locations for all selected goals were excluded. Automatic fixing is available via auto_corrections.")
        
        self.log(f"Set up {count-1} VictoryCon events.", LoggingLevel.HIGH)
        self.log(f"Final goal list: {", ".join(self.options.goal.value)}.", LoggingLevel.MEDIUM)
        self.multiworld.completion_condition[self.player] = lambda state: state.has_all(victory_cons, self.player)
    
    def create_regions(self):
        # TODO: how much of this needs to be here specifically? lot of setup done here and in create_items and probably would be good to review if it could be all in one place
        auto_corrections = self.options.auto_corrections.value  # setting as micro-optimization for checking later
            
        self.log("Setting up gadget costs.", LoggingLevel.LOW)
        if self.options.randomize_gadget_costs.value != 0:
            if self.options.randomize_gadget_costs.value == 2:  # shuffled:
                self.random.shuffle(self._gadget_costs)
            else:  # randomized:
                lmin, lmax = self.options.gadget_cost_min.value, self.options.gadget_cost_max.value
                bad_condition = lmin > lmax
                if bad_condition and auto_corrections:
                    self.log(f"gadget_cost_min of {lmin} is greater than {lmax}. Fixing by swapping them.", LoggingLevel.WARNING)
                    lmin, lmax = lmax, lmin
                elif bad_condition:
                    raise OptionError(f"gadget_cost_min of {lmin} is greater than {lmax}. Automatic fixing is available via auto_corrections.")
                self._gadget_costs = [self.random.randint(lmin, lmax) for _ in range(3)]
        self.log(f"Gadget Costs (in Light Gems): Ball requires {self._gadget_costs[0]}, invincibility requires {self._gadget_costs[1]}, and supercharge requires {self._gadget_costs[2]}.", LoggingLevel.MEDIUM)
        
        self.log("Setting up boss lair costs.", LoggingLevel.LOW)
        if self.options.randomize_boss_lair_door_costs.value != 0:  # if not default
            if self.options.randomize_boss_lair_door_costs.value == 2:  # shuffled:
                self.random.shuffle(self._boss_lairs)
            else:
                bmin, bmax = self.options.boss_lair_door_cost_min.value, self.options.boss_lair_door_cost_max.value
                bad_condition = bmin > bmax
                if bad_condition and auto_corrections:
                    self.log(f"boss_lair_door_cost_min of {bmin} is greater than {bmax}. Fixing by swapping them.", LoggingLevel.WARNING)
                    bmin, bmax = bmax, bmin
                elif bad_condition:
                    raise OptionError(f"boss_lair_door_cost_min of {bmin} is greater than {bmax}. Automatic fixing is available via auto_corrections.")

                self._boss_lairs = [self.random.randint(bmin, bmax) for _ in range(4)]
        
        self.log(f"Checking if boss lair costs need forcing via boss_lair_forcing.", LoggingLevel.LOW)
        lookup = ["Gnasty Gnorc", "Ineptune", "Red", "Mecha-Red"]
        forcing = self.options.boss_lair_forcing.value
        if forcing != 0:
            if 1 <= self.options.boss_lair_forcing.value <= 4: goal_boss_indices = [forcing-1]
            else: goal_boss_indices = [lookup.index(boss) for boss in lookup if boss in self.options.goal.value]
            non_goal_boss_indices = [index for index in [0, 1, 2, 3] if index not in goal_boss_indices]
            
            if len(goal_boss_indices) == 4:
                self.log("boss_lair_forcing is set to automatic, but all 4 bosses are part of goal. Skipping cost swapping.", LoggingLevel.HIGH)
            elif len(goal_boss_indices) == 0:
                self.log("boss_lair_forcing is set to automatic, but you have no goal bosses. Skipping cost swapping.", LoggingLevel.HIGH)
            else:
                for goal_boss_index in goal_boss_indices:
                    goal_boss_cost = self._boss_lairs[goal_boss_index]
                    
                    # find highest-costing non-goal boss
                    highest_non_goal_index = non_goal_boss_indices[0]
                    for non_goal_boss_index in non_goal_boss_indices:
                        if self._boss_lairs[non_goal_boss_index] > self._boss_lairs[highest_non_goal_index]:
                            highest_non_goal_index = non_goal_boss_index
                    highest_non_goal_cost = self._boss_lairs[highest_non_goal_index]
                    
                    # swap if needed
                    if self._boss_lairs[goal_boss_index] < highest_non_goal_cost:
                        self.log(f"Swapping {lookup[goal_boss_index]}'s cost of {goal_boss_cost} and {lookup[highest_non_goal_index]}'s cost of {highest_non_goal_cost} as the former is smaller.", LoggingLevel.HIGH)
                        self._boss_lairs[goal_boss_index] = highest_non_goal_cost
                        self._boss_lairs[highest_non_goal_index] = goal_boss_cost
                    else:
                        self.log(f"Skipping swapping {lookup[goal_boss_index]}'s cost of {goal_boss_cost} and {lookup[highest_non_goal_index]}'s cost of {highest_non_goal_cost} as the former is already larger.", LoggingLevel.HIGH)
        self.log(f"Boss Lair Costs (in Dark Gems): Gnasty Gnorc requires {self._boss_lairs[0]}, Ineptune requires {self._boss_lairs[1]}, Red requires {self._boss_lairs[2]}, and Mecha-Red requires {self._boss_lairs[3]}.", LoggingLevel.MEDIUM)
        
        self.log("Setting up Light Gem door costs.", LoggingLevel.LOW)
        if self.options.randomize_light_gem_door_costs.value != 0:
            if self.options.randomize_light_gem_door_costs.value == 2:  # shuffled:
                self.random.shuffle(self._lg_doors)
            else:
                lmin, lmax = self.options.light_gem_door_cost_min.value, self.options.light_gem_door_cost_max.value
                bad_condition = lmin > lmax
                if bad_condition and auto_corrections:
                    self.log(f"light_gem_door_cost_min of {lmin} is greater than light_gem_door_cost_max of {lmax}. Fixing by swapping them.", LoggingLevel.WARNING)
                    lmin, lmax = lmax, lmin
                elif bad_condition:
                    raise OptionError(f"light_gem_door_cost_min of {lmin} is greater than light_gem_door_cost_max of {lmax}. Automatic fixing is available via auto_corrections.")
                self._lg_doors = [self.random.randint(lmin, lmax) for _ in range(4)]
        self.log(f"Light Gem Door costs (in Light Gems): Dragonfly Falls requires {self._lg_doors[0]}, Coastal Remains requires {self._lg_doors[1]}, Frostbite Village requires {self._lg_doors[2]}, and Dark Mine requires {self._lg_doors[3]}.", LoggingLevel.MEDIUM)

        self.log("Setting up regions and locations.", LoggingLevel.LOW)
        data = _load_file("locations.json")
        self.multiworld.regions.extend(Region(r['name'], self.player, self.multiworld) for r in data.values())
        self.log("Regions created.", LoggingLevel.HIGH)
        
        for region_name, region_data in data.items():
            for entrance in region_data['entrances']:
                region_from, region_to = entrance['name'].split(" -> ")
                rule = self.rule_from_dict(entrance['access_rule'])
                self.get_region(region_from).connect(self.get_region(region_to), f"{region_from} => {region_to}", rule)
                self.log(f"Connected region {region_from} to region {region_to} with rule {rule}.", LoggingLevel.MAXIMUM)
        self.log("Regions connected.", LoggingLevel.HIGH)

        for region_data in data.values():
            region_object = self.get_region(region_data['name'])
            new_locations = {}
            for location_data in region_data['locations']:
                add = True
                for options in location_data.get('options', ()):
                    option = getattr(self.options, options['option'])
                    match options.get('operator', 'eq'):
                        case 'eq':
                            add = add and option.value == options['value']
                        case 'ne':
                            add = add and option.value != options['value']
                        case 'gt':
                            add = add and option.value > options['value']
                        case 'ge':
                            add = add and option.value >= options['value']
                        case 'lt':
                            add = add and option.value < options['value']
                        case 'le':
                            add = add and option.value <= options['value']
                if add:
                    new_locations[location_data['name']] = location_data['id']
                    
                    self.log(f"Added location {location_data['name']} with id {location_data['id']} to region {region_data['name']}.", LoggingLevel.MAXIMUM)
            region_object.add_locations(new_locations)
        self.log("Locations created.", LoggingLevel.HIGH)

        # add gem events, only if shop is randomized with gem logic
        self.log("Checking if gem logic needs to be set up.", LoggingLevel.LOW)
        blink_exclusions, other_exclusions = 0, 0
        if self.options.shop_randomization.value == 1 and self.options.gem_logic.value == 1:
            convert = {"1-1": 0, "1-2": 1, "2-1": 2, "2-2": 3, "3-1": 4, "3-2": 5, "4-1": 6, "4-2": 7}
            for reg, region_data in data.items():
                for gem_event in region_data["gem_events"]:
                    exclusion = False
                    for key in convert.keys():
                        if key in gem_event['name']:
                            if "Byrd minigames" in gem_event['name'] and minigame_locs[convert[key]] in self.options.exclude_locations.value:
                                self.log(f"Skipping Sgt. Byrd gem event {gem_event['name']} because its associated location {minigame_locs[convert[key]]} was excluded.", LoggingLevel.HIGH)
                                other_exclusions += int(gem_event['gem_amount'])
                                exclusion = True
                                break
                            elif "Blink minigames" in gem_event['name'] and minigame_locs[convert[key]+8] in self.options.exclude_locations.value:
                                self.log(f"Skipping Blink gem event {gem_event['name']} because its associated location {minigame_locs[convert[key]+8]} was excluded.", LoggingLevel.HIGH)
                                blink_exclusions += int(gem_event['gem_amount'])
                                exclusion = True
                                break
                            elif "Sparx minigames" in gem_event['name'] and minigame_locs[convert[key]+16] in self.options.exclude_locations.value:
                                self.log(f"Skipping Sparx gem event {gem_event['name']} because its associated location {minigame_locs[convert[key]+16]} was excluded.", LoggingLevel.HIGH)
                                other_exclusions += int(gem_event['gem_amount'])
                                exclusion = True
                                break
                                
                    if not exclusion:
                        location_name = f"{reg}: {gem_event['name']}"
                        self.get_region(reg).add_event(location_name, gem_event['name'], rule=self.rule_from_dict(gem_event["access_rule"]), show_in_spoiler=False)
                        self.log(f"Created gem event with location name {location_name}, item name {gem_event['name']}, and rule {gem_event['access_rule']}.", LoggingLevel.MAXIMUM)
                    
        # shop costs determined by multiple options. Doing after gem events in case of exclusions
        self.log("Checking if shop costs need to be set up.", LoggingLevel.LOW)
        if self.options.shop_randomization.value == 1:
            shop_item_count = 18 if self.options.key_rings.value else 56
            blink = (20203 - blink_exclusions) * self.options.blink_gems.value / 100
            non_blink_enemies = 16353 * self.options.non_blink_enemies.value / 100
            other = (105357 - other_exclusions) * self.options.other_gems.value / 100
            gem_total = blink + non_blink_enemies + other
            base_price = gem_total / (shop_item_count - 1)
            self.log(f"Shop prices are being initialized. blink_gems is {blink}, non_blink_enemies is {non_blink_enemies}, and other_gems is {other}. Base shop price is {base_price}.", LoggingLevel.MEDIUM)
            self.shop_costs.append(0)

            if self.options.gem_logic:  # gem logic = incrementing prices
                for counter in range(shop_item_count - 1):
                    self.shop_costs.append(int(base_price * (counter + 1)))
            else:  # no gem logic = items have equal pricing
                for _ in range(shop_item_count - 1):
                    self.shop_costs.append(int(base_price))
            self.log(f"Shop costs are: {", ".join(str(cost) for cost in self.shop_costs)}.", LoggingLevel.MEDIUM)
            
        self.handle_goaling()
    
    def create_item(self, name: str) -> Item:
        """Helper method for create_items which returns an Item object."""
        return Item(name, self._classifications[name], self.item_name_to_id[name], self.player)

    def setup_filler_list(self, item_data) -> tuple[dict[str, list], list[str]]:
        """Helper method which assembles a list of enabled filler item categories and the possible choices for each type."""
        all_filler_items = [item for item in item_data if item["group"] == "Filler"]
        enabled_filler_items: dict[str, list[str]] = {}
        generics = []
        
        for category in ["Dragon Eggs", "Breath Bombs", "Gem Packs", "Generics"]:
            if category in self.options.filler_items.value:
                enabled_filler_items[category] = []
        
        for filler_item in all_filler_items:
            if filler_item["name"] == "Gem Pack" and "Gem Packs" in enabled_filler_items.keys():
                enabled_filler_items["Gem Packs"].append(filler_item["name"])
            elif filler_item["name"] == "Dragon Egg" and "Dragon Eggs" in enabled_filler_items.keys():
                enabled_filler_items["Dragon Eggs"].append(filler_item["name"])
            elif "Bomb" in filler_item["name"] and "Breath Bombs" in enabled_filler_items.keys():
                enabled_filler_items["Breath Bombs"].append(filler_item["name"])
            elif filler_item.get("type", "") == "Generic" and "Generics" in enabled_filler_items.keys():
                enabled_filler_items["Generics"].append(filler_item["name"])
                generics.append(filler_item["name"])
        
        return enabled_filler_items, generics
    
    def create_items(self) -> None:
        item_data = _load_file("items.json")
        item_pool = []
        
        skip_double_gems = self.options.shop_randomization.value == 1 and self.options.double_gems.value == 1
        
        self.log("Checking if any minigames need vanilla rewards forced.", LoggingLevel.LOW)
        vanilla = self.options.vanilla_minigame_rewards.value  # just to make rest a  bit more readable
        skip_light_gems = len(vanilla) * 4  # done here so that it always has a value. 0 if no forcing, multiples of 4 otherwise
        if len(vanilla) != 0:
            self.log(f"Minigame types which will have vanilla rewards forced: {", ".join(vanilla)}.", LoggingLevel.MEDIUM)
            npc_names = ["Sgt. Byrd"] * 8 + ["Blink"] * 8 + ["Sparx"] * 8 + ["Turret"] * 8
            for npc, minigame_loc in zip(npc_names, minigame_locs):
                if npc in vanilla:
                    item = "Dragon Egg" if "Dragon Egg" in minigame_loc else "Light Gem"
                    self.get_location(minigame_loc).place_locked_item(self.create_item(item))
        
        self.log("Setting up starting breath(s).", LoggingLevel.LOW)
        starter_done = False
        if "None" not in self.options.starting_breaths.value:  # if none is there at all, it will be the only thing there, thus nothing should be done
            for breath in self.options.starting_breaths.value:
                breath_name = f"{breath} Breath"
                self._starting_breaths.append(breath_name)
                if starter_done:
                    self.push_precollected(self.create_item(breath_name))
                    self.log(f"{breath_name} has been placed into start inventory.", LoggingLevel.HIGH)
                else:
                    self.get_location("Starter Checks: Breath").place_locked_item(self.create_item(breath_name))
                    self.log(f"{breath_name} has been placed into Starter Checks: Breath.", LoggingLevel.HIGH)
                    starter_done = True
            self.log(f"Starting breath(s) are {", ".join(self._starting_breaths)}.", LoggingLevel.MEDIUM)
        else:
            self.log(f"Starting with no breaths.", LoggingLevel.MEDIUM)
        
        self.log("Setting up base movement abilities (glide, swim, and charge).", LoggingLevel.LOW)
        skip_movements = []
        for movement in ["Glide", "Swim", "Charge"]:
            if movement not in self.options.movement_randomization.value:
                self.get_location(f"Starter Checks: {movement}").place_locked_item(self.create_item(movement))
                self.log(f"{movement} has been placed into Starter Checks: {movement}.", LoggingLevel.HIGH)
                skip_movements.append(movement)
            else:
                self.log(f"{movement} will be added to the item pool.", LoggingLevel.HIGH)
        self.log(f"Starting movement abilities: {", ".join(skip_movements)}.", LoggingLevel.MEDIUM)
            
        self.log("Setting up starting realms, access cards, and starting shop unlocks (if open world mode is enabled).", LoggingLevel.LOW)
        if self.options.open_world_mode.value == 1:  # all 4 if open world is on
            self._starting_realms = ['Dragon Kingdom', 'Lost Cities', 'Icy Wilderness', 'Volcanic Isle']
            self.log("open_world_mode is set to full. starting_realms list has been overridden to start with all 4 realms.", LoggingLevel.WARNING)
        else:
            self._starting_realms = list(self.options.starting_realms.value)
        
        if len(self._starting_realms) == 1 and self._starting_realms[0] == "Icy Wilderness" and self.options.shop_randomization.value == 0 and len(self.options.movement_randomization.value) == 0:
            if self.options.auto_corrections:
                self.log("Can't have Icy Wilderness as the only starting realm if shop randomization is disabled and all 3 movement abilities are unrandomized. Fixing by changing starting realm to Dragon Kingdom.", LoggingLevel.WARNING)
                self._starting_realms[0] = "Dragon Kingdom"
            else:
                raise OptionError("Can't have Icy Wilderness as the only starting realm if shop randomization is disabled and all 3 movement abilities are unrandomized. Automatic fixing is available via auto_corrections.")
            
        # add starting realm choices to start inventory, if not already in start inventory
        added_realms, subtract_one = [], []
        convert = {"Dragon Kingdom": "Dragon Village - Village Depot Shop Unlock", "Lost Cities": "Coastal Remains - Coastal Depot Shop Unlock", "Icy Wilderness": "Frostbite Village - Frosty Depot Shop Unlock", "Volcanic Isle": "Stormy Beach - Stormy Depot Shop Unlock"}
        for realm in self._starting_realms:
            new_card = self.create_item(f"{realm} Access Card")
            added_realms.append(f"{realm} Access Card")
            if new_card not in self.multiworld.precollected_items[self.player]:  # don't add the card if the player already put it there
                self.log(f"Added {new_card.name} to start inventory.", LoggingLevel.HIGH)
                self.push_precollected(new_card)
            else:
                self.log(f"Skipped adding {new_card.name} to start inventory because it's already there.", LoggingLevel.HIGH)
                
            # also unlock starting realm depot shops if open world is on but not full and pause menu is open shop
            # this is to prevent softlocks if starting in a realm and teleporting away too early and thus being unable to return to the starting hub area
            # this is done by manually creating and pre-collecting individual depot unlock items regardless of mode
            # modes 5 and 6 (full levels + realms) doesn't need to have an item subtracted because their shop unlock items always include at least one non-starting hub shop
            if 2 <= self.options.open_world_mode.value <= 4 and self.options.pause_menu_patch.value == 0:
                new_shop_unlock = self.create_item(convert[realm])
                if new_shop_unlock not in self.multiworld.precollected_items[self.player]:
                    self.log(f"Adding {new_shop_unlock.name} to start inventory.", LoggingLevel.HIGH)
                    self.push_precollected(new_shop_unlock)
                else:
                    self.log(f"Skipping adding {new_shop_unlock.name} to start inventory because player already put it there.", LoggingLevel.HIGH)
                
                if self.options.open_world_mode.value == 2:  # randomized
                    subtract_one.append(convert[realm])
                elif 3 <= self.options.open_world_mode.value <= 4:  # progressive or rev progressive
                    depot_level = REALM_LEVEL_LOOKUP[realm][0]
                    subtract_one.append(f"Progressive {depot_level} - Shop Unlock")
        self.log(f"Starting realm list: {", ".join(self._starting_realms)}.", LoggingLevel.MEDIUM)
        
        self.log("Starting main item creation loop.", LoggingLevel.LOW)
        for item in item_data:
            if item["group"] == "Filler":  # filler handled later
                continue
            
            if item['name'] == "Double Gems" and skip_double_gems:
                self.log("Skipping creating Double Gems item because shop_randomization is enabled but double_gems is disabled.", LoggingLevel.HIGH)
                continue
            
            if item['name'] in skip_movements:
                self.log(f"Skipping creating {item['name']} due to already being placed into Starter Checks: {item['name']}.", LoggingLevel.HIGH)
                continue
                
            if item['name'] in self._starting_breaths:
                self.log(f"Skipping creating {item['name']} due to being a starting breath.", LoggingLevel.HIGH)
                continue
            
            if self.options.open_world_mode.value != 0 and "Access Card" in item['name']:
                # open world mode == 1 has access cards, but they're created and pre-collected above, thus all should be skipped here
                # open world mode > 1 has no access cards besides the one(s) the player starts with, created and pre-collected above, thus all should be skipped here
                self.log(f"Skipping creating {item['name']} because access cards have already been handled.", LoggingLevel.HIGH)
                continue
            elif item['name'] in added_realms:
                self.log(f"Skipping creating {item['name']} because it's a starting realm.", LoggingLevel.HIGH)
                continue  # non-open world has normal access card logic. only skip the ones pre-added, add the rest to the pool
            
            add = True

            for curr_option in item.get("option", ()):
                option = getattr(self.options, curr_option['option'])
                match curr_option.get('operator', 'eq'):
                    case 'eq':
                        add = add and option.value == curr_option['value']
                    case 'ne':
                        add = add and option.value != curr_option['value']
                    case 'gt':
                        add = add and option.value > curr_option['value']
                    case 'ge':
                        add = add and option.value >= curr_option['value']
                    case 'lt':
                        add = add and option.value < curr_option['value']
                    case 'le':
                        add = add and option.value <= curr_option['value']

            if add:
                count = item.get('count', 1)
                if item['name'] == 'Light Gem':
                    if skip_light_gems > 0:
                        self.log(f"Making {skip_light_gems} less Light Gems due to {skip_light_gems} being pre-placed via vanilla_minigame_rewards.", LoggingLevel.HIGH)
                        count -= skip_light_gems
                if item['name'] in subtract_one:  # make one less of each corresponding depot shop level unlock if added above already
                    if count == 1:
                        self.log(f"Skipping making {item['name']} because its corresponding realm is a starting realm.", LoggingLevel.HIGH)
                    else:
                        self.log(f"Making 1 less {item['name']} because its corresponding realm is a starting realm.", LoggingLevel.HIGH)
                    count -= 1

                for _ in range(count):
                    item_pool.append(self.create_item(item['name']))
                self.log(f"Created {count} of item {item['name']}.", LoggingLevel.MAXIMUM)
                
        # add filler. Randomly choose a category, randomly choose an item from that category.
        # generics have extra logic to force variety in the choices before duplicating
        self.log("Setting up and creating filler items.", LoggingLevel.LOW)
        self.filler_items, unchosen_generics = self.setup_filler_list(item_data)
        self.log(f"Enabled filler categories: {list(self.filler_items.keys())}.", LoggingLevel.MEDIUM)
        reset_generics = copy.copy(unchosen_generics)
        while len(item_pool) < len(self.multiworld.get_unfilled_locations(self.player)):
            category, items = self.random.choice(list(self.filler_items.items()))
            choice = self.random.choice(items)
            if category == "Generics":
                if len(unchosen_generics) == 0: unchosen_generics = copy.copy(reset_generics)
                while choice not in unchosen_generics:
                    choice = self.random.choice(unchosen_generics)
                unchosen_generics.remove(choice)
            self.log(f"Created filler item {choice}.", LoggingLevel.MAXIMUM)
            item_pool.append(self.create_item(choice))
        self.multiworld.itempool.extend(item_pool)
  
    def set_rules(self) -> None:
        self.log("Setting up location rules.", LoggingLevel.LOW)
        data = _load_file("locations.json")
        for r in data.values():
            for l in r['locations']:
                try:
                    loc = self.get_location(l['name'])
                except KeyError:
                    continue
                self.set_rule(loc, self.rule_from_dict(l['access_rule']))
    
    def fill_slot_data(self):
        self.log("Filling slot data.", LoggingLevel.LOW)
        slot_data: dict[str, Any] = {
            "death_link": self.options.death_link.value,
            "death_link_amnesty": self.options.death_link_amnesty.value,
            
            "logging_level": self.options.logging_level.value,
            "auto_corrections": self.options.auto_corrections.value,
            
            "goal": self.options.goal.value,
            "exclude_from_random_goal": self.options.exclude_from_random_goal.value,
            "open_world_mode": self.options.open_world_mode.value,
            "firework_checks": self.options.firework_checks.value,
            "vanilla_minigame_rewards": self.options.vanilla_minigame_rewards.value,
            "filler_items": self.options.filler_items.value,

            "starting_breaths": self.options.starting_breaths.value,
            "movement_randomization": self.options.movement_randomization.value,
            "starting_realms": self._starting_realms,

            "shop_randomization": self.options.shop_randomization.value,
            "key_rings": self.options.key_rings.value,
            "gem_logic": self.options.gem_logic.value,
            "blink_gems": self.options.blink_gems.value,
            "non_blink_enemies": self.options.non_blink_enemies.value,
            "other_gems": self.options.other_gems.value,
            "double_gems": self.options.double_gems.value,
            "shop_costs": self.shop_costs,

            "randomize_boss_lair_doors": self.options.randomize_boss_lair_door_costs.value,
            "boss_lair_costs": self._boss_lairs,
            "boss_lair_forcing": self.options.boss_lair_forcing.value,
            "randomize_light_gem_door_costs": self.options.randomize_light_gem_door_costs.value,
            "light_gem_door_costs": self._lg_doors,
            "randomize_gadget_costs": self.options.randomize_gadget_costs.value,
            "gadget_costs": self._gadget_costs,

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
            
            "excluded_goal_ids": self.excluded_goal_ids
        }
        
        return slot_data
    
    @staticmethod
    def interpret_slot_data(slot_data: dict[str, Any]) -> dict[str, Any]:
        return slot_data
    
    def write_spoiler(self, spoiler_handle: TextIO) -> None:
        super().write_spoiler(spoiler_handle)
        
        if self.options.shop_randomization:
            spoiler_handle.write(f"Shop Prices:                     {self.shop_costs}\n")
        spoiler_handle.write(f"Boss Lair Costs:                 {self._boss_lairs}\n")
        spoiler_handle.write(f"Light Gem Door Costs:            {self._lg_doors}\n")
        spoiler_handle.write(f"Gadget Costs:                    {self._gadget_costs}\n")

###############LOGIC RULES###############
@dataclass
class BossLairRule(Rule[SpyroAHTWorld], game="Spyro: A Hero's Tail"):
    index: int

    @override
    def _instantiate(self, world: SpyroAHTWorld) -> Rule.Resolved:
        return Has("Dark Gem", world._boss_lairs[self.index]).resolve(world)


@dataclass
class LGDoorRule(Rule[SpyroAHTWorld], game="Spyro: A Hero's Tail"):
    index: int

    @override
    def _instantiate(self, world: SpyroAHTWorld) -> Rule.Resolved:
        return Has("Light Gem", world._lg_doors[self.index]).resolve(world)


@dataclass
class BallGadget(Rule[SpyroAHTWorld], game="Spyro: A Hero's Tail"):
    @override
    def _instantiate(self, world: SpyroAHTWorld) -> Rule.Resolved:
        return Has("Light Gem", world._gadget_costs[0]).resolve(world)


@dataclass
class InvincibilityGadget(Rule[SpyroAHTWorld], game="Spyro: A Hero's Tail"):
    @override
    def _instantiate(self, world: SpyroAHTWorld) -> Rule.Resolved:
        return Has("Light Gem", world._gadget_costs[1]).resolve(world)


@dataclass
class SuperchargeGadget(Rule[SpyroAHTWorld], game="Spyro: A Hero's Tail"):
    @override
    def _instantiate(self, world: SpyroAHTWorld) -> Rule.Resolved:
        return And(Has("Light Gem", world._gadget_costs[2]), Has("Charge")).resolve(world)


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
        if world.options.gem_logic:
            if self.index == 0:
                return True_().resolve(world)  # first item always free. This ensures True_() before evaluating any gem logic so that it's in sphere 1
            blink_scaling = world.options.blink_gems.value / 100
            non_blink_enemy_scaling = world.options.non_blink_enemies.value / 100
            other_scaling = world.options.other_gems.value / 100
            return self.Resolved(world.shop_costs[self.index], blink_scaling, non_blink_enemy_scaling, other_scaling, player=world.player)
        else:
            return True_().resolve(world)  # always accessible if gem logic is not in use

    class Resolved(Rule.Resolved):
        item_cost: int
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
