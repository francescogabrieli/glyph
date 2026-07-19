# `.glp 0.2` Policy Architecture

## Decision

Glyph 0.2 uses one small recursive policy-expression language:

```txt
expression := atomic | all(expression...) | any(expression...) | not(expression)
atomic     := predicate-kind + subject + predicate + zero-or-more objects
```

A policy statement adds category (`must`, `deny`, `ask`, or `allow`), repository/code-area scope, attached
conditions, attached exceptions, risk, and tags. `all` and `any` children stay
inside one content-addressed policy statement, so inseparable compound meaning
is not split into independently selectable atoms. Conditions and exceptions
use the same expression grammar and name their attachment point (`policy` or a
nested atomic-expression id).

When one source clause contains different modalities, its statements remain
separate policies joined by a content-addressed `PolicyLink` with relation
`inseparable`. Selection, lockfiles, Markdown emitters, verification, and
semantic diff retain the linked set atomically. This is required by the
sanitized mixed-permission shape “actor may read the referenced resource but
must never delete it”; placing both predicates under one category would change
its meaning.

No sequence or general implication operator is included. An attached condition
already represents the only implication required by the audited shapes. The
sanitized blocker ledger does not prove ordering semantics.

## Field justification

| Semantic element | Sanitized blocker shape that requires it |
| --- | --- |
| `subject` | Subject-modal state/relation forms (`HRX-05`, `HRX-08`–`HRX-10`, `HRX-13`, `HRX-21`–`HRX-25`, `HRX-30`, `HRX-33`–`HRX-40`, `HRX-44`–`HRX-47`) govern an entity, not a path. |
| `scope` | Five `scope_phrase` blockers (`HRX-05`, `HRX-08`, `HRX-32`, `HRX-36`, `HRX-43`) separately constrain a code/repository area. |
| `predicate` and `objects` | Relation and passive forms require the relation to remain distinct from its object; an opaque target string cannot preserve that distinction. |
| `predicate_kind` (`action`, `state`, `passive`) | The corpus mixes imperative actions, required/prohibited states, and entities related through passive constructions. |
| `not` | Negative and subject-modal-negative shapes must negate the predicate expression, not mutate a target string. |
| `all` | Multi-entity and compound requirements whose clauses share modality/conditions must remain one inseparable policy. |
| `any` | Sanitized alternative-condition shapes outside this 47-row subset require explicit alternatives; a flat list would incorrectly mean conjunction. |
| attached condition expression | Leading, temporal, and gate blocker classes require a structured predicate and an explicit attachment point. |
| attached exception expression | Exception blocker classes require a structured exception and an explicit attachment point. |
| `allow` category | A residual explicit durable-authorization shape and a mixed allow/deny shape grant an action rather than requiring it or asking for approval. |
| `PolicyLink(relation=inseparable)` | A residual mixed allow/deny clause and a conditional approval-plus-reporting clause contain different modalities that cannot share one policy category or be selected independently. |

`subject`, `predicate`, and each object are canonical semantic terms, not raw
sentence fragments. When deterministic extraction cannot identify them, Glyph
keeps the source as a `PreservedDirective`.

## Version and compatibility boundary

- `glyph/0.1` and `g/0.1` retain their existing grammar and rendering.
- `glyph/0.2` and `g/0.2` explicitly select the expression grammar.
- A v0.1 policy upgrades to the shared semantic view as an action predicate
  with governed subject `agent`, its original action as predicate, and its
  original target as object. Original flat conditions and exceptions remain
  compatibility data; they are not relabeled as structured 0.2 expressions.
- A 0.2 statement may be rendered as 0.1 only when it is provably equivalent
  to one legacy action/target atom with no subject deviation, structured
  condition, structured exception, or compound expression. Otherwise downgrade
  fails explicitly.
- Content-derived ids cover the canonical semantic payload. Ordering is by id;
  expression children are canonicalized only for commutative `all` and `any`.
- `allow` and linked policies are 0.2-only. Attempting to render either as 0.1
  fails explicitly instead of dropping the permission or linkage.

## Sanitized 47-blocker acceptance matrix

The matrix is derived from the pre-existing local metadata-only audit. Anonymous
ids are ordered by the audit candidate hash and do not identify a repository or
reconstruct source text. “Preserve” means the architecture can hold a chosen
interpretation, but the sanitized shape still permits multiple lexical
decompositions and deterministic extraction must not guess.

