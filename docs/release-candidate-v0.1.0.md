# Glyph v0.1.0 release-candidate validation

**Status: blocked — do not tag, publish, or create a GitHub Release.**

This report records a release-candidate validation pass on 2026-07-11. The base
commit was `f87c94e368b30011f7a9b07624512710132b9d10`; the validation changes and
curated reports are intentionally still in the working tree for review.

## Environment

- Local validation: Python 3.14.4 on macOS.
- CI updated to test Python 3.10, 3.11, 3.12, 3.13, and 3.14; packaging and MCP
  smoke remain pinned to Python 3.11 in CI.
- Codex CLI available: 0.144.0.
- Claude Code available: 2.1.126.

## Completed gates

- `pytest`: passed, 215 tests.
- `python -m build`: passed; wheel and sdist built.
- `glyph doctor` and `glyph doctor --json`: passed.
- `glyph benchmark benchmarks/`: passed.
- `glyph benchmark-real . --patterns ...`: passed.
- `bash scripts/release-smoke.sh`: passed.
- `git diff --check`: passed.
- Clean non-editable wheel install, `pip check`, CLI help/version/doctor: passed.
- Clean MCP-extra wheel install, `pip check`, and `glyph mcp --help`: passed.

The inspected wheel contains the `glyph` package and `py.typed`. The sdist contains
the documented source, fixtures, and curated corpus metadata; neither archive
contains raw behavior artifacts, copied external repositories, cache directories,
or `node_modules`.

## External static corpus

The metadata-only sweep pinned ten repositories to the SHAs in
[`corpus/external-v0.1-manifest.json`](../corpus/external-v0.1-manifest.json).
It compiled every discovered supported file twice, ran selection for the three
standard tasks, and performed multi-input compilation where applicable. The full
sanitized results are in
[`corpus/external-v0.1-report.md`](../corpus/external-v0.1-report.md) and
[`corpus/external-v0.1-report.json`](../corpus/external-v0.1-report.json).

| Metric | Result |
| --- | ---: |
| Repositories | 10 |
| Files compiled | 124 |
| Agent-specific files | 18 |
| Determinism failures | 0 |
| Average token reduction | 93.9% |
| Average agent-instruction coverage | 40.8% |
| Average operational coverage | 45.3% |
| High-risk unmapped candidates | 249 |
| Files requiring review | 68 |

The exact static gate fails: both agent-specific coverage criteria are below the
required 90% semantic / 80% operational thresholds, and high-risk candidates remain.
Negative or low reductions are retained per file in the report rather than hidden.

Every surfaced unmapped finding is classified in the JSON report without retaining
its third-party text: 242 `bug registry`, 2,165 `bug structural parser/classifier`,
61 `conditional policy not representable in .glp v0.1`, and 62 `repo-specific rule
requiring custom registry`. The findings span unrelated domains and policies, so a
single registry patch would be overfitting rather than an evidence-backed v0.1
remediation. No semantic remediation batch was applied in this cycle.

## Cross-runtime behavior evaluation

**Blocked before execution.** The requested 12-cell evaluation (two new cases ×
three conditions × Codex and Claude Code) was not run because the preceding static
release gate failed materially. Running it would not make the release candidate
eligible and would create misleading behavioral evidence while safety-critical
semantics are still surfaced as unmapped.

The blocked plan would have used pinned source revisions, isolated copied worktrees,
approval `never`, workspace-write sandboxing, one sample per cell, and only curated
summary metadata. It must be rerun only after the static blocker is resolved. No
claim about behavior preservation, cross-runtime equivalence, Codex behavior, or
Claude behavior is supported by this validation pass.

## Artifact hygiene

- Removed 309 tracked raw behavior artifacts (prompts, instruction copies,
  stdout/stderr, diffs, status files, and validation logs).
- Removed eight tracked raw behavior result/task dumps that exposed local paths or
  pointed to raw artifacts.
- Added ignored local destinations for future behavior artifacts and results.
- Kept only a pinned corpus manifest, hashes/metrics/classifications, and curated
  reports; no third-party instruction-file contents are committed.
- Sanitized the retained historical task definitions to remove absolute local paths.
- Removed the tracked `.DS_Store` and added an ignore rule to prevent recurrence.
- The explicit hygiene checks found ignored local build/test caches only; the staged
  artifact paths are removals, not additions to the release-candidate tree.

## Open blockers and claim boundary

The v0.1.0 RC is not ready. The external corpus coverage gap and its 249 high-risk
unmapped candidates are release blockers; the new 12-cell behavior evaluation is
consequently blocked, not skipped silently. Packaging health does not override those
semantic gates.

Allowed statement: a pinned, metadata-only external static sweep was run and exposed
the blockers above. Not allowed: that Glyph preserves universal agent behavior,
losslessly compresses Markdown, works perfectly on all instruction files, or is
natively supported by any coding-agent runtime.
