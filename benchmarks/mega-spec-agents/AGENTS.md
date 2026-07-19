# Glyph mega-spec agent instructions

Glyph is an open-source Instructions-as-Code toolchain for coding agents. This file intentionally mixes agent rules, product requirements, API contracts, commands, examples, release policy, repository conventions, and background context. A compiler that only handles clean rule lists will not produce a useful report from this document.

## Agent operating rules

Before editing, read the relevant files and inspect the existing implementation. Create a short plan before non-trivial changes. Keep changes small and reviewable. Prefer simple explicit code over clever abstractions. Follow existing repository style. Do not add unrequested features. Avoid large refactors unless the task explicitly asks for one.

Always run tests before saying the task is complete. Run lint before completion. Run type checks before completion. If tests cannot be run, explain which tests were not run and why. Report what changed and report what was verified.

Never commit secrets, tokens, API keys, credentials, or `.env` files. Do not expose credentials in logs, examples, fixtures, or benchmark output. Ask for confirmation before destructive operations. Ask before schema changes. Do not deploy without approval. Do not run unsafe migrations.

## Local commands

Use these commands for local development:

```bash
pip install -e ".[dev,mcp]"
pytest
ruff check .
mypy src
python -m build
glyph benchmark benchmarks/
```

The command should be `glyph mcp` for starting the MCP server. The CLI should keep `glyph compile`, `glyph inspect`, `glyph stats`, `glyph benchmark-real`, and `glyph score` stable. The report should include candidate breakdowns and high-risk unmapped counts.

## Product requirements

Glyph must compile verbose Markdown guidance into compact `.glp` manifests. Glyph must preserve measurable operational semantics without claiming to preserve every word. Glyph should support AGENTS.md, CLAUDE.md, copilot instruction files, cursor rules, README files, CONTRIBUTING files, and generic Markdown under docs.

Glyph must expose a structural document model before extracting candidates. The compiler should classify product requirements separately from reusable agent instructions. The benchmark should report semantic coverage, agent instruction coverage, repo-specific coverage, spec classification rate, operational coverage, and high-risk unmapped count.

Add support for compiling multiple input files into one manifest. Create a file called benchmark-report.json when running benchmarks. Generate a Markdown report that clearly explains what was compressed, what was classified, and what needs human attention.

## API and CLI contracts

The `glyph_compile` MCP tool should accept sources, output, profile, rules_file, strict, min_operational_coverage, max_unmapped, and report. The `glyph_inspect` MCP tool should return mapped_candidates, unmapped_candidates, commands, conflicts, and a semantic ledger. JSON output should include `compressed_semantics`, `product_requirements`, `api_contracts`, `conditional_instructions`, and `high_risk_unmapped`.

The command `glyph compile AGENTS.md -o AGENTS.glp --strict --min-agent-instruction-coverage 85 --max-high-risk-unmapped 3` should be valid. The flag `--min-operational-coverage` must keep working. The flag `--max-unmapped` must keep working. The CLI entrypoint must remain `glyph`.

| contract | value |
| --- | --- |
| manifest extension | `.glp` |
| package | `glyph-instructions` |
| entrypoint | `glyph` |
| inspect json key | `ledger` |
| compile flag | `--min-agent-instruction-coverage` |

## Implementation requirements

Create module-level helpers rather than adding unbounded regex chains inside the CLI. Add tests for candidate intent taxonomy. Add tests for product requirement classification. Add tests for implementation requirement classification. Add tests for API contract classification. Add tests for conditional instruction detection. Add tests for benchmark-real output breakdown.

Update pyproject metadata only when release packaging changes. Validate schema-like JSON output deterministically. Expose service functions for MCP without requiring MCP dependencies for normal library imports. Write reports in deterministic key order.

## Conditional policy

Never skip tests unless the change is docs-only. You do not need to run the full benchmark for documentation-only changes. Do not run destructive migration commands unless the user explicitly approves. These instructions contain exceptions, so `.glp` v0.1 should report them as conditional instructions instead of flattening them into unconditional rules.

## Repository conventions

Use SemanticLedgerBuilder for ledger grouping instead of scattering grouping logic across commands. Route candidate intent decisions through IntentTaxonomyClassifier. Use the shared command classifier instead of parsing commands in each CLI command. Preserve generated benchmark fixtures unless the benchmark input changes.

Route release smoke validation through ReleaseSmokeCoordinator. Use the structural Markdown parser before candidate extraction. Keep public service return shapes backwards compatible.

