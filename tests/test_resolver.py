"""Tests for the resolver module."""


import pytest

from grippydoc.resolver import parse_reference, resolve_reference, resolve_symbol


class TestParseReference:
    """Tests for parse_reference function."""

    def test_whole_file(self):
        file_path, ref_type, start, end, symbol = parse_reference("src/auth.py")
        assert file_path == "src/auth.py"
        assert ref_type == "file"
        assert start is None
        assert end is None
        assert symbol is None

    def test_single_line(self):
        file_path, ref_type, start, end, symbol = parse_reference("src/auth.py:42")
        assert file_path == "src/auth.py"
        assert ref_type == "line"
        assert start == 42
        assert end == 42
        assert symbol is None

    def test_line_range(self):
        file_path, ref_type, start, end, symbol = parse_reference("src/auth.py:10-20")
        assert file_path == "src/auth.py"
        assert ref_type == "range"
        assert start == 10
        assert end == 20
        assert symbol is None

    def test_symbol_function(self):
        file_path, ref_type, start, end, symbol = parse_reference("src/auth.py#login")
        assert file_path == "src/auth.py"
        assert ref_type == "symbol"
        assert start is None
        assert end is None
        assert symbol == "login"

    def test_symbol_class(self):
        file_path, ref_type, start, end, symbol = parse_reference("src/auth.py#AuthManager")
        assert file_path == "src/auth.py"
        assert ref_type == "symbol"
        assert symbol == "AuthManager"

    def test_symbol_method(self):
        file_path, ref_type, start, end, symbol = parse_reference("src/auth.py#AuthManager.login")
        assert file_path == "src/auth.py"
        assert ref_type == "symbol"
        assert symbol == "AuthManager.login"

    def test_whitespace_stripped(self):
        file_path, ref_type, start, end, symbol = parse_reference("  src/auth.py:10-20  ")
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


class TestResolveSymbol:
    """Tests for resolve_symbol function."""

    def test_function(self):
        code = """def hello():
    print("hello")

def world():
    print("world")
"""
        result = resolve_symbol(code, "hello")
        assert result == (1, 2)

        result = resolve_symbol(code, "world")
        assert result == (4, 5)

    def test_async_function(self):
        code = """async def fetch_data():
    return await get_data()
"""
        result = resolve_symbol(code, "fetch_data")
        assert result == (1, 2)

    def test_class(self):
        code = """class MyClass:
    def __init__(self):
        pass

    def method(self):
        pass
"""
        result = resolve_symbol(code, "MyClass")
        assert result == (1, 6)

    def test_class_method(self):
        code = """class Auth:
    def login(self):
        return True

    def logout(self):
        return False
"""
        result = resolve_symbol(code, "Auth.login")
        assert result == (2, 3)

        result = resolve_symbol(code, "Auth.logout")
        assert result == (5, 6)

    def test_nested_class(self):
        code = """class Outer:
    class Inner:
        def method(self):
            pass
"""
        result = resolve_symbol(code, "Outer.Inner")
        assert result == (2, 4)

        result = resolve_symbol(code, "Outer.Inner.method")
        assert result == (3, 4)

    def test_variable(self):
        code = """MAX_RETRIES = 3
TIMEOUT = 30
"""
        result = resolve_symbol(code, "MAX_RETRIES")
        assert result == (1, 1)

        result = resolve_symbol(code, "TIMEOUT")
        assert result == (2, 2)

    def test_annotated_variable(self):
        code = """MAX_RETRIES: int = 3
"""
        result = resolve_symbol(code, "MAX_RETRIES")
        assert result == (1, 1)

    def test_decorated_function(self):
        code = """@decorator
def decorated():
    pass
"""
        result = resolve_symbol(code, "decorated")
        assert result == (1, 3)

    def test_decorated_class(self):
        code = """@dataclass
class Data:
    value: int
"""
        result = resolve_symbol(code, "Data")
        assert result == (1, 3)

    def test_symbol_not_found(self):
        code = """def existing():
    pass
"""
        result = resolve_symbol(code, "nonexistent")
        assert result is None

    def test_invalid_syntax(self):
        code = """def broken(
"""
        result = resolve_symbol(code, "broken")
        assert result is None


class TestResolveReferenceSymbol:
    """Tests for resolve_reference with symbol references."""

    def test_function_symbol(self, tmp_path):
        test_file = tmp_path / "test.py"
        test_file.write_text("""def hello():
    print("hello")

def world():
    print("world")
""")
        ref = resolve_reference("test.py#hello", tmp_path)

        assert ref is not None
        assert ref.ref_type == "symbol"
        assert ref.start_line == 1
        assert ref.end_line == 2
        assert ref.content == 'def hello():\n    print("hello")'

    def test_class_symbol(self, tmp_path):
        test_file = tmp_path / "test.py"
        test_file.write_text("""class MyClass:
    def method(self):
        pass
""")
        ref = resolve_reference("test.py#MyClass", tmp_path)

        assert ref is not None
        assert ref.ref_type == "symbol"
        assert ref.start_line == 1
        assert ref.end_line == 3
        assert "class MyClass:" in ref.content

    def test_method_symbol(self, tmp_path):
        test_file = tmp_path / "test.py"
        test_file.write_text("""class Auth:
    def login(self):
        return True

    def logout(self):
        return False
""")
        ref = resolve_reference("test.py#Auth.login", tmp_path)

        assert ref is not None
        assert ref.ref_type == "symbol"
        assert ref.start_line == 2
        assert ref.end_line == 3
        assert ref.content == "    def login(self):\n        return True"

    def test_constant_symbol(self, tmp_path):
        test_file = tmp_path / "test.py"
        test_file.write_text("""MAX_RETRIES = 3
TIMEOUT = 30
""")
        ref = resolve_reference("test.py#MAX_RETRIES", tmp_path)

        assert ref is not None
        assert ref.ref_type == "symbol"
        assert ref.content == "MAX_RETRIES = 3"

    def test_symbol_not_found(self, tmp_path):
        test_file = tmp_path / "test.py"
        test_file.write_text("def existing(): pass\n")

        ref = resolve_reference("test.py#nonexistent", tmp_path)
        assert ref is None

    def test_symbol_non_python_file(self, tmp_path):
        test_file = tmp_path / "test.js"
        test_file.write_text("function hello() {}\n")

        ref = resolve_reference("test.js#hello", tmp_path)
        assert ref is None

    def test_decorated_function_symbol(self, tmp_path):
        test_file = tmp_path / "test.py"
        test_file.write_text("""@decorator
@another
def decorated():
    pass
""")
        ref = resolve_reference("test.py#decorated", tmp_path)

        assert ref is not None
        assert ref.start_line == 1
        assert ref.end_line == 4
        assert "@decorator" in ref.content
