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
    recorded_hash: str | None = None  # Inline hash if present (e.g., "a1b2c3d4")


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
            raw = match.group(1).strip()
            if " @" in raw:
                ref_str, hash_str = raw.rsplit(" @", 1)
                reference = ref_str.strip()
                recorded_hash = hash_str.strip() or None
            else:
                reference = raw
                recorded_hash = None

            refs.append(DocReference(
                reference=reference,
                doc_file=str(file_path),
                line_number=line_num,
                recorded_hash=recorded_hash,
            ))

    return refs


def update_markdown_hashes(file_path: Path, hash_map: dict[str, str]) -> int:
    """Rewrite a markdown file in-place, updating grip reference hashes.

    Replaces [grip:ref] or [grip:ref @oldhash] with [grip:ref @newhash].

    Args:
        file_path: Path to the markdown file
        hash_map: Mapping of reference string to new hash

    Returns:
        Count of updated references
    """
    try:
        content = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return 0

    lines = content.splitlines(keepends=True)
    in_code_block = False
    updated_count = 0

    for i, line in enumerate(lines):
        # Toggle code block state on fence markers
        stripped = line.rstrip("\n\r")
        if CODE_FENCE_PATTERN.match(stripped):
            in_code_block = not in_code_block
            continue

        if in_code_block:
            continue

        # Mask inline code spans to avoid matching inside them
        masked = list(line)
        for m in INLINE_CODE_PATTERN.finditer(line):
            for j in range(m.start(), m.end()):
                masked[j] = ' '
        masked_line = ''.join(masked)

        # Find all grip matches on the masked line (to get correct positions)
        matches = list(GRIP_PATTERN.finditer(masked_line))
        if not matches:
            continue

        # Apply replacements right-to-left to preserve offsets
        new_line = line
        for m in reversed(matches):
            raw = m.group(1).strip()
            if " @" in raw:
                ref_str = raw.rsplit(" @", 1)[0].strip()
            else:
                ref_str = raw

            if ref_str not in hash_map:
                continue

            new_hash = hash_map[ref_str]
            replacement = f"[grip:{ref_str} @{new_hash}]"
            new_line = new_line[:m.start()] + replacement + new_line[m.end():]
            updated_count += 1

        lines[i] = new_line

    file_path.write_text(''.join(lines), encoding="utf-8")
    return updated_count


def scan_markdown_files(
    root: Path,
    exclude_dirs: list[str] | None = None,
) -> list[DocReference]:
    """Scan a directory recursively for grip references in Markdown files."""
    if exclude_dirs is None:
        exclude_dirs = [
            ".git", ".venv", "venv",
            "node_modules", "__pycache__", ".tox", ".nox",
        ]

    refs = []

    for path in root.rglob("*.md"):
        if not any(excluded in path.parts for excluded in exclude_dirs):
            refs.extend(parse_markdown(path))

    return refs
