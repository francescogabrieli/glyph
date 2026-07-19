# Working on Glyph

Glyph is a production-quality, open-source Instructions-as-Code toolchain for
coding-agent instruction files. It compiles verbose Markdown guidance into
compact, versioned `.glp` semantic manifests while preserving measurable
operational semantics.

This file is the operating contract for contributors and coding agents working
in this repository. Product and user documentation lives in [docs/README.md](docs/README.md).

## Product contract

Glyph must make instruction files:

- smaller and measurable;
- lintable, diffable, benchmarkable, and enforceable in CI;
- portable through Markdown compatibility emitters;
- deterministic and auditable;
- safe to evolve without silent semantic loss.

Glyph preserves measurable operational semantics. It does not preserve arbitrary
prose, guarantee identical LLM behavior, or promise a fixed token reduction.

Never weaken these product boundaries:

- no LLM calls, remote API calls, or network dependencies in the library,
  compiler, or benchmarks;
- no silent candidate drops or lossy v0.2-to-v0.1 downgrade;
- no corpus-specific phrases, repository identities, or third-party source
  text in committed code, fixtures, reports, or tests;
- no lowering a gate merely to make a result green;
- no conversion of ambiguous relations into opaque target strings.

## Documentation map

Read the relevant document before changing the associated behavior.

| Area | Documentation |
| --- | --- |
| Product onboarding and public claims | [README](README.md), [docs hub](docs/README.md), [FAQ](docs/faq.md) |
| Format and compatibility | [`.glp` spec](docs/glp-spec.md), [v0.1 spec](spec/glp-0.1.md), [compatibility](docs/compatibility.md) |
| 0.2 policy semantics | [policy architecture](docs/glp-0.2-policy-architecture.md) |
| Extraction and retention | [extraction engine](docs/semantic-extraction-engine.md), [no silent loss](docs/no-silent-semantic-loss.md) |
| CLI, config, rules, CI | [CLI reference](docs/cli-reference.md), [configuration](docs/configuration.md), [custom rules](docs/custom-rules.md), [CI guide](docs/ci-cd.md) |
| Architecture and security | [architecture](docs/architecture.md), [security model](docs/security-model.md) |
| Development and validation | [development](docs/development.md), [testing](docs/testing.md), [release process](docs/release-process.md) |
| Corpus and benchmark evidence | [benchmark methodology](docs/benchmark-methodology.md), [corpus harness](corpus/README.md), [static-gate report](docs/release-candidate-v0.2-static-gate-report.md) |

Update the closest document whenever code changes behavior, semantics, metrics,
public commands, release conditions, or a user-facing boundary.

## Repository map

```text
src/glyph/       compiler, parser, renderers, CLI, and local service surfaces
tests/           synthetic, conformance, regression, and integration tests
benchmarks/      license-safe fixtures and generated benchmark reports
corpus/          pinned metadata-only external-corpus manifest and reports
spec/            versioned format specification and conformance fixtures
docs/            product, engineering, security, and release documentation
evals/           separately governed evaluation harnesses
scripts/         repeatable release smoke validation
```

Keep modules focused. The main boundaries are documented in
[architecture.md](docs/architecture.md).

## Implementation workflow

Before a non-trivial change:

1. Read the relevant code and documentation.
2. Write a short plan stating scope, invariant, and validation.
3. Preserve unrelated work already in the worktree.
4. Make the smallest deterministic implementation change.
5. Add synthetic positive, negative, and ambiguity tests where parsing or
   classification changes.
6. Update documentation and generated evidence only through its normal tool.
7. Run validation proportional to risk; do not declare success from a single
   unit test when downstream consumers change.

Use `apply_patch` for source and documentation edits. Do not use destructive
Git commands unless explicitly requested.

## Semantic model requirements

Support canonical semantic units for common coding-agent behavior, including:

```text
read_before_edit
plan_before_edit
minimal_change
run_tests_before_done
simple_explicit_code
small_reviewable_changes
explain_unrun_tests
report_changes
report_verification
secrets_commit
prod_config_write
destructive_ops
credentials_exposure
api_key_exposure
unsafe_migrations
schema_changes
deploy_without_approval
security_sensitive_changes
lint_before_done
typecheck_before_done
follow_existing_style
no_large_refactors
no_unrequested_features
```

