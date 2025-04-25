from enum import  IntEnum
from typing import Optional, NamedTuple, Tuple, Dict, List
from math import ceil
import struct
from logging import Logger
from time import sleep

from .pcsx2_interface.pine import Pine
from .data.Constants import ADDRESSES, LEVELS

class Sly1Episode(IntEnum):
    Paris = 0
    Tide_Of_Terror = 1
    Sunset_Snake_Eyes = 2
    Vicious_Voodoo = 3
    Fire_In_The_Sky = 4
    Cold_Heart_Of_Hate = 5

class GameInterface():
    """
    Base class for connecting with a pcsx2 game
    """

    pcsx2_interface: Pine = Pine()
    logger: Logger
    game_id_error: Optional[str] = None
    current_game: Optional[str] = None
    addresses: Dict = {}

    def __init__(self, logger) -> None:
        self.logger = logger

    def _read8(self, address: int):
        return self.pcsx2_interface.read_int8(address)

    def _read16(self, address: int):
        return self.pcsx2_interface.read_int16(address)

    def _read32(self, address: int):
        return self.pcsx2_interface.read_int32(address)

    def _read_bytes(self, address: int, n: int):
        return self.pcsx2_interface.read_bytes(address, n)

    def _read_float(self, address: int):
        return struct.unpack("f",self.pcsx2_interface.read_bytes(address, 4))[0]

    def _write8(self, address: int, value: int):
        self.pcsx2_interface.write_int8(address, value)

    def _write16(self, address: int, value: int):
        self.pcsx2_interface.write_int16(address, value)

    def _write32(self, address: int, value: int):
        self.pcsx2_interface.write_int32(address, value)

    def _write_bytes(self, address: int, value: bytes):
        self.pcsx2_interface.write_bytes(address, value)

    def _write_float(self, address: int, value: float):
        self.pcsx2_interface.write_float(address, value)

    def _write_u32(self, address: int, value: int):
        value = value & 0xFFFFFFFF  # truncate to 32-bit unsigned
        value_bytes = value.to_bytes(4, byteorder='little', signed=False)
        self._write_bytes(address, value_bytes)

    def _write_u64(self, address: int, value: int):
        if value < 0 or value > 0xFFFFFFFFFFFFFFFF:
            raise ValueError(f"Value {value} out of range for unsigned 64-bit write.")
        value_bytes = value.to_bytes(8, byteorder='little', signed=False)
        self._write_bytes(address, value_bytes)

    def connect_to_game(self):
        """
        Initializes the connection to PCSX2 and verifies it is connected to the
        right game
        """
        if not self.pcsx2_interface.is_connected():
            self.pcsx2_interface.connect()
            if not self.pcsx2_interface.is_connected():
                return
            self.logger.info("Connected to PCSX2 Emulator")
        try:
            game_id = self.pcsx2_interface.get_game_id()
            # The first read of the address will be null if the client is faster than the emulator
            self.current_game = None
            if game_id in ADDRESSES.keys():
                self.current_game = game_id
                self.addresses = ADDRESSES[game_id]
            if self.current_game is None and self.game_id_error != game_id and game_id != b'\x00\x00\x00\x00\x00\x00':
                self.logger.warning(
                    f"Connected to the wrong game ({game_id})")
                self.game_id_error = game_id
        except RuntimeError:
            pass
        except ConnectionError:
            pass

    def disconnect_from_game(self):
        self.pcsx2_interface.disconnect()
        self.current_game = None
        self.logger.info("Disconnected from PCSX2 Emulator")

    def get_connection_state(self) -> bool:
        try:
            connected = self.pcsx2_interface.is_connected()
            return connected and self.current_game is not None
        except RuntimeError:
            return False

class Sly1Interface(GameInterface):
    def get_current_episode(self) -> Sly1Episode:
        episode_num = self._read32(self.addresses["world id"])
        return Sly1Episode(episode_num)

    def in_cutscene(self) -> bool:
        cutscene_pointer = self._read32(self.addresses["cutscene pointer"])
        sly_control = self._read32(self.addresses["sly control"])
        return cutscene_pointer > 0 and sly_control != 7

    def in_call(self) -> bool:
        binocucom = self._read32(self.addresses["binocucom"])
        return binocucom == 2

    def in_fmv(self) -> bool:
        fmv = self._read32(self.addresses["FMV"])
        return fmv > 20

    def skip_cutscene(self) -> None:
        if self.in_cutscene():
            cutscene_pointer = self._read32(self.addresses["cutscene pointer"])
            self._write32(cutscene_pointer + 744, 0)
        if self.in_call():
            self._write32(self.addresses["binocucom"], 0)
        if self.in_fmv():
            self._write32(self.addresses["FMV skip"], 0)

    def get_current_level_name(self) -> str:
        level_addresses = ADDRESSES["SCUS-97198"]["levels"]
        current_address = self.get_current_address()
        current_episode = self.get_current_episode()

        if current_episode in (Sly1Episode.Paris, Sly1Episode.Cold_Heart_Of_Hate) or current_address == 8:
            return "N/A"

        episode_index = current_episode - 1
        episode_levels = level_addresses[episode_index]

        return LEVELS[current_episode.name.replace("_", " ")][current_address]

    def get_current_address(self) -> int:
        current_address = self._read32(self.addresses["level id"])
        return current_address

    def check_paris_files(self) -> bool:
        files = self._read32(0x27C66C)
        return files > 0
