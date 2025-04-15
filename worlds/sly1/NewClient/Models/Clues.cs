using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Archipelago.Core.Util;

namespace SlyAP.Models
{
    internal class Clues
    {
        public static void UpdateBottles(long Id, int Bundles)
        {
            //Increment the count. Then, multiply it by the bundle size. If it exceeds the maximum for the level, reduce it to max. Then write it to the memory address.
            var BottleUpdate = Helpers.Levels.FirstOrDefault(x => x.BottleItemId == Id);
            if (BottleUpdate != null)
            {
                BottleUpdate.ItemBottles += 1;
                BottleUpdate.Bottles = BottleUpdate.ItemBottles * Bundles;
                if (BottleUpdate.Bottles > BottleUpdate.MaxBottles)
                {
                    BottleUpdate.Bottles = BottleUpdate.MaxBottles;
                }
            }
            if (App.NamePointersSet == true)
            {
                foreach (var Level in Helpers.Levels)
                {
                    if (Level.LevelType == "Level")
                    {
                        var NameLocation = Memory.ReadUInt(Level.NamePointer) + 0x20000000;
                        Memory.WriteString(NameLocation, Level.Name + " (" + Level.Bottles + "/" + Level.MaxBottles + ") ");
                    }
                }
            }
        }
        public static void BottleSync()
        {
            foreach (var Level in Helpers.Levels)
            {
                if (Level.LevelType == "Level")
                {
                    Memory.Write(Level.BottleWriteLoc, Level.Bottles);
                }
            }
        }
    }
}
