from chiquito.dsl import Circuit, StepType
from chiquito.cb import eq, mseq
from chiquito.util import F
from .common.gteq import GreaterEqVerifier

from utils.hash import hash_to_number

class OptionalConditionVerifier(StepType):
    def setup(self):
        self.constr(eq(self.circuit.p_common_hash - self.circuit.p_set_hash, 0))

    def wg(self, input):
        self.assign(self.circuit.p_common_hash, F(input["p_common_hash"]))
        self.assign(self.circuit.p_set_hash, F(input["p_set_hash"]))

class OptionalTotalComputedVerifier(StepType):
    def setup(self):
        self.constr(eq(self.circuit.total_computed - self.circuit.total_optional, 0))

    def wg(self, input):
        self.assign(self.circuit.total_computed, F(input["total_computed"]))
        self.assign(self.circuit.total_optional, F(input["total_optional"]))

class OptionalVerificationCircuit(Circuit):
    def __init__(self, max_steps):
        self.max_steps = max_steps
        super().__init__()

    def setup(self):
        self.p_common_hash = self.shared("p_common_hash")
        self.p_set_hash = self.shared("p_set_hash")
        self.total_computed = self.shared("total_computed")
        self.total_optional = self.shared("total_optional")

        self.total_optional_check_step = self.step_type(OptionalTotalComputedVerifier(self, "total_optional_check_step"))
        self.optional_check_step = self.step_type(OptionalConditionVerifier(self, "optional_check_step"))
        self.optional_gteq_check_step = self.step_type(GreaterEqVerifier(self, "optional_gteq_check_step"))
        self.pragma_num_steps(self.max_steps)


    def trace(self, p1, p2, result):
        # Step 1: Constrain the distinct result fields == the distinct set of p1 and p2 fields
        p1_obtained_vars = list(p1.keys())
        # p2_obtained_vars = list(p2.keys())
        # common_vars = set(p1_obtained_vars + p2_obtained_vars)

        # Constrain >= 0
        self.add(self.optional_gteq_check_step, 0, len(p1_obtained_vars))
        # self.add(self.optional_gteq_check_step, 0, len(p2_obtained_vars))

        # # a, b => Constrain b >= a
        # self.add(self.optional_gteq_check_step, min(len(p1_obtained_vars), len(p2_obtained_vars)), len(result.keys()))

        # common_vars_hash = hash_to_number(common_vars)
        # result_vars_hash = hash_to_number(set(list(result.keys())))
        # self.add(self.optional_check_step, {
        #     "p_common_hash": common_vars_hash,
        #     "p_set_hash": result_vars_hash
        # })

        # # Step 2: Constrain p1 vars
        # sorted_p1 = {key: sorted(value) for key, value in p1.items()}
        # p1_common = {}
        # for key in p1:
        #     if key in result:
        #         values1_1 = set(p1[key])
        #         values2_1 = set(result[key])
        #         common_1 = values1_1 & values2_1
        #         if common_1:
        #             p1_common[key] = list(common_1)
        
        # sorted_p1_common = {key: sorted(value) for key, value in p1_common.items()}

        # self.add(self.total_optional_check_step, {
        #     "total_computed": len(list(sorted_p1_common.keys())),
        #     "total_optional": len(list(sorted_p1.keys()))
        # })
        # self.add(self.optional_gteq_check_step, len(list(sorted_p1_common.keys())), len(list(sorted_p1.keys())))

        # if len(list(sorted_p1_common)) != len(list(sorted_p1.keys())):
        #     raise ValueError("Error: lhs - the number of values is not satisfied")
        
        # for key in sorted_p1_common.keys():
        #     # The values in result should exist in BGP p1
        #     # BGP p1 is a raw list (no operations applied) of triples in the graph DB
        #     existed_in_result_1 = set(sorted_p1_common[key]) & set(result[key])
        #     p_common_hash_1 = hash_to_number(sorted_p1_common[key])
        #     p_set_hash_1 = hash_to_number(existed_in_result_1)

        #     self.add(self.optional_check_step, {
        #             "p_common_hash": p_common_hash_1,
        #             "p_set_hash": p_set_hash_1
        #     })

        # Step 3: Constrain p2 vars
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

        self.add(self.total_optional_check_step, {
            "total_computed": len(list(sorted_p2_common.keys())),
            "total_optional": len(list(sorted_p2.keys()))
        })
        # a, b => Constrain b >= a
        self.add(self.optional_gteq_check_step, len(list(sorted_p2.keys())), len(list(sorted_p2_common.keys())))

        if len(list(sorted_p2_common)) != len(list(sorted_p2.keys())):
            raise ValueError("Error: rhs - the number of values is not satisfied")
        
        for key in sorted_p2_common.keys():
            # The values in result should exist in BGP p2
            # BGP p2 is a raw list (no operations applied) of triples in the graph DB
            existed_in_result_2 = sorted(set(sorted_p2_common[key]) & set(result[key]))
            p_common_hash_2 = hash_to_number(sorted_p2_common[key])
            p_set_hash_2 = hash_to_number(existed_in_result_2)

            self.add(self.optional_check_step, {
                    "p_common_hash": p_common_hash_2,
                    "p_set_hash": p_set_hash_2
            })

def sparql_like_optional(data):
    """
    General SPARQL-like optional (left outer join) for two sources of flattened RDF-like data.
    
    Input format:
        data = {0: [single-key dicts], 1: [single-key dicts]}
    
    Each source is a flat sequence of dictionaries, each containing exactly one key-value pair.
    Consecutive entries sharing the same key (variable) but with different values belong to different rows.
    
    The function:
    - Automatically parses each source into rows (dictionaries of variable → value)
    - Performs a left optional join:
        • Includes all rows from the left source
        • For each left row, extends with compatible rows from the right source (if any)
        • Compatibility: agree on values for variables bound in both
        • If no compatible right rows, include the left row as-is
        • If multiple compatible right rows, produce multiple extended rows (duplicating left)
    - Handles unbound variables (missing keys in rows) correctly per SPARQL semantics
    - If no shared variables: cross product (all left extended with all right)
    - Fully general: no hardcoded variable names
    
    :param data: dict mapping 0 (left) and 1 (right) to lists of single-key dicts
    :return: list of merged solution mappings (dicts)
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
    
    result_rows = []
    
    for left_row in left_rows:
        matched = False
        for right_row in right_rows:
            # Check compatibility: agree on overlapping bound variables
            overlapping_vars = set(left_row.keys()) & set(right_row.keys())
            conflict = False
            for var in overlapping_vars:
                if left_row[var] != right_row[var]:
                    conflict = True
                    break
            if conflict:
                continue
            
            # Merge: union of bindings
            merged = left_row.copy()
            for var, val in right_row.items():
                if var not in merged:
                    merged[var] = val
                # No need to check equality again, as conflicts already checked
            
            result_rows.append(merged)
            matched = True
        
        if not matched:
            result_rows.append(left_row.copy())
    
    # Sort for deterministic, readable output (by sorted variables and values)
    def sort_key(row):
        return tuple(sorted((var, str(val)) for var, val in row.items()))
    
    result_rows.sort(key=sort_key)
    
    return result_rows