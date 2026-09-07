import struct
from dataclasses import dataclass
from enum import IntEnum, IntFlag
from typing import Literal

# compared in world definition against YAML. Messages that are of equal or lower log level are logged
class LoggingLevel(IntEnum):
    WARNING = 0  # 0 because warnings are always logged, even if level is set to none
    NONE = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    MAXIMUM = 5

MOD_MAJOR = 14
MOD_MINOR = 0
MOD_VERSION_STR = f"{MOD_MAJOR}.{MOD_MINOR}"

CLIENT_MAJOR = 2
CLIENT_MINOR = 1
CLIENT_REVISION = 0
CLIENT_VERSION_STR = f"{CLIENT_MAJOR}.{CLIENT_MINOR}.{CLIENT_REVISION}"

BREATH_FIRE = 0x1
BREATH_WATER = 0x2
BREATH_ICE = 0x4
BREATH_ELECTRIC = 0x8

DARK_GEM = 0x8
LIGHT_GEM = 0x9
DRAGON_EGG = 0xA

COLOUR_WHITE = (0x80, 0x80, 0x80, 0x80)
COLOUR_RED = (0x80, 0x20, 0x20, 0x80)

# https://discord.com/channels/619694339777495056/692182418429575260/1477821351879507998

# (AP location ID, bitfield offset)
LOCATIONS_BITFIELD: dict[int, int] = {
    2: 65, 3: 66, 4: 70, 5: 73, 6: 74, 7: 76,
    8: 72, 9: 71, 10: 69, 11: 67, 12: 68,
    13: 181, 14: 182, 15: 77, 16: 75, 18: 48,
    19: 61, 20: 57, 21: 56, 22: 60, 23: 59,
    24: 62, 25: 55, 26: 51, 27: 49, 28: 53,
    29: 63, 30: 185, 31: 186, 32: 58, 34: 52,
    35: 64, 36: 50, 37: 183, 38: 184, 39: 54,
    40: 45, 41: 34, 42: 32, 43: 31, 44: 33,
    45: 35, 46: 36, 47: 44, 48: 187, 49: 188,
    50: 38, 51: 46, 52: 47, 53: 43, 54: 42,
    55: 40, 56: 37, 57: 41, 58: 39, 59: 155,
    60: 153, 61: 156, 62: 157, 63: 191, 64: 192,
    65: 146, 66: 147, 67: 148, 68: 145, 69: 158,
    70: 150, 71: 193, 72: 189, 73: 190, 74: 152,
    75: 151, 76: 154, 77: 159, 78: 149, 80: 19,
    81: 15, 82: 23, 84: 21, 85: 20, 86: 22,
    87: 27, 88: 26, 89: 25, 90: 24, 91: 28,
    92: 18, 93: 196, 94: 197, 95: 17, 96: 16,
    97: 30, 98: 29, 99: 7, 100: 3, 101: 5, 102: 8,
    103: 9, 104: 0, 105: 194, 106: 195, 107: 2,
    108: 10, 109: 1, 110: 13, 111: 4, 112: 11,
    113: 6, 114: 14, 115: 12, 116: 89, 117: 200,
    118: 201, 119: 101, 120: 94, 121: 102, 122: 95,
    123: 98, 124: 198, 125: 199, 172: 99, 126: 90,
    127: 91, 128: 105, 129: 92, 130: 96, 131: 97,
    132: 93, 133: 104, 134: 100, 135: 103, 137: 130,
    138: 204, 139: 121, 140: 129, 141: 120, 142: 122,
    143: 126, 144: 127, 145: 124, 146: 202, 147: 203,
    148: 128, 149: 125, 150: 123, 151: 209, 152: 106,
    153: 119, 154: 107, 156: 117, 157: 108, 158: 109,
    159: 111, 160: 205, 161: 206, 162: 207, 163: 113,
    164: 116, 165: 115, 166: 112, 167: 114, 168: 208,
    169: 210, 170: 110, 171: 118, 173: 143, 174: 144,
    175: 211, 176: 212, 177: 142, 178: 167, 179: 215,
    180: 162, 181: 213, 182: 214, 183: 168, 184: 160,
    185: 161, 186: 163, 187: 164, 188: 170, 189: 166,
    190: 169, 191: 165, 192: 172, 193: 171, 194: 173,
    195: 175, 196: 174, 197: 176, 198: 177, 199: 180,
    200: 179, 201: 178, 202: 216, 203: 217, 204: 79,
    205: 83, 206: 86, 207: 87, 208: 80, 209: 78, 210: 218,
    211: 219, 212: 88, 213: 82, 214: 84, 215: 81, 216: 85,
    217: 140, 218: 136, 219: 134, 220: 138, 221: 137,
    222: 135, 223: 139, 224: 141, 225: 132, 226: 131, 227: 133,
    234: 221, 235: 220, 236: 223, 237: 222, 238: 225, 239: 226,
    240: 230, 241: 227, 242: 228, 243: 229, 244: 224, 245: 234,
    246: 233, 247: 232, 248: 235, 249: 231, 250: 236, 251: 237,
    252: 238, 253: 239, 254: 240,
    1: 241, 33: 242, 83: 243, 155: 244,
    17: 245, 79: 246, 136: 247, 228: 248, 4003: 248,

    5000: 250, 5001: 249, 5002: 252, 5003: 251, 5004: 254,
    5005: 253, 5006: 255, 5007: 256, 5008: 257, 5009: 258,
    5010: 259, 5011: 262, 5012: 261, 5013: 260, 5014: 263,
    5015: 265, 5016: 264, 5017: 266, 5018: 267, 5019: 268,
    5020: 269, 5021: 270
}

