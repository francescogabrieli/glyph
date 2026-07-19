# Security Policy

## Scope

Glyph is a local developer tool. Its security-sensitive responsibilities are to
avoid silently losing safety instructions, avoid remote execution or LLM calls,
and report unresolved high-risk operational candidates clearly.

## Supported releases

Security fixes are made against the latest published release and the default
branch under active development. This repository is currently pre-1.0; users
should upgrade to the latest compatible release when a fix is announced.

## Reporting a vulnerability

Do not publish suspected vulnerabilities, secrets, private keys, tokens, or
unreleased exploit details in a public issue. Contact the maintainer through
the security contact published on the project hosting profile, with:

- a concise impact statement;
- reproduction steps or a minimal synthetic proof of concept;
- affected version and platform;
- proposed remediation if available.

Expect an acknowledgement before public disclosure is coordinated. Please do
not send third-party confidential instruction files unless they are necessary
and you have permission to share them.

## Security boundaries

- Glyph does not send source documents to a hosted service.
- Glyph does not call an LLM.
- Strict mode can reject high-risk preserved directives and conflicts.
- `preserve[]` is a safety fallback, not an assertion that a clause was fully
  interpreted.
- Generated Markdown preserves encoded semantics, not original wording.

See [Security model](docs/security-model.md) for operational detail.
