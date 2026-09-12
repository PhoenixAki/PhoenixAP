from dataclasses import dataclass

from Options import OptionSet, PerGameCommonOptions, Toggle, Choice, Range, OptionGroup, StartInventoryPool, NamedRange

###############DEATHLINK###############
class DeathLink(Choice):
    """Determines DeathLink behavior.

    disabled: Disabled.
    Shielded: The Butterfly Jar will protect you from a received DeathLink death, if you have it.
    Enabled: Enabled without shielding."""
    display_name = "DeathLink"
    option_disabled = 0
    option_shielded = 1
    option_enabled = 2
    default = 0
    

class DeathLinkAmnesty(Range):
    """If DeathLink is enabled, this option decides how many in-game deaths need to occur before a DeathLink
    death is sent out to the multiworld. The game mod tracks your deaths on the pause menu's box labeled "DL:"."""
    display_name = "DeathLink Amnesty"
    range_start = 1
    range_end = 100
    default = 1

###############GENERATION SETTINGS###############
class LoggingLevel(Choice):
    """This option lets you decide how much Spyro AHT generation information should be logged.
    The log will contain messages from all levels up to, and including, your choice. For example, "medium" will log low
    and medium messages, but not high or maximum messages. **Warning messages stemming from YAML issues are always logged.**
    
    None: No additional logging beyond warnings.
    Low: Logs notable generation steps, such as "Checking if any minigames need vanilla rewards forced."
    Medium: Logs useful debugging information, such as listing your randomized shop prices. This is the default because
      the information in these messages can be very helpful when making bug reports.
    High: Logs messages with extra generation logic, such as "Fire Breath has been placed into Starter Checks: Breath."
    Maximum: Logs with extreme detail, such as noting every single item created.
    """
    option_none = 1
    option_low = 2
    option_medium = 3
    option_high = 4
    option_maximum = 5
    default = 3
    display_name = "Logging Level"
    

class AutoCorrections(Choice):
    """This option decides the behavior of the generator if YAML issues are encountered. It is strongly recommended to
    set this to fix_minor or fix_major if putting AHT AP into a larger multiworld. Doing so drastically decreases the
    chance of hitting a generation error after potentially a long time of generating.
    
    A full detailing of every edge case that exists, and how auto_corrections reacts to them, is beyond the scope
    of this YAML. A full list can be found at the link below. It is only capable of fixing issues that stem from
    combinations of AHT options - issues with the base syntax of your YAML are not automatically fixable.
    https://github.com/PhoenixAki/PhoenixAP/wiki/Spyro:-AHT-1.2-%E2%80%90-List-of-auto_corrections-Fixes
    
    halt: Generation will be strictly halted upon any sort of YAML issue.
    fix_minor: Minor YAML issues will be automatically fixed to avoid making too big an impact on the seed.
    fix_major: All known YAML issues will be fixed, even if the fix has a significant impact on the seed."""
    display_name = "Auto Corrections"
    option_halt = 0
    option_fix_minor = 1
    option_fix_major = 2
    default = 1

###############GOAL###############
class BossGoals(OptionSet):
    """This option lets you choose which bosses are required in order to goal. They will stack on top of other goals.
    Leave the list empty to have no boss requirements. You can enter "Random" to have a random selection of bosses chosen,
    even if you also choose a few bosses explicitly alongside "Random".
    
    Valid Options: ["Gnasty Gnorc", "Ineptune", "Red", "Mecha-Red", "Random"]"""
    display_name = "Boss Goals"
    valid_keys = ("Gnasty Gnorc", "Ineptune", "Red", "Mecha-Red", "Random")
    default = ["Mecha-Red"]


class DarkGemsGoal(NamedRange):
    """This option lets you require completing a number of Dark Gem checks in order to goal. This stacks on top of other goals.
    To enable this, enter a number 1-40 to require that many Dark Gem checks in order to goal.
    To disable this, enter 0. To have a random number 1-40 chosen, select "random-range-1-40", or enter -1."""
    display_name = "Dark Gems Goal"
    range_start = -1
    range_end = 40
    default = 0
    special_range_names = {
        "random-range-1-40": -1
    }
    

class LightGemsGoal(NamedRange):
    """This option lets you require completing a number of Light Gem checks in order to goal. This stacks on top of other goals.
    To enable this, enter a number 1-100 to require that many Dark Gem checks in order to goal.
    To disable this, enter 0. To have a random number 1-100 chosen, select "random-range-1-100", or enter -1."""
    display_name = "Light Gems Goal"
    range_start = -1
    range_end = 100
    default = 0
    special_range_names = {
        "random-range-1-100": -1
    }
    

