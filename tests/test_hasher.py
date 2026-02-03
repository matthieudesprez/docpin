"""Tests for the hasher module."""

from grippydoc.hasher import compute_hash


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
