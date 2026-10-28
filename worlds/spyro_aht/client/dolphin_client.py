from __future__ import annotations

import asyncio
import random
import struct
from typing import TYPE_CHECKING

import dolphin_memory_engine

from NetUtils import NetworkItem
from . import addresses
from .. import consts

if TYPE_CHECKING:
    from .context import SpyroAHTContext

class DolphinClient:
    def retrieve_mod_version(self) -> tuple[int, int]:
        mod_version_full = dolphin_memory_engine.read_word(self.addresses.AP_VERSION_MAJOR)
        mod_version_major = mod_version_full >> 16
        mod_version_minor = mod_version_full & 0xFFFF
        if mod_version_major == 0:  # old mod versions reported only a single version in the space the minor version currently uses now. Need adjusting to match new format
            return mod_version_minor, 0
        else:
            return mod_version_major, mod_version_minor
        
    def __init__(self, ctx: SpyroAHTContext, logger) -> None:
        super().__init__()
        self.logger = logger
        self.ctx: SpyroAHTContext = ctx
        self._notification_task = asyncio.create_task(self.notification_task())
        self._trap_task = asyncio.create_task(self.trap_task())
        self.ready = asyncio.Event()
        self.msg_queue = asyncio.Queue()
        self.trap_queue = asyncio.Queue()
        self.trap_timer = ctx.slot_data['trap_length']
        self.addresses = None  # type: ignore
        
    async def notification_task(self):
        try:
            await self.ready.wait()
            while True:
                await asyncio.sleep(0.5)
                if await self.should_process_checks():
                    await asyncio.sleep(5)
                    dolphin_memory_engine.write_word(self.addresses.n_TIMER, 0)
                    col, msg = await self.msg_queue.get()

                    if len(msg) > 254:
                        msg = msg[:254]
                    
                    color = struct.pack(">BBBB", *col)
                    dolphin_memory_engine.write_bytes(self.addresses.n_COLOR, color)
                    dolphin_memory_engine.write_bytes(self.addresses.n_TEXT_BUFFER, (msg + "\0").encode("utf_16_be"))
                    dolphin_memory_engine.write_word(self.addresses.n_TIMER, 5*60)
        except Exception:
            self.logger.info("WARNING: Error in notification queue, please report to developers.", exc_info=True)
    
    async def trap_task(self):
        try:
            await self.ready.wait()
            while True:
                await asyncio.sleep(0.5)
                if await self.should_process_checks():
                    await asyncio.sleep(5)
                    name = await self.trap_queue.get()
                    
                    dolphin_memory_engine.write_word(self.addresses.g_TRAP_DATA, 60*self.trap_timer)
                    if name == "Spam Call": dolphin_memory_engine.write_byte(self.addresses.g_TRAP, 1)
                    elif name == "Reverse Controls": dolphin_memory_engine.write_byte(self.addresses.g_TRAP, 2)
                    elif name == "Bounce": dolphin_memory_engine.write_byte(self.addresses.g_TRAP, 3)
                    await asyncio.sleep(self.trap_timer - 5)
        except Exception:
            self.logger.info("WARNING: Error in trap queue, please report to developers", exc_info=True)

    async def connect(self):
        if not dolphin_memory_engine.is_hooked():
            dolphin_memory_engine.hook()
            game_id = dolphin_memory_engine.read_bytes(0x80000000, 6).decode()

            if game_id == consts.GAME_ID_NTSC:
                self.logger.info(f"INFO: Spyro: A Hero's Tail Archipelago (AHT AP) client version {consts.CLIENT_VERSION_STR} initializing. NTSC game detected.")
                self.addresses = addresses.G5SE7D()
            elif game_id == consts.GAME_ID_PAL:
                self.logger.info(f"INFO: Spyro: A Hero's Tail Archipelago (AHT AP) client version {consts.CLIENT_VERSION_STR} initializing. PAL game detected.")
                self.addresses = addresses.G5SP7D()
            else:
                self.logger.info(f"WARNING: Game ID {game_id} is invalid or unsupported.")
                return False

            mod_version_major, mod_version_minor = self.retrieve_mod_version()
            mod_version_str = f"{mod_version_major}.{mod_version_minor}"
            
            if mod_version_major != consts.MOD_MAJOR:
                self.logger.info(f"WARNING: Mod version {mod_version_major} is incompatible with AHT AP version {consts.CLIENT_VERSION_STR}. Please update game mod to version {consts.MOD_MAJOR}.")
                return False
            if mod_version_major == consts.MOD_MAJOR and mod_version_minor < consts.MOD_MINOR:
                self.logger.info(f"INFO: Mod version {mod_version_str} is compatible with AHT AP version {consts.CLIENT_VERSION_STR}, but there is a newer minor version available which may contain new features or bugfixes. Update at your leisure.")
            else:
                self.logger.info(f"INFO: Game mod version {mod_version_str} and AHT AP {consts.CLIENT_VERSION_STR} are compatible. Enjoy!")
        else:
            self.logger.info("WARNING: Dolphin memory engine was already hooked. This may cause issues!")
        self.ready.set()
    
    async def disconnect(self):
        self._notification_task.cancel()
        self._trap_task.cancel()
        if dolphin_memory_engine.is_hooked():
            dolphin_memory_engine.write_byte(self.addresses.p_PATCH_BEEN_WRITTEN_TO, 0)
            dolphin_memory_engine.un_hook()
            self.ready.clear()
    
    async def should_process_checks(self) -> bool:
        if dolphin_memory_engine.is_hooked():
            m_state = dolphin_memory_engine.read_word(self.addresses.IN_GAME)
            m_pause = dolphin_memory_engine.read_byte(self.addresses.PAUSE)
            return m_state == 3 and (m_pause & 0x80 == 0)
        else: return False

    async def scan_locations(self, slot_data: dict) -> set[int]:
        result: set[int] = set()
        for loc_id, offset in consts.LOCATIONS_BITFIELD.items():
            await asyncio.sleep(0)

            data = dolphin_memory_engine.read_byte(self.addresses.g_LOCATION_BITFIELD_COLLECTED + (offset // 8))
            checked = data & 1 << (offset % 8)
            if checked:
                match loc_id:
                    case 701:  # breath from gnasty -> add defeated gnasty
                        result.update({701, 702})
                    case 703:  # breath from ineptune -> add defeated ineptune
                        result.update({703, 704})
                    case 705:  # breath from red -> add defeated red
                        result.update({705, 706})
                    case _:
                        result.add(loc_id)
        
        if slot_data["shop_randomization"]:
            for i in range(slot_data["shop_item_count"]):
                await asyncio.sleep(0)
                purchase_flag = dolphin_memory_engine.read_byte(self.addresses.g_SHOP_TEXT + (0x62 * i))
                if purchase_flag:
                    result.add(901 + i)
        return result

    async def set_flag(self, address: int, flag: int, to: bool):
        flags = dolphin_memory_engine.read_word(address)
        if to: flags |= flag
        else: flags &= ~flag
        dolphin_memory_engine.write_word(address, int(flags))
    
    async def get_flag(self, address: int, flag: int) -> bool:
        return dolphin_memory_engine.read_word(address) & flag != 0

    async def get_objective(self, objective: int) -> bool:
        index = (objective & 0xFFFF) - 1
        uint = index // 32
        bit = index % 32
        if await self.get_flag(self.addresses.OBJECTIVES + (uint * 4), 1 << bit):
            return True
        else:
            return False
    
    async def debug_add_item(self, amount: int, address: int, bytes: int) -> bool:
        current_amount = int.from_bytes(dolphin_memory_engine.read_bytes(address, bytes))
        dolphin_memory_engine.write_bytes(address, (current_amount + amount).to_bytes(bytes, 'big'))
        return True
    
    async def has_any_breath(self) -> bool:
        b = dolphin_memory_engine.read_word(self.addresses.ABILITY_FLAGS)
        return b & (0x800e0) != 0

    async def set_breath(self, breath_id: int):
        convert = {consts.ITEM_INFO["Fire Breath"][0]: consts.BREATH_FIRE, consts.ITEM_INFO["Electric Breath"][0]: consts.BREATH_ELECTRIC,
                   consts.ITEM_INFO["Water Breath"][0]: consts.BREATH_WATER, consts.ITEM_INFO["Ice Breath"][0]: consts.BREATH_ICE}
        dolphin_memory_engine.write_word(self.addresses.ACTIVE_BREATH, convert[breath_id])
    
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
        if double: value *= 2
        count = dolphin_memory_engine.read_word(self.addresses.GEMS)
        dolphin_memory_engine.write_word(self.addresses.GEMS, count + value)
    
    async def gem_tax(self):
        value = random.randint(500, 1000)
        count = dolphin_memory_engine.read_word(self.addresses.GEMS)
        if (count - value) < 0: value = count
        dolphin_memory_engine.write_word(self.addresses.GEMS, count - value)
    
    async def damage_sparx(self):
        health = dolphin_memory_engine.read_word(self.addresses.HEALTH)
        decrease = 32
        if health == 64 and len([item for item in self.ctx.items_received if item.item == 0xF]) == 0: return # if no red Sparx
        if health - decrease <= 0: return # don't kill player
        dolphin_memory_engine.write_word(self.addresses.HEALTH, health - decrease)
    
    async def import_deathlink(self, mode: int):
        dolphin_memory_engine.write_byte(self.addresses.g_DEATHLINK_INGOING, mode)

    async def export_deathlink(self) -> bool:
        b = dolphin_memory_engine.read_byte(self.addresses.g_DEATHLINK_OUTGOING)
        if b:
            dolphin_memory_engine.write_byte(self.addresses.g_DEATHLINK_OUTGOING, 0)
            return b
        return False

    async def apply_patch(self):
        if self.ctx.slot_data["time_savers"]["Skip Cutscenes"] == "on":
            dolphin_memory_engine.write_byte(self.addresses.p_SKIP_CUTSCENE_BUTTON, 1)
        if self.ctx.slot_data["time_savers"]["Skip Elevators"] == "on":
            dolphin_memory_engine.write_byte(self.addresses.p_INSTANT_ELEVATORS, 1)
        
        convert_config = {"enabled": 0, "easy": 1, "disabled": 2}
        dolphin_memory_engine.write_byte(self.addresses.p_MINIGAME_BLINK_CONFIG, convert_config[self.ctx.slot_data['minigame_checks']['Blink']])
        dolphin_memory_engine.write_byte(self.addresses.p_MINIGAME_SGTBYRD_CONFIG, convert_config[self.ctx.slot_data['minigame_checks']['Sgt. Byrd']])
        dolphin_memory_engine.write_byte(self.addresses.p_MINIGAME_SPARX_CONFIG, convert_config[self.ctx.slot_data['minigame_checks']['Sparx']])
        dolphin_memory_engine.write_byte(self.addresses.p_MINIGAME_TURRET_CONFIG, convert_config[self.ctx.slot_data['minigame_checks']['Turret']])
            
        dolphin_memory_engine.write_byte(self.addresses.p_DISABLE_POPUPS, 1)
        dolphin_memory_engine.write_word(self.addresses.p_MW_SEED, (int(self.ctx._seed) & 0xffffffff))
        if self.ctx.slot_data['chest_keys'] >= 1:  # 1 = level key rings, 2 = realm key rings
            dolphin_memory_engine.write_byte(self.addresses.p_USE_KEY_RINGS, 1)
        dolphin_memory_engine.write_byte(self.addresses.p_FIREWORKS_ARE_RANDOMIZED, self.ctx.slot_data['firework_checks'])
        dolphin_memory_engine.write_byte(self.addresses.p_UT_ENABLED, int(self.ctx.tracker_found))
        if self.ctx.slot_data['death_link']:
            dolphin_memory_engine.write_byte(self.addresses.p_DEATHLINK_DEATHS_BEFORE_SEND, self.ctx.slot_data['death_link_amnesty'])

        if self.ctx.slot_data['pause_menu_patch'] == 0:
            dolphin_memory_engine.write_byte(self.addresses.p_INSTANT_TELEPORT_MODE, 2)
        elif self.ctx.slot_data['pause_menu_patch'] == 1:
            dolphin_memory_engine.write_byte(self.addresses.p_INSTANT_TELEPORT_MODE, 1)
        
        if self.ctx.slot_data['shop_randomization']:
            locations = consts.SHOP_ITEM_IDS[:self.ctx.slot_data["shop_item_count"]]
            dolphin_memory_engine.write_byte(self.addresses.p_DISPLAY_GEM_STATS, 1)
            if self.ctx.slot_data['shop_logic']:
                dolphin_memory_engine.write_byte(self.addresses.p_SHOP_UNLOCK_MODE, 1)
            await self.ctx.send_msgs([{"cmd": "LocationScouts", "locations": locations, "create_as_hint": 0}])
            await self.ctx._shop_items_received.wait()
            await self._prepare_shop_items(*self.ctx._shop_items)
        
        if self.ctx.slot_data["randomize_light_gem_door_costs"]:
            dolphin_memory_engine.write_bytes(self.addresses.p_LG_DOOR_COSTS, struct.pack(">BBBB", *self.ctx.slot_data["light_gem_door_costs"]))
        if self.ctx.slot_data["randomize_boss_lair_door_costs"]:
            dolphin_memory_engine.write_bytes(self.addresses.p_BOSS_COSTS, struct.pack(">BBBB", *self.ctx.slot_data["boss_lair_costs"]))
        
        b, i, s = self.ctx.slot_data['gadget_costs']
        dolphin_memory_engine.write_byte(self.addresses.p_BALL_GADGET_COST, b)
        dolphin_memory_engine.write_byte(self.addresses.p_INVINCIBILITY_COST, i)
        dolphin_memory_engine.write_byte(self.addresses.p_SUPERCHARGE_COST, s)

        convert_realm = {"Dragon Kingdom": 0, "Lost Cities": 1, "Icy Wilderness": 2, "Volcanic Isle": 3}
        realm_access = [False, False, False, False]
        for realm in self.ctx.slot_data['starting_realms']:
            realm_access[convert_realm[realm]] = True

        dolphin_memory_engine.write_byte(self.addresses.p_STARTING_REALM, convert_realm[self.ctx.slot_data['starting_realms'][0]])
        dolphin_memory_engine.write_bytes(self.addresses.p_REALM_ACCESS, struct.pack(">????", *realm_access))

        if self.ctx.slot_data['open_world_mode'] > 1 and self.ctx.slot_data['pause_menu_patch'] == 0:
            # non-full open world with "open shop" pause menu needs to have starting realm depot shops forcibly unlocked
            convert_open_world = {0: "Dragon Village - Village Depot", 1: "Coastal Remains - Coastal Depot", 2: "Frostbite Village - Frosty Depot", 3: "Stormy Beach - Stormy Depot"}
            for index, realm in enumerate(realm_access):
                if realm:  # if this is a starting realm
                    shop_name = convert_open_world[index]
                    self.ctx.unlocked_shops.append(shop_name)
                    await self.ctx._unlock_starting_realm_shop(shop_name)
        
        if self.ctx.slot_data['easy_bosses']:
            bosses = [False, False, False, False]
            for b in self.ctx.slot_data['easy_bosses']:
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
            
        if self.ctx.slot_data['time_savers']["Teleport Across Realms"] == "on":
            dolphin_memory_engine.write_byte(self.addresses.p_TELEPORT_ANYWHERE, 1)
            
        if self.ctx.slot_data['open_world_mode'] == 1:
            dolphin_memory_engine.write_byte(self.addresses.p_UNLOCK_ALL_SHOPS, 1)
        if self.ctx.slot_data['open_world_mode'] >= 2:
            dolphin_memory_engine.write_byte(self.addresses.p_DISABLE_MAIN_SHOP_ALWAYS_AVAILABLE, 1)
            if self.ctx.slot_data['shop_pad_proximity_activation'] == 0:
                dolphin_memory_engine.write_byte(self.addresses.p_DISABLE_SHOP_PAD_PROXIMITY_ACTIVATE, 1)
        
        dolphin_memory_engine.write_byte(self.addresses.p_PATCH_BEEN_WRITTEN_TO, 1)
        
    async def _prepare_shop_items(self, *shop_items: NetworkItem):
        dolphin_memory_engine.write_byte(self.addresses.p_RANDOMIZE_SHOP, 1)
        dolphin_memory_engine.write_word(self.addresses.p_XLS_SHOP_ROWCOUNT, len(shop_items)+1)

        for item_num, item in enumerate(shop_items):
            player = self.ctx.player_names[item.player]
            name = self.ctx.item_names.lookup_in_slot(item.item, item.player)
            game = self.ctx.slot_info[item.player]
            model = consts.ShopItemModel.Lockpick
            price = self.ctx.slot_data["shop_costs"][item_num]
            if game.game == "Spyro: A Hero's Tail":
                if item.item == consts.ITEM_INFO["Fire Breath"][0] or item.item == consts.ITEM_INFO["Fire Bomb"][0]:
                    model = consts.ShopItemModel.FireBomb
                elif item.item == consts.ITEM_INFO["Electric Breath"][0] or item.item == consts.ITEM_INFO["Electric Bomb"][0]:
                    model = consts.ShopItemModel.ElectricBomb
                elif item.item == consts.ITEM_INFO["Water Breath"][0] or item.item == consts.ITEM_INFO["Water Bomb"][0]:
                    model = consts.ShopItemModel.WaterBomb
                elif item.item == consts.ITEM_INFO["Ice Breath"][0] or item.item == consts.ITEM_INFO["Ice Bomb"][0]:
                    model = consts.ShopItemModel.IceBomb
                elif item.item == consts.ITEM_INFO["Health Unit+"][0]:
                    model = consts.ShopItemModel.HealthUpgrade
                elif item.item == consts.ITEM_INFO["Butterfly Jar"][0]:
                    model = consts.ShopItemModel.ButterflyJar
                elif item.item == consts.ITEM_INFO["Double Gems"][0]:
                    model = consts.ShopItemModel.DoubleGems
                elif item.item == consts.ITEM_INFO["Shockwave"][0]:
                    model = consts.ShopItemModel.Shockwave
                elif consts.ITEM_GROUP_IDS["Key Rings"][0] <= item.item <= consts.ITEM_GROUP_IDS["Key Rings"][1]:
                    model = consts.ShopItemModel.Keychain
            
            remote_price = price if self.ctx.slot_data["shop_randomization"] else (price * 1.25)
            large_prices = self.ctx.slot_data["shop_randomization"] == 1 and self.ctx.slot_data["shop_logic"] == 1  # large prices are only a concern if shop logic is ordered
            
            if "Player" in self.ctx.slot_data["disguise_shop_items"]: player = "???"
            if "Item" in self.ctx.slot_data["disguise_shop_items"]: name = "???"
            if "Model" in self.ctx.slot_data["disguise_shop_items"]: model = consts.ShopItemModel.Lockpick
            bought = consts.SHOP_ITEM_IDS[0] + item_num in self.ctx.checked_locations
            
            i = consts.XLSShoppingItem(model, consts.TextEntry(item_num, f"{player}'s {name}", bought), (price, remote_price), large_prices)
            dolphin_memory_engine.write_bytes(self.addresses.p_XLS_SHOP_ITEMS + (0x20 * (item_num + 1)), i.to_bytes('big'))
            dolphin_memory_engine.write_bytes(self.addresses.p_SHOP_TEXT + (0x62 * item_num), i.text.to_bytes('big'))

    async def update_tracker(self, in_logic_ids_to_names: dict[str, str], in_glitched_ids_to_names: dict[str, str]):
        # server_locations is list of all location ids for this slot, regardless of check status. combination of checked_locations and missing_locations
        for loc_id in self.ctx.server_locations:
            # exclusions: skip if no icon or if unchecked + unreachable
            if loc_id not in consts.LOCATIONS_BITFIELD: continue
            if loc_id not in self.ctx.checked_locations and in_logic_ids_to_names[str(loc_id)] == "" and in_glitched_ids_to_names[str(loc_id)] == "": continue
            
            # otherwise, update the icon accordingly to be checked, reachable, or glitched-reachable
            if in_logic_ids_to_names[str(loc_id)] != "":
                await self.write_icon(self.addresses.g_LOCATION_BITFIELD_REACHABLE, consts.LOCATIONS_BITFIELD[loc_id])
            elif in_glitched_ids_to_names[str(loc_id)] != "":
                await self.write_icon(self.addresses.g_LOCATION_BITFIELD_REACHABLE_TRICK, consts.LOCATIONS_BITFIELD[loc_id])
            elif loc_id in self.ctx.checked_locations:
                await self.write_icon(self.addresses.g_LOCATION_BITFIELD_COLLECTED, consts.LOCATIONS_BITFIELD[loc_id])
            
    async def write_icon(self, bitfield: int, bit: int):
        """Updates a map icon, given a bitfield address and index."""
        data = dolphin_memory_engine.read_byte(bitfield + (bit // 8))
        flag = 1 << (bit % 8)
        dolphin_memory_engine.write_byte(bitfield + (bit // 8), data | flag)

    async def update_pause_gems(self, events: list[str]):
        if not self.ctx.slot_data["shop_randomization"]:
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
        
        blink_in_logic = (blink_available * self.ctx.slot_data['blink_gems'] / 100)
        non_blink_enemy_in_logic = (non_blink_enemies_available * self.ctx.slot_data['non_blink_enemies'] / 100)
        other_in_logic = (other_available * self.ctx.slot_data['other_gems'] / 100)
        
        dolphin_memory_engine.write_word(self.addresses.g_TOTAL_GEMS_IN_LOGIC, int(blink_in_logic + non_blink_enemy_in_logic + other_in_logic))
        dolphin_memory_engine.write_word(self.addresses.g_TOTAL_GEMS_AVAILABLE, int(blink_available + non_blink_enemies_available + other_available))
    
    async def allow_realm_access(self, id: int):
        current: list[bool] = list(struct.unpack(">????", dolphin_memory_engine.read_bytes(self.addresses.g_REALM_ACCESS, 4)))
        current[id] = True
        dolphin_memory_engine.write_bytes(self.addresses.g_REALM_ACCESS, struct.pack(">????", *current))
    
    async def toggle_double_gems(self, to: bool):
        dolphin_memory_engine.write_byte(self.addresses.g_INFINITE_DOUBLE_GEM, 1 if to else 0)
