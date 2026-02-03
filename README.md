# GrippyDoc

Prevent documentation drift by linking Markdown files to specific code.

GrippyDoc tracks code references in your documentation and alerts you when the code changes but the docs haven't been updated. Perfect for CI/CD pipelines to catch stale docs before they reach production.

*Keep your docs gripping the code.*

## Installation

```bash
pip install grippydoc
```

Or install from source:

```bash
git clone https://github.com/grippydoc/grippydoc.git
cd grippydoc
pip install -e .
```

## Quick Start

### 1. Initialize GrippyDoc

```bash
grippydoc init
```

### 2. Reference Code in Your Docs

In your Markdown files, add grip references to code:

```markdown
# Authentication

The login function handles user authentication:

[grip:src/auth.py:10-25]

For the full module, see:

[grip:src/auth.py]
```

### 3. Record the Current State

```bash
grippydoc record
```

### 4. Check for Drift

```bash
grippydoc check
```

If any referenced code has changed since the last `record`, GrippyDoc will:
- List all stale documentation references
- Exit with code 1 (useful for CI/CD)

## Reference Syntax

| Syntax | Description |
|--------|-------------|
| `[grip:path/to/file.py]` | Track entire file |
| `[grip:path/to/file.py:42]` | Track single line |
| `[grip:path/to/file.py:42-58]` | Track line range |

## How It Works

```
┌─────────────────────────────────────────────────────────────────────┐
│                           SETUP PHASE                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   docs/auth.md                        src/auth.py                   │
│  ┌────────────────────────┐         ┌────────────────────────┐      │
│  │ ## Login Flow          │         │ 10: def login(user):   │      │
│  │                        │         │ 11:     validate(user) │      │
│  │ [grip:src/auth.py:10-15] ───────▶│ 12:     token = gen()  │      │
│  │                        │         │ 13:     return token   │      │
│  │ The login function...  │         │ ...                    │      │
│  └────────────────────────┘         └────────────────────────┘      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                          ┌──────────────────┐
                          │ grippydoc record │
                          └────────┬─────────┘
                                   │ hashes lines 10-15
                                   ▼
                     ┌─────────────────────────────┐
                     │  .grippydoc/manifest.json   │
                     │  ┌───────────────────────┐  │
                     │  │ "src/auth.py:10-15":  │  │
                     │  │   "hash": "a1b2c3..." │  │
                     │  └───────────────────────┘  │
                     └─────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                       CHECK PHASE (CI/CD)                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   Developer changes src/auth.py line 12:                            │
│                                                                     │
│   - token = gen()                                                   │
│   + token = generate_secure_token()                                 │
│                                                                     │
│    ┌──────────────────┐     ┌─────────────────────────────────────┐ │
│    │ grippydoc check  │────▶│ ⚠ Stale: docs/auth.md:5            │ │
│    └──────────────────┘     │   [grip:src/auth.py:10-15]         │ │
│              │              │   Exit code: 1                      │ │
│              ▼              └─────────────────────────────────────┘ │
│         CI fails ❌                                                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## CI/CD Integration

**GitHub Actions:**
```yaml
- name: Check documentation freshness
  run: |
    pip install grippydoc
    grippydoc check
```

**GitLab CI:**
```yaml
docs-check:
  script:
    - pip install grippydoc
    - grippydoc check
```

## Commands

| Command | Description |
|---------|-------------|
| `grippydoc init` | Initialize GrippyDoc in the current directory |
| `grippydoc record` | Scan docs and record hashes of referenced code |
| `grippydoc check` | Compare current code against recorded hashes |
| `grippydoc status` | Show status of all tracked references |

## Why GrippyDoc?

- **Zero source code changes** - References live in your docs, not your code
- **Simple syntax** - Just `[grip:file:lines]` in Markdown
- **CI/CD ready** - Exit code 1 on stale docs
- **Lightweight** - No dependencies, pure Python

## License

MIT
