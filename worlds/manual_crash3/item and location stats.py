import math

# I had an Excel sheet I was maintaining to visually do this, but it very quickly got out of hand with too many dimensions.
# Think of this as if creating a large grid, where N is the number of options available and the ways you can combine them.
# I visualize it like binary. Imagine there's 2 options only: clear_gem_checks and level_unlocks.
# There's 4 combinations of those existing together (with 0 = off, 1 = on): 00, 01, 10, and 11.
# Each of those outcomes has impacts on the number of checks and items for a seed.
# So, this script seeks to simulate the check and item counts for every possible combination of options.
# It then flags any that are problematic (more items than locations), at which point I have extra rules kick in.
# Those extra rules represent what auto_corrections does, to ensure a seed can succeed when a flagged combination is fixed.
# I'm typing all of this before actually writing this script...pray for me
class Entry:
    is_enabled: bool  # whether this option is enabled or not
    option: str  # an option name from options below
    check_amount: int  # how many checks this adds, if any
    item_amount: int  # how many items this adds, if any
    adjusted: bool  # did this entry require auto_corrections adjustments
    
    def __init__(self, is_enabled, option, amounts, adjusted):
        self.is_enabled = is_enabled
        self.option = option
        self.check_amount = amounts[0]
        self.item_amount = amounts[1]
        self.adjusted = adjusted
     
    def __str__(self):
        if include_status and self.is_enabled: status = "E"
        elif include_status and not self.is_enabled: status = "D"
        else: status = ""
        return f"{self.check_amount}/{self.item_amount}{status}"

def create_entry() -> Entry:
    # amounts format is (checks, items).
    # I don't know how to avoid making this fairly hardcoded, due to the nature of some options having different effects on locations/items dependent on other options.
    # So, hardcoded it is. This function needs updating when new options are introduced to account for their logic, and options needs updating. The rest is pretty generalized.
    
    # First, return a 0/0 Entry if the option is disabled.
    if not enabled:
        return Entry(enabled, option_name, (0, 0), False)
    
    # This is referenced by a lot of options below, so calculating it in advance makes the name and logic more readable.
    sapphire_enabled = options_list[options.index("sapphire_relics")] == 1
    
    if option_name == "colored_gems":
        amounts = (14, 5) if sapphire_enabled else (10, 4)  # Yellow Gem item and checks requires warp 6 access via sapphire_relics.
    elif option_name == "clear_gems":
        amounts = (39, 0) if sapphire_enabled else (28, 0)  # 11 checks require warp 6 access via sapphire_relics.
    elif option_name == "warp_unlocks":
        amounts = (0, 5)  # Always 0/5 when enabled.
    elif option_name == "level_unlocks":
        amounts = (0, 35) if sapphire_enabled else (0, 31)  # Ski Crazed, Area 51?, Rings of Power, and Eggipus Rex require warp 6 access via sapphire_relics.
    elif option_name == "sapphire_relics":
        amounts = (30, 30)  # Always 30/30 when enabled.
    elif option_name == "gold_relics" or option_name == "platinum_relics":
        amounts = (30, 0) if sapphire_enabled else (26, 0)  # Ski Crazed, Area 51?, Rings of Power, and Eggipus Rex require warp 6 access via sapphire_relics.
    else:
        raise TypeError("ya' dun fucked up, boy")
    
    if include_adjustments: adjusted = check_for_auto_corrections(sapphire_enabled)
    else: adjusted = False
    
    return Entry(enabled, option_name, amounts, adjusted)

