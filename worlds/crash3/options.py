from dataclasses import dataclass

from Options import OptionSet, PerGameCommonOptions, Choice, Range, OptionGroup

###############GENERATION SETTINGS###############
class LoggingLevel(Choice):
    """Choose how much Crash 3 generation information should be logged.
    The log will contain messages from all levels up to, and including, your choice. For example, "medium" will log low
    and medium messages, but not high or maximum messages. **Warning messages stemming from YAML issues are always logged.**

    None: No additional logging beyond warnings.
    Low: Logs only the notable generation steps.
    Medium: Also logs useful debugging information.
    High: Logs messages with extra generation logic.
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
    set to fix_minor, especially if intending to randomize multiple options.

    halt: Generation will be strictly halted upon any sort of YAML issue.
    chaos: The generator will not halt or make changes, even if there is a known problem or high likelihood of generation failing.
    fix_minor: Only issues deemed minor will be fixed.
    fix_major: All issues will be fixed, even if it has a major impact."""
    display_name = "Auto Corrections"
    option_halt = 0
    option_chaos = 1
    option_fix_minor = 2
    option_fix_major = 3
    default = 2


###############GOAL###############
class BossGoals(OptionSet):
    """Adds a goal requirement to defeat a number of boss(es).

    Valid Options: ["Tiny Tiger", "Dingodile", "N. Tropy", "N. Gin", "Cortex"]"""
    display_name = "Boss Goals"
    valid_keys = ("Tiny Tiger", "Dingodile", "N. Tropy", "N. Gin", "Cortex")
    default = ["Cortex"]

###############ITEMS###############
class StartingWarps(OptionSet):
    """Choose which warp room(s) to start with access to.
    
    Valid Options: ["Warp 1", "Warp 2", "Warp 3", "Warp 4", "Warp 5"]"""
    display_Name = "Starting Warps"
    valid_keys = ("Warp 1", "Warp 2", "Warp 3", "Warp 4", "Warp 5")
    default = ["Warp 1"]

    
class TrapPercentage(Range):
    """Decides how much of the junk (fillers + traps) item pool will be traps, as a percentage out of 100."""
    display_name = "Trap Percentage"
    range_start = 0
    range_end = 100


class FillerItems(OptionSet):
    """Choose which categories of filler (neutral-to-positive effect) items to enable.

    1 Wumpa: Gain a wumpa fruit. You're so rich.
    1 Life: Gain an extra life. You're so healthy.

    Valid options: ["1 Wumpa", "1 Life"]"""
    display_name = "Filler Items"
    valid_keys = ("1 Wumpa", "1 Life")
    default = ("1 Wumpa",)


class TrapItems(OptionSet):
    """Choose which trap (neutral-to-negative effect) items to enable.

    Lose 1 Wumpa: lose a wumpa fruit. Oh no.
    Lose 1 Life: lose a life. Slightly more oh no.

    Valid options: ["Lose 1 Wumpa", "Lose 1 Life"]"""
    display_name = "Trap Items"
    valid_keys = ("Lose 1 Wumpa", "Lose 1 Life")
    default = frozenset()


@dataclass
class Crash3Options(PerGameCommonOptions):
    logging_level: LoggingLevel
    auto_corrections: AutoCorrections
    
    boss_goal: BossGoals
    
    starting_warps: StartingWarps
    trap_percentage: TrapPercentage
    filler_items: FillerItems
    trap_items: TrapItems
    
crash3_options_groups = [
    OptionGroup("GENERATION SETTINGS", [LoggingLevel, AutoCorrections]),
    OptionGroup("GOAL", [BossGoals]),
    OptionGroup("ITEMS", [StartingWarps, TrapPercentage, FillerItems, TrapItems])
]