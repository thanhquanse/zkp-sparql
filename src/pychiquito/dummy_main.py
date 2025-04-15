from gates.filter import FilterVerificationCircuit
from gates.orderby import OrderByVerificationCircuit
from gates.optional import OptionalVerificationCircuit
from gates.union import UnionVerificationCircuit
from gates.slice import SliceVerificationCircuit
from gates.distinct import DistinctVerificationCircuit
from gates.aggregate import AggregateVerificationCircuit
from gates.groupby import GroupByVerificationCircuit
from gates.minus import MinusVerificationCircuit

from utils.hash import hash_to_u64

# Usage
# Filter
original_triples = [("a", "b", "c"), ("a", "e", "f"), ("g", "h", "i")]
filtered_triples = [("a", "b", "c"), ("a", "e", "f")]

original = [
    { 'a': 1, 'e': 5, 'f': 6 },
    { 'a': 2, 'e': 5, 'f': 6 },
    { 'a': 1, 'e': 7, 'f': 6 },
    { 'a': 1, 'e': 4, 'f': 3 }
]

filtered = [
    { 'a': 1, 'e': 5, 'f': 6 },
    { 'a': 1, 'e': 7, 'f': 6 },
    { 'a': 1, 'e': 4, 'f': 3 }
]

condition = {
    'expr': 'a',
    'op': '=',
    "other": 1
}

# encoded_original = [(hash_to_u64(s), hash_to_u64(p), hash_to_u64(o)) for s, p, o in original_triples]
# encoded_filtered = [(hash_to_u64(s), hash_to_u64(p), hash_to_u64(o)) for s, p, o in filtered_triples]
# target_subject = hash_to_u64("a")

total_steps = len(filtered) * 2 + 3
circuit = FilterVerificationCircuit(max_steps=total_steps)
witness = circuit.gen_witness(original, filtered, condition)

circuit.halo2_mock_prover(witness=witness, k=7)

# Order by
asc_list = [-2, -2, 3, 3]
circuit_asc = OrderByVerificationCircuit(max_steps=len(asc_list) * 2)
circuit_instance_asc = circuit_asc.gen_witness(asc_list, 1)  # 0 for ASC
circuit_asc.halo2_mock_prover(witness=circuit_instance_asc, k=7)

# Descending order
desc_list = [5, 3, 2, 1]
circuit_desc = OrderByVerificationCircuit(max_steps=len(desc_list) * 2)
circuit_instance_desc = circuit_desc.gen_witness(desc_list, 0)  # 1 for DESC
circuit_desc.halo2_mock_prover(witness=circuit_instance_desc, k=7)

# # Test with invalid cases
# invalid_asc = [1, 3, 2, 5]  # Not ascending
# circuit_invalid_asc = OrderByVerificationCircuit(max_steps=len(invalid_asc) * 2)
# circuit_instance_invalid_asc = circuit_invalid_asc.gen_witness(invalid_asc, 0)
# circuit_invalid_asc.halo2_mock_prover(witness=circuit_instance_invalid_asc, k=7)

# invalid_desc = [5, 2, 3, 1]  # Not descending
# circuit_invalid_desc = OrderByVerificationCircuit(max_steps=len(invalid_desc) * 2)
# circuit_instance_invalid_desc = circuit_invalid_desc.gen_witness(invalid_desc, 1)
# circuit_invalid_desc.halo2_mock_prover(witness=circuit_instance_invalid_desc, k=7)

# Union
p1 = [("a", "b", "c"), ("a", "e", "f"), ("g", "h", "i")]
p1 = [(hash_to_u64(s), hash_to_u64(p), hash_to_u64(o)) for s, p, o in p1]
p2 = [("a", "e", "f"), ("c", "h", "i")]
p2 = []
p2 = [(hash_to_u64(s), hash_to_u64(p), hash_to_u64(o)) for s, p, o in p2]
# result = [("a", "b", "c"), ("a", "e", "f"), ("g", "h", "i"), ("a", "e", "f"), ("c", "h", "i")]  # UNION with duplicates preserved
result = [("a", "b", "c"), ("a", "e", "f"), ("g", "h", "i")]
result = [(hash_to_u64(s), hash_to_u64(p), hash_to_u64(o)) for s, p, o in result]

