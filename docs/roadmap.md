# Roadmap and Scope

Glyph is built as a complete local developer tool, but its roadmap is governed
by evidence rather than a promise to interpret all natural language.

## Current capabilities

- Deterministic compilation of supported instruction-like Markdown.
- Versioned `.glp` manifests, including a conservative 0.2 policy model.
- Registry rules, custom semantic rules, and exact custom policies.
- Verification, strict gates, semantic diff, locks, emitters, selection, lint,
  score, benchmarks, and optional local MCP transport.

## Near-term maintenance criteria

Future parser work should be accepted only when a sanitized shape has one
demonstrated deterministic decomposition, synthetic positive and negative
fixtures, no safety-retention regression, and compatible downstream behavior.

## Explicit non-goals without a separate proposal

- LLM-driven extraction in the core library or benchmark.
- Hosted source processing or remote API dependencies.
- Claims of universal Markdown understanding or identical agent behavior.
- Silent flattening of `.glp 0.2` semantics to v0.1.
- Repository-specific parser phrases in the shared grammar.

## Evidence expansion

The static corpus validates a fixed set of pinned repositories. Broader
confidence comes from adding diverse, license-safe evaluation evidence and
monitoring preservation, safety, false positives, determinism, and token
reduction—not from weakening gates or memorizing source text.