KEY_RINGS = [0x22, 0x23, 0x24, 0x25, 0x27, 0x26, 0x28, 0x29, 0x2A, 0x2B, 0x2C, 0x2D, 0x2E, 0x2F]


MINIGAME_OBJECTIVES: dict[int, tuple[int, int]] = {
    0x44000017: (13, 14),
    0x44000013: (30, 31),
    0x4400000c: (37, 38),
    0x4400007b: (48, 49),

    0x4400001a: (63, 64),
    0x4400004b: (72, 73),
    0x440000a7: (93, 94),
    0x440000a5: (105, 106),

    0x4400008a: (117, 118),
    0x4400008f: (124, 125),
    0x440000aa: (146, 147),
    0x44000094: (160, 161),

    0x44000097: (175, 176),
    0x440000d1: (181, 182),
    0x440000bb: (202, 203),
    0x440000b6: (210, 211),
}

BOSS_OBJECTIVES = {
    0x44000111: 17,
    0x44000112: 79,
    0x44000113: 136
}


BOSS_GOALS = [
    0x44000081, # Defeat Gnasty Gnorc
    0x44000082, # Defeat Ineptune
    0x44000083, # Defeat Red
    0x44000084  # Defeat Mecha-Red
]

# for new goal detection
BOSS_IDS = [4000, 4001, 4002, 4003]
DARK_GEM_IDS = [2, 11, 3, 18, 32, 36, 41, 44, 46, 55, 65, 67, 74, 76, 81, 92, 96, 100, 111, 113, 119, 121, 131, 126, 127, 154, 157, 170, 165, 163, 177, 178, 186, 191, 198, 209, 216, 227, 225, 219]
DRAGON_EGG_IDS = [16, 13, 12, 8, 4, 6, 23, 20, 24, 27, 29, 30, 34, 37, 42, 45, 57, 48, 50, 53, 63, 68, 78, 61, 66, 72, 75, 85, 84, 87, 90, 91, 93, 97, 99, 101, 105, 107, 108, 114, 117, 120, 124, 122, 130, 133, 128, 137, 140, 141, 143, 145, 146, 153, 160, 158, 159, 171, 164, 166, 174, 175, 179, 180, 181, 188, 189, 193, 194, 196, 202, 201, 205, 207, 210, 212, 214, 217, 222, 221]
LIGHT_GEM_IDS = [7, 14, 10, 9, 5, 15, 21, 22, 26, 19, 25, 28, 31, 35, 38, 39, 40, 43, 56, 47, 49, 51, 52, 58, 54, 64, 69, 62, 59, 60, 70, 71, 73, 77, 80, 82, 86, 88, 89, 94, 95, 98, 102, 103, 104, 106, 109, 110, 112, 115, 116, 118, 125, 123, 135, 132, 172, 134, 129, 138, 139, 142, 144, 147, 148, 149, 150, 151, 152, 156, 161, 162, 169, 167, 168, 173, 176, 182, 183, 184, 185, 187, 190, 192, 195, 197, 199, 200, 203, 206, 204, 208, 211, 213, 215, 226, 223, 224, 218, 220]
FIREWORK_IDS = [5002, 5000, 5001, 5003, 5004, 5006, 5005, 5012, 5011, 5013, 5007, 5008, 5009, 5010, 5014, 5015, 5016, 5017, 5018, 5019, 5020, 5021]
LOCKED_CHEST_IDS = [7, 6, 15, 23, 19, 24, 40, 52, 234, 235, 80, 236, 85, 87, 237, 99, 102, 103, 108, 112, 114, 115, 238, 133, 128, 244, 239, 137, 140, 240, 153, 156, 241, 242, 243, 245, 246, 247, 248, 249, 183, 188, 190, 250, 193, 251, 199, 252, 206, 207, 253, 254]
SHOP_ITEM_IDS = [1000, 1001, 1002, 1003, 1004, 2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 3013, 3014, 3015, 3016, 3017, 3018, 3019, 3020, 3021, 3022, 3023, 3024, 3025, 3026, 3027, 3028, 3029, 3030, 3031, 3032, 3033, 3034, 3035, 3036, 3037, 3038, 3039, 3040, 3041, 3042, 3043, 3044, 3045, 3046, 3047, 3048, 3049, 3050]

