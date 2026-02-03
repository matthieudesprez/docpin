"""Hashing utility for detecting code changes."""

import hashlib


def compute_hash(content: str) -> str:
    """Compute a SHA-256 hash of the given content.

    Normalizes whitespace to avoid false positives from formatting changes.
    """
    normalized = content.strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
