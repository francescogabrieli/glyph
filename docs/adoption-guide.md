# Adoption Guide

Glyph is designed for progressive adoption. Start by measuring one file; do
not replace every instruction document in a repository on day one.

## Phase 1: Observe

Choose an established instruction file and inspect it without changing source:

```bash
glyph inspect AGENTS.md --show-unmapped
glyph lint AGENTS.md
glyph score AGENTS.md
```

Discuss what should be a reusable agent instruction, a repository convention,
or explanatory material. Preservation is an expected outcome during this phase.

## Phase 2: Compile and review

```bash
glyph compile AGENTS.md -o AGENTS.glp --report glyph-report.md
glyph render AGENTS.glp -o AGENTS.rendered.md
glyph diff AGENTS.md AGENTS.glp
```

Review the report and rendered fallback with code owners. Look especially at
safety directives, test requirements, approval rules, and preserved clauses.

## Phase 3: Encode local conventions

Add custom semantic rules for stable repository conventions. Use an exact
custom policy only when the source wording has one approved 0.2 decomposition.
Keep ambiguous clauses visible as preservation rather than teaching Glyph a
guess.

## Phase 4: Add CI

Begin with retention and high-risk safety gates, then introduce a structured
coverage target after collecting your own baseline. Add a semantic lockfile once
the generated manifest has been reviewed. See [CI and lockfiles](ci-cd.md).

## Phase 5: Adopt generated Markdown where useful

Use `glyph emit` for existing tools that consume Markdown. Keep `.glp` as a
reviewed semantic source of truth only when the team has agreed on ownership
and regeneration policy.

## Multi-file repositories

Compile related files together when they form one instruction set:

```bash
glyph compile AGENTS.md CONTRIBUTING.md docs/development.md -o AGENTS.glp
```

Glyph deduplicates equivalent semantics, retains source provenance, and reports
conflicts. It does not infer that every README paragraph is an agent rule.

## When not to structure a directive

Keep text preserved or use a human-reviewed exact policy when it depends on
unstated context, a pronoun with uncertain referent, multiple possible condition
attachments, temporal ordering, or repository-specific behavior. This is the
main protection against semantic overreach.
