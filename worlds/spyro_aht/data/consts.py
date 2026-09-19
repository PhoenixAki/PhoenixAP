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

MOD_MAJOR = 18
MOD_MINOR = 0
MOD_VERSION_STR = f"{MOD_MAJOR}.{MOD_MINOR}"

CLIENT_MAJOR = 2
CLIENT_MINOR = 2
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

KEY_RINGS = [0x22, 0x23, 0x24, 0x25, 0x27, 0x26, 0x28, 0x29, 0x2A, 0x2B, 0x2C, 0x2D, 0x2E, 0x2F]

MINIGAME_OBJECTIVES: dict[int, tuple[int, int]] = {
    # byrd
    0x44000017: (302, 201),
    0x440000a7: (328, 234),
    0x44000094: (342, 260),
    0x440000d1: (352, 267),
    # blink
    0x44000013: (309, 210),
    0x4400004b: (323, 228),
    0x4400008f: (335, 243),
    0x440000b6: (359, 278),
    # turret
    0x4400000c: (311, 212),
    0x4400001a: (318, 221),
    0x4400008a: (333, 242),
    0x44000097: (349, 266),
    # sparx
    0x4400007b: (315, 217),
    0x440000a5: (331, 238),    
    0x440000aa: (341, 254),
    0x440000bb: (356, 275)
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

DEATHLINK_MESSAGES = [
    "{name} died.", "{name} ended their tail.", "{name} was fed to the fish.", "{name} forgot their wings.",
    "{name} did a jig and then blew up.", "{name} became a dragon fossil.", "{name} became a purple pancake.",
    "{name} became grape ice cream.", "{name} spend one of their 9 lives.", "{name} failed to land on their feet.",
    "{name} discovered why cats hate water.", "{name} became roadkill.", "{name} blinked out of existence.",
    "{name} went in too deep.", "{name} touched the Earth's mantle.", "{name} discovered the dangers of cave diving.",
    "{name} caved in.", "{name} died in a reality-defying fashion.", "{name} failed a water landing.",
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
