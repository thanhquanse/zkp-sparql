from collections import defaultdict
from rdflib.term import Variable
from chiquito.dsl import Circuit, StepType
from chiquito.cb import eq
from chiquito.util import F
from .common.gteq import GreaterEqVerifier

from utils.hash import hash_to_number

class BGPConditionVerifier(StepType):
    def setup(self):
        self.constr(eq(self.circuit.comparator_1 - self.circuit.comparator_2, 0))

    def wg(self, input):
        self.assign(self.circuit.comparator_1, F(input["comparator_1"]))
        self.assign(self.circuit.comparator_2, F(input["comparator_2"]))
class BGPVerificationCircuit(Circuit):
    def __init__(self, max_steps):
        self.max_steps = max_steps
        super().__init__()

    def setup(self):
        self.comparator_1 = self.shared("comparator_1")
        self.comparator_2 = self.shared("comparator_2")

        self.bgp_check_step = self.step_type(BGPConditionVerifier(self, "bgp_check_step"))
        self.bgp_gteq_check_step = self.step_type(GreaterEqVerifier(self, "bgp_gteq_check_step"))
        self.pragma_num_steps(self.max_steps)

    def trace(self, ctx, triples, results):
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
        
        # common_var_position = find_common_variable_positions(triples)[0]
        # common_var = triples[0][common_var_position].__str__()
        # joined = merge_on(triple_dict, on=common_var)

        if len(triples) == 1:
            joined = single_triple_rs
        else:
            joined = sparql_like_join(triple_dict)
        
        self.add(self.bgp_gteq_check_step, len(results), len(joined))

        sorted_concat_list1 = sorted(joined, key=lambda d: tuple(sorted(d.items())))
        sorted_concat_list2 = sorted(results, key=lambda d: tuple(sorted(d.items())))

        # for i in range(len(sorted_concat_list1)):
        #     a = hash_to_number(sorted_concat_list1[i])
        #     b = hash_to_number(sorted_concat_list2[i])
        #     self.add(self.bgp_check_step, {
        #         "comparator_1": a,
        #         "comparator_2": b
        #     })

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