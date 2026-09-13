from __future__ import annotations

import asyncio
import random
import struct
from typing import TYPE_CHECKING

import dolphin_memory_engine

from NetUtils import NetworkItem
from .client import GenericClient
from ..data import consts

if TYPE_CHECKING:
    from ..context import SpyroAHTContext

class DolphinClient(GenericClient):
    def retrieve_mod_version(self) -> tuple[int, int]:
        mod_version_full = dolphin_memory_engine.read_word(self.addresses.AP_VERSION_MAJOR)
        mod_version_major = mod_version_full >> 16
        mod_version_minor = mod_version_full & 0xFFFF
        if mod_version_major == 0:  # old mod versions reported only a single version in the space the minor version currently uses now. Need adjusting to match new format
            return mod_version_minor, 0
        else:
            return mod_version_major, mod_version_minor
        
    def __init__(self) -> None:
        super().__init__()
        self._notification_task = asyncio.create_task(self.notification_task())
        self.ready = asyncio.Event()
        self.msg_queue = asyncio.Queue()
        self.addresses = consts.G5SE7D() # temp
        
        self.goal_list = []
        self.goal_target, self.goal_tally = 0, 0
        self.finished_goals = [False, False, False, False, False, False, False, False, False]
    
    async def notification_task(self):
        from CommonClient import logger
        try:
            await self.ready.wait()
            while True:
                await asyncio.sleep(0.5)
                if await self.should_process_checks():
                    await asyncio.sleep(5)
                    dolphin_memory_engine.write_word(self.addresses.n_AP_NOTIFICATION_TIMER, 0)
                    col, msg = await self.msg_queue.get()

                    if len(msg) > 254:
                        msg = msg[:254]
                    
                    colour = struct.pack(">BBBB", *col)
                    dolphin_memory_engine.write_bytes(self.addresses.n_AP_NOTIFICATION_COLOR, colour)
                    dolphin_memory_engine.write_bytes(self.addresses.n_AP_NOTIFICATION_TEXT_BUFFER, (msg + "\0").encode("utf_16_be"))
                    dolphin_memory_engine.write_word(self.addresses.n_AP_NOTIFICATION_TIMER, 5*60)
        except Exception:
            logger.error("ERROR IN NOTIFICATION TASK, REPORT IN THREAD", exc_info=True)

    async def connect(self):
        if not dolphin_memory_engine.is_hooked():
            from CommonClient import logger
            logger.info(f"Spyro: A Hero's Tail Archipelago (AHT AP) client initializing.")
            logger.info(f"Detected client version: {consts.CLIENT_VERSION_STR}.")            
            dolphin_memory_engine.hook()
            
            game_id = dolphin_memory_engine.read_bytes(0x80000000, 6)
            logger.info(f"Detected game ID: {game_id.decode()!r}.")

            if game_id == b'G5SE7D':
                self.addresses = consts.G5SE7D()
            elif game_id == b'G5SP7D':
                self.addresses = consts.G5SP7D()
            else:
                # dolphin_memory_engine.un_hook()
                logger.error("WARNING: Invalid or unsupported game ID.")
                return False

            mod_version_major, mod_version_minor = retrieve_mod_version()
            logger.info(f"Detected game mod version: {mod_version_major}.{mod_version_minor}.")
            
            if mod_version_major != consts.MOD_MAJOR:
                # dolphin_memory_engine.un_hook()
                logger.error(f"WARNING: Mod major version {mod_version_major} is incompatible with AHT AP {consts.CLIENT_VERSION_STR}. Please update game mod to major version {consts.MOD_MAJOR}.")
                return False
            if mod_version_major == consts.MOD_MAJOR and mod_version_minor < consts.MOD_MINOR:
                logger.warn(f"NOTICE: Mod minor version {mod_version_minor} is compatible with AHT AP {consts.CLIENT_VERSION_STR}, but there is at least one new minor version available which may contain new features or bugfixes. Update at your leisure.")
            else:
                logger.info(f"Game mod version {mod_version_major}.{mod_version_minor} and AHT AP {consts.CLIENT_VERSION_STR} are compatible. Enjoy!")    
        self.ready.set()
    
    async def disconnect(self):
        dolphin_memory_engine.write_byte(self.addresses.p_PATCH_BEEN_WRITTEN_TO, 0)
        self._notification_task.cancel()
        if dolphin_memory_engine.is_hooked():
            dolphin_memory_engine.un_hook()
            self.ready.clear()
    
    async def should_process_checks(self) -> bool:
        m_state = dolphin_memory_engine.read_word(self.addresses.IN_GAME)
        m_pause = dolphin_memory_engine.read_byte(self.addresses.PAUSE)
        return m_state == 3 and (m_pause & 0x80 == 0)

    async def scan_locations(self, slot_data: dict) -> set[int]:
        result: set[int] = set()
        for aploc, index in consts.LOCATIONS_BITFIELD.items():
            await asyncio.sleep(0)

            addr = self.addresses.g_LOCATION_BITFIELD + (index * 2) // 8
            data = dolphin_memory_engine.read_byte(addr)
            flag = data & (0b01 << ((index * 2) % 8))
            if flag:
                match aploc:
                    case 701:  # breath from gnasty -> add defeated gnasty
                        result.update({701, 702})
                    case 703:  # breath from ineptune -> add defeated ineptune
                        result.update({703, 704})
                    case 705:  # breath from red -> add defeated red
                        result.update({705, 706})
                    case _:
                        result.add(aploc)
        
        # TODO: continue from here
        if slot_data["shop_randomization"]:
            for i in range(slot_data["shop_item_count"]):
                await asyncio.sleep(0)
                purchase_flag = dolphin_memory_engine.read_byte(self.addresses.g_SHOP_TEXT + (0x62 * i))
                if purchase_flag:
                    result.add(901 + i)
        return result

    async def set_flag(self, address: int, flag: int, to: bool):
        flags = dolphin_memory_engine.read_word(address)
        if to:
            flags |= flag
        else:
            flags &= ~flag
        dolphin_memory_engine.write_word(address, int(flags))
    
    async def get_flag(self, address: int, flag: int) -> bool:
        return dolphin_memory_engine.read_word(address) & flag != 0

    async def get_objective(self, objective: int) -> bool:
        index = (objective & 0xFFFF) - 1
        uint = index // 32
        bit = index % 32
        if await self.get_flag(self.addresses.OBJECTIVES + (uint * 4), 1 << bit):
            self.goal_tally += 1
            return True
        else:
            return False
    
    async def debug_add_item(self, amount: int, address: int, bytes: int) -> bool:
        current_amount = int.from_bytes(dolphin_memory_engine.read_bytes(address, bytes))
        dolphin_memory_engine.write_bytes(address, (current_amount + amount).to_bytes(bytes, 'big'))
        if address == self.addresses.GEMS:
            current_total = int.from_bytes(dolphin_memory_engine.read_bytes(self.addresses.TOTAL_GEMS, bytes))
            dolphin_memory_engine.write_bytes(self.addresses.TOTAL_GEMS, (current_total + amount).to_bytes(bytes, 'big'))        
        return True
    
    async def has_any_breath(self) -> bool:
        b = dolphin_memory_engine.read_word(self.addresses.ABILITY_FLAGS)
        return b & (0x800e0) != 0

    async def set_breath(self, breath_id: int):
        dolphin_memory_engine.write_word(self.addresses.ACTIVE_BREATH, breath_id)
    
    async def get_item_count(self, address: int) -> int:
        return dolphin_memory_engine.read_byte(address)
    
    async def set_item(self, address: int, count: int):
        dolphin_memory_engine.write_byte(address, count)
    
    async def enable_butterfly_jar(self):
        check = dolphin_memory_engine.read_byte(self.addresses.g_INFINITE_BUTTERFLY_JAR)
        if not check:
            dolphin_memory_engine.write_byte(self.addresses.g_INFINITE_BUTTERFLY_JAR, 1)
            await self.set_flag(self.addresses.ABILITY_FLAGS, consts.AbilityFlags.ButterflyJar, True)
    
    async def add_gem_pack(self):
        value = random.randint(400, 600)
        double = dolphin_memory_engine.read_byte(self.addresses.g_INFINITE_DOUBLE_GEM)
        if double:
            value *= 2
        count = dolphin_memory_engine.read_word(self.addresses.GEMS)
        total = dolphin_memory_engine.read_word(self.addresses.TOTAL_GEMS)
        dolphin_memory_engine.write_word(self.addresses.GEMS, count + value)
        dolphin_memory_engine.write_word(self.addresses.TOTAL_GEMS, total + value)
    
    async def import_deathlink(self, mode: int):
        dolphin_memory_engine.write_byte(self.addresses.g_DEATHLINK_INGOING, mode)

    async def export_deathlink(self) -> bool:
        b = dolphin_memory_engine.read_byte(self.addresses.g_DEATHLINK_OUTGOING)
        if b:
            dolphin_memory_engine.write_byte(self.addresses.g_DEATHLINK_OUTGOING, 0)
            return b
        return False

    async def apply_patch(self, ctx: "SpyroAHTContext"):
        dolphin_memory_engine.write_byte(self.addresses.p_SKIP_CUTSCENE_BUTTON, ctx.slot_data['skip_cutscenes'])
        dolphin_memory_engine.write_byte(self.addresses.p_DISABLE_POPUPS, 1)
        dolphin_memory_engine.write_byte(self.addresses.p_INSTANT_ELEVATORS, ctx.slot_data['skip_elevators'])
        dolphin_memory_engine.write_word(self.addresses.p_MW_SEED, (int(ctx._seed) & 0xffffffff))
        dolphin_memory_engine.write_byte(self.addresses.p_USE_KEY_RINGS, ctx.slot_data['key_rings'])
        dolphin_memory_engine.write_byte(self.addresses.p_FIREWORKS_ARE_RANDOMIZED, ctx.slot_data['firework_checks'])
        dolphin_memory_engine.write_byte(self.addresses.p_UT_ENABLED, int(ctx.tracker_found))
        if ctx.slot_data['death_link']:
            dolphin_memory_engine.write_byte(self.addresses.p_DEATHLINK_DEATHS_BEFORE_SEND, ctx.slot_data['death_link_amnesty'])

        if ctx.slot_data['pause_menu_patch'] == 0:
            dolphin_memory_engine.write_byte(self.addresses.p_INSTANT_TELEPORT_MODE, 2)
        elif ctx.slot_data['pause_menu_patch'] == 1:
            dolphin_memory_engine.write_byte(self.addresses.p_INSTANT_TELEPORT_MODE, 1)
        
        if ctx.slot_data['shop_randomization']:
            locations = consts.SHOP_ITEM_IDS[:ctx.slot_data["shop_item_count"]]
            await ctx.send_msgs([{"cmd": "LocationScouts", "locations": locations, "create_as_hint": 0}])
            await ctx._shop_items_received.wait()
            await self._prepare_shop_items(ctx, *ctx._shop_items)
        
        if ctx.slot_data["randomize_light_gem_door_costs"]:
            dolphin_memory_engine.write_bytes(self.addresses.p_LG_DOOR_COSTS, struct.pack(">BBBB", *ctx.slot_data["light_gem_door_costs"]))
        if ctx.slot_data["randomize_boss_lair_doors"]:
            dolphin_memory_engine.write_bytes(self.addresses.p_BOSS_COSTS, struct.pack(">BBBB", *ctx.slot_data["boss_lair_costs"]))
        
        b, i, s = ctx.slot_data['gadget_costs']
        dolphin_memory_engine.write_byte(self.addresses.p_BALL_GADGET_COST, b)
        dolphin_memory_engine.write_byte(self.addresses.p_INVINCIBILITY_COST, i)
        dolphin_memory_engine.write_byte(self.addresses.p_SUPERCHARGE_COST, s)

        convert = {"Dragon Kingdom": 0, "Lost Cities": 1, "Icy Wilderness": 2, "Volcanic Isle": 3}
        realm_access = [False, False, False, False]
        for realm in ctx.slot_data['starting_realms']:
            realm_access[convert[realm]] = True

        dolphin_memory_engine.write_byte(self.addresses.p_STARTING_REALM, convert[ctx.slot_data['starting_realms'][0]])
        dolphin_memory_engine.write_bytes(self.addresses.p_REALM_ACCESS, struct.pack(">????", *realm_access))

        if ctx.slot_data['open_world_mode'] > 1 and ctx.slot_data['pause_menu_patch'] == 0:
            # non-full open world with "open shop" pause menu needs to have starting realm depot shops forcibly unlocked
            convert = {0: "Dragon Village - Village Depot", 1: "Coastal Remains - Coastal Depot", 2: "Frostbite Village - Frosty Depot", 3: "Stormy Beach - Stormy Depot"}
            for index, realm in enumerate(realm_access):
                if realm:  # if this is a starting realm
                    shop_name = convert[index]
                    ctx.unlocked_shops.append(shop_name)
                    await ctx._unlock_starting_realm_shop(shop_name)
        
        if ctx.slot_data['easy_bosses']:
            bosses = [False, False, False, False]
            for b in ctx.slot_data['easy_bosses']:
                match b:
                    case 'Gnasty Gnorc':
                        bosses[0] = True
                    case 'Ineptune':
                        bosses[1] = True
                    case 'Red':
                        bosses[2] = True
                    case 'Mecha-Red':
                        bosses[3] = True
            dolphin_memory_engine.write_bytes(self.addresses.p_BOSS_EASY_MODE, struct.pack(">????", *bosses))

        if ctx.slot_data['shop_randomization'] and ctx.slot_data['shop_logic']:
            dolphin_memory_engine.write_byte(self.addresses.p_SHOP_UNLOCK_MODE, 1)
        if ctx.slot_data['teleport_across_realms']:
            dolphin_memory_engine.write_byte(self.addresses.p_TELEPORT_ANYWHERE, 1)
            
        if ctx.slot_data['open_world_mode'] == 1:
            dolphin_memory_engine.write_byte(self.addresses.p_UNLOCK_ALL_SHOPS, 1)
        if ctx.slot_data['open_world_mode'] >= 2:
            dolphin_memory_engine.write_byte(self.addresses.p_DISABLE_MAIN_SHOP_ALWAYS_AVAILABLE, 1)
            if ctx.slot_data['shop_pad_proximity_activation'] == 0:
                dolphin_memory_engine.write_byte(self.addresses.p_DISABLE_SHOP_PAD_PROXIMITY_ACTIVATE, 1)
        
        dolphin_memory_engine.write_byte(self.addresses.p_PATCH_BEEN_WRITTEN_TO, 1)
        
        # set up some goal stuff while here since ctx is available and this is guaranteed to run at the start of save file
        self.goal_list = ctx.slot_data["goal"]
        self.goal_target = len(self.goal_list)
    
    async def _prepare_shop_items(self, ctx: "SpyroAHTContext", *shop_items: NetworkItem):
        dolphin_memory_engine.write_byte(self.addresses.p_RANDOMIZE_SHOP, 1)
        dolphin_memory_engine.write_word(self.addresses.p_XLS_SHOP_ROWCOUNT, len(shop_items)+1)

        for idx, item in enumerate(shop_items):
            player = ctx.player_names[item.player]
            name = ctx.item_names.lookup_in_slot(item.item, item.player)
            game = ctx.slot_info[item.player]
            model = consts.ShopItemModel.Lockpick
            price = ctx.slot_data["shop_costs"][idx]
            if game.game == "Spyro: A Hero's Tail":
                match item.item:
                    case 0xE:
                        model = consts.ShopItemModel.FireBomb
                    case 0x5:
                        model = consts.ShopItemModel.ElectricBomb
                    case 0x6:
                        model = consts.ShopItemModel.WaterBomb
                    case 0x7:
                        model = consts.ShopItemModel.IceBomb
                    case 0xF:
                        model = consts.ShopItemModel.HealthUpgrade
                    case 0x19:
                        model = consts.ShopItemModel.ButterflyJar
                    case 0x1A:
                        model = consts.ShopItemModel.DoubleGems
                    case 0x1B:
                        model = consts.ShopItemModel.Shockwave
                    case 0x22 | 0x23 | 0x24 | 0x25 | 0x26 | 0x27 | 0x28 | 0x29 | 0x2A | 0x2B | 0x2C | 0x2D | 0x2E | 0x2F:
                        model = consts.ShopItemModel.Keychain
            
            remote_price = price if ctx.slot_data["shop_randomization"] else (price * 1.25)
            large_prices = ctx.slot_data["shop_randomization"] == 1 and ctx.slot_data["shop_logic"] == 1  # large prices are only a concern if shop logic is ordered
            name = "???" if ctx.slot_data["hide_shop_item_names"] else name
            i = consts.XLSShoppingItem(model, consts.TextEntry(idx, f"{player}'s {name}"), (price, remote_price), large_prices)
            dolphin_memory_engine.write_bytes(self.addresses.p_XLS_SHOP_ITEMS + (0x20 * (idx + 1)), i.to_bytes('big'))
            dolphin_memory_engine.write_bytes(self.addresses.p_SHOP_TEXT + (0x62 * idx), i.text.to_bytes('big'))

    async def update_tracker(self, ctx: "SpyroAHTContext", locs: list[str]):
        from .. import loc_names_to_ids
        
        for loc in locs:
            loc_id = loc_names_to_ids[loc]
            if loc_id not in consts.LOCATIONS_BITFIELD:
                continue
            
            index = consts.LOCATIONS_BITFIELD[loc_id]
            addr = self.addresses.g_LOCATION_BITFIELD + (index * 2) // 8
            bit = (index * 2) % 8
            data = dolphin_memory_engine.read_byte(addr)
            dolphin_memory_engine.write_byte(addr, data | (0b10 << bit))
        return loc_names_to_ids

    async def update_pause_gems(self, ctx: "SpyroAHTContext", events: list[str]):
        if not ctx.slot_data["shop_randomization"]:
            return
        if ctx.slot_data["shop_randomization"] and not ctx.slot_data["shop_logic"]:
            return
        
        blink_available, non_blink_enemies_available, other_available = 0, 0, 0
        for event in events:
            if "VictoryCon" in event:
                continue
            gem_amount = int(event.split(" ", 1)[0])
            if "Blink minigames" in event:
                blink_available += gem_amount
            elif "[enemy]" in event:
                non_blink_enemies_available += gem_amount
            else:
                other_available += gem_amount
        
        blink_in_logic = (blink_available * ctx.slot_data['blink_gems'] / 100)
        non_blink_enemy_in_logic = (non_blink_enemies_available * ctx.slot_data['non_blink_enemies'] / 100)
        other_in_logic = (other_available * ctx.slot_data['other_gems'] / 100)
        
        dolphin_memory_engine.write_word(self.addresses.g_GEMS_IN_LOGIC, int(blink_in_logic + non_blink_enemy_in_logic + other_in_logic))
        dolphin_memory_engine.write_word(self.addresses.g_GEMS_AVAILABLE, int(blink_available + non_blink_enemies_available + other_available))
    
    async def allow_realm_access(self, id: int):
        current: list[bool] = list(struct.unpack(">????", dolphin_memory_engine.read_bytes(self.addresses.g_REALM_ACCESS, 4)))
        current[id - 0x30] = True
        dolphin_memory_engine.write_bytes(self.addresses.g_REALM_ACCESS, struct.pack(">????", *current))
    
    async def toggle_double_gems(self, to: bool):
        dolphin_memory_engine.write_byte(self.addresses.g_INFINITE_DOUBLE_GEM, 1 if to else 0)
