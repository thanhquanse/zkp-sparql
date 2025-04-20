from collections import defaultdict
from chiquito.dsl import Circuit, StepType
from chiquito.cb import eq
from chiquito.util import F

from utils.util import is_grouped_by

class GroupByConditionVerifier(StepType):
    def setup(self):
        self.constr(eq(self.circuit.is_grouped * (1 - self.circuit.is_grouped), 0))

    def wg(self, input):
        self.assign(self.circuit.is_grouped, F(input))

class GroupByVerificationCircuit(Circuit):
    def __init__(self, max_steps):
        self.max_steps = max_steps
        super().__init__()

    def setup(self):
        self.is_grouped = self.shared("is_grouped")

        self.groupby_check_step = self.step_type(GroupByConditionVerifier(self, "groupby_check_step"))
        self.pragma_num_steps(self.max_steps)

    def trace(self, groupby, results):
        is_grouped = is_grouped_by(results, groupby)

        self.add(self.groupby_check_step, int(is_grouped))