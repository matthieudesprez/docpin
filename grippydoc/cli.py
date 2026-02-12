"""Command-line interface for GrippyDoc."""

import argparse
import difflib
import sys
from pathlib import Path

from . import __version__
from .manifest import (
    check_references,
    get_grippydoc_dir,
    init_grippydoc,
    load_manifest,
    record_references,
)
from .resolver import resolve_reference
from .scanner import scan_markdown_files


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
    """Record code reference hashes to the manifest."""
    root = Path(args.path).resolve()

    if not get_grippydoc_dir(root).exists():
        print("Error: GrippyDoc not initialized. Run 'grippydoc init' first.", file=sys.stderr)
        return 1

    # Find all grip references in markdown files
    doc_refs = scan_markdown_files(root)

    if not doc_refs:
        print("No grip references found in markdown files.")
        return 0

    # Check for orphans before recording (references in manifest but not in docs)
    old_manifest = load_manifest(root)
    if old_manifest and old_manifest.entries:
        doc_ref_set = {ref.reference for ref in doc_refs}
        orphaned = [
            entry for ref_key, entry in old_manifest.entries.items()
            if ref_key not in doc_ref_set
        ]
        if orphaned:
            print(f"Removing {len(orphaned)} orphaned reference(s) from manifest:")
            for entry in orphaned:
                print(f"  [grip:{entry.reference}]")
            print()

    # Resolve each reference to code
    resolved = []
    errors = []

    for doc_ref in doc_refs:
        code_ref = resolve_reference(doc_ref.reference, root)
        if code_ref:
            resolved.append(code_ref)
        else:
            errors.append(doc_ref)

    if errors:
        print(f"Warning: {len(errors)} reference(s) could not be resolved:")
        for err in errors:
            rel_doc = Path(err.doc_file).relative_to(root)
            print(f"  {rel_doc}:{err.line_number} -> [grip:{err.reference}]")
        print()

    if not resolved:
        print("No valid references to record.")
        return 1 if errors else 0

    # Record to manifest
    manifest = record_references(root, resolved)

    print(f"Recorded {len(manifest.entries)} reference(s):")
    for entry in manifest.entries.values():
        ref_display = entry.reference
        if entry.ref_type == "file":
            ref_display = f"{entry.file_path} (whole file)"
        elif entry.ref_type == "line":
            ref_display = f"{entry.file_path}:{entry.start_line}"
        elif entry.ref_type == "range":
            ref_display = f"{entry.file_path}:{entry.start_line}-{entry.end_line}"
        print(f"  [grip:{ref_display}]")

    return 0


def _format_diff(old_content: str | None, new_content: str | None, reference: str) -> str | None:
    """Produce a unified diff between old and new code content."""
    if old_content is None:
        return None

    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True) if new_content else []

    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=f"a/{reference} (recorded)",
        tofile=f"b/{reference} (current)",
    )
    return "".join(diff)


def _get_doc_context(doc_file: str, doc_line: int, context: int = 3) -> str | None:
    """Read surrounding lines from a markdown file around the grip reference."""
    try:
        lines = Path(doc_file).read_text(encoding="utf-8").splitlines()
    except OSError:
        return None

    total = len(lines)
    start = max(0, doc_line - 1 - context)
    end = min(total, doc_line + context)

    result = []
    for i in range(start, end):
        line_num = i + 1
        if line_num == doc_line:
            prefix = f"  >>> {line_num:>4} | "
        else:
            prefix = f"      {line_num:>4} | "
        result.append(prefix + lines[i])

    return "\n".join(result)


def cmd_check(args: argparse.Namespace) -> int:
    """Check for stale documentation references."""
    root = Path(args.path).resolve()

    manifest = load_manifest(root)
    if manifest is None:
        print("Error: No manifest found. Run 'grippydoc record' first.", file=sys.stderr)
        return 1

    stale, broken, orphaned = check_references(root, manifest)

    has_issues = False
    show_diff = getattr(args, "diff", False)

    if broken:
        has_issues = True
        print(f"Found {len(broken)} broken reference(s):\n")
        for ref in broken:
            rel_doc = Path(ref.doc_file).relative_to(root)
            print(f"  [grip:{ref.reference}]")
            print(f"    Location: {rel_doc}:{ref.doc_line}")
            print(f"    Error: {ref.reason}")
            print()

    if stale:
        has_issues = True
        print(f"Found {len(stale)} stale reference(s):\n")
        for ref in stale:
            rel_doc = Path(ref.doc_file).relative_to(root)
            print(f"  [grip:{ref.reference}]")
            print(f"    Location: {rel_doc}:{ref.doc_line}")
            print(f"    Hash: {ref.old_hash[:8]}... -> {ref.new_hash[:8]}...")
            if show_diff:
                doc_ctx = _get_doc_context(ref.doc_file, ref.doc_line)
                if doc_ctx:
                    print(f"    Documentation context ({rel_doc}):")
                    print(doc_ctx)
                diff_text = _format_diff(ref.old_content, ref.new_content, ref.reference)
                if diff_text:
                    print("    Code diff:")
                    for line in diff_text.splitlines():
                        print(f"      {line}")
                elif ref.old_content is None:
                    print("    No diff available (re-run 'grippydoc record' to enable diffs)")
            print()

    if orphaned:
        has_issues = True
        print(f"Found {len(orphaned)} orphaned reference(s):\n")
        for ref in orphaned:
            print(f"  [grip:{ref.reference}]")
            print(f"    File: {ref.file_path}")
            print("    Status: No longer referenced in documentation")
            print()

    if has_issues:
        if stale or broken:
            print("For stale/broken references: update your documentation, then run 'grippydoc record'.")
        if orphaned:
            print("For orphaned references: run 'grippydoc record' to remove them from the manifest.")
        return 1

    print("All documentation references are up to date.")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    """Show the status of tracked references."""
    root = Path(args.path).resolve()

    manifest = load_manifest(root)
    if manifest is None:
        print("GrippyDoc not initialized or no references recorded.")
        return 0

    print(f"Tracking {len(manifest.entries)} reference(s):\n")

    for entry in manifest.entries.values():
        # Check current status
        code_ref = resolve_reference(entry.reference, root)

        if code_ref is None:
            status = "MISSING"
        elif code_ref.hash != entry.hash:
            status = "CHANGED"
        else:
            status = "OK"

        print(f"  [{status}] {entry.reference}")
        if entry.ref_type == "range":
            print(f"         {entry.file_path}:{entry.start_line}-{entry.end_line}")
        elif entry.ref_type == "line":
            print(f"         {entry.file_path}:{entry.start_line}")
        else:
            print(f"         {entry.file_path}")
        print()

    return 0


def main() -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog="grippydoc",
        description="Prevent documentation drift by linking Markdown to code.",
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
        help="Record code reference hashes to the manifest",
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
    check_parser.add_argument(
        "--diff",
        action="store_true",
        default=False,
        help="Show code diffs and documentation context for stale references",
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
        "init": cmd_init,
        "record": cmd_record,
        "check": cmd_check,
        "status": cmd_status,
    }

    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