| ID | Sanitized shape | Required fields/operators | Faithful model? | Multiple interpretations? | Preserve? |
| --- | --- | --- | --- | --- | --- |
| HRX-01 | required named-entity relation to sensitive data | subject, passive predicate, object | yes | yes | yes |
| HRX-02 | negative inclusion of sensitive data | not + action predicate + object | yes | no | no |
| HRX-03 | negative destructive relation | not + action predicate + object | yes | yes | yes |
| HRX-04 | required authorization state | subject, state predicate, object | yes | yes | yes |
| HRX-05 | scoped required environment relation | subject, state/passive predicate, object, scope | yes | yes | yes |
| HRX-06 | required named-entity relation to sensitive data | subject, passive predicate, object | yes | yes | yes |
| HRX-07 | negative sensitive-data state | not + state predicate + object | yes | yes | yes |
| HRX-08 | scoped required key-management relation | subject, passive predicate, object, scope | yes | yes | yes |
| HRX-09 | subject-modal negative sensitive-data relation | subject + not + state/passive predicate + object | yes | yes | yes |
| HRX-10 | subject-modal database normalization action | subject, action predicate, object | yes | yes | yes |
| HRX-11 | leading sensitive-data directive | action/passive predicate, object | yes | yes | yes |
| HRX-12 | negative deletion action | not + action predicate + object | yes | no | no |
| HRX-13 | subject-modal negative sensitive-data relation | subject + not + state/passive predicate + object | yes | yes | yes |
| HRX-14 | negative possession/creation relation | not + action/state predicate + object | yes | yes | yes |
| HRX-15 | negative passive return relation | not + passive predicate + subject + object | yes | no | no |
| HRX-16 | negative inclusion of sensitive data | not + action predicate + object | yes | no | no |
| HRX-17 | leading authorization-input directive | action predicate, object | yes | yes | yes |
| HRX-18 | negative inclusion of sensitive data | not + action predicate + object | yes | no | no |
| HRX-19 | negative authorization possession relation | not + state predicate + subject + object | yes | yes | yes |
| HRX-20 | negative acceptance of sensitive data | not + action predicate + object | yes | no | no |
| HRX-21 | subject-modal belonging relation | subject, state predicate, object | yes | no | no |
| HRX-22 | subject-modal negative sensitive-data relation | subject + not + state/passive predicate + object | yes | yes | yes |
| HRX-23 | authorization routing relation | action predicate, subject, object | yes | no | no |
| HRX-24 | subject-modal reference relation | subject, state predicate, object | yes | yes | yes |
| HRX-25 | subject-modal reference relation | subject, state predicate, object | yes | yes | yes |
| HRX-26 | negative compound database relation | not + all + linked atomic predicates | yes | yes | yes |
| HRX-27 | required absence state for sensitive data | not + state predicate + subject/object | yes | yes | yes |
| HRX-28 | negative export relation | not + action predicate + object | yes | yes | yes |
| HRX-29 | required absence state for sensitive data | not + state predicate + subject/object | yes | yes | yes |
| HRX-30 | subject-modal negative sensitive-data relation | subject + not + state/passive predicate + object | yes | yes | yes |
| HRX-31 | leading user-sensitive-data relation | action/passive predicate, object | yes | yes | yes |
| HRX-32 | scoped authorization treatment rule | action predicate, object, scope, attached condition | yes | yes | yes |
| HRX-33 | subject-modal mediated authorization relation | subject, passive predicate, object | yes | yes | yes |
| HRX-34 | subject-modal negative inclusion relation | subject + not + action predicate + object | yes | no | no |
| HRX-35 | required authorization state | subject, state predicate, object | yes | yes | yes |
| HRX-36 | scoped required deployment state | subject, passive/state predicate, object, scope | yes | yes | yes |
| HRX-37 | subject-modal key-management relation | subject, passive predicate, object | yes | yes | yes |
| HRX-38 | required negative authorization state | not + state predicate + subject/object | yes | yes | yes |
| HRX-39 | subject-modal key-management relation | subject, passive predicate, object | yes | yes | yes |
| HRX-40 | subject-modal negative request relation | subject + not + action predicate + object | yes | no | no |
| HRX-41 | negative targeting relation | not + action predicate + object | yes | yes | yes |
| HRX-42 | avoided deployment state/action | not + action/state predicate + object | yes | yes | yes |
| HRX-43 | scoped negative storage relation | scope + not + action/state predicate + object | yes | yes | yes |
| HRX-44 | subject-modal negative sensitive-data relation | subject + not + state/passive predicate + object | yes | yes | yes |
| HRX-45 | subject-modal negative sensitive-data relation | subject + not + state/passive predicate + object | yes | yes | yes |
| HRX-46 | negative authorization broadening action | not + action predicate + object | yes | yes | yes |
| HRX-47 | subject-modal required sensitive-data state | subject, state/passive predicate, object | yes | yes | yes |

