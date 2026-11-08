from dataclasses import dataclass
import itertools

from Options import OptionSet, PerGameCommonOptions, Toggle, Choice, Range, OptionGroup,StartInventoryPool, OptionDict, OptionCounter
from . import consts

###############DEATHLINK###############
class DeathLink(Choice):
    """Determines DeathLink behavior.

    disabled: Disabled.
    Shielded: The Butterfly Jar will protect you from a received DeathLink death, if you have it.
    Enabled: Enabled without shielding."""
    display_name = "Death Link"
    option_disabled = 0
    option_shielded = 1
    option_enabled = 2
    default = 0
    

class DeathLinkAmnesty(Range):
    """If DeathLink is enabled, this option decides how many in-game deaths need to occur before a DeathLink
    death is sent out to the multiworld. The game mod tracks your deaths on the pause menu's box labeled "DL:"."""
    display_name = "Death Link Amnesty"
    range_start = 1
    range_end = 100
    default = 1

###############GENERATION SETTINGS###############
class LoggingLevel(Choice):
    """Choose how much Spyro AHT generation information should be logged.
    The log will contain messages from all levels up to, and including, your choice. For example, "medium" will log low
    and medium messages, but not high or maximum messages. **Warning messages stemming from YAML issues are always logged.**
    
    None: No additional logging beyond warnings.
    Low: Logs notable generation steps, such as "Checking for common YAML option/setting issues".
    Medium: Logs useful debugging information, such as listing your randomized shop prices. This is the default because
      the information in these messages can be very helpful when making bug reports.
    High: Logs messages with extra generation logic, such as "Fire Breath has been placed into Starter Checks: Breath."
    Maximum: Logs with extreme detail, such as noting every single item created."""
    option_none = 1
    option_low = 2
    option_medium = 3
    option_high = 4
    option_maximum = 5
    default = 3
    display_name = "Logging Level"
    

class AutoCorrections(Choice):
    """Chooses the logging behavior of the generator if YAML issues are encountered. It is recommended to leave this
    set to fix_minor, especially if intending to randomize multiple options. Clashes stemming from this (such as having
    fireworks_goal on but having firework_checks disabled) are fixed by fix_minor.
    
    halt: Generation will be strictly halted upon any sort of YAML issue.
    chaos: The generator will not halt or make changes, even if there is a known problem or high likelihood of generation failing.
    fix_minor: Only issues deemed minor will be fixed (such as the above example with fireworks_goal).
    fix_major: All issues will be fixed, even if it has a major impact (such as changing your starting realm to avoid an impossible start).
    
    A full, detailed list of every scenario that can lead to a generation issue can be found on the project's wiki,
    linked below. auto_corrections is not capable of fixing issues with the base syntax of your YAML.
    https://github.com/PhoenixAki/PhoenixAP/wiki/Spyro:-AHT-1.2-%E2%80%90-List-of-auto_corrections-Fixes"""
    display_name = "Auto Corrections"
    option_halt = 0
    option_chaos = 1
    option_fix_minor = 2
    option_fix_major = 3
    default = 2

###############GOAL###############
class BossGoals(OptionSet):
    """Adds a goal requirement to defeat a number of boss(es). You can enter "Random" to have a random selection
    of bosses chosen, even if you also choose a few bosses explicitly alongside "Random".
    
    Note that this + all other goals are based on AHT checks. In specific circumstances, this can result in AHT
    registering goals unexpectedly early. See the below project wiki FAQ post for more info.
    https://github.com/PhoenixAki/PhoenixAP/wiki/Spyro:-AHT-1-%E2%80%90-Setup-Guide-&-FAQ#i-goaled-early-what-gives 
    
    Valid Options: ["Gnasty Gnorc", "Ineptune", "Red", "Mecha-Red", "Random"]"""
    display_name = "Boss Goals"
    valid_keys = ("Gnasty Gnorc", "Ineptune", "Red", "Mecha-Red", "Random")
    default = ["Gnasty Gnorc", "Ineptune", "Red", "Mecha-Red"]


class DarkGemsGoal(Range):
    """Adds a goal requirement to complete a number of Dark Gem checks."""
    display_name = "Dark Gems Goal"
    range_start = 0
    range_end = 40
    default = 0
    

class LightGemsGoal(Range):
    """Adds a goal requirement to complete a number of Light Gem checks."""
    display_name = "Light Gems Goal"
    range_start = 0
    range_end = 100
    default = 0
    

