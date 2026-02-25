from collections import defaultdict
from rdflib.term import Variable
from chiquito.dsl import Circuit, StepType
from chiquito.cb import eq
from chiquito.util import F
from .common.gteq import GreaterEqVerifier

from utils.hash import hash_to_number

class FieldElement:
    PRIME = 2**255 - 19  # A large prime for the field

    def __init__(self, val):
        self.val = val % self.PRIME

    def __add__(self, other):
        return FieldElement((self.val + other.val) % self.PRIME)

    def __mul__(self, other):
        return FieldElement((self.val * other.val) % self.PRIME)

    def __truediv__(self, other):
        inv = pow(other.val, self.PRIME - 2, self.PRIME)
        return FieldElement((self.val * inv) % self.PRIME)

    def __sub__(self, other):
        return FieldElement((self.val - other.val) % self.PRIME)

    def __eq__(self, other):
        return self.val == other.val

    @classmethod
    def zero(cls):
        return cls(0)

    @classmethod
    def one(cls):
        return cls(1)

class BGPConditionVerifier(StepType):
    def setup(self):
        self.constr(eq(self.circuit.comparator_1 - self.circuit.comparator_2, 0))

    def wg(self, input):
        self.assign(self.circuit.comparator_1, F(input["comparator_1"]))
        self.assign(self.circuit.comparator_2, F(input["comparator_2"]))

class BGPGPInitVerifier(StepType):
    def setup(self):
        self.constr(eq(self.circuit.z - 1, 0))

    def wg(self, input):
        self.assign(self.circuit.z, F(input["z"]))

class BGPGPStepVerifier(StepType):
    def setup(self):
        z = self.circuit.z
        z_next = self.circuit.z_next
        c_omega_star = self.circuit.c_omega_star
        c_omega = self.circuit.c_omega
        beta = self.circuit.beta

        self.constr(eq(z_next * (c_omega + beta) - z * (c_omega_star + beta), 0))

    def wg(self, input):
        self.assign(self.circuit.z, F(input["z"]))
        self.assign(self.circuit.z_next, F(input["z_next"]))
        self.assign(self.circuit.c_omega_star, F(input["c_omega_star"]))
        self.assign(self.circuit.c_omega, F(input["c_omega"]))
        self.assign(self.circuit.beta, F(input["beta"]))

class BGPGPEndVerifier(StepType):
    def setup(self):
        self.constr(eq(self.circuit.z - 1, 0))

    def wg(self, input):
        self.assign(self.circuit.z, F(input["z"]))

