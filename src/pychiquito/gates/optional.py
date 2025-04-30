from chiquito.dsl import Circuit, StepType
from chiquito.cb import eq
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
        p2_obtained_vars = list(p2.keys())
        common_vars = set(p1_obtained_vars + p2_obtained_vars)

        # Constrain >= 0
        self.add(self.optional_gteq_check_step, 0, len(p1_obtained_vars))
        self.add(self.optional_gteq_check_step, 0, len(p2_obtained_vars))

        # a, b => Constrain b >= a
        self.add(self.optional_gteq_check_step, min(len(p1_obtained_vars), len(p2_obtained_vars)), len(result.keys()))

        common_vars_hash = hash_to_number(common_vars)
        result_vars_hash = hash_to_number(set(list(result.keys())))
        self.add(self.optional_check_step, {
            "p_common_hash": common_vars_hash,
            "p_set_hash": result_vars_hash
        })

        # Step 2: Constrain p1 vars
        sorted_p1 = {key: sorted(value) for key, value in p1.items()}
        p1_common = {}
        for key in p1:
            if key in result:
                values1_1 = set(p1[key])
                values2_1 = set(result[key])
                common_1 = values1_1 & values2_1
                if common_1:
                    p1_common[key] = list(common_1)
        
        sorted_p1_common = {key: sorted(value) for key, value in p1_common.items()}

        self.add(self.total_optional_check_step, {
            "total_computed": len(list(sorted_p1_common.keys())),
            "total_optional": len(list(sorted_p1.keys()))
        })
        self.add(self.optional_gteq_check_step, len(list(sorted_p1_common.keys())), len(list(sorted_p1.keys())))

        if len(list(sorted_p1_common)) != len(list(sorted_p1.keys())):
            raise ValueError("Error: lhs - the number of values is not satisfied")
        
        for key in sorted_p1_common.keys():
            # The values in result should exist in BGP p1
            # BGP p1 is a raw list (no operations applied) of triples in the graph DB
            existed_in_result_1 = set(sorted_p1_common[key]) & set(result[key])
            p_common_hash_1 = hash_to_number(sorted_p1_common[key])
            p_set_hash_1 = hash_to_number(existed_in_result_1)

            self.add(self.optional_check_step, {
                    "p_common_hash": p_common_hash_1,
                    "p_set_hash": p_set_hash_1
            })

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