class DragonEggsGoal(Range):
    """Adds a goal requirement to complete a number of Dragon Egg checks."""
    display_name = "Dragon Eggs Goal"
    range_start = 0
    range_end = 80
    default = 0
    

class FireworksGoal(Range):
    """Adds a goal requirement to complete a number of firework checks. firework_checks must be enabled.""" 
    display_name = "Fireworks Goal"
    range_start = 0
    range_end = 22
    default = 0
    

class ShopItemsGoal(Range):
    """Adds a goal requirement to purchase a number of randomized shop items. shop_randomization must be enabled.
    Keep in mind that the first randomized shop item is always free."""
    display_name = "Shop Items Goal"
    range_start = 0
    range_end = 56
    default = 0
    

class LockedChestsGoal(Range):
    """Adds a goal requirement to open a number of locked chests."""
    display_name = "Locked Chests Goal"
    range_start = 0
    range_end = 52
    default = 0


class EldersGoal(OptionSet):
    """Adds a goal requirement to talk to a number of elder dragons. You can enter "Random" to have a random selection
    of elders chosen, even if you also choose a few elders explicitly alongside "Random".
    
    Valid Options: ["Elder Tomas", "Elder Magnus", "Elder Titan", "Elder Astor", "Random"]"""
    display_name = "Elders Goal"
    valid_keys = ("Elder Tomas", "Elder Magnus", "Elder Titan", "Elder Astor", "Random")
    default = frozenset()


class MinigamesGoal(OptionDict):
    """Adds a goal requirement to complete minigames. Next to each, you can enter any of the following:
    - 0-8: complete this many to goal.
    - Random-on: picks a random number from 1-8.
    - Random-off: 1/2 chance of 0, 1/2 chance of 1-8."""
    display_name = "Minigames Goal"
    valid_keys = ("Blink", "Cannon", "Sgt. Byrd", "Sparx")
    default = {
        "Blink": 0,
        "Cannon": 0,
        "Sgt. Byrd": 0,
        "Sparx": 0
    }
    

class ExcludeChestItems(Choice):
    """The checks for dragon_eggs_goal and light_gems_goal include locked chests which contain Dragon Eggs/Light Gems.
    This option lets you limit them to only Dragon Eggs and Light Gems from non-chest sources."""
    display_name = "Exclude Chest Items"
    option_disabled = 0
    option_exclude_eggs = 1
    option_exclude_light_gems = 2
    option_exclude_both = 3
    default = 0
    
###############CHECKS AND ITEMS###############
class EnabledTricks(OptionSet):
    """Many things in AHT can be done using "tricks", which by default you aren't expected to do. This option lets you choose
    to enable a series of tricks that you may be expected to do. These tricks can be enabled individually or through a few
    presets (Easy, Medium, Hard, Other). You can also combine them, for example as ["Easy", "Medium", "some trick name here"].
    Entering "Random" will pick a subset of not-already-chosen tricks.
    
    See here for a full list of tricks: https://github.com/PhoenixAki/PhoenixAP/wiki/Spyro:-AHT-3.1-%E2%80%90-List-of-Tricks
    Valid options: ["Easy", "Medium", "Hard", "Other", "Random", "trick names from the link above"]"""
    display_name = "Enabled Tricks"
    valid_keys = ("Easy", "Medium", "Hard", "Other", "Random", *itertools.chain(*consts.TRICK_LEVELS.values()))
    default = frozenset()
    
    
class OpenWorldMode(Choice):
    """In vanilla AHT, you can only teleport to a remote shop pad once you have physically reached it.
    open_world_mode lets you choose from a variety of new ways to unlock shop pads through Archipelago items.
    Any choice besides 'vanilla' requires enabling "Teleport Across Realms" in time_savers to prevent potential softlock scenarios.
    
    vanilla: Vanilla game behavior.
    full: All shop pads are unlocked from the start of the seed.
    randomized: Shop pads unlock individually e.g. "Dark Mine - Miner's Drop Shop Unlock".
    progressive_levels: Shop pads unlock per-level in vanilla game order e.g. "Progressive Crocovile Swamp Shop Unlock". 
    reverse_progressive_levels: Same as progressive_levels, but backwards vanilla order.
    full_level: All shop pads in a level will unlock at once e.g. "Sunken Ruins - Shop Unlock".
    full_realm: All shop pads in a realm will unlock at once e.g. "Icy Wilderness - Shop Unlock"."""
    display_name = "Open World Mode"
    option_vanilla = 0
    option_full = 1
    option_randomized = 2
    option_progressive_levels = 3
    option_reverse_progressive_levels = 4
    option_full_levels = 5
    option_full_realms = 6
    default = 0
    

