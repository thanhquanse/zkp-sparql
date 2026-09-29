from chiquito.dsl import Circuit, StepType
from chiquito.cb import eq, mseq
from chiquito.util import F

from utils.hash import hash_to_number
from utils.operator import apply_operator
from enums.aggregate import ExpressionEnum

class ExtendConditionVerifier(StepType):
    def setup(self):
        self.constr(eq(self.circuit.expected - self.circuit.actual, 0))

    def wg(self, input):
        self.assign(self.circuit.expected, F(input["expected"]))
        self.assign(self.circuit.actual, F(input["actual"]))

class ExtendVerificationCircuit(Circuit):
    def __init__(self, max_steps):
        self.max_steps = max_steps
        super().__init__()

    def setup(self):
        self.expected = self.shared("expected")
        self.actual = self.shared("actual")

        self.extend_check_step = self.step_type(ExtendConditionVerifier(self, "extend_check_step"))
        self.pragma_num_steps(self.max_steps)

    def trace(self, input, results):
        if input['extend_op_name'] in [ExpressionEnum.MULTIPLICATIVE.value, ExpressionEnum.ADDITIVE.value]:
            var_target = str(input['var_target'])
            var_cal = str(input['var_cal'])

            for result in results:
            # Temporarily hardcode 1 operator and other at index 0
                val_cal = result[var_cal]
                op = input['op'][0]
                other = input['other'][0]
                mul_result = result[var_target]
                try:
                    val_cal = float(val_cal)
                    other = float(other)
                    mul_result = float(mul_result)
                except:
                    raise ValueError(f"Error: {other} is non-digit to convert")

                mul_cal = apply_operator(val_cal, op, other)

                self.add(self.extend_check_step, {
                    "expected": hash_to_number(mul_result), # hash due to processing float
                    "actual": hash_to_number(mul_cal)
                })





