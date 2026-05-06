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
git clone https://github.com/matthieudesprez/grippydoc.git
cd grippydoc
pip install -e .
```

## Quick Start

### 1. Reference Code in Your Docs

In your Markdown files, add grip references to code:

```markdown
# Authentication

The login function handles user authentication:

[grip:src/auth.py:10-25]

For the full module, see:

[grip:src/auth.py]
```

### 2. Record the Current State

```bash
grippydoc record
```

This updates your markdown files in-place with content hashes:

```markdown
[grip:src/auth.py:10-25 @a1b2c3d4e5f6g7h8]
```

### 3. Check for Drift

```bash
grippydoc check
```

If any referenced code has changed since the last `record`, GrippyDoc will:
- List all stale documentation references
- List any unrecorded references (missing hashes)
- Exit with code 1 (useful for CI/CD)

## Reference Syntax

| Syntax | Description |
|--------|-------------|
| `[grip:path/to/file.py]` | Track entire file |
| `[grip:path/to/file.py:42]` | Track single line |
| `[grip:path/to/file.py:42-58]` | Track line range |
| `[grip:path/to/file.py#function_name]` | Track function by name |
| `[grip:path/to/file.py#ClassName]` | Track class by name |
| `[grip:path/to/file.py#ClassName.method]` | Track method by name |
| `[grip:path/to/file.py#CONSTANT]` | Track top-level variable |

After recording, hashes are appended inline: `[grip:path/to/file.py:42-58 @a1b2c3d4]`

### Symbol References (Python only)

Symbol references let you track code by name instead of line numbers. This is more resilient to code changes that shift line numbers:

```markdown
The authentication is handled by the login function:

[grip:src/auth.py#login]

The `Auth` class manages user sessions:

[grip:src/auth.py#Auth]

Specifically, the logout method:

[grip:src/auth.py#Auth.logout]
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
                     ┌──────────────────────────────────┐
                     │  docs/auth.md (updated in-place) │
                     │  [grip:src/auth.py:10-15 @a1b2]  │
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
│    │ grippydoc check  │────▶│ ⚠ Stale: docs/auth.md:5            │ │
│    └──────────────────┘     │   [grip:src/auth.py:10-15]         │ │
│              │              │   Exit code: 1                      │ │
│              ▼              └─────────────────────────────────────┘ │
│         CI fails ❌                                                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Integration

`grippydoc check` is a single command that exits non-zero on stale docs. Wire it in wherever you run other checks.

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

**Makefile:**
```makefile
check-docs:
	grippydoc check docs/
```

Pass a path to scope the check (e.g. `grippydoc check docs/`) if you only want to scan part of the repo.

## Commands

| Command | Description |
|---------|-------------|
| `grippydoc record` | Scan docs and record hashes of referenced code inline |
| `grippydoc check` | Compare current code against recorded hashes |
| `grippydoc status` | Show status of all tracked references |

## Why GrippyDoc?

- **Zero source code changes** - References live in your docs, not your code
- **No extra files** - Hashes are stored inline in your markdown
- **Simple syntax** - Just `[grip:file:lines]` in Markdown
- **CI/CD ready** - Exit code 1 on stale docs
- **Lightweight** - No dependencies, pure Python

## License

MIT
