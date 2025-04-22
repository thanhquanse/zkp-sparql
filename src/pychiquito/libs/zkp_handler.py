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

from utils.util import find_next_stage

class ZKPHandler:
    def __init__(self, stage_dict):
        self.stage_dict = stage_dict
        self.k = 17

    def build(self):
        stage_orders = self.stage_dict.keys()
        for stage in stage_orders:
            stage_name = self.stage_dict[stage]['name']
            stage_results = self.stage_dict[stage]['value']

            if stage_name != "BGP":
                print(f"Proving results of the stage {stage_name}...")
            if stage_name == "Filter":
                total_steps = len(stage_results) * 2 + 3 # +3 for greater than constraint
                filter_condition = self.stage_dict[stage]['condition']
                
                filter_circuit = FilterVerificationCircuit(max_steps=total_steps)
                # TODO: Should check the original data
                filter_circuit_witness = filter_circuit.gen_witness(stage_results, stage_results, filter_condition)
                
                filter_circuit.halo2_mock_prover(witness=filter_circuit_witness, k=self.k)

            elif stage_name == "Union":
                total_steps = len(self.stage_dict[stage]['value']) + 8 # +8 for greater than constraint
                p1 = self.stage_dict[stage]['condition']['p1']
                p2 = self.stage_dict[stage]['condition']['p2']
                
                union_circuit = UnionVerificationCircuit(max_steps=total_steps)
                union_circuit_instance = union_circuit.gen_witness(p1, p2, stage_results)
                
                union_circuit.halo2_mock_prover(witness=union_circuit_instance, k=self.k)

            elif stage_name == "OrderBy":
                total_steps = len(self.stage_dict[stage]['value']) * 2
                
                orderby_circuit_asc = OrderByVerificationCircuit(max_steps=total_steps)

                # TODO: Temporarily hardcode one orderby '1' condition
                direction = self.stage_dict[stage]['condition']['1']['value']
                field = self.stage_dict[stage]['condition']['1']['expr']

                order = int(direction is None or direction == 'ASC' or direction == 'asc')
                    
                orderby_circuit_instance_asc = orderby_circuit_asc.gen_witness(stage_results, [field], order)  # 0 for ASC
                orderby_circuit_asc.halo2_mock_prover(witness=orderby_circuit_instance_asc, k=self.k)

            elif stage_name == "Slice":
                total_steps = 4
                start = int(self.stage_dict[stage]['condition']['start'])
                length = int(self.stage_dict[stage]['condition']['len'])

                slice_circuit = SliceVerificationCircuit(max_steps=total_steps)

                slice_circuit_instance = slice_circuit.gen_witness(start, length, stage_results)
                slice_circuit.halo2_mock_prover(witness=slice_circuit_instance, k=self.k)

            elif stage_name == "AggregateJoin":
                _condition = self.stage_dict[stage]['condition']

                condition = _condition['agg']
                groupby = _condition['op']
                vals_before = _condition['value']

                total_steps = len(condition) * 13 + 4 # +4 for greater than constraint
                
                agg_circuit = AggregateVerificationCircuit(max_steps=total_steps)

                agg_circuit_instance = agg_circuit.gen_witness(condition, groupby, vals_before, stage_results)
                agg_circuit.halo2_mock_prover(witness=agg_circuit_instance, k=self.k)

            elif stage_name == "Group":
                # pass
                total_steps = 1
                # TODO: Check more than 3 groupby vars
                groupby = self.stage_dict[stage]['condition']['groupby']

                groupby_circuit = GroupByVerificationCircuit(max_steps=total_steps)
                groupby_result_instance = groupby_circuit.gen_witness(groupby, stage_results)

                groupby_circuit.halo2_mock_prover(witness=groupby_result_instance, k=self.k)

            elif stage_name == "Distinct":
                distinct_circuit = DistinctVerificationCircuit(max_steps=2)
                distinct_circuit_instance = distinct_circuit.gen_witness(stage_results)
                
                distinct_circuit.halo2_mock_prover(witness=distinct_circuit_instance, k=self.k)

            elif stage_name == "LeftJoin":
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
                optional_circuit = OptionalVerificationCircuit(max_steps=total_steps)
                optional_circuit_instance = optional_circuit.gen_witness(p1_grouped, p2_grouped, value_grouped)

                optional_circuit.halo2_mock_prover(witness=optional_circuit_instance, k=self.k)

            elif stage_name == "Minus":
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
                minus_circuit = MinusVerificationCircuit(max_steps=total_steps) 
                minus_circuit_instance = minus_circuit.gen_witness(p2_grouped, value_grouped)
                minus_circuit.halo2_mock_prover(witness=minus_circuit_instance, k=self.k)

            elif stage_name == "Project" or stage_name == "AskQuery":
                if stage_name == "AskQuery":
                    # AsKQuery does not actually return data, it relies on Project
                    pos, _ = find_next_stage(self.stage_dict, stage_name, "Project")
                    print(f"Found Project stage at {pos}")

                    stage_results = self.stage_dict[pos]['value']

                project_vars = self.stage_dict[stage]['condition']['pv']

                total_steps = len(stage_results) + 2 # +2 for greater than constraint
                project_circuit = ProjectVerificationCircuit(max_steps=total_steps)
                project_circuit_instance = project_circuit.gen_witness(project_vars, stage_results)
                project_circuit.halo2_mock_prover(witness=project_circuit_instance, k=self.k)

            elif stage_name == "BGP":
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

            elif stage_name == "Extend":
                condition = self.stage_dict[stage]['condition']

                total_steps = len(stage_results)
                extend_circuit = ExtendVerificationCircuit(max_steps=total_steps)
                extend_circuit_instance = extend_circuit.gen_witness(condition, stage_results)

                extend_circuit.halo2_mock_prover(witness=extend_circuit_instance, k=self.k)

            elif stage_name == "ToMultiSet":
                pass

            elif stage_name == "Join":
                pass

            else:
                raise ValueError(f"Not supported the stage {stage_name}")
