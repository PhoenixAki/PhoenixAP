import math

# I had an Excel sheet I was maintaining to visually do this, but it very quickly got out of hand with too many dimensions.
# Think of this as if creating a large grid, where N is the number of options available and the ways you can combine them.
# I visualize it like binary. Imagine there's 2 options only: clear_gem_checks and level_unlocks.
# There's 4 combinations of those existing together (with 0 = off, 1 = on): 00, 01, 10, and 11.
# Each of those outcomes has impacts on the number of checks and items for a seed.
# So, this script seeks to simulate the check and item counts for every possible combination of options.
# It then flags any that are problematic (more items than locations), at which point I have extra rules kick in which represent raised OptionErrors.
# I'm typing all of this before actually writing this script...pray for me
def get_amounts() -> tuple[list[list], list]:
    counts: list[list] = []
    sapphire_enabled = options_list[options.index("sapphire_relics")] == 1  # makes later logic more readable
    
    for option in options:
        if options_list[options.index(option)] == 0:
            counts.append([0, 0])
            continue
        
        if option == "clear_gems":
            counts.append([39, 0] if sapphire_enabled else [28, 0])  # 11 checks require warp 6 access via sapphire_relics.
        if option == "colored_gems":
            counts.append([14, 5] if sapphire_enabled else [10, 4])  # Yellow Gem item and checks requires warp 6 access via sapphire_relics.
        if option == "warp_unlocks":
            counts.append([0, 5])  # Always 0/5 when enabled.
        if option == "level_unlocks":
            counts.append([0, 35] if sapphire_enabled else [0, 31])  # Ski Crazed, Area 51?, Rings of Power, and Eggipus Rex require warp 6 access via sapphire_relics.
        if option == "sapphire_relics":
            counts.append([30, 30])  # Always 30/30 when enabled.
        if option == "gold_relics" or option == "platinum_relics":
            counts.append([30, 0] if sapphire_enabled else [26, 0])  # Ski Crazed, Area 51?, Rings of Power, and Eggipus Rex require warp 6 access via sapphire_relics.
    
    row_total = [sum([count[0] for count in counts]), sum([count[1] for count in counts])]
    return counts, row_total

def find_problem() -> tuple[bool, int]:
    clear_gems_enabled = options_list[options.index("clear_gems")] == 1
    gold_relics_enabled = options_list[options.index("gold_relics")] == 1
    platinum_relics_enabled = options_list[options.index("platinum_relics")] == 1
    warps_enabled = options_list[options.index("warp_unlocks")] == 1
    levels_enabled = options_list[options.index("level_unlocks")] == 1
    
    # level_unlocks requires at least 2 of clear_gems, gold_relics, or platinum_relics on
    enabled_count = sum([clear_gems_enabled, gold_relics_enabled, platinum_relics_enabled])
    if levels_enabled and enabled_count < 2:
        return True, 1
    
    # warp_unlocks requires at least one of clear_gems, gold_relics, or platinum_relics on.
    if warps_enabled and not clear_gems_enabled and not gold_relics_enabled and not platinum_relics_enabled:
        return True, 2

    return False, 0

# options is the basis of all the scaling here: how many options there are to consider. This script is designed with the assumption that each is a binary toggle (either off or on).
# The current options list is ordered very specifically due to how auto_corrections is emulated. warp_unlocks and level_unlocks must come first, because they need to be processed before the options that they may force on.
options = ["clear_gems", "colored_gems", "warp_unlocks", "level_unlocks", "sapphire_relics", "gold_relics", "platinum_relics"]
n = int(math.pow(2, len(options)))  # 2^n permutations
original_options_lists = []  # stores the original form of each permutation, since they might get auto_corrections adjustments. Original form is included in final output.
yes_count, no_count, error_count = 0, 0, 0  # stored for statistics output at the end

row_header = ""
for option in options:
    row_header += f"{option:<20}"

row_header += f"{'TOTAL':<20}"
row_header += f"{'OK?':<20}"
row_header += f"{'PERMUTATION':<20}"
print(row_header)
print("-"*len(row_header))

for row in range(n):
    # row is converted from decimal to binary to determine which options are enabled at each step
    # e.g. value of 2 is 0000010, so only 2nd to last option is enabled then.
    
    # This line does a lot at once. For example, if current_row is 5 and there are 7 options, this line generates options_list as [0, 0, 0, 0, 1, 0, 1].
    # It does this by converting 5 to a binary string (0000101) with enough padding to make it 7 bits, and then converts each of those characters into ints and puts them into the list.
    options_list = [int(num) for num in list(f"{row:0{len(options)}b}")]
    original_options_lists.append("".join(str(num) for num in options_list))
    
    amount_list, total = get_amounts()
    if total[1] > total[0]: found, code = find_problem()
    else: found, code = False, 0
    
    # print row data
    output = ""
    for amount in amount_list:
        entry = f"{amount[0]}/{amount[1]}"
        output += f"{entry:<20}"
        
    total_entry = f"{total[0]}/{total[1]}"
    output += f"{total_entry:<20}"
    
    err_txt = "ERROR " + str(code)
    if found: output += f"{err_txt:<20}"
    elif not found and total[0] >= total[1]: output += f"{'YES':<20}"
    elif not found and total[0] < total[1]: output += f"{'NO':<20}"
    
    output += original_options_lists[row]
    
    if "YES" in output: yes_count += 1
    elif "NO" in output: no_count += 1
    elif "ERROR" in output: error_count += 1

    print(output)

print()
print(f"YES: {yes_count}/{n} ({(yes_count/n)*100:.2f}%)")
print(f"NO: {no_count}/{n} ({(no_count/n)*100:.2f}%)")
print(f"ERROR: {error_count}/{n} ({(error_count/n)*100:.2f}%)")