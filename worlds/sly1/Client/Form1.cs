using Archipelago.Core.Util;
using Archipelago.Core.Models;
using Archipelago.Core.GameClients;
using Newtonsoft.Json;
using System.Media;
using System.Reflection;
using System.Text;
using System.Windows.Forms;
using static System.Windows.Forms.AxHost;
using static System.Windows.Forms.Design.AxImporter;
using Archipelago.Core;
using Sly1AP.Models;
using System.Windows;
using System.Timers;
using System.Security.Policy;
using System.Text.Json;
using System;
using System.Linq;
using static Sly1AP.Helpers;

namespace Sly1AP
{
    public partial class Form1 : Form
    {
        public static string GameVersion { get; set; } = "0";
        public static bool IsConnected { get; set; } = false;
        public static GameState CurrentGameState = new GameState();
        public static ArchipelagoClient? Client { get; set; }
        public static SlyKeys keys = new SlyKeys();
        public static uint SlyMoves { get; set; } = 0;
        public static int GameCompletion { get; set; } = 0;
        public static Random rnd = new Random();
        public static int ClueBundles { get; set; } = 0;
        public static int ClueLocations { get; set; } = 0;
        public static int MurrayTextAddress { get; set; } = 0x2024A7B0;
        public static int RequiredBosses { get; set; } = 0;
        public static int NameAddress { get; set; } = 0;
        public static int NameOffset { get; set; } = 2484736;
        public static bool DidReceive { get; set; } = false;
        public static bool DidConnect { get; set; } = false;
        public static bool NamePointersSet { get; set; } = false;
        public static List<Item> Items = new List<Item>();
        public Form1()
        {
            InitializeComponent();
            Encoding.RegisterProvider(CodePagesEncodingProvider.Instance);
            ThreadPool.SetMinThreads(500, 500);
        }
        public async Task Loop()
        {
            // Console.SetBufferSize(Console.BufferWidth, 32766);

            while (true)
            {
                UpdateValues();
                CutsceneSkip();
                UpdateBosses();
                StopAnticheat();
                if (ClueBundles > 0)
                {
                    Clues.BottleSync();
                }
                if (ClueLocations > 0 && Client != null)
                {
                    Helpers.SendBottles(Helpers.Levels, Client);
                }
                if (Memory.ReadByte(0x202623C0) == 0)
                {
                    Thread.Sleep(1000);
                    if (Memory.ReadByte(0x202623C0) == 0)
                    {
                        WriteLine("Lost connection to PCSX2. Are you using 1.6.0?");
                        return;
                    }
                }
                if (!IsConnected)
                {
                    return;
                }
                await Task.Delay(100);
            }
        }

