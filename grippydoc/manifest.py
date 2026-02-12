"""Manifest management for storing and comparing reference hashes."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .resolver import CodeReference

GRIPPYDOC_DIR = ".grippydoc"
MANIFEST_FILE = "manifest.json"
CONFIG_FILE = "config.json"


@dataclass
class ManifestEntry:
    """A single entry in the manifest."""
    reference: str
    file_path: str
    ref_type: str
    start_line: int | None
    end_line: int | None
    hash: str
    recorded_at: str
    content: str | None = None


@dataclass
class Manifest:
    """The grippydoc manifest containing all tracked references."""
    version: str
    entries: dict[str, ManifestEntry]

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "entries": {k: asdict(v) for k, v in self.entries.items()},
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Manifest":
        entries = {}
        for k, v in data.get("entries", {}).items():
            entries[k] = ManifestEntry(**v)
        return cls(version=data.get("version", "1"), entries=entries)


def get_grippydoc_dir(root: Path) -> Path:
    """Get the .grippydoc directory path."""
    return root / GRIPPYDOC_DIR


def init_grippydoc(root: Path) -> Path:
    """Initialize the .grippydoc directory with config."""
    grippydoc_dir = get_grippydoc_dir(root)
    grippydoc_dir.mkdir(exist_ok=True)

    config_path = grippydoc_dir / CONFIG_FILE
    if not config_path.exists():
        config = {
            "version": "1",
        }
        config_path.write_text(json.dumps(config, indent=2))

    manifest_path = grippydoc_dir / MANIFEST_FILE
    if not manifest_path.exists():
        manifest = Manifest(version="1", entries={})
        manifest_path.write_text(json.dumps(manifest.to_dict(), indent=2))

    return grippydoc_dir


def load_manifest(root: Path) -> Manifest | None:
    """Load the manifest from disk."""
    manifest_path = get_grippydoc_dir(root) / MANIFEST_FILE

    if not manifest_path.exists():
        return None

    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        return Manifest.from_dict(data)
    except (json.JSONDecodeError, OSError):
        return None


def save_manifest(root: Path, manifest: Manifest) -> None:
    """Save the manifest to disk."""
    manifest_path = get_grippydoc_dir(root) / MANIFEST_FILE
    manifest_path.write_text(json.dumps(manifest.to_dict(), indent=2))


def record_references(root: Path, refs: list[CodeReference]) -> Manifest:
    """Record code references to the manifest."""
    timestamp = datetime.now(timezone.utc).isoformat()

    entries = {}
    for ref in refs:
        entries[ref.reference] = ManifestEntry(
            reference=ref.reference,
            file_path=ref.file_path,
            ref_type=ref.ref_type,
            start_line=ref.start_line,
            end_line=ref.end_line,
            hash=ref.hash,
            recorded_at=timestamp,
            content=ref.content,
        )

    manifest = Manifest(version="1", entries=entries)
    save_manifest(root, manifest)

    return manifest


@dataclass
class StaleReference:
    """Represents a documentation reference that may be stale."""
    reference: str
    doc_file: str
    doc_line: int
    old_hash: str
    new_hash: str
    old_content: str | None = None
    new_content: str | None = None


@dataclass
class BrokenReference:
    """Represents a documentation reference that cannot be resolved."""
    reference: str
    doc_file: str
    doc_line: int
    reason: str


@dataclass
class OrphanedReference:
    """Represents a manifest entry with no corresponding documentation reference."""
    reference: str
    file_path: str
    ref_type: str


def check_references(
    root: Path,
    manifest: Manifest,
) -> tuple[list[StaleReference], list[BrokenReference], list[OrphanedReference]]:
    """Check documentation references against the manifest."""
    from .resolver import resolve_reference
    from .scanner import scan_markdown_files

    stale = []
    broken = []

    doc_refs = scan_markdown_files(root)

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

        if doc_ref.reference in manifest.entries:
            entry = manifest.entries[doc_ref.reference]
            if entry.hash != resolved.hash:
                stale.append(StaleReference(
                    reference=doc_ref.reference,
                    doc_file=doc_ref.doc_file,
                    doc_line=doc_ref.line_number,
                    old_hash=entry.hash,
                    new_hash=resolved.hash,
                    old_content=entry.content,
                    new_content=resolved.content,
                ))
        else:
            # Reference not in manifest - treat as new (not stale)
            pass

    # Find orphaned references (in manifest but not in docs)
    doc_ref_set = {doc_ref.reference for doc_ref in doc_refs}
    orphaned = []
    for ref_key, entry in manifest.entries.items():
        if ref_key not in doc_ref_set:
            orphaned.append(OrphanedReference(
                reference=entry.reference,
                file_path=entry.file_path,
                ref_type=entry.ref_type,
            ))

    return stale, broken, orphaned
