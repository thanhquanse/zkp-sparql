from chiquito.dsl import Circuit, StepType
from chiquito.cb import eq, lteq
from chiquito.util import F

class LtEqStepType(StepType):
    def setup(self):
        self.constr(eq(self.circuit.bitcheck - F(1), 0))

    def wg(self, check):
        self.assign(self.circuit.bitcheck, F(check))

class LtEqCircuit(Circuit):
    def setup(self):
        self.bitcheck = self.shared("bitcheck")

        self.lteq_check = self.step_type(LtEqStepType(self, "lteq_comparator"))

        self.pragma_num_steps(2)

    def trace(self, a, b):
        rs = lteq(a, b)
        self.add(self.lteq_check, rs)

circuit = LtEqCircuit()
circuit_instance = circuit.gen_witness(2, 3)
circuit.halo2_mock_prover(witness=circuit_instance)