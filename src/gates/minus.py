from chiquito.dsl import Circuit, StepType
from chiquito.cb import eq
from chiquito.util import F
from .common.gteq import GreaterEqVerifier
from .common.noteq import NotEqualVerifier

from utils.hash import hash_to_number

class MinusConditionVerifier(StepType):
    def setup(self):
        self.constr(eq(self.circuit.p_common_hash - self.circuit.p_set_hash, 0))

    def wg(self, input):
        self.assign(self.circuit.p_common_hash, F(input["p_common_hash"]))
        self.assign(self.circuit.p_set_hash, F(input["p_set_hash"]))

class MinusTotalComputedVerifier(StepType):
    def setup(self):
        self.constr(eq(self.circuit.total_computed * self.circuit.total_minus, 0))

    def wg(self, input):
        self.assign(self.circuit.total_computed, F(input["total_computed"]))
        self.assign(self.circuit.total_minus, F(input["total_minus"]))

class MinusVerificationCircuit(Circuit):
    def __init__(self, max_steps):
        self.max_steps = max_steps
        super().__init__()

    def setup(self):
        self.p_common_hash = self.shared("p_common_hash")
        self.p_set_hash = self.shared("p_set_hash")
        self.total_computed = self.shared("total_computed")
        self.total_minus = self.shared("total_minus")

        self.minus_check_step = self.step_type(MinusConditionVerifier(self, "minus_check_step"))
        self.minus_gteq_check_step = self.step_type(GreaterEqVerifier(self, "minus_gteq_check_step"))
        self.minus_noteq_check_step = self.step_type(NotEqualVerifier(self, "minus_noteq_check_step"))
        self.minus_total_check_step = self.step_type(MinusTotalComputedVerifier(self, "minus_total_check_step"))
        self.pragma_num_steps(self.max_steps)

    def trace(self, p2, result):
        sorted_p2 = {key: sorted(value) for key, value in p2.items()}
        p2_common = {}
        for key in p2:
            if key in result:
                values1_2 = set(p2[key])
                values2_2 = set(result[key])
                common_2 = values1_2 & values2_2
                if common_2:
                    p2_common[key] = list(common_2)
        
        sorted_p2_common = {key: sorted(value) for key, value in p2_common.items()}

        # Constrain results >= 0
        self.add(self.minus_gteq_check_step, 0, len(list(sorted_p2.keys())))
        self.add(self.minus_gteq_check_step, 0, len(list(sorted_p2_common.keys())))

        # Constrain items in minus not in results
        self.add(self.minus_total_check_step, {
            "total_computed": len(list(p2_common.keys())),
            "total_minus": 0
        })
        self.add(self.minus_gteq_check_step, len(result.keys()), len(list(p2_common.keys())))

        for key in p2.keys():
            orig_p2_key_hash = hash_to_number(p2[key])
            if key in result:
                result_key_hash = hash_to_number(result[key])
            else:
                result_key_hash = hash_to_number([])
            
            self.add(self.minus_noteq_check_step, orig_p2_key_hash, result_key_hash)


def sparql_like_minus(data):
    """
    General SPARQL-like MINUS (anti-join) for two sources of flattened RDF-like data.
    
    Input format:
        data = {0: [single-key dicts], 1: [single-key dicts]}
    
    Each source is a flat sequence of dictionaries, each containing exactly one key-value pair.
    Consecutive entries sharing the same key (variable) but with different values belong to different rows.
    
    The function:
    - Automatically parses each source into rows (dictionaries of variable → value)
    - Performs a MINUS operation:
        • Includes rows from the left source that have NO compatible rows in the right source
        • Compatibility: agree on values for all shared variables (and shared variables exist)
        • If no shared variables, preserve left results unchanged (regardless of right)
        • Does not extend left rows with right variables (filters only)
    - Handles unbound variables correctly per SPARQL semantics
    - Fully general: no hardcoded variable names
    
    :param data: dict mapping 0 (left) and 1 (right) to lists of single-key dicts
    :return: list of filtered solution mappings (dicts) from left
    """
    # Step 1: Parse each source into a list of rows (dict: variable → value)
    def parse_source(lst):
        if not lst:
            return []
        
        rows = []
        current_row = {}
        
        for d in lst:
            if len(d) != 1:
                raise ValueError("Each element must be a dict with exactly one key-value pair")
            
            var, val = next(iter(d.items()))
            
            if var in current_row:
                if current_row[var] != val:
                    # Different value for the same variable → new row starts
                    rows.append(current_row)
                    current_row = {var: val}
                # else: same var + same val → redundant, ignore
            else:
                # New variable in current row
                current_row[var] = val
        
        if current_row:
            rows.append(current_row)
        
        return rows
    
    if 0 not in data:
        raise ValueError("Data must include key 0 for the left source")
    
    left_rows = parse_source(data[0])
    
    if not left_rows:
        return []
    
    right_rows = parse_source(data.get(1, []))
    
    # If right is empty, return all left (no removals)
    if not right_rows:
        result_rows = [row.copy() for row in left_rows]
    else:
        result_rows = []
        for left_row in left_rows:
            has_match = False
            for right_row in right_rows:
                # Check compatibility: agree on overlapping bound variables, but only if overlap exists
                overlapping_vars = set(left_row.keys()) & set(right_row.keys())
                if overlapping_vars:
                    conflict = any(left_row[var] != right_row[var] for var in overlapping_vars)
                    if not conflict:
                        has_match = True
                        break
            
            if not has_match:
                result_rows.append(left_row.copy())
    
    # Sort for deterministic, readable output (by sorted variables and values)
    def sort_key(row):
        return tuple(sorted((var, str(val)) for var, val in row.items()))
    
    result_rows.sort(key=sort_key)
    
    return result_rows