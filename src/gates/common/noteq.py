from chiquito.dsl import StepType
from chiquito.cb import eq, neq
from chiquito.util import F

class NotEqualVerifier(StepType):
    def setup(self):
        self.bitcheck = self.internal("bitcheck")

        self.constr(eq(self.bitcheck - F(1), 0))
        self.constr(eq(self.bitcheck * (self.bitcheck - 1), 0))

    def wg(self, a_val, b_val):
        # SIGMOD range check circuit
        rs = neq(a_val, b_val)
        self.assign(self.bitcheck, rs)

def egcd(a, b):
    if a == 0:
        return b, 0, 1
    g, x1, y1 = egcd(b % a, a)
    x = y1 - (b // a) * x1
    y = x1
    return g, x, y

# Compute modular multiplicative inverse
def mod_inverse(a, p):
    a = a % p
    g, x, _ = egcd(a, p)
    if g != 1:
        raise ValueError("Inverse does not exist (a == b?)")
    return (x % p + p) % p

class NotEqualVerifier(StepType):
    def setup(self):
        self.a = self.internal("a")
        self.b = self.internal("b")
        self.diff = self.internal("diff")
        self.inv = self.internal("inv")
        self.constr(eq(self.diff, self.a - self.b))
        # self.constr(eq(self.diff * self.inv, 1))

    def wg(self, a_value, b_value):
        P = F.field_modulus
        a = F(a_value % P)
        b = F(b_value % P)
        diff = a - b
        diff_int = int(diff) % P
        if diff_int == 0:
            raise ValueError("a equals b, no inverse exists")
        inv_int = mod_inverse(diff_int, P)
        inv = F(inv_int)
        # Log values for clarity
        # print(f"a = {a_value}, b = {b_value}")
        # print(f"diff = a - b = {diff_int} (mod {P})")
        # print(f"inv = {inv_int} (mod {P})")
        self.assign(self.a, a)
        self.assign(self.b, b)
        self.assign(self.diff, diff)
        self.assign(self.inv, inv)