class DragonEggsGoal(NamedRange):
    """This option lets you require completing a number of Dragon Egg checks in order to goal. This stacks on top of other goals.
    To enable this, enter a number 1-80 to require that many Dragon Egg checks in order to goal.
    To disable this, enter 0. To have a random number 1-80 chosen, select "random-range-1-80", or enter -1."""
    display_name = "Dragon Eggs Goal"
    range_start = -1
    range_end = 80
    default = 0
    special_range_names = {
        "random-range-1-80": -1
    }
    

class FireworksGoal(NamedRange):
    """This option lets you require completing a number of firework checks in order to goal. This stacks on top of other goals.
    To enable this, enter a number 1-22 to require that many firework checks in order to goal.
    To disable this, enter 0. To have a random number 1-22 chosen, select "random-range-1-22", or enter -1.
    This goal requires firework_checks to be enabled.""" 
    display_name = "Fireworks Goal"
    range_start = -1
    range_end = 22
    default = 0
    special_range_names = {
        "random-range-1-22": -1
    }
    

class ShopItemsGoal(NamedRange):
    """This option lets you require purchasing a number of randomized shop items in order to goal. This stacks on top of other goals.
    To enable this, enter a number 1-56 to require that many shop item purchases checks in order to goal.
    To disable this, enter 0. To have a random number 1-56 chosen, select "random-range-1-56", or enter -1.
    This goal requires shop_randomization to be enabled."""
    display_name = "Shop Items Goal"
    range_start = -1
    range_end = 56
    default = 0
    special_range_names = {
        "random-range-1-56": -1
    }
    

class LockedChestsGoal(NamedRange):
    """This option lets you require opening a number of locked chests in order to goal. This stacks on top of other goals.
    To enable this, enter a number 1-52 to require opening that many locked chests checks in order to goal.
    To disable this, enter 0. To have a random number 1-52 chosen, select "random-range-1-52", or enter -1."""
    display_name = "Locked Chests Goal"
    range_start = -1
    range_end = 52
    default = 0
    special_range_names = {
        "random-range-1-52": -1
    }
    
    
class ExcludeChestItems(Choice):
    """dragon_eggs_goal includes locked chests which contain Dragon Eggs as a valid way to make goal progress.
    light_gems_goal is the same with Light Gems. This option lets you limit these goals to only Dragon Eggs and Light
    Gems which come from other sources. Useful if wanting to require them as goals but with less requirement on locked chests."""
    display_name = "Exclude Chest Items"
    option_disabled = 0
    option_exclude_eggs = 1
    option_exclude_light_gems = 2
    option_exclude_both = 3
    default = 0
    
###############CHECKS AND ITEMS###############
class OpenWorldMode(Choice):
    """In the vanilla game, you can only teleport to a remote shop pad once you have physically reached it.
    open_world_mode lets you choose from a variety of ways to have shop pads become unlocked by Archipelago items.
    Any choice besides 'vanilla' requires enabling teleport_across_realms to prevent potential softlock scenarios.
    
    vanilla: Shop pads are only unlocked by physically reaching them.
    full: All shop pads are unlocked from the start of the seed.
    randomized: Shop pads unlock through individual AP items e.g. "Dark Mine - Miner's Drop Shop Unlock".
    progressive_levels: Shop pads unlock per-level in vanilla game order e.g. "Progressive Crocovile Swamp Shop Unlock". 
    reverse_progressive_levels: Same as progressive_levels, but backwards vanilla order.
    full_level: All shop pads in a level will unlock at once through AP items. e.g. "Sunken Ruins - Shop Unlock".
    full_realm: All shop pads in a realm will unlock at once through AP items. e.g. "Icy Wilderness - Shop Unlock"."""
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


class VanillaMinigameRewards(OptionSet):
    """This option lets you decide if you want any type of minigame to reward
    their vanilla Dragon Eggs and Light Gems instead of having randomized rewards.
    
    Valid options: ["Sgt. Byrd", "Blink", "Turret", "Sparx"]"""
    display_name = "Vanilla Minigame Rewards"
    valid_keys = ("Sgt. Byrd", "Blink", "Turret", "Sparx")
    default = frozenset()


