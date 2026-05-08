# docpin

Prevent documentation drift by linking Markdown files to specific code.

docpin tracks code references in your documentation and alerts you when the code changes but the docs haven't been updated. Perfect for CI/CD pipelines to catch stale docs before they reach production.

*Pin your docs to your code.*

## Installation

```bash
pip install docpin
```

Or install from source:

```bash
git clone https://github.com/matthieudesprez/docpin.git
cd docpin
pip install -e .
```

## Quick Start

### 1. Reference Code in Your Docs

In your Markdown files, add pin references to code:

```markdown
# Authentication

The login function handles user authentication:

[pin:src/auth.py:10-25]

For the full module, see:

[pin:src/auth.py]
```

### 2. Record the Current State

```bash
docpin record
```

This updates your markdown files in-place with content hashes:

```markdown
[pin:src/auth.py:10-25 @a1b2c3d4e5f6g7h8]
```

### 3. Check for Drift

```bash
docpin check
```

If any referenced code has changed since the last `record`, docpin will:
- List all stale documentation references
- List any unrecorded references (missing hashes)
- Exit with code 1 (useful for CI/CD)

## Reference Syntax

| Syntax | Description |
|--------|-------------|
| `[pin:path/to/file.py]` | Track entire file |
| `[pin:path/to/file.py:42]` | Track single line |
| `[pin:path/to/file.py:42-58]` | Track line range |
| `[pin:path/to/file.py#function_name]` | Track function by name |
| `[pin:path/to/file.py#ClassName]` | Track class by name |
| `[pin:path/to/file.py#ClassName.method]` | Track method by name |
| `[pin:path/to/file.py#CONSTANT]` | Track top-level variable |

After recording, hashes are appended inline: `[pin:path/to/file.py:42-58 @a1b2c3d4]`

### Symbol References (Python only)

Symbol references let you track code by name instead of line numbers. This is more resilient to code changes that shift line numbers:

```markdown
The authentication is handled by the login function:

[pin:src/auth.py#login]

The `Auth` class manages user sessions:

[pin:src/auth.py#Auth]

Specifically, the logout method:

[pin:src/auth.py#Auth.logout]
```

Symbol references support:
- Functions (sync and async)
- Classes
- Methods (including nested classes)
- Top-level variables and constants
- Decorated functions and classes (includes decorator lines)

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
│  │ [pin:src/auth.py:10-15] ───────▶│ 12:     token = gen()  │      │
│  │                        │         │ 13:     return token   │      │
│  │ The login function...  │         │ ...                    │      │
│  └────────────────────────┘         └────────────────────────┘      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                          ┌──────────────────┐
                          │ docpin record │
                          └────────┬─────────┘
                                   │ hashes lines 10-15
                                   ▼
                     ┌──────────────────────────────────┐
                     │  docs/auth.md (updated in-place) │
                     │  [pin:src/auth.py:10-15 @a1b2]  │
                     └──────────────────────────────────┘

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
│    │ docpin check  │────▶│ ⚠ Stale: docs/auth.md:5            │ │
│    └──────────────────┘     │   [pin:src/auth.py:10-15]         │ │
│              │              │   Exit code: 1                      │ │
│              ▼              └─────────────────────────────────────┘ │
│         CI fails ❌                                                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Integration

`docpin check` is a single command that exits non-zero on stale docs. Wire it in wherever you run other checks.

**GitHub Actions:**
```yaml
- name: Check documentation freshness
  run: |
    pip install docpin
    docpin check
```

**GitLab CI:**
```yaml
docs-check:
  script:
    - pip install docpin
    - docpin check
```

**Makefile:**
```makefile
check-docs:
	docpin check docs/
```

Pass a path to scope the check (e.g. `docpin check docs/`) if you only want to scan part of the repo.

## Commands

| Command | Description |
|---------|-------------|
| `docpin record` | Scan docs and record hashes of referenced code inline |
| `docpin check` | Compare current code against recorded hashes |
| `docpin status` | Show status of all tracked references |

## Why docpin?

- **Zero source code changes** - References live in your docs, not your code
- **No extra files** - Hashes are stored inline in your markdown
- **Simple syntax** - Just `[pin:file:lines]` in Markdown
- **CI/CD ready** - Exit code 1 on stale docs
- **Lightweight** - No dependencies, pure Python

## License

MIT
