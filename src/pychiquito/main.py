from chiquito.dsl import Circuit, StepType
from chiquito.cb import eq
from chiquito.util import F
from chiquito.chiquito_ast import Last

# Helper: Encode strings to integers (simplified)
def encode_term(term):
    mapping = {"a": 1, "b": 2, "c": 3, "e": 4, "f": 5, "g": 6, "h": 7, "i": 8}
    return mapping.get(term, 0)

# Simplified hash function (replace with Poseidon in Halo 2)
def simple_hash(s, p, o):
    return (s * 31 + p * 17 + o) % 101  # Dummy hash for triple commitment

def simple_hash_v2(tuple):
    rs = 0
    for i in range(len(tuple)):
        rs = rs + (30 + i) * tuple[i]
    
    return rs

################ FILTER ################
class FilterConditionVerifier(StepType):
    def setup(self):
        self.constr(eq((self.circuit.subject - self.circuit.condition) * (1 - self.circuit.flag), 0))
        self.constr(eq(self.circuit.flag * (1 - self.circuit.flag), 0))

    def wg(self, input):
        self.assign(self.circuit.subject, F(input["subject"]))
        self.assign(self.circuit.predicate, F(input["predicate"]))
        self.assign(self.circuit.object, F(input["object"]))
        self.assign(self.circuit.condition, F(input["condition"]))
        self.assign(self.circuit.flag, input["flag"])

class FilterTotalComputedVerifier(StepType):
    def setup(self):
        self.constr(eq(self.circuit.total_computed - self.circuit.total_filtered, 0))

    def wg(self, input):
        self.assign(self.circuit.total_computed, F(input["total_computed"]))
        self.assign(self.circuit.total_filtered, F(input["total_filtered"]))

class FilterComputationVerifier(StepType):
    def setup(self):
        self.constr(eq(self.circuit.hashed_triple_computed - self.circuit.hashed_triple_filtered, 0))

    def wg(self, input):
        self.assign(self.circuit.hashed_triple_computed, F(input["hashed_triple_computed"]))
        self.assign(self.circuit.hashed_triple_filtered, F(input["hashed_triple_filtered"]))

# Circuit: Prove the filtered list is correct
class FilterVerificationCircuit(Circuit):
    def __init__(self, max_steps):
        self.max_steps = max_steps
        super().__init__()

    def setup(self):
        self.subject = self.shared("subject")
        self.predicate = self.shared("predicate")
        self.object = self.shared("object")
        self.condition = self.shared("condition")
        self.flag = self.shared("flag")

        self.total_computed = self.shared("total_computed")
        self.total_filtered = self.shared("total_filtered")

        self.hashed_triple_computed = self.shared("hashed_triple_computed")
        self.hashed_triple_filtered = self.shared("hashed_triple_filtered")

        self.condition_check_step = self.step_type(FilterConditionVerifier(self, "condition_check_step"))
        self.total_computed_check_step = self.step_type(FilterTotalComputedVerifier(self, "total_computed_check_step"))
        self.computation_check_step = self.step_type(FilterComputationVerifier(self, "computation_check_step"))
        self.pragma_num_steps(self.max_steps)
    
    def trace(self, original_triples, filtered_triples, target_subject_value):
        # Step 1: Process original triples and collect hashes
        computed_hashes = []
        for triple in original_triples:
            subject, predicate, object = triple
            flag = 1 if subject == target_subject_value else 0
            hashed_triple = simple_hash(subject, predicate, object)
            if flag:
                computed_hashes.append(hashed_triple)
        
        # Step 2: Process filtered triples and check against original
        # Also constrain the filtering condition
        filtered_hashes = []
        for triple in filtered_triples:
            subject, predicate, object = triple
            hashed_triple = simple_hash(subject, predicate, object)
            self.add(self.condition_check_step, {
                "subject": subject,
                "predicate": predicate,
                "object": object,
                "condition": target_subject_value,
                "flag": 1,  # Must pass filter
            })
            filtered_hashes.append(hashed_triple)

        # Step 3: Constrain the total expected items == the total filtered items
        self.add(self.total_computed_check_step, {
            "total_computed": len(computed_hashes),
            "total_filtered": len(filtered_hashes)
        })
        
        # Step 4: Constrain filtered hashes to match expected
        if len(computed_hashes) == len(filtered_hashes):
            computed_hashes.sort()
            filtered_hashes.sort()
            
            for i in range(len(computed_hashes)):
                self.add(self.computation_check_step, {
                    "hashed_triple_computed": computed_hashes[i],
                    "hashed_triple_filtered": filtered_hashes[i],
                })

