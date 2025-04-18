import json
import hashlib
import poseidon
from poseidon_py.poseidon_hash import (
    poseidon_perm,
    poseidon_hash_func,
    poseidon_hash,
    poseidon_hash_single,
    poseidon_hash_many,
)
from typing import List, Union, Dict, Tuple
from numpy import ndarray

HashType = int | dict | tuple | list
prime = poseidon.parameters.prime_255

def string_to_field_element(input) -> int:
    # Hash the string using BLAKE2b with a 32-byte digest
    string = str(input)
    digest = hashlib.blake2b(string.encode('utf-8'), digest_size=32).digest()
    # Convert the digest to an integer (big-endian)
    return int.from_bytes(digest, 'big')

def hash_to_u64_v2(input) -> int:
    # Blake2b with 8-byte output for 64 bits
    data = str(input)
    digest = hashlib.blake2b(data.encode('utf-8'), digest_size=8).digest()
    return int.from_bytes(digest, 'big')  # or 'big'

def hash_to_u64(value, digest_size=32):
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

def zkp_poseidon_hash_single(value):
    return poseidon_hash_single(value)

def zkp_poseidon_hash_many(values):
    return poseidon_hash_many(values)

def hash_fed(hashee: HashType):
    if isinstance(hashee, int):
        return hash_to_u64(hashee)
    elif isinstance(hashee, (tuple, list)):
        rs = 0
        for i in range(len(hashee)):
            rs = rs + hash_to_u64(hashee[i])
        return rs
    elif isinstance(hashee, dict):
        rs = 0
        keys = list(hashee.keys())
        for i in range(len(keys)):
            rs = rs + hash_to_u64(hashee[keys[i]])
        return rs
    
def to_field_elements(data: Union[List[int], Tuple[int, ...], Dict[any, int]], 
                     prime: int) -> List[int]:
    """Convert collection of u64 hashes to field elements."""
    if isinstance(data, (list, tuple)):
        return [x % prime for x in data]  # Ensure u64s are in field
    elif isinstance(data, dict):
        # Sort keys for determinism, use values (or include keys if needed)
        sorted_items = sorted(data.items(), key=lambda x: str(x[0]))
        return [v % prime for _, v in sorted_items]  # Only values
    else:
        raise ValueError("Unsupported type: must be list, tuple, or dict")
    
def transform_data(data: Union[List[int], Tuple[int, ...], Dict[any, int], int, str, ndarray]):
    if isinstance(data, (list, tuple, ndarray)):
        return [string_to_field_element(v) for v in data]
    if isinstance(data, (str)):
        return string_to_field_element(data)
    elif isinstance(data, dict):
        sorted_items = sorted(data.items(), key=lambda x: str(x[0]))
        return [string_to_field_element(v) for _, v in sorted_items]
    else:
        raise ValueError("Unsupported type: must be list, tuple, int, str, ndarrays or dict")

def poseidon_hash_to_u64(data: Union[List[int], Tuple[int, ...], Dict[any, int], int, str]) -> int:
    poseidon_new = poseidon.Poseidon(
        p=prime,
        security_level=128,
        input_rate=3,
        t=3,
        alpha=5
    )

    return int(poseidon_new.run_hash(transform_data(data)))