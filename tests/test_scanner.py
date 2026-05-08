"""Tests for the scanner module."""


from docpin.scanner import parse_markdown, scan_markdown_files, update_markdown_hashes


class TestParseMarkdown:
    """Tests for parse_markdown function."""

    def test_finds_pin_reference(self, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text("# Header\n\n[pin:src/auth.py:10-20]\n")

        refs = parse_markdown(md_file)

        assert len(refs) == 1
        assert refs[0].reference == "src/auth.py:10-20"
        assert refs[0].line_number == 3

    def test_multiple_references(self, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text("""# Header

[pin:src/auth.py]

Some text.

[pin:src/utils.py:1-10]
""")

        refs = parse_markdown(md_file)

        assert len(refs) == 2
        assert refs[0].reference == "src/auth.py"
        assert refs[1].reference == "src/utils.py:1-10"

    def test_skips_fenced_code_blocks(self, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text("""# Header

[pin:real/reference.py]

```markdown
[pin:example/in/code/block.py]
```

[pin:another/real.py]
""")

        refs = parse_markdown(md_file)

        assert len(refs) == 2
        assert refs[0].reference == "real/reference.py"
        assert refs[1].reference == "another/real.py"

    def test_skips_tilde_fenced_code_blocks(self, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text("""# Header

[pin:real/reference.py]

~~~markdown
[pin:example/in/code/block.py]
~~~

[pin:another/real.py]
""")

        refs = parse_markdown(md_file)

        assert len(refs) == 2
        assert refs[0].reference == "real/reference.py"
        assert refs[1].reference == "another/real.py"

    def test_skips_inline_code(self, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text("""# Header

Use `[pin:example.py]` syntax to reference code.

[pin:real/reference.py]
""")

        refs = parse_markdown(md_file)

        assert len(refs) == 1
        assert refs[0].reference == "real/reference.py"

    def test_multiple_on_same_line(self, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text("See [pin:a.py] and [pin:b.py] for details.\n")

        refs = parse_markdown(md_file)

        assert len(refs) == 2
        assert refs[0].reference == "a.py"
        assert refs[1].reference == "b.py"

    def test_empty_file(self, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text("")

        refs = parse_markdown(md_file)

        assert len(refs) == 0

    def test_no_references(self, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text("# Just a normal markdown file\n\nNo pin references here.\n")

        refs = parse_markdown(md_file)

        assert len(refs) == 0

    def test_parses_inline_hash(self, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text("[pin:src/auth.py:10-20 @a1b2c3d4]\n")

        refs = parse_markdown(md_file)

        assert len(refs) == 1
        assert refs[0].reference == "src/auth.py:10-20"
        assert refs[0].recorded_hash == "a1b2c3d4"

    def test_reference_without_hash_has_none(self, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text("[pin:src/auth.py]\n")

        refs = parse_markdown(md_file)

        assert len(refs) == 1
        assert refs[0].reference == "src/auth.py"
        assert refs[0].recorded_hash is None


class TestUpdateMarkdownHashes:
    """Tests for update_markdown_hashes function."""

    def test_update_adds_hash(self, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text("[pin:src/auth.py]\n")

        count = update_markdown_hashes(md_file, {"src/auth.py": "abc123"})

        assert count == 1
        assert md_file.read_text() == "[pin:src/auth.py @abc123]\n"

    def test_update_replaces_existing_hash(self, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text("[pin:src/auth.py @oldhash]\n")

        count = update_markdown_hashes(md_file, {"src/auth.py": "newhash"})

        assert count == 1
        assert md_file.read_text() == "[pin:src/auth.py @newhash]\n"

    def test_update_skips_code_blocks(self, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text("```\n[pin:src/auth.py]\n```\n")

        count = update_markdown_hashes(md_file, {"src/auth.py": "abc123"})

        assert count == 0
        assert md_file.read_text() == "```\n[pin:src/auth.py]\n```\n"

    def test_update_skips_inline_code(self, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text("Use `[pin:src/auth.py]` syntax.\n")

        count = update_markdown_hashes(md_file, {"src/auth.py": "abc123"})

        assert count == 0
        assert md_file.read_text() == "Use `[pin:src/auth.py]` syntax.\n"

    def test_update_multiple_refs_same_line(self, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text("See [pin:a.py] and [pin:b.py] here.\n")

        count = update_markdown_hashes(md_file, {"a.py": "hash_a", "b.py": "hash_b"})

        assert count == 2
        content = md_file.read_text()
        assert "[pin:a.py @hash_a]" in content
        assert "[pin:b.py @hash_b]" in content

    def test_update_preserves_surrounding_text(self, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text("# Header\n\nSome text before.\n\n[pin:src/auth.py]\n\nSome text after.\n")

        count = update_markdown_hashes(md_file, {"src/auth.py": "abc123"})

        assert count == 1
        content = md_file.read_text()
        assert content == "# Header\n\nSome text before.\n\n[pin:src/auth.py @abc123]\n\nSome text after.\n"

    def test_update_only_updates_known_refs(self, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text("[pin:known.py]\n[pin:unknown.py]\n")

        count = update_markdown_hashes(md_file, {"known.py": "abc123"})

        assert count == 1
        content = md_file.read_text()
        assert "[pin:known.py @abc123]" in content
        assert "[pin:unknown.py]" in content


class TestScanMarkdownFiles:
    """Tests for scan_markdown_files function."""

    def test_scans_directory(self, tmp_path):
        # Create markdown files
        (tmp_path / "doc1.md").write_text("[pin:file1.py]\n")
        (tmp_path / "doc2.md").write_text("[pin:file2.py]\n")

        refs = scan_markdown_files(tmp_path)

        assert len(refs) == 2
        references = {r.reference for r in refs}
        assert references == {"file1.py", "file2.py"}

    def test_scans_nested_directories(self, tmp_path):
        docs = tmp_path / "docs" / "api"
        docs.mkdir(parents=True)
        (docs / "auth.md").write_text("[pin:src/auth.py]\n")

        refs = scan_markdown_files(tmp_path)

        assert len(refs) == 1
        assert refs[0].reference == "src/auth.py"

    def test_excludes_directories(self, tmp_path):
        # Create files in excluded directory
        node_modules = tmp_path / "node_modules"
        node_modules.mkdir()
        (node_modules / "doc.md").write_text("[pin:should/be/ignored.py]\n")

        # Create file in included directory
        (tmp_path / "doc.md").write_text("[pin:included.py]\n")

        refs = scan_markdown_files(tmp_path)

        assert len(refs) == 1
        assert refs[0].reference == "included.py"

    def test_excludes_venv_directories(self, tmp_path):
        # Create files in .venv directory
        venv = tmp_path / ".venv" / "lib"
        venv.mkdir(parents=True)
        (venv / "README.md").write_text("[pin:should/be/ignored.py]\n")

        # Create file in included directory
        (tmp_path / "doc.md").write_text("[pin:included.py]\n")

        refs = scan_markdown_files(tmp_path)

        assert len(refs) == 1
        assert refs[0].reference == "included.py"

    def test_only_scans_md_files(self, tmp_path):
        (tmp_path / "doc.md").write_text("[pin:found.py]\n")
        (tmp_path / "doc.txt").write_text("[pin:ignored.py]\n")

        refs = scan_markdown_files(tmp_path)

        assert len(refs) == 1
        assert refs[0].reference == "found.py"
