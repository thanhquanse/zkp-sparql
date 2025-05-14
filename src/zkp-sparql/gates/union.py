from chiquito.dsl import Circuit, StepType
from chiquito.cb import eq
from chiquito.util import F
from .common.gteq import GreaterEqVerifier

from utils.hash import hash_to_number
from utils.util import normalize_data

class UnionConditionVerifier(StepType):
    def setup(self):
        self.constr(eq(self.circuit.p_common_hash - self.circuit.p_set_hash, 0))

    def wg(self, input):
        self.assign(self.circuit.p_common_hash, F(input["p_common_hash"]))
        self.assign(self.circuit.p_set_hash, F(input["p_set_hash"]))

class UnionTotalComputedVerifier(StepType):
    def setup(self):
        self.constr(eq(self.circuit.total_computed - self.circuit.total_union, 0))

    def wg(self, input):
        self.assign(self.circuit.total_computed, F(input["total_computed"]))
        self.assign(self.circuit.total_union, F(input["total_union"]))

class UnionVerificationCircuit(Circuit):
    def __init__(self, max_steps):
        self.max_steps = max_steps
        super().__init__()

    def setup(self):
        self.p_common_hash = self.shared("p_common_hash")
        self.p_set_hash = self.shared("p_set_hash")
        self.total_computed = self.shared("total_computed")
        self.total_union = self.shared("total_union")

        self.total_union_check_step = self.step_type(UnionTotalComputedVerifier(self, "total_union_check_step"))
        self.union_check_step = self.step_type(UnionConditionVerifier(self, "union_check_step"))
        self.union_gteq_check_step = self.step_type(GreaterEqVerifier(self, "union_gteq_check_step"))
        self.pragma_num_steps(self.max_steps)

    def trace(self, p1, p2, result):
        # Step 1: Constrain the total expected items == the total united items
        # self.add(self.total_union_check_step, {
        #     "total_computed": len(p1) + len(p2),
        #     "total_union": len(result)
        # })
        # self.add(self.union_gteq_check_step, len(p1) + len(p2), len(result))

        # Step 2: Constrain p1 triples
        p1_common = set(tuple(sorted(d.items())) for d in result) & set(tuple(sorted(d.items())) for d in p1) #sorted(list(set(result) & set(p1)))
        p1_set = set(tuple(sorted(d.items())) for d in p1) #sorted(set(p1))

        self.add(self.union_gteq_check_step, 0, len(p1_common))
        self.add(self.union_gteq_check_step, 0, len(p1_set))
        self.add(self.total_union_check_step, {
            "total_computed": len(p1_common),
            "total_union": len(p1_set)
        })

        # Back to list to execute further
        p1_common = normalize_data(list(p1_common))
        p1_set = normalize_data(list(p1_set))

        if len(p1_common) == len(p1_set):
            for i in range(len(p1_set)):
                p_common_hash = hash_to_number(p1_common[i])
                p_set_hash = hash_to_number(p1_set[i])

                self.add(self.union_check_step, {
                    "p_common_hash": p_common_hash,
                    "p_set_hash": p_set_hash
                })

        # Step 3: Constrain p2 triples
        p2_common = set(tuple(sorted(d.items())) for d in result) & set(tuple(sorted(d.items())) for d in p2) #sorted(list(set(result) & set(p2)))
        p2_set = set(tuple(sorted(d.items())) for d in p2) #sorted(set(p2))

        # Constrain >= 0
        self.add(self.union_gteq_check_step, 0, len(p2_common))
        self.add(self.union_gteq_check_step, 0, len(p2_set))
        self.add(self.total_union_check_step, {
            "total_computed": len(p2_common),
            "total_union": len(p2_set)
        })

        # Back to list to execute further
        p2_common = normalize_data(list(p2_common))
        p2_set = normalize_data(list(p2_set))

        if len(p2_common) == len(p2_set):
            for i in range(len(p2_set)):
                p_common_hash = hash_to_number(p2_common[i])
                p_set_hash = hash_to_number(p2_set[i])

                self.add(self.union_check_step, {
                    "p_common_hash": p_common_hash,
                    "p_set_hash": p_set_hash
                })