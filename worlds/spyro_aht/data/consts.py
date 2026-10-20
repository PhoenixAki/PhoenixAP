import struct
from dataclasses import dataclass
from enum import IntEnum, IntFlag
from typing import Literal
from BaseClasses import ItemClassification

# compared in world definition against YAML. Messages that are of equal or lower log level are logged
class LoggingLevel(IntEnum):
    WARNING = 0  # 0 because warnings are always logged, even if level is set to none
    NONE = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    MAXIMUM = 5

MOD_MAJOR = 20
MOD_MINOR = 2
MOD_VERSION_STR = f"{MOD_MAJOR}.{MOD_MINOR}"

CLIENT_MAJOR = 2
CLIENT_MINOR = 2
CLIENT_REVISION = 2
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

GAME_ID_NTSC = "G5SE7D"
GAME_ID_PAL = "G5SP7D"

# (AP location ID, bitfield offset)
LOCATIONS_BITFIELD: dict[int, int] = {
    # Dark Gems 101-140
    101: 65, 102: 67, 103: 66, 104: 48, 105: 58, 106: 50, 107: 34, 108: 33, 109: 36, 110: 40,
    111: 146, 112: 148, 113: 152, 114: 154, 115: 15, 116: 18, 117: 16, 118: 3, 119: 4, 120: 6,
    121: 101, 122: 102, 123: 97, 124: 90, 125: 91, 126: 107, 127: 108, 128: 110, 129: 115, 130: 113,
    131: 142, 132: 167, 133: 163, 134: 165, 135: 177, 136: 78, 137: 85, 138: 133, 139: 132, 140: 134,
    # Light Gems (non-chest) 201-285
    201: 182, 202: 69, 203: 71, 204: 73, 205: 56, 206: 60, 207: 51, 208: 55, 209: 53, 210: 186,
    211: 64, 212: 184, 213: 54, 214: 31, 215: 37, 216: 44, 217: 188, 218: 46, 219: 39, 220: 42,
    221: 192, 222: 158, 223: 157, 224: 155, 225: 153, 226: 150, 227: 193, 228: 190, 229: 159, 230: 23,
    231: 22, 232: 26, 233: 25, 234: 197, 235: 17, 236: 29, 237: 0, 238: 195, 239: 1, 240: 13,
    241: 89, 242: 201, 243: 199, 244: 98, 245: 103, 246: 93, 247: 99, 248: 100, 249: 92, 250: 204,
    251: 121, 252: 122, 253: 127, 254: 203, 255: 128, 256: 125, 257: 123, 258: 209, 259: 106, 260: 206,
    261: 207, 262: 210, 263: 114, 264: 208, 265: 143, 266: 212, 267: 214, 268: 160, 269: 161, 270: 164,
    271: 172, 272: 175, 273: 176, 274: 179, 275: 217, 276: 79, 277: 80, 278: 219, 279: 82, 280: 81,
    281: 131, 282: 139, 283: 141, 284: 136, 285: 138,
    # Dragon Eggs (non-chest) 301-364
    301: 75, 302: 181, 303: 68, 304: 72, 305: 70, 306: 57, 307: 49, 308: 63, 309: 185, 310: 52,
    311: 183, 312: 32, 313: 35, 314: 41, 315: 187, 316: 38, 317: 43, 318: 191, 319: 145, 320: 149,
    321: 156, 322: 147, 323: 189, 324: 151, 325: 21, 326: 24, 327: 28, 328: 196, 329: 30, 330: 5,
    331: 194, 332: 2, 333: 200, 334: 94, 335: 198, 336: 95, 337: 96, 338: 120, 339: 126, 340: 124,
    341: 202, 342: 205, 343: 109, 344: 111, 345: 118, 346: 116, 347: 112, 348: 144, 349: 211, 350: 215,
    351: 162, 352: 213, 353: 166, 354: 173, 355: 174, 356: 216, 357: 178, 358: 83, 359: 218, 360: 88,
    361: 84, 362: 140, 363: 135, 364: 137,
    # Fireworks 401-422
    401: 252, 402: 250, 403: 249, 404: 251, 405: 254, 406: 255, 407: 253, 408: 261, 409: 262, 410: 260,
    411: 256, 412: 257, 413: 258, 414: 259, 415: 263, 416: 265, 417: 264, 418: 266, 419: 267, 420: 268,
    421: 269, 422: 270, 
    # Elder Abilities 601-604
    601: 241, 602: 242, 603: 243, 604: 244,
    # Bosses (only breath rewards) 701, 703, 705
    701: 245, 703: 246, 705: 247, 707: 248,
    # Chests 801-821 (empty), 822-836 (light gems), 837-852 (dragon eggs)
    801: 221, 802: 220, 803: 223, 804: 222, 805: 225, 806: 224, 807: 226, 808: 230, 809: 227, 810: 228,
    811: 229, 812: 234, 813: 233, 814: 232, 815: 235, 816: 231, 817: 236, 818: 237, 819: 238, 820: 239,
    821: 240, 822: 76, 823: 77, 824: 61, 825: 45, 826: 47, 827: 19, 828: 8, 829: 9, 830: 11,
    831: 12, 832: 117, 833: 168, 834: 169, 835: 180, 836: 86, 837: 74, 838: 59, 839: 62, 840: 20,
    841: 27, 842: 7, 843: 10, 844: 14, 845: 104, 846: 105, 847: 130, 848: 129, 849: 119, 850: 170,
    851: 171, 852: 87
}

