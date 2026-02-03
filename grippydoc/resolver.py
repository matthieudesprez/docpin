"""Resolver for extracting code content from file references."""

import re
from pathlib import Path
from dataclasses import dataclass

from .hasher import compute_hash


@dataclass
class CodeReference:
    """Represents a resolved code reference."""
    reference: str      # Original reference string (e.g., "src/auth.py:10-20")
    file_path: str      # Resolved file path
    ref_type: str       # "file", "line", or "range"
    start_line: int | None
    end_line: int | None
    content: str
    hash: str


# Pattern to parse grip references:
# - file.py          -> whole file
# - file.py:42       -> single line
# - file.py:42-58    -> line range
REFERENCE_PATTERN = re.compile(
    r'^(?P<file>[^:]+?)(?::(?P<start>\d+)(?:-(?P<end>\d+))?)?$'
)


def parse_reference(reference: str) -> tuple[str, str, int | None, int | None]:
    """Parse a reference string into components.

    Returns: (file_path, ref_type, start_line, end_line)
    """
    match = REFERENCE_PATTERN.match(reference.strip())
    if not match:
        raise ValueError(f"Invalid reference format: {reference}")

    file_path = match.group("file")
    start = match.group("start")
    end = match.group("end")

    if start is None:
        return file_path, "file", None, None
    elif end is None:
        line = int(start)
        return file_path, "line", line, line
    else:
        return file_path, "range", int(start), int(end)


def resolve_reference(reference: str, root: Path) -> CodeReference | None:
    """Resolve a reference to its code content.

    Args:
        reference: The reference string (e.g., "src/auth.py:10-20")
        root: The project root directory

    Returns:
        CodeReference with the resolved content and hash, or None if not found
    """
    try:
        file_path, ref_type, start_line, end_line = parse_reference(reference)
    except ValueError:
        return None

    full_path = root / file_path

    if not full_path.is_file():
        return None

    try:
        file_content = full_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None

    lines = file_content.splitlines()

    if ref_type == "file":
        content = file_content
    elif ref_type in ("line", "range"):
        # Convert to 0-indexed
        start_idx = start_line - 1
        end_idx = end_line  # end_line is inclusive, so don't subtract 1

        if start_idx < 0 or end_idx > len(lines):
            return None

        content = "\n".join(lines[start_idx:end_idx])
    else:
        return None

    return CodeReference(
        reference=reference,
        file_path=str(file_path),
        ref_type=ref_type,
        start_line=start_line,
        end_line=end_line,
        content=content,
        hash=compute_hash(content),
    )
