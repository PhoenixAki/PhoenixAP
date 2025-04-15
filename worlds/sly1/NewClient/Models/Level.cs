using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace SlyAP.Models
{
    public class Level
    {
        public string Name { get; set; }
        public string LevelType { get; set; }
        public ulong Address { get; set; }
        public int BottleId { get; set; }
        public int BottleItemId { get; set; }
        public int ItemBottles { get; set; }
        public int Bottles { get; set; }
        public int MaxBottles { get; set; }
        public ulong BottleWriteLoc { get; set; }
        public ulong NamePointer { get; set; }

        public Level(string name, string levelType, ulong address, int bottleId, int bottleItemId, int itemBottles, int bottles, int maxBottles, ulong bottleWriteLoc, ulong namePointer)
        {
            Name = name;
            LevelType = levelType;
            Address = address;
            BottleId = bottleId;
            BottleItemId = bottleItemId;
            ItemBottles = itemBottles;
            Bottles = bottles;
            MaxBottles = maxBottles;
            BottleWriteLoc = bottleWriteLoc;
            NamePointer = namePointer;
        }
    }
}
