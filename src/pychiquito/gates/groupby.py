from collections import defaultdict
from chiquito.dsl import Circuit, StepType
from chiquito.cb import eq
from chiquito.util import F

from utils.util import is_grouped_by, group_by_fields
from utils.hash import hash_to_number

class GroupByConditionVerifier(StepType):
    def setup(self):
        self.constr(eq(self.circuit.is_grouped * (1 - self.circuit.is_grouped), 0))

    def wg(self, input):
        self.assign(self.circuit.is_grouped, F(input))

class GroupByContentConditionVerifier(StepType):
    def setup(self):
        self.constr(eq(self.circuit.group_expected - self.circuit.group_actual, 0))

    def wg(self, input):
        self.assign(self.circuit.group_expected, F(input["group_expected"]))
        self.assign(self.circuit.group_actual, F(input["group_actual"]))

class GroupByVerificationCircuit(Circuit):
    def __init__(self, max_steps):
        self.max_steps = max_steps
        super().__init__()

    def setup(self):
        self.is_grouped = self.shared("is_grouped")
        self.group_expected = self.shared("group_expected")
        self.group_actual = self.shared("group_actual")

        self.groupby_content_check_step = self.step_type(GroupByContentConditionVerifier(self, "groupby_content_check_step"))
        self.groupby_check_step = self.step_type(GroupByConditionVerifier(self, "groupby_check_step"))
        self.pragma_num_steps(self.max_steps)

    def trace(self, groupby, value2group, results):
        is_grouped = is_grouped_by(results, groupby)
        # Constraint 1: the results are grouped properly
        self.add(self.groupby_check_step, int(is_grouped))

        # Constraint 2: the results must ensure the correctness from the witness data
        # grouped_check = group_by_fields(value2group, groupby)
        # self.add(self.groupby_content_check_step, {
        #     "group_expected": hash_to_u64(grouped_check),
        #     "group_actual": hash_to_u64(results)
        # })