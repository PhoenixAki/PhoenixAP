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
        convert = {0: "halt on", 1: "auto fix"}
        self.output(f"You chose to {convert[self.ctx.slot_data['auto_corrections']]} generation errors.")
        
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
                amount = self.ctx.slot_data[self.ctx.convert_goal_info[goal][1]]
                
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
        self.output(f"Enabled Elder Titan Goals: {output}.")
        # minigame goals
        enabled = []
        for goal in ["Sgt. Byrd", "Blink", "Turret", "Sparx"]:
            if goal in self.ctx.slot_data["goals_dict"].keys():
                amount = self.ctx.slot_data["minigames_goal_count"]
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
        # vanilla minigame rewards
        output = ""
        for minigame_type in ["Sgt. Byrd", "Blink", "Turret", "Sparx"]:
            output += f"{minigame_type} rewards are {'vanilla' if minigame_type in self.ctx.slot_data['vanilla_minigame_rewards'] else 'randomized'}, "
        self.output(f"Minigames: {output[:-2]}.")
        # filler items
        output = ""
        for minigame_type in ["Dragon Eggs", "Breath Bombs", "Gem Packs", "Shinies"]:
            if minigame_type in self.ctx.slot_data['filler_items']: output+= f"{minigame_type}, "
        self.output(f"Enabled Filler Item Types: {output[:-2]}.")
        
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
        for breath in ["Fire", "Electric", "Water", "Ice"]:
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
        output_2 = "enabled" if self.ctx.slot_data["key_rings"] == 1 else "not enabled"
        self.output(f"Shop items are {output} and key rings are {output_2}.")
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
            output = "disable" if self.ctx.slot_data['double_gems'] else "enable"
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
        output = "will" if self.ctx.slot_data["hint_boss_rewards"] else "won't"
        output_2 = "will" if self.ctx.slot_data["hint_minigame_rewards"] else "won't"
        output_3 = "will" if self.ctx.slot_data["hint_shop_items"] else "won't"
        self.output(f"Boss rewards {output} be hinted, minigame rewards {output_2} be hinted, and randomized shop items {output_3} be hinted.")
        # hide shop item names
        output = "hidden" if self.ctx.slot_data["hide_shop_item_names"] else "not hidden"
        self.output(f"Your shop item names are {output}.")
        # easy bosses
        output = "Boss Difficulty: "
        for boss in ["Gnasty Gnorc", "Ineptune", "Red", "Mecha-Red"]:
            output += f"{boss} easy, " if boss in self.ctx.slot_data["easy_bosses"] else f"{boss} normal, "
        self.output(f"{output[:-2]}.")
        # skip cutscenes & elevators
        output = "can" if self.ctx.slot_data["skip_cutscenes"] else "can't"
        output_2 = "can" if self.ctx.slot_data["skip_elevators"] else "can't"
        self.output(f"Cutscenes {output} be skipped and elevators {output_2} be skipped.")
        # teleport across realms
        output = "can" if self.ctx.slot_data['teleport_across_realms'] else "can't"
        self.output(f"You {output} teleport across realms.")

        return True

    async def _cmd_check_goal(self) -> bool:
        """Details completion progress on all enabled goals, including how many checks are left to do for each."""
        if self.ctx.goals_dict == {}:
            self.output("Command cannot be ran before entering your save file.")
            return True
        
        completed_goals, incomplete_goals = [], []
        for goal in self.ctx.goals_dict.keys():
            # have all enabled goals here. check status of each
            _, option_name, id_list = self.ctx.convert_goal_info[goal]
            # get amounts
            if goal in ["Gnasty Gnorc", "Ineptune", "Red", "Mecha-Red"]: amount = 1
            elif "Elder" in goal: amount = 1
            elif goal in ["Sgt. Byrd", "Blink", "Turret", "Sparx"]: amount = self.ctx.slot_data["minigames_goal_count"]
            else: amount = self.ctx.slot_data[option_name]
            # adjust id lists
            if goal == "Light Gems" and self.ctx.slot_data["exclude_chest_items"] >= 2: id_list = id_list[:-15]
            if goal == "Dragon Eggs" and self.ctx.slot_data["exclude_chest_items"] in [1, 3]: id_list = id_list[:-16]
            if goal == "Shop Items": id_list = id_list[:self.ctx.slot_data["shop_item_count"]]
            # tally it up
            count = 0
            for goal_id in id_list:
                count += goal_id in self.ctx.checked_locations  # += 1 if true, otherwise 0
            # check for copmleted status
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
        self.loc_flag = False
        self.event_flag = False
        self._in_logic_events: list[str] = []
        self._in_logic_locations: list[str] = []
        
        # these cut back on repetitively scanning to-be-hinted locations after they've been hinted already
        self.shop_hinted = False
        
        # used for checking goal components
        self.goal_stuff_setup = False
        self.goals_dict: dict = {}
        self.goal_tally, self.goal_target = 0, 0
        self.finished_goals = [False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False]
        # this has a lot of info stuffed into it. goal name -> (finished_goals index, goal option name, id list)
        self.convert_goal_info = {"Gnasty Gnorc": (0, "boss_goal", consts.BOSS_IDS[0:2]), "Ineptune": (1, "boss_goal", consts.BOSS_IDS[2:4]), "Red": (2, "boss_goal", consts.BOSS_IDS[4:6]), "Mecha-Red": (3, "boss_goal", [consts.BOSS_IDS[6]]),
            "Dark Gems": (4, "dark_gems_goal", consts.DARK_GEM_IDS), "Light Gems": (5, "light_gems_goal", consts.LIGHT_GEM_IDS), "Dragon Eggs": (6, "dragon_eggs_goal", consts.DRAGON_EGG_IDS),
            "Fireworks": (7, "fireworks_goal", consts.FIREWORK_IDS), "Shop Items": (8, "shop_items_goal", consts.SHOP_ITEM_IDS), "Locked Chests": (9, "locked_chests_goal", consts.LOCKED_CHEST_IDS),
            "Elder Tomas": (10, "elders_goal", [consts.ELDER_ABILITY_IDS[0]]), "Elder Magnus": (11, "elders_goal", [consts.ELDER_ABILITY_IDS[1]]), "Elder Titan": (12, "elders_goal", [consts.ELDER_ABILITY_IDS[2]]),
            "Elder Astor": (13, "elders_goal", [consts.ELDER_ABILITY_IDS[3]]), "Sgt. Byrd": (14, "minigames_goal", consts.BYRD_IDS), "Blink": (15, "minigames_goal", consts.BLINK_IDS),
            "Turret": (16, "minigames_goal", consts.TURRET_IDS), "Sparx": (17, "minigames_goal", consts.SPARX_IDS)
        }
        
        self.unlocked_shops = []

        self.emu_client: GenericClient = None # type: ignore
        self.emu_loop: asyncio.Task = None # type: ignore
        self.auth_ready = asyncio.Event()

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
                    case 'ItemSend':  # TODO: put the send notification here?
                        item = args['item']
                        if args['receiving'] == self.slot:
                            if item.item in [80, 83]: player = "Moneybags"
                            else: player = self.player_names[item.player]
                            self.emu_client.msg_queue.put_nowait((consts.COLOUR_WHITE, f'Received {self.item_names.lookup_in_slot(item.item, self.slot)} from {player}'))
                        elif args['receiving'] != self.slot: self.emu_client.msg_queue.put_nowait((consts.COLOUR_WHITE, f"Sent {self.item_names.lookup_in_slot(item.item, self.slot)} to {self.player_names[item.player]}"))
                    case 'Hint':
                        if args['found']: return
                        if args['receiving'] == self.slot:
                            item = args['item']
                            player = "your" if item.player == self.slot else f"{self.player_names[item.player]}'s"
                            location = self.location_names.lookup_in_slot(item.location, item.player)
                            msg = f"[Hint] Your {self.item_names.lookup_in_slot(item.item, self.slot)} is at {player} {location}"
                            self.emu_client.msg_queue.put_nowait((consts.COLOUR_WHITE, msg))
                        elif args['item'].player == self.slot:
                            item = args['item']
                            location = self.location_names.lookup_in_slot(item.location, self.slot)
                            player = self.player_names[args['receiving']]
                            msg = f"[Hint] {player}'s {self.item_names.lookup_in_slot(item.item, args['receiving'])} is at {location}"
                            self.emu_client.msg_queue.put_nowait((consts.COLOUR_WHITE, msg))
    
    async def start_emu_client(self):
        self.emu_client = DolphinClient(self, logger)
        await self.emu_client.connect()
        await self.emu_client.apply_patch()
        await self.emu_client.ready.wait()
    
    async def _receive_items(self):
        item_counts = collections.Counter(self.item_names.lookup_in_slot(i.item, self.slot) for i in self.items_received)
        for item in self.items_received:
            if item in self._handled_items: continue
            self._handled_items.add(item)
            match item.item:
                case 0xB:
                    await self.emu_client.set_flag(self.emu_client.addresses.ABILITY_FLAGS, consts.AbilityFlags.Swim, True)
                case 0xC:
                    await self.emu_client.set_flag(self.emu_client.addresses.ABILITY_FLAGS, consts.AbilityFlags.Glide, True)
                case 0xD:
                    await self.emu_client.set_flag(self.emu_client.addresses.ABILITY_FLAGS, consts.AbilityFlags.Charge, True)
                case 0x1:
                    await self.emu_client.set_flag(self.emu_client.addresses.ABILITY_FLAGS, consts.AbilityFlags.DoubleJump, True)
                case 0x2:
                    await self.emu_client.set_flag(self.emu_client.addresses.ABILITY_FLAGS, consts.AbilityFlags.PoleSpin, True)
                case 0x3:
                    await self.emu_client.set_flag(self.emu_client.addresses.ABILITY_FLAGS, consts.AbilityFlags.WingShield, True)
                case 0x4:
                    await self.emu_client.set_flag(self.emu_client.addresses.ABILITY_FLAGS, consts.AbilityFlags.WallKick, True)
                case 0xE:
                    if not await self.emu_client.has_any_breath():
                        await self.emu_client.set_breath(consts.BREATH_FIRE)
                    await self.emu_client.set_flag(self.emu_client.addresses.ABILITY_FLAGS, consts.AbilityFlags.FireBreath, True)
                case 0x5:
                    if not await self.emu_client.has_any_breath():
                        await self.emu_client.set_breath(consts.BREATH_ELECTRIC)
                    await self.emu_client.set_flag(self.emu_client.addresses.ABILITY_FLAGS, consts.AbilityFlags.ElectricBreath, True)
                case 0x6:
                    if not await self.emu_client.has_any_breath():
                        await self.emu_client.set_breath(consts.BREATH_WATER)
                    await self.emu_client.set_flag(self.emu_client.addresses.ABILITY_FLAGS, consts.AbilityFlags.WaterBreath, True)
                case 0x7:
                    if not await self.emu_client.has_any_breath():
                        await self.emu_client.set_breath(consts.BREATH_ICE)
                    await self.emu_client.set_flag(self.emu_client.addresses.ABILITY_FLAGS, consts.AbilityFlags.IceBreath, True)
                case 0x8:
                    count = await self.emu_client.get_item_count(self.emu_client.addresses.DARK_GEM_COUNT)
                    if count < item_counts["Dark Gem"]:
                        await self.emu_client.set_item(self.emu_client.addresses.DARK_GEM_COUNT, count + 1)
                case 0x9:
                    count = await self.emu_client.get_item_count(self.emu_client.addresses.LIGHT_GEM_COUNT)
                    if count < item_counts["Light Gem"]:
                        await self.emu_client.set_item(self.emu_client.addresses.LIGHT_GEM_COUNT, count + 1)
                case 0xA:
                    count = await self.emu_client.get_item_count(self.emu_client.addresses.DRAGON_EGG_COUNT)
                    if count < item_counts["Dragon Egg"]:
                        await self.emu_client.set_item(self.emu_client.addresses.DRAGON_EGG_COUNT, count + 1)
                case 0x1C:
                    count = await self.emu_client.get_item_count(self.emu_client.addresses.g_NUM_LOCK_PICKS_RECEIVED)
                    if count < item_counts["Lockpick"]:
                        lc = await self.emu_client.get_item_count(self.emu_client.addresses.LOCKPICKS)
                        await self.emu_client.set_item(self.emu_client.addresses.g_NUM_LOCK_PICKS_RECEIVED, count + 1)
                        await self.emu_client.set_item(self.emu_client.addresses.LOCKPICKS, lc + 1)
                case 0xF:
                    await self.emu_client.set_flag(self.emu_client.addresses.ABILITY_FLAGS, consts.AbilityFlags.SparxHealthUpgrade, True)
                case 0x19:
                    await self.emu_client.enable_butterfly_jar()
                case 0x1A:
                    #await self.emu_client.set_flag(self.emu_client.addresses.ABILITY_FLAGS, consts.AbilityFlags.DoubleGems, True)
                    await self.emu_client.toggle_double_gems(True)
                case 0x1B:
                    await self.emu_client.set_flag(self.emu_client.addresses.ABILITY_FLAGS, consts.AbilityFlags.Shockwave, True)
                case 0x1D:
                    count = await self.emu_client.get_item_count(self.emu_client.addresses.g_NUM_GEM_PACKS_RECEIVED)
                    if count < item_counts["Gem Pack"]:
                        await self.emu_client.set_item(self.emu_client.addresses.g_NUM_GEM_PACKS_RECEIVED, count + 1)
                        await self.emu_client.add_gem_pack()
                case 0x1E:
                    total = await self.emu_client.get_item_count(self.emu_client.addresses.g_NUM_FIRE_AMMO_RECEIVED)
                    if total < item_counts["Fire Bomb"]:
                        count = await self.emu_client.get_item_count(self.emu_client.addresses.FIRE_BOMBS)
                        await self.emu_client.set_item(self.emu_client.addresses.g_NUM_FIRE_AMMO_RECEIVED, total + 1)
                        await self.emu_client.set_item(self.emu_client.addresses.FIRE_BOMBS, count + 1)
                case 0x1F:
                    total = await self.emu_client.get_item_count(self.emu_client.addresses.g_NUM_ELECTRIC_AMMO_RECEIVED)
                    if total < item_counts["Electric Bomb"]:
                        count = await self.emu_client.get_item_count(self.emu_client.addresses.ELECTRIC_BOMBS)
                        await self.emu_client.set_item(self.emu_client.addresses.g_NUM_ELECTRIC_AMMO_RECEIVED, total + 1)
                        await self.emu_client.set_item(self.emu_client.addresses.ELECTRIC_BOMBS, count + 1)
                case 0x20:
                    total = await self.emu_client.get_item_count(self.emu_client.addresses.g_NUM_WATER_AMMO_RECEIVED)
                    if total < item_counts["Water Bomb"]:
                        count = await self.emu_client.get_item_count(self.emu_client.addresses.WATER_BOMBS)
                        await self.emu_client.set_item(self.emu_client.addresses.g_NUM_WATER_AMMO_RECEIVED, total + 1)
                        await self.emu_client.set_item(self.emu_client.addresses.WATER_BOMBS, count + 1)
                case 0x21:
                    total = await self.emu_client.get_item_count(self.emu_client.addresses.g_NUM_ICE_AMMO_RECEIVED)
                    if total < item_counts["Ice Bomb"]:
                        count = await self.emu_client.get_item_count(self.emu_client.addresses.ICE_BOMBS)
                        await self.emu_client.set_item(self.emu_client.addresses.g_NUM_ICE_AMMO_RECEIVED, total + 1)
                        await self.emu_client.set_item(self.emu_client.addresses.ICE_BOMBS, count + 1)
                case 0x22 | 0x23 | 0x24 | 0x25 | 0x26 | 0x27 | 0x28 | 0x29 | 0x2A | 0x2B | 0x2C | 0x2D | 0x2E | 0x2F:
                    bit = consts.KEY_RINGS.index(item.item)
                    address = self.emu_client.addresses.g_KEYRING_BITFIELD + (bit // 8)
                    await self._set_keyring_or_shop(bit, address)
                case 0x30 | 0x31 | 0x32 | 0x33: # access cards
                    await self.emu_client.allow_realm_access(item.item)
                case 0x50:  # spam call
                    total = await self.emu_client.get_item_count(self.emu_client.addresses.g_TRAP_COUNTERS)
                    if total < item_counts["Spam Call"]:
                        await self.emu_client.set_item(self.emu_client.addresses.g_TRAP_COUNTERS, total + 1)
                        self.emu_client.trap_queue.put_nowait("Spam Call")
                case 0x51:  # reverse controls
                    total = await self.emu_client.get_item_count(self.emu_client.addresses.g_TRAP_COUNTERS + 1)
                    if total < item_counts["Reverse Controls"]:
                        await self.emu_client.set_item(self.emu_client.addresses.g_TRAP_COUNTERS + 1, total + 1)
                        self.emu_client.trap_queue.put_nowait("Reverse Controls")
                case 0x52:  # damage sparx trap
                    total = await self.emu_client.get_item_count(self.emu_client.addresses.g_TRAP_COUNTERS + 2)
                    if total < item_counts["Damage Sparx"]:
                        await self.emu_client.set_item(self.emu_client.addresses.g_TRAP_COUNTERS + 2, total + 1)
                        await self.emu_client.damage_sparx(logger)
                case 0x53:  # gem tax trap
                    total = await self.emu_client.get_item_count(self.emu_client.addresses.g_TRAP_COUNTERS + 3)
                    if total < item_counts["Gem Tax"]:
                        await self.emu_client.set_item(self.emu_client.addresses.g_TRAP_COUNTERS + 3, total + 1)
                        await self.emu_client.gem_tax()
                case 0x64 | 0x65 | 0x66 | 0x67 | 0x68 | 0x69 | 0x6A | 0x6B | 0x6C | 0x6D | 0x6E | 0x6F | 0x70 | 0x71 | 0x72 | 0x73 | 0x74 | 0x75 \
                | 0x76 | 0x77 | 0x78 | 0x79 | 0x7A | 0x7B | 0x7C | 0x7D | 0x7E | 0x7F | 0x80 | 0x81 | 0x82 | 0x83 | 0x84 | 0x85 | 0x86 | 0x87 | 0x88:
                    await self._unlock_shop(item.item, "Randomized")
                case 0x89 | 0x8A | 0x8B | 0x8C | 0x8D | 0x8E | 0x8F | 0x90 | 0x91 | 0x92 | 0x93 | 0x94 | 0x95:
                    await self._unlock_shop(item.item, "Progressive")
                case 0x96 | 0x97 | 0x98 | 0x99 | 0x9A | 0x9B | 0x9C | 0x9D | 0x9E | 0x9F | 0xA0 | 0xA1 | 0xA2:
                    await self._unlock_shop(item.item, "Level")
                case 0xA3 | 0xA4 | 0xA5 | 0xA6:
                    await self._unlock_shop(item.item, "Realm")
                
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
        if "Village Depot" in name: await self.emu_client.allow_realm_access(0x30)
        elif "Coastal Depot" in name: await self.emu_client.allow_realm_access(0x31)
        elif "Frosty Depot" in name: await self.emu_client.allow_realm_access(0x32)
        elif "Stormy Depot" in name: await self.emu_client.allow_realm_access(0x33)

    async def _check_doors(self):
        dark = await self.emu_client.get_item_count(self.emu_client.addresses.DARK_GEM_COUNT)
        for idx, cost in enumerate(self.slot_data['boss_lair_costs']):
            if idx in self._checked_boss_doors: continue
            if dark >= cost:
                self._checked_boss_doors.add(idx)
                msg = consts.COLOUR_RED, "SOMETHING WENT WRONG"
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
                msg = consts.COLOUR_RED, "SOMETHING WENT WRONG"
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
                msg = consts.COLOUR_RED, "SOMETHING WENT WRONG"
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
        if self.slot_data['hint_minigame_rewards']:
            for obj, loc in consts.MINIGAME_OBJECTIVES.items():
                flag = await self.emu_client.get_objective(obj)
                if flag:
                    locations.update(loc)
        
        if self.slot_data['hint_boss_rewards']:
            for obj, loc in consts.BOSS_LAIR_OPEN_OBJECTIVES.items():
                flag = await self.emu_client.get_objective(obj)
                if flag:
                    locations.update(loc)
        
        if self.slot_data['hint_shop_items'] and not self.shop_hinted:
            locations.update(consts.SHOP_ITEM_IDS[:self.slot_data['shop_item_count']])
            self.shop_hinted = True
                
        locations -= self._scouted_locations
        if locations:
            self._scouted_locations.update(locations)
            await self.send_msgs([{"cmd":"LocationScouts","locations":locations,"create_as_hint":2}])
    
    def _event_update(self, events: list[str]) -> bool:
        self._in_logic_events = events
        self.loc_flag = True
        return True  # does nothing but is required (and is documented as such by UT)
    
    def _location_update(self, locations: list[str]) -> bool:
        self._in_logic_locations = locations
        self.event_flag = True
        return True  # does nothing but is required (and is documented as such by UT)

    async def check_goal(self) -> bool:
        from CommonClient import logger
        output = []
        
        # self.finished_goals avoids re-checking goals that have already been found to be complete
        last_one = (self.goal_tally == self.goal_target - 1)  # marks if check_goal_component should acknowledge being last goal or not
        for goal in self.goals_dict:
            finished_index, option_name, id_list = self.convert_goal_info[goal]
            # adjust id lists as needed. variable shop item amounts as well as exclude_chest_items for light gems and dragon eggs
            if goal == "Shop Items":
                id_list = id_list[:self.slot_data['shop_item_count']]
            if goal == "Light Gems" and self.slot_data["exclude_chest_items"] >= 2:  # 2 = just light gems, 3 = both
                id_list = id_list[:-15]
            if goal == "Dragon Eggs" and self.slot_data["exclude_chest_items"] in [1, 3]:  # 1 = just eggs, 3 = both
                id_list = id_list[:-16]
            
            if not self.finished_goals[finished_index]:
                done, new_output = await self.check_goal_component(goal, id_list, option_name, last_one)
                self.finished_goals[finished_index] = done
                if new_output != "": output.append(new_output)
            
        # tally goes +1 when a goal component is met. If that value matches however many goals there are, we're done!
        if self.goal_tally == self.goal_target:
            logger.info(f"All goals are complete, nice work! The client should recognize your full goal status momentarily.")
            await self.send_msgs([{"cmd": "StatusUpdate", "status": ClientStatus.CLIENT_GOAL}])
            return True
        else:
            if len(output) > 0:
                logger.info(f"You've completed the following goal(s): {", ".join(output)}! Run /check_goal for info on what's left to do.")
            return False

    async def check_goal_component(self, goal: str, loc_id_list: list[int], option_name: str, last_one: bool) -> tuple[bool, str]:
        count = 0
        # find how many ids need to be checked
        if goal in ["Gnasty Gnorc", "Ineptune", "Red"]: amount = 2
        elif "Elder" in goal or goal == "Mecha-Red": amount = 1
        elif goal in ["Sgt. Byrd", "Blink", "Turret", "Sparx"]: amount = self.slot_data["minigames_goal_count"]
        else: amount = self.slot_data[option_name]
        for goal_id in loc_id_list:
            if goal_id in self.checked_locations:
                count += 1
        
        if count >= amount:
            self.goal_tally += 1
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
                    logger.info("Client disconnected")
                    await self.emu_client.disconnect()
                    return

                try:
                    await asyncio.wait_for(self.watcher_event.wait(), 1.0)
                except asyncio.TimeoutError:
                    pass
                self.watcher_event.clear()

                if await self.emu_client.should_process_checks():
                    # done here to ensure it's only all set up once connected
                    if not self.goal_stuff_setup:
                        self.goals_dict = self.slot_data['goals_dict']
                        self.goal_target = len(self.goals_dict.keys())
                        self.goal_stuff_setup = True
                        
                    if self.slot_data["death_link"] > 0:
                        await self._send_deathlink()
                    await self._receive_items()
                    await self._check_doors()
                    await self._location_checks()
                    await self._location_scouts()
                    if self.event_flag and tracker_loaded:
                        await self.emu_client.update_pause_gems(self._in_logic_events)
                    if self.loc_flag and tracker_loaded:
                        await self.emu_client.update_tracker(self._in_logic_locations)
                    if not has_goaled:
                        has_goaled = await self.check_goal()
        except Exception:
            logger.error("ERROR IN EMULATOR LOOP, PLEASE REPORT IN THE THREAD", exc_info=True)
    
    async def _send_deathlink(self):
        death_id = await self.emu_client.export_deathlink()
        if death_id:
            if death_id < 0 or death_id > 27:
                raise TypeError(f"Invalid outgoing deathlink id: {death_id}.")
            await self.send_death(consts.DEATHLINK_MESSAGES[death_id-1].format(name=self.player_names[self.slot]))

    async def _receive_deathlink(self, msg: str):
        self.emu_client.msg_queue.put_nowait((consts.COLOUR_RED, msg))
        await self.emu_client.import_deathlink(self.slot_data['death_link'])
    
    def on_deathlink(self, data: dict) -> None:
        Utils.async_start(self._receive_deathlink(data.get('cause') or f"{data['source']} died."))

    async def shutdown(self):
        if self.emu_loop:
            self.emu_loop.cancel()
        if self.emu_client:
            await self.emu_client.disconnect()
        return await super().shutdown()