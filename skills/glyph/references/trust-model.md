# Glyph trust model

Glyph produces a separate, deterministic semantic artifact from supported coding-agent instruction Markdown.

## What a successful run supports

A run can provide evidence that:

- the same supported input and configuration produce the same canonical manifest;
- recognized operational requirements are represented as canonical units or structured policies;
- unresolved operational directives remain visible as preserved or unmapped content;
- safety retention, retained coverage, structured coverage, and token reduction are measured separately;
- a committed manifest is fresh relative to its source when verification passes.

## What a successful run does not prove

Do not infer that:

- arbitrary Markdown was understood universally;
- every word or prose relationship was preserved;
- two different coding agents will behave identically;
- token reduction implies semantic retention;
- high structured coverage means nothing requires human review;
- a repository-specific instruction is safe to generalize into the shared parser.

## Review priorities

Pay special attention to:

- removed or weakened safety denials;
- removed approval requirements;
- testing, linting, type checking, build, and reporting requirements;
- production configuration, deployment, secrets, credentials, migrations, and destructive operations;
- preserved high-risk directives;
- unmapped repository-specific routing or ownership rules;
- semantic conflicts;
- dropped candidates, which should never be hidden.

## Source ownership

The source Markdown remains authoritative until the repository explicitly adopts the `.glp` artifact as policy. Compilation does not authorize replacing or deleting `AGENTS.md`, `CLAUDE.md`, or any other source file.

## Agent behavior

An agent using this skill must report uncertainty and incomplete validation. It must not repair ambiguous meaning by guessing. The correct fallback is to preserve, surface, and request human review.