# Glyph Corpus Harness

Use this directory to sanity-check Glyph against real instruction files before a release.

Recommended workflow:

```bash
glyph benchmark-real corpus/
glyph benchmark-real corpus/local --write
```

Place manually collected real files under `corpus/local/`. That directory is ignored by Git so maintainers can test against `AGENTS.md`, `CLAUDE.md`, README, CONTRIBUTING, Copilot, and Cursor files without committing third-party content.

Do not add large third-party files to the repository unless their license clearly permits redistribution.
