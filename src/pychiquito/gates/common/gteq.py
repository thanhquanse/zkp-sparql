from chiquito.dsl import StepType
from chiquito.cb import eq

class GreaterEqVerifier(StepType):
    def setup(self):
        self.a = self.internal("a")
        self.b = self.internal("b")
        self.d = self.internal("d")
        self.bits = [self.internal(f"bit_{i}") for i in range(64)]  # 64 bits

        # Constraints
        # 1. d = a - b
        self.constr(eq(self.d, self.a - self.b))
        # 2. d = sum(bits[i] * 2^i)
        bit_sum = sum(self.bits[i] * (1 << i) for i in range(64))
        self.constr(eq(self.d, bit_sum))
        # 3. Each bit is binary
        for bit in self.bits:
            self.constr(eq(bit * (bit - 1), 0))

    #TODO: Should implement to work with double/float
    def wg(self, a_val, b_val):
        d_val = a_val - b_val
        assert d_val >= 0, "a < b, invalid witness"
        assert d_val < (1 << 64), "d out of range"
        self.assign(self.a, a_val)
        self.assign(self.b, b_val)
        self.assign(self.d, d_val)
        for i in range(64):
            bit = (d_val >> i) & 1
            self.assign(self.bits[i], bit)