"""Parser for extracting grip-tagged code blocks from source files."""

import re
from pathlib import Path
from dataclasses import dataclass

from .hasher import compute_hash


@dataclass
class CodeBlock:
    """Represents a grip-tagged code block."""
    id: str
    file_path: str
    start_line: int
    end_line: int
    content: str
    hash: str


# Pattern to match opening grip tag: # <grip id="...">
# Supports various comment styles: #, //, --, <!--
OPEN_PATTERN = re.compile(
    r'(?:#|//|--|<!--)\s*<grip\s+id=["\']([^"\']+)["\']\s*>',
    re.IGNORECASE
)

# Pattern to match closing grip tag: # </grip>
CLOSE_PATTERN = re.compile(
    r'(?:#|//|--|<!--)\s*</grip>\s*(?:-->)?',
    re.IGNORECASE
)


def parse_file(file_path: Path) -> list[CodeBlock]:
    """Parse a file and extract all grip-tagged code blocks."""
    blocks = []

    try:
        content = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return blocks

    lines = content.splitlines()
    current_block = None
    block_lines = []

    for line_num, line in enumerate(lines, start=1):
        if current_block is None:
            match = OPEN_PATTERN.search(line)
            if match:
                current_block = {
                    "id": match.group(1),
                    "start_line": line_num,
                }
                block_lines = []
        else:
            if CLOSE_PATTERN.search(line):
                content = "\n".join(block_lines)
                blocks.append(CodeBlock(
                    id=current_block["id"],
                    file_path=str(file_path),
                    start_line=current_block["start_line"],
                    end_line=line_num,
                    content=content,
                    hash=compute_hash(content),
                ))
                current_block = None
                block_lines = []
            else:
                block_lines.append(line)

    return blocks


def scan_directory(
    root: Path,
    extensions: list[str] | None = None,
    exclude_dirs: list[str] | None = None,
) -> list[CodeBlock]:
    """Scan a directory recursively for grip-tagged code blocks."""
    if extensions is None:
        extensions = [
            ".py", ".js", ".ts", ".jsx", ".tsx",
            ".go", ".rs", ".rb", ".java", ".c", ".cpp", ".h",
            ".sh", ".bash", ".zsh",
            ".sql", ".html", ".css", ".scss",
        ]

    if exclude_dirs is None:
        exclude_dirs = [
            ".git", ".grippydoc", "node_modules", "__pycache__",
            ".venv", "venv", "dist", "build", ".tox",
        ]

    blocks = []

    for path in root.rglob("*"):
        if path.is_file() and path.suffix in extensions:
            if not any(excluded in path.parts for excluded in exclude_dirs):
                blocks.extend(parse_file(path))

    return blocks
