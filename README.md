# GrippyDoc

Prevent documentation drift by linking Markdown files to specific code blocks.

GrippyDoc tracks tagged code blocks in your source files and alerts you when the code changes but the documentation hasn't been updated. Perfect for CI/CD pipelines to catch stale docs before they reach production.

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

This creates a `.grippydoc/` directory with configuration and manifest files.

### 2. Tag Your Code Blocks

Add grip tags around important code sections:

**Python:**
```python
# <grip id="auth-logic">
def authenticate(username, password):
    user = db.find_user(username)
    if user and verify_password(password, user.password_hash):
        return create_session(user)
    return None
# </grip>
```

**JavaScript/TypeScript:**
```javascript
// <grip id="api-endpoint">
app.post('/api/users', async (req, res) => {
    const user = await createUser(req.body);
    res.json(user);
});
// </grip>
```

**SQL:**
```sql
-- <grip id="user-schema">
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
-- </grip>
```

### 3. Link Documentation to Code

In your Markdown files, reference the tagged blocks:

```markdown
# Authentication

This section explains how user authentication works.

[grip:auth-logic]

The `authenticate` function verifies credentials and creates a session.
```

### 4. Record the Current State

```bash
grippydoc record
```

This scans your codebase and saves hashes of all tagged blocks.

### 5. Check for Drift

```bash
grippydoc check
```

If any tagged code has changed since the last `record`, GrippyDoc will:
- List all stale documentation links
- Exit with code 1 (useful for CI/CD)

## CI/CD Integration

Add GrippyDoc to your CI pipeline to catch documentation drift:

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
| `grippydoc record` | Scan and record hashes of all tagged code blocks |
| `grippydoc check` | Compare current code against recorded hashes |
| `grippydoc status` | Show status of all tracked code blocks |

## Supported Languages

GrippyDoc recognizes comment styles for:

- Python, Ruby, Shell (`#`)
- JavaScript, TypeScript, Go, Rust, Java, C/C++ (`//`)
- SQL (`--`)
- HTML (`<!-- -->`)

## Configuration

The `.grippydoc/config.json` file lets you customize:

```json
{
  "version": "1",
  "extensions": [".py", ".js", ".ts", ".go"],
  "exclude_dirs": [".git", "node_modules", "__pycache__"]
}
```

## How It Works

```
┌─────────────────────────────────────────────────────────────────────┐
│                           SETUP PHASE                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   auth.py                            docs/auth.md                   │
│  ┌────────────────────────┐         ┌────────────────────────┐      │
│  │ # <grip id="login">    │         │ ## Login Flow          │      │
│  │ def login(user, pw):   │         │                        │      │
│  │     validate(user)     │────────▶│ [grip:login]           │      │
│  │     return token       │ linked  │                        │      │
│  │ # </grip>              │         │ Users call login()...  │      │
│  └────────────────────────┘         └────────────────────────┘      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                          ┌──────────────────┐
                          │ grippydoc record │
                          └────────┬─────────┘
                                   │ saves hashes
                                   ▼
                     ┌─────────────────────────────┐
                     │  .grippydoc/manifest.json   │
                     │  ┌───────────────────────┐  │
                     │  │ "login": {            │  │
                     │  │   "hash": "a1b2c3...",│  │
                     │  │   "file": "auth.py"   │  │
                     │  │ }                     │  │
                     │  └───────────────────────┘  │
                     └─────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                       CHECK PHASE (CI/CD)                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   Developer changes code:                                           │
│  ┌────────────────────────┐                                         │
│  │ # <grip id="login">    │                                         │
│  │ def login(user, pw):   │                                         │
│  │     validate(user)     │                                         │
│  │     log_attempt()      │ ◀── NEW LINE                            │
│  │     return token       │                                         │
│  │ # </grip>              │                                         │
│  └────────────────────────┘                                         │
│              │                                                      │
│              ▼                                                      │
│    ┌──────────────────┐     ┌─────────────────────────────────────┐ │
│    │ grippydoc check  │────▶│ ⚠ Stale doc: docs/auth.md:5        │ │
│    └──────────────────┘     │   Block [login] changed in auth.py │ │
│              │              │   Exit code: 1                      │ │
│              ▼              └─────────────────────────────────────┘ │
│         CI fails ❌                                                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**In short:**

1. **Tag** code blocks with `<grip id="...">` in comments
2. **Link** from Markdown with `[grip:id]`
3. **Record** hashes with `grippydoc record`
4. **Check** for drift with `grippydoc check` (exits 1 if stale)

## License

MIT
