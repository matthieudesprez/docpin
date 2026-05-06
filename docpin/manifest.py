"""Reference checking and recording using inline hashes."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .resolver import resolve_reference
from .scanner import DocReference, scan_markdown_files, update_markdown_hashes


@dataclass
class StaleReference:
    """Represents a documentation reference whose code has changed."""
    reference: str
    doc_file: str
    doc_line: int
    old_hash: str
    new_hash: str


@dataclass
class BrokenReference:
    """Represents a documentation reference that cannot be resolved."""
    reference: str
    doc_file: str
    doc_line: int
    reason: str


@dataclass
class UnrecordedReference:
    """Represents a documentation reference without an inline hash."""
    reference: str
    doc_file: str
    doc_line: int


def record_references(
    root: Path,
) -> tuple[int, list[DocReference]]:
    """Record code reference hashes inline in markdown files.

    Scans all markdown files for pin references, resolves each one,
    and writes the hash back into the markdown.

    Returns:
        Tuple of (recorded_count, error_doc_refs)
    """
    doc_refs = scan_markdown_files(root)

    # Build hash map and collect errors
    hash_map: dict[str, str] = {}
    errors: list[DocReference] = []

    for doc_ref in doc_refs:
        if doc_ref.reference in hash_map:
            continue
        resolved = resolve_reference(doc_ref.reference, root)
        if resolved is not None:
            hash_map[doc_ref.reference] = resolved.hash
        else:
            errors.append(doc_ref)

    # Group refs by file and update each
    files: dict[str, list[DocReference]] = {}
    for doc_ref in doc_refs:
        files.setdefault(doc_ref.doc_file, []).append(doc_ref)

    recorded_count = 0
    for file_path in files:
        recorded_count += update_markdown_hashes(Path(file_path), hash_map)

    return recorded_count, errors


def check_references(
    root: Path,
) -> tuple[list[StaleReference], list[BrokenReference], list[UnrecordedReference]]:
    """Check documentation references against current code.

    Returns:
        Tuple of (stale, broken, unrecorded) reference lists
    """
    doc_refs = scan_markdown_files(root)

    stale: list[StaleReference] = []
    broken: list[BrokenReference] = []
    unrecorded: list[UnrecordedReference] = []

    for doc_ref in doc_refs:
        resolved = resolve_reference(doc_ref.reference, root)

        if resolved is None:
            broken.append(BrokenReference(
                reference=doc_ref.reference,
                doc_file=doc_ref.doc_file,
                doc_line=doc_ref.line_number,
                reason="Could not resolve reference (file not found or invalid syntax)",
            ))
            continue

        if doc_ref.recorded_hash is None:
            unrecorded.append(UnrecordedReference(
                reference=doc_ref.reference,
                doc_file=doc_ref.doc_file,
                doc_line=doc_ref.line_number,
            ))
            continue

        if doc_ref.recorded_hash != resolved.hash:
            stale.append(StaleReference(
                reference=doc_ref.reference,
                doc_file=doc_ref.doc_file,
                doc_line=doc_ref.line_number,
                old_hash=doc_ref.recorded_hash,
                new_hash=resolved.hash,
            ))

    return stale, broken, unrecorded