DEATHLINK_MESSAGES = [
    "{name} died.",
    "{name} ended their tail.",
    "{name} was fed to the fish.",
    "{name} forgot their wings.",
    "{name} did a jig and then blew up.",
    "{name} became a dragon fossil.",
    "{name} became a purple pancake.",
    "{name} became grape ice cream.",
    "{name} spend one of their 9 lives.",
    "{name} failed to land on their feet.",
    "{name} discovered why cats hate water.",
    "{name} became roadkill.",
    "{name} blinked out of existence.",
    "{name} went in too deep.",
    "{name} touched the Earth's mantle.",
    "{name} discovered the dangers of cave diving.",
    "{name} caved in.",
    "{name} died in a reality-defying fashion.",
    "{name} failed a water landing.",
    "{name} became roasted chicken.",
    "{name}'s parachute failed.",
    "{name} ended the Bug's Life.",
    "{name} dropped the ball.",
    "{name} let Fredneck starve.",
    "{name} was a terrible godfather.",
    "{name} was put on ice.",
    "{name} was overrun."
]

# matches order of shops in bitfield. Will look up bitfield indexes via .index(shop_name)
SHOP_PAD_LIST = [
    "Dragon Village - Village Depot",
    "Crocovile Swamp - Elder's Tree", "Crocovile Swamp - Forgotten Temple", "Crocovile Swamp - Perilous Pyramid",
    "Dragonfly Falls - Steep Canyon", "Dragonfly Falls - Secret Area", "Dragonfly Falls - Tropical Cove",
    "Coastal Remains - Waterfall Walkway", "Coastal Remains - Domain Doorstep", "Coastal Remains - Coastal Depot",
    "Cloudy Domain - Elevator Top", "Cloudy Domain - Elder's Homestead", "Cloudy Domain - Tallest Tower",
    "Sunken Ruins - Atlantian Entryway", "Sunken Ruins - The Depths", "Sunken Ruins - Toxic Rise",
    "Frostbite Village - Eskimole Village", "Frostbite Village - Icy Camp", "Frostbite Village - Frosty Depot",
    "Ice Citadel - Cool Courtyard", "Ice Citadel - Supercharge Central", "Ice Citadel - Royal Chamber", "Ice Citadel - Drawbridge Drop-off",
    "Stormy Beach - Stormy Depot",
    "Molten Mount - Destroyed Village", "Molten Mount - Collapsed Bridge", "Molten Mount - Lumber Storage",
    "Magma Falls - Crackling Cave", "Magma Falls - Sparx Can Fly", "Magma Falls - Chains of Lava",
    "Dark Mine - Mine Mouth", "Dark Mine - Hidden Depths", "Dark Mine - Miner's Drop",
    "Red's Laboratory - Celestial Show", "Red's Laboratory - Mechanical Mishaps", "Red's Laboratory - Pre-production", "Red's Laboratory - Laser Leaps"
]

