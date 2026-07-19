# External Corpus High-Risk Taxonomy — `.glp 0.2`

## Scope

This metadata-only taxonomy follows all 95 high-risk preserved candidates from
the `.glp 0.2` parser baseline through the deterministic-clause milestone. It
contains no third-party wording, repository identity, local path, or source
snippet. Candidate correlation uses the existing content hash within its
metadata-only file record.

The taxonomy is emitted from the same `CandidateResolution` derivation evidence
used by the compiler. The corpus reporter does not reinterpret source text.

## Baseline-95 outcomes

| Shape | Predicate | Objects | Operators | Attachment | Ambiguous | Reason | New outcome | Count |
| --- | --- | ---: | --- | --- | --- | --- | --- | ---: |
| compound state | — | 4 | `all`, `any`, `atomic` | — | no | `unique_compound_state` | policy | 1 |
| contrastive relation | state | 2 | `atomic` | — | no | `unique_contrastive_relation` | policy | 1 |
| negative action | — | 2 | `all`, `atomic`, `not` | — | no | `unique_negative_action` | policy | 1 |
| negative passive | — | 0 | `all`, `atomic`, `not` | — | no | `unique_negative_passive` | policy | 1 |
| negative passive | passive | 0 | `atomic`, `not` | — | no | `unique_negative_passive` | policy | 1 |
| unresolved | — | 0 | — | — | no | `narrative_attribution` | preserve | 2 |
| unresolved | — | 0 | — | — | no | `unsupported_action_predicate` | preserve | 5 |
| unresolved | — | 0 | — | — | no | `unsupported_clause_shape` | preserve | 59 |
| unresolved | — | 0 | — | — | no | `unsupported_predicate` | preserve | 6 |
| unresolved | — | 0 | — | — | yes | `ambiguous_condition_attachment` | preserve | 5 |
| unresolved | — | 0 | — | — | yes | `ambiguous_exception_attachment` | preserve | 3 |
| unresolved | — | 0 | — | — | yes | `pronoun_reference` | preserve | 6 |
| unresolved | — | 0 | — | — | yes | `subject_too_broad` | preserve | 4 |

All 95 baseline candidates were correlated: 5 now have one structured
interpretation and 90 remain preserved. “Unsupported” is distinct from
“ambiguous”: unsupported clauses may continue through the lossless v0.1
compatibility parser, while ambiguous high-risk clauses cannot be guessed.

## Deterministic-clause milestone result

| Metric | Parser baseline | Deterministic-clause milestone |
| --- | ---: | ---: |
| Average structured coverage | 45.00% | 45.22% |
| Agent-instruction coverage | 79.18% | 78.33% |
| Structured operational coverage | 54.63% | 53.18% |
| Preserved directives | 1,361 | 1,375 |
| High-risk preserved directives | 95 | 94 |
| Retained / safety retention | 100% / 100% | 100% / 100% |
| Dropped / conflicts / nondeterminism | 0 / 0 / 0 | 0 / 0 / 0 |
| Average token reduction | 58.29% | 58.22% |

The milestone satisfies its monotonic static criteria but does not satisfy the
full release gate. The remaining ambiguous population still requires exact
repository custom policies or continued preservation. No gate was lowered and
no behavior matrix was run.

## Final static-gate result

A subsequent fail-closed pass classified the residual population by sanitized
shape, corrected contextual risk and document-role false positives, added
bounded local antecedent resolution, and introduced only the two serialized
semantics proven necessary by the residual audit: `allow` and inseparable
cross-modality policy linkage.

| Metric | Pre-final baseline | Final result |
| --- | ---: | ---: |
| Average structured coverage | 64.82% | 78.65% |
| Agent-instruction coverage | 95.95% | 96.63% |
| Structured operational coverage | 80.81% | 82.18% |
| Preserved directives | 606 | 316 |
| High-risk preserved directives | 24 | 0 |
| High-risk operational candidates | 112 | 59 |
| Retained / safety retention | 100% / 100% | 100% / 100% |
| Dropped / nondeterminism | 0 / 0 | 0 / 0 |

The 24 residual blockers were resolved without storing their wording: false
operational candidates and incidental risk lexemes were removed through the
authoritative context/risk decisions; uniquely decomposable condition,
alternative, permission, and mixed-modality shapes became structured; and the
preserved fallback remains active for ambiguity outside the high-risk set.
Every fixed static gate criterion now passes. The external behavior matrix was
not run.