class FireworkChecks(Toggle):
    """Enables 22 checks for flaming fireworks."""
    display_name = "Firework Checks"
    default = 0


class MinigameChecks(OptionDict):
    """Customize whether each minigame will be fully enabled, enabled with only Dragon Egg challenges,
    or disabled. For each minigame, enter one of:
    
    Enabled: Keeps vanilla behavior for this minigame.
    Easy: Disables the Light Gem challenges for this minigame.
    Disabled: Fully disables this minigame. Its NPCs will not spawn at all in-game.
      If cannon minigames are disabled, Fredneck's lilypads will instead raise when breaking the Dark Gem before him.
    Random: Random choice between Enabled, Easy, and Disabled."""
    display_name = "Minigame Checks"
    valid_keys = ("Blink", "Cannon", "Sgt. Byrd", "Sparx")
    default = {
        "Blink": "Enabled",
        "Cannon": "Enabled",
        "Sgt. Byrd": "Enabled",
        "Sparx": "Enabled"
    }


class ItemBundles(OptionCounter):
    """Some AHT AP items can be bundled together so that you receive multiple at a time. For example, if you set the Dark Gem
    bundle size to 7, there would be 6 "Dark Gem Bundle" items created. 5 would be worth 7 each (35 total) and the 6th
    would be worth 5 (to get to 40 total).
    
    Currently supported items for bundling:
    Dark Gem: bundle size 1-40, or 0 for random choice.
    Global Lockpick: bundle size 1-52, or 0 for random choice. Requires chest_keys to be set to global_lockpicks.
    Light Gem: bundle size 1-100, or 0 for random choice."""
    display_name = "Item Bundles"
    valid_keys = ("Dark Gem", "Global Lockpick", "Light Gem")
    min = 0
    max = 100
    default = {
        "Dark Gem": 1,
        "Global Lockpick": 1,
        "Light Gem": 1
    }


class CannonLock(Toggle):
    """If enabled, you will not be able to use cannons in the game until you receive the "Cannon Unlock" item.
    Cannons in minigames are excluded, and are always usable."""
    display_name = "Cannon Lock"
    default = 0
    
    
class TrapPercentage(Range):
    """Decides how much of the junk (fillers + traps) item pool will be traps, as a percentage out of 100."""
    display_name = "Trap Percentage"
    range_start = 0
    range_end = 100
    default = 0


class FillerItems(OptionSet):
    """Choose which filler (neutral-to-positive effect) items to enable.
    Entering "Random" will pick a subset of not-already-chosen filler items.

    Dragon Egg: These are filler due to having no logical impact.
    Fire/Electric/Water/Ice Bomb: Only usable if their respective breath is unlocked.
    Gem Pack: Gives a random amount of gems (400-600, 800-1200 if you have double gems).
      It is advised to disable these if using shop_randomization, as shop logic does not account for gem packs.
    Shinies: A set 16 items which do nothing, but have humorous names referencing AHT or other games/series. 
    
    Valid options: ["Dragon Egg", "Fire Bomb", "Electric Bomb", "Water Bomb", "Ice Bomb", "Gem Pack", "Shinies", "Random"]"""
    display_name = "Filler Items"
    valid_keys = ("Dragon Egg", "Fire Bomb", "Electric Bomb", "Water Bomb", "Ice Bomb", "Gem Pack", "Shinies", "Random")
    default = ("Dragon Egg", "Fire Bomb", "Electric Bomb", "Water Bomb", "Ice Bomb")


class TrapItems(OptionSet):
    """Choose which trap (neutral-to-negative effect) items to enable. Spam Call, Reverse Controls, and Bounce are
    queued and triggered sequentially. Traps received while offline will get processed upon next client reconnection.
    Entering "Random" will pick a subset of not-already-chosen trap items.

    Spam Call: Random lines of Moneybags dialog + shop music will play for trap_length seconds.
    Reverse Controls: Flips the X and Y axis of both control sticks for trap_length seconds.
    Damage Sparx: Take 1 hit of damage. Does nothing if Sparxless or if in a Sparx minigame.
    Gem Tax: Takes away a random amount of gems (500-1000).
      It is advised to disable these if using shop_randomization, as shop logic does not account for gem taxes.
    Bounce: The player character's model will bounce for trap_length seconds. Can negatively affect first-person camera aiming.
    
    Valid options: ["Spam Call", "Reverse Controls", "Damage Sparx", "Gem Tax", "Bounce", "Random"]"""
    display_name = "Trap Items"
    valid_keys = ("Spam Call", "Reverse Controls", "Damage Sparx", "Gem Tax", "Bounce", "Random")
    default = frozenset()