# used to find all shops for a given level, in vanilla game order (list is reversed if reverse progressive is in use)
LEVEL_SHOP_LOOKUP = {
    "Dragon Village": ["Village Depot"],
    "Crocovile Swamp": ["Perilous Pyramid", "Forgotten Temple", "Elder's Tree"],
    "Dragonfly Falls": ["Steep Canyon", "Tropical Cove", "Secret Area"],
    "Coastal Remains": ["Coastal Depot", "Domain Doorstep", "Waterfall Walkway"],
    "Cloudy Domain": ["Elevator Top", "Elder's Homestead", "Tallest Tower"],
    "Sunken Ruins": ["Atlantian Entryway", "The Depths", "Toxic Rise"],
    "Frostbite Village": ["Frosty Depot", "Icy Camp", "Eskimole Village"],
    "Ice Citadel": ["Cool Courtyard", "Supercharge Central", "Royal Chamber", "Drawbridge Drop-off"],
    "Stormy Beach": ["Stormy Depot"],
    "Molten Mount": ["Destroyed Village", "Collapsed Bridge", "Lumber Storage"],
    "Magma Falls": ["Crackling Cave", "Chains of Lava", "Sparx Can Fly"],
    "Dark Mine": ["Mine Mouth", "Hidden Depths", "Miner's Drop"],
    "Red's Laboratory": ["Celestial Show", "Mechanical Mishaps", "Pre-production", "Laser Leaps"]
}

# simplifies finding all the shops for a given realm. Look up realm here -> look up each level from that realm's list in LEVEL_SHOP_LOOKUP
REALM_LEVEL_LOOKUP = {
    "Dragon Kingdom": ["Dragon Village", "Crocovile Swamp", "Dragonfly Falls"],
    "Lost Cities": ["Coastal Remains", "Cloudy Domain", "Sunken Ruins"],
    "Icy Wilderness": ["Frostbite Village", "Ice Citadel"],
    "Volcanic Isle": ["Stormy Beach", "Molten Mount", "Magma Falls", "Dark Mine", "Red's Laboratory"]
}

# used when generating location groups. Differs from REALM_LEVEL_LOOKUP in that it includes GG and separates MFt and MFb
REALM_LEVEL_LISTS = {
    "Dragon Kingdom": ["Dragon Village", "Crocovile Swamp", "Dragonfly Falls"],
    "Lost Cities": ["Coastal Remains", "Cloudy Domain", "Sunken Ruins"],
    "Icy Wilderness": ["Frostbite Village", "Gloomy Glacier", "Ice Citadel"],
    "Volcanic Isle": ["Stormy Beach", "Molten Mount", "Magma Falls Top", "Magma Falls Bottom", "Dark Mine", "Red's Laboratory"]
}

