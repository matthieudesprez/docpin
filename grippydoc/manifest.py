"""Manifest management for storing and comparing code block hashes."""

import json
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime

from .parser import CodeBlock


GRIPPYDOC_DIR = ".grippydoc"
MANIFEST_FILE = "manifest.json"
CONFIG_FILE = "config.json"


@dataclass
class ManifestEntry:
    """A single entry in the manifest."""
    id: str
    file_path: str
    start_line: int
    end_line: int
    hash: str
    recorded_at: str


@dataclass
class Manifest:
    """The grippydoc manifest containing all tracked code blocks."""
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
            "extensions": [
                ".py", ".js", ".ts", ".jsx", ".tsx",
                ".go", ".rs", ".rb", ".java", ".c", ".cpp", ".h",
            ],
            "exclude_dirs": [
                ".git", ".grippydoc", "node_modules", "__pycache__",
                ".venv", "venv", "dist", "build",
            ],
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


def record_blocks(root: Path, blocks: list[CodeBlock]) -> Manifest:
    """Record code blocks to the manifest."""
    timestamp = datetime.utcnow().isoformat() + "Z"

    entries = {}
    for block in blocks:
        entries[block.id] = ManifestEntry(
            id=block.id,
            file_path=block.file_path,
            start_line=block.start_line,
            end_line=block.end_line,
            hash=block.hash,
            recorded_at=timestamp,
        )

    manifest = Manifest(version="1", entries=entries)
    save_manifest(root, manifest)

    return manifest


@dataclass
class StaleLink:
    """Represents a documentation link that may be stale."""
    block_id: str
    doc_file: str
    doc_line: int
    code_file: str
    old_hash: str
    new_hash: str


def check_blocks(
    root: Path,
    blocks: list[CodeBlock],
    manifest: Manifest,
) -> list[StaleLink]:
    """Check code blocks against the manifest and find stale links."""
    from .scanner import scan_markdown_files

    stale = []
    changed_ids = set()

    # Find blocks with changed hashes
    for block in blocks:
        if block.id in manifest.entries:
            entry = manifest.entries[block.id]
            if entry.hash != block.hash:
                changed_ids.add(block.id)

    if not changed_ids:
        return stale

    # Find documentation links to changed blocks
    doc_links = scan_markdown_files(root)

    for link in doc_links:
        if link.block_id in changed_ids:
            block = next((b for b in blocks if b.id == link.block_id), None)
            entry = manifest.entries.get(link.block_id)

            if block and entry:
                stale.append(StaleLink(
                    block_id=link.block_id,
                    doc_file=link.file_path,
                    doc_line=link.line_number,
                    code_file=block.file_path,
                    old_hash=entry.hash,
                    new_hash=block.hash,
                ))

    return stale