class FillerItems(OptionSet):
    """This option lets you choose the contents of your filler item pool. Items will be chosen at random from the enabled categories.

    Dragon Eggs: These are considered filler due to having no impact on game progression.
    Breath Bombs: Fire, Electric, Water, and Ice Bombs. Bombs are only usable if you have their respective breath unlocked.
    Gem Packs: Gives a random amount of gems (400-600 or 800-1200 if you have double gems).
      It is advised to disable gem packs if randomizing the shop, as gem logic does not account for them.
    Generics: Items which do nothing, but have humorous names referencing things in the game and series.
    
    Valid options: ["Dragon Eggs", "Breath Bombs", "Gem Packs", "Generics"]"""
    display_name = "Filler Items"
    valid_keys = ("Dragon Eggs", "Breath Bombs", "Gem Packs", "Generics")
    default = ("Dragon Eggs", "Breath Bombs", "Gem Packs", "Generics")

###############START OF GAME###############
class StartingBreaths(OptionSet):
    """Choose which breath(s) you want to start with.
    
    If multiple breaths are listed, all will be given (one into "Starter Checks: Breath", the rest into your start inventory).
    "None" will start you with no breath, meaning "Starter Checks: Breath" will have a random item determined by Archipelago.
    If the list is left empty, 1 random breath will be chosen.
    
    Valid Options: ["Fire", "Electric", "Water", "Ice", "None"]"""
    display_name = "Starting Breaths"
    valid_keys = ("Fire", "Electric", "Water", "Ice", "None")
    default = ("Fire",)


class MovementRandomization(OptionSet):
    """Choose whether to randomize each of the 3 base movement abilities (glide, swim, and charge).
    If any are randomized, you will start with a random item from Archipelago in their place.
    
    Valid Options: ["Glide", "Swim", "Charge"]"""
    display_name = "Movement Randomization"
    valid_keys = ("Glide", "Swim", "Charge")
    default = frozenset()


class StartingRealms(OptionSet):
    """Choose which realm(s) you will start with realm access cards for. 
    
    If the list is left empty, 1 random realm will be chosen.
    If using full open_world_mode, you will start with all 4 access cards.
    If using non-full open_world_mode, non-starting realms will be unlocked when their "Depot" shops are unlocked.
        
    Starting in Icy Wilderness with shop_randomization odd and no movement abilities randomized is disallowed due to restrictive starts.
    
    Valid Options: ["Dragon Kingdom", "Lost Cities", "Icy Wilderness", "Volcanic Isle"]"""
    display_name = "Starting Realms"
    valid_keys = ("Dragon Kingdom", "Lost Cities", "Icy Wilderness", "Volcanic Isle")
    default = ("Dragon Kingdom",)
    
###############SHOP SETTINGS###############
class ShopRandomization(Toggle):
    """Determines whether to randomize Moneybags' shop. If not randomized, it will function identically to the vanilla game. 

    If randomized, vanilla game shop items will be replaced with items from Archipelago. This has a few consequences:
        - Double Gems, if enabled, is permanent once received, as is the Butterfly Jar (it replenishes on death if depleted).
        - There is no limit to how many lockpicks you can hold at once. Same with ammo for breath bombs.
        - Shop item prices will be the same everywhere i.e. remote shop pads will not upcharge you."""
    display_name = "Shop Randomization"
    default = 0
    

class KeyRings(Toggle):
    """This option decides whether you can purchase lockpicks or key rings, which are keys that open all locked chests in a level.
    
    If shop_randomization is off, they will be placed in the shop, and locked chests will be in logic as soon as you have access to them.
    If shop_randomization is on, they will be placed into the world by Archipelago. Locked chests will be in logic as you collect each
      level's key ring, or once you collect all 52 lockpicks."""
    display_name = "Key Rings"
    default = 0


class ShopItemCount(Range):
    """This option decides how many shop items you will have, if shop_randomization is on. The shop must have a minimum
    of 2 items to enable the gem logic system to function properly."""
    display_name = "Shop Item Count"
    range_start = 2
    range_end = 56
    default = 18