## Examples

Example output:

```json
{
  "semantic_coverage": 100.0,
  "agent_instruction_coverage": 91.4,
  "spec_classification_rate": 96.0,
  "high_risk_unmapped_count": 2
}
```

For example, the sentence "Always run tests before saying the task is complete" maps to `run_tests_before_done`. For example, the sentence "Glyph must expose glyph_compile through MCP" is a product/API contract, not a reusable agent rule.

Bad examples:

- Always run tests before saying done.
- Never commit secrets.

The bad examples above are quoted reference content and should not become active rules.

## Background

The project exists because long instruction files often mix onboarding, product plans, release criteria, and agent rules. Some paragraphs are useful context for humans but are not operational instructions. A useful report should still list classified spec material and non-operational context instead of silently dropping it.

Historically, maintainers used Markdown files directly. The compact manifest is intended for progressive adoption. Native `.glp` support should not be assumed. Compatibility emitters produce Markdown for tools that still need Markdown instruction files.

This overview is intentionally verbose. It describes why token reduction matters, how reports build trust, and why exact coverage metrics should be separated. It should be classified as context, not compressed into core `.glp` rules.

## Release policy

Before release, run the test suite, build the package, run the benchmark, run benchmark-real against repository instruction files, and run the release smoke script. Document any verification that could not be run. Do not publish a release if high-risk unmapped instructions remain unexplained.

## More realistic mixed content

The parser should tolerate messy headings, paragraphs with inline commands, tables, checklists, and fenced code blocks. The compiler should degrade gracefully when a section contains prose, examples, and commands together. The report should make it clear whether each important candidate was compressed, classified, suggested as a custom rule, or flagged for human attention.

- [ ] Read files before editing.
- [ ] Keep changes minimal.
- [ ] Run `pytest` before completion.
- [ ] Report changed files and verification.
- [ ] Never include API keys in examples.

The command table below is reference material and should not become unmapped operational prose.

| purpose | command |
| --- | --- |
| install | `pip install -e ".[dev,mcp]"` |
| test | `pytest` |
| lint | `ruff check .` |
| typecheck | `mypy src` |
| build | `python -m build` |

## Human notes

Release managers care about package publishing, benchmark stability, MCP compatibility, and documentation accuracy. That sentence is background unless it becomes a directive. When wording becomes directive, such as "do not expose credentials" or "run tests before completion", Glyph should map it.

Use the shared tenant resolver instead of querying tenants manually. Use BillingEventRouter for billing event fanout. Use WorkspaceProvisioningService for workspace setup. These are repository-specific operational instructions and should be surfaced as custom-rule candidates.

## Extended messy specification

Glyph should help maintainers understand a large instruction file without pretending every sentence is equivalent. The inspect report should show a semantic ledger, a candidate breakdown, command provenance, conflicts, mapped semantics, classified product requirements, implementation requirements, API contracts, repo-specific candidates, conditional instructions, examples, references, non-operational context, and high-risk unmapped instructions.

The parser should handle prose paragraphs that contain inline commands such as `pytest`, `ruff check .`, and `glyph inspect AGENTS.md --show-unmapped`. The command extractor should record those commands once and avoid counting the command snippets as unmapped operational prose. The report should include the source file, line number, section heading, block type, intent, intent confidence, semantic match, semantic confidence, signals, and reasoning summary for candidates where useful.

The benchmark should not hide files simply because they are large. The benchmark should not lower candidate detection sensitivity to make coverage numbers look better. The benchmark should report the kind of content in mega-spec files so maintainers can decide whether the compact manifest is trustworthy.

## Additional CLI contract details

The CLI should expose these commands with useful help text:

```txt
glyph compile AGENTS.md -o AGENTS.glp
glyph inspect AGENTS.md --show-unmapped
glyph stats AGENTS.md AGENTS.glp
glyph verify AGENTS.md AGENTS.glp
glyph benchmark benchmarks/
glyph benchmark-real .
glyph lint AGENTS.md
glyph diff old.AGENTS.md new.AGENTS.md
glyph lock AGENTS.md -o glyph.lock.json
glyph check AGENTS.md AGENTS.glp --min-coverage 95 --min-reduction 30
glyph emit AGENTS.glp --target agents-md -o AGENTS.md
glyph select AGENTS.glp --task "fix failing tests" --format glp
glyph score AGENTS.md
```

