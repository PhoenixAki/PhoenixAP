from __future__ import annotations

import asyncio
import collections

import Utils
from CommonClient import ClientCommandProcessor, logger
from kvui import GameManager

tracker_loaded = False
try:
    from worlds.tracker.TrackerClient import TrackerGameContext as SuperContext
    tracker_loaded = True
except ModuleNotFoundError:
    from CommonClient import CommonContext as SuperContext

from NetUtils import ClientStatus, NetworkItem

from .client import GenericClient, DolphinClient
from .data import consts


class SpyroAHTCommands(ClientCommandProcessor):
    ctx: SpyroAHTContext
    
    async def _cmd_reset_client(self) -> bool:
        """Forcibly reconnect the client."""
        self.output("Resetting client...")
        if self.ctx.emu_client:
            self.ctx.emu_loop.cancel()
            await self.ctx.emu_client.disconnect()
        self.ctx.emu_loop = asyncio.create_task(self.ctx._emu_loop())
        return True
    
    async def _cmd_add_item(self, item, amount) -> bool:
        """Format: /add_item item_name amount.
        Adds <amount> of <item_name> to the game's memory directly.
        Currently supported items: "dark_gem", "light_gem", "gems", and "lockpick".
        Please use responsibly - minimal error checking is done. High values risk crashing the game.
        Intended for use in recovering save files, as well as testing and debugging."""
        if len(self.ctx.slot_data) == 0:
            self.output("Connect to a slot before using commands.")
            return True
        
        types = {
            "dark_gem": [self.ctx.emu_client.addresses.DARK_GEM_COUNT, 1],
            "light_gem": [self.ctx.emu_client.addresses.LIGHT_GEM_COUNT, 1],
            "gems": [self.ctx.emu_client.addresses.GEMS, 4],
            "lockpick": [self.ctx.emu_client.addresses.LOCKPICKS, 1]
        }
        
        if item not in types.keys():
            self.output("Incorrect command format. Please use one of the supported item types.")
            return True

        amount = int(amount)
        if amount < 0:
            self.output("This command can only add items. Please enter a positive amount.")
            return True
        
        await self.ctx.emu_client.debug_add_item(amount, *types[item])
        return True

    async def _cmd_list_options(self) -> bool:
        # this is grossly repetitive, but it only runs when the player demands it so it's not a big deal
        # even if it was reformatted it'd still be the same amount of output and data lookup, it's just code cleanliness
        """Displays seed information, retrieved directly from data sent from Archipelago.
        Some of this info is also viewable on the pause menu."""
        from . import options
        
        if len(self.ctx.slot_data) == 0:
            self.output("Connect to a slot before using commands.")
            return True
        
        self.output("---------------DEATHLINK---------------")
        # death link
        convert = {0: "disabled", 1: "enabled (shielded)", 2: "enabled"}
        self.output(f"DeathLink is set to {convert[self.ctx.slot_data['death_link']]}.")
        # amnesty
        if self.ctx.slot_data["death_link"] != 0:
            self.output(f"You chose to have DeathLink deaths be sent out every {self.ctx.slot_data['death_link_amnesty']} AHT death(s).")
        
        self.output("---------------GENERATION SETTINGS---------------")
        # logging level
        convert = {1: "none", 2: "low", 3: "medium", 4: "high", 5: "maximum"}
        self.output(f"You set your logging level to {convert[self.ctx.slot_data['logging_level']]}.")
        # auto corrections
        convert = {0: "halt", 1: "chaos", 2: "fix_minor", 3: "fix_major"}
        self.output(f"auto_corrections is set to {convert[self.ctx.slot_data['auto_corrections']]}.")
        
        self.output("---------------GOAL---------------")
        # 4 boss goals
        enabled = []
        for goal in ["Gnasty Gnorc", "Ineptune", "Red", "Mecha-Red"]:
            if goal in self.ctx.slot_data["goals_dict"].keys(): enabled.append(goal)
        output = "none" if len(enabled) == 0 else f"{", ".join(enabled)}"
        self.output(f"Enabled Boss Goals: {output}.")
        # 6 collectible goals
        enabled = []
        for goal in ["Dark Gems", "Light Gems", "Dragon Eggs", "Fireworks", "Shop Items", "Locked Chests"]:
            chests = ""
            if goal in self.ctx.slot_data["goals_dict"].keys():
                amount = self.ctx.slot_data["goals_dict"][goal]["amount"]
                
                if goal == "Light Gems" and self.ctx.slot_data["exclude_chest_items"] >= 2:
                    chests = " excluding chests"
                elif goal == "Light Gems" and self.ctx.slot_data["exclude_chest_items"] < 2:
                    chests = " including chests"
                elif goal == "Dragon Eggs" and self.ctx.slot_data["exclude_chest_items"] in [1, 3]:
                    chests = " excluding chests"
                elif goal == "Dragon Eggs" and self.ctx.slot_data["exclude_chest_items"] not in [1, 3]:
                    chests = " including chests"
                    
                enabled.append(f"{goal} ({amount} required{chests})")
        output = "none" if len(enabled) == 0 else f"{", ".join(enabled)}"
        self.output(f"Enabled Collectible Goals: {output}.")
        # elder goals
        enabled = []
        for goal in ["Elder Tomas", "Elder Magnus", "Elder Titan", "Elder Astor"]:
            if goal in self.ctx.slot_data["goals_dict"].keys(): enabled.append(goal)
        output = "none" if len(enabled) == 0 else f"{", ".join(enabled)}"
        self.output(f"Enabled Elder Goals: {output}.")
        # minigame goals
        enabled = []
        for goal in ["Sgt. Byrd", "Blink", "Turret", "Sparx"]:
            if goal in self.ctx.slot_data["goals_dict"].keys():
                amount = self.ctx.slot_data["minigames_goal"][goal]
                enabled.append(f"{goal} ({amount} required)")
        output = "none" if len(enabled) == 0 else f"{", ".join(enabled)}"
        self.output(f"Enabled Minigame Goals: {output}.")

        self.output("---------------CHECKS & ITEMS---------------")
        # open world mode
        convert = {0: "vanilla", 1: "full", 2: "randomized", 3: "progressive levels", 4: "reverse progressive levels", 5: "full levels", 6: "full realms"}
        self.output(f"You chose to set open world mode to {convert[self.ctx.slot_data['open_world_mode']]}.")
        # firework checks
        output = "enabled" if self.ctx.slot_data["firework_checks"] else "disabled"
        self.output(f"Firework checks are {output}.")
        # minigame checks
        output = ""
        for minigame_type in ["Blink", "Sgt. Byrd", "Sparx", "Turret"]:
            output += f"{minigame_type} is set to {self.ctx.slot_data['minigame_checks'][minigame_type]}, "
        self.output(f"Minigame Checks: {output[:-2]}.")
        # item bundles
        output = ""
        for bundle_type in ["Dark Gem", "Light Gem", "Lockpick"]:
            if bundle_type == "Lockpick" and not self.ctx.slot_data['shop_randomization']:
                continue
            output += f"{bundle_type} bundle size of {self.ctx.slot_data['item_bundles'][bundle_type]}, "
        self.output(f"Item Bundling: {output[:-2]}.")
        # filler
        output = ""
        for key in options.FillerItems.valid_keys:
            if key in self.ctx.slot_data["filler_items"]:
                output += key + ", "
        if output == "":
            output = "none, "
        self.output(f"Enabled Filler Items: {output[:-2]}.")
        # traps
        output = ""
        for key in options.TrapItems.valid_keys:
            if key in self.ctx.slot_data["trap_items"]:
                output += key + ", "
        if output == "":
            output = "none, "
        self.output(f"Enabled Trap Items: {output[:-2]}.")
        
        self.output("---------------START OF GAME---------------")
        # movement randomization
        output = ""
        for movement in ["Glide", "Swim", "Charge"]:
            if movement in self.ctx.slot_data["movement_randomization"]:
                output += f"{movement} randomized, "
            else:
                output += f"{movement} not randomized, "
        self.output(f"Movement randomization: you chose to have {output[:-2]}.")
        # starting breath(s)
        output = ""
        for breath in ["Fire Breath", "Electric Breath", "Water Breath", "Ice Breath"]:
            if breath in self.ctx.slot_data["starting_breaths"]:
                output += f"{breath}, "
        if output == "":
            output += "no, "
        self.output(f"You chose to start with {output[:-2]} breath(s).")
        # starting realm(s)
        self.output(f"You chose to start with access to the following realm(s): {self.ctx.slot_data['starting_realms']}.")

        self.output("---------------SHOP SETTINGS---------------")
        # shop items & key rings
        output = "randomized" if self.ctx.slot_data["shop_randomization"] == 1 else "not randomized"
        convert = {0: "lockpicks", 1: "per-level key rings", 2: "per-realm key rings"}
        self.output(f"Shop items are {output} and you chose to unlock chests using {convert[self.ctx.slot_data['chest_keys']]}.")
        if self.ctx.slot_data["shop_randomization"]:
            # shop item count
            self.output(f"You chose to have {self.ctx.slot_data['shop_item_count']} shop items.")
            # shop logic
            output = "ordered" if self.ctx.slot_data["shop_logic"] == 1 else "unordered"
            self.output(f"The shop logic system is set to {output}.")
            # gem collection options
            self.output(f"You chose to collect {self.ctx.slot_data['blink_gems']}% of Blink's gems, {self.ctx.slot_data['non_blink_enemies']}% of non-Blink enemy gems, and {self.ctx.slot_data['other_gems']}% of other gems.")
            # shop prices
            self.output(f"This means your shop prices are {self.ctx.slot_data['shop_costs']}.")
            # double gems
            output = "enable" if self.ctx.slot_data['double_gems'] else "disable"
            self.output(f"You chose to {output} the Double Gems item.")
            
        self.output("---------------GATE AND GADGET COSTS---------------")
        # boss costs
        data = self.ctx.slot_data["boss_lair_costs"]
        self.output(f"The boss lair gates require, in vanilla realm order: {data[0]}, {data[1]}, {data[2]}, and {data[3]} Dark Gems.")
        # boss lair forcing
        data = self.ctx.slot_data["boss_lair_forcing"]
        convert = {0: "none of the bosses", 1: "Gnasty Gnorc", 2: "Ineptune", 3: "Red", 4: "Mecha-Red", 5: "all goal bosses"}
        self.output(f"You chose to force {convert[data]} to have the highest boss lair cost(s).")
        # light gem doors
        data = self.ctx.slot_data["light_gem_door_costs"]
        self.output(f"The Light Gem doors require, in vanilla realm order: {data[0]}, {data[1]}, {data[2]}, and {data[3]} Light Gems.")
        # gadget costs
        data = self.ctx.slot_data["gadget_costs"]
        self.output(f"Gadget Costs: Ball requires {data[0]} Light Gems, invincibility requires {data[1]} Light Gems, and supercharge requires {data[2]} Light Gems.")

        self.output("---------------QUALITY OF LIFE---------------")
        # pause menu patch
        output = "open shop" if self.ctx.slot_data["pause_menu_patch"] == 0 else "teleport to hub"
        self.output(f"You set your pause menu patch to {output}.")
        # shop pad proximity activation
        if self.ctx.slot_data["open_world_mode"] >= 2:
            output = "re-enable" if self.ctx.slot_data["shop_pad_proximity_activation"] else "disable"
            self.output(f"You chose to {output} shop pad proximity activation.")
        # auto-hinting
        output = ""
        for key in options.AutoHinting.valid_keys:
            output_2 = "on" if key in self.ctx.slot_data["auto_hinting"][key] else "off"
            output += f"{key} is {output_2}, "
        self.output(f"Auto Hinting: {output[:-2]}.")
        # disguise shop items
        if self.ctx.slot_data["shop_randomization"] == 1:
            output = ""
            for key in options.DisguiseShopItems.valid_keys:
                output_2 = "hidden" if key in self.ctx.slot_data["disguise_shop_items"] else "unhidden"
                output += f"{key}s are {output_2}, "
            self.output(f"Randomized shop item disguising: {output[:-2]}.")
        # easy bosses
        output = "Boss Difficulty: "
        for boss in ["Gnasty Gnorc", "Ineptune", "Red", "Mecha-Red"]:
            output += f"{boss} easy, " if boss in self.ctx.slot_data["easy_bosses"] else f"{boss} normal, "
        self.output(f"{output[:-2]}.")
        # time savers
        output = ""
        for key in options.TimeSavers.valid_keys:
            output_2 = "on" if key in self.ctx.slot_data["time_savers"][key] else "off"
            output += f"{key} is {output_2}, "
        self.output(f"time_saver game patches: {output[:-2]}.")

        return True

    async def _cmd_check_goal(self) -> bool:
        """Details completion progress on all enabled goals, including how many checks are left to do for each."""
        if len(self.ctx.slot_data) == 0:
            self.output("Command cannot be ran before entering your save file.")
            return True
        
        completed_goals, incomplete_goals = [], []
        for goal in self.ctx.slot_data["goals_dict"].keys():
            # retrieve data from goals dict
            id_list = self.ctx.slot_data["goals_dict"][goal]["ids"]
            amount = self.ctx.slot_data["goals_dict"][goal]["amount"]
            # tally it up
            count = 0
            for goal_id in id_list:
                count += goal_id in self.ctx.checked_locations  # += 1 if true, otherwise 0
            # check for completed status
            if count >= amount: completed_goals.append(goal)
            else: incomplete_goals.append(f"{goal} ({amount-count} checks left)")
        # output while being cautious of empty lists
        complete_text = "none" if len(completed_goals) == 0 else f"{", ".join(completed_goals)}"
        incomplete_text = "none" if len(incomplete_goals) == 0 else f"{", ".join(incomplete_goals)}"
        self.output(f"Completed Goals: {complete_text}.")
        self.output(f"Incomplete Goals: {incomplete_text}.")
        return True

    async def _cmd_costs(self) -> bool:
        """Displays the cost of each boss lair, light gem door, and gadget.
        This information is also listed in /list_options.
        /costs is offered as a convenience in case costs are the only information you want."""
        if len(self.ctx.slot_data) == 0:
            self.output("Connect to a slot before using commands.")
            return True
        
        # boss costs
        data = self.ctx.slot_data["boss_lair_costs"]
        self.output(f"The boss lair gates require, in vanilla realm order: {data[0]}, {data[1]}, {data[2]}, and {data[3]} Dark Gems.")
        # light gem doors
        data = self.ctx.slot_data["light_gem_door_costs"]
        self.output(f"The Light Gem doors require, in vanilla realm order: {data[0]}, {data[1]}, {data[2]}, and {data[3]} Light Gems.")
        # gadget costs
        data = self.ctx.slot_data["gadget_costs"]
        self.output(f"Gadget Costs: Ball requires {data[0]} Light Gems, invincibility requires {data[1]} Light Gems, and supercharge requires {data[2]} Light Gems.")
        return True
    
    async def _cmd_toggle_notifications(self, argument) -> bool:
        """Toggles displaying 2 types of in-game notifications.
        Useful if you only want certain types of notifications.
        This command does not remove any already-queued notifications.
        1) "/toggle_notifications hints" toggles showing hints notifications
        2) "/toggle_notifications self_sent" toggles notifications for items you send to yourself (such as when playing a solo seed)."""
        
        if argument not in ["hints", "self_sent"]:
            self.output(f"{argument} is not a valid argument. Must be either \"hints\" or \"self_sent\".")
            return True
        
        if argument == "hints":
            self.output(f"Toggling hint notifications from {self.ctx.hint_notifs} to {not self.ctx.hint_notifs}.")
            self.ctx.hint_notifs = not self.ctx.hint_notifs
            return True
        else:
            self.output(f"Toggling self sent notifications from {self.ctx.self_sent_notifs} to {not self.ctx.self_sent_notifs}.")
            self.ctx.self_sent_notifs = not self.ctx.self_sent_notifs
            return True
    
    async def _cmd_toggle_deathlink(self, argument: str) -> bool:
        """Toggles DeathLink, if enabled for this seed.
        Can be toggled separately for incoming and outgoing deaths.
        1) "/toggle_deathlink incoming" toggles whether to process or ignore incoming deaths.
        2) "/toggle_deathlink outgoing" toggles whether to send deaths when you die enough times (per your amnesty value)."""
        if len(self.ctx.slot_data) == 0:
            self.output("Connect to a slot before using commands.")
            return True
        
        if not self.ctx.slot_data["death_link"]:
            self.output("DeathLink is not enabled for this seed.")
            return True
        
        if argument not in ["incoming", "outgoing"]:
            self.output("Invalid command format. Must be \"/toggle_deathlink incoming\" or \"/toggle_deathlink outgoing\".")
            return True
        
        if argument == "outgoing":
            self.output(f"Toggling DeathLink from {self.ctx.deathlink_outgoing} to {not self.ctx.deathlink_outgoing}.")
            self.ctx.deathlink_outgoing = not self.ctx.deathlink_outgoing
        elif argument == "incoming":
            self.output(f"Toggling incoming DeathLink from {self.ctx.deathlink_incoming} to {not self.ctx.deathlink_incoming}.")
            self.ctx.deathlink_incoming = not self.ctx.deathlink_incoming
        return True
        

