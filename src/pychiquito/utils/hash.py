import json
import hashlib
from typing import List, Union, Dict, Tuple
from numpy import ndarray

def hash_to_number(value, digest_size=4):
    # Handle serialization for hashable and complex types
    if isinstance(value, (list, tuple, set)):
        # Convert to sorted list for consistency across unordered types
        value = sorted(value)
    elif isinstance(value, dict):
        # Convert dicts to sorted list of key-value tuples
        value = sorted(value.items())

    # Convert to string using json to support complex nested structures
    if not isinstance(value, str):
        value_str = json.dumps(value, sort_keys=True)
    else:
        value_str = value

    # Create the hash
    # TODO: Current, the sigmod impl is able to support int32, so digest_size = 4
    digest = hashlib.blake2b(value_str.encode('utf-8'), digest_size=digest_size).digest()

    # Convert bytes to int
    return int.from_bytes(digest, byteorder='big')

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

def simple_hash_v3(value):
    return value * 30

def simple_hash_v4(dict):
    rs = 0
    keys = list(dict.keys())
    for i in range(len(keys)):
         rs = rs + (30 + i) * dict[keys[i]]
    
    return rs