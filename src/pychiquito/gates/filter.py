from chiquito.dsl import Circuit, StepType
from chiquito.cb import eq
from chiquito.util import F
from .common.gteq import GreaterEqVerifier

from enums.filter import FilterEnum
from utils.operator import apply_operator
from utils.hash import hash_to_number
from utils.util import find_common_variables, group_by_variable, group_by_keys, is_datetime, to_timestamp

class FilterConditionVerifier(StepType):
    def setup(self):
        self.constr(eq((self.circuit.field_check - self.circuit.condition) * (1 - self.circuit.flag), 0))
        self.constr(eq(self.circuit.flag * (1 - self.circuit.flag), 0))

    def wg(self, input):
        self.assign(self.circuit.field_check, F(input["field_check"]))
        self.assign(self.circuit.condition, F(input["condition"]))
        self.assign(self.circuit.flag, input["flag"])

class FilterTotalComputedVerifier(StepType):
    def setup(self):
        self.constr(eq(self.circuit.total_computed - self.circuit.total_filtered, 0))

    def wg(self, input):
        self.assign(self.circuit.total_computed, F(input["total_computed"]))
        self.assign(self.circuit.total_filtered, F(input["total_filtered"]))

class FilterComputationVerifier(StepType):
    def setup(self):
        self.constr(eq(self.circuit.hashed_triple_computed - self.circuit.hashed_triple_filtered, 0))

    def wg(self, input):
        self.assign(self.circuit.hashed_triple_computed, F(input["hashed_triple_computed"]))
        self.assign(self.circuit.hashed_triple_filtered, F(input["hashed_triple_filtered"]))

# Circuit: Prove the filtered list is correct
class FilterVerificationCircuit(Circuit):
    def __init__(self, max_steps):
        self.max_steps = max_steps
        super().__init__()

    def setup(self):
        self.field_check = self.shared("field_check")
        self.condition = self.shared("condition")
        self.flag = self.shared("flag")

        self.total_computed = self.shared("total_computed")
        self.total_filtered = self.shared("total_filtered")

        self.hashed_triple_computed = self.shared("hashed_triple_computed")
        self.hashed_triple_filtered = self.shared("hashed_triple_filtered")

        self.condition_check_step = self.step_type(FilterConditionVerifier(self, "condition_check_step"))
        self.total_computed_check_step = self.step_type(FilterTotalComputedVerifier(self, "total_computed_check_step"))
        self.computation_check_step = self.step_type(FilterComputationVerifier(self, "computation_check_step"))
        self.filter_gteq_step = self.step_type(GreaterEqVerifier(self, "filter_gteq_step"))
        self.pragma_num_steps(self.max_steps)
    
    def trace(self, prev_values, filtered, condition):
        match condition['op']:
            case FilterEnum.BUILTIN_EXISTS.value | FilterEnum.BUILTIN_NOT_EXISTS.value:
                vars_set = condition['expr']
                operator = condition['op']
                vars_set_values = condition['value']
                target_intersect_vars = find_common_variables(vars_set, filtered)

                vars_set_values_group = group_by_variable(vars_set_values)
                filtered_values_group = group_by_keys(prev_values)

                for var in target_intersect_vars:
                    # Condition: the intersected values must (NOT) be in the filtered result values
                    # Logic 1: if existing => actual - expected = 0
                    # Logic 2: if not existing => actual - expected != 0
                    flag = int(apply_operator(vars_set_values_group[var], operator, filtered_values_group[var]))
                    expected_filter_hash = hash_to_number(sorted(vars_set_values_group[var]))
                    actual_filter_hash = hash_to_number(sorted(filtered_values_group[var]))

                    self.add(self.condition_check_step, {
                            "field_check": actual_filter_hash,
                            "condition": expected_filter_hash,
                            "flag": flag
                        })
            case _:
                target = condition['expr']
                operator = condition['op']
                other = condition['value']

                # Step 1: Process original triples and collect hashes
                computed_hashes = []
                for element in prev_values:
                    # subject, predicate, object = triple

                    field_check = element[target]
                    checker = other
                    flag = int(apply_operator(field_check, operator, checker))
                    hashed_triple = hash_to_number(element)
                    if flag:
                        computed_hashes.append(hashed_triple)
                
                # Step 2: Process filtered triples and check against original
                # Also constrain the filtering condition
                filtered_hashes = []
                for element in filtered:
                    field_check = element[target]
                    checker = other
                    flag = int(apply_operator(field_check, operator, checker))
                    hashed_triple = hash_to_number(element)
                    if flag:
                        filtered_hashes.append(hashed_triple)
                    
                    if operator == '=':
                        self.add(self.condition_check_step, {
                            "field_check": hash_to_number(field_check),
                            "condition": hash_to_number(checker),
                            "flag": flag,  # Must pass filter
                        })
                    elif operator == '>' or operator == '>=':
                        if is_datetime(field_check) and is_datetime(checker):
                            field_check = to_timestamp(field_check)
                            checker = to_timestamp(checker)
                        # a, b => Constrain b >= a
                        self.add(self.filter_gteq_step, int(checker), int(field_check))
                    elif operator == '<' or operator == '<=':
                        if is_datetime(field_check) and is_datetime(checker):
                            field_check = to_timestamp(field_check)
                            checker = to_timestamp(checker)
                        self.add(self.filter_gteq_step, int(field_check), int(checker))

                # Step 3: Constrain the total expected items == the total filtered items
                self.add(self.total_computed_check_step, {
                    "total_computed": len(computed_hashes),
                    "total_filtered": len(filtered_hashes)
                })

                # Constrain >= 0
                self.add(self.filter_gteq_step, 0, len(computed_hashes))
                self.add(self.filter_gteq_step, 0, len(filtered_hashes))
                
                # Step 4: Constrain filtered hashes to match expected
                if len(computed_hashes) == len(filtered_hashes):
                    computed_hashes.sort()
                    filtered_hashes.sort()
                    
                    for i in range(len(computed_hashes)):
                        self.add(self.computation_check_step, {
                            "hashed_triple_computed": computed_hashes[i],
                            "hashed_triple_filtered": filtered_hashes[i],
                        })
