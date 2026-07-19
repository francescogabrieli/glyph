# Behavior Evaluation

Token reduction and semantic coverage are necessary, but they are not the full evaluation target.

The practical question is:

```txt
Does the coding agent follow the same important must/deny/ask rules when using Glyph-generated instructions compared to original Markdown?
```

Glyph does not claim universal behavioral equivalence. Behavior must be measured for real agents and real repositories.

## Evaluation Target

The strongest evidence is not that a `.glp` manifest is smaller.

The strongest evidence is that an agent still:

- follows required behaviors
- avoids prohibited behaviors
- asks before approval-gated actions
- runs expected tests or explains skipped verification
- reports work clearly

## Suggested Experimental Design

### Repositories

Use multiple repositories with different instruction styles, for example:

- backend service
- frontend application
- fullstack monorepo
- security-sensitive codebase
- data pipeline repository

### Tasks

Use realistic tasks such as:

- fix failing tests
- implement a small bug fix
- update a React component
- add a migration
- adjust CI or lint configuration

### Conditions

Evaluate at least these conditions:

- `original_markdown`
- `glyph_rendered_markdown`
- `glyph_selected_markdown`
- `future_native_glp`

### Rubric

Score whether the agent:

- followed each relevant `must` rule
- violated any relevant `deny` rule
- asked before any relevant `ask` rule
- ran or explained testing and verification
- completed the task successfully

### Metrics

Track at least:

- instruction tokens
- must-rule adherence
- deny violations
- ask-rule adherence
- test compliance
- reporting compliance
- task success
- manual reviewer notes

### Manual Review

Human review is still required because many important behaviors are visible only in task transcripts, command histories, diffs, and final reports.

Useful artifacts:

- task prompt
- repository snapshot or commit
- instruction condition used
- agent transcript
- commands executed
- final diff
- reviewer notes

### Limitations

- different agents have different planning and reporting habits
- the same agent may vary run to run
- `.glp` selection may intentionally omit irrelevant context
- behavior can degrade even when semantic coverage stays high
- manual review is expensive but still necessary

## Relationship To Existing Glyph Metrics

Glyph benchmarks:

- token reduction
- semantic coverage
- operational coverage
- unresolved candidates

Behavior evaluation extends that by measuring whether actual runtime behavior stays aligned with the original instruction intent.

## Included Harness

The repository includes a non-executing evaluation skeleton under `evals/behavior/`.

It does not call external agents.

It provides structure for:

- recording runs
- storing synthetic or real result files
- documenting rubrics
- analyzing per-condition deltas