Use `must`, `deny`, `ask`, and, in 0.2 structured policies, `allow` correctly.
Keep governed subject distinct from repository/code-area scope. Keep predicate
distinct from objects. Preserve action, state, and passive relation kinds.

The supported 0.2 expression language is deliberately small:

```text
atomic | all(...) | any(...) | not(...)
```

Conditions and exceptions must be structured and attached to the policy or a
content-derived expression node. Inseparable mixed-modality policies use an
explicit link and must remain atomic for selection, lockfiles, diff, verification,
and Markdown emission. Do not add sequence, implication, arbitrary NLP, or new
fields without a sanitised blocker shape and tests proving they are required.

When deterministic extraction does not have one valid interpretation, keep a
`PreservedDirective`. Exact custom policy rules are the repository-specific
mechanism; ordinary parser logic must remain general.

## Format and compatibility

The `.glp` format is plain UTF-8 and versioned. It supports `glyph/0.1` and
`glyph/0.2` headers, with short `g/` aliases where specified.

- Parse and render 0.1 exactly and deterministically.
- Upgrade 0.1 policies losslessly into the internal 0.2 semantic view.
- Reject 0.2-to-0.1 rendering when it would lose semantics.
- Preserve canonical ordering and content-derived IDs.
- Keep comments, whitespace flexibility, parse errors, and conformance fixtures
  aligned with the versioned spec.

Read [spec/glp-0.1.md](spec/glp-0.1.md) and
[docs/glp-0.2-policy-architecture.md](docs/glp-0.2-policy-architecture.md)
before modifying models, parser, or renderer.

## Markdown and extraction

Glyph must work on messy real-world instruction material, including AGENTS,
Claude, Copilot, Cursor, README, CONTRIBUTING, and generic Markdown files.
Support headings, prose, lists, checklists, tables, blockquotes, fenced code,
inline code, commands, setup, testing, deployment, architecture, and safety
context without assuming ideal headings or formatting.

Use one authoritative operational-status decision throughout candidates,
metrics, verification, and reports. Generic documentation and examples must not
inflate operational or safety denominators. Conversely, real instructions and
safety candidates must not disappear.

The deterministic pipeline is:

```text
Markdown → Document IR → candidate extraction → context/risk classification
→ exact custom policy → custom rule → registry → clause parser → preserve
→ provenance, conflicts, metrics, renderer, and CI consumers
```

See [semantic extraction engine](docs/semantic-extraction-engine.md).

## Public CLI and integrations

The `glyph` entry point must keep useful help and readable errors for:

```text
version, doctor, init, compile, render, stats, verify, benchmark,
benchmark-real, lint, diff, lock, check, emit, select, score, inspect,
rules suggest, and optional mcp
```

Maintain progressive Markdown compatibility targets:

```text
agents-md, claude-md, copilot, cursor, generic-md
```

Task-aware selection is deterministic and rule-based. Safety and approval rules
normally remain selected. Commands that modify files must fail clearly on
missing paths, invalid formats, unsafe thresholds, or semantic conflicts.

## Tests and validation

Minimum everyday validation:

```bash
pytest
ruff check .
mypy
glyph benchmark benchmarks/
git diff --check
```

For release-sensitive changes:

```bash
python -m build
bash scripts/release-smoke.sh
```

Required coverage depends on the affected surface:

- tokenizer, parser, renderer, compiler, verifier, lint, diff, lock, check,
  emitters, selection, score, adapters, and MCP service where relevant;
- v0.1 compatibility and v0.2 parse/render/parse determinism;
- content-derived IDs and canonical ordering;
- subject versus scope; action, state, and passive predicates; conditions,
  exceptions, alternatives, and inseparable policy linkage;
- strict mode, semantic safety regression detection, lock stability, and
  Markdown compatibility;
- conservative narrative non-matches, ambiguous preservation, and context
  denominator correctness.

Run the fixed corpus only after synthetic tests and local validation pass. Its
reports must remain metadata-only. Do not run the separately governed behavior
matrix unless a user explicitly schedules it; static green is not permission to
claim behavioral equivalence.

## Release and documentation honesty

Generated benchmark and corpus reports are evidence for the exact input set and
revision measured. Never present their percentages as universal guarantees.

Release work requires the validation described in
[docs/release-process.md](docs/release-process.md). Do not tag, publish, or
contact external projects without explicit authorization. Keep the changelog,
README, release report, and compatibility claims aligned with the artifact.
