"""Resolver for extracting code content from file references."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

from .hasher import compute_hash


@dataclass
class CodeReference:
    """Represents a resolved code reference."""
    reference: str      # Original reference string (e.g., "src/auth.py:10-20")
    file_path: str      # Resolved file path
    ref_type: str       # "file", "line", "range", or "symbol"
    start_line: int | None
    end_line: int | None
    content: str
    hash: str


# Pattern to parse grip references:
# - file.py          -> whole file
# - file.py:42       -> single line
# - file.py:42-58    -> line range
# - file.py#symbol   -> symbol (function, class, method, or variable)
REFERENCE_PATTERN = re.compile(
    r'^(?P<file>[^:#]+?)(?::(?P<start>\d+)(?:-(?P<end>\d+))?|#(?P<symbol>[\w.]+))?$'
)


def parse_reference(reference: str) -> tuple[str, str, int | None, int | None, str | None]:
    """Parse a reference string into components.

    Returns: (file_path, ref_type, start_line, end_line, symbol)
    """
    match = REFERENCE_PATTERN.match(reference.strip())
    if not match:
        raise ValueError(f"Invalid reference format: {reference}")

    file_path = match.group("file")
    start = match.group("start")
    end = match.group("end")
    symbol = match.group("symbol")

    if symbol is not None:
        return file_path, "symbol", None, None, symbol
    elif start is None:
        return file_path, "file", None, None, None
    elif end is None:
        line = int(start)
        return file_path, "line", line, line, None
    else:
        return file_path, "range", int(start), int(end), None


def _get_node_end_line(node: ast.AST) -> int:
    """Get the end line of an AST node, handling decorators."""
    return node.end_lineno if node.end_lineno else node.lineno


def _get_node_start_line(node: ast.AST) -> int:
    """Get the start line of an AST node, including decorators."""
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        if node.decorator_list:
            return node.decorator_list[0].lineno
    return node.lineno


def resolve_symbol(file_content: str, symbol: str) -> tuple[int, int] | None:
    """Resolve a symbol name to its line range in a Python file.

    Args:
        file_content: The Python file content
        symbol: The symbol to find (e.g., "function_name", "ClassName", "ClassName.method")

    Returns:
        Tuple of (start_line, end_line) or None if not found
    """
    try:
        tree = ast.parse(file_content)
    except SyntaxError:
        return None

    parts = symbol.split(".")

    def find_in_body(body: list[ast.stmt], names: list[str]) -> tuple[int, int] | None:
        """Recursively find a symbol in a list of AST statements."""
        if not names:
            return None

        target_name = names[0]
        remaining = names[1:]

        for node in body:
            # Check functions (sync and async)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name == target_name:
                    if not remaining:
                        return _get_node_start_line(node), _get_node_end_line(node)
                    # Look for nested functions/classes
                    return find_in_body(node.body, remaining)

            # Check classes
            elif isinstance(node, ast.ClassDef):
                if node.name == target_name:
                    if not remaining:
                        return _get_node_start_line(node), _get_node_end_line(node)
                    # Look for methods or nested classes
                    return find_in_body(node.body, remaining)

            # Check assignments (top-level variables/constants)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == target_name:
                        if not remaining:
                            return node.lineno, _get_node_end_line(node)

            # Check annotated assignments
            elif isinstance(node, ast.AnnAssign):
                if isinstance(node.target, ast.Name) and node.target.id == target_name:
                    if not remaining:
                        return node.lineno, _get_node_end_line(node)

        return None

    return find_in_body(tree.body, parts)


def resolve_reference(reference: str, root: Path) -> CodeReference | None:
    """Resolve a reference to its code content.

    Args:
        reference: The reference string (e.g., "src/auth.py:10-20" or "src/auth.py#login")
        root: The project root directory

    Returns:
        CodeReference with the resolved content and hash, or None if not found
    """
    try:
        file_path, ref_type, start_line, end_line, symbol = parse_reference(reference)
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
    elif ref_type == "symbol":
        # Symbol references only supported for Python files
        if not file_path.endswith(".py"):
            return None

        line_range = resolve_symbol(file_content, symbol)
        if line_range is None:
            return None

        start_line, end_line = line_range
        start_idx = start_line - 1
        end_idx = end_line

        content = "\n".join(lines[start_idx:end_idx])
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
