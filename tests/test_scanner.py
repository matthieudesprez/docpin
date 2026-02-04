"""Tests for the scanner module."""


from grippydoc.scanner import parse_markdown, scan_markdown_files


class TestParseMarkdown:
    """Tests for parse_markdown function."""

    def test_finds_grip_reference(self, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text("# Header\n\n[grip:src/auth.py:10-20]\n")

        refs = parse_markdown(md_file)

        assert len(refs) == 1
        assert refs[0].reference == "src/auth.py:10-20"
        assert refs[0].line_number == 3

    def test_multiple_references(self, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text("""# Header

[grip:src/auth.py]

Some text.

[grip:src/utils.py:1-10]
""")

        refs = parse_markdown(md_file)

        assert len(refs) == 2
        assert refs[0].reference == "src/auth.py"
        assert refs[1].reference == "src/utils.py:1-10"

    def test_skips_fenced_code_blocks(self, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text("""# Header

[grip:real/reference.py]

```markdown
[grip:example/in/code/block.py]
```

[grip:another/real.py]
""")

        refs = parse_markdown(md_file)

        assert len(refs) == 2
        assert refs[0].reference == "real/reference.py"
        assert refs[1].reference == "another/real.py"

    def test_skips_tilde_fenced_code_blocks(self, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text("""# Header

[grip:real/reference.py]

~~~markdown
[grip:example/in/code/block.py]
~~~

[grip:another/real.py]
""")

        refs = parse_markdown(md_file)

        assert len(refs) == 2
        assert refs[0].reference == "real/reference.py"
        assert refs[1].reference == "another/real.py"

    def test_skips_inline_code(self, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text("""# Header

Use `[grip:example.py]` syntax to reference code.

[grip:real/reference.py]
""")

        refs = parse_markdown(md_file)

        assert len(refs) == 1
        assert refs[0].reference == "real/reference.py"

    def test_multiple_on_same_line(self, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text("See [grip:a.py] and [grip:b.py] for details.\n")

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
        md_file.write_text("# Just a normal markdown file\n\nNo grip references here.\n")

        refs = parse_markdown(md_file)

        assert len(refs) == 0


class TestScanMarkdownFiles:
    """Tests for scan_markdown_files function."""

    def test_scans_directory(self, tmp_path):
        # Create markdown files
        (tmp_path / "doc1.md").write_text("[grip:file1.py]\n")
        (tmp_path / "doc2.md").write_text("[grip:file2.py]\n")

        refs = scan_markdown_files(tmp_path)

        assert len(refs) == 2
        references = {r.reference for r in refs}
        assert references == {"file1.py", "file2.py"}

    def test_scans_nested_directories(self, tmp_path):
        docs = tmp_path / "docs" / "api"
        docs.mkdir(parents=True)
        (docs / "auth.md").write_text("[grip:src/auth.py]\n")

        refs = scan_markdown_files(tmp_path)

        assert len(refs) == 1
        assert refs[0].reference == "src/auth.py"

    def test_excludes_directories(self, tmp_path):
        # Create files in excluded directory
        node_modules = tmp_path / "node_modules"
        node_modules.mkdir()
        (node_modules / "doc.md").write_text("[grip:should/be/ignored.py]\n")

        # Create file in included directory
        (tmp_path / "doc.md").write_text("[grip:included.py]\n")

        refs = scan_markdown_files(tmp_path)

        assert len(refs) == 1
        assert refs[0].reference == "included.py"

    def test_excludes_venv_directories(self, tmp_path):
        # Create files in .venv directory
        venv = tmp_path / ".venv" / "lib"
        venv.mkdir(parents=True)
        (venv / "README.md").write_text("[grip:should/be/ignored.py]\n")

        # Create file in included directory
        (tmp_path / "doc.md").write_text("[grip:included.py]\n")

        refs = scan_markdown_files(tmp_path)

        assert len(refs) == 1
        assert refs[0].reference == "included.py"

    def test_only_scans_md_files(self, tmp_path):
        (tmp_path / "doc.md").write_text("[grip:found.py]\n")
        (tmp_path / "doc.txt").write_text("[grip:ignored.py]\n")

        refs = scan_markdown_files(tmp_path)

        assert len(refs) == 1
        assert refs[0].reference == "found.py"
