# Configuration

Glyph discovers `.glyph/config.toml` from the working directory upward. The
file supplies project defaults; explicit command-line options take precedence.

Create a starter configuration with:

```bash
glyph init --from AGENTS.md
```

## Reference configuration

```toml
version = "0.1"
default_profile = "compact"
min_semantic_coverage = 95
min_operational_coverage = 80
min_reduction = 20
max_unmapped = 10

[paths]
source = "AGENTS.md"
manifest = "AGENTS.glp"
rules = "glyph.rules.yml"
lock = "glyph.lock.json"
```

`source` and `manifest` make `glyph compile` usable without positional inputs
or `-o`. The configured `rules` file applies to commands that accept
`--rules`. `lock` is a project convention for your automation; lock commands
still take their explicit output path.

## Profiles

| Profile | Intended use |
| --- | --- |
| `readable` | Reviewable manifests with more vertical structure. |
| `compact` | Default balance of readability and token reduction. |
| `ultra` | Minimal UTF-8 representation when token cost is the priority. |

Profile changes affect rendering, not the semantic manifest. Parse and render
remain deterministic for a given version and profile.

## Thresholds are policy, not magic numbers

Use strict thresholds only after inspecting a representative set of your files.

- `min_operational_coverage` is the configuration alias for structured
  coverage.
- `min_reduction` belongs in CI checks where a reduction target is appropriate.
- `max_unmapped` limits genuinely dropped candidates; it does not hide
  preserved directives.

High-risk preservation is deliberately set on the command line or CI command,
where reviewers can see it directly:

```bash
glyph compile AGENTS.md -o AGENTS.glp \
  --strict --min-retained-coverage 100 --max-high-risk-preserved 0
```

See [CI and lockfiles](ci-cd.md) and [No silent semantic loss](no-silent-semantic-loss.md).