class ShopLogic(Choice):
    """When the shop is randomized, a series of "gem logic" rules tracks how many gems you have access to at all times.
    The generator uses these rules to determine how to logically spread out shop item purchases in one of 2 ways, determined by this option.
    
    unordered: shop items will all have the same price. You can buy them in whatever order you wish, but the generator assumes
      you will buy the items in order left -> right. This makes it possible to buy them in the "wrong" order which may require farming extra gems.
    ordered: shop items will instead display as "Unlocked at X Gems". Once you have X gems, the item will be free to purchase.
      Prices will steadily increase to enforce a specific order of unlocking the items, removing the risk of getting logically softlocked.
    
    Either way, the formula below is used to calculate your "base shop price", and your choice here determines the final prices.
    The first shop item is always free. If you don't fancy doing the math, you can tweak test seed(s) until you're happy with the prices.
    
    ********************************FORMULA INFO (for the math nerds)********************************
    blink_gems_total = (20,203 - exclusions) * blink_gems%
    non_blink_enemies_total = (16,353 - exclusions) * non_blink_enemies%
    other_gems_total = (105,357 - exclusions) * other_gems%
      If a full level location group or an individual minigame location is added to exclude_locations, the gems inside
      will be left out of the above calculations so you aren't logically expected to get those gems.
    gem_total = blink_gems_total + non_blink_enemies_total + other_gems_total
    base_shop_price = gem_total / (shop_item_count - 1)

    If shop_logic is unordered, shop items will all cost base_shop_price, rounded down as needed.
    If shop_logic is ordered, shop items will cost base_shop_price * 1, base_shop_price * 2, etc., rounded down as needed.
    *************************************************************************************************"""
    display_name = "Shop Logic"
    option_unordered = 0
    option_ordered = 1
    default = 0 
    

class BlinkGems(Range):
    """This option is used when shop_randomization is enabled. It lets you decide what % of gems from Blink minigames you want to
    be expected to collect. For example, a value of 50 means being expected to collect approximately 50% of such gems."""
    display_name = "Blink Gems"
    range_start = 0
    range_end = 100
    default = 75


class NonBlinkEnemies(Range):
    """This option is used when shop_randomization is enabled. It lets you decide what % of gems from enemies you want
    to be expected to collect. This only applies to enemies in Spyro & Hunter levels."""
    display_name = "Non-Blink Enemies"
    range_start = 0
    range_end = 100
    default = 75


class OtherGems(Range):
    """This option is used when shop_randomization is enabled. It lets you decide what % of gems you want to be expected
    to collect from breakable containers, gems on the ground, and Sgt. Byrd + Sparx minigames."""
    display_name = "Other Gems"
    range_start = 0
    range_end = 100
    default = 75
    
    
class DoubleGems(Choice):
    """This option is used when shop_randomization is enabled. It lets you enable or disable the permanent Double Gems item.
    Gem logic does not account for double gems, so if left enabled, you will collect gems faster than expected by logic."""
    display_name = "Double Gems"
    option_enabled = 0
    option_disabled = 1
    default = 0

###############GATE & GADGET COSTS###############
class RandomizeBossLairDoorCosts(Choice):
    """Determines the Dark Gem cost for each boss lair.

    default: Each boss lair has their vanilla cost (10/20/30/40).
    randomized: Randomly pick costs in the range defined by boss_lair_door_cost_min and boss_lair_door_cost_max.
    shuffle: Vanilla boss lair costs are shuffled between each other (still 10/20/30/40 but in a random order)."""
    display_name = "Randomize Boss Lair Requirements"
    option_default = 0
    option_randomized = 1
    option_shuffle = 2
    default = 0


class BossLairDoorCostMin(Range):
    """Minimum cost for boss lairs, if set to randomized. Must be less than or equal to boss_lair_door_cost_max."""
    display_name = "Boss Lair Door Cost Minimum"
    range_start = 1
    range_end = 40
    default = 1


class BossLairDoorCostMax(Range):
    """Maximum cost for boss lairs, if set to randomized."""
    display_name = "Boss Lair Door Cost Maximum"
    range_start = 1
    range_end = 40
    default = 40


class BossLairForcing(Choice):
    """This option decides if the generator should force boss lair(s) to have the most expensive Dark Gem costs.
    Such forcing takes place *after* costs have been decided through the above 3 options.
    
    unchanged: Leaves boss lair costs untouched.
    gnasty_gnorc/ineptune/red/mecha_red: Swaps that boss's cost with the highest cost.
    automatic: Swaps all goal boss costs so that they are collectively the highest.
    """
    display_name = "Boss Lair Forcing"
    option_unchanged = 0
    option_gnasty_gnorc = 1
    option_ineptune = 2
    option_red = 3
    option_mecha_red = 4
    option_automatic = 5
    default = 0
    