class TrapLength(OptionCounter):
    """Determines how long Spam Call, Reverse Controls, and Bounce run for, in seconds (maximum 60).
    Set to 0 to have a random number of seconds chosen."""
    display_name = "Trap Length"
    valid_keys = ("Spam Call", "Reverse Controls", "Bounce")
    min = 0
    max = 60
    default = {
        "Spam Call": 30,
        "Reverse Controls": 30,
        "Bounce": 30
    }

###############START OF GAME###############
class StartingBreaths(OptionSet):
    """Choose which breath(s) you want to start with.
    
    If multiple are listed, one will go into "Starter Checks: Breath", and the rest will go into your start inventory.
    If the list is left empty, you will start with no breath.
    Entering "Random" will pick a subset of not-already-chosen breaths.
    
    Valid Options: ["Fire Breath", "Electric Breath", "Water Breath", "Ice Breath", "Random"]"""
    display_name = "Starting Breaths"
    valid_keys = ("Fire Breath", "Electric Breath", "Water Breath", "Ice Breath", "Random")
    default = ("Fire Breath",)


class MovementRandomization(OptionSet):
    """Choose whether to randomize each of the 3 base movement abilities (glide, swim, and charge).
    If any are randomized, you will start with a random item from Archipelago in their place.
    Entering "Random" will pick a subset of not-already-chosen abilities. 
    
    Valid Options: ["Glide", "Swim", "Charge", "Random"]"""
    display_name = "Movement Randomization"
    valid_keys = ("Glide", "Swim", "Charge", "Random")
    default = frozenset()


class StartingRealms(OptionSet):
    """Choose which realm(s) to start with realm access cards for. 
    
    If the list is empty, a random subset of realms will be chosen for you.
    If using full open_world_mode, you will start with all 4 access cards.
    If using non-full open_world_mode, non-starting realms are unlocked via shop unlocks instead of access cards.
    
    Starting with only Icy Wilderness, shop_randomization off, and movement_randomization empty is disallowed due to impossible starts.
    
    Valid Options: ["Dragon Kingdom", "Lost Cities", "Icy Wilderness", "Volcanic Isle"]"""
    display_name = "Starting Realms"
    valid_keys = ("Dragon Kingdom", "Lost Cities", "Icy Wilderness", "Volcanic Isle")
    default = ("Dragon Kingdom",)
    
###############SHOP SETTINGS###############
class ShopRandomization(Toggle):
    """Choose whether to randomize Moneybags' shop. If not randomized, it will function identically to the vanilla game. 

    If randomized, vanilla game shop items will be replaced with items from Archipelago. This has a few consequences:
        - Double Gems, if enabled, is permanent once received, as is the Butterfly Jar (it replenishes on death).
        - There is no limit to how many lockpicks or breath bombs you can hold at once.
        - Remote shop pads will not upcharge you for items."""
    display_name = "Shop Randomization"
    default = 0
    

class ChestKeys(Choice):
    """Choose how you want to open locked chests. The items will be placed in the shop if shop_randomization
    is disabled, or placed into the world by Archipelago otherwise.
    
    The way chests come into logic depends on chest_keys as well as shop_randomization. See the project wiki for a breakdown:
    https://github.com/PhoenixAki/PhoenixAP/wiki/Spyro:-AHT-2-%E2%80%90-Features-(Overview)
    
    global_lockpicks: each opens 1 chest anywhere in the game. Same as vanilla game lockpicks.
    level_lockpicks: each opens 1 chest in a specific level e.g. "Sunken Ruins Lockpick"
    level_key_rings: each opens all chests in 1 level e.g. "Dragon Village Key Ring".
    realm_key_rings: each opens all chests in 1 realm e.g. "Lost Cities Key Ring"."""
    display_name = "Chest Keys"
    option_global_lockpicks = 0
    option_level_lockpicks = 1
    option_level_key_rings = 2
    option_realm_key_rings = 3
    default = 0


