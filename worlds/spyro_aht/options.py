from dataclasses import dataclass

from Options import OptionSet, PerGameCommonOptions, Toggle, Choice, Range, OptionGroup, StartInventoryPool, OptionList, Visibility

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
    
    In a worst-case, low and medium each log around 15 messages, high can log around 30 messages, and maximum
    can log multiple hundreds of messages. Maximum is only intended for developer use, but you can enable it if curious :)
    
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
    """This option decides the behavior of the generator if YAML issues are encountered. It is strongly recommended to enable
    this if putting AHT AP into a larger multiworld, to increase the chance of generation success even if issues are encountered.
    
    halt: YAML issues will result in generation being halted so that the player can decide how to resolve it.
    fix: YAML issues will be automatically fixed. Options which can lead to known issues have their automatic fixes described in them."""
    display_name = "Auto Corrections"
    option_halt = 0
    option_fix = 1
    default = 0

###############GOAL, CHECKS, AND ITEMS###############
class Goal(OptionList):
    """Choose your goal(s) for this seed. Run /check_goal overview in the client for mid-run information. Any locations in
    exclude_locations will be left out of goals they belong to. If you exclude all locations for all chosen goal types and
    auto_corrections is enabled, Mecha-Red will be forced as your goal regardless of exclusions.
    
    Collectible goals are based on *AHT locations*, not item collection. For example, "Dragon Eggs" requires checking all
    80 AHT locations which have "Dragon Egg" in their name. This can lead to early goals if your seed allows the use !collect
    (check the project wiki FAQ for details). 

    Available Goals:
    Gnasty Gnorc/Ineptune/Red/Mecha-Red: Defeat each boss.
    Fireworks: Flame all 22 fireworks. firework_checks will be enabled automatically if auto_corrections is enabled.
    Dark Gems: Break all 40 Dark Gems.
    Dragon Eggs: Collect all 80 Dragon Eggs (including those from locked chests).
    Light Gems: Collect all 100 Light Gems (including those from locked chests).
    Locked Chests: Open all 52 locked chests.
    Shop Items: Buy all randomized shop items. shop_randomization will be enabled automatically if auto_corrections is enabled.
    Random: For each "Random" you include, a random goal from above will be chosen, excluding any from exclude_from_random_goal.
    
    If the list is empty and auto_corrections is enabled, a single random goal will be chosen.
    If the list has too many entries and auto_corrections is enabled, entries will be removed at random until in range."""
    display_name = "Goal"
    valid_keys = ("Gnasty Gnorc", "Ineptune", "Red", "Mecha-Red", "Fireworks", "Dark Gems", "Dragon Eggs", "Light Gems", "Locked Chests", "Shop Items", "Random")
    default = ("Mecha-Red",)
    
    
class ExcludeFromRandomGoal(OptionSet):
    """This option lets you exclude goals from being randomly chosen. For example, entering "Shop Items" below means "Shop Items"
    will never be chosen in place of "Random" (you can still explicitly choose "Shop Items" in this example).
    
    If too many goals are excluded to allow for enough random choices and auto_corrections is enabled, goals will be
    un-excluded at random until in range. If this isn't enough to fix it, random choices will be skipped entirely.
    
    Valid Options: ["Gnasty Gnorc", "Ineptune", "Red", "Mecha-Red", "Fireworks", "Dark Gems", "Dragon Eggs", "Light Gems", "Locked Chests", "Shop Items"]"""
    display_name= "Exclude From Random Goal"
    valid_keys = ("Gnasty Gnorc", "Ineptune", "Red", "Mecha-Red", "Fireworks", "Dark Gems", "Dragon Eggs", "Light Gems", "Locked Chests", "Shop Items")
    default = frozenset()
    