MINIGAME_OBJECTIVES: dict[int, tuple[int, int]] = {
    0x44000017: (302, 201), 0x440000a7: (328, 234), 0x44000094: (342, 260), 0x440000d1: (352, 267),  # byrd
    0x44000013: (309, 210), 0x4400004b: (323, 228), 0x4400008f: (335, 243), 0x440000b6: (359, 278),  # blink
    0x4400000c: (311, 212), 0x4400001a: (318, 221), 0x4400008a: (333, 242), 0x44000097: (349, 266),  # turret
    0x4400007b: (315, 217), 0x440000a5: (331, 238), 0x440000aa: (341, 254), 0x440000bb: (356, 275)  # sparx
}

#
BOSS_LAIR_OPEN_OBJECTIVES = {
    0x44000111: (701, 702),  # gnorc
    0x44000112: (703, 704),  # ineptune
    0x44000113: (705, 706),  # red
    0x44000114: (707,)  # mecha-red
}

BOSS_DEFEATED_OBJECTIVES = [
    0x44000081, # Defeat Gnasty Gnorc
    0x44000082, # Defeat Ineptune
    0x44000083, # Defeat Red
    0x44000084  # Defeat Mecha-Red
]

###############LOCATION ID REFERENCE###############
DARK_GEM_IDS = list(range(101, 141))  # IDs 101-140
LIGHT_GEM_IDS = list(range(201, 286)) + list(range(822, 837))  # IDs 201-285 and 822-836
DRAGON_EGG_IDS = list(range(301, 365)) + list(range(837, 853))  # IDs 301-364 and 837-852
FIREWORK_IDS = list(range(401, 423))  # IDs 401-422
STARTER_CHECK_IDS = list(range(501, 505))  # IDs 501-504
ELDER_ABILITY_IDS = list(range(601, 605))  # IDs 601-604
BOSS_IDS = list(range(701, 708))  # IDs 701-707. odds are "defeat", evens are breaths
LOCKED_CHEST_IDS = list(range(801, 853))  # IDs 801-852
SHOP_ITEM_IDS = list(range(901, 957))  # IDs 901-956
# these 4 aren't as generalizable since the ID design didn't specifically separate them 
BYRD_IDS = [302, 201, 328, 234, 342, 260, 352, 267]
BLINK_IDS = [309, 210, 323, 228, 335, 243, 359, 278]
TURRET_IDS = [311, 212, 318, 221, 333, 242, 349, 266]
SPARX_IDS = [315, 217, 331, 238, 341, 254, 356, 275]

###############ITEM REFERENCES###############
# just to shorten references to these below
filler, prog, useful, trap, prog_dep_skip = ItemClassification.filler, ItemClassification.progression, ItemClassification.useful, ItemClassification.trap, ItemClassification.progression_deprioritized_skip_balancing