class AddressList:
    p_LOCATION_BITFIELD: int
    p_KEYRING_BITFIELD: int
    p_SHOPPAD_BITFIELD: int
    p_NUM_GEM_PACKS_RECEIVED: int
    p_NUM_LOCK_PICKS_RECEIVED: int
    p_NUM_FIRE_AMMO_RECEIVED: int
    p_NUM_ELECTRIC_AMMO_RECEIVED: int
    p_NUM_WATER_AMMO_RECEIVED: int
    p_NUM_ICE_AMMO_RECEIVED: int
    p_DEATHLINK_INGOING: int
    p_DEATHLINK_OUTGOING: int
    p_DEATHLINK_DEATHS_BEFORE_SEND: int
    p_DEATHLINK_DEATH_COUNTER: int
    p_INFINITE_BUTTERFLY_JAR: int
    p_INFINITE_DOUBLE_GEM: int
    p_FIREWORKS_ARE_RANDOMIZED: int
    p_RANDOMIZE_SHOP: int
    p_USE_KEY_RINGS: int
    p_SKIP_CUTSCENE_BUTTON: int
    p_INSTANT_TELEPORT_MODE: int
    p_DISABLE_POPUPS: int
    p_INSTANT_ELEVATORS: int
    p_STARTING_REALM: int
    p_REALM_ACCESS: int
    p_PATCH_BEEN_WRITTEN_TO: int
    p_MW_SEED: int
    p_INIT: int
    p_BOSS_COSTS: int
    p_LG_DOOR_COSTS: int
    p_BALL_GADGET_COST: int
    p_INVINCIBILITY_COST: int
    p_SUPERCHARGE_COST: int
    p_BOSS_EASY_MODE: int
    p_SHOP_UNLOCK_MODE: int
    p_TELEPORT_ANYWHERE: int
    p_UNLOCK_ALL_SHOPS: int
    p_DISABLE_SHOP_PAD_PROXIMITY_ACTIVATE: int
    p_DISABLE_MAIN_SHOP_ALWAYS_AVAILABLE: int
    p_GEMS_IN_LOGIC: int
    p_GEMS_AVAILABLE: int
    p_UT_ENABLED: int
    p_XLS_SHOP_SHEETCOUNT_ALWAYS_1: int
    p_XLS_SHOP_SHEET_OFFSET_ALWAYS_4: int
    p_XLS_SHOP_ROWCOUNT: int
    p_XLS_SHOP_ITEMS: int
    p_SHOP_TEXT: int

    g_LOCATION_BITFIELD: int
    g_KEYRING_BITFIELD: int
    g_SHOPPAD_BITFIELD: int
    g_NUM_GEM_PACKS_RECEIVED: int
    g_NUM_LOCK_PICKS_RECEIVED: int
    g_NUM_FIRE_AMMO_RECEIVED: int
    g_NUM_ELECTRIC_AMMO_RECEIVED: int
    g_NUM_WATER_AMMO_RECEIVED: int
    g_NUM_ICE_AMMO_RECEIVED: int
    g_DEATHLINK_INGOING: int
    g_DEATHLINK_OUTGOING: int
    g_DEATHLINK_DEATHS_BEFORE_SEND: int
    g_DEATHLINK_DEATH_COUNTER: int
    g_INFINITE_BUTTERFLY_JAR: int
    g_INFINITE_DOUBLE_GEM: int
    g_FIREWORKS_ARE_RANDOMIZED: int
    g_RANDOMIZE_SHOP: int
    g_USE_KEY_RINGS: int
    g_SKIP_CUTSCENE_BUTTON: int
    g_INSTANT_TELEPORT_MODE: int
    g_DISABLE_POPUPS: int
    g_INSTANT_ELEVATORS: int
    g_STARTING_REALM: int
    g_REALM_ACCESS: int
    g_PATCH_BEEN_WRITTEN_TO: int
    g_MW_SEED: int
    g_INIT: int
    g_BOSS_COSTS: int
    g_LG_DOOR_COSTS: int
    g_BALL_GADGET_COST: int
    g_INVINCIBILITY_COST: int
    g_SUPERCHARGE_COST: int
    g_BOSS_EASY_MODE: int
    g_SHOP_UNLOCK_MODE: int
    g_TELEPORT_ANYWHERE: int
    g_UNLOCK_ALL_SHOPS: int
    g_DISABLE_SHOP_PAD_PROXIMITY_ACTIVATE: int
    g_DISABLE_MAIN_SHOP_ALWAYS_AVAILABLE: int
    g_GEMS_IN_LOGIC: int
    g_GEMS_AVAILABLE: int
    g_UT_ENABLED: int
    g_XLS_SHOP_SHEETCOUNT_ALWAYS_1: int
    g_XLS_SHOP_SHEET_OFFSET_ALWAYS_4: int
    g_XLS_SHOP_ROWCOUNT: int
    g_XLS_SHOP_ITEMS: int
    g_SHOP_TEXT: int

    n_AP_NOTIFICATION_COLOR: int
    n_AP_NOTIFICATION_TIMER: int
    n_AP_NOTIFICATION_TEXT_BUFFER: int

    OBJECTIVES: int
    DARK_GEM_COUNT: int
    LIGHT_GEM_COUNT: int
    DRAGON_EGG_COUNT: int

    GEMS: int
    TOTAL_GEMS: int

    LOCKPICKS: int

    ACTIVE_BREATH: int
    ABILITY_FLAGS: int
    IN_GAME: int
    PAUSE: int
    LOADING: int

    FIRE_BOMBS: int
    ICE_BOMBS: int
    WATER_BOMBS: int
    ELECTRIC_BOMBS: int


