# docpin Roadmap

Future improvements and features planned for docpin.

## Reference Types

### Currently Supported

- [x] `[pin:file.py]` - Whole file
- [x] `[pin:file.py:42]` - Single line
- [x] `[pin:file.py:42-58]` - Line range

### Planned

- [x] `[pin:file.py#function_name]` - Function by name
- [x] `[pin:file.py#ClassName]` - Class by name
- [x] `[pin:file.py#ClassName.method]` - Method by name
- [x] `[pin:file.py#CONSTANT]` - Top-level variable/constant
- [ ] `[pin:file.py?/regex/]` - Regex pattern match
- [ ] `[pin:src/**/*.py]` - Glob patterns (multiple files)

## Symbol Resolution

To support function/class/method references without modifying source code:

### Python
- Use `ast` module to parse and extract symbols
- Map symbol names to line ranges automatically
- Handle nested classes and functions

### Other Languages
- **JavaScript/TypeScript**: Use tree-sitter or regex heuristics
- **Go**: Parse with regex (function signatures are predictable)
- **Rust**: Parse with regex or tree-sitter
- **Generic fallback**: Regex-based detection for common patterns

## Output & Integration

- [ ] **JSON output** - `docpin check --format json` for tooling
- [ ] **GitHub Actions annotations** - Inline PR comments on stale docs
- [ ] **Watch mode** - `docpin watch` for local development

## Developer Experience

- [ ] **VSCode extension**
  - Syntax highlighting for `[pin:...]`
  - Autocomplete file paths and symbols
  - Jump-to-definition from reference to code
  - Inline status indicators (OK/STALE)

- [ ] **JetBrains plugin**
  - Same features as VSCode extension

## Validation

- [x] **Orphan detection** - Warn when manifest entries are no longer referenced in docs
- [ ] **Unused reference detection** - Find pin references that no doc uses
- [ ] **Overlapping ranges** - Warn when multiple docs reference same code

## Smart Hashing

- [x] **Ignore whitespace-only changes** - Don't flag formatting changes
- [ ] **Ignore comment changes** - Comments inside referenced code
- [ ] **Semantic hashing** - For supported languages, hash the AST not text
- [ ] **Configurable sensitivity** - `strict`, `normal`, `relaxed` modes

## Configuration

```yaml
# .docpin/config.yaml (future)
version: 2
sensitivity: normal
ignore_patterns:
  - "*.test.py"
  - "**/__pycache__/**"
symbol_languages:
  - python
  - javascript
  - typescript
```

## Not Planned

These features are out of scope to keep docpin simple and focused:

- Rich editing UI (use Swimm.io for that)
- Cloud/hosted platform
- Team collaboration features
- Auto-generated documentation
- Documentation hosting

docpin aims to be a **simple, focused CLI tool** for drift detection.

## Contributing

See a feature you'd like? Contributions welcome!

1. Open an issue to discuss the feature
2. Fork the repo
3. Submit a PR

Priority is given to features that:
- Keep the tool simple and focused
- Don't add external dependencies
- Work across multiple languages