The model is structurally sufficient for all 47 sanitized shapes. The matrix
does **not** claim deterministic extraction for all 47: 37 remain marked for
preservation because sanitized lexical evidence permits more than one predicate
or argument attachment. That is an extraction boundary, not a reason to coerce
meaning into 0.2 fields.

## Implemented compatibility and consumers

The implementation covers the shared models, 0.1/0.2 parser and renderer,
compiler provenance, verifier, semantic diff and safety regression reporting,
task selection, lock schema `glyph-lock/v3`, score/check readers, and every
Markdown compatibility emitter. A structured 0.2 policy id is validated against
its canonical payload while parsing. An attached condition or exception must
name `policy` or a content-derived expression-node id.

Natural-language extraction is intentionally smaller than the serialized
language. It accepts explicit subject-modal action, state, passive, permission,
and negative relations, plus conditions/exceptions whose atomic predicates and
`and`, `or`, or `not` operators are unambiguous. A local antecedent may be used
only from the immediately preceding clause in the same Markdown item, and only
when it exposes one label, located resource, or grammatical subject. Narrative attribution and explicitly
unknown, undocumented, unspecified, “appropriate”, or “relevant” relation
objects remain preserved.

## Validation and fixed-corpus result

The architecture and synthetic tests passed before the fixed corpus was run.

| Validation | Result |
| --- | ---: |
| Pytest | 384 passed |
| Synthetic benchmark structured / retained / safety | 96.6% / 100.0% / 100.0% |
| Synthetic benchmark preserved / high-risk preserved / dropped | 29 / 0 / 0 |
| Fresh-wheel release smoke | pass |
| Repeated 0.2 parse/render/parse | equal in readable, compact, and ultra profiles |
| Determinism failures in fixed corpus | 0 |

The fixed-corpus comparison is metadata-only:

| Metric | Pre-final 0.2 baseline | Final deterministic parser |
| --- | ---: | ---: |
| Average retained coverage | 100.0% | 100.0% |
| Average safety retention | 100.0% | 100.0% |
| Average structured coverage | 64.82% | 78.65% |
| Agent-instruction structured coverage | 95.95% | 96.63% |
| Structured operational coverage | 80.81% | 82.18% |
| Preserved directives | 606 | 316 |
| High-risk preserved directives | 24 | 0 |
| Dropped directives | 0 | 0 |
| Average token reduction | not retained in the transient baseline | 55.82% |
| Minimum reduction / negative files | not retained in the transient baseline | -352.0% / 12 |

The candidate-context correction removes the 21 generic-document blockquotes
already resolved as non-operational from both operational and safety
denominators. Positive instruction-adapter blockquotes remain operational, and
synthetic paragraph safety directives remain encoded. This repairs retention
and safety accounting without hiding a retained or safety candidate.

## Current boundary

The fixed static gate is green without lowering a threshold: all high-risk
operational candidates are structured or canonical, while genuinely ambiguous
lower-risk clauses remain preserved. The parser did not require `sequence`, a
general implication operator, NLP, or an ambiguity operator. Credential
availability and command-example descriptions were corrected at the context
or risk layer instead of being coerced into expressions.

The remaining 316 preserved directives are a deliberate product boundary, not
a claim of universal natural-language understanding. Extending deterministic
grammar remains appropriate only for sanitized shapes with one demonstrated
parse. Repository-specific meaning still requires an exact custom policy. The
external behavior matrix was not run in this milestone.