class ShopItemCount(Range):
    """Determines how many shop items checks you will have, if shop_randomization is on."""
    display_name = "Shop Item Count"
    range_start = 2
    range_end = 56
    default = 18


class ShopLogic(Choice):
    """When using shop_randomization, how many gems you have access to is tracked. This is used to logically spread out shop item purchases.
    The formula below is used to calculate a "base shop price", and your choice here determines item prices using that.
    The first item is always free, to prevent restrictive starts (Moneybags offers it as a loss-leader).
    
    unordered: items will have equal prices and can be bought in any order. Logic assumes you will buy them in order left -> right.
    ordered: items will be free, but get unlocked at a steadily increasing amount of gems, which enforces the logical order.
     
    ***********************************FORMULA (for the math nerds)***********************************
    blink_gems_total = (20,203 - exclusions) * blink_gems%
    non_blink_enemies_total = 16,353 * non_blink_enemies%
    other_gems_total = (105,357 - exclusions) * other_gems%
    gem_total = blink_gems_total + non_blink_enemies_total + other_gems_total
    base_shop_price = gem_total / (shop_item_count - 1)

    If shop_logic is unordered, shop items will all cost base_shop_price, rounded down as needed.
    If shop_logic is ordered, shop items will cost base_shop_price * 1, base_shop_price * 2, etc., rounded down as needed.
    **************************************************************************************************"""
    display_name = "Shop Logic"
    option_unordered = 0
    option_ordered = 1
    default = 0 
    

class BlinkGems(Range):
    """Decides what % of gems from Blink minigames you want to be expected to collect, if shop_randomization is enabled.
    For example, a value of 50 means being expected to collect approximately 50% of such gems.
    Any Blink minigames that are added to exclude_locations, or disabled via minigame_checks, are omitted."""
    display_name = "Blink Gems"
    range_start = 0
    range_end = 100
    default = 75


class NonBlinkEnemies(Range):
    """Decides what % of gems from enemies you want to be expected to collect, if shop_randomization is enabled.
    Only applies to enemies in Spyro & Hunter levels."""
    display_name = "Non Blink Enemies"
    range_start = 0
    range_end = 100
    default = 75


class OtherGems(Range):
    """Decides what % of gems you want to be expected to collect from gems on the ground, breakable containers, and
    Sgt. Byrd + Sparx minigames, if shop_randomization is enabled.
    Any Sgt. Byrd and Sparx minigames that are added to exclude_locations, or disabled via minigame_checks, are omitted."""
    display_name = "Other Gems"
    range_start = 0
    range_end = 100
    default = 75
    
    
class DoubleGems(Choice):
    """Enables or disables the Double Gems item, if shop_randomization is enabled. It is advised to keep this disabled if so,
    as shop logic does not account for gems received through Double Gems."""
    display_name = "Double Gems"
    option_disabled = 0
    option_enabled = 1
    default = 0

###############GATE & GADGET COSTS###############
class RandomizeBossLairDoorCosts(Choice):
    """Determines the method of calculating Dark Gem costs for boss lairs.

    default: Each boss lair has their vanilla cost (10/20/30/40).
    randomized: Costs are randomly generated using the Boss Lair Min and Boss Lair Max values defined in random_costs.
    shuffle: Vanilla boss lair costs are shuffled between each other (still 10/20/30/40 but in a random order)."""
    display_name = "Randomize Boss Lair Door Costs"
    option_default = 0
    option_randomized = 1
    option_shuffle = 2
    default = 0


class RandomizeLightGemDoorCosts(Choice):
    """Determines the method of calculating Light Gem costs for Light Gem Doors.

    default: Each door has their vanilla cost (20/45/70/95).
    randomized: Costs are randomly generated using the Light Gem Door Min and Light Gem Door Max values defined in random_costs.
    shuffle: Each door has their vanilla cost shuffled with the others (still 20/45/70/95 but in a random order)."""
    display_name = "Randomize Light Gem Door Costs"
    option_default = 0
    option_randomized = 1
    option_shuffle = 2
    default = 0


class RandomizeGadgetCosts(Choice):
    """Determines the method of calculating Light Gem costs for gadgets. Listed in order of Ball Gadget -> Invincibility -> Supercharge.

    default: Each gadget has their vanilla cost (8/24/40).
    randomized: Costs are randomly generated using the Gadget Min and Gadget Max values defined in random_costs.
    shuffle: Each gadget has their vanilla cost shuffled with the others (still 8/24/40 but in a random order)."""
    display_name = "Randomize Gadget Costs"
    option_default = 0
    option_randomized = 1
    option_shuffle = 2
    default = 0