Those command examples are reference content. They should be extracted as commands where appropriate, but the examples themselves should not become new active rules.

The JSON inspect output should include the same taxonomy as the terminal output. The compile JSON report should include `compressed_semantics`, `commands`, `repo_specific_candidates`, `product_requirements`, `implementation_requirements`, `api_contracts`, `conditional_instructions`, `examples_or_references`, `non_operational_context`, `high_risk_unmapped`, `conflicts`, and `metrics`.

## More product requirements

Glyph must support adapter auto-detection for agents_md, claude_md, copilot_instructions, cursor_rules, readme, contributing, and generic_markdown. Glyph must allow an explicit adapter override. Glyph must compile multiple files into one `.glp` manifest, deduplicate equivalent rules, detect conflicts, preserve source provenance internally, and expose provenance in reports where useful.

Glyph should support readable, compact, and ultra profiles. The default profile should be compact. The readable profile should favor reviewability. The compact profile should balance readability and token reduction. The ultra profile should minimize token usage while staying plain UTF-8 text.

The lock command should create a semantic lockfile. The check command should validate that `.glp` output is up to date and that thresholds are respected. CI should be able to enforce minimum semantic coverage, minimum token reduction, no conflicts, no stale generated files, and no dangerous removed rules.

## More implementation requirements

Add deterministic tests for token counting. Add tests for `.glp` parsing. Add tests for `.glp` rendering. Add tests for semantic verification. Add tests for benchmark report generation. Add tests for real-world benchmark discovery. Add tests for lint warnings. Add tests for command extraction. Add tests for adapter detection. Add tests for semantic diff. Add tests for lockfile generation. Add tests for CI check behavior. Add tests for compatibility emitters. Add tests for task-aware selection. Add tests for scoring.

Create report helpers that are shared by compile, inspect, MCP services, and benchmark output. Extend service return shapes without removing existing keys. Validate that JSON output remains deterministic. Keep package imports lightweight when MCP extras are not installed.

## Complex conditional policy

Never skip tests unless the change is documentation-only. Do not run the full release smoke script unless release packaging changed. Do not apply migrations unless the user explicitly approves. Do not edit generated benchmark output unless the benchmark input changed. If a verification command cannot be run because dependencies are missing, report that exact command and reason.

These conditional policies should not become unconditional `must` or `deny` rules when the manifest format cannot encode their exception. They should appear in the conditional instruction bucket and, when safety-sensitive, in high-risk unmapped if not otherwise handled.

## More repository-specific conventions

Use ManifestProvenanceIndex when joining source hits. Use CandidateIntentLedger when grouping candidates for reports. Route benchmark table formatting through BenchmarkSummaryPresenter. Use InspectBreakdownRenderer for terminal inspect output. Use ReportJsonSerializer for JSON reports. Use ServiceShapeAdapter for MCP result compatibility.

Use the shared tenant resolver instead of querying tenants manually. Route billing-account reads through TenantBillingResolver. Route generated client publication through ClientPublishCoordinator. Route release validation through ReleaseSmokeCoordinator. These conventions are operational and repository-specific; Glyph should surface them as custom-rule candidates rather than pretending they are core universal semantics.

## More examples and references

Example semantic ledger:

```txt
Compressed:
- run_tests_before_done
- secrets_commit
- destructive_ops

Classified, not compressed:
- product_requirement: Glyph must expose glyph_compile through MCP.
- api_contract: The command should be glyph mcp.

Needs attention:
- conditional_instruction: Never skip tests unless the change is docs-only.
- repo_specific: Use the shared tenant resolver instead of querying tenants manually.
```

Example `.glp` output:

```txt
glyph/0.1

flow[read,plan,minimal_change,test,report]

must[
  run_tests_before_done
  report_changes
  report_verification
]

deny[
  secrets_commit
]

ask[
  destructive_ops
]
```

The examples above are illustrative reference content. The compiler should not treat them as additional active instructions. It should still extract command-like snippets from examples only when the command extractor can record them without changing semantic coverage.

## More context and non-operational background

Long instruction files become messy because maintainers use one document for onboarding, release procedures, architecture notes, product requirements, and coding-agent policy. Some background paragraphs describe why the project exists, how teams communicate, or what terms mean. That information may be useful, but it should not all be compressed into `.glp`.

