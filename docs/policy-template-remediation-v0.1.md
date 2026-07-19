# Policy-Template Remediation Assessment — v0.1

## Decision boundary

This document records the static-corpus architecture checkpoint. It is not an
implementation plan for forcing the current gate to pass.

The current pipeline is:

```txt
source directive -> normalization -> atomization -> policy template -> PolicyAtom/canonical rule -> preserve
```

The fixed-corpus audit verified that bounded normalization and simple
single-predicate templates remain valid improvements. They cannot satisfy the
release gate under the current serialized semantics because 47 high-risk
directives require relation-aware representation and the gate permits no
high-risk preserved fallback.

## Safe work that was deliberately not used as a metric shortcut

| Family | Current representation | Decision |
| --- | --- | --- |
| Non-instruction blockquotes in README/CONTRIBUTING/generic Markdown | Resolver already treats them as non-operational, but the metric denominator still includes them | Candidate-context correction is valid, but it is insufficient for the gate and was not bundled with unrelated template expansion |
| Label-prefixed direct imperatives | Current action/target/condition fields can represent bounded cases | Suitable for future isolated implementation with synthetic positive and narrative non-match tests |
| Autonomous compound imperatives | Separate atoms can preserve shared context when both clauses are independently directive | Suitable only where recombination is demonstrably equivalent |
| Flat conditional imperative | Current condition/exception strings can retain a simple single predicate | Suitable only when no actor, alternative, nesting, or linked clause is lost |
| Subject-modal, state, or relationship policy | `scope` is not a subject field and `target` is not a relation AST | Do not implement as a template; it requires architecture work |

## Required architecture work before another full-gate remediation pass

Any redesign must be versioned, deterministic, and preserve the existing v0.1
reader for existing manifests. At minimum it needs a way to serialize, rather
than infer at render time:

- the governed subject or actor separately from code-area scope;
- the relation or predicate, including state and passive constructions;
- structured condition operators and their attachment point;
- exception and alternative relationships; and
- a compound-policy relationship when atomization would change meaning.

That is new serialized semantic information. It cannot be added as a
backward-compatible implementation-only `PolicyAtom` refinement without
either discarding it on render or redefining existing fields. It therefore
exceeds the v0.1 `.glp` grammar constraint for this release-gating task.

## Regression safeguards for a future redesign

Before re-running the external corpus, tests should cover each new structural
form with license-safe synthetic fixtures:

- positive relation extraction and deterministic rendering;
- conservative non-match for nearby narrative prose;
- subject versus code-area scope distinction;
- simple, nested, and alternative conditions;
- exception attachment;
- compound policy recombination; and
- preservation of unresolved and high-risk clauses without risk downgrades.

The next corpus pass must compare candidate outcomes by adapter, document role,
risk, section/block type, and structured/preserved/filtered result. It must
also reassert no retained or safety candidate disappears and that generic
documentation false positives do not increase.

## Non-actions

This assessment did not change the `.glp` grammar, register corpus-specific
phrases, relax confidence, reclassify genuine directives for a metric gain,
run the behavior matrix, tag a release, or publish an artifact.
