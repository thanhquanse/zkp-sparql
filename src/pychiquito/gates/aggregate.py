import statistics

from chiquito.dsl import Circuit, StepType
from chiquito.cb import eq
from chiquito.util import F
from .common.gteq import GreaterEqVerifier

from utils.hash import hash_to_number
from utils.util import group_by, check_tuple_in_flat_list
from enums.aggregate import AggregateOperations

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

    def trace(self, agg_condition, agg_groupby, agg_orginal_vals, agg_result, has_distinct):
        category_groups = group_by(agg_orginal_vals, agg_groupby['groupby'], has_distinct)

        for agg_operator in agg_condition:
            match agg_operator['name']:
                case AggregateOperations.COUNT.value:
                    count_var = agg_operator['vars']
                    count_res = agg_operator['res']

                    for category in category_groups:
                        # category_count = sum(count_var in item for item in category_groups[category])
                        category_count = len({item[count_var] for item in category_groups[category] if count_var in item})
                        for result in agg_result:
                            if check_tuple_in_flat_list(list(result.values()), category):
                                if int(category_count) != int(result[count_res]):
                                    print(f"COUNT: {category_count} + {int(result[count_res])}")
                                self.add(self.aggregate_check_step, {
                                    "agg_condition_hash": category_count,
                                    "agg_result_hash": int(result[count_res])
                                })
                                break

                case AggregateOperations.SUM.value:
                    sum_var = agg_operator['vars']
                    sum_res = agg_operator['res']
                    
                    for category in category_groups:
                        # category_sum = sum(float(item[sum_var]) for item in category_groups[category])
                        category_sum = sum(float(item[sum_var]) for item in category_groups[category] if sum_var in item and item[sum_var])
                        for result in agg_result:
                            if check_tuple_in_flat_list(list(result.values()), category):
                                if float(category_sum) != float(result[sum_res]):
                                    print(f"Sum: {category_sum} + {float(result[sum_res])}")
                                self.add(self.aggregate_check_step, {
                                    "agg_condition_hash": hash_to_number(category_sum),
                                    "agg_result_hash": hash_to_number(float(result[sum_res]))
                                })
                                break
                                
                case AggregateOperations.MAX.value:
                    max_var = agg_operator['vars']
                    max_res = agg_operator['res']

                    for category in category_groups:
                        # category_max = max(float(item[max_var]) for item in category_groups[category])
                        category_max = max(float(item[max_var]) for item in category_groups[category] if max_var in item and item[max_var])
                        for result in agg_result:
                            if check_tuple_in_flat_list(list(result.values()), category):
                                self.add(self.aggregate_check_step, {
                                    "agg_condition_hash": hash_to_number(category_max),
                                    "agg_result_hash": hash_to_number(float(result[max_res]))
                                })
                                break
                
                case AggregateOperations.MIN.value:
                    min_var = agg_operator['vars']
                    min_res = agg_operator['res']

                    for category in category_groups:
                        # category_min = min(float(item[min_var]) for item in category_groups[category])
                        category_min = min(float(item[min_var]) for item in category_groups[category] if min_var in item and item[min_var])
                        for result in agg_result:
                            if check_tuple_in_flat_list(list(result.values()), category):
                                self.add(self.aggregate_check_step, {
                                    "agg_condition_hash": hash_to_number(category_min),
                                    "agg_result_hash": hash_to_number(float(result[min_res]))
                                })
                                break

                case AggregateOperations.AVG.value:
                    avg_var = agg_operator['vars']
                    avg_res = agg_operator['res']

                    for category in category_groups:
                        # category_avg = statistics.mean(float(item[avg_var]) for item in category_groups[category])
                        category_avg = statistics.mean(float(item[avg_var]) for item in category_groups[category] if avg_var in item and item[avg_var])
                        for result in agg_result:
                            if check_tuple_in_flat_list(list(result.values()), category):
                                self.add(self.aggregate_check_step, {
                                    "agg_condition_hash": hash_to_number(category_avg),
                                    "agg_result_hash": hash_to_number(float(result[avg_res]))
                                })
                                break
                                
                case AggregateOperations.SAMPLE.value:
                    sample_var = agg_operator['vars']
                    sample_res = agg_operator['res']

                    for category in category_groups:
                        for result in agg_result:
                            if check_tuple_in_flat_list(list(result.values()), category):
                                for cat in category:
                                    if cat == result[sample_res]:
                                        self.add(self.aggregate_check_step, {
                                            "agg_condition_hash": hash_to_number(cat), # due to str possibility
                                            "agg_result_hash": hash_to_number(result[sample_res]) # due to str possibility
                                        })
                                break
                case _:
                    raise ValueError(f"Error: {agg_operator['name']} not supported")

        # Constrain aggregation having at least 1 calculated
        # Constrain >= 1
        self.add(self.aggregate_gteq_step, 1, len(agg_condition))
        self.add(self.aggregate_gteq_step, 1, len(agg_result))

        # Constrain aggregate condition elements appearing in results
        agg_condition_res_list = sorted([item['res'] for item in agg_condition])

        for rs in agg_result:
            agg_result_res_list = sorted(list(rs.keys()))

            agg_condition_hash = hash_to_number(agg_condition_res_list)
            agg_result_hash = hash_to_number(agg_result_res_list)

            self.add(self.aggregate_check_step, {
                    "agg_condition_hash": agg_condition_hash,
                    "agg_result_hash": agg_result_hash
            })