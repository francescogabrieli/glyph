# Release Process

This guide separates technical evidence from the human act of publishing.
Passing a static gate is necessary evidence; it is not an automatic permission
to publish a package.

## Prepare the release

1. Review `CHANGELOG.md`, package version, and user-facing documentation.
2. Confirm generated benchmark and corpus reports are reproducible.
3. Review `git diff` for accidental third-party text, secrets, generated noise,
   or undocumented semantic changes.
4. Ensure no active feature changes are mixed with release-only work.

## Required validation

```bash
pytest
ruff check .
mypy
python -m build
glyph benchmark benchmarks/
bash scripts/release-smoke.sh
git diff --check
```

For a release that claims fixed external-corpus results, run the metadata-only
static sweep against the pinned corpus and compare the generated reports with
the tracked versions. Do not quote stale benchmark numbers.

## Semantic release review

- v0.1 parse/render compatibility remains intact.
- v0.2 policies do not silently downgrade to v0.1.
- Strict mode has not been weakened.
- Retention and safety retention remain at the approved threshold.
- High-risk preservation, dropped candidates, conflicts, and nondeterminism are
  reviewed explicitly.
- Public documentation states what metrics demonstrate and what they do not.

## Publish only after approval

After a maintainer approves the validation evidence, create the commit, tag,
artifact upload, and release notes according to the project's hosting workflow.
These actions are intentionally outside Glyph's compiler and test suite.

## Out of scope evaluation

The behavior matrix is separately governed. Do not run, imply, or publish it as
part of a static-parser release unless the release owner explicitly schedules
that evaluation and accepts its methodology.

The operational command checklist is maintained in
[release-checklist.md](release-checklist.md).
