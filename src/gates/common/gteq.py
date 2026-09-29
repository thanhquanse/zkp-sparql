from chiquito.dsl import StepType
from chiquito.cb import eq, lteq
from chiquito.util import F

class GreaterEqVerifier(StepType):
    def setup(self):
        self.bitcheck = self.internal("bitcheck")

        self.constr(eq(self.bitcheck - F(1), 0))
        self.constr(eq(self.bitcheck * (self.bitcheck - 1), 0))

    def wg(self, a_val, b_val):
        # SIGMOD range check circuit
        rs = lteq(a_val, b_val)
        self.assign(self.bitcheck, rs)