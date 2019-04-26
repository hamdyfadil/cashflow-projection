from enum import Enum

class SHEETS(Enum):
    INITIAL_CONDITIONS = "INITIAL_CONDITIONS"
    YEARLY = "YEARLY"
    MONTHLY = "MONTHLY"
    BIWEEKLY = "BIWEEKLY"
    WEEKLY = "WEEKLY"
    ONE_TIME = "ONE-TIME"
    YEARLY_HEBREW = "YEARLY-HEBREW"


class FILES(Enum):
    CONTROL: str = "CONTROL.xlsx"
    OUTPUT: str = "OUTPUT.xlsx"
