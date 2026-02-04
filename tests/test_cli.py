"""Tests for the CLI module."""

from argparse import Namespace

from grippydoc.cli import cmd_check, cmd_record
from grippydoc.manifest import init_grippydoc, load_manifest, record_references
from grippydoc.resolver import resolve_reference


class TestCmdRecord:
    """Tests for cmd_record function."""

    def test_reports_orphans_being_removed(self, tmp_path, capsys):
        # Setup: create file and markdown
        test_file = tmp_path / "test.py"
        test_file.write_text("content")

        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "doc.md").write_text("[grip:test.py]\n")

        # Initialize and record
        init_grippydoc(tmp_path)
        ref = resolve_reference("test.py", tmp_path)
        record_references(tmp_path, [ref])

        # Remove the reference from docs
        (docs / "doc.md").write_text("No more grip references here.\n")

        # Create a new reference so record has something to do
        test_file2 = tmp_path / "test2.py"
        test_file2.write_text("content2")
        (docs / "doc.md").write_text("[grip:test2.py]\n")

        # Run record command
        args = Namespace(path=str(tmp_path))
        result = cmd_record(args)

        captured = capsys.readouterr()
        assert result == 0
        assert "Removing 1 orphaned reference(s) from manifest:" in captured.out
        assert "[grip:test.py]" in captured.out

        # Verify manifest only has the new reference
        manifest = load_manifest(tmp_path)
        assert "test2.py" in manifest.entries
        assert "test.py" not in manifest.entries

    def test_no_orphan_message_when_none(self, tmp_path, capsys):
        # Setup: create file and markdown
        test_file = tmp_path / "test.py"
        test_file.write_text("content")

        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "doc.md").write_text("[grip:test.py]\n")

        # Initialize and record
        init_grippydoc(tmp_path)

        # Run record command
        args = Namespace(path=str(tmp_path))
        result = cmd_record(args)

        captured = capsys.readouterr()
        assert result == 0
        assert "orphaned" not in captured.out.lower()


class TestCmdCheck:
    """Tests for cmd_check function."""

    def test_separate_advice_for_stale_and_orphan(self, tmp_path, capsys):
        # Setup: create two files
        test_file1 = tmp_path / "test1.py"
        test_file1.write_text("original content")
        test_file2 = tmp_path / "test2.py"
        test_file2.write_text("content2")

        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "doc.md").write_text("[grip:test1.py]\n[grip:test2.py]\n")

        # Initialize and record
        init_grippydoc(tmp_path)
        ref1 = resolve_reference("test1.py", tmp_path)
        ref2 = resolve_reference("test2.py", tmp_path)
        record_references(tmp_path, [ref1, ref2])

        # Make test1 stale and test2 orphaned
        test_file1.write_text("modified content")
        (docs / "doc.md").write_text("[grip:test1.py]\n")

        # Run check command
        args = Namespace(path=str(tmp_path))
        result = cmd_check(args)

        captured = capsys.readouterr()
        assert result == 1
        assert "stale/broken references: update your documentation" in captured.out.lower()
        assert "orphaned references: run 'grippydoc record'" in captured.out.lower()

    def test_only_orphan_advice_when_no_stale(self, tmp_path, capsys):
        # Setup
        test_file = tmp_path / "test.py"
        test_file.write_text("content")

        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "doc.md").write_text("[grip:test.py]\n")

        # Initialize and record
        init_grippydoc(tmp_path)
        ref = resolve_reference("test.py", tmp_path)
        record_references(tmp_path, [ref])

        # Make it orphaned (remove from docs)
        (docs / "doc.md").write_text("No references.\n")

        # Run check command
        args = Namespace(path=str(tmp_path))
        result = cmd_check(args)

        captured = capsys.readouterr()
        assert result == 1
        assert "orphaned references: run 'grippydoc record'" in captured.out.lower()
        assert "stale/broken" not in captured.out.lower()
