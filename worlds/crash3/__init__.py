import logging
import math
import pkgutil
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, override

import orjson

from BaseClasses import Item, ItemClassification, MultiWorld, Region, CollectionState
from Options import OptionError
from rule_builder.rules import Has, Rule, True_
from worlds.AutoWorld import World, WebWorld
from worlds.LauncherComponents import icon_paths
from .data.consts import LoggingLevel, BOSS_IDS
from .options import Crash3Options, crash3_options_groups

icon_paths['crash3'] = f'ap:{__name__}/icons/game_logo.png'

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
    warp_levels = {
        "Warp 1": ["Toad Village", "Under Pressure", "Orient Express", "Bone Yard", "Makin' Waves"],
        "Warp 2": ["Gee Wiz", "Hang'em High", "Hog Ride", "Tomb Time", "Midnight Run"],
        "Warp 3": ["Dino Might!", "Deep Trouble", "High Time", "Road Crash", "Double Header"],
        "Warp 4": ["Sphynxinator", "Bye Bye Blimps", "Tell No Tales", "Future Frenzy", "Tomb Wader"],
        "Warp 5": ["Gone Tomorrow", "Orange Asphalt", "Flaming Passion", "Mad Bombesr", "Bug Lite"],
        "Warp 6": ["Ski Crazed", "Area 51?", "Rings of Power"]
    }
    
    loc_groups = defaultdict(set)
    for region in location_data.values():
        for location in region['locations']:
            level_name = location['name'].split(': ')[0]
            for warp, levels in warp_levels.items():
                if level_name in levels:
                    loc_groups[warp].add(location['name'])
                
            if "Crystal" in location['name']:
                loc_groups["Crystals"].add(location['name'])
            
            if "Box Gem" in location['name']:
                loc_groups["Box Gems"].add(location['name'])
            elif "Path Gem" in location['name']:
                loc_groups["Colored Gem Paths"].add(location['name'])
            elif "Gem" in location['name']:
                loc_groups["Colored Gems"].add(location['name'])
                
            if "Relic" in location['name']:
                loc_groups["Relics"].add(location['name'])
            if "Sapphire Relic" in location['name']:
                loc_groups["Sapphire Relics"].add(location['name'])
            if "Gold Relic" in location['name']:
                loc_groups["Gold Relics"].add(location['name'])
            if "Platinum Relic" in location['name']:
                loc_groups["Platinum Relics"].add(location['name'])
                
            if "Defeat" in location['name']:
                loc_groups["Bosses"].add(location['name'])
    return loc_groups


class Crash3Web(WebWorld):
    option_groups = crash3_options_groups

