from chiquito.dsl import Circuit, StepType
from chiquito.cb import eq, mseq
from chiquito.util import F
from .common.gteq import GreaterEqVerifier

# Slice for 'limit' and 'offset'
# TODO
# actual <= expected
class SliceConditionVerifier(StepType):
    def setup(self):
        self.constr(eq(self.circuit.start * (self.circuit.num_expected - self.circuit.num_actual), 0))
        # self.constr(eq(self.circuit.num_actual - self.circuit.num_expected, 0))

    def wg(self, input):
        self.assign(self.circuit.start, F(input["start"]))
        self.assign(self.circuit.num_expected, F(input['num_expected']))
        self.assign(self.circuit.num_actual, F(input['num_actual']))

class SliceVerificationCircuit(Circuit):
    def __init__(self, max_steps):
        self.max_steps = max_steps
        super().__init__()

    def setup(self):
        self.start = self.shared("start")
        self.num_expected = self.shared('num_expected')
        self.num_actual = self.shared('num_actual')

        self.slice_check_step = self.step_type(SliceConditionVerifier(self, "slice_check_step"))
        self.slice_gteq_check_step = self.step_type(GreaterEqVerifier(self, "slice_gteq_check_step"))
        self.pragma_num_steps(self.max_steps)

    def trace(self, start, slice_num, result):
        # Constrain >= 0
        self.add(self.slice_gteq_check_step, 0, slice_num)
        self.add(self.slice_gteq_check_step, 0, len(result))
        
        # Constrain actual results may be less than the expectation
        # a, b => Constrain b >= a
        self.add(self.slice_gteq_check_step, len(result), slice_num)
        self.add(self.slice_check_step, {
            "start": start,
            "num_expected": slice_num,
            "num_actual": len(result)
        })