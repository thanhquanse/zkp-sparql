from chiquito.dsl import Circuit, StepType
from chiquito.cb import eq
from chiquito.util import F
from .common.gteq import GreaterEqVerifier

from utils.hash import hash_to_u64

class DistinctConditionVerifier(StepType):
    def setup(self):
        self.constr(eq(self.circuit.total_computed - self.circuit.total_distinct, 0))

    def wg(self, input):
        self.assign(self.circuit.total_computed, F(input["total_computed"]))
        self.assign(self.circuit.total_distinct, F(input["total_distinct"]))

class DistinctVerificationCircuit(Circuit):
    def __init__(self, max_steps):
        self.max_steps = max_steps
        super().__init__()

    def setup(self):
        self.total_computed = self.shared("total_computed")
        self.total_distinct = self.shared("total_distinct")

        self.distinct_check_step = self.step_type(DistinctConditionVerifier(self, "distinct_check_step"))
        self.distinct_gteq_step = self.step_type(GreaterEqVerifier(self, "distinct_gteq_step"))
        self.pragma_num_steps(self.max_steps)

    def trace(self, result):
        # Convert to set to ensure the content is still the same when comparing
        result_set = {tuple(d.items()) for d in result}
        distinct_set = set(tuple(sorted(d.items())) for d in result)

        self.add(self.distinct_gteq_step, len(distinct_set), 1)
        self.add(self.distinct_check_step, {
            "total_computed": len(result),
            "total_distinct": len(distinct_set)
        })

        # Normalize to ensure the order does not impact the hashing results
        normalized_result_set = [tuple(sorted(t)) for t in result_set]
        normalized_result_set.sort()
        normalized_distinct_set = [tuple(sorted(t)) for t in distinct_set]
        normalized_distinct_set.sort()

        self.add(self.distinct_check_step, {
            "total_computed": hash_to_u64(normalized_result_set),
            "total_distinct": hash_to_u64(normalized_distinct_set)
        })
