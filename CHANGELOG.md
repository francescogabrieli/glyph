# Changelog

All notable user-facing changes are documented here. Glyph follows semantic
versioning once it reaches a stable public API; before 1.0, minor versions may
include intentional format and API evolution.

## Unreleased

No unreleased changes.

## 0.2.0 - 2026-07-19

- **Breaking:** Remove the legacy flat `glyph.<module>` import paths. Import
  from the owning package instead, such as `glyph.pipeline.compiler` or
  `glyph.formats.parser`.
- Add the explicit `glyph/0.2` format and a small structured policy expression
  model with atomic, all, any, and not expressions; governed subjects,
  predicates, objects, scopes, structured conditions and exceptions, and
  inseparable policy links remain distinct.
- Preserve byte-stable `glyph/0.1` parsing and rendering, lossless internal
  upgrade, deterministic content-derived IDs, and guarded 0.2-to-0.1
  downgrade.
- Add conservative deterministic clause extraction and exact repository-local
  custom policies while retaining ambiguous directives source-faithfully.
- Correct operational retention denominators so resolved non-operational
  generic-document blockquotes do not inflate the candidate population.
- Reorganize the implementation into focused core, format, governance,
  interface, pipeline, semantic, and source packages.
- Document the `.glp 0.2` structured policy architecture and conservative
  extraction boundary.
- Add comprehensive adoption, CLI, configuration, CI, security, development,
  testing, release, and troubleshooting documentation.
- Add isolated wheel smoke validation so stale local artifacts cannot affect
  release evidence.

## 0.1.0

Initial development release line of the deterministic Instructions-as-Code toolchain:
Markdown compilation, canonical semantic rules, benchmark and verification
metrics, compatibility emitters, semantic diff, lockfiles, task selection,
linting, scoring, and optional local MCP support.
