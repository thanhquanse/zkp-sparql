from chiquito.dsl import Circuit, StepType
from chiquito.cb import eq
from chiquito.util import F
from .common.gteq import GreaterEqVerifier

from utils.util import word_to_int_order

class OrderByConditionVerifier(StepType):
    def setup(self):
        self.constr(eq(
            (1 - self.circuit.direction) * (self.circuit.current - self.circuit.next - self.circuit.slack) + 
            self.circuit.direction * (self.circuit.next - self.circuit.current - self.circuit.slack), 0)
        )
        self.constr(eq(self.circuit.direction * (1 - self.circuit.direction), 0))  # Direction is boolean (0 or 1)

    def wg(self, current, next, direction, slack):
        self.assign(self.circuit.current, F(current))
        self.assign(self.circuit.next, F(next))
        self.assign(self.circuit.direction, F(direction))
        self.assign(self.circuit.slack, F(slack))

class OrderByVerificationCircuit(Circuit):
    def __init__(self, max_steps):
        self.max_steps = max_steps
        super().__init__()

    def setup(self):
        self.current = self.forward("current")
        self.next = self.forward("next")

        self.direction = self.shared("direction")
        self.slack = self.shared("slack")

        self.orderby_check_step = self.step_type(OrderByConditionVerifier(self, "orderby_check_step"))
        self.orderby_gteq_step = self.step_type(GreaterEqVerifier(self, "orderby_gteq_step"))
        self.pragma_num_steps(self.max_steps)

    def trace(self, sorted_values, fields, direction):
        # TODO: Temporarily hardcode 1 sort field
        field = fields[0]
        sorted_list_items = [item[field] for item in sorted_values]
        sorted_list = word_to_int_order(sorted_list_items, direction)

        for i in range((len(sorted_list) - 1)):
            current = sorted_list[i]
            next = sorted_list[i + 1]

            if direction == 1:  # ASC
                slack = max(0, next - current)  # current <= next
            else:  # DESC
                slack = max(0, current - next)  # next <= current

            self.add(self.orderby_check_step, current, next, direction, slack)
            # Slack is non-negative
            self.add(self.orderby_gteq_step, slack, 0)