class OpenWorldMode(Choice):
    """In the vanilla game, you can only teleport to a remote shop pad once you have physically reached it.
    open_world_mode lets you choose from a variety of ways to have shop pads become unlocked by Archipelago items.
    This will dominate the logic of seeds using open_world_mode, as you will be expected to utilize any and all unlocked shop
    pads to clever teleport around the game, potentially playing large sections of the game backwards or in chunks at a time.
    
    vanilla: Shop pads are only unlocked by physically reaching them.
    full: All shop pads are unlocked from the start of the seed.
    randomized: Shop pads unlock through individual AP items. For example, "Dark Mine - Miner's Drop Shop Unlock".
    progressive_levels: Shop pads unlock per-level in vanilla game order. For example, "Progressive Crocovile Swamp Shop Unlock"
      would first unlock Perilous Pyramid, then Forgotten Temple, then Elder's Tree. AHT AP's wiki has a reference list for this. 
    reverse_progressive_levels: Same as progressive_levels, but backwards vanilla order.
    full_level: All shop pads in a level will unlock at once through AP items. For example, "Sunken Ruins - Shop Unlock".
    full_realm: All shop pads in a realm will unlock at once through AP items. For example, "Icy Wilderness - Shop Unlock"."""
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
    """Enables 22 locations for flaming fireworks."""
    display_name = "Firework Checks"
    default = 0


class VanillaMinigameRewards(OptionSet):
    """Minigames are always enabled as locations. This option lets you decide if you want any type of minigame to reward
    their vanilla Dragon Eggs and Light Gems instead of having randomized rewards.
    
    Valid options: ["Sgt. Byrd", "Blink", "Turret", "Sparx"]"""
    display_name = "Vanilla Minigame Rewards"
    valid_keys = ("Sgt. Byrd", "Blink", "Turret", "Sparx")
    default = frozenset()


class FillerItems(OptionSet):
    """This option lets you choose the contents of your filler item pool. For each location which needs a filler item,
    a random enabled category will be chosen, and if needed, a random item from that category will then be chosen.

    Descriptions:
    Dragon Eggs: These are considered filler due to having no impact on game progression.
    Breath Bombs: Fire, Electric, Water, and Ice Bombs. Bombs are only usable if you have their respective breath unlocked.
    Gem Packs: Gives a random amount of gems (400-600 or 800-1200 if you have double gems).
      It is advised to exclude gem packs if using shop_randomization and gem_logic, as gem logic does not account for gem packs.
    Generics: Items which do nothing, but have humorous names referencing things in the game and series.
    
    If the list is empty and auto_corrections is enabled, the filler pool will default to only "Generics".

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
    
    If the list contains both "None" and breath(s) and auto_corrections is enabled, the "None" will be discarded.
    
    Valid Options: ["Fire", "Electric", "Water", "Ice", "None"]"""
    display_name = "Starting Breaths"
    valid_keys = ("Fire", "Electric", "Water", "Ice", "None")
    default = ("Fire",)


class MovementRandomization(OptionSet):
    """Choose whether to randomize each of the 3 base movement abilities (glide, swim, and charge).
    Each one listed below will be randomized, meaning you will start with a different random item from Archipelago in their place.
    For example, "Starter Checks: Glide" will award a random Archipelago item if glide is listed below, otherwise it will award glide.
    
    Note: vanilla AHT does not technically require you to have charge in order to charge underwater, but AHT AP overrides
    this and requires it. If you have swim but not charge, you can still swim, but will be limited to paddling slowly,
    which is not enough to get through most acid swimming sections, and limits underwater gem collection.
    
    Valid Options: ["Glide", "Swim", "Charge"]"""
    display_name = "Movement Randomization"
    valid_keys = ("Glide", "Swim", "Charge")
    default = frozenset()