class BGPVerificationCircuit(Circuit):
    def __init__(self, max_steps):
        self.max_steps = max_steps
        super().__init__()

    def setup(self):
        self.z = self.shared("z")
        self.z_next = self.shared("z_next")
        self.c_omega_star = self.shared("c_omega_star")
        self.c_omega = self.shared("c_omega")
        self.beta = self.shared("beta")

        self.comparator_1 = self.shared("comparator_1")
        self.comparator_2 = self.shared("comparator_2")

        self.bgp_gp_init_step = self.step_type(BGPGPInitVerifier(self, "bgp_gp_init_step"))
        self.bgp_gp_end_step = self.step_type(BGPGPEndVerifier(self, "bgp_gp_end_step"))
        self.bgp_check_step = self.step_type(BGPConditionVerifier(self, "bgp_check_step"))
        self.bgp_gteq_check_step = self.step_type(GreaterEqVerifier(self, "bgp_gteq_check_step"))
        self.bgp_gp_step = self.step_type(BGPGPStepVerifier(self, "bgp_gp_step"))
        self.pragma_num_steps(self.max_steps)

    def trace2(self, ctx, triples, results):
        triple_dict = {}
        single_triple_rs = []
        j = 0
        for triple in triples:
            new_triple = []
            matching_triples = []
            fixed_val = {}

            for i, el in enumerate(triple):
                if isinstance(el, Variable):
                    new_triple.append(None)
                else:
                    new_triple.append(el)
                    fixed_val[i] = el

            # Query the graph
            for result in ctx.graph.triples(tuple(new_triple)):
                # constraints fixed values
                for i in fixed_val.keys():
                    tphash = hash_to_number(result[i])
                    valhash = hash_to_number(fixed_val[i])
                    self.add(self.bgp_check_step, {
                        "comparator_1": tphash,
                        "comparator_2": valhash
                    })
                # handle 1 triple pattern
                if len(triples) == 1:
                    temp = {}
                    for idx, el in enumerate(result):
                        if idx not in fixed_val.keys():
                            temp[str(triple[idx])] = str(el)
                    single_triple_rs.append(temp)
                
                # handle multiple triple patterns
                for idx, el in enumerate(result):
                    if idx not in fixed_val.keys():
                        matching_triples.append({str(triple[idx]): str(el)})
            
            triple_dict[j] = matching_triples
            j += 1

        if len(triples) == 1:
            joined = single_triple_rs
        else:
            joined = sparql_like_join(triple_dict)
        
        self.add(self.bgp_gteq_check_step, len(results), len(joined))

        sorted_concat_list1 = sorted(joined, key=lambda d: tuple(sorted(d.items())))
        sorted_concat_list2 = sorted(results, key=lambda d: tuple(sorted(d.items())))

        for i in range(len(sorted_concat_list1)):
            common_keys = set(sorted_concat_list1[i].keys()).intersection(set(sorted_concat_list2[i].keys()))
            concat1 = ''.join([str(sorted_concat_list1[i][k]) for k in sorted(common_keys)])
            concat2 = ''.join([str(sorted_concat_list2[i][k]) for k in sorted(common_keys)])
            a = hash_to_number(concat1)
            b = hash_to_number(concat2)
            self.add(self.bgp_check_step, {
                "comparator_1": a,
                "comparator_2": b
            })

    def trace(self, ctx, triples, results):
        PRIME = 2**255 - 19  # A large prime for the field

        def mod_inverse(a, m=PRIME):
            return pow(a, m - 2, m)

        triple_dict = {}
        single_triple_rs = []
        j = 0
        for triple in triples:
            new_triple = []
            matching_triples = []
            fixed_val = {}

            for i, el in enumerate(triple):
                if isinstance(el, Variable):
                    new_triple.append(None)
                else:
                    new_triple.append(el)
                    fixed_val[i] = el

            # Query the graph
            for result in ctx.graph.triples(tuple(new_triple)):
                # constraints fixed values
                for i in fixed_val.keys():
                    tphash = hash_to_number(result[i])
                    valhash = hash_to_number(fixed_val[i])
                    self.add(self.bgp_check_step, {
                        "comparator_1": tphash,
                        "comparator_2": valhash
                    })
                # handle 1 triple pattern
                if len(triples) == 1:
                    temp = {}
                    for idx, el in enumerate(result):
                        if idx not in fixed_val.keys():
                            temp[str(triple[idx])] = str(el)
                    single_triple_rs.append(temp)
                
                # handle multiple triple patterns
                for idx, el in enumerate(result):
                    if idx not in fixed_val.keys():
                        matching_triples.append({str(triple[idx]): str(el)})
            
            triple_dict[j] = matching_triples
            j += 1

        if len(triples) == 1:
            joined = single_triple_rs
        else:
            joined = sparql_like_join(triple_dict)
        
        # BC you can use your code to compute Omega* (scanning triple in G) and Omega (engine output table)
        joined_tmp = sorted(joined, key=lambda d: tuple(sorted(d.items())))
        results_tmp = sorted(results, key=lambda d: tuple(sorted(d.items())))
        omega_star = joined_tmp  # off-circuit witness generation
        omega = results_tmp      # off-circuit (public/claimed output)

        # Get all unique sorted variables (columns) across both tables
        all_vars = set()
        for row in omega_star + omega:
            all_vars.update(row.keys())
        sorted_vars = sorted(list(all_vars))
        L = len(sorted_vars)

        # Dummy row encoded as reserved field elements (e.g., zero)
        reserved = 0
        DUMMY_ROW = [reserved] * L

        # Convert dict rows to lists of field elements (integers mod PRIME)
        def row_to_field_list(row_dict):
            return [(hash_to_number(row_dict.get(v)) % PRIME) if v in row_dict else reserved for v in sorted_vars]

        omega_star_rows = [row_to_field_list(row) for row in omega_star]
        omega_rows = [row_to_field_list(row) for row in omega]

        # Pad both tables to the same length N
        N = max(len(omega_star_rows), len(omega_rows))
        omega_star_padded = omega_star_rows + [DUMMY_ROW] * (N - len(omega_star_rows))
        omega_padded = omega_rows + [DUMMY_ROW] * (N - len(omega_rows))

        # Challenges (for prototype: fixed/public constants; ideally Fiat–Shamir)
        alpha = 1234567 % PRIME
        beta = 89101112 % PRIME

        # Compress function
        def compress_row(row_vals, alpha):
            """
            Compress a multi-column row into one field element:
            c = v0 + alpha*v1 + alpha^2*v2 + ... + alpha^(L-1)*v(L-1)
            """
            acc = 0
            powa = 1
            for v in row_vals:
                acc = (acc + (powa * v) % PRIME) % PRIME
                powa = (powa * alpha) % PRIME
            return acc

        # Enforce Z[0] = 1
        z = 1
        self.add(self.bgp_gp_init_step, {"z": z})

        # Running product over all rows
        for i in range(N):
            c_omega_star = compress_row(omega_star_padded[i], alpha)
            c_omega = compress_row(omega_padded[i], alpha)

            # Witness for next accumulator value:
            # z_next = z * (c_omega_star + beta) / (c_omega + beta)
            numerator = (z * ((c_omega_star + beta) % PRIME)) % PRIME
            denominator = (c_omega + beta) % PRIME
            z_next = (numerator * mod_inverse(denominator)) % PRIME

            # Enforce: z_next * (c_omega + beta) = z * (c_omega_star + beta)
            self.add(self.bgp_gp_step, {
                "z": z,
                "z_next": z_next,
                "c_omega_star": c_omega_star,
                "c_omega": c_omega,
                "beta": beta
            })

            z = z_next

        # Enforce Z[N] = 1
        self.add(self.bgp_gp_end_step, {"z": z})

