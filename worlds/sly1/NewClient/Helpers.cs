using Archipelago.Core.Util;
using Archipelago.Core;
using Newtonsoft.Json;
using SlyAP.Models;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Text;
using System.Threading.Tasks;
using Location = Archipelago.Core.Models.Location;

namespace SlyAP
{
    public class Helpers
    {
        public static int StealthyApproachItems { get; set; }
        public static int IntoTheMachineItems { get; set; }
        public static int HighClassHeistItems { get; set; }
        public static int FireDownBelowItems { get; set; }
        public static int CunningDisguiseItems { get; set; }
        public static int GunboatGraveyardItems { get; set; }
        public static int RockyStartItems { get; set; }
        public static int BoneyardCasinoItems { get; set; }
        public static int BackAlleyHeistItems { get; set; }
        public static int StraightToTheTopItems { get; set; }
        public static int TwoToTangoItems { get; set; }
        public static int DreadSwampPathItems { get; set; }
        public static int LairOfTheBeastItems { get; set; }
        public static int GraveUndertakingItems { get; set; }
        public static int DescentIntoDangerItems { get; set; }
        public static int PerilousAscentItems { get; set; }
        public static int FlamingTempleItems { get; set; }
        public static int UnseenFoeItems { get; set; }
        public static int DuelByTheDragonItems { get; set; }
        public static int StealthyApproachBottles { get; set; }
        public static int StealthyApproachMax { get; set; } = 20;
        public static int IntoTheMachineBottles { get; set; }
        public static int IntoTheMachineMax { get; set; } = 30;
        public static int HighClassHeistBottles { get; set; }
        public static int HighClassHeistMax { get; set; } = 30;
        public static int FireDownBelowBottles { get; set; }
        public static int FireDownBelowMax { get; set; } = 30;
        public static int CunningDisguiseBottles { get; set; }
        public static int CunningDisguiseMax { get; set; } = 30;
        public static int GunboatGraveyardBottles { get; set; }
        public static int GunboatGraveyardMax { get; set; } = 20;
        public static int RockyStartBottles { get; set; }
        public static int RockyStartMax { get; set; } = 40;
        public static int BoneyardCasinoBottles { get; set; }
        public static int BoneyardCasinoMax { get; set; } = 40;
        public static int StraightToTheTopBottles { get; set; }
        public static int StraightToTheTopMax { get; set; } = 40;
        public static int TwoToTangoBottles { get; set; }
        public static int TwoToTangoMax { get; set; } = 30;
        public static int BackAlleyHeistBottles { get; set; }
        public static int BackAlleyHeistMax { get; set; } = 30;
        public static int DreadSwampPathBottles { get; set; }
        public static int DreadSwampPathMax { get; set; } = 20;
        public static int LairOfTheBeastBottles { get; set; }
        public static int LairOfTheBeastMax { get; set; } = 30;
        public static int GraveUndertakingBottles { get; set; }
        public static int GraveUndertakingMax { get; set; } = 40;
        public static int DescentIntoDangerBottles { get; set; }
        public static int DescentIntoDangerMax { get; set; } = 40;
        public static int PerilousAscentBottles { get; set; }
        public static int PerilousAscentMax { get; set; } = 30;
        public static int FlamingTempleBottles { get; set; }
        public static int FlamingTempleMax { get; set; } = 25;
        public static int UnseenFoeBottles { get; set; }
        public static int UnseenFoeMax { get; set; } = 30;
        public static int DuelByTheDragonBottles { get; set; }
        public static int DuelByTheDragonMax { get; set; } = 40;
        public static List<Level> Levels = new()
            {
                new Level("Stealthy Approach", "Level", 0x2027C67C, 10020400, 10020030, StealthyApproachItems, StealthyApproachBottles, StealthyApproachMax, 0x2027C6E0, 0x20247B98),
                new Level("Into the Machine", "Level", 0x2027C7E4, 10020420, 10020031, IntoTheMachineItems, IntoTheMachineBottles, IntoTheMachineMax, 0x2027C848, 0x20247C1C),
                new Level("High Class Heist", "Level", 0x2027C76C, 10020450, 10020032, HighClassHeistItems, HighClassHeistBottles, HighClassHeistMax, 0x2027C7D0, 0x20247BF0),
                new Level("Fire Down Below", "Level", 0x2027C8D4, 10020480, 10020033, FireDownBelowItems, FireDownBelowBottles, FireDownBelowMax, 0x2027C938, 0x20247C74),
                new Level("Cunning Disguise", "Level", 0x2027C85C, 10020510, 10020034, CunningDisguiseItems, CunningDisguiseBottles, CunningDisguiseMax, 0x2027C8C0, 0x20247C48),
                new Level("Gunboat Graveyard", "Level", 0x2027C9C4, 10020540, 10020035, GunboatGraveyardItems, GunboatGraveyardBottles, GunboatGraveyardMax, 0x2027CA28, 0x20247CCC),
                new Level("Rocky Start", "Level", 0x2027CAC8, 10020560, 10020036, RockyStartItems, RockyStartBottles, RockyStartMax, 0x2027CB2C, 0x20247D24),
                new Level("Boneyard Casino", "Level", 0x2027CBB8, 10020600, 10020037, BoneyardCasinoItems, BoneyardCasinoBottles, BoneyardCasinoMax, 0x2027CC1C, 0x20247D7C),
                new Level("Back Alley Heist", "Level", 0x2027CE10, 10020710, 10020038, BackAlleyHeistItems, BackAlleyHeistBottles, BackAlleyHeistMax, 0x2027CDFC, 0x20247E58),
                new Level("Straight to the Top", "Level", 0x2027CD98, 10020640, 10020039, StraightToTheTopItems, StraightToTheTopBottles, StraightToTheTopMax, 0x2027CD84, 0x20247E2C),
                new Level("Two to Tango", "Level", 0x2027CD20, 10020680, 10020040, TwoToTangoItems, TwoToTangoBottles, TwoToTangoMax, 0x2027CE74, 0x20247E00),
                new Level("Dread Swamp Path", "Level", 0x2027CF14, 10020740, 10020041, DreadSwampPathItems, DreadSwampPathBottles, DreadSwampPathMax, 0x2027CF78, 0x20247EB0),
                new Level("Lair of the Beast", "Level", 0x2027D004, 10020760, 10020042, LairOfTheBeastItems, LairOfTheBeastBottles, LairOfTheBeastMax, 0x2027D068, 0x20247F08),
                new Level("Grave Undertaking", "Level", 0x2027D07C, 10020790, 10020043, GraveUndertakingItems, GraveUndertakingBottles, GraveUndertakingMax, 0x2027D0E0, 0x20247F34),
                new Level("Descent into Danger", "Level", 0x2027D16C, 10020830, 10020044, DescentIntoDangerItems, DescentIntoDangerBottles, DescentIntoDangerMax, 0x2027D1D0, 0x20247F8C),
                new Level("Perilous Ascent", "Level", 0x2027D360, 10020870, 10020045, PerilousAscentItems, PerilousAscentBottles, PerilousAscentMax, 0x2027D3C4, 0x2024803C),
                new Level("Flaming Temple of Flame", "Level", 0x2027D450, 10020930, 10020046, FlamingTempleItems, FlamingTempleBottles, FlamingTempleMax, 0x2027D4B4, 0x20248094),
                new Level("Unseen Foe", "Level", 0x2027D4C8, 10020900, 10020047, UnseenFoeItems, UnseenFoeBottles, UnseenFoeMax, 0x2027D52C, 0x202480C0),
                new Level("Duel by the Dragon", "Level", 0x2027D630, 10020955, 10020048, DuelByTheDragonItems, DuelByTheDragonBottles, DuelByTheDragonMax, 0x2027D694, 0x20248144),
                new Level("Tide of Terror", "Hub", 0x2027C67C, 0, 0, 0, 0, 0, 0, 0x20274434),
                new Level("Sunset Snake Eyes", "Hub", 0x2027CAC8, 0, 0, 0, 0, 0, 0, 0x20274438),
                new Level("Vicious Voodoo", "Hub", 0x2027CF14, 0, 0, 0, 0, 0, 0, 0x2027443C),
                new Level("Fire in the Sky", "Hub", 0x2027D360, 0, 0, 0, 0, 0, 0, 0x20274440)
            };

