"""Scanner for finding grip references in Markdown files."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DocReference:
    """Represents a grip reference found in a Markdown file."""
    reference: str      # The reference string (e.g., "src/auth.py:10-20")
    doc_file: str       # Path to the markdown file
    line_number: int    # Line number in the markdown file


# Pattern to match [grip:reference] syntax in markdown
# Captures everything between [grip: and ]
GRIP_PATTERN = re.compile(r'\[grip:([^\]]+)\]')

# Pattern to match fenced code block delimiters (``` or ~~~, 3+ chars)
CODE_FENCE_PATTERN = re.compile(r'^(`{3,}|~{3,})')

# Pattern to match inline code (backticks)
INLINE_CODE_PATTERN = re.compile(r'`[^`]+`')


def parse_markdown(file_path: Path) -> list[DocReference]:
    """Parse a Markdown file and extract all grip references.

    Skips references inside:
    - Fenced code blocks (```)
    - Inline code (`...`)
    """
    refs = []

    try:
        content = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return refs

    in_code_block = False

    for line_num, line in enumerate(content.splitlines(), start=1):
        # Toggle code block state on fence markers
        if CODE_FENCE_PATTERN.match(line):
            in_code_block = not in_code_block
            continue

        # Skip lines inside code blocks
        if in_code_block:
            continue

        # Remove inline code before searching for grip references
        line_without_code = INLINE_CODE_PATTERN.sub('', line)

        for match in GRIP_PATTERN.finditer(line_without_code):
            refs.append(DocReference(
                reference=match.group(1).strip(),
                doc_file=str(file_path),
                line_number=line_num,
            ))

    return refs


def scan_markdown_files(
    root: Path,
    exclude_dirs: list[str] | None = None,
) -> list[DocReference]:
    """Scan a directory recursively for grip references in Markdown files."""
    if exclude_dirs is None:
        exclude_dirs = [
            ".git", ".grippydoc", ".venv", "venv",
            "node_modules", "__pycache__", ".tox", ".nox",
        ]

    refs = []

    for path in root.rglob("*.md"):
        if not any(excluded in path.parts for excluded in exclude_dirs):
            refs.extend(parse_markdown(path))

    return refs
