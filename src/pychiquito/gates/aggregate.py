import statistics

from collections import defaultdict
from chiquito.dsl import Circuit, StepType
from chiquito.cb import eq
from chiquito.util import F
from .common.gteq import GreaterEqVerifier

from utils.hash import hash_to_u64
from constants.aggregate import AggregateOperations

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

    def trace(self, agg_condition, agg_groupby, agg_orginal_vals, agg_result):
        # TODO: Hardcoded 1 groupby var
        category_groups = defaultdict(list)
        for item in agg_orginal_vals:
            category_groups[item[agg_groupby]].append(item)

        for agg_operator in agg_condition:
            if agg_operator['name'] == AggregateOperations.COUNT.value:
                count_var = agg_operator['vars']
                count_res = agg_operator['res']

                for category in category_groups:
                    category_count = sum(count_var in item for item in category_groups[category])
                    for result in agg_result:
                        if any(value == category for value in result.values()):
                            self.add(self.aggregate_check_step, {
                                "agg_condition_hash": category_count,
                                "agg_result_hash": int(result[count_res])
                            })
                            break

            elif agg_operator['name'] == AggregateOperations.SUM.value:
                sum_var = agg_operator['vars']
                sum_res = agg_operator['res']
                
                for category in category_groups:
                    category_sum = sum(float(item[sum_var]) for item in category_groups[category])
                    for result in agg_result:
                        if any(value == category for value in result.values()):
                            self.add(self.aggregate_check_step, {
                                "agg_condition_hash": hash_to_u64(category_sum),
                                "agg_result_hash": hash_to_u64(float(result[sum_res]))
                            })
                            break
                            
            elif agg_operator['name'] == AggregateOperations.MAX.value:
                max_var = agg_operator['vars']
                max_res = agg_operator['res']

                for category in category_groups:
                    category_max = max(float(item[max_var]) for item in category_groups[category])
                    for result in agg_result:
                        if any(value == category for value in result.values()):
                            self.add(self.aggregate_check_step, {
                                "agg_condition_hash": hash_to_u64(category_max),
                                "agg_result_hash": hash_to_u64(float(result[max_res]))
                            })
                            break
            
            elif agg_operator['name'] == AggregateOperations.MIN.value:
                min_var = agg_operator['vars']
                min_res = agg_operator['res']

                for category in category_groups:
                    category_min = min(float(item[min_var]) for item in category_groups[category])
                    for result in agg_result:
                        if any(value == category for value in result.values()):
                            self.add(self.aggregate_check_step, {
                                "agg_condition_hash": hash_to_u64(category_min),
                                "agg_result_hash": hash_to_u64(float(result[min_res]))
                            })
                            break

            elif agg_operator['name'] == AggregateOperations.AVG.value:
                avg_var = agg_operator['vars']
                avg_res = agg_operator['res']

                for category in category_groups:
                    category_avg = statistics.mean(float(item[avg_var]) for item in category_groups[category])
                    for result in agg_result:
                        if any(value == category for value in result.values()):
                            self.add(self.aggregate_check_step, {
                                "agg_condition_hash": hash_to_u64(category_avg),
                                "agg_result_hash": hash_to_u64(float(result[avg_res]))
                            })
                            break
                            
            elif agg_operator['name'] == AggregateOperations.SAMPLE.value:
                sample_var = agg_operator['vars']
                sample_res = agg_operator['res']

                for category in category_groups:
                    category_sample = category
                    for result in agg_result:
                        if any(value == category for value in result.values()):
                            self.add(self.aggregate_check_step, {
                                "agg_condition_hash": hash_to_u64(category_sample), # due to str possibility
                                "agg_result_hash": hash_to_u64(result[sample_res]) # due to str possibility
                            })
                            break
            else:
                raise ValueError(f"Error: {agg_operator['name']} not supported")

        # Constrain aggregation having at least 1 calculated
        self.add(self.aggregate_gteq_step, len(agg_condition), 1)
        self.add(self.aggregate_gteq_step, len(agg_result), 1)

        # Constrain aggregate condition elements appearing in results
        agg_condition_res_list = [item['res'] for item in agg_condition].sort()
        for rs in agg_result:
            agg_result_res_list = list(rs.keys()).sort()

            agg_condition_hash = hash_to_u64(agg_condition_res_list)
            agg_result_hash = hash_to_u64(agg_result_res_list)

            self.add(self.aggregate_check_step, {
                    "agg_condition_hash": agg_condition_hash,
                    "agg_result_hash": agg_result_hash
            })