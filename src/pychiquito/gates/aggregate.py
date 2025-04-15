from chiquito.dsl import Circuit, StepType
from chiquito.cb import eq
from chiquito.util import F
from .common.gteq import GreaterEqVerifier

from utils.hash import hash_to_u64

class AggregateConditionVerifier(StepType):
    def setup(self):
        self.constr(eq(self.circuit.agg_condition_hash - self.circuit.agg_result_hash, 0))

    def wg(self, input):
        self.assign(self.circuit.agg_condition_hash, F(input["agg_condition_hash"]))
        self.assign(self.circuit.agg_result_hash, F(input["agg_result_hash"]))

class AggregateTotalConditionVerifier(StepType):
    def setup(self):
        self.constr(eq(self.circuit.total_computed - self.circuit.total_aggregate, 0))

    def wg(self, input):
        self.assign(self.circuit.total_computed, F(input["total_computed"]))
        self.assign(self.circuit.total_aggregate, F(input["total_aggregate"]))

class AggregateVerificationCircuit(Circuit):
    def __init__(self, max_steps):
        self.max_steps = max_steps
        super().__init__()

    def setup(self):
        self.agg_condition_hash = self.shared("agg_condition_hash")
        self.agg_result_hash = self.shared("agg_result_hash")
        self.total_computed = self.shared("total_computed")
        self.total_aggregate = self.shared("total_aggregate")

        self.total_aggregate_check_step = self.step_type(AggregateTotalConditionVerifier(self, "total_aggregate_check_step"))
        self.aggregate_check_step = self.step_type(AggregateConditionVerifier(self, "aggregate_check_step"))
        self.aggregate_gteq_step = self.step_type(GreaterEqVerifier(self, "aggregate_gteq_step"))
        self.pragma_num_steps(self.max_steps)

    def trace(self, agg_condition, agg_result):       
        # Constrain aggregation vars in condition appearing in the result
        self.add(self.total_aggregate_check_step, {
            "total_computed": len(agg_condition),
            "total_aggregate": len(agg_result)
        })

        # Constrain aggregation having at least 1 calculated
        self.add(self.aggregate_gteq_step, len(agg_condition), 1)
        self.add(self.aggregate_gteq_step, len(agg_result), 1)
        self.add(self.aggregate_gteq_step, len(agg_condition), len(agg_result))

        # Constrain aggregate condition elements appearing in results
        agg_condition.sort()
        agg_result.sort()
        if len(agg_result) == len(agg_condition):
            for i in range(len(agg_result)):
                agg_condition_hash = hash_to_u64(agg_condition[i])
                agg_result_hash = hash_to_u64(agg_result[i])

                self.add(self.aggregate_check_step, {
                    "agg_condition_hash": agg_condition_hash,
                    "agg_result_hash": agg_result_hash
                })