class RandomCosts(OptionCounter):
    """If randomize_boss_lair_door_costs, randomize_light_gem_door_costs, or randomize_gadget_costs are set to randomized,
    this option determines the bounds of each randomly generated cost. Enter 0 for any to get a random choice.
    
    Light Gem door and gadget costs can't exceed 90 if open world mode is set to vanilla, due to being too restrictive."""
    display_name = "Random Costs"
    valid_keys = ("Boss Lair Min", "Boss Lair Max", "Light Gem Door Min", "Light Gem Door Max", "Gadget Min", "Gadget Max")
    min = 0
    max = 100
    default = {
        "Boss Lair Min": 10,
        "Boss Lair Max": 40,
        "Light Gem Door Min": 20,
        "Light Gem Door Max": 95,
        "Gadget Min": 8,
        "Gadget Max": 40
    }


class BossLairForcing(Choice):
    """Decides if the generator should force any boss lair(s) to have the most expensive Dark Gem costs.
    Useful if you want to ensure any bosses get unlocked after the others, even if costs are fully randomized.
    
    unchanged: Leaves boss lair costs untouched.
    gnasty_gnorc/ineptune/red/mecha_red: Swaps that boss's cost with the highest cost.
    automatic: Swaps all goal boss costs so that they are collectively the highest."""
    display_name = "Boss Lair Forcing"
    option_unchanged = 0
    option_gnasty_gnorc = 1
    option_ineptune = 2
    option_red = 3
    option_mecha_red = 4
    option_automatic = 5
    default = 0
    
###############QUALITY OF LIFE###############
class PauseMenuPatch(Choice):
    """Decides which of 2 pause menu patches you can choose between which can help with escaping situations where you're stuck.
    
    open_shop: pressing Y will open the shop if you are Spyro. If using non-full open_world_mode, this will auto-unlock
      your starting realm's "Depot" shop to prevent potential softlock scenarios.
    teleport_to_hub: holding Y will bring you to the current realm's realm teleporter. If using non-full open_world_mode,
      this will be considered a valid alternative way to logically access a realm's hub level."""
    display_name = "Pause Menu Patch"
    option_open_shop = 0
    option_teleport_to_hub = 1
    default = 0


class ShopPadProximityActivation(Toggle):
    """When using non-full open_world_mode, shop pads only unlock via their unlock items. This can lead to situations where you
    can physically reach a shop pad but be unable to teleport back to it after, adding walking time on revisits. Enabling this
    allows you to teleport to any shop you've interacted with, even if you don't have its unlock item yet."""
    display_name = "Shop Pad Proximity Activation"
    default = 1


class AutoHinting(OptionDict):
    """Toggles automatic hinting for boss rewards (upon opening their lair), minigames (upon talking to NPCs), and shop
    items (upon creating the save file). For each, you can enter "On", "Off", or "Random"."""
    display_name = "Auto Hinting"
    valid_keys = ("Bosses", "Minigames", "Shop Items")
    default = {
        "Bosses": "Off",
        "Minigames": "Off",
        "Shop Items": "Off"
    }
    
    
class DisguiseShopItems(OptionSet):
    """When the shop is randomized, items show as "<player name>'s <item name>". By default, they use the lockpick model,
    but this is overridden in some cases, such as key rings using the keychain model. This option lets you disguise your
    randomized shop items in a few ways, to add more mystery to your purchases. Hinting still works even if disguised.
    
    Player: Replaced player names with ???.
    Item: Replaces item names with ???.
    Model: All items will use the lockpick model.
     
    Valid options: ["Player", "Item", "Model", "Random"]"""
    valid_keys = ("Player", "Item", "Model", "Random")
    display_name = "Disguise Shop Items"
    default = frozenset()
    

class EasyBosses(OptionSet):
    """Bosses listed below will take triple damage, significantly shortening fights.
    Entering "Random" will pick a subset of not-already-chosen bosses.
    
    Valid options: ["Gnasty Gnorc", "Ineptune", "Red", "Mecha-Red", "Random"]"""
    display_name = "Easy Bosses"
    valid_keys = ("Gnasty Gnorc", "Ineptune", "Red", "Mecha-Red", "Random")
    default = ("Gnasty Gnorc", "Ineptune", "Red", "Mecha-Red")