class SpyroAHTContext(SuperContext):
    tags = {"AP"}
    items_handling = 0b111
    game = "Spyro: A Hero's Tail"
    command_processor = SpyroAHTCommands

    def __init__(self, server_address: str | None = None, password: str | None = None) -> None:
        super().__init__(server_address, password)
        if tracker_loaded:
            super().set_events_callback(self._event_update)
            super().set_callback(self._location_update)
        self.tracker_found = tracker_loaded
        
        # these update whenever UT reports a new location or event is in logic
        self._in_logic_events: list[str] = []
        self._in_logic_locations: list[str] = []
        
        # these cut back on repetitively scanning to-be-hinted locations after they've been hinted already
        self.shop_hinted = False
        
        # notification flags
        self.self_sent_notifs = True
        self.hint_notifs = True
        
        # tracks goal completion so far. finished_goals replaces Falses with Trues as things complete. full_goal_list is used with .index to find a given goal's index
        self.full_goal_list = ["Gnasty Gnorc", "Ineptune", "Red", "Mecha-Red", "Dark Gems", "Light Gems", "Dragon Eggs", "Fireworks", "Shop Items", "Locked Chests", "Elder Tomas", "Elder Magnus", "Elder Titan", "Elder Astor", "Sgt. Byrd", "Blink", "Turret", "Sparx"]
        self.finished_goals = [False]*len(self.full_goal_list)
        
        self.unlocked_shops = []

        self.emu_client: GenericClient = None # type: ignore
        self.emu_loop: asyncio.Task = None # type: ignore
        self.auth_ready = asyncio.Event()
        self.deathlink_incoming = True
        self.deathlink_outgoing = True

        self.slot_data = {}
        self._seed = ""

        self._shop_items: list[NetworkItem] = []
        self._shop_items_received = asyncio.Event()

        self._handled_items: set[NetworkItem] = set()

        self._checked_boss_doors = set()
        self._checked_gem_doors = set()
        self._checked_gadgets = set()

        self._scouted_locations: set[int] = set()
    
    def make_gui(self) -> type[GameManager]:
        ui = super().make_gui()
        ui.base_title = "Spyro: A Hero's Tail Archipelago Client"
        return ui

    async def server_auth(self, password_requested: bool = False):
        if password_requested and not self.password:
            await super().server_auth(password_requested)
        await self.get_username()
        await self.send_connect(game=self.game)
    
    def on_package(self, cmd: str, args: dict):
        super().on_package(cmd, args)
        
        match cmd:
            case 'Connected':
                self.slot_data = args['slot_data']
                # TODO: try messing with this to see if able to prevent connection if version mismatch?
                if self.slot_data['death_link'] != 0:
                    self.tags.add("DeathLink")
                    Utils.async_start(self.send_msgs([{"cmd": "ConnectUpdate", "tags": self.tags}]))
                if self.emu_loop and not self.emu_loop.cancelled():
                    self.emu_loop.cancel()
                self.emu_loop = asyncio.create_task(self._emu_loop())
                self.auth_ready.set()
            case 'RoomInfo':
                self._seed = args['seed_name']
            case 'LocationInfo':
                if not self._shop_items_received.is_set():
                    self._shop_items = [NetworkItem(*item) for item in args['locations']]
                    self._shop_items_received.set()
            case 'PrintJSON':
                match args.get('type', ''):
                    case 'ItemSend':
                        # item.player = # of player who sent it
                        # args['receiving'] = # of player receiving it
                        # item.item = id of item
                        # item.location = id of location where it was found
                        # self.slot = # of currently connected AHT player
                        item = args['item']
                        if args['receiving'] == self.slot:
                            if item.item == consts.ITEM_INFO["Spam Call"][0] or item.item == consts.ITEM_INFO["Gem Tax"][0]: sender = "Moneybags" 
                            elif item.player == self.slot: sender = "yourself"
                            else: sender = self.player_names[item.player]
                            item_name = self.item_names.lookup_in_slot(item.item, self.slot)
                            if item.player == self.slot and not self.self_sent_notifs:  # don't send "received <item> from yourself" notifs if flag is off
                                return
                            self.emu_client.msg_queue.put_nowait((consts.COLOUR_WHITE, f'Received {item_name} from {sender}'))
                        elif args['receiving'] != self.slot and item.player == self.slot:
                            receiver_id = args['receiving']
                            receiver_name = self.player_names[receiver_id]
                            item_name = self.item_names.lookup_in_slot(item.item, receiver_id)
                            self.emu_client.msg_queue.put_nowait((consts.COLOUR_WHITE, f"Sent {item_name} to {receiver_name}"))
                    case 'Hint':
                        if args['found']: return
                        if args['receiving'] == self.slot and self.hint_notifs:  # don't send hint notifs if flag is off
                            item = args['item']
                            player = "your" if item.player == self.slot else f"{self.player_names[item.player]}'s"
                            location = self.location_names.lookup_in_slot(item.location, item.player)
                            msg = f"[Hint] Your {self.item_names.lookup_in_slot(item.item, self.slot)} is at {player} {location}"
                            self.emu_client.msg_queue.put_nowait((consts.COLOUR_WHITE, msg))
                        elif args['item'].player == self.slot and self.hint_notifs:  # don't send hint notifs if flag is off
                            item = args['item']
                            location = self.location_names.lookup_in_slot(item.location, self.slot)
                            player = self.player_names[args['receiving']]
                            msg = f"[Hint] {player}'s {self.item_names.lookup_in_slot(item.item, args['receiving'])} is at {location}"
                            self.emu_client.msg_queue.put_nowait((consts.COLOUR_WHITE, msg))
    
    async def start_emu_client(self):
        # bizarre issue where passworded seeds re-trigger parts of the emu and connection setup process
        # this ensures that if dolphin engine is hooked through that, to unhook it first before continuing as usual
        if self.emu_client is not None:
            await self.emu_client.disconnect()
        self.emu_client = DolphinClient(self, logger)
        await self.emu_client.connect()
        await self.emu_client.apply_patch()
        await self.emu_client.ready.wait()
    
    async def _receive_items(self):
        item_counts = collections.Counter(self.item_names.lookup_in_slot(i.item, self.slot) for i in self.items_received)
        for item in self.items_received:
            if item in self._handled_items: continue
            self._handled_items.add(item)
            if consts.ITEM_GROUP_IDS["Elder Abilities"][0] <= item.item <= consts.ITEM_GROUP_IDS["Abilities"][1]:
                await self.emu_client.set_flag(self.emu_client.addresses.ABILITY_FLAGS, consts.ABILITY_MATCH[item.item], True)
                if not await self.emu_client.has_any_breath() and consts.ITEM_GROUP_IDS["Breaths"][0] <= item.item <= consts.ITEM_GROUP_IDS["Breaths"][1]:
                    await self.emu_client.set_breath(item.item)
            elif consts.ITEM_GROUP_IDS["Key Rings"][0] <= item.item <= consts.ITEM_GROUP_IDS["Key Rings"][1]:
                if item.item >= consts.ITEM_GROUP_IDS["Key Rings"][1]-4:  # if realm key ring, needs converting into list of level key rings
                    ring_ids = consts.REALM_KEY_RING_LOOKUP[item.item]  # converts from realm key ring id -> list of level key ring ids
                else: ring_ids = [item.item]  # already is a level key ring id
                
                for ring_id in ring_ids:
                    key_ring_id_list = list(range(consts.ITEM_GROUP_IDS["Key Rings"][0], consts.ITEM_GROUP_IDS["Key Rings"][1]-3))
                    bit = key_ring_id_list.index(ring_id)
                    address = self.emu_client.addresses.g_KEYRING_BITFIELD + (bit // 8)
                    await self._set_keyring_or_shop(bit, address)
            elif consts.ITEM_GROUP_IDS["Access Cards"][0] <= item.item <= consts.ITEM_GROUP_IDS["Access Cards"][1]:
                await self.emu_client.allow_realm_access(item.item - consts.ITEM_GROUP_IDS["Access Cards"][0])  # adjust to value from 0-3
            elif item.item == consts.ITEM_INFO["Health Unit+"][0] or item.item == consts.ITEM_INFO["Shockwave"][0]:
                await self.emu_client.set_flag(self.emu_client.addresses.ABILITY_FLAGS, consts.ABILITY_MATCH[item.item], True)
            elif item.item == consts.ITEM_INFO["Butterfly Jar"][0]:
                await self.emu_client.enable_butterfly_jar()
            elif item.item == consts.ITEM_INFO["Double Gems"][0]:
                await self.emu_client.toggle_double_gems(True)
            elif item.item == consts.ITEM_INFO["Lockpick"][0]:
                count = await self.emu_client.get_item_count(self.emu_client.addresses.g_NUM_LOCK_PICKS_RECEIVED)
                if count < item_counts["Lockpick"]:
                    lc = await self.emu_client.get_item_count(self.emu_client.addresses.LOCKPICKS)
                    await self.emu_client.set_item(self.emu_client.addresses.g_NUM_LOCK_PICKS_RECEIVED, count + 1)
                    await self.emu_client.set_item(self.emu_client.addresses.LOCKPICKS, lc + 1)
            elif item.item == consts.ITEM_INFO["Lockpick Bundle"][0]:
                amount_from_bundles = item_counts["Lockpick Bundle"] * self.slot_data["item_bundles"]["Lockpick"]
                if amount_from_bundles > 52: amount_from_bundles = 52
                file_count = await self.emu_client.get_item_count(self.emu_client.addresses.g_NUM_LOCK_PICKS_RECEIVED)
                if amount_from_bundles > file_count:
                    await self.emu_client.set_item(self.emu_client.addresses.g_NUM_LOCK_PICKS_RECEIVED, amount_from_bundles)
                    difference = amount_from_bundles - file_count
                    curr_lockpick_amount = await self.emu_client.get_item_count(self.emu_client.addresses.LOCKPICKS)
                    await self.emu_client.set_item(self.emu_client.addresses.LOCKPICKS, curr_lockpick_amount + difference)
            elif item.item == consts.ITEM_INFO["Dark Gem"][0]:
                count = await self.emu_client.get_item_count(self.emu_client.addresses.DARK_GEM_COUNT)
                if count < item_counts["Dark Gem"]:
                    await self.emu_client.set_item(self.emu_client.addresses.DARK_GEM_COUNT, count + 1)
            elif item.item == consts.ITEM_INFO["Dark Gem Bundle"][0]:
                amount_from_bundles = item_counts["Dark Gem Bundle"] * self.slot_data["item_bundles"]["Dark Gem"]
                if amount_from_bundles > 40: amount_from_bundles = 40
                file_count = await self.emu_client.get_item_count(self.emu_client.addresses.DARK_GEM_COUNT)
                if amount_from_bundles > file_count:
                    await self.emu_client.set_item(self.emu_client.addresses.DARK_GEM_COUNT, amount_from_bundles)
            elif item.item == consts.ITEM_INFO["Light Gem"][0]:
                count = await self.emu_client.get_item_count(self.emu_client.addresses.LIGHT_GEM_COUNT)
                if count < item_counts["Light Gem"]:
                    await self.emu_client.set_item(self.emu_client.addresses.LIGHT_GEM_COUNT, count + 1)
            elif item.item == consts.ITEM_INFO["Light Gem Bundle"][0]:
                amount_from_bundles = item_counts["Light Gem Bundle"] * self.slot_data["item_bundles"]["Light Gem"]
                if amount_from_bundles > 100: amount_from_bundles = 100
                file_count = await self.emu_client.get_item_count(self.emu_client.addresses.LIGHT_GEM_COUNT)
                if amount_from_bundles > file_count:
                    await self.emu_client.set_item(self.emu_client.addresses.LIGHT_GEM_COUNT, amount_from_bundles)
            elif consts.ITEM_GROUP_IDS["Shop Unlocks"][0] <= item.item <= consts.ITEM_GROUP_IDS["Shop Unlocks"][0]+36:
                await self._unlock_shop(item.item, "Randomized")
            elif consts.ITEM_GROUP_IDS["Shop Unlocks"][0]+37 <= item.item <= consts.ITEM_GROUP_IDS["Shop Unlocks"][0]+49:
                await self._unlock_shop(item.item, "Progressive")
            elif consts.ITEM_GROUP_IDS["Shop Unlocks"][0]+50 <= item.item <= consts.ITEM_GROUP_IDS["Shop Unlocks"][0]+62:
                await self._unlock_shop(item.item, "Level")
            elif consts.ITEM_GROUP_IDS["Shop Unlocks"][0]+63 <= item.item <= consts.ITEM_GROUP_IDS["Shop Unlocks"][1]:
                await self._unlock_shop(item.item, "Realm")
            elif item.item == consts.ITEM_INFO["Dragon Egg"][0]:
                count = await self.emu_client.get_item_count(self.emu_client.addresses.DRAGON_EGG_COUNT)
                if count < item_counts["Dragon Egg"]:
                    await self.emu_client.set_item(self.emu_client.addresses.DRAGON_EGG_COUNT, count + 1)
            elif item.item == consts.ITEM_INFO["Gem Pack"][0]:
                count = await self.emu_client.get_item_count(self.emu_client.addresses.g_NUM_GEM_PACKS_RECEIVED)
                if count < item_counts["Gem Pack"]:
                    await self.emu_client.set_item(self.emu_client.addresses.g_NUM_GEM_PACKS_RECEIVED, count + 1)
                    await self.emu_client.add_gem_pack()
            elif item.item == consts.ITEM_INFO["Fire Bomb"][0]:
                await self.add_breath_bomb(self.emu_client.addresses.g_NUM_FIRE_AMMO_RECEIVED, item_counts["Fire Bomb"], self.emu_client.addresses.FIRE_BOMBS)
            elif item.item == consts.ITEM_INFO["Electric Bomb"][0]:
                await self.add_breath_bomb(self.emu_client.addresses.g_NUM_ELECTRIC_AMMO_RECEIVED, item_counts["Electric Bomb"], self.emu_client.addresses.ELECTRIC_BOMBS)
            elif item.item == consts.ITEM_INFO["Water Bomb"][0]:
                await self.add_breath_bomb(self.emu_client.addresses.g_NUM_WATER_AMMO_RECEIVED, item_counts["Water Bomb"], self.emu_client.addresses.WATER_BOMBS)
            elif item.item == consts.ITEM_INFO["Ice Bomb"][0]:
                await self.add_breath_bomb(self.emu_client.addresses.g_NUM_ICE_AMMO_RECEIVED, item_counts["Ice Bomb"], self.emu_client.addresses.ICE_BOMBS)
            elif item.item == consts.ITEM_INFO["Spam Call"][0]:
                await self.queue_trap(self.emu_client.addresses.g_TRAP_COUNTERS, "Spam Call", item_counts["Spam Call"])
            elif item.item == consts.ITEM_INFO["Reverse Controls"][0]:
                await self.queue_trap(self.emu_client.addresses.g_TRAP_COUNTERS+1, "Reverse Controls", item_counts["Reverse Controls"])
            elif item.item == consts.ITEM_INFO["Bounce"][0]:
                await self.queue_trap(self.emu_client.addresses.g_TRAP_COUNTERS+4, "Bounce", item_counts["Bounce"])
            elif item.item == consts.ITEM_INFO["Damage Sparx"][0]:
                total = await self.emu_client.get_item_count(self.emu_client.addresses.g_TRAP_COUNTERS + 2)
                if total < item_counts["Damage Sparx"]:
                    await self.emu_client.set_item(self.emu_client.addresses.g_TRAP_COUNTERS + 2, total + 1)
                    await self.emu_client.damage_sparx()
            elif item.item == consts.ITEM_INFO["Gem Tax"][0]:
                total = await self.emu_client.get_item_count(self.emu_client.addresses.g_TRAP_COUNTERS + 3)
                if total < item_counts["Gem Tax"]:
                    await self.emu_client.set_item(self.emu_client.addresses.g_TRAP_COUNTERS + 3, total + 1)
                    await self.emu_client.gem_tax()
    
    async def add_breath_bomb(self, ammo_address, count, bomb_address):
        total = await self.emu_client.get_item_count(ammo_address)
        if total < count:
            count = await self.emu_client.get_item_count(bomb_address)
            await self.emu_client.set_item(ammo_address, total + 1)
            await self.emu_client.set_item(bomb_address, count + 1)
    
    async def queue_trap(self, trap_address: int, name: str, count: int):
        total = await self.emu_client.get_item_count(trap_address)
        if total < count:
            await self.emu_client.set_item(trap_address, total + 1)
            self.emu_client.trap_queue.put_nowait(name)
                
    async def _unlock_shop(self, item_id, shop_type):
        if shop_type == "Randomized":
            name = self.item_names.lookup_in_slot(item_id, self.slot).replace(" Shop Unlock", "")
            if "Depot" in name: await self.check_hub_access(name)
            bit = consts.SHOP_PAD_LIST.index(name)
            address = self.emu_client.addresses.g_SHOPPAD_BITFIELD + (bit // 8)
            await self._set_keyring_or_shop(bit, address)
        elif shop_type == "Progressive":
            name = self.item_names.lookup_in_slot(item_id, self.slot).replace("Progressive ", "")
            level = name.split(" - ")[0]
            shops = consts.LEVEL_SHOP_LOOKUP[level].copy()
            if self.slot_data["open_world_mode"] == 4: shops.reverse()
            for shop in shops:
                if f"{level} - {shop}" not in self.unlocked_shops:
                    name = f"{level} - {shop}"
                    if "Depot" in name: await self.check_hub_access(name)
                    self.unlocked_shops.append(name)
                    bit = consts.SHOP_PAD_LIST.index(name)
                    address = self.emu_client.addresses.g_SHOPPAD_BITFIELD + (bit // 8)
                    await self._set_keyring_or_shop(bit, address)
                    break
        elif shop_type == "Level":
            level = self.item_names.lookup_in_slot(item_id, self.slot).split(" - ")[0]
            for shop in consts.LEVEL_SHOP_LOOKUP[level]:
                name = f"{level} - {shop}"
                if "Depot" in name: await self.check_hub_access(name)
                self.unlocked_shops.append(name)
                bit = consts.SHOP_PAD_LIST.index(name)
                address = self.emu_client.addresses.g_SHOPPAD_BITFIELD + (bit // 8)
                await self._set_keyring_or_shop(bit, address)
        elif shop_type == "Realm":
            realm = self.item_names.lookup_in_slot(item_id, self.slot).split(" - ")[0]
            for level in consts.REALM_LEVEL_LOOKUP[realm]:
                for shop in consts.LEVEL_SHOP_LOOKUP[level]:
                    name = f"{level} - {shop}"
                    if "Depot" in name: await self.check_hub_access(name)
                    self.unlocked_shops.append(name)
                    bit = consts.SHOP_PAD_LIST.index(name)
                    address = self.emu_client.addresses.g_SHOPPAD_BITFIELD + (bit // 8)
                    await self._set_keyring_or_shop(bit, address)
    
    async def _unlock_starting_realm_shop(self, name: str):
        bit = consts.SHOP_PAD_LIST.index(name)
        address = self.emu_client.addresses.p_SHOPPAD_BITFIELD + (bit // 8)
        await self._set_keyring_or_shop(bit, address)
    
    async def _set_keyring_or_shop(self, bit, address):
        data = await self.emu_client.get_item_count(address)
        flag = 1 << (bit % 8)
        data |= flag
        await self.emu_client.set_item(address, data)
        
    async def check_hub_access(self, name: str):
        if "Village Depot" in name: await self.emu_client.allow_realm_access(0)
        elif "Coastal Depot" in name: await self.emu_client.allow_realm_access(1)
        elif "Frosty Depot" in name: await self.emu_client.allow_realm_access(2)
        elif "Stormy Depot" in name: await self.emu_client.allow_realm_access(3)

    async def _check_doors(self):
        dark = await self.emu_client.get_item_count(self.emu_client.addresses.DARK_GEM_COUNT)
        for idx, cost in enumerate(self.slot_data['boss_lair_costs']):
            if idx in self._checked_boss_doors: continue
            if dark >= cost:
                self._checked_boss_doors.add(idx)
                msg = consts.COLOUR_RED, "SOMETHING WENT WRONG CHECKING BOSS LAIR DOOR COSTS"
                match idx:
                    case 0:
                        msg = consts.COLOUR_WHITE, "You have enough Dark Gems for Gnasty's Lair!"
                    case 1:
                        msg = consts.COLOUR_WHITE, "You have enough Dark Gems for Ineptune's Lair!"
                    case 2:
                        msg = consts.COLOUR_WHITE, "You have enough Dark Gems for Red's Lair!"
                    case 3:
                        msg = consts.COLOUR_WHITE, "You have enough Dark Gems for Mecha-Red's Lair!"
                self.emu_client.msg_queue.put_nowait(msg)
        
        light = await self.emu_client.get_item_count(self.emu_client.addresses.LIGHT_GEM_COUNT)
        for idx, cost in enumerate(self.slot_data['light_gem_door_costs']):
            if idx in self._checked_gem_doors: continue
            if light >= cost:
                self._checked_gem_doors.add(idx)
                msg = consts.COLOUR_RED, "SOMETHING WENT WRONG CHECKING LIGHT GEM DOOR COSTS"
                match idx:
                    case 0:
                        msg = consts.COLOUR_WHITE, "You have enough Light Gems for the door in Dragonfly Falls!"
                    case 1:
                        msg = consts.COLOUR_WHITE, "You have enough Light Gems for the door in Coastal Remains!"
                    case 2:
                        msg = consts.COLOUR_WHITE, "You have enough Light Gems for the door in Frostbite Village"
                    case 3:
                        msg = consts.COLOUR_WHITE, "You have enough Light Gems for the door in Dark Mine!"
                self.emu_client.msg_queue.put_nowait(msg)
        
        for idx, cost in enumerate(self.slot_data['gadget_costs']):
            if idx in self._checked_gadgets: continue
            if light >= cost:
                self._checked_gadgets.add(idx)
                msg = consts.COLOUR_RED, "SOMETHING WENT WRONG CHECKING GADGET COSTS"
                match idx:
                    case 0:
                        msg = consts.COLOUR_WHITE, "You have enough Light Gems for the Ball Gadget!"
                    case 1:
                        msg = consts.COLOUR_WHITE, "You have enough Light Gems for the Invincibility Gadget!"
                    case 2:
                        msg = consts.COLOUR_WHITE, "You have enough Light Gems for the Supercharge Gadget!"
                self.emu_client.msg_queue.put_nowait(msg)

    async def _location_checks(self):
        locations = await self.emu_client.scan_locations(self.slot_data)
        if consts.STARTER_CHECK_IDS[0] not in self.checked_locations:
            locations.update(consts.STARTER_CHECK_IDS)
        locations -= self.checked_locations
        if locations:
            await self.send_msgs([{"cmd": "LocationChecks", "locations": locations}])
    
    async def _location_scouts(self):
        locations = set()
        if self.slot_data['auto_hinting']["Minigames"] == "on":
            for obj, loc in consts.MINIGAME_OBJECTIVES.items():
                flag = await self.emu_client.get_objective(obj)
                if flag:
                    locations.update(loc)
        
        if self.slot_data['auto_hinting']["Bosses"] == "on":
            for obj, loc in consts.BOSS_LAIR_OPEN_OBJECTIVES.items():
                flag = await self.emu_client.get_objective(obj)
                if flag:
                    locations.update(loc)
        
        if self.slot_data['auto_hinting']["Shop Items"] == "on" and not self.shop_hinted:
            locations.update(consts.SHOP_ITEM_IDS[:self.slot_data['shop_item_count']])
            self.shop_hinted = True
                
        locations -= self._scouted_locations
        if locations:
            self._scouted_locations.update(locations)
            await self.send_msgs([{"cmd":"LocationScouts","locations":locations,"create_as_hint":2}])
    
    def _event_update(self, events: list[str]) -> bool:
        self._in_logic_events = events
        return True  # does nothing but is required (and is documented as such by UT)
    
    def _location_update(self, locations: list[str]) -> bool:
        from . import loc_names_to_ids
        self._in_logic_locations = locations
        self.in_logic_ids_to_names = collections.defaultdict(str)
        for loc_name in self._in_logic_locations:
            id = str(loc_names_to_ids[loc_name])
            self.in_logic_ids_to_names[id] = loc_name
        return True  # does nothing but is required (and is documented as such by UT)

    async def check_goal(self) -> bool:
        output = []
        
        last_one = self.finished_goals.count(True) == len(self.slot_data["goals_dict"].keys()) - 1  # marks if check_goal_component should acknowledge being last goal or not
        for goal in self.slot_data["goals_dict"]:
            if not self.finished_goals[self.full_goal_list.index(goal)]:
                done, new_output = await self.check_goal_component(goal, last_one)
                self.finished_goals[self.full_goal_list.index(goal)] = done
                if new_output != "": output.append(new_output)
            
        # tally goes +1 when a goal component is met. If that value matches however many goals there are, we're done!
        if self.finished_goals.count(True) == len(self.slot_data["goals_dict"].keys()):
            logger.log("INFO: All goals are complete, nice work!")
            await self.send_msgs([{"cmd": "StatusUpdate", "status": ClientStatus.CLIENT_GOAL}])
            return True
        else:
            if len(output) > 0:
                logger.log(f"INFO: You've completed the following goal(s): {", ".join(output)}! Run /check_goal for info on what's left to do.")
            return False

    async def check_goal_component(self, goal: str, last_one: bool) -> tuple[bool, str]:
        count = 0
        for goal_id in self.slot_data["goals_dict"][goal]["ids"]:
            if goal_id in self.checked_locations:
                count += 1
        
        if count >= self.slot_data["goals_dict"][goal]["amount"]:
            return_text = "" if last_one else goal
            return True, return_text
            
        return False, ""
    
    async def _emu_loop(self):
        has_goaled = False
        try:
            await self.auth_ready.wait()
            await self.start_emu_client()

            while not self.exit_event.is_set():
                if not self.server or self.server.socket.closed:
                    logger.log("INFO: Client disconnected.")
                    await self.emu_client.disconnect()
                    return

                try:
                    await asyncio.wait_for(self.watcher_event.wait(), 1.0)
                except asyncio.TimeoutError:
                    pass
                self.watcher_event.clear()

                if await self.emu_client.should_process_checks():
                    if self.slot_data["death_link"] > 0:
                        await self._send_deathlink()
                    await self._receive_items()
                    await self._check_doors()
                    await self._location_checks()
                    await self._location_scouts()
                    if tracker_loaded:
                        await self.emu_client.update_pause_gems(self._in_logic_events)
                    if tracker_loaded:
                        await self.emu_client.update_tracker(self.in_logic_ids_to_names)
                    if not has_goaled:
                        has_goaled = await self.check_goal()
        except Exception:
            logger.log("WARNING: Error in main emulator loop, please report to developers.", exc_info=True)
    
    async def _send_deathlink(self):
        if not self.deathlink_outgoing:  # client-side toggling of deathlink
            return
        death_id = await self.emu_client.export_deathlink()
        if death_id:
            if death_id < 0 or death_id > 27:
                raise TypeError(f"Invalid outgoing deathlink id: {death_id}.")
            await self.send_death(consts.DEATHLINK_MESSAGES[death_id-1].format(name=self.player_names[self.slot]))

    async def _receive_deathlink(self, msg: str):
        self.emu_client.msg_queue.put_nowait((consts.COLOUR_RED, msg))
        await self.emu_client.import_deathlink(self.slot_data['death_link'])
    
    def on_deathlink(self, data: dict) -> None:
        if not self.deathlink_incoming:  # client-side toggling of deathlink
            return
        Utils.async_start(self._receive_deathlink(data.get('cause') or f"{data['source']} died."))

    async def shutdown(self):
        if self.emu_loop:
            self.emu_loop.cancel()
        if self.emu_client:
            await self.emu_client.disconnect()
        return await super().shutdown()