union_circuit = UnionVerificationCircuit(max_steps=len(result) + 8)
union_circuit_instance = union_circuit.gen_witness(p1, p2, result)
union_circuit.halo2_mock_prover(witness=union_circuit_instance, k=7)

# Optional
p1 = [('a', 'b'), ('c', 'd'), ('e', 'f')]
p1 = [tuple(hash_to_u64(item) for item in t) for t in p1]
p2 = [('a', 'g'), ('e', 'i')]
p2 = [tuple(hash_to_u64(item) for item in t) for t in p2]
result = [('a', 'b', 'g'), ('c', 'd'), ('e', 'f', 'i')]
result = [tuple(hash_to_u64(item) for item in t) for t in result]

optional_circuit = OptionalVerificationCircuit(max_steps=(len(p1) + len(p2)) + 8)
optional_circuit_instance = optional_circuit.gen_witness(p1, p2, result)
optional_circuit.halo2_mock_prover(witness=optional_circuit_instance, k=7)

# Limit
slice = [('a', 'b', 'g'), ('c', 'd'), ('e', 'f', 'i')]
slice = [tuple(hash_to_u64(item) for item in t) for t in slice]
slice_circuit = SliceVerificationCircuit(max_steps=1 + 3)
slice_circuit_instance = slice_circuit.gen_witness(0, 10, slice)
slice_circuit.halo2_mock_prover(witness=slice_circuit_instance, k=7)

# Offset
# TODO: expected slice can be greater than actual existence in db
slice_circuit_instance = slice_circuit.gen_witness(1, 3, slice)
slice_circuit.halo2_mock_prover(witness=slice_circuit_instance, k=7)

# Distinct
distinct = [('a', 'b', 'g'), ('c', 'd'), ('e', 'f', 'i')]
distinct = [tuple(hash_to_u64(item) for item in t) for t in distinct]
distinct_circuit = DistinctVerificationCircuit(max_steps=2)
distinct_circuit_instance = distinct_circuit.gen_witness(distinct)
distinct_circuit.halo2_mock_prover(witness=distinct_circuit_instance)

# Aggregate
agg_condition = ['a', 'b', 'c']
agg_condition = [hash_to_u64(item) for item in agg_condition]
agg_result = ['c', 'b', 'a']
agg_result = [hash_to_u64(item) for item in agg_result]
agg_circuit = AggregateVerificationCircuit(max_steps=len(agg_condition) + 4)
agg_circuit_instance = agg_circuit.gen_witness(agg_condition, agg_result)
agg_circuit.halo2_mock_prover(witness=agg_circuit_instance)

# Groupby
groupby_field = "name"
groupby_result = [
    {'item': 'http://example.org/item1', 'person': 'http://example.org/alice', 'amount': '20', 'name': 1},
    {'item': 'http://example.org/item2', 'person': 'http://example.org/alice', 'amount': '50', 'name': 1},
    {'item': 'http://example.org/item3', 'person': 'http://example.org/bob', 'amount': '30', 'name': 2},
    {'item': 'http://example.org/item4', 'person': 'http://example.org/carol', 'amount': '100', 'name': 3},
    {'item': 'http://example.org/item5', 'person': 'http://example.org/carol', 'amount': '75', 'name': 3},
    {'item': 'http://example.org/item6', 'person': 'http://example.org/carol', 'amount': '25', 'name': 3}
]
groupby_circuit = GroupByVerificationCircuit(max_steps=len(groupby_result) * 2)
groupby_result_instance = groupby_circuit.gen_witness(groupby_field, groupby_result)
groupby_circuit.halo2_mock_prover(witness=groupby_result_instance)

# Minus
result = [('a', 'b', 'g'), ('c', 'd'), ('e', 'f', 'i')]
result = [tuple(hash_to_u64(item) for item in t) for t in result]
minus = [('a', 'b', 'a')]
minus = [tuple(hash_to_u64(item) for item in t) for t in minus]
minus_circuit = MinusVerificationCircuit(max_steps=len(result) * 2 + 3) 
minus_circuit_instance = minus_circuit.gen_witness(minus, result)
minus_circuit.halo2_mock_prover(witness=minus_circuit_instance)