ITEM_INFO: dict[str, tuple] = {  # "Name": (id, classification)
    # elder abilities
    "Double Jump": (1, prog), "Pole Spin": (2, prog), "Wing Shield": (3, prog), "Wall Kick": (4, prog),
    # breaths
    "Fire Breath": (10, prog), "Electric Breath": (11, prog), "Water Breath": (12, prog), "Ice Breath": (13, prog),
    # abilities
    "Swim": (20, prog), "Glide": (21, prog), "Charge": (22, prog),
    # per-level key rings
    "Dragon Village Key Ring": (30, prog), "Crocovile Swamp Key Ring": (31, prog), "Dragonfly Falls Key Ring": (32, prog),
    "Coastal Remains Key Ring": (33, prog), "Sunken Ruins Key Ring": (34, prog), "Cloudy Domain Key Ring": (35, prog),
    "Frostbite Village Key Ring": (36, prog), "Gloomy Glacier Key Ring": (37, prog), "Ice Citadel Key Ring": (38, prog),
    "Stormy Beach Key Ring": (39, prog), "Molten Mount Key Ring": (40, prog), "Magma Falls Key Ring": (41, prog),
    "Dark Mine Key Ring": (42, prog), "Red's Laboratory Key Ring": (43, prog),
    # per-realm key rings
    "Dragon Kingdom Key Ring": (44, prog), "Lost Cities Key Ring": (45, prog), "Icy Wilderness Key Ring": (46, prog), "Volcanic Isle Key Ring": (47, prog),
    # access cards
    "Dragon Kingdom Access Card": (50, prog), "Lost Cities Access Card": (51, prog), "Icy Wilderness Access Card": (52, prog), "Volcanic Isle Access Card": (53, prog),
    # shop items
    "Health Unit+": (60, useful), "Butterfly Jar": (61, useful), "Double Gems": (62, useful), "Shockwave": (63, useful),
    "Lockpick": (64, prog_dep_skip), "Lockpick Bundle": (65, prog),
    # collectibles
    "Dark Gem": (85, prog_dep_skip), "Dark Gem Bundle": (86, prog), "Light Gem": (87, prog_dep_skip), "Light Gem Bundle": (88, prog),
    # individual shop unlocks
    "Dragon Village - Village Depot Shop Unlock": (95, prog),
    "Crocovile Swamp - Perilous Pyramid Shop Unlock": (96, prog), "Crocovile Swamp - Forgotten Temple Shop Unlock": (97, prog), "Crocovile Swamp - Elder's Tree Shop Unlock": (98, prog),
    "Dragonfly Falls - Steep Canyon Shop Unlock": (99, prog), "Dragonfly Falls - Tropical Cove Shop Unlock": (100, prog), "Dragonfly Falls - Secret Area Shop Unlock": (101, prog),
    "Coastal Remains - Coastal Depot Shop Unlock": (102, prog), "Coastal Remains - Domain Doorstep Shop Unlock": (103, prog), "Coastal Remains - Waterfall Walkway Shop Unlock": (104, prog),
    "Sunken Ruins - Atlantian Entryway Shop Unlock": (105, prog), "Sunken Ruins - The Depths Shop Unlock": (106, prog), "Sunken Ruins - Toxic Rise Shop Unlock": (107, prog),
    "Cloudy Domain - Elevator Top Shop Unlock": (108, prog), "Cloudy Domain - Elder's Homestead Shop Unlock": (109, prog), "Cloudy Domain - Tallest Tower Shop Unlock": (110, prog),
    "Frostbite Village - Frosty Depot Shop Unlock": (111, prog), "Frostbite Village - Icy Camp Shop Unlock": (112, prog), "Frostbite Village - Eskimole Village Shop Unlock": (113, prog),
    "Ice Citadel - Cool Courtyard Shop Unlock": (114, prog), "Ice Citadel - Supercharge Central Shop Unlock": (115, prog), "Ice Citadel - Royal Chamber Shop Unlock": (116, prog), "Ice Citadel - Drawbridge Drop-off Shop Unlock": (117, prog),
    "Stormy Beach - Stormy Depot Shop Unlock": (118, prog),
    "Molten Mount - Destroyed Village Shop Unlock": (119, prog), "Molten Mount - Collapsed Bridge Shop Unlock": (120, prog), "Molten Mount - Lumber Storage Shop Unlock": (121, prog),
    "Magma Falls - Crackling Cave Shop Unlock": (122, prog), "Magma Falls - Chains of Lava Shop Unlock": (123, prog), "Magma Falls - Sparx Can Fly Shop Unlock": (124, prog),
    "Dark Mine - Mine Mouth Shop Unlock": (125, prog), "Dark Mine - Hidden Depths Shop Unlock": (126, prog), "Dark Mine - Miner's Drop Shop Unlock": (127, prog),
    "Red's Laboratory - Celestial Show Shop Unlock": (128, prog), "Red's Laboratory - Mechanical Mishaps Shop Unlock": (129, prog),
    "Red's Laboratory - Pre-production Shop Unlock": (130, prog), "Red's Laboratory - Laser Leaps Shop Unlock": (131, prog),
    # progressive shop unlocks
    "Progressive Dragon Village - Shop Unlock": (132, prog), "Progressive Crocovile Swamp - Shop Unlock": (133, prog), "Progressive Dragonfly Falls - Shop Unlock": (134, prog),
    "Progressive Coastal Remains - Shop Unlock": (135, prog), "Progressive Sunken Ruins - Shop Unlock": (136, prog), "Progressive Cloudy Domain - Shop Unlock": (137, prog),
    "Progressive Frostbite Village - Shop Unlock": (138, prog), "Progressive Ice Citadel - Shop Unlock": (139, prog),
    "Progressive Stormy Beach - Shop Unlock": (140, prog), "Progressive Molten Mount - Shop Unlock": (141, prog), "Progressive Magma Falls - Shop Unlock": (142, prog),
    "Progressive Dark Mine - Shop Unlock": (143, prog), "Progressive Red's Laboratory - Shop Unlock": (144, prog),
    # level shop unlocks
    "Dragon Village - Shop Unlock": (145, prog), "Crocovile Swamp - Shop Unlock": (146, prog), "Dragonfly Falls - Shop Unlock": (147, prog),
    "Coastal Remains - Shop Unlock": (148, prog), "Sunken Ruins - Shop Unlock": (149, prog), "Cloudy Domain - Shop Unlock": (150, prog),
    "Frostbite Village - Shop Unlock": (151, prog), "Ice Citadel - Shop Unlock": (152, prog),
    "Stormy Beach - Shop Unlock": (153, prog), "Molten Mount - Shop Unlock": (154, prog), "Magma Falls - Shop Unlock": (155, prog),
    "Dark Mine - Shop Unlock": (156, prog), "Red's Laboratory - Shop Unlock": (157, prog),
    # realm shop unlocks
    "Dragon Kingdom - Shop Unlock": (158, prog), "Lost Cities - Shop Unlock": (159, prog), "Icy Wilderness - Shop Unlock": (160, prog), "Volcanic Isle - Shop Unlock": (161, prog),
    # non-shinies filler
    "Dragon Egg": (170, filler), "Gem Pack": (171, filler),
    "Fire Bomb": (172, filler), "Electric Bomb": (173, filler), "Water Bomb": (174, filler), "Ice Bomb": (175, filler),
    # shinies filler
    "Spare Jetpack for Sgt. Byrd": (180, filler), "New Goggles for Blink": (181, filler), "New Bow for Hunter": (182, filler),
    "New Monocle for Moneybags": (183, filler), "A Cracked Gem": (184, filler), "Mouthwash for Inpetune": (185, filler),
    "Anger Management Class for Red": (186, filler), "A Long Story from Elder Tomas": (187, filler), "1 Million Brain Cells": (188, filler),
    "Treasure from the 10th Dimension": (189, filler), "Stress Ball for Gnasty Gnorc": (190, filler), "Portable Heater for the Ice Princess": (191, filler),
    "Apartment Lease for Teena": (192, filler), "New Sneakers for Crash": (193, filler), "Green Eco for Jak": (194, filler), "Oil Change for Clank": (195, filler),
    # traps
    "Spam Call": (200, trap), "Reverse Controls": (201, trap), "Damage Sparx": (202, trap), "Gem Tax": (203, trap), "Bounce": (204, trap)
}

