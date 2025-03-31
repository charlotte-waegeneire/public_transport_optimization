import enum


class DayCategoryEnum(enum.Enum):
    JOHV = "JOHV"  # business day outside school holidays
    SAHV = "SAHV"  # saturday outside school holidays
    JOVS = "JOVS"  # business day in school holidays
    SAVS = "SAVS"  # saturday in school holidays
    DIJFP = "DIJFP"  # sunday, bank holidays and other special days
