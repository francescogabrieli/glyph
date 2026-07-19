# Architecture

Glyph is a local, deterministic compiler pipeline. It turns instruction-like
Markdown into a semantic manifest and an auditable extraction ledger.

```text
source files
  → adapter detection and Markdown parser
  → Document IR
  → candidate extraction and operational decision
  → custom policy / custom rule / registry / clause parser
  → canonical rules, structured policies, preserve fallback
  → conflict detection, provenance, metrics, renderers, and CI consumers
```

## Package boundaries

The implementation is organized by responsibility rather than by command or
file age. Dependencies flow inward toward the domain model and through the
deterministic compilation pipeline:

```text
glyph.interfaces       CLI, service layer, configuration, optional MCP
        ↓
glyph.governance       diff, lock, check, selection, emit, lint, score, benchmark
        ↓
glyph.pipeline         compilation, provenance, conflicts, verification
glyph.formats          versioned .glp parsing and rendering
glyph.semantics        rule registry, clause parsing, risk, policy resolution
glyph.source           adapters, Markdown AST, document IR, candidates, tokenizer
        ↓
glyph.core             Pydantic domain models and shared value objects
```

| Package | Responsibility |
| --- | --- |
| `core/` | Version-independent domain models, enums, IDs, and shared value objects. |
| `source/` | Source adapters, Markdown structure, document IR, candidate extraction, and tokenization. |
| `semantics/` | Registry mapping, confidence, deterministic clause decomposition, custom rules, risk, and policy resolution. |
| `formats/` | Lossless versioned `.glp` parsing and canonical rendering. |
| `pipeline/` | Compilation, provenance, extraction ledger, conflict analysis, and verification. |
| `governance/` | Review, CI, compatibility, selection, emitters, linting, scoring, reports, and benchmarks. |
| `interfaces/` | CLI implementation, service façade, configuration, diagnostics, and optional MCP transport. |

Each module is imported from its owning package. The package root intentionally
contains no legacy module aliases: dependency direction remains visible in both
imports and the filesystem.

## Design invariants

- No network calls or LLM calls in the library, compiler, or benchmark.
- Canonical ordering and content-derived identifiers are deterministic.
- A candidate has an explicit auditable destination.
- Ambiguity resolves to preservation, not invented structure.
- Safety and retention are tracked separately from token reduction.
- Downstream consumers preserve `.glp 0.2` semantics or fail clearly rather
  than silently downgrade them.

## Version boundary

`glyph/0.1` keeps its flat action/target policy form. `glyph/0.2` adds recursive
policy expressions, conditions, exceptions, `allow`, and inseparable links.
The internal model upgrades 0.1 losslessly; rendering a 0.2 policy as 0.1 is
rejected whenever meaning would be lost.

Read [Semantic extraction engine](semantic-extraction-engine.md) for the
pipeline and [`.glp 0.2` policy architecture](glp-0.2-policy-architecture.md)
for the expression model.