        public async Task<bool> ConnectAsync()
        {
            if (Client != null)
            {
                Client.Connected -= OnConnected;
                Client.Disconnected -= OnDisconnected;
            }
            PCSX2Client client = new PCSX2Client();
            var pcsx2Connected = client.Connect();
            if (!pcsx2Connected)
            {
                WriteLine("Failed to connect to PCSX2.");
                return false;
            }
            WriteLine($"Connected to PCSX2.");
            WriteLine($"Connecting to Archipelago.");

            Client = new ArchipelagoClient(client);
            Client.Connected += OnConnected;
            Client.Disconnected += OnDisconnected;

            foreach (var Level in Helpers.Levels)
            {
                if (Level.LevelType == "Hub" && Memory.ReadInt(Level.Address) == 1)
                {
                    Memory.Write(Level.Address, 0);
                }
            }

            await NamePointers();
            UpdateValues();

            if (DidConnect == false)
            {
                Client.ItemReceived += async (e, args) =>
                {
                    Items.Add(args.Item);
                    WriteLine($"Received: {JsonConvert.SerializeObject(args.Item.Name)}");
                    if (args.Item.Id >= 10020001 & args.Item.Id <= 100200014)
                    {
                        UpdateMoves(args.Item.Id);
                    }
                    if (args.Item.Id >= 10020015 & args.Item.Id <= 10020018)
                    {
                        UpdateKeys(args.Item.Id);
                    }
                    if (args.Item.Id >= 10020021 & args.Item.Id <= 10020024)
                    {
                        UpdateLevels(args.Item.Id);
                    }
                    if (args.Item.Id >= 10020019 & args.Item.Id <= 10020020)
                    {
                        UpdateJunk(args.Item.Id);
                    }
                    if (args.Item.Id >= 10020026 & args.Item.Id <= 10020029)
                    {
                        UpdateTraps(args.Item.Id);
                    }
                    if (args.Item.Id == 10020025)
                    {
                        Client.SendGoalCompletion();
                    }
                    if (args.Item.Id >= 10020030 && args.Item.Id <= 10020048)
                    {
                        var tcs = new TaskCompletionSource<bool>();

                        _ = Task.Run(() =>
                        {
                            while (ClueBundles == 0)
                            {
                                Thread.Sleep(10);
                            }
                            tcs.SetResult(true);
                        });
                        await tcs.Task;

                        Clues.UpdateBottles(args.Item.Id, ClueBundles);
                    }
                    await Task.Delay(250);
                };
            }

            await Client.Connect(hostTextbox.Text, "Sly Cooper and the Thievius Raccoonus");
            if (!Client.IsConnected)
            {
                WriteLine("Couldn't connect. Check settings.");
                return false;
            }
            await Client.Login(slotTextbox.Text, passwordTextbox.Text);
            if (!Client.IsLoggedIn)
            {
                WriteLine("Couldn't connect. Check settings.");
                return false;
            }

            var PlayerName = slotTextbox.Text;

            if (DidConnect == false)
            {
                Client.MessageReceived += (e, args) =>
                {
                    string? ClientMessage = args.Message?.ToString();
                    if (ClientMessage != null && ClientMessage.Contains(PlayerName))
                    {
                        WriteLine($"{args.Message}");
                    }
                };
            }

            var locations = Helpers.GetLocations();
            Client.MonitorLocations(locations);
            ConfigureOptions(Client.Options);

            Client.MessageReceived += (e, args) =>
            {
                string? ClientMessage = args.Message?.ToString();
                if (!string.IsNullOrEmpty(ClientMessage) && ClientMessage.Contains(PlayerName))
                {
                    WriteLine($"{args.Message}");
                }
            };

            await InitialLoad(Client, Items);

            DidConnect = true;

            //Just to be sure...
            foreach (var Level in Helpers.Levels)
            {
                if (Level.LevelType == "Hub" && Client.GameState.ReceivedItems.Any(h => h.Name == Level.Name) && Memory.ReadInt(Level.Address) == 0)
                {
                    Memory.Write(Level.Address, 1);
                }
            }

            await Loop();

            return true;
        }

        private void Client_Disconnected(object? sender, ConnectionChangedEventArgs e)
        {
            throw new NotImplementedException();
        }

        public static void ConfigureOptions(Dictionary<string, object> options)
        {
            var Options = new ArchipelagoOptions();
            if (options == null)
            {
                Console.WriteLine("Options dictionary is null.");
                return;
            }
            if (options.ContainsKey("ItemCluesanityBundleSize"))
            {
                var ClueBundleSizeElement = (JsonElement)options["ItemCluesanityBundleSize"];
                ClueBundles = ClueBundleSizeElement.GetUInt16();
            }
            if (options.ContainsKey("LocationCluesanityBundleSize"))
            {
                var LocationBundleSizeElement = (JsonElement)options["LocationCluesanityBundleSize"];
                ClueLocations = LocationBundleSizeElement.GetUInt16();
            }
            if (options.ContainsKey("RequiredBosses"))
            {
                var RequiredBossesElement = (JsonElement)options["RequiredBosses"];
                RequiredBosses = RequiredBossesElement.GetUInt16();
            }
        }

