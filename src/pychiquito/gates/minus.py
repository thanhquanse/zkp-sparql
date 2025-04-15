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
        self.constr(eq(self.circuit.total_computed - self.circuit.total_minus, 0))

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
        self.pragma_num_steps(self.max_steps)

    def trace(self, p2, result):
        p2_common = sorted(list(set(result) & set(p2)))
        p2_set = sorted(set(p2))

        self.add(self.minus_gteq_check_step, len(p2_common), 0)
        self.add(self.minus_gteq_check_step, len(p2_set), 0)
        self.add(self.minus_gteq_check_step, len(result), len(p2_common))

        if len(p2_common) == len(result):
            for i in range(len(p2_set)):
                p_common_hash = hash_to_u64(p2_common[i])
                p_set_hash = hash_to_u64(result[i])

                self.add(self.minus_check_step, {
                    "p_common_hash": p_common_hash,
                    "p_set_hash": p_set_hash
                })
        
        min_val = min(len(p2), len(result))
        for i in range(min_val):
            p_common_hash = hash_to_u64(p2[i])
            p_set_hash = hash_to_u64(result[i])

            self.add(self.minus_noteq_check_step, p_common_hash, p_set_hash)