import operator, re

def apply_op(a, op_str, b):
    ops = {
        "==": operator.eq,
        "=": operator.eq,
        "!=": operator.ne,
        ">": operator.gt,
        "<": operator.lt,
        ">=": operator.ge,
        "<=": operator.le,
        "regex": lambda a, b: re.match(b, a) is not None
    }
    return ops[op_str](a, b)