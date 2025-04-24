import re
from collections import defaultdict
from itertools import groupby, product

charsets = '.-_0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'

def contains_regex(input):
    return re.search(r'regex', input, re.IGNORECASE) is not None

def constains_builtin(input):
    return re.search(r'builtin', input, re.IGNORECASE) is not None

def word_to_int(word: str) -> int:
    # Define character set in lexicographical order
    char_to_value = {char: idx + 1 for idx, char in enumerate(charsets)}  # 1-based mapping
    
    # Base for conversion (must be > number of unique chars)
    base = len(charsets) + 1  # 65 chars + 1 for padding = base 66
    
    # Convert word to integer
    result = 0
    for char in word:
        if char not in char_to_value:
            raise ValueError(f"Invalid character in word: {char}")
        result = result * base + char_to_value[char]
    
    return result

def sort_words_as_ints(words):
    return sorted(words, key=word_to_int)

def word_to_int_order(words: list, direction: int = 1) -> list:
    if direction not in [0, 1]:
        raise ValueError("Direction must be 'asc' or 'desc'")
    
    # Track unique strings in order of appearance
    unique_strings = []
    for word in words:
        if word not in unique_strings:
            unique_strings.append(word)
    
    # Total number of unique strings
    total_unique = len(unique_strings)
    
    # Map each unique string to an integer based on direction
    if direction == 1:
        # Ascending: first string gets 1, second gets 2, etc.
        string_to_int = {word: idx + 1 for idx, word in enumerate(unique_strings)}
    else:
        # Descending: first string gets n, second gets n-1, etc.
        string_to_int = {word: total_unique - idx for idx, word in enumerate(unique_strings)}
    
    # Convert each word in the original list to its integer
    return [string_to_int[word] for word in words]

def find_next_stage(data_dict, current, target):
    keys = sorted(data_dict.keys(), key=int)
    found_current = False

    for key in keys:
        item = data_dict[key]
        if not found_current:
            if item.get("name") == current:
                found_current = True
        else:
            if item.get("name") == target:
                return key, item  # Return the key and the item

    return None, None

def group_by(data, keys):
    grouped = defaultdict(list)
    for item in data:
        # Create a tuple of key values for grouping
        if all(k in item for k in keys):
            group_key = tuple(item[k] for k in keys)
            grouped[group_key].append(item)
    return grouped

def check_tuple_in_flat_list(flat_list, target_tuple):
    tuple_size = len(target_tuple)
    if tuple_size == 0 or tuple_size > len(flat_list):
        return False

    # Create sliding window tuples of the same size as target_tuple
    tuple_list = [
        tuple(flat_list[i:i + tuple_size])
        for i in range(len(flat_list) - tuple_size + 1)
    ]
    
    return target_tuple in tuple_list

def is_grouped_by(data, group_fields):
    if not data or not group_fields:
        return False

    # Extract the group key for each item in order
    # actual_keys = [tuple(item[field] for field in group_fields) for item in data]
    actual_keys = [
        tuple(item[field] for field in group_fields)
        for item in data
        if all(field in item for field in group_fields)
    ]


    # Use groupby to find unique groups in sequence
    grouped_keys = [key for key, _ in groupby(actual_keys)]

    # Reconstruct what a properly grouped sequence should look like
    expected_sequence = []
    for key in grouped_keys:
        count = actual_keys.count(key)
        expected_sequence.extend([key] * count)

    return actual_keys == expected_sequence

def normalize_data(data):
    # Convert each row to a dict and sort key-value pairs for consistent ordering
    normalized = [tuple(sorted(dict(row).items())) for row in data]
    return sorted(normalized)

def find_common_variables(var1, var2):
    # Extract variables from var1 (set of (Variable, Value) pairs)
    var1_vars = {str(var) for var in var1}
    
    # Extract variables from var2 (list of dicts)
    var2_vars = set()
    for binding in var2:
        var2_vars.update(binding.keys())

    # Find intersection
    common_vars = var1_vars & var2_vars
    return common_vars

def group_by_variable(pairs):
    # The input is in pair like (rdflib.term.Variable('book'), rdflib.term.URIRef('http://example.org/book2'))
    result = defaultdict(list)
    for var, val in pairs:
        result[str(var)].append(str(val))
    return dict(result)

def group_by_keys(dict_list):
    # The input is like [{'person': 'http://example.org/bob', 'name': 'Bob'}, {'person': 'http://example.org/carol', 'name': 'Carol'}]
    result = defaultdict(list)
    for entry in dict_list:
        for key, value in entry.items():
            result[key].append(value)
    return dict(result)

def group_by_fields(data, fields):
    var_map = defaultdict(list)
    for var, value in data:
        var_map[str(var)].append(str(value))  # convert values to strings for consistent output

    # Extract the value lists for the selected fields
    value_lists = [var_map.get(field, []) for field in fields]

    # Compute Cartesian product
    combos = product(*value_lists)

    # Build dictionaries for each combination
    return [dict(zip(fields, combo)) for combo in combos]