class RandomizeLightGemDoorCosts(Choice):
    """Determines the Light Gem cost for each Light Gem door.

    default: Each door has their vanilla cost (20/45/70/95).
    randomized: Randomly pick costs in the range defined by light_gem_door_cost_min and light_gem_door_cost_max.
    shuffle: Each door has their vanilla cost shuffled with the others (still 20/45/70/95 but in a random order)."""
    display_name = "Randomize Light Gem Door Cost"
    option_default = 0
    option_randomized = 1
    option_shuffle = 2
    default = 0


class LightGemDoorCostMin(Range):
    """Minimum cost for light gem doors, if set to randomized. Must be less than or equal to light_gem_door_cost_max."""
    display_name = "Minimum Light Gem Door Cost"
    range_start = 1
    range_end = 100
    default = 1


class LightGemDoorCostMax(Range):
    """Maximum cost for light gem doors, if set to randomized."""
    display_name = "Maximum Light Gem Door Cost"
    range_start = 1
    range_end = 100
    default = 50


class RandomizeGadgetCosts(Choice):
    """Determines the Light Gem cost for each gadget. Listed in order of Ball Gadget -> Invincibility -> Supercharge.

    default: Each gadget has their vanilla cost (8/24/40).
    randomized: Randomly picks costs in the range defined by gadget_cost_min and gadget_cost_max.
    shuffle: Each gadget has their vanilla cost shuffled with the others (still 8/24/40 but in a random order)."""
    display_name = "Randomize Gadget Cost"
    option_default = 0
    option_randomized = 1
    option_shuffle = 2
    default = 0


class GadgetCostMin(Range):
    """Minimum cost for gadgets, if set to randomized. Must be less than or equal to gadget_cost_max."""
    display_name = "Minimum Gadget Cost"
    range_start = 1
    range_end = 100
    default = 8


class GadgetCostMax(Range):
    """Maximum cost for gadgets, if set to randomized."""
    display_name = "Maximum Gadget Cost"
    range_start = 1
    range_end = 100
    default = 40
    
###############QUALITY OF LIFE###############
class PauseMenuPatch(Choice):
    """The pause menu has 2 patches you can choose between which can help with escaping situations where you're stuck.
    Take note that each one has logic implications if using open_world_mode.
    
    open_shop: pressing Y will open the shop display without needing to go to a shop physically. If using non-full open_world_mode,
      this will auto-unlock your starting realm's "Depot" shop to prevent potential softlock scenarios.
    teleport_to_hub: pressing and holding Y will bring you to the current realm's realm teleporter. If using non-full open_world_mode,
      this will be considered a valid alternative way to logically access a realm's hub level."""
    display_name = "Pause Menu Patch"
    option_open_shop = 0
    option_teleport_to_hub = 1
    default = 0


class ShopPadProximityActivation(Toggle):
    """When using non-full open_world_mode, shop pads only unlock via their unlock items. This can lead to situations where you
    can physically reach a shop pad but be unable to teleport back to it after, adding walking time on revisits.
    
    This option lets you re-enable proximity-based activation of shop pads. If enabled, any shop that you physically reach can be teleported
    back to once you interact with them. This will result in each affected shop pad's unlock item becoming effectively an empty filler item."""
    display_name = "Shop Pad Proximity Activation"
    default = 0
    
    
class HintMinigameRewards(Toggle):
    """Whether to auto-hint a mini-game's rewards when talking to its NPC."""
    display_name = "Hint Mini Game Rewards"
    default = 0


class HintBossRewards(Toggle):
    """Whether to auto-hint a boss's rewards when their lair is opened."""
    display_name = "Hint Boss Rewards"
    default = 0


class HintShopItems(Toggle):
    """Whether to auto-hint randomized shop items upon starting your save file."""
    display_name = "Hint Shop Items"
    default = 0


class HideShopItemNames(Toggle):
    """Whether to hide the name of each randomized shop item (player name is still shown). This adds a mystery element to
    what item you'll get, at risk of wasting your gems on fillers/traps. Hinted shop checks will still show their item in the hint."""
    display_name = "Hide Shop Item Names"
    default = 0
    