################ ORDER BY ################
class OrderByConditionVerifier(StepType):
    def setup(self):
        self.constr(eq(
            (1 - self.circuit.direction) * (self.circuit.current - self.circuit.next - self.circuit.slack) + 
            self.circuit.direction * (self.circuit.next - self.circuit.current - self.circuit.slack), 0)
        )
        # TODO
        # self.constr(self.circuit.slack >= 0)  # Slack is non-negative
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
        self.pragma_num_steps(self.max_steps)

    def trace(self, sorted_list, direction):
        for i in range((len(sorted_list) - 1)):
            current = sorted_list[i]
            next = sorted_list[i + 1]

            if direction == 1:  # ASC
                slack = max(0, next - current)  # current <= next
            else:  # DESC
                slack = max(0, current - next)  # next <= current

            self.add(self.orderby_check_step, current, next, direction, slack)

################ GROUP BY ################
# TODO
class GroupByConditionVerifier(StepType):
    def setup(self):
        pass

    def wg(self):
        pass

class GroupByVerificationCircuit(Circuit):
    def setup(self):
        pass

    def trace(self):
        pass

################ UNION ################
class UnionConditionVerifier(StepType):
    def setup(self):
        self.constr(eq(self.circuit.p_common_hash - self.circuit.p_set_hash, 0))

    def wg(self, input):
        self.assign(self.circuit.p_common_hash, F(input["p_common_hash"]))
        self.assign(self.circuit.p_set_hash, F(input["p_set_hash"]))

class UnionTotalComputedVerifier(StepType):
    def setup(self):
        self.constr(eq(self.circuit.total_computed - self.circuit.total_union, 0))

    def wg(self, input):
        self.assign(self.circuit.total_computed, F(input["total_computed"]))
        self.assign(self.circuit.total_union, F(input["total_union"]))

class UnionVerificationCircuit(Circuit):
    def __init__(self, max_steps):
        self.max_steps = max_steps
        super().__init__()

    def setup(self):
        self.p_common_hash = self.shared("p_common_hash")
        self.p_set_hash = self.shared("p_set_hash")
        self.total_computed = self.shared("total_computed")
        self.total_union = self.shared("total_union")

        self.total_union_check_step = self.step_type(UnionTotalComputedVerifier(self, "total_union_check_step"))
        self.union_check_step = self.step_type(UnionConditionVerifier(self, "union_check_step"))
        self.pragma_num_steps(self.max_steps)

    def trace(self, p1, p2, result):
        # Step 1: Constrain the total expected items == the total united items
        self.add(self.total_union_check_step, {
            "total_computed": len(p1) + len(p2),
            "total_union": len(result)
        })

        # Step 2: Constrain p1 triples
        p1_common = sorted(list(set(result) & set(p1)))
        p1_set = sorted(set(p1))

        self.add(self.total_union_check_step, {
            "total_computed": len(p1_common),
            "total_union": len(p1_set)
        })

        if len(p1_common) == len(p1_set):
            for i in range(len(p1_set)):
                p_common_hash = simple_hash(p1_common[i][0], p1_common[i][1], p1_common[i][2])
                p_set_hash = simple_hash(p1_set[i][0], p1_set[i][1], p1_set[i][2])

                self.add(self.union_check_step, {
                    "p_common_hash": p_common_hash,
                    "p_set_hash": p_set_hash
                })

        # Step 3: Constrain p2 triples
        p2_common = sorted(list(set(result) & set(p2)))
        p2_set = sorted(set(p2))

        self.add(self.total_union_check_step, {
            "total_computed": len(p2_common),
            "total_union": len(p2_set)
        })

        if len(p2_common) == len(p2_set):
            for i in range(len(p2_set)):
                p_common_hash = simple_hash(p2_common[i][0], p2_common[i][1], p2_common[i][2])
                p_set_hash = simple_hash(p2_set[i][0], p2_set[i][1], p2_set[i][2])

                self.add(self.union_check_step, {
                    "p_common_hash": p_common_hash,
                    "p_set_hash": p_set_hash
                })