ITEM_GROUP_IDS = {  # "Name": [start of id range, end of id range] INCLUSIVE
    "Elder Abilities": [1, 4], "Breaths": [10, 13], "Abilities": [20, 22], "Key Rings": [30, 47], "Access Cards": [50, 53],
    "Shop Items": [60, 65], "Collectibles": [85, 88], "Shop Unlocks": [95, 161], "Filler": [170, 195], "Traps": [200, 204] 
}

REALM_KEY_RING_LOOKUP = {  # converts a realm key ring ID to a list of level key ring IDs
    ITEM_INFO["Dragon Kingdom Key Ring"][0]: list(range(ITEM_GROUP_IDS["Key Rings"][0], ITEM_GROUP_IDS["Key Rings"][0]+3)),
    ITEM_INFO["Lost Cities Key Ring"][0]: list(range(ITEM_GROUP_IDS["Key Rings"][0]+3, ITEM_GROUP_IDS["Key Rings"][0]+6)),
    ITEM_INFO["Icy Wilderness Key Ring"][0]: list(range(ITEM_GROUP_IDS["Key Rings"][0]+6, ITEM_GROUP_IDS["Key Rings"][0]+9)),
    ITEM_INFO["Volcanic Isle Key Ring"][0]: list(range(ITEM_GROUP_IDS["Key Rings"][0]+9, ITEM_GROUP_IDS["Key Rings"][0]+14))
}

