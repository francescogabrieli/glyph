# Glyph Documentation

Glyph is an Instructions-as-Code toolchain for coding-agent guidance. It compiles
measurable operational semantics from Markdown into deterministic `.glp`
manifests, while keeping uncertain meaning visible instead of pretending to
understand it.

## Start here

- [Getting started](getting-started.md) — install Glyph, compile a first file,
  and add a CI check.
- [Adoption guide](adoption-guide.md) — introduce Glyph into an existing
  repository without replacing existing agent-tool Markdown files.
- [CLI reference](cli-reference.md) — every public command and its intended
  use.
- [`.glp` specification](glp-spec.md) — readable format, versions, and
  conformance fixtures.

## Product and architecture

- [Architecture](architecture.md) — component boundaries and data flow.
- [Semantic extraction engine](semantic-extraction-engine.md) — deterministic
  extraction and preservation pipeline.
- [Semantic equivalence](semantic-equivalence.md) — what Glyph measures and
  what it deliberately does not claim.
- [`.glp 0.2` policy architecture](glp-0.2-policy-architecture.md) — structured
  predicates, conditions, exceptions, and inseparable policy linkage.
- [Glossary](glossary.md) — shared terminology for users and maintainers.

## Configure and integrate

- [Configuration](configuration.md) — `.glyph/config.toml`, profiles, and
  defaults.
- [Custom rules](custom-rules.md) — reusable semantic rules and exact 0.2
  repository policies.
- [CI and lockfiles](ci-cd.md) — strict compilation, freshness, safety gates,
  and semantic locks.
- [Compatibility](compatibility.md) — Markdown fallbacks and v0.1/v0.2
  boundaries.
- [MCP server](mcp.md) — local Model Context Protocol integration.
- [Native agent support](native-agent-support.md) — progressive integration
  model for agent-tool maintainers.
- [Agent maintainer proposal](agent-maintainer-proposal.md) — concise adoption
  proposal for ecosystem maintainers.

## Quality, security, and evidence

- [No silent semantic loss](no-silent-semantic-loss.md) — retention model and
  conservative fallback.
- [Security model](security-model.md) — local-only operation, safe defaults,
  and reporting boundaries.
- [Instruction smells](instruction-smells.md) — lint diagnostics and remedies.
- [Benchmark methodology](benchmark-methodology.md) — reproducible token and
  retention measurement.
- [External corpus harness](../corpus/README.md) — metadata-only static
  evaluation.
- [Static-gate report](release-candidate-v0.2-static-gate-report.md) — current
  fixed-corpus validation result.
- [Behavior evaluation](behavior-evaluation.md) — separately governed
  methodology; it is not part of routine static validation.

## Maintain Glyph

- [Development guide](development.md) — local environment and repository map.
- [Testing guide](testing.md) — test layers and validation commands.
- [Contribution guide](../CONTRIBUTING.md) — issue, change, and review process.
- [Release process](release-process.md) — artifact, validation, and publishing
  checklist.
- [v0.2.0 release notes](release-notes-v0.2.0.md) — compatibility, validation
  evidence, known limits, and the publication boundary for the first public
  alpha candidate.
- [Troubleshooting](troubleshooting.md) — common installation, parsing, and CI
  failures.
- [FAQ](faq.md) — concise product and operational answers.
- [Roadmap](roadmap.md) — current scope and decision rules for future work.

## Historical and exploratory records

- [Launch plan](launch-plan.md) and [release checklist](release-checklist.md)
  contain operational launch material.
- [External preserved clusters](external-corpus-preserved-clusters-v0.1.md),
  [policy-template assessment](policy-template-remediation-v0.1.md), and the
  [v0.1.0 hardening report](release-candidate-v0.1.0-hardening-report.md)
  retain earlier audit evidence.
- [v0.1.0 release-candidate validation](release-candidate-v0.1.0.md) records
  the earlier release-candidate boundary.

Historical audits and release-candidate reports are retained in this directory
as evidence. They describe the state at the time of their run; current product
guidance is linked above.
