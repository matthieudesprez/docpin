# docpin

Pin your Markdown to specific code. docpin fails CI when the referenced code changes but the docs don't.

## Install

```bash
pip install docpin
```

## Usage

Add `[pin:...]` references to your Markdown:

```markdown
The login function handles authentication:

[pin:src/auth.py:10-25]
```

Run `docpin record`. docpin writes a content hash back into the Markdown, in place:

```markdown
[pin:src/auth.py:10-25 @a1b2c3d4e5f6g7h8]
```

In CI, run `docpin check`. It exits 1 if any referenced code has changed since the last record, listing the stale and unrecorded references.

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
│  │ [pin:src/auth.py:10-15]├────────▶│ 12:     token = gen()  │      │
│  │                        │         │ 13:     return token   │      │
│  │ The login function...  │         │ ...                    │      │
│  └────────────────────────┘         └────────────────────────┘      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                          ┌──────────────────┐
                          │  docpin record   │
                          └────────┬─────────┘
                                   │ hashes lines 10-15
                                   ▼
                     ┌──────────────────────────────────┐
                     │  docs/auth.md (updated in-place) │
                     │  [pin:src/auth.py:10-15 @a1b2]   │
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
│    │   docpin check   ├────▶│ ⚠ Stale: docs/auth.md:5             │ │
│    └──────────────────┘     │   [pin:src/auth.py:10-15]           │ │
│              │              │   Exit code: 1                      │ │
│              ▼              └─────────────────────────────────────┘ │
│         CI fails ❌                                                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## CI

```yaml
- run: pip install docpin && docpin check
```

Pass a path to scope the check: `docpin check docs/`.

## Commands

| Command | Description |
|---------|-------------|
| `docpin record` | Scan docs and write content hashes inline |
| `docpin check`  | Compare current code against recorded hashes; exit 1 on drift |
| `docpin status` | Show status of all tracked references |

## License

MIT
