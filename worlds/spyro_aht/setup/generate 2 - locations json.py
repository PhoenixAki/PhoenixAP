import json

# These are imported so that eval() can recognize them as types below
from rule_builder.rules import Rule, True_, Has, HasAll, And, HasAny, Or, CanReachRegion
from worlds.spyro_aht import BossLairRule, BallGadget, LGDoorRule, InvincibilityGadget, SuperchargeGadget, \
    ShopCheckRule, LockedChestRule, OpenWorldRule, RealmAccessRule

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
    region_info, rule = entrance_full.split(" | ")
    region_from, region_to = region_info.split(" -> ")
    
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
    region, loc_name, loc_id, loc_rule = line.split(" | ")
    options = []  # default, overridden below if an optionable location is encountered
    evaluated_rule: Rule = eval(loc_rule)

    if "Shop Item" in loc_name:
        options = [{
            "option": "shop_randomization",
            "value": 1
        },
        {
            "option": "shop_item_count",
            "operator": "ge",
            "value": int(loc_name[-2:])
        }]
    elif "Firework" in loc_name:
        options = [{
            "option": "firework_checks",
            "value": 1
        }]

    regions[region]["locations"].append({
        "name": loc_name,
        "id": int(loc_id),
        "options": options,
        "access_rule": evaluated_rule.to_dict()
    })
file_in.close()

########################################################################################################################
# load gem events
file_in = open("4 - gem events.txt", "r")
for line in file_in:
    line = line.strip()
    region, event_name, event_rule = line.split(" | ")
    gem_amount = event_name.split(" ", 1)[0]
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