# Glossary

| Term | Meaning |
| --- | --- |
| Adapter | Source-format hint such as `agents_md`, `claude_md`, `copilot_instructions`, `cursor_rules`, `readme`, or `contributing`. |
| Candidate | A source span considered for operational semantic extraction. |
| Canonical rule | A built-in or custom semantic identifier such as `run_tests_before_done`. |
| Clause parser | The deterministic 0.2 parser that emits a policy only when one decomposition is valid. |
| Condition / exception | A structured expression attached to a policy or expression node. |
| Content-derived ID | Deterministic identifier calculated from canonical semantic payload. |
| Expression | 0.2 recursive policy model: `atomic`, `all`, `any`, or `not`. |
| High-risk preserved | A safety-sensitive directive retained rather than structured; usually a strict CI failure. |
| Manifest | A versioned `.glp` document containing canonical rules, policies, commands, and preservation. |
| Operational candidate | A candidate that instructs a coding agent rather than merely describing a product or document. |
| Policy atom | A structured policy statement with category, expression, scope, attachments, risk, and tags. |
| Preserve | Source-faithful fallback for operational text that cannot be safely structured. |
| Provenance | Source file, line, and text evidence attached to emitted semantic output. |
| Retention | Fraction of operational candidates encoded or preserved, measured separately from compression. |
| Scope | Repository or code-area constraint; it is not the governed subject. |
| Structured coverage | Fraction of operational candidates represented as a canonical rule or structured policy. |
