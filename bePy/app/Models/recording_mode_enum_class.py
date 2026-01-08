import enum
from sqlalchemy import Enum

class RecordingMode(enum.Enum):
    CMR = "CMR"
    MOTION = "MOTION"
    ALARM = "ALARM"
    EDR = "EDR"
    ALARMANDMOTION = "ALARMANDMOTION"
    AllEvent = "AllEvent"
