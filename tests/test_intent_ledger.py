from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from glyph.governance.benchmark import benchmark_real, run_benchmark
from glyph.governance.reports import report_to_json, report_to_markdown
from glyph.interfaces.cli import app
from glyph.pipeline.compiler import analyze_text
from glyph.semantics.custom_rules import suggest_rules
from glyph.source.candidates import extract_instruction_candidates
from glyph.source.markdown_ast import parse_markdown
from glyph.source.tokenizer import count_tokens

runner = CliRunner()


@pytest.mark.parametrize(
    ("text", "intent"),
    [
        ("Always run tests before saying the task is complete.", "testing_policy"),
        ("Never commit secrets, tokens, API keys, or credentials.", "safety_policy"),
        ("The command should be glyph mcp.", "api_contract"),
        ("Glyph must expose glyph_compile through MCP.", "api_contract"),
        ("The report should include high-risk unmapped counts.", "product_requirement"),
        ("Create module-level helpers for the semantic ledger.", "implementation_requirement"),
        ("Add tests for candidate intent taxonomy.", "implementation_requirement"),
        ("Example output:", "example_content"),
        ("This project exists to reduce token usage for agent instruction files.", "non_operational_context"),
        ("Never skip tests unless the change is docs-only.", "conditional_instruction"),
        ("Use the shared tenant resolver instead of querying tenants manually.", "repo_convention"),
        ("Before release, run the release smoke script.", "release_policy"),
        ("Run lint before completion.", "agent_instruction"),
        ("Do not deploy without approval.", "safety_policy"),
        ("The CLI should keep glyph inspect stable.", "api_contract"),
    ],
)
def test_candidate_intent_taxonomy(text: str, intent: str):
    _, report = analyze_text(f"## Spec\n{text}", "AGENTS.md")
    assert report.candidates
    assert report.candidates[0].intent == intent
    assert report.candidates[0].intent_confidence > 0
    assert report.candidates[0].reasoning_summary


def test_semantic_ledger_groups_mixed_file():
    text = """
## Rules
Always run tests before completion. Never commit secrets.

## Product
Glyph must expose glyph_compile through MCP. The report should include candidate breakdowns.

## Implementation
Create module-level helpers for ledger grouping. Add tests for API contract classification.

## Conditional
Never skip tests unless the change is docs-only.

## Repository
Use the shared tenant resolver instead of querying tenants manually.

## Background
This project exists to reduce token usage for instruction files.
"""
    manifest, report = analyze_text(text, "AGENTS.md")
    assert "run_tests_before_done" in manifest.semantic_units()
    assert report.ledger.compressed_semantics
    assert report.ledger.product_requirements
    assert report.ledger.implementation_requirements
    assert report.ledger.api_contracts
    assert report.ledger.conditional_instructions
    assert report.ledger.repo_specific_candidates
    assert report.ledger.non_operational_context


def test_product_requirements_do_not_destroy_agent_instruction_coverage():
    text = "\n".join(
        [
            "Always run tests before completion.",
            "Never commit secrets.",
            *[f"Glyph must implement product capability {idx}." for idx in range(30)],
            *[f"The CLI should support --flag-{idx}." for idx in range(10)],
        ]
    )
    _, report = analyze_text(text, "AGENTS.md")
    assert report.agent_instruction_coverage == 100.0
    assert report.spec_classification_rate == 100.0
    assert len(report.ledger.product_requirements) >= 30
    assert not report.ledger.high_risk_unmapped


def test_conditional_instruction_is_reported_not_flattened():
    manifest, report = analyze_text("Never skip tests unless the change is docs-only.", "AGENTS.md")
    assert "run_tests_before_done" not in manifest.semantic_units()
    assert report.ledger.conditional_instructions
    assert report.unmapped_operational_candidates


def test_repo_specific_candidate_is_suggestible_not_product_requirement():
    _, report = analyze_text("Use the shared tenant resolver instead of querying tenants manually.", "README.md")
    assert report.ledger.repo_specific_candidates
    assert not report.ledger.product_requirements
    suggestions = suggest_rules(report.unmapped_operational_candidates)
    assert suggestions
    assert suggestions[0]["id"].startswith("use_shared_tenant")


def test_high_risk_unmapped_detection_for_unknown_safety_policy():
    _, report = analyze_text("Production emergency changes must be approved by an undocumented safety process.", "AGENTS.md")
    assert report.high_risk_unmapped_count >= 1
    assert report.ledger.high_risk_unmapped


def test_example_blocks_do_not_become_active_rules():
    text = """## Examples

Example output:

```markdown
Always run tests before completion.
Never commit secrets.
```
"""
    manifest, report = analyze_text(text, "README.md")
    assert not manifest.semantic_units()
    assert report.ledger.examples_or_references
    assert not report.unmapped_operational_candidates


