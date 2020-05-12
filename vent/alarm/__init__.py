from enum import Enum, auto


class AlarmType(Enum):
    LOW_PRESSURE  = auto()  # low airway pressure alarm
    HIGH_PRESSURE = auto()  # high airway pressure alarm
    LOW_VTE       = auto()  # low VTE
    HIGH_VTE      = auto()
    LOW_PEEP      = auto()
    HIGH_PEEP     = auto()
    LOW_O2        = auto()
    HIGH_O2       = auto()
    OBSTRUCTION   = auto()
    LEAK          = auto()


class AlarmSeverity(Enum):
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    TECHNICAL = 1
    OFF = 0