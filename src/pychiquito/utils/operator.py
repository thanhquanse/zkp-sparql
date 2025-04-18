import operator, re

def apply_operator(a, op_str, b):
    ops = {
        "==": operator.eq,
        "=": operator.eq,
        "!=": operator.ne,
        ">": operator.gt,
        "<": operator.lt,
        ">=": operator.ge,
        "<=": operator.le,
        "*": operator.mul,
        "+": operator.add,
        "-": operator.sub,
        "/": operator.truediv,
        "%": operator.mod,
        "regex_i": lambda a, b: re.search(rf"{b}", a, re.IGNORECASE) is not None
    }
    return ops[op_str](a, b)