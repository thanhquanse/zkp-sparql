from collections import defaultdict
from chiquito.dsl import SuperCircuit

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

class ZKPSparqlSuperCircuit(SuperCircuit):
    # TODO: step_num harcoded with a large number
    def setup(self):
        # Filter circuit
        self.filter_circuit = self.sub_circuit(FilterVerificationCircuit(max_steps=self.step_num))

        # Union circuit
        self.union_circuit = self.sub_circuit(UnionVerificationCircuit(max_steps=self.step_num))

        # Orderby circuit
        self.orderby_circuit = self.sub_circuit(OrderByVerificationCircuit(max_steps=self.step_num))

        # Slice (limit/offset)
        self.slice_circuit = self.sub_circuit(SliceVerificationCircuit(max_steps=self.step_num))

        # Aggregation
        self.aggregate_circuit = self.sub_circuit(AggregateVerificationCircuit(max_steps=self.step_num))

        # Groupby circuit
        self.groupby_circuit = self.sub_circuit(GroupByVerificationCircuit(max_steps=self.step_num))

        # Distinct circuit
        self.distinct_circuit = self.sub_circuit(DistinctVerificationCircuit(max_steps=3))

        # LeftJoin (Optional) circuit
        self.optional_circuit = self.sub_circuit(OptionalVerificationCircuit(max_steps=self.step_num))

        # Minus circuit
        self.minus_circuit = self.sub_circuit(MinusVerificationCircuit(max_steps=self.step_num))

        # Project circuit
        self.project_circuit = self.sub_circuit(ProjectVerificationCircuit(max_steps=self.step_num))

        # BGP circuit
        self.bgp_circuit = self.sub_circuit(BGPVerificationCircuit(max_steps=self.step_num))

        # Extend circuit
        self.extend_circuit = self.sub_circuit(ExtendVerificationCircuit(max_steps=self.step_num))

    def mapping(self, stage_dict):
        stage_dict = self.stage_dict

        stage_orders = self.stage_dict.keys()
        for stage in stage_orders:
            stage_name = stage_dict[stage]['name']
            stage_results = self.stage_dict[stage]['value']

            match stage_name:
                case QueryExecutionStage.FILTER.value:
                    filter_condition = self.stage_dict[stage]['condition']

                    # TODO: Should check the original data
                    self.map(self.filter_circuit, stage_results, stage_results, filter_condition)

                case QueryExecutionStage.UNION.value:
                    p1 = self.stage_dict[stage]['condition']['p1']
                    p2 = self.stage_dict[stage]['condition']['p2']

                    self.map(self.union_circuit, p1, p2, stage_results)

                case QueryExecutionStage.ORDER_BY.value:
                    direction = self.stage_dict[stage]['condition']['1']['value']
                    field = self.stage_dict[stage]['condition']['1']['expr']

                    order = int(direction is None or direction == 'ASC' or direction == 'asc')

                    self.map(self.orderby_circuit, stage_results, [field], order)

                case QueryExecutionStage.SLICE.value:
                    start = int(self.stage_dict[stage]['condition']['start'])
                    length = int(self.stage_dict[stage]['condition']['len'])

                    self.map(self.slice_circuit, start, length, stage_results)

                case QueryExecutionStage.AGGREGATE.value:
                    _condition = self.stage_dict[stage]['condition']
                    has_distinct = any(entry.get("name") == "Distinct" for entry in self.stage_dict.values())
                    condition = _condition['agg']
                    groupby = _condition['op']
                    vals_before = _condition['value']

                    self.map(self.aggregate_circuit, condition, groupby, vals_before, stage_results, has_distinct)

                case QueryExecutionStage.GROUP.value:
                    # TODO: Check more than 3 groupby vars
                    groupby = self.stage_dict[stage]['condition']['groupby']
                    values2group = self.stage_dict[stage]['condition']['value']

                    self.map(self.groupby_circuit, groupby, values2group, stage_results)

                case QueryExecutionStage.DISTINCT.value:
                    self.map(self.distinct_circuit, stage_results)

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

                    self.map(self.optional_circuit, p1_grouped, p2_grouped, value_grouped)

                case QueryExecutionStage.MINUS.value:
                    p2 = self.stage_dict[stage]['condition']['p2']

                    p2_dict = defaultdict(list)
                    value_dict = defaultdict(list)

                    # Process group values by names for p2
                    for var, val in p2:
                        p2_dict[str(var)].append(str(val))
                    p2_grouped = dict(p2_dict)

                    # Process group values by names for results
                    for entry in stage_results:
                        for key, value in entry.items():
                            value_dict[key].append(value)
                    value_grouped = dict(value_dict)

                    self.map(self.minus_circuit, p2_grouped, value_grouped)

                case QueryExecutionStage.PROJECT.value | QueryType.ASK.value:
                    if stage_name == QueryType.ASK.value:
                        # AsKQuery does not actually return data, it relies on Project
                        pos, _ = find_next_stage(self.stage_dict, stage_name, QueryExecutionStage.PROJECT.value)
                        print(f"Found Project stage at {pos}")

                        stage_results = self.stage_dict[pos]['value']

                    project_vars = self.stage_dict[stage]['condition']['pv']

                    self.map(self.project_circuit, project_vars, stage_results)

                case QueryExecutionStage.BGP.value:
                    pass
                    # p = self.stage_dict[stage]['condition']['p']
                    # p_dict = defaultdict(list)
                    # value_dict = defaultdict(list)

                    # # Process group values by names for p
                    # for var, val in p:
                    #     p_dict[str(var)].append(str(val))
                    # p_grouped = dict(p_dict)

                    # # Process group values by names for results
                    # for entry in stage_results:
                    #     for key, value in entry.items():
                    #         value_dict[key].append(value)
                    # value_grouped = dict(value_dict)

                    # total_steps = len(stage_results) + 8 # +8 for greater than constraint
                    # bgp_circuit = BGPVerificationCircuit(max_steps=total_steps)
                    # bgp_circuit_instance = bgp_circuit.gen_witness(p_grouped, value_grouped)

                    # bgp_circuit.halo2_mock_prover(witness=bgp_circuit_instance, k=self.k)

                case QueryExecutionStage.EXTEND.value:
                    condition = self.stage_dict[stage]['condition']

                    self.map(self.extend_circuit, condition, stage_results)

                case QueryExecutionStage.TO_MULTISET.value:
                    pass

                case QueryExecutionStage.JOIN.value:
                    pass

                case _:
                    raise ValueError(f"Not supported the stage {stage_name}")

class ZKPSuperHandler:
    def __init__(self, stage_dict,
                 params: dict = {
                     "k": 19,
                     "param": "./proof/super_params_test.bin",
                     "paramgen": False,
                     "proof": "./proof/super_proof_test.bin",
                     "proofgen": False
                }
        ):
        self.stage_dict = stage_dict
        self.k = params["k"]
        self.param = params["param"]
        self.proof = params["proof"]
        self.paramgen = params["paramgen"]
        self.proofgen = params["proofgen"]

    def build(self):
        zkp_super_circuit = ZKPSparqlSuperCircuit(stage_dict=self.stage_dict, step_num=1100000)
        zkp_super_circuit_witness = zkp_super_circuit.gen_witness(self.stage_dict)

        zkp_super_circuit.halo2_mock_prover(zkp_super_circuit_witness, k=self.k)
        
        if self.paramgen: 
            zkp_super_circuit.create_param_file(self.param, self.k)
        
        if self.proofgen:
            zkp_super_circuit.generate_proof_file(zkp_super_circuit_witness, self.param, self.proof)