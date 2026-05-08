# docpin vs Swimm.io

A comparison of docpin with [Swimm.io](https://swimm.io), a popular documentation platform, and what would be needed to fully replace it.

## Feature Comparison

| Feature | docpin | Swimm.io |
|---------|:---------:|:--------:|
| Detect code/doc drift | Yes | Yes |
| CI/CD integration | Yes | Yes |
| Free & open source | Yes | No (freemium) |
| Self-hosted | Yes | No (cloud) |
| Zero dependencies | Yes | No |
| Rich editor | No | Yes |
| IDE plugins (VSCode, JetBrains) | No | Yes |
| Shows *what* changed in code | No | Yes |
| Auto-suggests doc updates | No | Yes |
| Doc search & discovery | No | Yes |
| Team collaboration | No | Yes |
| Tutorials / walkthroughs | No | Yes |
| Auto-generated docs | No | Yes |
| Git-based storage | Yes | Yes |
| Works offline | Yes | Partial |

## When to Use docpin

docpin is a good fit if you:

- Want a **simple, lightweight** solution
- Only need **drift detection** (not a full doc platform)
- Prefer **self-hosted** and **open source** tools
- Want **zero dependencies** and easy CI integration
- Are comfortable writing docs in plain Markdown

## When to Use Swimm

Swimm is a better fit if you:

- Need a **rich editing experience** with IDE integration
- Want **auto-generated documentation** from code
- Need **team collaboration** features
- Want to see **exactly what changed** in code (not just that it changed)
- Need **tutorials and walkthroughs** with step-by-step code references
- Prefer a managed **cloud platform**

## What's Missing to Replace Swimm

To fully replace Swimm.io, docpin would need:

### High Priority

1. **Link Validation**
   - Verify all `[pin:id]` references point to existing blocks
   - Catch orphaned links (block was deleted)
   - Catch typos in pin IDs

2. **Watch Mode**
   - `docpin watch` for local development
   - Live feedback as you edit code

### Medium Priority

3. **IDE Extensions**
   - VSCode extension to insert pin tags easily
   - Highlight pin tags and links
   - Jump-to-definition from `[pin:id]` to code block

4. **Smarter Hashing**
   - Ignore whitespace-only changes
   - Ignore comment changes within blocks
   - Configurable sensitivity levels

5. **Better Output Formats**
   - JSON output for tooling integration
   - GitHub Actions annotations
   - PR comments via GitHub API

### Lower Priority

6. **Doc Generation**
   - Auto-generate stub documentation for unlinked blocks
   - List all pin blocks with their locations

7. **Multi-repo Support**
   - Track blocks across multiple repositories
   - Monorepo support with scoped manifests

8. **Web UI**
   - Simple dashboard showing doc health
   - Browse all pin links and their status

## Roadmap

docpin aims to stay **simple and focused**. The goal is not to replicate all of Swimm's features, but to provide a solid open-source foundation for documentation drift detection.

Planned additions:
- [ ] Link validation (orphan detection)
- [ ] JSON output format
- [ ] VSCode extension
- [ ] Watch mode

Not planned (use Swimm if you need these):
- Rich editing UI
- Cloud platform
- Team collaboration
- Auto-generated documentation
