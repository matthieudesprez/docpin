"""Tests for the resolver module."""

import pytest
from pathlib import Path

from grippydoc.resolver import parse_reference, resolve_reference


class TestParseReference:
    """Tests for parse_reference function."""

    def test_whole_file(self):
        file_path, ref_type, start, end = parse_reference("src/auth.py")
        assert file_path == "src/auth.py"
        assert ref_type == "file"
        assert start is None
        assert end is None

    def test_single_line(self):
        file_path, ref_type, start, end = parse_reference("src/auth.py:42")
        assert file_path == "src/auth.py"
        assert ref_type == "line"
        assert start == 42
        assert end == 42

    def test_line_range(self):
        file_path, ref_type, start, end = parse_reference("src/auth.py:10-20")
        assert file_path == "src/auth.py"
        assert ref_type == "range"
        assert start == 10
        assert end == 20

    def test_whitespace_stripped(self):
        file_path, ref_type, start, end = parse_reference("  src/auth.py:10-20  ")
        assert file_path == "src/auth.py"
        assert ref_type == "range"

    def test_invalid_reference(self):
        with pytest.raises(ValueError):
            parse_reference("")


class TestResolveReference:
    """Tests for resolve_reference function."""

    def test_whole_file(self, tmp_path):
        # Create a test file
        test_file = tmp_path / "test.py"
        test_file.write_text("line 1\nline 2\nline 3\n")

        ref = resolve_reference("test.py", tmp_path)

        assert ref is not None
        assert ref.reference == "test.py"
        assert ref.ref_type == "file"
        assert ref.content == "line 1\nline 2\nline 3\n"

    def test_single_line(self, tmp_path):
        test_file = tmp_path / "test.py"
        test_file.write_text("line 1\nline 2\nline 3\n")

        ref = resolve_reference("test.py:2", tmp_path)

        assert ref is not None
        assert ref.ref_type == "line"
        assert ref.start_line == 2
        assert ref.end_line == 2
        assert ref.content == "line 2"

    def test_line_range(self, tmp_path):
        test_file = tmp_path / "test.py"
        test_file.write_text("line 1\nline 2\nline 3\nline 4\n")

        ref = resolve_reference("test.py:2-3", tmp_path)

        assert ref is not None
        assert ref.ref_type == "range"
        assert ref.start_line == 2
        assert ref.end_line == 3
        assert ref.content == "line 2\nline 3"

    def test_file_not_found(self, tmp_path):
        ref = resolve_reference("nonexistent.py", tmp_path)
        assert ref is None

    def test_line_out_of_range(self, tmp_path):
        test_file = tmp_path / "test.py"
        test_file.write_text("line 1\nline 2\n")

        ref = resolve_reference("test.py:100", tmp_path)
        assert ref is None

    def test_nested_path(self, tmp_path):
        nested = tmp_path / "src" / "auth"
        nested.mkdir(parents=True)
        test_file = nested / "login.py"
        test_file.write_text("def login():\n    pass\n")

        ref = resolve_reference("src/auth/login.py:1", tmp_path)

        assert ref is not None
        assert ref.content == "def login():"
