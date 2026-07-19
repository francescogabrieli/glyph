# v0.2.0 Release Checklist

This checklist prepares the first public alpha without conflating a green
static gate with package publication.

## Automated validation

Run from a clean checkout with the development dependencies installed:

```bash
pip install -e ".[dev,mcp]"
pytest
ruff check .
mypy
python -m build
glyph version
glyph doctor
glyph compile benchmarks/backend-fastapi/AGENTS.md -o /tmp/backend.glp --strict --min-structured-coverage 80 --min-retained-coverage 100 --max-high-risk-preserved 0
glyph check benchmarks/backend-fastapi/AGENTS.md /tmp/backend.glp --min-structured-coverage 80 --min-retained-coverage 100 --max-high-risk-preserved 0 --min-reduction 20
glyph inspect benchmarks/readme-dev-section/README.md --show-unmapped
glyph select /tmp/backend.glp --task "fix failing tests" --format markdown
glyph benchmark benchmarks/
glyph benchmark-real . --patterns "AGENTS.md,README.md,CONTRIBUTING.md,CLAUDE.md,.github/copilot-instructions.md,.cursor/rules/*.mdc"
glyph mcp --help
bash scripts/release-smoke.sh
git diff --check
```

The smoke script builds into a disposable artifact directory and installs that
wheel into a fresh virtual environment. Existing files in `dist/` cannot affect
the result.

## Evidence review

- Confirm all supported Python versions pass in GitHub Actions.
- Confirm Ruff, mypy, package build, fresh-wheel smoke, and optional MCP help
  pass in CI.
- Review the generated manifest and inspect output for visible preservation.
- Confirm the benchmark report is generated from its committed synthetic
  fixtures rather than hard-coded.
- Reproduce the pinned, metadata-only fixed corpus only when release claims
  depend on it; do not commit source directives or checkout identities.
- Confirm retained coverage and safety retention are 100%, with zero dropped
  candidates, zero high-risk preserved directives, and zero nondeterminism.
- Confirm `glyph/0.1` compatibility, `glyph/0.2` round trips, downgrade guards,
  semantic diff, selection, locks, and Markdown emitters remain covered.
- Review `CHANGELOG.md`, the release notes, package metadata, and the complete
  diff for secrets, third-party text, generated noise, and stale claims.

## Hosting preparation

- The repository is public and `main` contains the reviewed release commit.
- Package-registry setup is intentionally deferred until a maintainer creates
  and secures the required publishing account.

## Release boundary

- Merging does not tag or publish the package.
- Do not create the `v0.2.0` tag or GitHub Release until the maintainer performs
  the final artifact review and explicitly authorizes publication.
- Do not add registry credentials or a publish workflow until the package
  registry and authentication method have been reviewed separately.
- Do not include a VS Code plugin, hosted web service, LLM classifier, remote
  dependency, or binary `.glp` format in v0.2.0.
- Do not claim native Codex or Claude runtime integration or universal corpus
  performance.
- Do not run or imply the separately governed behavior matrix unless the
  release owner explicitly schedules it.