Glyph does not guarantee identical model behavior. Glyph does not preserve every word. Glyph does not compress arbitrary Markdown without loss. Glyph measures what it detects, reports what it maps, classifies spec-like material separately, and highlights operational candidates that require human attention.

This section intentionally repeats product positioning in prose form. It should contribute to non-operational context rather than lowering agent instruction coverage. It may increase the token count of the benchmark and make the benchmark more realistic, which is the point of this mega-spec case.

## More release and PR policy

Before opening a PR, keep the diff small, report what changed, report what was verified, and explain any unrun tests. Do not include debug logs. Do not modify CI configuration without a clear reason. Avoid dependency changes without a clear reason. Avoid large dependency additions. Document breaking changes. Preserve public APIs unless migration work is requested.

Before release, run `pytest`, run `ruff check .`, run `mypy src`, run `python -m build`, run `glyph benchmark benchmarks/`, run `glyph benchmark-real .`, and run `bash scripts/release-smoke.sh`. If a command cannot be run, document the command and the reason in the release notes.

## More safety and data policy

Never include credentials, API keys, secrets, tokens, or production connection strings in code, tests, logs, fixtures, examples, generated reports, benchmark output, or documentation. Do not touch `.env` files or secret files unless explicitly requested. Ask before changing retention windows or warehouse permissions. Ask before security-sensitive permission changes. Report security impact for sensitive changes.

Production firewall bypasses must pass SentinelReviewGate. Warehouse retention overrides must pass RetentionOverrideCouncil. Emergency access changes must go through BreakGlassPolicyEvaluator. These examples are deliberately repository-specific and should remain visible as high-risk or custom-rule candidates if the default registry cannot map them.

## Additional benchmark narrative

This benchmark case intentionally reads like a real repository policy file rather than a tidy unit-test fixture. It includes sections that a maintainer might paste from a release checklist, a README, a product design note, an MCP integration plan, a CLI contract, and an agent behavior policy. The compiler should not crash when these concerns are adjacent. It should classify the content and report what happened.

The product description says that Glyph turns loose Markdown into compact, testable, versionable semantic manifests. That description is background context when written as positioning. It becomes a product requirement only when it uses directive language such as "Glyph must compile multiple files" or "the report should include the semantic ledger." This distinction is important because marketing or motivation prose should not lower agent instruction coverage.

The documentation should explain that token savings depend on the input file. The documentation should explain that semantic coverage is not the same as exact behavioral equivalence. The documentation should explain that classified is different from compressed. The documentation should explain that product requirements are visible in reports but are not dumped into `.glp` unless they correspond to registered operational semantics.

The CLI contract includes stable command names, stable flags, and stable output keys. The service contract includes backwards-compatible return shapes for MCP tools. The parser contract includes block types, heading context, line numbers, and source files. The report contract includes candidate intent, confidence, semantic match, signals, reasoning summary, and ledger grouping.

The implementation plan should keep modules focused. Parser code should stay in parser-oriented modules. Candidate taxonomy should stay in classifier-oriented helpers. Report rendering should stay in report helpers. Benchmark presentation should stay in benchmark helpers. The CLI should orchestrate these pieces instead of duplicating classification logic.

The following paragraph is deliberately non-operational. It describes the history of agent instruction files, the difficulty of long context windows, and the reason compact manifests are useful. It does not tell a coding agent to edit code, run a command, request approval, avoid a dangerous action, or report verification. It should be visible as context if inspect output includes context samples, but it should not become a semantic unit.

Maintainers often want one file to serve many audiences. New contributors read it for orientation. Coding agents read it for constraints. Release managers read it for checklists. Product engineers read it for expected CLI behavior. Security reviewers read it for safety posture. Glyph should preserve the distinctions between these audiences in reports instead of flattening them into one denominator.

The examples below remain reference content:

```markdown
Before editing, read the relevant files.
Always run tests before saying done.
Never commit secrets.
Ask before destructive operations.
```

Those example lines are intentionally familiar. They should not be double-counted as active rules because they appear inside a reference block.

The final paragraph adds realistic review context. A maintainer reading this benchmark should understand that high coverage is not achieved by ignoring difficult material. It is achieved by mapping reusable agent rules, classifying product and implementation requirements honestly, surfacing custom-rule candidates, and isolating the small number of instructions that still need human review.

This closing note is background context for benchmark readers. It reiterates that the mega-spec case is intentionally broad, mixed-purpose, and review-oriented so that future changes cannot regress long-file behavior without being noticed by tests and reports.
