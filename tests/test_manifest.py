"""Tests for the manifest module."""

import pytest
import json
from pathlib import Path

from grippydoc.manifest import (
    init_grippydoc,
    load_manifest,
    save_manifest,
    record_references,
    check_references,
    get_grippydoc_dir,
    Manifest,
    ManifestEntry,
)
from grippydoc.resolver import CodeReference


class TestInitGrippydoc:
    """Tests for init_grippydoc function."""

    def test_creates_directory(self, tmp_path):
        init_grippydoc(tmp_path)

        grippydoc_dir = tmp_path / ".grippydoc"
        assert grippydoc_dir.exists()
        assert grippydoc_dir.is_dir()

    def test_creates_config(self, tmp_path):
        init_grippydoc(tmp_path)

        config_file = tmp_path / ".grippydoc" / "config.json"
        assert config_file.exists()

        config = json.loads(config_file.read_text())
        assert "version" in config

    def test_creates_manifest(self, tmp_path):
        init_grippydoc(tmp_path)

        manifest_file = tmp_path / ".grippydoc" / "manifest.json"
        assert manifest_file.exists()

        manifest = json.loads(manifest_file.read_text())
        assert manifest["version"] == "1"
        assert manifest["entries"] == {}

    def test_idempotent(self, tmp_path):
        init_grippydoc(tmp_path)
        init_grippydoc(tmp_path)  # Should not raise

        assert (tmp_path / ".grippydoc").exists()


class TestManifest:
    """Tests for Manifest class."""

    def test_to_dict(self):
        entry = ManifestEntry(
            reference="test.py:1-10",
            file_path="test.py",
            ref_type="range",
            start_line=1,
            end_line=10,
            hash="abc123",
            recorded_at="2024-01-01T00:00:00Z",
        )
        manifest = Manifest(version="1", entries={"test.py:1-10": entry})

        data = manifest.to_dict()

        assert data["version"] == "1"
        assert "test.py:1-10" in data["entries"]
        assert data["entries"]["test.py:1-10"]["hash"] == "abc123"

    def test_from_dict(self):
        data = {
            "version": "1",
            "entries": {
                "test.py:1-10": {
                    "reference": "test.py:1-10",
                    "file_path": "test.py",
                    "ref_type": "range",
                    "start_line": 1,
                    "end_line": 10,
                    "hash": "abc123",
                    "recorded_at": "2024-01-01T00:00:00Z",
                }
            },
        }

        manifest = Manifest.from_dict(data)

        assert manifest.version == "1"
        assert "test.py:1-10" in manifest.entries
        assert manifest.entries["test.py:1-10"].hash == "abc123"


class TestRecordReferences:
    """Tests for record_references function."""

    def test_records_references(self, tmp_path):
        init_grippydoc(tmp_path)

        refs = [
            CodeReference(
                reference="test.py:1-10",
                file_path="test.py",
                ref_type="range",
                start_line=1,
                end_line=10,
                content="test content",
                hash="abc123",
            )
        ]

        manifest = record_references(tmp_path, refs)

        assert len(manifest.entries) == 1
        assert "test.py:1-10" in manifest.entries

    def test_persists_to_disk(self, tmp_path):
        init_grippydoc(tmp_path)

        refs = [
            CodeReference(
                reference="test.py",
                file_path="test.py",
                ref_type="file",
                start_line=None,
                end_line=None,
                content="content",
                hash="xyz789",
            )
        ]

        record_references(tmp_path, refs)

        # Load and verify
        loaded = load_manifest(tmp_path)
        assert loaded is not None
        assert "test.py" in loaded.entries


class TestCheckReferences:
    """Tests for check_references function."""

    def test_detects_stale_reference(self, tmp_path):
        # Setup: create file and markdown
        test_file = tmp_path / "test.py"
        test_file.write_text("original content")

        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "doc.md").write_text("[grip:test.py]\n")

        # Initialize and record
        init_grippydoc(tmp_path)
        from grippydoc.resolver import resolve_reference
        ref = resolve_reference("test.py", tmp_path)
        record_references(tmp_path, [ref])

        # Modify the file
        test_file.write_text("modified content")

        # Check
        manifest = load_manifest(tmp_path)
        stale, broken = check_references(tmp_path, manifest)

        assert len(stale) == 1
        assert stale[0].reference == "test.py"
        assert len(broken) == 0

    def test_detects_broken_reference(self, tmp_path):
        # Setup: create markdown pointing to non-existent file
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "doc.md").write_text("[grip:nonexistent.py]\n")

        init_grippydoc(tmp_path)
        manifest = load_manifest(tmp_path)

        stale, broken = check_references(tmp_path, manifest)

        assert len(broken) == 1
        assert broken[0].reference == "nonexistent.py"

    def test_no_issues_when_unchanged(self, tmp_path):
        # Setup
        test_file = tmp_path / "test.py"
        test_file.write_text("content")

        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "doc.md").write_text("[grip:test.py]\n")

        init_grippydoc(tmp_path)
        from grippydoc.resolver import resolve_reference
        ref = resolve_reference("test.py", tmp_path)
        record_references(tmp_path, [ref])

        # Check without modifying
        manifest = load_manifest(tmp_path)
        stale, broken = check_references(tmp_path, manifest)

        assert len(stale) == 0
        assert len(broken) == 0