class SLUS_20884(AddressList):
    pass


class SLES_52569(AddressList):
    pass


class G5SE7D(AddressList):
    p_LOCATION_BITFIELD = 0x803d8fa8
    p_KEYRING_BITFIELD = 0x803d8ff8
    p_SHOPPAD_BITFIELD = 0x803d8ffa
    p_NUM_GEM_PACKS_RECEIVED = 0x803d8fff
    p_NUM_LOCK_PICKS_RECEIVED = 0x803d9000
    p_NUM_FIRE_AMMO_RECEIVED = 0x803d9001
    p_NUM_ELECTRIC_AMMO_RECEIVED = 0x803d9002
    p_NUM_WATER_AMMO_RECEIVED = 0x803d9003
    p_NUM_ICE_AMMO_RECEIVED = 0x803d9004
    p_DEATHLINK_INGOING = 0x803d9005
    p_DEATHLINK_OUTGOING = 0x803d9006
    p_DEATHLINK_DEATHS_BEFORE_SEND = 0x803d9007
    p_DEATHLINK_DEATH_COUNTER = 0x803d9008
    p_INFINITE_BUTTERFLY_JAR = 0x803d9009
    p_INFINITE_DOUBLE_GEM = 0x803d900a
    p_FIREWORKS_ARE_RANDOMIZED = 0x803d900b
    p_RANDOMIZE_SHOP = 0x803d900c
    p_USE_KEY_RINGS = 0x803d900d
    p_SKIP_CUTSCENE_BUTTON = 0x803d900e
    p_INSTANT_TELEPORT_MODE = 0x803d900f
    p_DISABLE_POPUPS = 0x803d9010
    p_INSTANT_ELEVATORS = 0x803d9011
    p_STARTING_REALM = 0x803d9012
    p_REALM_ACCESS = 0x803d9013
    p_PATCH_BEEN_WRITTEN_TO = 0x803d9017
    p_MW_SEED = 0x803d9018
    p_INIT = 0x803d901c
    p_BOSS_COSTS = 0x803d9020
    p_LG_DOOR_COSTS = 0x803d9024
    p_BALL_GADGET_COST = 0x803d9028
    p_INVINCIBILITY_COST = 0x803d9029
    p_SUPERCHARGE_COST = 0x803d902a
    p_BOSS_EASY_MODE = 0x803d902b
    p_SHOP_UNLOCK_MODE = 0x803d902f
    p_TELEPORT_ANYWHERE = 0x803d9030
    p_UNLOCK_ALL_SHOPS = 0x803d9031
    p_DISABLE_SHOP_PAD_PROXIMITY_ACTIVATE = 0x803d9032
    p_DISABLE_MAIN_SHOP_ALWAYS_AVAILABLE = 0x803d9033
    p_GEMS_IN_LOGIC = 0x803d9034
    p_GEMS_AVAILABLE = 0x803d9038
    p_UT_ENABLED = 0x803d903c
    p_XLS_SHOP_SHEETCOUNT_ALWAYS_1 = 0x803d9040
    p_XLS_SHOP_SHEET_OFFSET_ALWAYS_4 = 0x803d9044
    p_XLS_SHOP_ROWCOUNT = 0x803d9048
    p_XLS_SHOP_ITEMS = 0x803d904c
    p_SHOP_TEXT = 0x803d97ec

    g_LOCATION_BITFIELD = 0x80467ce4
    g_KEYRING_BITFIELD = 0x80467d34
    g_SHOPPAD_BITFIELD = 0x80467d36
    g_NUM_GEM_PACKS_RECEIVED = 0x80467d3b
    g_NUM_LOCK_PICKS_RECEIVED = 0x80467d3c
    g_NUM_FIRE_AMMO_RECEIVED = 0x80467d3d
    g_NUM_ELECTRIC_AMMO_RECEIVED = 0x80467d3e
    g_NUM_WATER_AMMO_RECEIVED = 0x80467d3f
    g_NUM_ICE_AMMO_RECEIVED = 0x80467d40
    g_DEATHLINK_INGOING = 0x80467d41
    g_DEATHLINK_OUTGOING = 0x80467d42
    g_DEATHLINK_DEATHS_BEFORE_SEND = 0x80467d43
    g_DEATHLINK_DEATH_COUNTER = 0x80467d44
    g_INFINITE_BUTTERFLY_JAR = 0x80467d45
    g_INFINITE_DOUBLE_GEM = 0x80467d46
    g_FIREWORKS_ARE_RANDOMIZED = 0x80467d47
    g_RANDOMIZE_SHOP = 0x80467d48
    g_USE_KEY_RINGS = 0x80467d49
    g_SKIP_CUTSCENE_BUTTON = 0x80467d4a
    g_INSTANT_TELEPORT_MODE = 0x80467d4b
    g_DISABLE_POPUPS = 0x80467d4c
    g_INSTANT_ELEVATORS = 0x80467d4d
    g_STARTING_REALM = 0x80467d4e
    g_REALM_ACCESS = 0x80467d4f
    g_PATCH_BEEN_WRITTEN_TO = 0x80467d53
    g_MW_SEED = 0x80467d54
    g_INIT = 0x80467d58
    g_BOSS_COSTS = 0x80467d5c
    g_LG_DOOR_COSTS = 0x80467d60
    g_BALL_GADGET_COST = 0x80467d64
    g_INVINCIBILITY_COST = 0x80467d65
    g_SUPERCHARGE_COST = 0x80467d66
    g_BOSS_EASY_MODE = 0x80467d67
    g_SHOP_UNLOCK_MODE = 0x80467d6b
    g_TELEPORT_ANYWHERE = 0x80467d6c
    g_UNLOCK_ALL_SHOPS = 0x80467d6d
    g_DISABLE_SHOP_PAD_PROXIMITY_ACTIVATE = 0x80467d6e
    g_DISABLE_MAIN_SHOP_ALWAYS_AVAILABLE = 0x80467d6f
    g_GEMS_IN_LOGIC = 0x80467d70
    g_GEMS_AVAILABLE = 0x80467d74
    g_UT_ENABLED = 0x80467d78
    g_XLS_SHOP_SHEETCOUNT_ALWAYS_1 = 0x80467d7c
    g_XLS_SHOP_SHEET_OFFSET_ALWAYS_4 = 0x80467d80
    g_XLS_SHOP_ROWCOUNT = 0x80467d84
    g_XLS_SHOP_ITEMS = 0x80467d88
    g_SHOP_TEXT = 0x80468528

    n_AP_NOTIFICATION_COLOR = 0x8029e35c
    n_AP_NOTIFICATION_TIMER = 0x8029e360
    n_AP_NOTIFICATION_TEXT_BUFFER = 0x8029e158

    OBJECTIVES = 0x80465C88
    DARK_GEM_COUNT = 0x80465BB7
    LIGHT_GEM_COUNT = 0x80465BB6
    DRAGON_EGG_COUNT = 0x80465BB8

    GEMS = 0x80465B68
    TOTAL_GEMS = 0x80465B6C

    LOCKPICKS = 0x80465b70

    ACTIVE_BREATH = 0x80465B60
    ABILITY_FLAGS = 0x80465B88
    IN_GAME = 0x8046F344 
    PAUSE = 0x8046F378
    LOADING = 0x0

    FIRE_BOMBS = 0x80465b74
    ICE_BOMBS = 0x80465b78
    WATER_BOMBS = 0x80465b7c
    ELECTRIC_BOMBS = 0x80465b80


