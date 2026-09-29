import time
from collections import defaultdict

from gates.filter import FilterVerificationCircuit
from gates.orderby import OrderByVerificationCircuit
from gates.optional import OptionalVerificationCircuit
from gates.union import UnionVerificationCircuit
from gates.slice import SliceVerificationCircuit
from gates.distinct import DistinctVerificationCircuit
from gates.aggregate import AggregateVerificationCircuit
from gates.groupby import GroupByVerificationCircuit
from gates.minus import MinusVerificationCircuit
from gates.project import ProjectVerificationCircuit
from gates.bgp import BGPVerificationCircuit
from gates.extend import ExtendVerificationCircuit

from enums.stages import QueryExecutionStage, QueryType

from utils.util import find_next_stage

class ZKPSingleHandler:
    def __init__(self, stage_dict):
        self.stage_dict = stage_dict
        self.k = 20

    def build(self):
        time_measurement = {
            "proving": 0,
            "param_gen": 0,
            "proof_gen": 0
        }

        stage_orders = self.stage_dict.keys()
        for stage in stage_orders:
            stage_name = self.stage_dict[stage]['name']
            stage_results = self.stage_dict[stage]['value']

            print(f"Proving results of the stage {stage_name}...")

            match stage_name:
                case QueryExecutionStage.FILTER.value:
                    total_steps = len(stage_results) * 50 + 3 # +3 for greater than constraint
                    filter_condition = self.stage_dict[stage]['condition']
                    prev_values = self.stage_dict[stage]['condition']['prev_value']
                    
                    start = time.time()

                    filter_circuit = FilterVerificationCircuit(max_steps=total_steps)
                    filter_circuit_witness = filter_circuit.gen_witness(prev_values, stage_results, filter_condition)
                    
                    filter_circuit.halo2_mock_prover(witness=filter_circuit_witness, k=self.k)
                    
                    end = time.time()
                    print(f"Proving time: {end - start}\n")
                    time_measurement["proving"] = end - start

                    start = time.time()
                    filter_circuit.create_param_file(f"./proof/param_{self.k}.bin", self.k, f"./logs/experiment_create_params.log")
                    end = time.time()
                    print(f"Param k = {self.k} generation time: {end - start}")
                    time_measurement["param_gen"] = end - start

                case QueryExecutionStage.UNION.value:
                    total_steps = len(stage_results) + 8 # +8 for greater than constraint
                    p1 = self.stage_dict[stage]['condition']['p1']
                    p2 = self.stage_dict[stage]['condition']['p2']
                    
                    start = time.time()
                    
                    union_circuit = UnionVerificationCircuit(max_steps=total_steps)
                    union_circuit_instance = union_circuit.gen_witness(p1, p2, stage_results)
                    
                    union_circuit.halo2_mock_prover(witness=union_circuit_instance, k=self.k)
                    
                    end = time.time()
                    print(f"Proving time: {end - start}\n")
                    time_measurement["proving"] = end - start

                case QueryExecutionStage.ORDER_BY.value:
                    total_steps = len(stage_results) * 2
                    
                    start = time.time()
                    
                    orderby_circuit_asc = OrderByVerificationCircuit(max_steps=total_steps)

                    # TODO: Temporarily hardcode one orderby '1' condition
                    direction = self.stage_dict[stage]['condition']['1']['value']
                    field = self.stage_dict[stage]['condition']['1']['expr']

                    order = int(direction is None or direction == 'ASC' or direction == 'asc')
                        
                    orderby_circuit_instance_asc = orderby_circuit_asc.gen_witness(stage_results, [field], order)  # 0 for ASC
                    orderby_circuit_asc.halo2_mock_prover(witness=orderby_circuit_instance_asc, k=self.k)
                    
                    end = time.time()
                    print(f"Proving time: {end - start}\n")
                    time_measurement["proving"] = end - start

                case QueryExecutionStage.SLICE.value:
                    total_steps = 4
                    start_idx = int(self.stage_dict[stage]['condition']['start'])
                    length = int(self.stage_dict[stage]['condition']['len'])

                    start = time.time()
                    
                    slice_circuit = SliceVerificationCircuit(max_steps=total_steps)

                    slice_circuit_instance = slice_circuit.gen_witness(start_idx, length, stage_results)
                    slice_circuit.halo2_mock_prover(witness=slice_circuit_instance, k=self.k)
                    
                    end = time.time()
                    print(f"Proving time: {end - start}\n")
                    time_measurement["proving"] = end - start

                case QueryExecutionStage.AGGREGATE.value:
                    _condition = self.stage_dict[stage]['condition']
                    has_distinct = any(entry.get("name") == "Distinct" for entry in self.stage_dict.values())

                    condition = _condition['agg']
                    groupby = _condition['op']
                    vals_before = _condition['value']

                    total_steps = len(stage_results) * 50 + 4 # +4 for greater than constraint
                    
                    start = time.time()
                    
                    agg_circuit = AggregateVerificationCircuit(max_steps=total_steps)

                    agg_circuit_instance = agg_circuit.gen_witness(condition, groupby, vals_before, stage_results, has_distinct)
                    agg_circuit.halo2_mock_prover(witness=agg_circuit_instance, k=self.k)
                    
                    end = time.time()
                    print(f"Proving time: {end - start}\n")
                    time_measurement["proving"] = end - start

                case QueryExecutionStage.GROUP.value:
                    total_steps = 2
                    groupby = self.stage_dict[stage]['condition']['groupby']
                    values2group = self.stage_dict[stage]['condition']['value']

                    start = time.time()
                    
                    groupby_circuit = GroupByVerificationCircuit(max_steps=total_steps)
                    groupby_result_instance = groupby_circuit.gen_witness(groupby, values2group, stage_results)

                    groupby_circuit.halo2_mock_prover(witness=groupby_result_instance, k=self.k)
                    
                    end = time.time()
                    print(f"Proving time: {end - start}\n")
                    time_measurement["proving"] = end - start

                case QueryExecutionStage.DISTINCT.value:
                    start = time.time()
                    
                    distinct_circuit = DistinctVerificationCircuit(max_steps=3)
                    distinct_circuit_instance = distinct_circuit.gen_witness(stage_results)
                    
                    distinct_circuit.halo2_mock_prover(witness=distinct_circuit_instance, k=self.k)
                    
                    end = time.time()
                    print(f"Proving time: {end - start}\n")
                    time_measurement["proving"] = end - start

                case QueryExecutionStage.OPTIONAL.value:
                    p1 = self.stage_dict[stage]['condition']['p1']
                    p2 = self.stage_dict[stage]['condition']['p2']

                    p1_dict = defaultdict(list)
                    p2_dict = defaultdict(list)
                    value_dict = defaultdict(list)

                    # Process group values by names for p1
                    for var, val in p1:
                        p1_dict[str(var)].append(str(val))
                    p1_grouped = dict(p1_dict) #[{var: values} for var, values in p1_dict.items()]

                    # Process group values by names for p2
                    for var, val in p2:
                        p2_dict[str(var)].append(str(val))
                    p2_grouped = dict(p2_dict) #[{var: values} for var, values in p2_dict.items()]

                    # Process group values by names for results
                    for entry in stage_results:
                        for key, value in entry.items():
                            value_dict[key].append(value)
                    value_grouped = dict(value_dict)

                    total_steps = (len(p1) + len(p2)) * 2 + 8 # +8 for greater than constraint
                    
                    start = time.time()
                    
                    optional_circuit = OptionalVerificationCircuit(max_steps=total_steps)
                    optional_circuit_instance = optional_circuit.gen_witness(p1_grouped, p2_grouped, value_grouped)

                    optional_circuit.halo2_mock_prover(witness=optional_circuit_instance, k=self.k)
                    
                    end = time.time()
                    print(f"Proving time: {end - start}\n")
                    time_measurement["proving"] = end - start

                case QueryExecutionStage.MINUS.value:
                    p2 = self.stage_dict[stage]['condition']['p2']

                    p2_dict = defaultdict(list)
                    value_dict = defaultdict(list)

                    # Process group values by names for p2
                    for var, val in p2:
                        p2_dict[str(var)].append(str(val))
                    p2_grouped = dict(p2_dict) #[{var: values} for var, values in p2_dict.items()]

                    # Process group values by names for results
                    for entry in stage_results:
                        for key, value in entry.items():
                            value_dict[key].append(value)
                    value_grouped = dict(value_dict)

                    total_steps = len(stage_results) * 2 + 3 # +3 for greater than constraint

                    start = time.time()
                    
                    minus_circuit = MinusVerificationCircuit(max_steps=total_steps) 
                    minus_circuit_instance = minus_circuit.gen_witness(p2_grouped, value_grouped)
                    minus_circuit.halo2_mock_prover(witness=minus_circuit_instance, k=self.k)
                    
                    end = time.time()
                    print(f"Proving time: {end - start}\n")
                    time_measurement["proving"] = end - start

                case QueryExecutionStage.PROJECT.value | QueryType.ASK.value:
                    if stage_name == QueryType.ASK.value:
                        # AsKQuery does not actually return data, it relies on Project
                        pos, _ = find_next_stage(self.stage_dict, stage_name, QueryExecutionStage.PROJECT.value)
                        print(f"Found Project stage at {pos}")

                        stage_results = self.stage_dict[pos]['value']

                    project_vars = self.stage_dict[stage]['condition']['pv']

                    total_steps = len(stage_results) + 2 # +2 for greater than constraint
                    project_circuit = ProjectVerificationCircuit(max_steps=total_steps)
                    project_circuit_instance = project_circuit.gen_witness(project_vars, stage_results)
                    project_circuit.halo2_mock_prover(witness=project_circuit_instance, k=self.k)

                    # project_circuit.create_param_file("project_params_test.bin", self.k)
                    # project_circuit.generate_proof_file(project_circuit_instance, "project_params_test.bin", "project_proof.bin")

                case QueryExecutionStage.BGP.value:
                    ctx = self.stage_dict[stage]['condition']['ctx']
                    triples = self.stage_dict[stage]['condition']['triples']

                    total_steps = len(stage_results)*100
                    bgp_circuit = BGPVerificationCircuit(max_steps=total_steps)
                    bgp_circuit_instance = bgp_circuit.gen_witness(ctx, triples, stage_results)

                    bgp_circuit.halo2_mock_prover(witness=bgp_circuit_instance, k=self.k)

                case QueryExecutionStage.EXTEND.value:
                    condition = self.stage_dict[stage]['condition']

                    total_steps = len(stage_results)
                    extend_circuit = ExtendVerificationCircuit(max_steps=total_steps)
                    extend_circuit_instance = extend_circuit.gen_witness(condition, stage_results)

                    extend_circuit.halo2_mock_prover(witness=extend_circuit_instance, k=self.k)

                case QueryExecutionStage.TO_MULTISET.value:
                    pass

                case QueryExecutionStage.JOIN.value:
                    pass

                case _:
                    raise ValueError(f"Not supported the stage {stage_name}")

        return time_measurement        