def test_command_references_are_commands_not_unmapped():
    _, report = analyze_text("## Commands\n\n| purpose | command |\n| --- | --- |\n| test | `pytest` |\n", "README.md")
    assert report.commands_detected["test"] == "pytest"
    assert not report.unmapped_operational_candidates


def test_report_json_and_markdown_include_ledger_breakdown():
    _, report = analyze_text("Glyph must expose glyph_compile through MCP. Use TenantResolver for tenant reads.", "AGENTS.md")
    payload = json.loads(report_to_json(report))
    md = report_to_markdown(report)
    assert {"structured_coverage", "retained_coverage", "safety_retention", "preserved_count", "high_risk_preserved_count", "dropped_count"} <= set(payload["metrics"])
    assert "Post-hardening metrics" in md
    assert "Compatibility diagnostics" in md
    assert "ledger" in payload
    assert "api_contracts" in payload["ledger"]
    assert "Repo-Specific Custom-Rule Candidates" in md
    assert "API Contracts" in md


def test_inspect_text_output_shows_breakdown(tmp_path: Path):
    source = tmp_path / "AGENTS.md"
    source.write_text("Always run tests before completion. Glyph must expose glyph_compile through MCP.", encoding="utf-8")
    result = runner.invoke(app, ["inspect", str(source), "--show-unmapped"])
    assert result.exit_code == 0, result.output
    assert "Agent instruction coverage" in result.output
    assert "Candidate breakdown" in result.output
    assert "Classified product/spec/API requirements" in result.output


def test_inspect_json_output_includes_taxonomy(tmp_path: Path):
    source = tmp_path / "AGENTS.md"
    source.write_text("Glyph must expose glyph_compile through MCP.", encoding="utf-8")
    result = runner.invoke(app, ["inspect", str(source), "--format", "json"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["ledger"]["api_contracts"]
    assert payload["candidates"][0]["intent"] == "api_contract"


def test_strict_mode_allows_large_classified_product_spec(tmp_path: Path):
    source = tmp_path / "AGENTS.md"
    out = tmp_path / "AGENTS.glp"
    source.write_text(
        "Never commit secrets. Always run tests before completion.\n"
        + "\n".join(f"Glyph must implement capability {idx}." for idx in range(20)),
        encoding="utf-8",
    )
    result = runner.invoke(app, ["compile", str(source), "-o", str(out), "--strict", "--min-agent-instruction-coverage", "85", "--max-high-risk-unmapped", "0"])
    assert result.exit_code == 0, result.output


def test_strict_mode_fails_on_high_risk_unmapped(tmp_path: Path):
    source = tmp_path / "AGENTS.md"
    out = tmp_path / "AGENTS.glp"
    source.write_text("Never commit secrets. Production emergency changes must be approved by an undocumented safety process.", encoding="utf-8")
    result = runner.invoke(app, ["compile", str(source), "-o", str(out), "--strict", "--max-high-risk-unmapped", "0"])
    assert result.exit_code != 0
    assert "high-risk unmapped" in result.output


def test_benchmark_real_output_breakdown(tmp_path: Path):
    source = tmp_path / "AGENTS.md"
    source.write_text("Always run tests before completion. Glyph must expose glyph_compile through MCP.", encoding="utf-8")
    result = benchmark_real(tmp_path)
    row = result["files"][0]
    assert "agent_instruction_coverage" in row
    assert {"structured_coverage", "retained_coverage", "safety_retention", "preserved_count", "high_risk_preserved_count", "dropped_count"} <= set(row)
    assert "spec_classification_rate" in row
    assert "candidate_breakdown" in row
    assert result["average_spec_classification_rate"] == 1.0
    assert {"preserved_count", "high_risk_preserved_count", "dropped_count"} <= set(result)


def test_mega_spec_benchmark_case_is_large_enough_and_interpretable():
    path = Path("benchmarks/mega-spec-agents/AGENTS.md")
    tokens, _ = count_tokens(path.read_text(encoding="utf-8"))
    assert tokens >= 1500
    _, report = analyze_text(path.read_text(encoding="utf-8"), str(path))
    assert report.agent_instruction_coverage >= 85
    assert report.spec_classification_rate >= 90
    assert report.high_risk_unmapped_count <= 5
    assert report.ledger.product_requirements
    assert report.ledger.api_contracts
    assert report.ledger.repo_specific_candidates


def test_benchmark_includes_mega_spec_case():
    result = run_benchmark(Path("benchmarks"), write_reports=False)
    cases = {case["case"]: case for case in result["cases"]}
    assert "mega-spec-agents" in cases
    assert cases["mega-spec-agents"]["agent_instruction_coverage"] >= 0.85
    assert cases["mega-spec-agents"]["spec_classification_rate"] >= 0.9


def test_low_level_extractor_still_filters_context_by_default():
    doc = parse_markdown("## Background\nThis project exists to reduce token usage.", "README.md")
    assert extract_instruction_candidates(doc) == []
    assert extract_instruction_candidates(doc, include_classified=True)[0].intent == "non_operational_context"
