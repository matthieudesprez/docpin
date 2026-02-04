"""Hashing utility for detecting code changes."""

import hashlib


def normalize_content(content: str) -> str:
    """Normalize content to ignore formatting-only changes.

    Ignores:
    - Trailing whitespace on lines
    - Multiple consecutive blank lines (collapsed to one)
    - Leading/trailing blank lines

    Preserves:
    - Indentation (semantic in Python)
    - Single blank lines between sections
    """
    lines = content.splitlines()
    # Strip trailing whitespace from each line
    lines = [line.rstrip() for line in lines]
    # Collapse multiple consecutive blank lines into one
    normalized = []
    prev_blank = False
    for line in lines:
        is_blank = not line.strip()
        if is_blank:
            if not prev_blank:
                normalized.append("")
            prev_blank = True
        else:
            normalized.append(line)
            prev_blank = False
    # Strip leading/trailing blank lines
    return "\n".join(normalized).strip()


def compute_hash(content: str) -> str:
    """Compute a SHA-256 hash of the given content.

    Normalizes whitespace to avoid false positives from formatting changes.
    """
    normalized = normalize_content(content)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
