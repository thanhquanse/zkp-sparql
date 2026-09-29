from enum import Enum

class FilterEnum(Enum):
    REGEX_I = "regex_i"
    BUILTIN_EXISTS = "Builtin_EXISTS"
    BUILTIN_NOT_EXISTS = "Builtin_NOTEXISTS"