from chiquito.dsl import Circuit, StepType
from chiquito.cb import eq
from chiquito.util import F
from .common.gteq import GreaterEqVerifier

from utils.operator import apply_op
from utils.hash import hash_to_u64

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
    
    def trace(self, original, filtered, condition):
        target = condition['expr']
        op = condition['op']
        other = condition['other']

        # Step 1: Process original triples and collect hashes
        computed_hashes = []
        for element in original:
            # subject, predicate, object = triple

            field_check = element[target]
            flag = int(apply_op(field_check, op, other))
            hashed_triple = hash_to_u64(element)
            if flag:
                computed_hashes.append(hashed_triple)
        
        # Step 2: Process filtered triples and check against original
        # Also constrain the filtering condition
        filtered_hashes = []
        for element in filtered:
            # subject, predicate, object = triple

            field_check = element[target]
            flag = int(apply_op(field_check, op, other))
            hashed_triple = hash_to_u64(element)
            self.add(self.condition_check_step, {
                "field_check": field_check,
                "condition": other,
                "flag": flag,  # Must pass filter
            })
            filtered_hashes.append(hashed_triple)

        # Step 3: Constrain the total expected items == the total filtered items
        self.add(self.total_computed_check_step, {
            "total_computed": len(computed_hashes),
            "total_filtered": len(filtered_hashes)
        })

        self.add(self.filter_gteq_step, len(computed_hashes), 0)
        self.add(self.filter_gteq_step, len(filtered_hashes), 0)
        
        # Step 4: Constrain filtered hashes to match expected
        if len(computed_hashes) == len(filtered_hashes):
            computed_hashes.sort()
            filtered_hashes.sort()
            
            for i in range(len(computed_hashes)):
                self.add(self.computation_check_step, {
                    "hashed_triple_computed": computed_hashes[i],
                    "hashed_triple_filtered": filtered_hashes[i],
                })
