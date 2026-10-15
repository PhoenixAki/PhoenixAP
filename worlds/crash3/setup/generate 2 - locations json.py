import json

# These are imported so that eval() can recognize them as types below
from rule_builder.rules import Rule, True_
from worlds.crash3 import WarpAccessRule, LevelAccessRule, BossAccessRule

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

    regions[region]["locations"].append({
        "name": loc_name,
        "id": int(loc_id),
        "options": options,
        "access_rule": evaluated_rule.to_dict()
    })
file_in.close()

########################################################################################################################
# output
file_out = open("test-locations.json", "w")
output = json.dumps(regions, indent=4)
file_out.write(output)
print("###############DON'T FORGET TO MOVE THE LOCATION DATA TO LOCATIONS.JSON, BOY###############")