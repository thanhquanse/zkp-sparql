from collections import defaultdict
from chiquito.dsl import Circuit, StepType
from chiquito.cb import eq
from chiquito.util import F
from .common.gteq import GreaterEqVerifier

from utils.hash import hash_to_u64

class GroupByConditionVerifier(StepType):
    def setup(self):
        self.constr(eq(self.circuit.indices_list_hash - self.circuit.indices_group_hash, 0))

    def wg(self, input):
        self.assign(self.circuit.indices_list_hash, F(input["indices_list_hash"]))
        self.assign(self.circuit.indices_group_hash, F(input["indices_group_hash"]))

class GroupByVerificationCircuit(Circuit):
    def __init__(self, max_steps):
        self.max_steps = max_steps
        super().__init__()

    def setup(self):
        self.indices_list_hash = self.shared("indices_list_hash")
        self.indices_group_hash = self.shared("indices_group_hash")

        self.groupby_check_step = self.step_type(GroupByConditionVerifier(self, "groupby_check_step"))
        self.groupby_gteq_step = self.step_type(GreaterEqVerifier(self, "groupby_gteq_step"))
        self.pragma_num_steps(self.max_steps)

    def trace(self, groupby, result):
        # Extract groupby fields
        groupby_arr = []
        for rs in result:
            groupby_arr.append(rs[groupby])

        # Build a dictionary of indices for each value
        index_map = defaultdict(list)
        for idx, name in enumerate(groupby_arr):
            index_map[name].append(idx)
        
        # Check if indices are consecutive (grouped together)
        # def is_grouped(indices):
        #     return indices == list(range(min(indices), max(indices) + 1))
        
        for name, indices in index_map.items():
            group_indices = list(range(min(indices), max(indices) + 1))

            self.add(self.groupby_gteq_step, min(indices), 0)
            self.add(self.groupby_gteq_step, max(indices), 0)
            self.add(self.groupby_gteq_step, max(indices), min(indices))
            self.add(self.groupby_check_step, {
                "indices_list_hash": hash_to_u64(indices),
                "indices_group_hash": hash_to_u64(group_indices)
            })