class Crash3World(World):
    """Crash 3: Warped is a 3D platformer and collect-a-thon released in 1998 for the Playstation."""
    ###############WORLD SETUP & INITIALIZATION###############
    game = "Crash 3: Warped"
    origin_region_name = "START"

    options_dataclass = Crash3Options
    options: Crash3Options
    web = Crash3Web()
    
    item_data = _load_file("items.json")
    item_name_to_id = {i['name']: i['id'] for i in item_data}
    item_name_groups = create_item_groups(item_data)
    
    location_data = _load_file("locations.json")
    location_name_to_id = _location_name_to_id(location_data)
    location_name_groups = create_location_groups(location_data)
    
    # ut_can_gen_without_yaml = True

    def __init__(self, multiworld: MultiWorld, player: int):
        super().__init__(multiworld, player)

        self.classifications = {i['name']: ItemClassification(i['classification']) for i in self.item_data}
        self.filler_items: list[str] = {}
        self.goals_dict: dict[str, list[int]] = defaultdict(list[int])  # dict of enabled goal name -> list of location ids. Sent to client via slot data
        self.goal_events = {}  # associates goal events -> locations, used in set_rules
    
    ###############HELPER METHODS + OVERRIDES###############
    def log(self, message, level: LoggingLevel):
        """Logs messages from generation."""
        if self.options.logging_level.value >= level:
            logging.info(f"[Crash 3] LOG-{level.name}: {message}")
    
    def create_item(self, name: str, placement: str = "item pool") -> Item:
        """Returns an Item object, given an item name."""
        self.log(f"Created item {name} with classification {self.classifications[name]} and ID {self.item_name_to_id[name]}, placed into {placement}.", LoggingLevel.MAXIMUM)
        return Item(name, self.classifications[name], self.item_name_to_id[name], self.player)
    
    def custom_ut_sort(self, region_label: str, location_label: str) -> str | int:
        """Sorts Crash 3 locations in UT based on vanilla game level order, then alphabetical per level."""
        # used for UT custom sorting
        id_lookup = {"Toad Village": "A", "Under Pressure": "B", "Orient Express": "C", "Bone Yard": "D", "Makin' Waves": "E", "Defeat Tiny Tiger": "F",
                     "Gee Wiz": "G", "Hang'em High": "H", "Hog Ride": "I", "Tomb Time": "J", "Midnight Run": "K", "Defeat Dingodile": "L",
                     "Dino Might!": "M", "Deep Trouble": "N", "High Time": "O", "Road Crash": "P", "Double Header": "Q", "Defeat N. Trophy": "R",
                     "Sphynxinator": "S", "Bye Bye Blimps": "T", "Tell No Tales": "U", "Future Frenzy": "V", "Tomb Wader": "W", "Defeat N. Gin": "X",
                     "Gone Tomorrow": "Y", "Orange Asphalt": "Z", "Flaming Passion": "a", "Mad Bombers": "b", "Bug Lite": "c", "Defeat Cortex": "d",
                     "Ski Crazed": "e", "Area 51?": "f", "Rings of Power": "g", "Hot Coco": "h", "Eggipus Rex": "i"}
        
        level_acronym, rest_of_name = location_label.split(": ")
        level_id = id_lookup[level_acronym]
        return f"{level_id} {rest_of_name}"

    def get_filler_item_name(self):
        """Override of World.get_filler_item_name which returns a random filler item name.
        Used whenever start_inventory_from_pool is used."""
        if len(self.filler_items) == 0:
            random_choice = "1 Wumpa Fruit"
        else:
            random_choice = self.random.choice(self.filler_items)
        self.log(f"Replacing a start_inventory_from_pool item with \"{random_choice}\".", LoggingLevel.HIGH)
        return random_choice
                
    ###############GENERATION PROCESS OVERRIDES###############
    def generate_early(self) -> None:
        passthrough = getattr(self.multiworld, "re_gen_passthrough", {})
        if isinstance(passthrough, dict) and self.game in passthrough:
            self._apply_slot_data(passthrough[self.game])

    def _apply_slot_data(self, slot_data: dict[str, Any]) -> None:
        self._ut_active = True
        
        self.options.logging_level.value = slot_data["logging_level"]
        self.options.auto_corrections.value = slot_data["auto_corrections"]
        
        self.options.boss_goal.value = slot_data["boss_goal"]
        
        self.options.starting_warps.value = slot_data["starting_warps"]
        self.options.trap_percentage.value = slot_data["trap_percentage"]
        self.options.filler_items.value = slot_data["filler_items"]
        self.options.trap_items.value = slot_data["trap_items"]

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
        
        self.create_goal_events()  # adds rule-less events to existing regions. Rules then set in set_rules
        
    def create_goal_events(self):
        self.log("Processing goal choices.", LoggingLevel.LOW)
        victory_cons = defaultdict(tuple[str])
        enabled_goals = []

        goal_info = {
            "Tiny Tiger": {"ids": [BOSS_IDS[0]], "count": 1}, "Dingodile": {"ids": [BOSS_IDS[1]], "count": 1},
            "N. Tropy": {"ids": [BOSS_IDS[2]], "count": 1}, "N. Gin": {"ids": [BOSS_IDS[3]], "count": 1},
            "Cortex": {"ids": [BOSS_IDS[4]], "count": 1}
        }
        enabled_tests = {
            "Tiny Tiger": "Tiny Tiger" in self.options.boss_goal.value, "Dingodile": "Dingodile" in self.options.boss_goal.value,
            "N. Tropy": "N. Tropy" in self.options.boss_goal.value, "N. Gin": "N. Gin" in self.options.boss_goal.value,
            "Cortex": "Cortex" in self.options.boss_goal.value
        }

        for goal_name, data in goal_info.items():
            ind_count = 1
            if not enabled_tests[goal_name]:
                continue
            for loc_id in data["ids"]:
                loc_name = self.location_id_to_name[loc_id]
                loc = self.get_location(loc_name)
                loc.parent_region.add_event(f"{loc.name} Victory{ind_count}", f"VictoryCon{goal_name.replace(" ", "")}{ind_count}", show_in_spoiler=False)  # rule assigned later in set_rules
                self.goal_events[f"{loc.name} Victory{ind_count}"] = loc_name  # associates goal events to their corresponding location, for rule setup later
                victory_cons[goal_name] += (f"VictoryCon{goal_name.replace(" ", "")}{ind_count}",)
                self.goals_dict[goal_name].append(loc_id)
                self.log(f"Added VictoryCon{goal_name.replace(" ", "")}{ind_count} event for {loc.name}.", LoggingLevel.MAXIMUM)
                ind_count += 1
                if goal_name not in enabled_goals: enabled_goals.append(goal_name)
            self.log(f"Set up {ind_count - 1} goal events for goal \"{goal_name}\".", LoggingLevel.HIGH)

        bad_condition = len(enabled_goals) == 0
        if bad_condition and self.options.auto_corrections.value == 3:  # fix_major exclusive
            self.log("No enabled goals were detected. Seeds must have at least 1 goal. Fixing by enabling Cortex as a goal.", LoggingLevel.WARNING)
            loc = self.get_location(self.location_id_to_name[BOSS_IDS[1]])
            loc.parent_region.add_event(f"{loc.name} Victory1", "VictoryConCortex1", rule=loc.access_rule, show_in_spoiler=False)
            victory_cons["Cortex"] += ("VictoryConCortex1",)
            enabled_goals.append("Cortex")
        elif bad_condition and self.options.auto_corrections.value == 0:  # halt
            raise OptionError("No enabled goals were detected. Seeds must have at least 1 goal. Fix this, or set auto_corrections to fix_major to have this automatically fixed.")

        enabled_with_amounts = [f"{goal} ({goal_info[goal]["count"]} checks)" for goal in enabled_goals]
        self.log(f"Final goal list: {", ".join(enabled_with_amounts)}.", LoggingLevel.MEDIUM)

        def check_for_goal(state: CollectionState) -> bool:
            for goal in enabled_goals:
                events = victory_cons[goal]
                amount = goal_info[goal]["count"]
                if state.has_from_list(events, self.player, amount):
                    continue
                else:
                    return False
            return True
        
        self.multiworld.completion_condition[self.player] = lambda state: check_for_goal(state)
    
    def create_items(self) -> None:
        crash_items = []
        for _ in range(25):
            crash_items.append(self.create_item("Crystal"))
        
        for _ in range(40):
            crash_items.append(self.create_item("Clear Gem"))
        
        for color in ["Blue", "Green", "Purple", "Yellow", "Red"]:
            crash_items.append(self.create_item(f"{color} Gem"))
        
        for i in range(1, 6):
            warp_name = f"Warp {i}"
            if warp_name in self.options.starting_warps.value:
                self.push_precollected(self.create_item(f"{warp_name} Unlock", "start inventory"))
            else:
                crash_items.append(self.create_item(f"Warp {i} Unlock"))
        
        # skipping relics for now
        
        for ability in ["Super Body Slam", "Double Jump", "Tornado Spin", "Bazooka", "Running Shoes"]:
            crash_items.append(self.create_item(ability))
        
        # Filler and Traps
        self.log("Setting up filler and trap items.", LoggingLevel.LOW)
        junk_count = len(self.multiworld.get_unfilled_locations(self.player)) - len(crash_items)
        trap_number = junk_count * (self.options.trap_percentage.value / 100)
        if 0 < trap_number < 1: trap_number = math.ceil(trap_number)
        else: trap_number = math.floor(trap_number)
        filler_number = junk_count - trap_number
        self.log(f"Number of fillers: {filler_number}. Number of traps: {trap_number}.", LoggingLevel.HIGH)
        
        output = "none" if len(self.options.trap_items.value) == 0 else ", ".join(self.options.trap_items.value)
        self.log(f"Enabled trap items: {output}.", LoggingLevel.MEDIUM)
        trap_choices = list(self.options.trap_items.value)
        trap_choices.sort()  # non-determinism fix
        for _ in range(trap_number):
            choice = self.random.choice(trap_choices)
            crash_items.append(self.create_item(choice))

        output = "none" if len(self.options.filler_items.value) == 0 else ", ".join(self.options.filler_items.value)
        self.log(f"Enabled filler items: {output}.", LoggingLevel.MEDIUM)
        filler_choices = list(self.options.filler_items.value)
        filler_choices.sort()  # non-determinism fix
        for _ in range(filler_number):
            choice = self.random.choice(filler_choices)
            crash_items.append(self.create_item(choice))
    
        self.multiworld.itempool.extend(crash_items)

    def set_rules(self) -> None:
        self.log("Setting up location rules.", LoggingLevel.LOW)
        # this does non-goal locations
        for region in self.location_data.values():
            for location in region['locations']:
                try:
                    loc = self.get_location(location['name'])
                except KeyError:
                    continue
                self.set_rule(loc, self.rule_from_dict(location['access_rule']))

        # this does goal events
        for goal_event, location_name in self.goal_events.items():
            self.get_location(goal_event).access_rule = self.get_location(location_name).access_rule
    
    def fill_slot_data(self):
        self.log("Filling slot data.", LoggingLevel.LOW)
        slot_data: dict[str, Any] = {
            "logging_level": self.options.logging_level.value,
            "auto_corrections": self.options.auto_corrections.value,
            
            "boss_goal": self.options.boss_goal.value,
            
            "starting_warps": self.options.starting_warps.value,
            "trap_percentage": self.options.trap_percentage.value,
            "filler_items": self.options.filler_items.value,
            "trap_items": self.options.trap_items.value
        }
        
        return slot_data
    
    @staticmethod
    def interpret_slot_data(slot_data: dict[str, Any]) -> dict[str, Any]:
        return slot_data

###############LOGIC RULES###############
@dataclass
class WarpAccessRule(Rule[Crash3World], game="Crash 3: Warped"):
    warp_num: int

    @override
    def _instantiate(self, world: Crash3World) -> Rule.Resolved:
        return Has(f"Warp {self.warp_num} Unlock").resolve(world)


@dataclass
class LevelAccessRule(Rule[Crash3World], game="Crash 3: Warped"):
    level_name: str
    
    @override
    def _instantiate(self, world: Crash3World) -> Rule.Resolved:
        return True_().resolve(world)
        # return Has(f"{self.level_name} Unlock").resolve(world)


@dataclass
class BossAccessRule(Rule[Crash3World], game="Crash 3: Warped"):
    boss_num: int
    
    @override
    def _instantiate(self, world: Crash3World) -> Rule.Resolved:
        return Has("Crystal", self.boss_num*5).resolve(world)