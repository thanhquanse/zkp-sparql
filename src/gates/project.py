from chiquito.dsl import Circuit, StepType
from chiquito.cb import eq, mseq
from chiquito.util import F

from .common.gteq import GreaterEqVerifier

from utils.hash import hash_to_number

class ProjectConditionVerifier(StepType):
    def setup(self):
        self.constr(eq(self.circuit.expected_project_vars - self.circuit.actual_project_vars, 0))

    def wg(self, input):
        self.assign(self.circuit.expected_project_vars, F(input["expected_project_vars"]))
        self.assign(self.circuit.actual_project_vars, F(input["actual_project_vars"]))

class ProjectVerificationCircuit(Circuit):
    def __init__(self, max_steps):
        self.max_steps = max_steps
        super().__init__()

    def setup(self):
        self.expected_project_vars = self.shared("expected_project_vars")
        self.actual_project_vars = self.shared("actual_project_vars")

        self.project_check_step = self.step_type(ProjectConditionVerifier(self, "project_check_step"))
        self.project_gteq_check_step = self.step_type(GreaterEqVerifier(self, "project_gteq_check_step"))
        self.pragma_num_steps(self.max_steps)

    def trace(self, project_vars, results):
        sorted_project_vars = sorted(project_vars)

        # Constrain >= 1
        self.add(self.project_gteq_check_step, 1, len(project_vars))
        # With optional operator, sometimes, there is no result
        self.add(self.project_gteq_check_step, 0, len(results))

        for project_el in results:
            sort_project_el = sorted(list(project_el.keys()))
            # Intersect to ensure the vars in the results present in the projected vars
            # But due to optional, sometimes they are not
            common_vars = set(sorted_project_vars) & set(sort_project_el)

            common_vars_hash = hash_to_number(common_vars)
            sort_project_el_hash = hash_to_number(sort_project_el)

            self.add(self.project_check_step, {
                "expected_project_vars": common_vars_hash,
                "actual_project_vars": sort_project_el_hash
            })