        public static void UpdateMoves(long id)
        {
            var Move = Moves.ThiefMoves.FirstOrDefault(m => m.Id == id);
            if (Move != null)
            {
                Move.Received += 1;
                if (Move.Received == 1)
                {
                    SlyMoves += Move.FirstValue;
                }
                else if (Move.Received == 2)
                {
                    SlyMoves += Move.SecondValue;
                }
                else if (Move.Received == 3)
                {
                    SlyMoves += Move.ThirdValue;
                }
            }
        }
        public static void UpdateKeys(long id)
        {
            //Keys
            if (id == 10020015)
            {
                keys.RaleighKeys += 1;
                Memory.Write(0x2027CAB4, keys.RaleighKeys);
            }
            if (id == 10020016)
            {
                keys.MuggshotKeys += 1;
                Memory.Write(0x2027CF00, keys.MuggshotKeys);
            }
            if (id == 10020017)
            {
                keys.MzRubyKeys += 1;
                Memory.Write(0x2027D34C, keys.MzRubyKeys);
            }
            if (id == 10020018)
            {
                keys.PandaKingKeys += 1;
                Memory.Write(0x2027D798, keys.PandaKingKeys);
            }
            return;
        }
        public static void UpdateLevels(long id)
        {
            // Levels
            if (id == 10020021 && Memory.ReadInt(0x2027C67C) == 0)
            {
                keys.RaleighStart = 1;
                Memory.Write(0x2027C67C, keys.RaleighStart);
                var LevelName = Helpers.Levels.FirstOrDefault(l => l.Name == "Tide of Terror");
                if (LevelName != null && LevelName.NamePointer != 0)
                {
                    var PlaceToWrite = Memory.ReadUInt(LevelName.NamePointer) + 536870912;
                    Memory.Write((ulong)(PlaceToWrite + LevelName.Name.Length), 0);
                }
            }
            if (id == 10020022 && Memory.ReadInt(0x2027CAC8) == 0)
            {
                keys.MuggshotStart = 1;
                Memory.Write(0x2027CAC8, keys.MuggshotStart);
                var LevelName = Helpers.Levels.FirstOrDefault(l => l.Name == "Sunset Snake Eyes");
                if (LevelName != null && LevelName.NamePointer != 0)
                {
                    var PlaceToWrite = Memory.ReadUInt(LevelName.NamePointer) + 536870912;
                    Memory.Write((ulong)(PlaceToWrite + LevelName.Name.Length), 0);
                }
            }
            if (id == 10020023 && Memory.ReadInt(0x2027CF14) == 0)
            {
                keys.MzRubyStart = 1;
                Memory.Write(0x2027CF14, keys.MzRubyStart);
                var LevelName = Helpers.Levels.FirstOrDefault(l => l.Name == "Vicious Voodoo");
                if (LevelName != null && LevelName.NamePointer != 0)
                {
                    var PlaceToWrite = Memory.ReadUInt(LevelName.NamePointer) + 536870912;
                    Memory.Write((ulong)(PlaceToWrite + LevelName.Name.Length), 0);
                }
            }
            if (id == 10020024 && Memory.ReadInt(0x2027D360) == 0)
            {
                keys.PandaKingStart = 1;
                Memory.Write(0x2027D360, keys.PandaKingStart);
                var LevelName = Helpers.Levels.FirstOrDefault(l => l.Name == "Fire in the Sky");
                if (LevelName != null && LevelName.NamePointer != 0)
                {
                    var PlaceToWrite = Memory.ReadUInt(LevelName.NamePointer) + 536870912;
                    Memory.Write((ulong)(PlaceToWrite + LevelName.Name.Length), 0);
                }
            }
            return;
        }
        public static void UpdateJunk(long id)
        {
            //Junk
            //Don't continuously update these or else they'll never go down!
            if (id == 10020020)
            {
                var Lives = Memory.ReadInt(0x2027DC00);
                Lives += 1;
                Memory.Write(0x2027DC00, Lives);
            }
            if (id == 10020019)
            {
                var Charms = Memory.ReadInt(0x2027DC04);
                if (Charms < 2)
                {
                    Charms += 1;
                    Memory.Write(0x2027DC04, Charms);
                }
                else
                {
                    var Lives = Memory.ReadInt(0x2027DC00);
                    Lives += 1;
                    Memory.Write(0x2027DC00, Lives);
                }
            }
            return;
        }
        public static async void UpdateTraps(long id)
        {
            var TrapTimer = new System.Timers.Timer(10000);
            TrapTimer.AutoReset = false;
            //Traps
            uint SlyControl = 0x20262C68;
            if (Memory.ReadByte(SlyControl) != 7)
            {
                while (Memory.ReadByte(SlyControl) != 7)
                {
                   await Task.Delay(1000);
                }
            }
            if (id == 10020026)
            {
                TrapTimer.Start();
                if (TrapTimer.Interval != 0) // Check if the trap timer is not 0
                {
                   Memory.Write(0x20274AD0, 1060655596);
                }
                TrapTimer.Elapsed += (sender, e) =>
                {
                    Memory.Write(0x20274AD0, 0);
                    Memory.Write(0x20274AD2, -49280);
                    TrapTimer.Stop();
                    TrapTimer.Dispose();
                };
            }
            if (id == 10020027)
            {
                TrapTimer.Start();
                int random = rnd.Next(1, 3);
                if (TrapTimer.Interval != 0)
                {
                    if (random == 1)
                    {
                        Memory.Write(0x20261850, 1056964608);
                    }
                    if (random == 2)
                    {
                        Memory.Write(0x20261850, 1069547520);
                    }
                }
                TrapTimer.Elapsed += (sender, e) =>
                {
                    Memory.Write(0x20261850, 1065353216);
                    //Memory.Write(0x20261852, -128);
                    TrapTimer.Stop();
                    TrapTimer.Dispose();
                };
            }
            if (id == 10020028)
            {
                TrapTimer.Start();
                uint TrueMoves = 0;
                int TrueSelect = 0;
                if (SlyMoves != 4)
                {
                    TrueMoves = SlyMoves;
                }

                //Get the current position of Sly's data in code.
                uint SlyPos = (Memory.ReadUInt(0x20262E10) + 536870912) + 8736;
                uint BodyPos = SlyPos + 8;
                uint CanePos = SlyPos + 28;
                //Reset Sly's current action to 0.
                Memory.Write(SlyPos, 0);
                Memory.Write(BodyPos, 0);
                Memory.Write(CanePos, 0);

                //if (slyMoves.SafetyCount == 1)
                //{
                //    slyMoves.SlyMoves = 260;
                //}
                //if (slyMoves.SafetyCount == 2)
                //{
                //    slyMoves.SlyMoves = 16644;
                //}
                //else
                //{
                //    slyMoves.SlyMoves = 4;
                //}

                while (TrapTimer.Enabled == true)
                {
                    Memory.Write(0x20274F74, 1);
                    Memory.Write(0x20262D18, 16);
                    Memory.Write(0x20262D22, 0xFF);
                    Memory.Write(0x20262D1A, 16);
                    await Task.Delay(1);
                };
                TrapTimer.Elapsed += (sender, e) =>
                {
                    Memory.Write(0x20262D18, 0);
                    Memory.Write(0x20262D22, 0);
                    Memory.Write(0x20262D1A, 0);
                    Memory.Write(0x20262D1C, 0);
                };
                TrapTimer.Stop();
                TrapTimer.Dispose();
                SlyMoves = TrueMoves;
                Memory.Write(0x20274F74, TrueSelect);
                return;
            }
            if (id == 10020029)
            {
                int random = rnd.Next(Helpers.bentley.Length);
                string SoundFile = Helpers.bentley[random];
                var stream = Assembly.GetExecutingAssembly().GetManifestResourceStream(SoundFile);
                SoundPlayer player = new SoundPlayer(stream);
                player.Play();
            }
        }
        public static void UpdateValues()
        {
            Memory.Write(0x2027DC10, SlyMoves);
            Memory.Write(0x2027CAB4, keys.RaleighKeys);
            Memory.Write(0x2027CF00, keys.MuggshotKeys);
            Memory.Write(0x2027D34C, keys.MzRubyKeys);
            Memory.Write(0x2027D798, keys.PandaKingKeys);
            //Make all maps selectable.
            if (Memory.ReadInt(0x2027CAC4) == 0)
            {
                Memory.Write(0x2027CAC4, keys.Map);
            }
            if (Memory.ReadInt(0x2027CF10) == 0)
            {
                Memory.Write(0x2027CF10, keys.Map);
            }
            if (Memory.ReadInt(0x2027D35C) == 0)
            {
                Memory.Write(0x2027D35C, keys.Map);
            }
            if (Memory.ReadInt(0x2027D7A8) == 0)
            {
                Memory.Write(0x2027D7A8, keys.Map);
            }
            return;
        }
        public void WriteLine(string output)
        {
            Invoke(() =>
            {
                outputTextbox.Text += output;
                outputTextbox.Text += System.Environment.NewLine;
                outputTextbox.SelectionStart = outputTextbox.Text.Length;
                outputTextbox.ScrollToCaret();

                System.Diagnostics.Debug.WriteLine(output + System.Environment.NewLine);
            });
        }
        private void OnConnected(object? sender, EventArgs args)
        {
            WriteLine("Connected to Archipelago.");
            WriteLine($"Playing {Client?.CurrentSession.ConnectionInfo.Game} as {Client?.CurrentSession.Players.GetPlayerName(Client.CurrentSession.ConnectionInfo.Slot)}");
            Invoke(() =>
            {
                connectBtn.Text = "Disconnect";
            });
        }
        private void OnDisconnected(object? sender, EventArgs args)
        {
            WriteLine($"Disconnected from Archipelago.");
            Invoke(() =>
            {
                connectBtn.Text = "Connect";
            });
        }
        private bool ValidateSettings()
        {
            var valid = !string.IsNullOrWhiteSpace(hostTextbox.Text) && !string.IsNullOrWhiteSpace(slotTextbox.Text);
            return valid;
        }
        private async void connectBtn_Click(object sender, EventArgs e)
        {
            if (!(Client?.IsConnected ?? false))
            {
                var valid = ValidateSettings();
                if (!valid)
                {
                    WriteLine("Invalid settings, please check your input and try again.");
                    return;
                }
                await ConnectAsync().ConfigureAwait(false);
            }
            else
            {
                WriteLine("Disconnecting...");
                Client.Disconnect();
            }
        }
        private void CutsceneSkip()
        {
            //Dialogue Skipper
            uint Cutscene = Memory.ReadUInt(0x2027051C) + 0x20000000;
            uint Playing = Cutscene + 744;
            int SlyControl = Memory.ReadInt(0x20262C68);
            if (Memory.ReadUInt(Cutscene) != 0 & SlyControl != 7)
            {
                Memory.Write(Playing, 0);
            }

            //Bentley Skipper
            if (Memory.ReadInt(0x20270458) == 2)
            {
                Memory.Write(0x20270458, 0);
            }

            //FMV Skipper
            if (Memory.ReadInt(0x20269A18) > 20)
            {
                Memory.Write(0x20269A60, 0);
            }
        }
        private void UpdateBosses()
        {
            int Bosses = 0;
            if (Memory.ReadBit(0x2027DC18, 5))
            {
                Bosses += 1;
            }
            if (Memory.ReadBit(0x2027DC18, 7))
            {
                Bosses += 1;
            }
            if (Memory.ReadBit(0x2027DC19, 1))
            {
                Bosses += 1;
            }
            if (Memory.ReadBit(0x2027DC19, 3))
            {
                Bosses += 1;
            }
            if (Bosses < RequiredBosses)
            {
                Memory.WriteString(0x2024A7B0, Bosses + "/" + RequiredBosses);
                Memory.Write(0x2024A7B3, 0);
            }
            if (Bosses >= RequiredBosses)
            {
                Memory.Write(0x2027D7A8, 53);
            }
            else if (Memory.ReadByte(0x2027D7A8) >= 21)
            {
                Memory.Write(0x2027D7A8, 21);
            }
        }
        //Sly 1 has anti-piracy measures that can seriously mess with the randomizer's functionality.
        //We freeze the related flags to stop them from ever being flipped.
        //In case the Into the Machine anticheat activates, we disable the burners.
        private void StopAnticheat()
        {
            Memory.Write(0x20261080, 0);
            Memory.Write(0x20262310, 0);
            Memory.Write(0x20269B48, 0);
            Memory.Write(0x20275C34, 0);
            Memory.Write(0x2027C828, 0);
            Memory.Write(0x2027C829, 0);
            Memory.Write(0x2027C82C, 0);
            Memory.Write(0x2027C82D, 0);
        }

