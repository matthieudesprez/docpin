"""Command-line interface for GrippyDoc."""

import argparse
import sys
from pathlib import Path

from . import __version__
from .parser import scan_directory
from .manifest import (
    init_grippydoc,
    load_manifest,
    record_blocks,
    check_blocks,
    get_grippydoc_dir,
)


def cmd_init(args: argparse.Namespace) -> int:
    """Initialize grippydoc in the current directory."""
    root = Path(args.path).resolve()

    if not root.is_dir():
        print(f"Error: {root} is not a directory", file=sys.stderr)
        return 1

    grippydoc_dir = get_grippydoc_dir(root)
    if grippydoc_dir.exists():
        print(f"GrippyDoc already initialized at {grippydoc_dir}")
        return 0

    init_grippydoc(root)
    print(f"Initialized GrippyDoc at {grippydoc_dir}")
    return 0


def cmd_record(args: argparse.Namespace) -> int:
    """Record code block hashes to the manifest."""
    root = Path(args.path).resolve()

    if not get_grippydoc_dir(root).exists():
        print("Error: GrippyDoc not initialized. Run 'grippydoc init' first.", file=sys.stderr)
        return 1

    blocks = scan_directory(root)

    if not blocks:
        print("No grip-tagged code blocks found.")
        return 0

    manifest = record_blocks(root, blocks)

    print(f"Recorded {len(manifest.entries)} code block(s):")
    for entry in manifest.entries.values():
        rel_path = Path(entry.file_path).relative_to(root)
        print(f"  [{entry.id}] {rel_path}:{entry.start_line}-{entry.end_line}")

    return 0


def cmd_check(args: argparse.Namespace) -> int:
    """Check for stale documentation links."""
    root = Path(args.path).resolve()

    manifest = load_manifest(root)
    if manifest is None:
        print("Error: No manifest found. Run 'grippydoc record' first.", file=sys.stderr)
        return 1

    blocks = scan_directory(root)
    stale_links = check_blocks(root, blocks, manifest)

    if not stale_links:
        print("All documentation links are up to date.")
        return 0

    print(f"Found {len(stale_links)} stale documentation link(s):\n")

    for link in stale_links:
        doc_rel = Path(link.doc_file).relative_to(root)
        code_rel = Path(link.code_file).relative_to(root)
        print(f"  [{link.block_id}]")
        print(f"    Documentation: {doc_rel}:{link.doc_line}")
        print(f"    Code changed:  {code_rel}")
        print(f"    Hash: {link.old_hash[:8]}... -> {link.new_hash[:8]}...")
        print()

    print("Run 'grippydoc record' after updating documentation to clear this warning.")
    return 1


def cmd_status(args: argparse.Namespace) -> int:
    """Show the status of tracked code blocks."""
    root = Path(args.path).resolve()

    manifest = load_manifest(root)
    if manifest is None:
        print("GrippyDoc not initialized or no blocks recorded.")
        return 0

    blocks = scan_directory(root)
    block_map = {b.id: b for b in blocks}

    print(f"Tracking {len(manifest.entries)} code block(s):\n")

    for entry in manifest.entries.values():
        rel_path = Path(entry.file_path).relative_to(root)
        current = block_map.get(entry.id)

        if current is None:
            status = "MISSING"
        elif current.hash != entry.hash:
            status = "CHANGED"
        else:
            status = "OK"

        print(f"  [{entry.id}] {status}")
        print(f"    File: {rel_path}:{entry.start_line}-{entry.end_line}")
        print()

    return 0


def main() -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog="grippydoc",
        description="Prevent documentation drift by linking Markdown to code blocks.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # init command
    init_parser = subparsers.add_parser(
        "init",
        help="Initialize GrippyDoc in the current directory",
    )
    init_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to initialize (default: current directory)",
    )

    # record command
    record_parser = subparsers.add_parser(
        "record",
        help="Record code block hashes to the manifest",
    )
    record_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to scan (default: current directory)",
    )

    # check command
    check_parser = subparsers.add_parser(
        "check",
        help="Check for stale documentation links",
    )
    check_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to check (default: current directory)",
    )

    # status command
    status_parser = subparsers.add_parser(
        "status",
        help="Show status of tracked code blocks",
    )
    status_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to check (default: current directory)",
    )

    args = parser.parse_args()

    commands = {
        "init": cmd_init,
        "record": cmd_record,
        "check": cmd_check,
        "status": cmd_status,
    }

    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
