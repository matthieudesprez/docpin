"""Tests for the CLI module."""

from argparse import Namespace

from grippydoc.cli import cmd_check, cmd_record, cmd_status
from grippydoc.manifest import record_references


class TestCmdRecord:
    """Tests for cmd_record function."""

    def test_record_output(self, tmp_path, capsys):
        # Setup: create file and markdown
        test_file = tmp_path / "test.py"
        test_file.write_text("content")

        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "doc.md").write_text("[grip:test.py]\n")

        args = Namespace(path=str(tmp_path))
        result = cmd_record(args)

        captured = capsys.readouterr()
        assert result == 0
        assert "Recorded 1 reference(s)." in captured.out

    def test_record_warns_on_unresolvable(self, tmp_path, capsys):
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "doc.md").write_text("[grip:nonexistent.py]\n")

        args = Namespace(path=str(tmp_path))
        result = cmd_record(args)

        captured = capsys.readouterr()
        assert "Warning" in captured.out
        assert "nonexistent.py" in captured.out


class TestCmdCheck:
    """Tests for cmd_check function."""

    def test_check_stale_output(self, tmp_path, capsys):
        # Setup
        test_file = tmp_path / "test.py"
        test_file.write_text("original content")

        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "doc.md").write_text("[grip:test.py]\n")

        # Record first
        record_references(tmp_path)

        # Modify the code
        test_file.write_text("modified content")

        args = Namespace(path=str(tmp_path))
        result = cmd_check(args)

        captured = capsys.readouterr()
        assert result == 1
        assert "stale" in captured.out.lower()
        assert "test.py" in captured.out
        assert "Run 'grippydoc record' to update hashes." in captured.out

    def test_check_unrecorded_output(self, tmp_path, capsys):
        # Setup: file exists, no hash recorded
        test_file = tmp_path / "test.py"
        test_file.write_text("content")

        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "doc.md").write_text("[grip:test.py]\n")

        args = Namespace(path=str(tmp_path))
        result = cmd_check(args)

        captured = capsys.readouterr()
        assert result == 1
        assert "unrecorded" in captured.out.lower()
        assert "test.py" in captured.out

    def test_check_all_ok(self, tmp_path, capsys):
        # Setup
        test_file = tmp_path / "test.py"
        test_file.write_text("content")

        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "doc.md").write_text("[grip:test.py]\n")

        # Record
        record_references(tmp_path)

        args = Namespace(path=str(tmp_path))
        result = cmd_check(args)

        captured = capsys.readouterr()
        assert result == 0
        assert "All documentation references are up to date." in captured.out


class TestCmdStatus:
    """Tests for cmd_status function."""

    def test_status_shows_states(self, tmp_path, capsys):
        # Setup: one OK, one CHANGED, one MISSING, one UNRECORDED
        ok_file = tmp_path / "ok.py"
        ok_file.write_text("ok content")

        changed_file = tmp_path / "changed.py"
        changed_file.write_text("original")

        unrecorded_file = tmp_path / "unrecorded.py"
        unrecorded_file.write_text("content")

        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "doc.md").write_text(
            "[grip:ok.py]\n"
            "[grip:changed.py]\n"
            "[grip:missing.py]\n"
            "[grip:unrecorded.py]\n"
        )

        # Record first two (ok and changed)
        record_references(tmp_path)

        # Now modify changed.py
        changed_file.write_text("modified")

        # Manually add an unrecorded reference by editing the file
        # We need to re-read the recorded content and append unrecorded ref
        content = (docs / "doc.md").read_text()
        # The record call above would have written hashes for ok.py, changed.py
        # but missing.py would have been an error (no file), and unrecorded.py got a hash.
        # Let's set up more carefully:

        # Reset: create a fresh scenario
        (docs / "doc.md").write_text("")
        ok_file.write_text("ok content")
        changed_file.write_text("original")

        # First write and record ok.py and changed.py
        (docs / "doc.md").write_text("[grip:ok.py]\n[grip:changed.py]\n")
        record_references(tmp_path)

        # Now modify changed.py
        changed_file.write_text("modified")

        # Add unrecorded and missing refs (manually, without recording)
        recorded_content = (docs / "doc.md").read_text()
        (docs / "doc.md").write_text(
            recorded_content + "[grip:unrecorded.py]\n[grip:missing.py]\n"
        )

        args = Namespace(path=str(tmp_path))
        result = cmd_status(args)

        captured = capsys.readouterr()
        assert result == 0
        assert "[OK]" in captured.out
        assert "[CHANGED]" in captured.out
        assert "[MISSING]" in captured.out
        assert "[UNRECORDED]" in captured.out
