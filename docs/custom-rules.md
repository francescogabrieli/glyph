# Custom Rules and Exact Policies

Glyph has two repository-owned extension mechanisms. Both are local,
version-controlled, deterministic, and evaluated before the built-in registry
or clause parser.

## Precedence

```text
exact custom policy
  → custom semantic rule
  → built-in semantic registry
  → deterministic 0.2 clause parser
  → preserve
```

Multiple incompatible exact policy matches are reported as a readable conflict.
The effective risk cannot be lower than the source candidate's classified risk.

## Custom semantic rule

Use a semantic rule for a repeated, unambiguous convention that maps to one
canonical identifier.

```yaml
rules:
  - id: use_project_query_helper
    category: must
    patterns:
      - "use the project query helper"
    positive_terms:
      - query
      - helper
    section_hints:
      - database
    modal_hints:
      - use
    rendered: "Use the project query helper."
    severity: medium
    safety_critical: false
    always_select: false
```

Use it with any relevant command:

```bash
glyph inspect AGENTS.md --rules glyph.rules.yml
glyph compile AGENTS.md -o AGENTS.glp --rules glyph.rules.yml
glyph emit AGENTS.glp --target agents-md -o AGENTS.generated.md --rules glyph.rules.yml
```

## Exact 0.2 custom policy

Use a custom policy only when a repository-specific instruction needs structured
subject, predicate, object, scope, condition, or exception semantics and has a
single human-approved interpretation.

Exact policies require `match: exact`. Matching performs Unicode NFC
normalization, outer trimming, and whitespace collapse only. It does not change
case or punctuation.

```yaml
rules:
  - id: service_data_boundary
    match: exact
    patterns:
      - "Service handlers may read the request context but must not write it."
    policy:
      category: must
      expression: '{"op":"atomic","kind":"action","subject":["service_handler"],"predicate":"read","objects":["request_context"]}'
      scope:
        - services/
      risk: medium
      tags:
        - architecture
```

The JSON expression uses the same model as `.glp 0.2`; see
[`.glp 0.2` policy architecture](glp-0.2-policy-architecture.md). Use an exact
policy for one intended policy, not as a loose pattern-matching language.

## Suggestions and review

```bash
glyph rules suggest AGENTS.md --format yaml
```

Suggestions are seeds for ordinary custom semantic rules. They intentionally do
not manufacture structured policy expressions for ambiguous source text.

Review every custom rule for false positives, category, safety risk, emitted
wording, and selection behavior. Add synthetic positive and negative tests in
the owning repository before relying on it in strict CI.