def find_common_variable_positions(triples_list):
    if not triples_list:
        return []

    # Number of positions in a triple (usually 3)
    triple_len = len(triples_list[0])
    common_positions = []

    for pos in range(triple_len):
        first_elem = triples_list[0][pos]
        # Check if this element is a Variable
        if not isinstance(first_elem, Variable):
            continue  # skip non-variable positions

        # Check if all triples have the same variable at this position by name
        var_name = str(first_elem)
        if all(isinstance(triple[pos], Variable) and str(triple[pos]) == var_name for triple in triples_list):
            common_positions.append(pos)

    return common_positions

def merge_on(data, on='s'):
    """
    Merge multiple lists of alternating dictionaries on a common key.
    
    Each list in data is expected to be structured as:
    [{on: subj}, {prop1: val1, prop2: val2, ...}, {on: subj2}, ...]
    
    Performs an inner join: only subjects present in ALL lists are included.
    
    :param data: dict mapping arbitrary keys (e.g., 0, 1, ...) to lists of dicts
    :param on: the key to join on (e.g., 's')
    :return: list of merged dictionaries, each containing the on + all properties
    """
    # Step 1: Build a mapping from subject -> properties for each source
    subject_to_props = defaultdict(dict)  # Will hold merged result temporarily
    source_count = len(data)
    source_subjects = []  # To track which subjects exist in which sources

    for source_id, lst in data.items():
        i = 0
        subjects_in_this_source = set()
        
        while i < len(lst):
            if i + 1 >= len(lst):
                raise ValueError(f"Incomplete data in source {source_id}: missing property dict after index {i}")
            
            subj_dict = lst[i]
            prop_dict = lst[i + 1]
            
            if on not in subj_dict:
                raise ValueError(f"Expected '{on}' in dict at position {i} in source {source_id}")
            
            subject = subj_dict[on]
            subjects_in_this_source.add(subject)
            
            # Merge all key-value pairs from prop_dict (could have multiple keys)
            for k, v in prop_dict.items():
                if subject in subject_to_props and k in subject_to_props[subject]:
                    raise ValueError(f"Duplicate property '{k}' for subject {subject} in different sources")
                subject_to_props[subject][k] = v
            
            i += 2
        
        source_subjects.append(subjects_in_this_source)
    
    # Step 2: Find subjects that appear in ALL sources (inner join)
    if source_count == 0:
        return []
    
    common_subjects = set.intersection(*source_subjects)
    
    # Step 3: Build final list of merged records
    result = []
    for subject in common_subjects:
        entry = {on: subject}
        entry.update(subject_to_props[subject])
        result.append(entry)
    
    return result

