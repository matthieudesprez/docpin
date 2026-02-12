"""Tests for the manifest module."""

from grippydoc.manifest import check_references, record_references
from grippydoc.resolver import resolve_reference


class TestCheckReferences:
    """Tests for check_references function."""

    def test_check_detects_stale(self, tmp_path):
        # Setup: create file and markdown with hash
        test_file = tmp_path / "test.py"
        test_file.write_text("original content")

        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "doc.md").write_text("[grip:test.py]\n")

        # Record to get the hash
        record_references(tmp_path)
        content = (docs / "doc.md").read_text()
        assert " @" in content

        # Modify the file
        test_file.write_text("modified content")

        # Check
        stale, broken, unrecorded = check_references(tmp_path)

        assert len(stale) == 1
        assert stale[0].reference == "test.py"
        assert len(broken) == 0
        assert len(unrecorded) == 0

    def test_check_detects_broken(self, tmp_path):
        # Setup: markdown pointing to non-existent file with hash
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "doc.md").write_text("[grip:nonexistent.py @abc123]\n")

        stale, broken, unrecorded = check_references(tmp_path)

        assert len(broken) == 1
        assert broken[0].reference == "nonexistent.py"

    def test_check_detects_unrecorded(self, tmp_path):
        # Setup: file exists, markdown has no hash
        test_file = tmp_path / "test.py"
        test_file.write_text("content")

        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "doc.md").write_text("[grip:test.py]\n")

        stale, broken, unrecorded = check_references(tmp_path)

        assert len(unrecorded) == 1
        assert unrecorded[0].reference == "test.py"
        assert len(stale) == 0
        assert len(broken) == 0

    def test_check_no_issues_when_up_to_date(self, tmp_path):
        # Setup
        test_file = tmp_path / "test.py"
        test_file.write_text("content")

        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "doc.md").write_text("[grip:test.py]\n")

        # Record to get correct hash
        record_references(tmp_path)

        # Check without modifying
        stale, broken, unrecorded = check_references(tmp_path)

        assert len(stale) == 0
        assert len(broken) == 0
        assert len(unrecorded) == 0


class TestRecordReferences:
    """Tests for record_references function."""

    def test_record_writes_hashes_inline(self, tmp_path):
        # Setup
        test_file = tmp_path / "test.py"
        test_file.write_text("content")

        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "doc.md").write_text("[grip:test.py]\n")

        count, errors = record_references(tmp_path)

        assert count == 1
        assert len(errors) == 0

        # Verify the markdown was updated with a hash
        content = (docs / "doc.md").read_text()
        assert " @" in content
        assert content.startswith("[grip:test.py @")

    def test_record_updates_existing_hashes(self, tmp_path):
        # Setup
        test_file = tmp_path / "test.py"
        test_file.write_text("original content")

        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "doc.md").write_text("[grip:test.py]\n")

        # First record
        record_references(tmp_path)
        first_content = (docs / "doc.md").read_text()

        # Modify code
        test_file.write_text("modified content")

        # Re-record
        count, errors = record_references(tmp_path)

        assert count == 1
        second_content = (docs / "doc.md").read_text()
        assert second_content != first_content
        assert " @" in second_content

    def test_record_reports_errors(self, tmp_path):
        # Setup: markdown pointing to non-existent file
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "doc.md").write_text("[grip:nonexistent.py]\n")

        count, errors = record_references(tmp_path)

        assert count == 0
        assert len(errors) == 1
        assert errors[0].reference == "nonexistent.py"
