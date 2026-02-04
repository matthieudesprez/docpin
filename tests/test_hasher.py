"""Tests for the hasher module."""

from grippydoc.hasher import compute_hash, normalize_content


class TestNormalizeContent:
    """Tests for normalize_content function."""

    def test_strips_trailing_whitespace_on_lines(self):
        result = normalize_content("foo  \nbar\t\n")
        assert result == "foo\nbar"

    def test_collapses_multiple_blank_lines(self):
        result = normalize_content("a\n\n\nb")
        assert result == "a\n\nb"

    def test_strips_leading_trailing_blank_lines(self):
        result = normalize_content("\n\ncode\n\n")
        assert result == "code"

    def test_preserves_indentation(self):
        result = normalize_content("def foo():\n    pass")
        assert result == "def foo():\n    pass"

    def test_preserves_single_blank_lines(self):
        result = normalize_content("a\n\nb")
        assert result == "a\n\nb"

    def test_empty_string(self):
        result = normalize_content("")
        assert result == ""

    def test_only_whitespace(self):
        result = normalize_content("   \n\n   \n")
        assert result == ""


class TestComputeHash:
    """Tests for compute_hash function."""

    def test_returns_string(self):
        result = compute_hash("test content")
        assert isinstance(result, str)

    def test_consistent_hash(self):
        content = "def hello():\n    print('world')\n"
        hash1 = compute_hash(content)
        hash2 = compute_hash(content)
        assert hash1 == hash2

    def test_different_content_different_hash(self):
        hash1 = compute_hash("content a")
        hash2 = compute_hash("content b")
        assert hash1 != hash2

    def test_strips_whitespace(self):
        hash1 = compute_hash("content")
        hash2 = compute_hash("  content  ")
        hash3 = compute_hash("\ncontent\n")
        assert hash1 == hash2 == hash3

    def test_truncated_to_16_chars(self):
        result = compute_hash("any content")
        assert len(result) == 16

    def test_empty_string(self):
        result = compute_hash("")
        assert isinstance(result, str)
        assert len(result) == 16

    def test_ignores_trailing_whitespace_changes(self):
        hash1 = compute_hash("foo\nbar")
        hash2 = compute_hash("foo  \nbar\t")
        assert hash1 == hash2

    def test_ignores_extra_blank_lines(self):
        hash1 = compute_hash("a\n\nb")
        hash2 = compute_hash("a\n\n\n\nb")
        assert hash1 == hash2

    def test_preserves_indentation_in_hash(self):
        hash1 = compute_hash("def foo():\n    pass")
        hash2 = compute_hash("def foo():\npass")
        assert hash1 != hash2

    def test_preserves_single_blank_line_in_hash(self):
        hash1 = compute_hash("a\n\nb")
        hash2 = compute_hash("a\nb")
        assert hash1 != hash2
