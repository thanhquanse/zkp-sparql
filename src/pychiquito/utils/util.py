import re

charsets = '.-_0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'

def contains_regex(text):
    return re.search(r'regex', text, re.IGNORECASE) is not None

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