        private static async Task InitialLoad(ArchipelagoClient Client, List<Item> Items)
        {
            if (Client.GameState != null && Client.GameState.ReceivedItems.Count != 0 && DidReceive == false)
            {
                var ItemsReceived = Client.GameState.ReceivedItems;
                var NewItems = new List<Item>(ItemsReceived);

                // Filter out the items that are already in the Items
                var itemsToProcess = NewItems
                    .Where(item => !Items.Any(receivedItem => receivedItem.Id == item.Id))
                    .ToList();

                foreach (var item in itemsToProcess)
                {
                    for (int i = 0; i < item.Quantity; i++)
                    {
                        if (item.Id >= 10020001 && item.Id <= 10020014)
                        {
                            UpdateMoves(item.Id);
                        }
                        if (item.Id >= 10020015 && item.Id <= 10020018)
                        {
                            UpdateKeys(item.Id);
                        }
                        if (item.Id >= 10020021 && item.Id <= 10020024)
                        {
                            UpdateLevels(item.Id);
                        }
                        if (item.Id >= 10020030 && item.Id <= 10020048)
                        {
                            while (ClueBundles == 0)
                            {
                                await Task.Delay(10);
                            }
                            Clues.UpdateBottles(item.Id, ClueBundles);
                        }
                    }
                }
            }
            DidReceive = true;
            await Task.CompletedTask;
        }

        private static Task NamePointers()
        {
            foreach (var Level in Helpers.Levels)
            {
                if (Level.NamePointer == 0)
                {
                    continue;
                }
                Memory.Write(Level.NamePointer, (NameAddress + NameOffset));
                NameOffset += 50;

                if (Level.LevelType == "Hub" && (Memory.ReadInt(Level.Address) == 0))
                {
                    var PlaceToWrite = Memory.ReadUInt(Level.NamePointer) + 0x20000000;
                    Memory.WriteString(PlaceToWrite, Level.Name + " (Locked)");
                }
                else if (Level.LevelType == "Hub")
                {
                    var PlaceToWrite = Memory.ReadUInt(Level.NamePointer) + 0x20000000;
                    Memory.WriteString(PlaceToWrite, Level.Name);
                }
            }
            NamePointersSet = true;

            Clues.UpdateBottles(0, 0);

            return Task.CompletedTask;
        }
    }
}