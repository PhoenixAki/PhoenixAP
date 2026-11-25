from typing import Optional, Any
from BaseClasses import MultiWorld


# Use this if you want to override the default behavior of is_option_enabled
# Return True to enable the category, False to disable it, or None to use the default behavior
def before_is_category_enabled(multiworld: MultiWorld, player: int, category_name: str) -> Optional[bool]:
    # gold_relic_checks and platinum_relic_checks are choices with their "on" values being 1 and 2.
    # Categories normally look for Toggle options to enable them naturally, so this hook extends that behavior for them.
    from ..Helpers import get_option_value
    if category_name == "Gold Relics":
        return get_option_value(multiworld, player, "gold_relic_checks") in [1, 2]  # 1 = on_running, 2 = on_hard
    elif category_name == "Platinum Relics":
        return get_option_value(multiworld, player, "platinum_relic_checks") in [1, 2]  # 1 = on_running, 2 = on_hard
    else:
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
