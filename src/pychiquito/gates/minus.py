from chiquito.dsl import Circuit, StepType
from chiquito.cb import eq
from chiquito.util import F
from .common.gteq import GreaterEqVerifier
from .common.noteq import NotEqualVerifier

from utils.hash import hash_to_u64

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
        self.add(self.minus_gteq_check_step, len(list(sorted_p2.keys())), 0)
        self.add(self.minus_gteq_check_step, len(list(sorted_p2_common.keys())), 0)

        # Constrain items in minus not in results
        self.add(self.minus_total_check_step, {
            "total_computed": len(list(p2_common.keys())),
            "total_minus": 0
        })
        self.add(self.minus_gteq_check_step, len(result.keys()), len(list(p2_common.keys())))

        for key in p2.keys():
            orig_p2_key_hash = hash_to_u64(p2[key])
            if key in result:
                result_key_hash = hash_to_u64(result[key])
            else:
                result_key_hash = hash_to_u64([])
            
            self.add(self.minus_noteq_check_step, orig_p2_key_hash, result_key_hash)


        