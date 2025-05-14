from chiquito.dsl import Circuit, StepType
from chiquito.cb import eq
from chiquito.util import F
from .common.gteq import GreaterEqVerifier

from utils.hash import hash_to_number

class BGPConditionVerifier(StepType):
    def setup(self):
        self.constr(eq(self.circuit.p_common_hash - self.circuit.p_set_hash, 0))

    def wg(self, input):
        self.assign(self.circuit.p_common_hash, F(input["p_common_hash"]))
        self.assign(self.circuit.p_set_hash, F(input["p_set_hash"]))

class BGPVerificationCircuit(Circuit):
    def __init__(self, max_steps):
        self.max_steps = max_steps
        super().__init__()

    def setup(self):
        self.p_common_hash = self.shared("p_common_hash")
        self.p_set_hash = self.shared("p_set_hash")

        self.bgp_check_step = self.step_type(BGPConditionVerifier(self, "bgp_check_step"))
        self.bgp_gteq_check_step = self.step_type(GreaterEqVerifier(self, "bgp_gteq_check_step"))
        self.pragma_num_steps(self.max_steps)

    def trace(self, p, result):
        p_obtained_vars = list(p.keys())

        # Constrain >= 0
        self.add(self.bgp_gteq_check_step, 0, len(p_obtained_vars))
        self.add(self.bgp_gteq_check_step, 0, len(result.keys()), len(p_obtained_vars))

        # Step 2: Constrain p vars
        sorted_p = {key: sorted(value) for key, value in p.items()}

        p_common = {}
        for key in result.keys():
            if key in p_obtained_vars:
                values1 = set(p[key])
                values2 = set(result[key])
                common = values1 & values2
                if common:
                    p_common[key] = list(common)
        
        sorted_p_common = {key: sorted(value) for key, value in p_common.items()}
        
        for key in sorted_p_common.keys():
            p_common_hash = hash_to_number(sorted_p_common[key])
            p_set_hash = hash_to_number(sorted_p[key])

            self.add(self.bgp_check_step, {
                    "p_common_hash": p_common_hash,
                    "p_set_hash": p_set_hash
            })