class StartingRealms(OptionSet):
    """Realm access is primarily controlled by "access cards" e.g. "Dragon Kingdom Access Card". Choose which realm(s) you will start with access cards for. 
    
    If the list is left empty, 1 random realm will be chosen.
    If open_world_mode is enabled and 'full', you will start with all 4 access cards.
    If open_world_mode is enabled and not 'full', you will start with access cards based on this option, but later realms will be unlocked
      via their "Depot" shop unlock. For example, unlocking "Frostbite Village - Frosty Depot" grants realm access to Icy Wilderness.
      See pause_menu_patch for a potential alteration to this.
        
    Starting in Icy Wilderness with shop_randomization disabled and movement_randomization empty is disallowed due to impossible starts.
    If this is done and auto_corrections is enabled, your starting realm will be changed to Dragon Kingdom.
    
    Valid Options: ["Dragon Kingdom", "Lost Cities", "Icy Wilderness", "Volcanic Isle"]"""
    display_name = "Starting Realms"
    valid_keys = ("Dragon Kingdom", "Lost Cities", "Icy Wilderness", "Volcanic Isle")
    default = ("Dragon Kingdom",)
    
###############SHOP & GEM LOGIC###############
class ShopRandomization(Toggle):
    """Determines whether to randomize Moneybags' shop. If not randomized, it will function identically to the vanilla game. 

    If randomized, vanilla game shop items will be replaced with items from Archipelago. This has a few consequences:
        - Double Gems, if enabled, is permanent once received, as is the Butterfly Jar (it replenishes on death if depleted).
        - There is no limit to how many lockpicks you can hold at once. Same with ammo for breath bombs.
        - Shop item prices will be the same everywhere i.e. remote shop pads will not upcharge you."""
    display_name = "Shop Randomization"
    default = 0
    

class KeyRings(Toggle):
    """This option replaces lockpicks with level-specific key rings which will open all locked chests in that level.
    This indirectly decides how many items you will have in your shop.

    If shop_randomization is disabled: this decides whether key rings or lockpicks will be buyable in the shop.
      Locked chests will be in-logic as soon as you can reach them.
    If shop_randomization and key_rings are enabled: you will have 18 shop items, and 14 key rings will be placed into the world.
      Locked chests will be in-logic once their level's key ring is obtained.
    If shop_randomization is enabled and key_rings is disabled: you will have 56 shop items, and 52 lockpicks will be placed in the world.
      Locked chests will be in-logic once you have all 52 lockpicks, to prevent softlock situations from opening them in the 'wrong' order."""
    display_name = "Key Rings"
    default = 0

    
class GemLogic(Choice):
    """This option is only used when shop_randomization is enabled. The generator is capable of keeping track of how many gems you
    have access to, and can use that information to improve the logic of the shop.
    
    Regardless of gem_logic, the formula below calculates your prices. It is included for those who are math-inclined, but you can always
    do test generation(s) to see your prices. The first item is always free due to inflation in the Dragon Kingdom (it prevents restrictive starts).
    
    disabled: shop items will be priced equally and all be in-logic in sphere 1. This can result in difficult or impossible
      seeds as it is infeasible to afford every item that early. However, it does give you the choice of which order to buy them.
    enabled: shop items will instead display "Unlocked at X Gems". Once you have X gems, the item will be free to purchase.
      Prices will steadily increase so that you unlock them in a spread-out set order, instead of all in sphere 1. This is significantly
      safer and improves generation quality a bit, at the cost of losing the ability to choose which order you buy them.
    
    Gems that come from any minigames added to exclude_locations will not be factored into gem calculations. 
    
    ********************************FORMULA INFO (for the math nerds)********************************
    blink_gems_total = (20,203 - blink exclusions) * blink_gems%
    non_blink_enemies_total = 16,353 * non_blink_enemies%
    other_gems_total = (105,087 - sparx/byrd exclusions) * other_gems%
    gem_total = blink_gems_total + non_blink_enemies_total + other_gems_total
    base_shop_price = gem_total / (number of shop items - 1)

    If gem_logic is disabled, shop items will all cost base_shop_price, rounded down if needed.
    If gem_logic is enabled, shop items will cost base_shop_price * 1, base_shop_price * 2, etc., rounded down if needed.
    *************************************************************************************************"""
    display_name = "Gem Logic"
    option_disabled = 0
    option_enabled = 1
    default = 0


