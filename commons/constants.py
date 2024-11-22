from enum import Enum

class CompoundFrequency(Enum):
    ANNUALLY = 1 
    SEMIANNUAL = 2
    QUARTERLY = 4
    MONTHLY = 12
    
class PaymentFrequency(Enum):
    ANNUALLY = 1
    SEMIANNUALLY = 2
    QUARTERLY = 4
    BIMONTHLY = 6
    MONTHLY = 12
    SEMIMONTHLY = 24
    BIWEEKLY = 26
    WEEKLY = 52
    
class MonthOffset(Enum):
    ANNUALLY = 12
    SEMIANNUALLY = 6
    QUARTERLY = 3
    BIMONTHLY = 2
    MONTHLY = 1
    SEMIMONTHLY = 0
    BIWEEKLY = 0
    WEEKLY = 0
    
class DayOffset(Enum):
    ANNUALLY = 0
    SEMIANNUALLY = 0
    QUARTERLY = 0
    BIMONTHLY = 0
    MONTHLY = 0
    SEMIMONTHLY = 15
    BIWEEKLY = 14
    WEEKLY = 7
    

    
    