        public static string[] bentley = { "Sly1AP.Bentley.Bentley1.wav", "Sly1AP.Bentley.Bentley2.wav", "Sly1AP.Bentley.Bentley3.wav", "Sly1AP.Bentley.Bentley4.wav",
                                               "Sly1AP.Bentley.Bentley5.wav", "Sly1AP.Bentley.Bentley6.wav", "Sly1AP.Bentley.Bentley7.wav", "Sly1AP.Bentley.Bentley8.wav",
                                               "Sly1AP.Bentley.Bentley9.wav", "Sly1AP.Bentley.Bentley10.wav", "Sly1AP.Bentley.Bentley11.wav", "Sly1AP.Bentley.Bentley12.wav",
                                               "Sly1AP.Bentley.Bentley13.wav", "Sly1AP.Bentley.Bentley14.wav", "Sly1AP.Bentley.Bentley15.wav"};
        public static void SendBottles(List<Level> Levels, ArchipelagoClient Client)
        {
            ulong CurrentLevel = Memory.ReadUInt(0x202623C8) + 0x20000000;
            Level? LevelObj = Levels.FirstOrDefault(x => x.Address == CurrentLevel);
            CurrentLevel += 0x68;
            if ((Memory.ReadByte(0x202623C4) == 0 || Memory.ReadByte(0x26202023C4) == 5) || LevelObj == null)
            {
                return;
            }
            int CurrentBit = 0;
            int TotalBottles = 0;
            for (int i = 0; i < LevelObj.MaxBottles; i++)
            {
                if (Memory.ReadBit(CurrentLevel, CurrentBit))
                {
                    TotalBottles++;
                    {
                        Location BottleLoc = new Location
                        {
                            Name = LevelObj.Name + " Bottle #" + TotalBottles,
                            Id = LevelObj.BottleId + TotalBottles - 1,
                        };
                        if (BottleLoc.Id < LevelObj.BottleId)
                        {
                            return;
                        }
                        if (!Client.GameState.CompletedLocations.Any(l => l.Id == BottleLoc.Id))
                        {
                            Client.SendLocation(BottleLoc);
                        }
                    }
                }
                CurrentBit++;
                if (CurrentBit == 8)
                {
                    CurrentBit = 0;
                    CurrentLevel++;
                }
            }
            Task.Delay(100);
            return;
        }
        public static List<Archipelago.Core.Models.Location> GetLocations()
        {
            var json = OpenEmbeddedResource("SlyAP.Resources.Locations.json");
            var list = JsonConvert.DeserializeObject<List<Archipelago.Core.Models.Location>>(json);
            return list;
        }
        public static string OpenEmbeddedResource(string resourceName)
        {
            var assembly = Assembly.GetExecutingAssembly();
            using (Stream stream = assembly.GetManifestResourceStream(resourceName))
            using (StreamReader reader = new StreamReader(stream))
            {
                string file = reader.ReadToEnd();
                return file;
            }
        }
    }
}