class BlinkGems(Range):
    """This option is used when shop_randomization is enabled. It lets you decide what % of gems from Blink's minigames you
    want to be expected to collect. Like non_blink_enemies and other_gems, a value of 50 means being expected to collect approximately
    50% of the gems available in each Blink minigame, minus any that you put into exclude_locations."""
    display_name = "Blink Gems"
    range_start = 0
    range_end = 100
    default = 75


class NonBlinkEnemies(Range):
    """This option is used when shop_randomization is enabled. It lets you decide what % of gems from enemies you want
    to be expected to collect. This only applies to enemies when playing as Spyro or Hunter. Logic assumes you will kill every
    enemy exactly once, which is nearly impossible to do accurately. This option was introduced to mitigate logic implications from this.
    
    Like blink_gems and other_gems, a value of 40 means being expected to collect approximately 40% of all gems available from enemies."""
    display_name = "Non-Blink Enemies"
    range_start = 0
    range_end = 100
    default = 75


class OtherGems(Range):
    """This option is used when shop_randomization is enabled. It lets you decide what % of gems from non-Blink and non-enemies
    you want to be expected to collect. This primarily consists of gems from containers, Sgt. Byrd + Sparx minigames, and some misc. others.
    
    Like blink_gems and non_blink_enemies, a value of 35 would mean being expected to collect approximately 35% of all gems in this category.
    
    Note: Sparx minigames are hard to get consistent gems from. Their programmed totals were calculated as an average of 4-5 runs,
    scaled down ~80-90%. Each pair expects, at other_gems 100: 675/700 -> 900/800 -> 950/900 -> 1100/900."""
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
    """Minimum cost for boss lairs, if set to be random. Will be swapped with boss lair maximum if min > max and auto_corrections is enabled."""
    display_name = "Boss Lair Door Cost Minimum"
    range_start = 1
    range_end = 40
    default = 1


class BossLairDoorCostMax(Range):
    """Maximum cost for boss lairs, if set to be random. Will be swapped with boss lair minimum if min > max and auto_corrections is enabled."""
    display_name = "Boss Lair Door Cost Maximum"
    range_start = 1
    range_end = 40
    default = 40


class BossLairForcing(Choice):
    """This option decides if the generator should force a subset of boss lairs to have the most expensive Dark Gem costs.
    This is useful if you want to ensure those bosses are accessed later in the run as opposed to possibly earlier.
    Any adjustments from this option take place *after* costs have been decided through the above 3 options.
    
    unchanged: Leaves boss lair costs untouched.
    gnasty_gnorc/ineptune/red/mecha_red: Forces the selected boss's lair to have the highest Dark Gem cost.
    automatic: Forces all goal bosses to have the highest costs. If you have no goal bosses, or all 4 are goals, this will do nothing.
      For example, if you have Ineptune and Red as goal bosses and select automatic, their costs will be swapped, as needed,
      to ensure they have the 2 most expensive costs, while Gnasty Gnorc and Mecha-Red would have the 2 least expensive costs.
      
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
    """Minimum cost for light gem doors, if set to be random. Will be swapped with light gem door maximum if min > max and auto_corrections is enabled."""
    display_name = "Minimum Light Gem Door Cost"
    range_start = 1
    range_end = 100
    default = 1


class LightGemDoorCostMax(Range):
    """Maximum cost for light gem doors, if set to be random. Will be swapped with light gem door minimum if min > max and auto_corrections is enabled."""
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
    """Minimum cost for gadgets, if set to be random. Will be swapped with gadget maximum if min > max and auto_corrections is enabled."""
    display_name = "Minimum Gadget Cost"
    range_start = 1
    range_end = 100
    default = 8


class GadgetCostMax(Range):
    """Maximum cost for gadgets, if set to be random. Will be swapped with gadget minimum if min > max and auto_corrections is enabled."""
    display_name = "Maximum Gadget Cost"
    range_start = 1
    range_end = 100
    default = 40
    
###############QUALITY OF LIFE###############
class PauseMenuPatch(Choice):
    """The pause menu has 2 patches you can choose between which can help with escaping situations where you're stuck.
    Take note that each one has logic implications if using open_world_mode.
    
    open_shop: pressing Y will open the shop display without needing to go to a shop physically. If open_world_mode is enabled and
      not 'full', having this enabled will auto-unlock your starting realm's "Depot" shop to prevent potential softlock scenarios.
    teleport_to_hub: pressing and holding Y will bring you to the current realm's realm teleporter. This will be considered a
      valid alternative way to access a realm's hub level when open_world_mode is enabled and not 'full'."""
    display_name = "Pause Menu Patch"
    option_open_shop = 0
    option_teleport_to_hub = 1
    default = 0


