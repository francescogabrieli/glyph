# CI, Lockfiles, and Release Gates

Glyph CI should enforce semantics your team has reviewed, not force a
universally fixed percentage.

## Recommended repository flow

```bash
glyph compile AGENTS.md -o AGENTS.glp \
  --strict \
  --min-structured-coverage 80 \
  --min-retained-coverage 100 \
  --max-high-risk-preserved 0

glyph check AGENTS.md AGENTS.glp \
  --min-structured-coverage 80 \
  --min-retained-coverage 100 \
  --max-high-risk-preserved 0 \
  --min-reduction 20 \
  --fail-on-conflicts
```

The first command writes only after strict validation succeeds. The second
checks that the manifest is fresh and that required coverage, retention,
reduction, preservation, and conflict conditions still hold.

## Semantic lockfile

Create a lockfile after reviewing the semantic output:

```bash
glyph lock AGENTS.md CONTRIBUTING.md -o glyph.lock.json
glyph check --lock glyph.lock.json
```

The lock captures source hashes, generated manifest identity, canonical rules,
structured policy fingerprints, preservation fingerprints, and relevant
provenance. It detects instruction changes that would otherwise look like
ordinary Markdown edits.

Regenerate the lock intentionally whenever you accept a semantic change:

```bash
glyph lock AGENTS.md CONTRIBUTING.md -o glyph.lock.json
git diff -- glyph.lock.json
```

## Example GitHub Actions step

```yaml
- name: Validate Glyph semantics
  run: |
    pip install "glyph-instructions @ git+https://github.com/francescogabrieli/glyph.git@v0.2.0"
    glyph compile AGENTS.md -o AGENTS.glp --strict \
      --min-structured-coverage 80 \
      --min-retained-coverage 100 \
      --max-high-risk-preserved 0
    glyph check AGENTS.md AGENTS.glp \
      --min-structured-coverage 80 \
      --min-retained-coverage 100 \
      --max-high-risk-preserved 0 \
      --min-reduction 20 \
      --fail-on-conflicts
    glyph check --lock glyph.lock.json
```

Adapt paths and thresholds to your repository. Do not set a reduction gate on
tiny instruction files without first measuring them; a compact manifest can be
larger than a two-line source document.

## What a failure means

| Failure | Review action |
| --- | --- |
| Low structured coverage | Inspect preserved candidates; add only proven deterministic rules or custom mappings. |
| Retained coverage below 100 | Treat as a compiler defect or review the dropped candidate immediately. |
| High-risk preserved directive | Clarify the source, add an exact custom policy, or keep the check failing until reviewed. |
| Conflict | Resolve contradictory policy categories or source instructions. |
| Lock mismatch | Review the semantic diff and deliberately regenerate the lock if intended. |

See [No silent semantic loss](no-silent-semantic-loss.md) for metric meanings.