def check_for_auto_corrections(sapphire):
    # Similarly to create_entry, this is very hardcoded to specific issues. More documentation on what these auto_corrections fixes are can be found
    #   in hooks/World.py, in before_generate_early. That contains Python code that does the fixes during generation time, and this emulates that.
    # Like create_entry, I felt it good to store these on their own first for more readable logic.
    was_something_adjusted = False
    clear_gems_enabled = options_list[options.index("clear_gems")] == 1
    gold_relics_enabled = options_list[options.index("gold_relics")] == 1
    platinum_relics_enabled = options_list[options.index("platinum_relics")] == 1
    warps_enabled = options_list[options.index("warp_unlocks")] == 1
    
    # warp_unlocks requires at least one of clear_gems, gold_relics, or platinum_relics on.
    if option_name == "warp_unlocks" and not clear_gems_enabled and not gold_relics_enabled and not platinum_relics_enabled:
        options_list[options.index("clear_gems")] = 1
        clear_gems_enabled = True
        was_something_adjusted = True
    
    # level_unlocks has 2 cases:
    # 1) If sapphire_relics is on and warp_unlocks is off, then clear_gems is all that is needed to be forced on.
    if option_name == "level_unlocks" and sapphire and not warps_enabled:
        options_list[options.index("clear_gems")] = 1
        clear_gems_enabled = True
        was_something_adjusted = True
    # 2) Otherwise, level_unlocks requires at least 2 of clear_gems, gold_relics, or platinum_relics on.
    enabled_count = sum([clear_gems_enabled, gold_relics_enabled, platinum_relics_enabled])
    if option_name == "level_unlocks" and enabled_count < 2:
        was_something_adjusted = True
        options_list[options.index("clear_gems")] = 1
        clear_gems_enabled = True
        enabled_count = sum([clear_gems_enabled, gold_relics_enabled, platinum_relics_enabled])
        if enabled_count < 2:
            options_list[options.index("gold_relics")] = 1
            gold_relics_enabled = True
    
    return was_something_adjusted

# options is the basis of all the scaling here: how many options there are to consider. This script is designed with the assumption that each is a binary toggle (either off or on).
# The current options list is ordered very specifically due to how auto_corrections is emulated. warp_unlocks and level_unlocks must come first, because they need to be processed before the options that they may force on.
options = ["warp_unlocks", "level_unlocks", "colored_gems", "clear_gems", "sapphire_relics", "gold_relics", "platinum_relics"]
current_row = 0  # will be converted from decimal to binary to determine which options are enabled at each step e.g. value of 2 is 0000010, so only 2nd to last option is enabled then
n = int(math.pow(2, len(options)))  # 2^n permutations
data = [[] for _ in range(n)]  # each of these will store 1 set of Entry objects
original_options_lists = []  # stores the original form of each permutation, since they might get auto_corrections adjustments. Original form is included in final output.

include_status = False  # setting that toggles including an E or a D for enabled/disabled, next to each entry's amount.
include_adjustments = True  # setting that toggles whether to simulate auto_corrections taking action when problematic combinations are identified.

# This loop generates all the option permutations.
for row in data:
    # Each iteration needs to update row from being an empty list to a list of Entry objects.
    new_row = []
    # This line does a lot at once. For example, if current_row is 5 and there are 7 options, this line generates options_list as [0, 0, 0, 0, 1, 0, 1].
    # It does this by converting 5 to a binary string (0000101) with enough padding to make it 7 bits, and then converts each of those characters into ints and puts them into the list.
    options_list = [int(num) for num in list(f"{current_row:0{len(options)}b}")]
    original_options_lists.append("".join(str(num) for num in options_list))
    
    for option_name, enabled in zip(options, options_list):
        new_row.append(create_entry())
    
    data[current_row] = new_row
    current_row += 1

# This section generates the statistics output for each permutation.
# Example of how the table displays (showing just 2 rows with gibberish data I made up):
# colored_gems  clear_gems      warp_unlocks    level_unlocks   sapphire_relics     gold_relics     platinum_relics     totals
# 1/1           2/0             0/0             0/30            30/30               0/0             30/0                63/61
# repeat row 2 for all permutations
print(f"SETTINGS: include_status {include_status}, include_adjustments {include_adjustments}.\n")

row_header = ""
for option in options:
    row_header += f"{option:<20}"

row_header += f"{'TOTAL':<20}"
row_header += f"{'OK?':<20}"
row_header += f"{'ORIGINAL PERMUTATION':<20}"
print(row_header)
print("-"*len(row_header))
for counter, row in enumerate(data):
    output = ""
    adj = False
    checks = 30  # always 25 Crystal checks and 5 boss checks
    items = 30  # always 25 Crystal items and 5 boss abilities
    
    for entry in row:
        checks += entry.check_amount
        items += entry.item_amount
        if not adj and entry.adjusted: adj = True
        output += f"{str(entry):<20}"
    output += f"{f"{checks}/{items}":<20}"  # this is disgusting
    if adj: output += f"{'YES (ADJUSTED)':<20}" if checks >= items else f"{'NO (ADJUSTED)':<20}"
    else: output += f"{'YES':<20}" if checks >= items else f"{'NO':<20}"
    output += original_options_lists[counter]
    
    print(output)
