# Semantic Extraction Engine

Glyph is not a regex compressor. It uses a deterministic semantic extraction pipeline over structured Markdown.

Pipeline:

```txt
Markdown / instruction-like files
        ↓
Markdown structural parser
        ↓
Document IR
        ↓
Document role/audience and atomic operational candidate extraction
        ↓
Multi-signal semantic classification
        ↓
Exact custom policy → custom semantic rule → canonical registry → deterministic clause parser → preserve
        ↓
Conflict detection
        ↓
GLP compilation
        ↓
Candidate ledger, retention metrics, and reports
```

The Markdown parser recognizes headings, paragraphs, bullet lists, numbered lists, checklists, fenced code blocks, inline code, tables, blockquotes, and horizontal rules. The Document IR retains source path, line numbers, section hierarchy, block type, table rows, code language, document role, and intended audience.

Operational candidates are extracted before classification. A candidate is a text span that looks like it may instruct a coding agent. Candidate signals include modal verbs, negative language, approval language, completion language, testing terms, safety terms, imperatives, section context, and repository-specific terms.

Semantic classification uses multiple deterministic signals: phrase patterns, semantic keyword groups, section hints, modal hints, adapter context, block type, and command proximity. Each match has a confidence score from `0.0` to `1.0` and signal explanations.

Glyph atomizes clauses only where a second autonomous directive predicate exists, inherits mode from headings such as “Ask first” or “Never”, and keeps conditions/exceptions attached to their directive. Tables and code blocks count as instructions only in explicit operational context. If an operational instruction cannot be mapped or structured safely, Glyph preserves its wording and records the candidate-to-atom resolution.

The `.glp 0.2` clause parser records its modality, subject, predicate kind,
objects, operators, attachment, evidence, and a deterministic reason code. It
emits a structured policy only when exactly one decomposition survives. Vague
references, pronouns without a safely retained antecedent, ambiguous
coordination, and unknown attachment remain `preserve` outcomes. These
derivation fields also drive metadata-only corpus taxonomy; no second corpus
heuristic reinterprets the source.

See [No Silent Semantic Loss](no-silent-semantic-loss.md) for the coverage model, strict mode, unmapped candidates, and custom-rule workflow.
