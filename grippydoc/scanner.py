"""Scanner for finding grip links in Markdown files."""

import re
from pathlib import Path
from dataclasses import dataclass


@dataclass
class DocLink:
    """Represents a grip link in a Markdown file."""
    block_id: str
    file_path: str
    line_number: int


# Pattern to match [grip:id] syntax in markdown
LINK_PATTERN = re.compile(r'\[grip:([^\]]+)\]')


def parse_markdown(file_path: Path) -> list[DocLink]:
    """Parse a Markdown file and extract all grip links."""
    links = []

    try:
        content = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return links

    for line_num, line in enumerate(content.splitlines(), start=1):
        for match in LINK_PATTERN.finditer(line):
            links.append(DocLink(
                block_id=match.group(1),
                file_path=str(file_path),
                line_number=line_num,
            ))

    return links


def scan_markdown_files(
    root: Path,
    exclude_dirs: list[str] | None = None,
) -> list[DocLink]:
    """Scan a directory recursively for grip links in Markdown files."""
    if exclude_dirs is None:
        exclude_dirs = [".git", ".grippydoc", "node_modules", "__pycache__"]

    links = []

    for path in root.rglob("*.md"):
        if not any(excluded in path.parts for excluded in exclude_dirs):
            links.extend(parse_markdown(path))

    return links
