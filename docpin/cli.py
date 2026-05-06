"""Command-line interface for docpin."""

import argparse
import sys
from pathlib import Path

from . import __version__
from .manifest import check_references, record_references
from .resolver import resolve_reference
from .scanner import scan_markdown_files


def cmd_record(args: argparse.Namespace) -> int:
    """Record code reference hashes inline in markdown files."""
    root = Path(args.path).resolve()

    if not root.is_dir():
        print(f"Error: {root} is not a directory", file=sys.stderr)
        return 1

    count, errors = record_references(root)

    if errors:
        print(f"Warning: {len(errors)} reference(s) could not be resolved:")
        for err in errors:
            rel_doc = Path(err.doc_file).relative_to(root)
            print(f"  {rel_doc}:{err.line_number} -> [pin:{err.reference}]")
        print()

    if count == 0 and not errors:
        print("No pin references found in markdown files.")
        return 0

    print(f"Recorded {count} reference(s).")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    """Check for stale documentation references."""
    root = Path(args.path).resolve()

    stale, broken, unrecorded = check_references(root)

    has_issues = False

    if broken:
        has_issues = True
        print(f"Found {len(broken)} broken reference(s):\n")
        for ref in broken:
            rel_doc = Path(ref.doc_file).relative_to(root)
            print(f"  [pin:{ref.reference}]")
            print(f"    Location: {rel_doc}:{ref.doc_line}")
            print(f"    Error: {ref.reason}")
            print()

    if stale:
        has_issues = True
        print(f"Found {len(stale)} stale reference(s):\n")
        for ref in stale:
            rel_doc = Path(ref.doc_file).relative_to(root)
            print(f"  [pin:{ref.reference}]")
            print(f"    Location: {rel_doc}:{ref.doc_line}")
            print(f"    Hash: {ref.old_hash[:8]}... -> {ref.new_hash[:8]}...")
            print()

    if unrecorded:
        has_issues = True
        print(f"Found {len(unrecorded)} unrecorded reference(s):\n")
        for ref in unrecorded:
            rel_doc = Path(ref.doc_file).relative_to(root)
            print(f"  [pin:{ref.reference}]")
            print(f"    Location: {rel_doc}:{ref.doc_line}")
            print()

    if has_issues:
        print("Run 'docpin record' to update hashes.")
        return 1

    print("All documentation references are up to date.")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    """Show the status of tracked references."""
    root = Path(args.path).resolve()

    doc_refs = scan_markdown_files(root)

    if not doc_refs:
        print("No pin references found in markdown files.")
        return 0

    for doc_ref in doc_refs:
        code_ref = resolve_reference(doc_ref.reference, root)

        if code_ref is None:
            status = "MISSING"
        elif doc_ref.recorded_hash is None:
            status = "UNRECORDED"
        elif doc_ref.recorded_hash != code_ref.hash:
            status = "CHANGED"
        else:
            status = "OK"

        rel_doc = Path(doc_ref.doc_file).relative_to(root)
        print(f"  [{status}] {doc_ref.reference}")
        print(f"         {rel_doc}:{doc_ref.line_number}")
        print()

    return 0


def main() -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog="docpin",
        description="Prevent documentation drift by linking Markdown to code.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # record command
    record_parser = subparsers.add_parser(
        "record",
        help="Record code reference hashes inline in markdown files",
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
        help="Check for stale documentation references",
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
        help="Show status of tracked references",
    )
    status_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to check (default: current directory)",
    )

    args = parser.parse_args()

    commands = {
        "record": cmd_record,
        "check": cmd_check,
        "status": cmd_status,
    }

    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
