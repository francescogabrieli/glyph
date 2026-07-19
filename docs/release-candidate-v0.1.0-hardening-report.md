# Glyph v0.1.0 RC Hardening Report

Date: 2026-07-12  
Validation tree: `1e7cf73` plus the working-tree hardening batch

## Scope completed

- Retained deterministic `PolicyAtom`, `PreservedDirective`, and candidate-resolution ledger semantics.
- Applied one cross-cutting policy-extraction batch for labeled Markdown directives, leading conditional imperatives, compound safety denials, and explicit modal-category precedence.
- Added synthetic, license-safe regression coverage for those directive shapes.
- Kept the fixed ten-repository corpus pinned to the SHAs in [`corpus/external-v0.1-manifest.json`](../corpus/external-v0.1-manifest.json).
- Reworked the external sweep to emit only license-safe metadata and aggregate post-hardening metrics; no third-party source text is stored.

## Local validation

| Check | Result |
|---|---:|
| `pytest` | 228 passed |
| `glyph benchmark benchmarks/` | 11 cases; 94.0% structured, 100.0% retained, 100.0% safety, 46 preserved, 0 high-risk preserved, 0 dropped |
| `glyph benchmark-real .` | 17 files; 59.0% reduction, 34.0% structured, 99.8% retained, 98.0% safety, 175 preserved, 9 high-risk preserved, 0 dropped |
| Fixed ten-SHA external corpus sweep | 10 repositories, 124 files, 0 crashes, 0 non-determinisms, 0 conflicts |
| `python -m build` | sdist and wheel built successfully |
| Clean-wheel strict compile | passed |
| Clean-wheel strict check | passed |
| Clean-wheel MCP help smoke | passed |
| `git diff --check` | passed |
| Artifact hygiene check | passed |

The synthetic benchmark remains green, but the external corpus is a release gate and is not green. The complete metadata-only results are in [`corpus/external-v0.1-report.json`](../corpus/external-v0.1-report.json) and [`corpus/external-v0.1-report.md`](../corpus/external-v0.1-report.md).

## External corpus result

The sweep used exactly the ten manifest repositories and their pinned SHAs. It discovered 124 supported Markdown files, compiled each deterministically, measured token reduction without clamping negative values, and retained only hashes, sizes, counts, adapter names, classifications, and aggregate metadata.

| Metric | Result |
|---|---:|
| Average structured coverage | 40.4% |
| Minimum structured coverage | 0.0% |
| Average retained coverage | 98.6% |
| Minimum retained coverage | 50.0% |
| Average safety retention | 98.5% |
| Minimum safety retention | 0.0% |
| Preserved directives | 1,450 |
| High-risk preserved directives | 99 |
| Dropped candidates | 0 |
| Average canonical candidate coverage | 5.1% |
| Agent-instruction coverage | 72.2% average; 0.0% minimum |
| Structured operational coverage | 51.2% average; 0.0% minimum |
| Token reduction | 59.3% average; -105.3% minimum; 9 negative files |

The external gate therefore fails unchanged criteria: retained coverage is not 100% across all supported files, safety retention is not 100%, high-risk preserved count is not zero, and both structured agent-instruction and structured operational coverage thresholds are below their required levels. Dropped count and determinism pass.

## Failure classification

The sweep classifies surfaced retained/dropped candidates without serializing their wording:

| Classification | Count |
|---|---:|
| Correct preserved blocker | 936 |
| Unsupported conditional pattern | 220 |
| False-positive operational candidate | 181 |
| Non-operational documentation | 92 |
| Policy extraction bug | 13 |
| Repo-specific custom rule candidate | 8 |
| Parser/classifier bug | 0 |
| Conflict requiring human review | 0 |

The remediation batch addressed the general policy-extraction pattern identified in the first pass. It improved agent-specific structured coverage from 37.3% to 51.2% and reduced agent-specific high-risk preserved directives from 20 to 6. The remaining external failures span correct preservation, conditional semantics, false-positive classification, and repository-specific conventions; no second remediation batch was applied and no gate was lowered.

## Static-corpus architecture audit

The authoritative baseline was reproduced after the hardening batch with the
same 10 repositories, 124 files, and reported metrics. The regenerated
metadata-only JSON and Markdown were byte-identical to the tracked external
reports. The environment did not provide a `python` shell shim, so the
canonical sweep script was invoked through `uv run python` with the same
manifest, checkout root, and output arguments.

The audit inspected every high-risk preserved candidate and every failing
population through a local-only sanitized structural ledger. It found 21
unretained candidates, all blockquotes outside instruction adapters; the
resolver rejects them as non-operational while the current metric denominator
still counts them as operational. Four are high-risk by the safety classifier.
This is a bounded false-positive/context issue, not a source-loss fix.

More importantly, 47 of the 99 high-risk preserved directives use subject-modal
state, relation, passive-predicate, or multi-entity forms that cannot be
faithfully encoded by the v0.1 `PolicyAtom` fields. The remaining high-risk
population includes 26 condition/exception forms, 24 inheritance forms, and
two Markdown-wrapper forms. Their current policy derivation confidence is
`0.00`, so lowering a confidence threshold cannot address them.

The current serialized policy fields do not distinguish a governed subject
from code-area scope, encode a relation/predicate or object complement, retain
condition operators, or link inseparable compound policies. Coercing these
forms into `action`, `target`, or `scope` would change serialized semantics.
Because the fixed gate requires zero high-risk preserved directives, no
backward-compatible implementation-only remediation can make this corpus pass
honestly. No second policy-template wave was implemented.

The full sanitized cluster table and redesign boundary are in
[`docs/external-corpus-preserved-clusters-v0.1.md`](external-corpus-preserved-clusters-v0.1.md)
and [`docs/policy-template-remediation-v0.1.md`](policy-template-remediation-v0.1.md).

## RC gate status

The RC is **not ready to publish**.

The external behavior matrix was not run because the fixed external static corpus gate failed. No Git tag, GitHub Release, or PyPI publication was created.

No third-party instruction files, raw transcripts, worktrees, caches, stdout/stderr dumps, or local absolute paths were added to the committed tree.