DEATHLINK_MESSAGES = [
    "{name} died.", "{name} ended their tail.", "{name} was fed to the fish.", "{name} forgot their wings.",
    "{name} did a jig and then blew up.", "{name} became a dragon fossil.", "{name} became a purple pancake.",
    "{name} became grape ice cream.", "{name} spent one of their 9 lives.", "{name} failed to land on their feet.",
    "{name} discovered why cats hate water.", "{name} became roadkill.", "{name} blinked out of existence.",
    "{name} went in too deep.", "{name} touched the Earth's mantle.", "{name} discovered the dangers of cave diving.",
    "{name} caved in.", "{name} died.", "{name} failed a water landing.",
    "{name} became roasted chicken.", "{name}'s parachute failed.", "{name} ended the Bug's Life.",
    "{name} dropped the ball.", "{name} let Fredneck starve.", "{name} was a terrible godfather.",
    "{name} was put on ice.", "{name} was overrun."
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

# level name -> realm
LEVEL_TO_REALM = {
    "Dragon Village": "Dragon Kingdom", "Crocovile Swamp": "Dragon Kingdom", "Dragonfly Falls": "Dragon Kingdom",
    "Coastal Remains": "Lost Cities", "Sunken Ruins": "Lost Cities", "Cloudy Domain": "Lost Cities",
    "Frostbite Village": "Icy Wilderness", "Gloomy Glacier": "Icy Wilderness", "Ice Citadel": "Icy Wilderness",
    "Stormy Beach": "Volcanic Isle", "Molten Mount": "Volcanic Isle", "Magma Falls": "Volcanic Isle", "Dark Mine": "Volcanic Isle", "Red's Laboratory": "Volcanic Isle"
}

# used to find all shops for a given level, in vanilla game order (list is reversed if reverse progressive is in use)
LEVEL_SHOP_LOOKUP = {
    "Dragon Village": ["Village Depot"],
    "Crocovile Swamp": ["Perilous Pyramid", "Forgotten Temple", "Elder's Tree"],
    "Dragonfly Falls": ["Steep Canyon", "Tropical Cove", "Secret Area"],
    "Coastal Remains": ["Coastal Depot", "Domain Doorstep", "Waterfall Walkway"],
    "Sunken Ruins": ["Atlantian Entryway", "The Depths", "Toxic Rise"],
    "Cloudy Domain": ["Elevator Top", "Elder's Homestead", "Tallest Tower"],
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
    "Lost Cities": ["Coastal Remains", "Sunken Ruins", "Cloudy Domain"],
    "Icy Wilderness": ["Frostbite Village", "Ice Citadel"],
    "Volcanic Isle": ["Stormy Beach", "Molten Mount", "Magma Falls", "Dark Mine", "Red's Laboratory"]
}

# used when generating location groups. Differs from REALM_LEVEL_LOOKUP in that it includes GG and separates MFt and MFb
REALM_LEVEL_LISTS = {
    "Dragon Kingdom": ["Dragon Village", "Crocovile Swamp", "Dragonfly Falls"],
    "Lost Cities": ["Coastal Remains", "Sunken Ruins", "Cloudy Domain"],
    "Icy Wilderness": ["Frostbite Village", "Gloomy Glacier", "Ice Citadel"],
    "Volcanic Isle": ["Stormy Beach", "Molten Mount", "Magma Falls Top", "Magma Falls Bottom", "Dark Mine", "Red's Laboratory"]
}

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

ABILITY_MATCH = {
    ITEM_INFO["Double Jump"][0]: AbilityFlags.DoubleJump, ITEM_INFO["Pole Spin"][0]: AbilityFlags.PoleSpin, ITEM_INFO["Wing Shield"][0]: AbilityFlags.WingShield,
    ITEM_INFO["Wall Kick"][0]: AbilityFlags.WallKick, ITEM_INFO["Fire Breath"][0]: AbilityFlags.FireBreath, ITEM_INFO["Electric Breath"][0]: AbilityFlags.ElectricBreath,
    ITEM_INFO["Water Breath"][0]: AbilityFlags.WaterBreath, ITEM_INFO["Ice Breath"][0]: AbilityFlags.IceBreath, ITEM_INFO["Swim"][0]: AbilityFlags.Swim,
    ITEM_INFO["Glide"][0]: AbilityFlags.Glide, ITEM_INFO["Charge"][0]: AbilityFlags.Charge, ITEM_INFO["Health Unit+"][0]: AbilityFlags.SparxHealthUpgrade, ITEM_INFO["Shockwave"][0]: AbilityFlags.Shockwave
}


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

    def __init__(self, index: int, text: str, bought: bool):
        self.index = index
        self._text = text
        self.been_bought = bought
    
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
