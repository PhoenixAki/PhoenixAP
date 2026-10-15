from enum import IntEnum

# compared in world definition against YAML. Messages that are of equal or lower log level are logged
class LoggingLevel(IntEnum):
    WARNING = 0  # 0 because warnings are always logged, even if level is set to none
    NONE = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    MAXIMUM = 5

BOSS_IDS = [27, 55, 84, 113, 142]