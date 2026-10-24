import json

from rule_builder.options import OptionFilter
from worlds.spyro_aht.options import ShopRandomization, MinigameChecks, ShopItemCount, FireworkChecks, EnabledTricks
# These are imported so that eval() can recognize them as types below
from rule_builder.rules import Rule, NestedRule, True_, Has, HasAll, And, HasAny, Or, CanReachRegion
from worlds.spyro_aht.data import consts
from worlds.spyro_aht import BossLairRule, BallGadget, LGDoorRule, InvincibilityGadget, SuperchargeGadget, \
    ShopCheckRule, LockedChestRule, OpenWorldRule, RealmAccessRule

# takes some key (mostly entrance/location names) and returns a trick name, used to create option filter dicts.
# hardcoded to indices here to keep the trick names themselves in one place in consts
trick_lookup = {
    "glide_above_elder_astor": consts.TRICK_LEVELS["Easy"][0],
    "toxic_rise_without_electric": consts.TRICK_LEVELS["Easy"][1],
    "fire_breath_idle_animation": consts.TRICK_LEVELS["Other"][0]
}

regions = {}
########################################################################################################################
# load regions
file_in = open("1 - region list.txt", "r")
for line in file_in:
    region_name = line.strip()
    if region_name not in regions:
        regions[region_name] = {
            "name": region_name,
            "entrances": [],
            "locations": [],
            "gem_events": []
        }
    
file_in.close()

########################################################################################################################
# load entrances
file_in = open("2 - region entrances.txt", "r")
for line in file_in:
    entrance_full = line.strip()
    region_info, rule = entrance_full.split(" | ", 1)
    region_from, region_to = region_info.split(" -> ")
    
    # check for rule-level options (tricks). tricks have an additional | i.e. normal logic | trick logic
    if " | " in rule:
        normal_rule = eval(rule.split(" | ")[0])
        trick_name = rule.split(" | ")[1].split(" ", 1)[0]  # left half of trick rule side is name with underscore spaces
        trick_rule = eval(rule.split(" | ")[1].split(" ", 1)[1])
        trick_rule.options = (OptionFilter(EnabledTricks, trick_lookup[trick_name], operator="contains"),)
        evaluated_rule = Or(normal_rule, trick_rule)
    else:
        evaluated_rule = eval(rule)
    
    regions[region_to]["entrances"].append({
        "name": region_info,
        "access_rule": evaluated_rule.to_dict()
    })
file_in.close()

########################################################################################################################
# load locations
file_in = open("3 - locations.txt", "r")
for line in file_in:
    line = line.strip()
    region, loc_name, loc_id, loc_rule = line.split(" | ", 3)
    loc_id = int(loc_id)
    options = []
    
    # check for rule-level options (tricks). tricks have an additional | i.e. normal logic | trick logic
    if " | " in loc_rule:
        normal_rule = eval(loc_rule.split(" | ")[0])
        trick_name = loc_rule.split(" | ")[1].split(" ", 1)[0]
        trick_rule = eval(loc_rule.split(" | ")[1].split(" ", 1)[1])
        trick_rule.options = (OptionFilter(EnabledTricks, trick_lookup[trick_name], operator="contains"),)
        evaluated_rule = Or(normal_rule, trick_rule)
    else:
        evaluated_rule = eval(loc_rule)
    
    # check for location-level options
    if "Shop Item" in loc_name:
        options = [
            OptionFilter(ShopRandomization, 1, operator="eq").to_dict(),
            OptionFilter(ShopItemCount, int(loc_name[-2:]), operator="ge").to_dict()
        ]
    elif "Firework" in loc_name:
        options = [OptionFilter(FireworkChecks, 1, operator="eq").to_dict()]
    elif loc_id in [*consts.BLINK_IDS, *consts.BYRD_IDS, *consts.SPARX_IDS, *consts.TURRET_IDS]:
        if loc_id in consts.BLINK_IDS: npc = "Blink"
        elif loc_id in consts.BYRD_IDS: npc = "Sgt. Byrd"
        elif loc_id in consts.SPARX_IDS: npc = "Sparx"
        else: npc = "Turret"
        
        # enabled or easy if dragon egg (id in the 300's). only enabled for light gems (id in the 200's)
        values = ["enabled", "easy"] if loc_id // 100 == 3 else ["enabled"]
        options = [{  # can't make into a proper OptionFilter to then to_dict on since this is custom format
            "option": "worlds.spyro_aht.options.MinigameChecks",
            "npc": npc,
            "value": values
        }]

    regions[region]["locations"].append({
        "name": loc_name,
        "id": loc_id,
        "options": options,
        "access_rule": evaluated_rule.to_dict()
    })
file_in.close()

########################################################################################################################
# load gem events
file_in = open("4 - gem events.txt", "r")
for line in file_in:
    line = line.strip()
    region, event_name, event_rule = line.split(" | ", 2)
    gem_amount = event_name.split(" ", 1)[0]
    
    # check for rule-level options (tricks). tricks have an additional | i.e. normal logic | trick logic 
    if " | " in event_rule:
        normal_rule = eval(event_rule.split(" | ")[0])
        trick_name = event_rule.split(" | ")[1].split(" ", 1)[0]
        trick_rule = eval(event_rule.split(" | ")[1].split(" ", 1)[1])
        trick_rule.options = (OptionFilter(EnabledTricks, trick_lookup[trick_name], operator="eq"),)
        evaluated_rule = Or(normal_rule, trick_rule)
    else:
        evaluated_rule: Rule = eval(event_rule)

    regions[region]["gem_events"].append({
        "name": event_name,
        "gem_amount": int(gem_amount),
        "options": [],
        "access_rule": evaluated_rule.to_dict()
    })

########################################################################################################################
# output
file_out = open("test-locations.json", "w")
output = json.dumps(regions, indent=4)
file_out.write(output)
print("###############DON'T FORGET TO MOVE THE LOCATION DATA TO LOCATIONS.JSON, BOY###############")