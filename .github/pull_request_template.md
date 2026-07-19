## Outcome

Describe the user-visible result and why this change is needed.

## Semantic boundary

Explain what operational meaning may change and what must remain invariant. For parser or classifier changes, include the sanitized deterministic shape and why it has one valid interpretation.

## Validation

List the exact commands run and their results. Explain any required check that was not run.

## Checklist

- [ ] The change is focused and does not include unrelated refactoring or features.
- [ ] Tests include positive, negative, and ambiguity coverage where parsing or classification changes.
- [ ] v0.1 compatibility and v0.2 determinism/downgrade guards remain intact where relevant.
- [ ] Documentation and generated evidence were updated through their normal workflow when behavior, commands, metrics, or public claims changed.
- [ ] No secrets, credentials, proprietary instructions, third-party source text, repository identities, or generated local artifacts were committed.
- [ ] Retention, safety, and release gates were not lowered merely to make the change pass.
- [ ] Security-sensitive details are being reported privately according to `SECURITY.md`, not disclosed in this pull request.