################ OPTIONAL ################
class OptionalConditionVerifier(StepType):
    def setup(self):
        self.constr(eq(self.circuit.p_common_hash - self.circuit.p_set_hash, 0))

    def wg(self, input):
        self.assign(self.circuit.p_common_hash, F(input["p_common_hash"]))
        self.assign(self.circuit.p_set_hash, F(input["p_set_hash"]))

class OptionalTotalComputedVerifier(StepType):
    def setup(self):
        self.constr(eq(self.circuit.total_computed - self.circuit.total_optional, 0))

    def wg(self, input):
        self.assign(self.circuit.total_computed, F(input["total_computed"]))
        self.assign(self.circuit.total_optional, F(input["total_optional"]))

class OptionalVerificationCircuit(Circuit):
    def __init__(self, max_steps):
        self.max_steps = max_steps
        super().__init__()

    def setup(self):
        self.p_common_hash = self.shared("p_common_hash")
        self.p_set_hash = self.shared("p_set_hash")
        self.total_computed = self.shared("total_computed")
        self.total_optional = self.shared("total_optional")

        self.total_optional_check_step = self.step_type(OptionalTotalComputedVerifier(self, "total_optional_check_step"))
        self.optional_check_step = self.step_type(OptionalConditionVerifier(self, "optional_check_step"))
        self.pragma_num_steps(self.max_steps)


    def trace(self, p1, p2, result):
        # Step 1: Constrain the total expected items == the total united items
        self.add(self.total_optional_check_step, {
            "total_computed": max(len(p1), len(p2)),
            "total_optional": len(result)
        })

        # Step 2: Constrain p1 triples
        p1_common = sorted([t1 for t1 in p1 if any(set(t1).issubset(set(rs)) for rs in result)])
        p1_set = sorted(set(p1))

        self.add(self.total_optional_check_step, {
            "total_computed": len(p1_common),
            "total_optional": len(p1_set)
        })

        if len(p1_common) == len(p1_set):
            for i in range(len(p1_set)):
                p_common_hash = simple_hash_v2(p1_common[i])
                p_set_hash = simple_hash_v2(p1_set[i])

                self.add(self.optional_check_step, {
                    "p_common_hash": p_common_hash,
                    "p_set_hash": p_set_hash
                })

        # Step 3: Constrain p2 triples
        p2_common = sorted([t2 for t2 in p2 if any(set(t2).issubset(set(rs)) for rs in result)])
        p2_set = sorted(set(p2))

        self.add(self.total_optional_check_step, {
            "total_computed": len(p2_common),
            "total_optional": len(p2_set)
        })

        if len(p2_common) == len(p2_set):
            for i in range(len(p2_set)):
                p_common_hash = simple_hash_v2(p2_common[i])
                p_set_hash = simple_hash_v2(p2_set[i])

                self.add(self.optional_check_step, {
                    "p_common_hash": p_common_hash,
                    "p_set_hash": p_set_hash
                })

################ AGGREGATION ################


