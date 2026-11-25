from typing import Optional, Any
from BaseClasses import MultiWorld


# Use this if you want to override the default behavior of is_option_enabled
# Return True to enable the category, False to disable it, or None to use the default behavior
def before_is_category_enabled(multiworld: MultiWorld, player: int, category_name: str) -> Optional[bool]:
    from ..Helpers import get_option_value
    # A few categories have extended logic here that goes beyond just simple toggles, or also requires referencing a Range option.
    # 1) Gold Relics and Platinum Relics go through gold_relic_checks and platinum_relic_checks, both of which are not simple toggles.
    #    they have values 1 and 2 (for on_casual and on_speedrun), so those must be checked more directly here.
    if category_name == "Gold Relics":
        return get_option_value(multiworld, player, "gold_relic_checks") in [1, 2]  # 1 = on_casual, 2 = on_speedrun
    elif category_name == "Platinum Relics":
        return get_option_value(multiworld, player, "platinum_relic_checks") in [1, 2]  # 1 = on_casual, 2 = on_speedrun
    
    # 2) Gold Relic Events and Platinum Relic Events is basically the same thing. The categories are virtually identical,
    #    with events only applying to, well, events. However, gold and platinum events are only ever used when determining
    #    goal progress, so they have an additional check for if that goal is selected.
    if category_name == "Gold Relic Events":
        return get_option_value(multiworld, player, "gold_relic_checks") in [1, 2] and get_option_value(multiworld, player, "goal") == 3
    elif category_name == "Platinum Relic Events":
        return get_option_value(multiworld, player, "platinum_relic_checks") in [1, 2] and get_option_value(multiworld, player, "goal") == 4
    
    return None

# Use this if you want to override the default behavior of is_option_enabled
# Return True to enable the item, False to disable it, or None to use the default behavior
def before_is_item_enabled(multiworld: MultiWorld, player: int, item:  dict[str, Any]) -> Optional[bool]:
    return None

# Use this if you want to override the default behavior of is_option_enabled
# Return True to enable the location, False to disable it, or None to use the default behavior
def before_is_location_enabled(multiworld: MultiWorld, player: int, location:  dict[str, Any]) -> Optional[bool]:
    return None

# Use this if you want to override the default behavior of is_option_enabled
# Return True to enable the event, False to disable it, or None to use the default behavior
def before_is_event_enabled(multiworld: MultiWorld, player: int, event:  dict[str, Any]) -> Optional[bool]:
    return None