class AbilityFlags(IntFlag):
    DoubleJump = 0x1
    SparxHealthUpgrade = 0x4
    PoleSpin = 0x10
    IceBreath = 0x20
    ElectricBreath = 0x40
    WaterBreath = 0x80
    DoubleGems = 0x200
    SuperchargeGadget = 0x1000
    InvincibilityGadget = 0x2000
    PurchasedLockpick = 0x4000
    WingShield = 0x8000
    WallKick = 0x10000
    Shockwave = 0x20000
    ButterflyJar = 0x40000
    FireBreath = 0x80000
    Glide = 0x100000
    Charge = 0x200000
    Swim = 0x400000


class ShopItemModel(IntEnum):
    Lockpick = 0x0200014c
    HealthUpgrade = 0x0200014b
    FireBomb = 0x02000077
    ElectricBomb = 0x020000a7
    WaterBomb = 0x02000114
    IceBomb = 0x020000a1
    FireMag = 0x0200023f
    ElectricMag = 0x0200023e
    WaterMag = 0x02000241
    IceMag = 0x02000240
    Keychain = 0x02000242
    ButterflyJar = 0x020001b1
    DoubleGems = 0x0200023a
    Shockwave = 0x0200023b
    TeleportTicket = 0x0200023c
    TeleportTicketMain = 0x0200023d


