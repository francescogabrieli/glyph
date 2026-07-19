# External Corpus Preserved-Directive Clusters — v0.1

## Scope and reproducibility

This is a metadata-only analysis of the fixed ten-repository, ten-SHA external
corpus. No third-party directive text, checkout path, transcript, generated
manifest, or cache is included.

Canonical sweep command (using the project runtime in an environment without a
`python` shell shim):

```bash
export GLYPH_EXTERNAL_CORPUS=/path/to/ignored/pinned-checkouts
export GLYPH_CORPUS_REPORT_DIR=/path/to/local/output-directory

uv run python evals/corpus_sweep.py \
  --manifest corpus/external-v0.1-manifest.json \
  --checkouts "$GLYPH_EXTERNAL_CORPUS" \
  --json-out "$GLYPH_CORPUS_REPORT_DIR/external-v0.1-report.json" \
  --markdown-out "$GLYPH_CORPUS_REPORT_DIR/external-v0.1-report.md"
```

The resulting JSON and Markdown are byte-identical to the tracked canonical
reports. The manifest pins 10 repositories and the run discovers 124 supported
files.

## Metric definitions

The external sweep uses the post-resolution ledger produced by
`src/glyph/compiler.py`.

| Metric | Numerator | Denominator |
| --- | --- | --- |
| Retained coverage | Operational candidates with a `canonical`, `policy`, or `preserve` destination | All candidates whose intent is mappable and whose operational confidence is at least 0.18 |
| Safety retention | Retained high-risk operational candidates | High-risk operational candidates; risk is determined from safety terms even if resolver state has not been assigned |
| Structured agent-instruction coverage | Agent/testing/safety candidates with a `canonical` or `policy` destination | The corresponding operational agent candidate subset (confidence at least 0.4, plus canonically/policy-resolved candidates) |
| Structured operational coverage | Operational candidates with a `canonical` or `policy` destination | All operational candidates |
| Dropped count | Operational candidates with `dropped` destination | Count, not a percentage |
| High-risk preserved count | Preserved operational candidates whose risk is high | Count, not a percentage |

The gate averages the two structured metrics over the 18 agent-specific files;
retention and safety gates are required for every supported file.

## Verified baseline

| Measure | Result |
| --- | ---: |
| Repositories / supported files | 10 / 124 |
| Crashes / nondeterministic outputs / conflicts | 0 / 0 / 0 |
| Average retained coverage / minimum | 98.6% / 50.0% |
| Average safety retention / minimum | 98.5% / 0.0% |
| Preserved directives / high-risk preserved | 1,450 / 99 |
| Dropped directives | 0 |
| Structured agent-instruction coverage | 72.2% |
| Structured operational coverage | 51.2% |
| Average token reduction / minimum | 59.3% / -105.3% |
| Negative-reduction files | 9 |

The nine files below 100% retention are limited to metadata identifiers in the
canonical report; all 21 unretained candidates are blockquotes outside an
instruction adapter. Four are high risk according to the safety classifier.
The resolver deliberately records these as non-operational, while the current
metric denominator still counts them as operational. This is a false-positive
candidate/context inconsistency, not source loss or a dropped directive.

## Population inspection

The local-only ledger analysis inspected every high-risk preserved candidate,
every unretained and safety-unretained candidate, all 12 agent-instruction and
14 agent-operational coverage failures, all nine negative-reduction files, and
all preserved-directive clusters. It records only adapter, document role,
section role, block type, modality, inherited category, action family, target
family, condition/exception shape, risk, and resolution outcome.

The 99 high-risk preserved candidates are all `preserve` outcomes with a
policy-derivation confidence of `0.00` against the high-risk `0.90` threshold.
They span sensitive-data (56), authorization (17), deployment (16), database
change (6), and other (4) target families. Their structural forms include
simple modal/state relations (64), temporal or gate relations (11), leading
conditions (7), scoped forms (7), and smaller exception, label, and compound
forms. They are not candidates that would become structured merely by relaxing
confidence.

## Ranked remediation assessment

