import operator, re
import rdflib
from typing import Any, Dict
from .util import is_datetime, to_datetime

def apply_operator(a, op_str, b):
    if op_str not in ['regex_i', 'Builtin_EXISTS', 'Builtin_NOTEXISTS']:
        if is_datetime(a) and is_datetime(b):
            a = to_datetime(a)
            b = to_datetime(b)
        else:
            a = float(a)
            b = float(b)
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
        "regex_i": lambda a, b: re.search(rf"{b}", a, re.IGNORECASE) is not None,
        "Builtin_EXISTS": lambda a, b : all(x in a for x in b) is True,
        "Builtin_NOTEXISTS": lambda a, b: all(x in a for x in b) is False
    }
    return ops[op_str](a, b)

def evaluate_expression(expr: Dict[str, Any], data: Dict[str, Any]) -> float:
    def resolve(term: Any) -> float:
        if isinstance(term, rdflib.term.Variable):
            return float(data.get(str(term), 0))
        elif isinstance(term, rdflib.term.Literal):
            return float(term.toPython())
        elif isinstance(term, (int, float)):
            return float(term)
        return float(term)

    # Base value
    result = resolve(expr['expr'])

    # Apply all operations
    for op, other_expr in zip(expr.get('op', []), expr.get('other', [])):
        right = evaluate_expression(other_expr, data) if isinstance(other_expr, dict) else resolve(other_expr)
        
        result = apply_operator(result, op, right)
    
    return result