# Usage
# Filter
original_triples = [("a", "b", "c"), ("a", "e", "f"), ("g", "h", "i")]
filtered_triples = [("a", "b", "c"), ("a", "e", "f")]
encoded_original = [(encode_term(s), encode_term(p), encode_term(o)) for s, p, o in original_triples]
encoded_filtered = [(encode_term(s), encode_term(p), encode_term(o)) for s, p, o in filtered_triples]
target_subject = encode_term("a")

total_steps = len(filtered_triples) * 2 + 1
circuit = FilterVerificationCircuit(max_steps=total_steps)
witness = circuit.gen_witness(encoded_original, encoded_filtered, target_subject)

circuit.halo2_mock_prover(witness=witness, k=7)

# Order by
asc_list = [1, 2, 3, 5]
circuit_asc = OrderByVerificationCircuit(max_steps=len(asc_list))
circuit_instance_asc = circuit_asc.gen_witness(asc_list, 1)  # 0 for ASC
circuit_asc.halo2_mock_prover(witness=circuit_instance_asc, k=7)

# Descending order
desc_list = [5, 3, 2, 1]
circuit_desc = OrderByVerificationCircuit(max_steps=len(desc_list))
circuit_instance_desc = circuit_desc.gen_witness(desc_list, 0)  # 1 for DESC
circuit_desc.halo2_mock_prover(witness=circuit_instance_desc, k=7)

# # Test with invalid cases
# invalid_asc = [1, 3, 2, 5]  # Not ascending
# circuit_invalid_asc = OrderByVerificationCircuit(max_steps=len(invalid_asc))
# circuit_instance_invalid_asc = circuit_invalid_asc.gen_witness(invalid_asc, 0)
# circuit_invalid_asc.halo2_mock_prover(witness=circuit_instance_invalid_asc, k=7)

# invalid_desc = [5, 2, 3, 1]  # Not descending
# circuit_invalid_desc = OrderByVerificationCircuit(max_steps=len(invalid_desc))
# circuit_instance_invalid_desc = circuit_invalid_desc.gen_witness(invalid_desc, 1)
# circuit_invalid_desc.halo2_mock_prover(witness=circuit_instance_invalid_desc, k=7)

# Union
p1 = [("a", "b", "c"), ("a", "e", "f"), ("g", "h", "i")]
p1 = [(encode_term(s), encode_term(p), encode_term(o)) for s, p, o in p1]
p2 = [("a", "e", "f"), ("c", "h", "i")]
p2 = []
p2 = [(encode_term(s), encode_term(p), encode_term(o)) for s, p, o in p2]
# result = [("a", "b", "c"), ("a", "e", "f"), ("g", "h", "i"), ("a", "e", "f"), ("c", "h", "i")]  # UNION with duplicates preserved
result = [("a", "b", "c"), ("a", "e", "f"), ("g", "h", "i")]
result = [(encode_term(s), encode_term(p), encode_term(o)) for s, p, o in result]

union_circuit = UnionVerificationCircuit(max_steps=len(result) + 3)
union_circuit_instance = union_circuit.gen_witness(p1, p2, result)
union_circuit.halo2_mock_prover(witness=union_circuit_instance, k=7)

# Optional
p1 = [('a', 'b'), ('c', 'd'), ('e', 'f')]
p1 = [tuple(encode_term(item) for item in t) for t in p1]
p2 = [('a', 'g'), ('e', 'i')]
p2 = [tuple(encode_term(item) for item in t) for t in p2]
result = [('a', 'b', 'g'), ('c', 'd'), ('e', 'f', 'i')]
result = [tuple(encode_term(item) for item in t) for t in result]

optional_circuit = OptionalVerificationCircuit(max_steps=(len(p1) + len(p2)) + 3)
optional_circuit_instance = optional_circuit.gen_witness(p1, p2, result)
optional_circuit.halo2_mock_prover(witness=optional_circuit_instance, k=7)