def sparql_like_join(data):
    """
    General SPARQL-like join for multiple sources of flattened RDF-like data.
    
    Input format:
        data = {0: [single-key dicts], 1: [single-key dicts], ...}
    
    Each source is a flat sequence of dictionaries, each containing exactly one key-value pair.
    Consecutive entries sharing the same key (variable) but with different values belong to different rows.
    
    The function:
    - Automatically parses each source into rows (dictionaries of variable → value)
    - Performs successive joins across all sources:
        • If shared variables exist → natural inner join on all shared variables
        • If no shared variables → Cartesian product
    - Fully general: no hardcoded variable names (no 'book', 'author', etc.)
    - Matches real SPARQL basic graph pattern (BGP) join semantics
    
    :param data: dict mapping arbitrary keys to lists of single-key dicts
    :return: list of merged solution mappings (dicts)
    """
    # Step 1: Parse each source into a list of rows (dict: variable → value)
    def parse_source(lst):
        if not lst:
            return []
        
        rows = []
        current_row = {}
        
        for d in lst:
            if len(d) != 1:
                raise ValueError("Each element must be a dict with exactly one key-value pair")
            
            var, val = next(iter(d.items()))
            
            if var in current_row:
                if current_row[var] != val:
                    # Different value for the same variable → new row starts
                    rows.append(current_row)
                    current_row = {var: val}
                # else: same var + same val → redundant, ignore
            else:
                # New variable in current row
                current_row[var] = val
        
        if current_row:
            rows.append(current_row)
        
        return rows
    
    # Parse all sources
    parsed_sources = [parse_source(lst) for lst in data.values()]
    
    if not parsed_sources:
        return []
    
    # Start with the rows from the first source
    result_rows = parsed_sources[0][:]
    
    # Successively join with each subsequent source
    for next_rows in parsed_sources[1:]:
        if not result_rows or not next_rows:
            return []  # Empty side → empty result
        
        # Collect all variables present in current result and in next source
        current_vars = {var for row in result_rows for var in row.keys()}
        next_vars = {var for row in next_rows for var in row.keys()}
        shared_vars = current_vars.intersection(next_vars)
        
        new_result = []
        
        if shared_vars:
            # Natural join on all shared variables
            # Build index on next_rows using the shared variables as composite key
            index = defaultdict(list)
            for row in next_rows:
                key_tuple = tuple((var, row[var]) for var in sorted(shared_vars))
                index[key_tuple].append(row)
            
            for left_row in result_rows:
                key_tuple = tuple((var, left_row[var]) for var in sorted(shared_vars))
                matches = index.get(key_tuple, [])
                
                for right_row in matches:
                    merged = left_row.copy()
                    conflict = False
                    for var, val in right_row.items():
                        if var in merged and merged[var] != val:
                            conflict = True
                            break
                        merged[var] = val
                    if not conflict:
                        new_result.append(merged)
        else:
            # No shared variables → Cartesian product (SPARQL semantics)
            for left_row in result_rows:
                for right_row in next_rows:
                    merged = left_row.copy()
                    conflict = False
                    for var, val in right_row.items():
                        if var in merged and merged[var] != val:
                            conflict = True
                            break
                        merged[var] = val
                    if not conflict:
                        new_result.append(merged)
        
        result_rows = new_result
    
    # Sort for deterministic, readable output (by sorted variables and values)
    def sort_key(row):
        return tuple(sorted((var, str(val)) for var, val in row.items()))
    
    result_rows.sort(key=sort_key)
    
    return result_rows