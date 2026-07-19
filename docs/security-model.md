# Security Model

## What Glyph protects

Glyph is designed to make safety-related instructions visible, measurable, and
harder to lose during instruction-file maintenance. It is not a sandbox, a
secret scanner, an authorization system, or a proof of agent behavior.

## Trust boundaries

| Boundary | Glyph behavior |
| --- | --- |
| Source Markdown | Parsed locally. It may contain prose, code examples, commands, and safety directives. |
| Semantic output | Canonical rules, structured policies, or source-faithful preservation are emitted deterministically. |
| Ambiguous instruction | Preserved rather than structurally guessed. |
| High-risk candidate | Counted separately for retention and strict-mode gating. |
| External corpus | Evaluated from local pinned checkouts; committed reports are metadata-only. |
| MCP | Optional local stdio server; no hosted endpoint is created. |

## Safety controls

- Retention and safety retention are explicit metrics.
- Strict compilation defaults to rejecting high-risk preserved directives unless
  the user sets a different explicit threshold.
- Conflicting semantic categories fail strict mode.
- `glyph diff` flags removed safety and testing semantics as risks.
- Lockfiles expose semantic changes even when text changes appear small.
- Exact custom policies keep repository-specific interpretation reviewable.

## What remains a human decision

Glyph cannot infer authorization, validate business risk, interpret unstated
context, or guarantee that an agent obeys an instruction. A preserved directive
must be reviewed by the repository owner if it matters operationally.

## Handling sensitive material

Use synthetic examples in issues, tests, and reports. Do not put secrets,
credentials, production identifiers, or third-party confidential instructions
in a custom rule or reproduction unless you have explicit authority to do so.

For vulnerability reporting, read [SECURITY.md](../SECURITY.md).