class ShopPadProximityActivation(Toggle):
    """When open_world_mode is enabled and not 'full', shop pads only unlock via their unlock items. This can lead to situations
    where you can physically reach other shop pads but not be able to teleport back to them after leaving, adding to walking time on revisits.
    
    This option lets you re-enable proximity-based activation of shop pads. If enabled, any shop that you physically reach can be teleported
    back to once you interact with them. This will result in each affected shop pad's unlock item becoming effectively an empty filler item."""
    display_name = "Shop Pad Proximity Activation"
    default = 0
    
    
class HintMinigameRewards(Toggle):
    """Whether to auto-hint a mini-game's rewards when talking to its NPC."""
    display_name = "Hint Mini Game Rewards"
    default = 0


class HintBossRewards(Toggle):
    """Whether to auto-hint a boss's rewards when their gate is opened."""
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
    """Enables skipping most cutscenes with the Y button."""
    display_name = "Auto Skip Cutscenes"
    default = 1


class SkipElevators(Toggle):
    """Enables replacing the long elevator waits to Cloudy Domain, Sunken Ruins and Magma Falls, with loading screens."""
    display_name = "Skip Elevators"
    default = 0


class TeleportAcrossRealms(Toggle):
    """Allows for teleporting to unlocked shop pads in any realm, from any realm. For example, you could
    teleport directly from Dragonfly Falls to Dark Mine without needing to use a hub realm teleporter.
    
    This option is automatically enabled if you are using any value for open_world_mode besides "vanilla"."""
    display_name = "Teleport Across Realms"
    default = 0


@dataclass
class SpyroAHTOptions(PerGameCommonOptions):
    death_link: DeathLink
    death_link_amnesty: DeathLinkAmnesty
    
    logging_level: LoggingLevel
    auto_corrections: AutoCorrections
    start_inventory_from_pool: StartInventoryPool
    
    goal: Goal
    exclude_from_random_goal: ExcludeFromRandomGoal
    open_world_mode: OpenWorldMode
    firework_checks: FireworkChecks
    vanilla_minigame_rewards: VanillaMinigameRewards
    filler_items: FillerItems
    
    starting_breaths: StartingBreaths
    movement_randomization: MovementRandomization
    starting_realms: StartingRealms
    
    shop_randomization: ShopRandomization
    key_rings: KeyRings
    gem_logic: GemLogic
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
    OptionGroup("GOAL, CHECKS, AND ITEMS", [
        Goal, ExcludeFromRandomGoal, OpenWorldMode, FireworkChecks, VanillaMinigameRewards, FillerItems
    ]),
    OptionGroup("START OF GAME", [
        StartingBreaths, MovementRandomization, StartingRealms
    ]),
    OptionGroup("SHOP & GEM LOGIC", [
        ShopRandomization, KeyRings, GemLogic, BlinkGems, NonBlinkEnemies, OtherGems, DoubleGems
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