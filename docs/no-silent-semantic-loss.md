# No Silent Semantic Loss

Glyph does not pretend every Markdown sentence can be safely compressed.

Every operational candidate has an explicit ledger destination: a custom rule, a registered semantic unit, a structured repository policy, a source-faithful preserved directive, or non-operational context. A candidate may be marked `dropped` only for an internal compiler error, which fails compilation. This keeps semantic loss reviewable instead of silent.

## Registered Semantic Units

Registered semantic units are deterministic rule IDs in the Glyph registry or a project custom-rule file.

Examples:

```txt
run_tests_before_done
secrets_commit
destructive_ops
avoid_generated_files
update_docs_when_behavior_changes
```

These units represent operational behavior, not original wording.

## Operational Candidates

An operational candidate is a text span that looks like it may instruct a coding agent.

Glyph uses deterministic signals such as:

- modal language: must, should, never, avoid, ask, before
- imperatives: run, use, keep, report, update, preserve
- safety terms: secrets, credentials, production, destructive
- testing terms: tests, suite, pytest, lint, typecheck
- section context: Testing, Security, Pull Requests, Database
- command proximity and repository-specific wording

Glyph also filters likely non-operational prose such as project descriptions, conceptual overview, historical notes, example-only context, and command-table labels.

## Semantic Coverage

Semantic coverage answers:

```txt
Of the registered semantic units detected in the source, how many are encoded in the .glp?
```

Formula:

```txt
Semantic Coverage = encoded_semantic_units / detected_semantic_units
```

This is not a claim that arbitrary prose was preserved.

## Coverage Metrics

Glyph keeps the existing **semantic coverage** metric for registered semantic IDs as a compatibility diagnostic. It is deliberately not a claim about the whole document and is not the post-hardening retention gate.

The end-to-end ledger also reports:

```txt
- **Canonical candidate coverage**: candidates mapped to a registered or custom rule.
- **Structured coverage**: candidates encoded as a canonical rule or `policy[]` atom.
- **Retained coverage**: candidates encoded as a canonical rule, policy atom, or `preserve[]` directive.
- **Safety retention**: retained coverage for high-risk operational candidates.
- **Preserved count**, **high-risk preserved count**, and **dropped count**.
```

Formula:

```txt
Structured Coverage = (canonical + policy candidates) / all operational candidates

Retained Coverage = (canonical + policy + preserved candidates) / all operational candidates
```

A file can have high semantic coverage while using preserved directives. That is expected for repository-specific wording that cannot be structurally represented with sufficient confidence.

## Conservative Fallback

Glyph structures a repository policy only at confidence `>= 0.80`, and at `>= 0.90` for safety-critical content. Below that threshold it stores the exact operational clause in `preserve[]`; it does not silently omit it. `--max-unmapped` counts genuinely dropped candidates, and `--max-high-risk-preserved` gates high-risk preserved fallbacks. The legacy `--max-high-risk-unmapped` field remains a compatibility diagnostic for genuinely dropped candidates.

They appear in:

```bash
glyph inspect README.md --show-unmapped
glyph compile README.md -o README.glp --report report.md
glyph lint README.md
glyph rules suggest README.md
```

Keeping these visible is the main safety mechanism. Glyph compresses what it understands, structures what it can represent safely, and preserves the remainder for human review.

## Strict Mode

Strict mode can fail compilation when unmapped candidates or low operational coverage would make the generated manifest too risky for CI:

```bash
glyph compile README.md -o README.glp \
  --strict \
  --min-retained-coverage 100 \
  --min-structured-coverage 90 \
  --max-high-risk-preserved 0
```

`glyph check` can enforce the same behavior against a committed `.glp`:

```bash
glyph check README.md README.glp \
  --min-coverage 95 \
  --min-structured-coverage 80 \
  --min-retained-coverage 100 \
  --min-reduction 30 \
  --max-preserved 5 \
  --fail-on-conflicts
```

## Custom Rules

Repository-specific instructions should become custom rules when they are repeated or important enough to encode.

Example:

```yaml
rules:
  - id: route_tenant_reads
    category: must
    patterns:
      - "route tenant reads through tenantresolver"
    positive_terms:
      - tenant
    section_hints:
      - database
    modal_hints:
      - route
    rendered: "Route tenant reads through TenantResolver."
    severity: high
    safety_critical: true
    always_select: true
```

Then run:

```bash
glyph compile README.md -o README.glp --rules glyph.rules.yml
glyph inspect README.md --rules glyph.rules.yml
```

Use suggestions as a starting point:

```bash
glyph rules suggest README.md --format yaml
```

Suggested rules are deterministic, but they should still be reviewed before being committed.