Each material cluster has one primary cause. Counts are candidate counts and
are intentionally not a reconstruction of source text.

| Rank | Cluster class and sanitized shape | Count / high risk | Affected adapters | Primary cause | Proposed general action | Expected impact | False-positive risk | Current PolicyAtom faithful? |
| ---: | --- | ---: | --- | --- | --- | --- | --- | --- |
| 1 | Generic-document blockquote with directive-like language | 21 / 4 | README, CONTRIBUTING, generic Markdown | false-positive operational candidate | Make candidate operational status respect the same blockquote context that the resolver already rejects | Would repair the retention/safety denominator inconsistency only | Low when limited to non-instruction adapters | N/A — classify before policy extraction |
| 2 | Subject-modal state/relation, passive predicate, or multi-entity safety rule | 47 / 47 | Mostly generic Markdown; also agent/README | PolicyAtom expressiveness blocker | Requires an explicit subject/object/relation representation; do not coerce into `scope` or opaque target text | Gate remains blocked without redesign | High if coerced | No |
| 3 | Leading/trailing condition, temporal gate, or exception with non-atomic predicate | 341 / 26 | All major adapters | condition/exception extraction gap | Extract only autonomous single-predicate cases after a richer condition model exists; retain the rest | Some structured increase possible, but cannot clear the high-risk set safely today | High for nested/alternative conditions | No for the recurrent compound subset |
| 4 | Terse entry inheriting `must` from a section | 625 / 24 | All major adapters; 133 agent-specific | mode/category inheritance gap | Require directive evidence or an explicitly modal list context before inheritance | Can reduce false-positive pressure, not turn every entry into policy | Medium; headings and lists are ambiguous | N/A until candidate status is justified |
| 5 | Directive with no stable action/target decomposition | 298 / 0 | All major adapters; 53 agent-specific | genuinely ambiguous preserved blocker | Preserve; no extraction change is justified | No safe structured gain | High | No |
| 6 | Simple reusable imperative with clear action and object | 98 / 0 | All major adapters; 27 agent-specific | deterministic policy-template gap | Add only independently tested templates after the architecture redesign decision | Limited; insufficient to clear any blocked high-risk relation | Medium | Yes for this bounded subset |
| 7 | Markdown label/wrapper hiding an otherwise direct predicate | 26 / 2 | Agents, CONTRIBUTING, README, generic Markdown | Markdown normalization gap | Normalize wrappers before recognition | Small, bounded improvement | Low | Yes |
| 8 | Multiple autonomous imperative predicates | 7 / 0 | Agents, CONTRIBUTING, README, generic Markdown | directive atomization gap | Split only when each clause has its own predicate and inherited context can be duplicated | Small, bounded improvement | Medium | Yes |
| 9 | Repository-local convention shape | 8 / 0 | CONTRIBUTING, README, generic Markdown | scoped convention extraction gap | Preserve unless a user provides a repository custom rule | No general gate gain | High | No as a universal rule |

## Architecture checkpoint

The v0.1 serialized `PolicyAtom` has category, action, target, scope, flat
conditions, flat exceptions, risk, and tags. It has no serialized subject or
actor, relation/predicate type, object complement, condition operator, or
compound-policy linkage. Reusing `scope` as a subject or flattening a relation
into `target` changes the semantics of those fields and would produce a
plausible-looking but unfaithful policy.

Because the fixed gate requires zero high-risk preserved directives, the 47
high-risk expressiveness blockers alone prevent a safe green result. The
remaining 52 high-risk preserved candidates include condition, inheritance,
and normalization forms; a subset may be addressable after redesign, but that
does not remove this blocker. No policy template or confidence relaxation was
implemented in this audit.

## Token accounting

Token reduction is reported, not used to alter any gate. The canonical report
lists each negative-reduction file: two short agent files, four agent or
agent-adjacent instruction files with preserved clauses, one short CLAUDE file,
one large README containing many preserved candidates, and one Kubernetes
agent file. The aggregate is 59.3%; the minimum is -105.3%; nine files are
negative. No reduction was clamped or optimized for this decision.