class TextEntry:
    base = 0x28010000

    def __init__(self, index: int, text: str):
        self.index = index
        self._text = text
        self.been_bought = False
    
    @property
    def address(self):
        return self.base + self.index

    @property
    def text(self):
        if len(self._text) >= 48:
            return self._text[:44] + "..."
        return self._text
    
    def to_bytes(self, byteorder: Literal['big', 'little'] = 'big'):
        return struct.pack(('<' if byteorder == 'little' else '>') + '?B96s', self.been_bought, 0, self.text.encode("utf_16_be"))


@dataclass
class XLSShoppingItem:
    entity: ShopItemModel
    text: TextEntry
    cost: tuple[int, int] # [u16, u16] (base, remote). Might be treated as if [u32] (price everywhere) if shop_rando = True
    large_prices: bool
    
    @property
    def structure(self) -> str:
        return "IIIIihhII" if self.large_prices else "IIIIHHhhII"

    def to_bytes(self, byteorder: Literal['big', 'little'] = 'big'):
        args = [self.cost[0], self.cost[1], 1, 0, 0, 0]
        if self.large_prices: del args[0]
        return struct.pack(('<' if byteorder == 'little' else '>') + self.structure, self.entity, 0x01000028, 
                           self.text.address, self.text.address, *args)
