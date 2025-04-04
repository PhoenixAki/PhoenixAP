using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Sly1AP.Models
{
    class Moves
    {
        public class ThiefMove
        {
            public string MoveName { get; set; }
            public int Id { get; set; }
            public uint FirstValue { get; set; }
            public uint SecondValue { get; set; }
            public uint ThirdValue { get; set; }
            public int Received { get; set; }

            public ThiefMove(string moveName, int id, uint firstValue, uint secondValue, uint thirdValue, int received)
            {
                MoveName = moveName;
                Id = id;
                FirstValue = firstValue;
                SecondValue = secondValue;
                ThirdValue = thirdValue;
                Received = received;
            }
        }

        public static List<ThiefMove> ThiefMoves = new()
            {
                new ThiefMove("Progressive Dive Attack", 10020001, 2, 16, 0, 0),
                new ThiefMove("Progressive Roll", 10020002, 4, 1024, 0, 0),
                new ThiefMove("Progressive Slow Motion", 10020003, 8, 4096, 32768, 0),
                new ThiefMove("Coin Magnet", 10020004, 32, 0, 0, 0),
                new ThiefMove("Mine", 10020005, 64, 0, 0, 0),
                new ThiefMove("Fast", 10020006, 128, 0, 0, 0),
                new ThiefMove("Progressive Safety", 1002007, 256, 16384, 0, 0),
                new ThiefMove("Decoy", 10020008, 512, 0, 0, 0),
                new ThiefMove("Hacking", 10020009, 2048, 0, 0, 0),
                new ThiefMove("Progressive Invisibility", 10020010, 65536, 8192, 0, 0),
                new ThiefMove("ToT Blueprints", 10020011, 536870912, 0, 0, 0),
                new ThiefMove("SSE Blueprints", 10020012, 1073741824, 0, 0, 0),
                new ThiefMove("VV Blueprints", 10020013, 2147483648, 0, 0, 0),
                new ThiefMove("FitS Blueprints", 10020014, 3489660928, 0, 0, 0)
            };

        public uint DiveAttack { get; set; } = 2;
        public uint Roll { get; set; } = 4;
        public uint Slow { get; set; } = 8;
        public uint Safety { get; set; } = 256;
        public int SafetyCount { get; set; } = 0;
        public uint Invisibility { get; set; } = 65536;
        public uint CoinMagnet { get; set; } = 32;
        public uint Mine { get; set; } = 64;
        public uint Fast { get; set; } = 128;
        public uint Decoy { get; set; } = 512;
        public uint Hacking { get; set; } = 2048;
        public uint RaleighBlueprint { get; set; } = 0x20000000;
        public uint MuggshotBlueprint { get; set; } = 0x40000000;
        public uint MzRubyBlueprint { get; set; } = 0x80000000;
        public uint PandaKingBlueprint { get; set; } = 0xD0000000;
    }
}