class EasyBosses(OptionSet):
    """Toggles 'easy mode' for each boss, making them take triple damage to significantly shorten fights.
    Valid options: ["Gnasty Gnorc", "Ineptune", "Red", "Mecha-Red"]"""
    display_name = "Easy Bosses"
    valid_keys = ("Gnasty Gnorc", "Ineptune", "Red", "Mecha-Red")
    default = ("Gnasty Gnorc", "Ineptune", "Red", "Mecha-Red")


class SkipCutscenes(Toggle):
    """Allows for skipping most cutscenes with the Y button."""
    display_name = "Auto Skip Cutscenes"
    default = 1


class SkipElevators(Toggle):
    """Replaces the long elevator waits to Cloudy Domain, Sunken Ruins and Magma Falls, with loading screens."""
    display_name = "Skip Elevators"
    default = 1


class TeleportAcrossRealms(Toggle):
    """Allows for teleporting to unlocked shop pads in any realm, from any realm. For example, you could
    teleport directly from Dragonfly Falls to Dark Mine without needing to use a hub realm teleporter."""
    display_name = "Teleport Across Realms"
    default = 1


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
    
    open_world_mode: OpenWorldMode
    firework_checks: FireworkChecks
    vanilla_minigame_rewards: VanillaMinigameRewards
    filler_items: FillerItems
    
    starting_breaths: StartingBreaths
    movement_randomization: MovementRandomization
    starting_realms: StartingRealms
    
    shop_randomization: ShopRandomization
    key_rings: KeyRings
    shop_item_count: ShopItemCount
    shop_logic: ShopLogic
    blink_gems: BlinkGems
    non_blink_enemies: NonBlinkEnemies
    other_gems: OtherGems
    double_gems: DoubleGems
    
    randomize_boss_lair_door_costs: RandomizeBossLairDoorCosts
    boss_lair_door_cost_min: BossLairDoorCostMin
    boss_lair_door_cost_max: BossLairDoorCostMax
    boss_lair_forcing: BossLairForcing
    randomize_light_gem_door_costs: RandomizeLightGemDoorCosts
    light_gem_door_cost_min: LightGemDoorCostMin
    light_gem_door_cost_max: LightGemDoorCostMax
    randomize_gadget_costs: RandomizeGadgetCosts
    gadget_cost_min: GadgetCostMin
    gadget_cost_max: GadgetCostMax
    
    pause_menu_patch: PauseMenuPatch
    shop_pad_proximity_activation: ShopPadProximityActivation
    hint_minigame_rewards: HintMinigameRewards
    hint_boss_rewards: HintBossRewards
    hint_shop_items: HintShopItems
    hide_shop_item_names: HideShopItemNames
    easy_bosses: EasyBosses
    skip_cutscenes: SkipCutscenes
    skip_elevators: SkipElevators
    teleport_across_realms: TeleportAcrossRealms
    
    
spyro_options_groups = [
    OptionGroup("DEATHLINK", [
        DeathLink, DeathLinkAmnesty
    ]),
    OptionGroup("GENERATION SETTINGS", [
        LoggingLevel, AutoCorrections
    ]),
    OptionGroup("GOAL", [
        BossGoals, DarkGemsGoal, LightGemsGoal, DragonEggsGoal, FireworksGoal, ShopItemsGoal, LockedChestsGoal, ExcludeChestItems
    ]),
    OptionGroup("CHECKS AND ITEMS", [
        OpenWorldMode, FireworkChecks, VanillaMinigameRewards, FillerItems
    ]),
    OptionGroup("START OF GAME", [
        StartingBreaths, MovementRandomization, StartingRealms
    ]),
    OptionGroup("SHOP SETTINGS", [
        ShopRandomization, KeyRings, ShopItemCount, ShopLogic, BlinkGems, NonBlinkEnemies, OtherGems, DoubleGems
    ]),
    OptionGroup("GATE & GADGET COSTS", [
        RandomizeBossLairDoorCosts, BossLairDoorCostMin, BossLairDoorCostMax, BossLairForcing,
        RandomizeLightGemDoorCosts, LightGemDoorCostMin, LightGemDoorCostMax,
        RandomizeGadgetCosts, GadgetCostMin, GadgetCostMax
    ]),
    OptionGroup("QUALITY OF LIFE", [
        PauseMenuPatch, ShopPadProximityActivation,
        HintMinigameRewards, HintBossRewards, HintShopItems, HideShopItemNames,
        EasyBosses,
        SkipCutscenes, SkipElevators,
        TeleportAcrossRealms
    ])
]