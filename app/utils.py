# app/utils.py
import hashlib

def hash_value(value: str, salt: str = "") -> str:
    """
    Generates a SHA256 hash for the given value.
    An optional salt can be provided for persistent hashing.
    """
    salted_value = value + salt
    return hashlib.sha256(salted_value.encode('utf-8')).hexdigest()