class TimeSavers(OptionDict):
    """Choose which time-saving quality of life patches are enabled. For each, enter "On", "Off", or "Random".
    Skip Cutscenes: enables skipping most cutscenes with the Y button.
    Skip Elevators: enables skipping long elevator waits with loading screen.
    Teleport Across Realms: enables teleporting across realms using normal shop pads."""
    display_name = "Time Savers"
    valid_keys = ("Skip Cutscenes", "Skip Elevators", "Teleport Across Realms")
    default = {
        "Skip Cutscenes": "On",
        "Skip Elevators": "On",
        "Teleport Across Realms": "On"
    }

@dataclass
class SpyroAHTOptions(PerGameCommonOptions):
    death_link: DeathLink
    death_link_amnesty: DeathLinkAmnesty
    
    logging_level: LoggingLevel
    auto_corrections: AutoCorrections
    start_inventory_from_pool: StartInventoryPool
    
    boss_goal: BossGoals
    dark_gems_goal: DarkGemsGoal
    light_gems_goal: LightGemsGoal
    dragon_eggs_goal: DragonEggsGoal
    fireworks_goal: FireworksGoal
    shop_items_goal: ShopItemsGoal
    locked_chests_goal: LockedChestsGoal
    exclude_chest_items: ExcludeChestItems
    elders_goal: EldersGoal
    minigames_goal: MinigamesGoal
    
    enabled_tricks: EnabledTricks
    open_world_mode: OpenWorldMode
    firework_checks: FireworkChecks
    minigame_checks: MinigameChecks
    item_bundles: ItemBundles
    cannon_lock: CannonLock
    trap_percentage: TrapPercentage
    filler_items: FillerItems
    trap_items: TrapItems
    trap_length: TrapLength
    
    starting_breaths: StartingBreaths
    movement_randomization: MovementRandomization
    starting_realms: StartingRealms
    
    shop_randomization: ShopRandomization
    chest_keys: ChestKeys
    shop_item_count: ShopItemCount
    shop_logic: ShopLogic
    blink_gems: BlinkGems
    non_blink_enemies: NonBlinkEnemies
    other_gems: OtherGems
    double_gems: DoubleGems
    
    randomize_boss_lair_door_costs: RandomizeBossLairDoorCosts
    randomize_light_gem_door_costs: RandomizeLightGemDoorCosts
    randomize_gadget_costs: RandomizeGadgetCosts
    random_costs: RandomCosts
    boss_lair_forcing: BossLairForcing
    
    pause_menu_patch: PauseMenuPatch
    shop_pad_proximity_activation: ShopPadProximityActivation
    auto_hinting: AutoHinting
    disguise_shop_items: DisguiseShopItems
    easy_bosses: EasyBosses
    time_savers: TimeSavers
    
    
spyro_options_groups = [
    OptionGroup("DEATHLINK", [
        DeathLink, DeathLinkAmnesty
    ]),
    OptionGroup("GENERATION SETTINGS", [
        LoggingLevel, AutoCorrections
    ]),
    OptionGroup("GOAL", [
        BossGoals, DarkGemsGoal, LightGemsGoal, DragonEggsGoal, FireworksGoal, ShopItemsGoal, 
        LockedChestsGoal, EldersGoal, MinigamesGoal, ExcludeChestItems
    ]),
    OptionGroup("CHECKS AND ITEMS", [
        EnabledTricks, OpenWorldMode, FireworkChecks, MinigameChecks, ItemBundles, CannonLock,
        TrapPercentage, FillerItems, TrapItems, TrapLength
    ]),
    OptionGroup("START OF GAME", [
        StartingBreaths, MovementRandomization, StartingRealms
    ]),
    OptionGroup("SHOP SETTINGS", [
        ShopRandomization, ChestKeys, ShopItemCount, ShopLogic, BlinkGems, NonBlinkEnemies, OtherGems, DoubleGems
    ]),
    OptionGroup("GATE & GADGET COSTS", [
        RandomizeBossLairDoorCosts, RandomizeLightGemDoorCosts, RandomizeGadgetCosts, RandomCosts, BossLairForcing
    ]),
    OptionGroup("QUALITY OF LIFE", [
        PauseMenuPatch, ShopPadProximityActivation, AutoHinting, DisguiseShopItems, EasyBosses, TimeSavers
    ])
]