from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from glyph.governance.reports import report_to_json, report_to_markdown
from glyph.interfaces.cli import app
from glyph.pipeline.compiler import analyze_files, analyze_text, compile_text
from glyph.semantics.classifier import classify_commands
from glyph.semantics.custom_rules import load_custom_rules, suggest_rules
from glyph.source.candidates import extract_command_candidates, extract_instruction_candidates
from glyph.source.markdown_ast import parse_markdown

runner = CliRunner()


STRUCTURAL_MD = """
# Root

Paragraph with `pytest`.

## Testing

- [ ] Before opening a PR, make sure the suite is green.
- Run lint before done.
1. Run type checks before completion.

| purpose | command |
| --- | --- |
| tests | `pytest` |

> Ask before destructive operations.

```bash
ruff check .
```

---
"""


@pytest.mark.parametrize(
    ("block_type", "expected"),
    [
        ("heading", True),
        ("paragraph", True),
        ("bullet_list", True),
        ("numbered_list", True),
        ("checklist", True),
        ("fenced_code_block", True),
        ("inline_code", True),
        ("table", True),
        ("blockquote", True),
        ("horizontal_rule", True),
    ],
)
def test_markdown_structural_parser_block_types(block_type: str, expected: bool):
    doc = parse_markdown(STRUCTURAL_MD, "AGENTS.md")
    assert (block_type in {block.type for block in doc.blocks}) is expected


def test_document_ir_heading_hierarchy():
    doc = parse_markdown("# A\n\n## B\nText\n### C\nMore", "README.md")
    assert [section.title for section in doc.sections] == ["A", "B", "C"]
    assert doc.sections[2].parent_titles == ["A", "B"]


def test_soft_wrapped_list_item_remains_one_candidate_clause():
    text = (
        "## Rules\n"
        "- Do not include credentials in\n"
        "  generated output.\n"
        "- Keep audit records available.\n"
    )
    manifest, report = analyze_text(text, "AGENTS.md")

    operational_texts = [candidate.text for candidate in report.ledger.operational_candidates]
    assert operational_texts == [
        "Do not include credentials in generated output.",
        "Keep audit records available.",
    ]
    assert report.retained_coverage == 100.0
    assert report.safety_retention == 100.0
    assert not manifest.preserved


def test_bold_markdown_modals_and_labels_are_normalized_before_policy_parsing():
    text = (
        "## Rules\n"
        "- User communication**: Always respond in the requested language.\n"
        "- Do **not** hardcode sensitive sample values.\n"
    )
    manifest, report = analyze_text(text, "AGENTS.md")

    assert report.structured_coverage == 100.0
    assert not manifest.preserved
    assert any(policy.expression and policy.expression.predicate == "respond" for policy in manifest.policies)
    assert any(policy.expression and "hardcode" in policy.expression.terms() for policy in manifest.policies)


def test_fenced_code_block_extraction():
    doc = parse_markdown("## Lint\n```bash\nruff check .\n```", "AGENTS.md")
    commands = classify_commands(extract_command_candidates(doc))
    assert commands[0].command == "ruff check ."
    assert commands[0].label == "lint"


def test_inline_command_extraction():
    doc = parse_markdown("Run `npm test` before completion.", "README.md")
    commands = classify_commands(extract_command_candidates(doc))
    assert commands[0].label == "test"


def test_markdown_table_command_extraction():
    doc = parse_markdown("| purpose | command |\n| --- | --- |\n| typecheck | `mypy src` |", "README.md")
    commands = classify_commands(extract_command_candidates(doc))
    assert commands[0].label == "typecheck"


@pytest.mark.parametrize(
    "markdown",
    [
        "- Always run tests before completion.",
        "1. Before opening a PR, make sure the suite is green.",
        "- [ ] Run lint before done.",
        "Never commit secrets or API keys.",
        "> Ask before destructive operations.",
    ],
)
def test_candidate_extraction_from_shapes(markdown: str):
    doc = parse_markdown(markdown, "AGENTS.md")
    assert extract_instruction_candidates(doc)


@pytest.mark.parametrize(
    ("text", "unit"),
    [
        ("Before opening a PR, make sure the suite is green.", "run_tests_before_done"),
        ("Avoid touching unrelated packages while fixing a bug.", "small_reviewable_changes"),
        ("Keep the PR focused and avoid broad rewrites.", "no_large_refactors"),
        ("Never include credentials, API keys, or tokens in code, tests, logs, fixtures, or examples.", "api_key_exposure"),
        ("Do not add unrequested features.", "no_unrequested_features"),
        ("Follow existing repository conventions.", "follow_existing_style"),
        ("If tests cannot be run, explain unrun tests.", "explain_unrun_tests"),
        ("Report what changed and report what was verified.", "report_changes"),
        ("Ask before security-sensitive permission changes.", "security_sensitive_changes"),
        ("Do not deploy without approval.", "deploy_without_approval"),
        ("Ask before schema changes.", "schema_changes"),
        ("Do not run unsafe migrations.", "unsafe_migrations"),
    ],
)
def test_classification_synonyms_and_context(text: str, unit: str):
    manifest = compile_text(f"## Pull requests\n{text}", "AGENTS.md")
    assert unit in manifest.semantic_units()


def test_promptfoo_cache_permission_wording_is_structurally_protected():
    source = (
        "## Debugging & Troubleshooting\n"
        "**NEVER delete or clear the cache without explicit permission.** "
        "Use `--no-cache` flag instead.\n"
    )
    manifest, report = analyze_text(source, "AGENTS.md")

    assert "cache_clear_permission" in manifest.ask
    assert not any("delete or clear the cache" in item.text for item in report.unmapped_operational_candidates)


def test_terse_deleting_files_bullet_under_ask_first_maps_destructive_ops():
    manifest = compile_text(
        "### Ask first\n- Schema changes\n- Deleting files\n",
        "AGENTS.md",
    )

    assert "destructive_ops" in manifest.ask
    assert "schema_changes" in manifest.ask


def test_confidence_scores_and_signals_are_explainable():
    _, report = analyze_text("## Pull requests\nBefore opening a PR, make sure the suite is green.", "AGENTS.md")
    match = next(match for match in report.matches if match.semantic_unit == "run_tests_before_done")
    assert 0.0 <= match.confidence <= 1.0
    assert match.signals


def test_unmapped_operational_candidates_are_reported():
    _, report = analyze_text("## Database\nRoute tenant reads through TenantResolver.", "README.md")
    assert report.unmapped_operational_candidates
    candidate = report.unmapped_operational_candidates[0]
    assert candidate.line == 2
    assert "modal:route" in candidate.reasons


def test_custom_rules_map_previous_unmapped_candidate(tmp_path: Path):
    rules = tmp_path / "glyph.rules.yml"
    rules.write_text(
        """rules:
  - id: use_tenant_resolver
    category: must
    patterns:
      - "route tenant reads through tenantresolver"
    rendered: "Route tenant reads through TenantResolver."
""",
        encoding="utf-8",
    )
    manifest, report = analyze_text("## Database\nRoute tenant reads through TenantResolver.", "README.md", rules_path=rules)
    assert "use_tenant_resolver" in manifest.must
    assert not report.unmapped_operational_candidates


def test_custom_rules_loading_readable_errors(tmp_path: Path):
    rules = tmp_path / "glyph.rules.yml"
    rules.write_text("rules:\n  - category: must\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_custom_rules(rules)


def test_rule_suggestions_are_deterministic():
    _, report = analyze_text("Route tenant reads through TenantResolver.", "README.md")
    first = suggest_rules(report.unmapped_operational_candidates)
    second = suggest_rules(report.unmapped_operational_candidates)
    assert first == second
    assert first[0]["id"].startswith("route_tenant_reads")


def test_conflict_detection_in_report():
    _, report = analyze_text("Always run tests before completion. Do not run tests unless explicitly asked.", "AGENTS.md")
    assert any(conflict.id == "testing_required_and_skipped" for conflict in report.conflicts)


def test_compile_json_and_markdown_reports(tmp_path: Path):
    md = tmp_path / "AGENTS.md"
    md.write_text("Always run tests before completion. `pytest`", encoding="utf-8")
    manifest, report = analyze_files([md])
    json_text = report_to_json(report)
    md_text = report_to_markdown(report)
    assert json.loads(json_text)["input_files"] == [str(md)]
    assert "# Glyph compile report" in md_text
    assert "run_tests_before_done" in manifest.must


def test_cli_compile_report_and_strict(tmp_path: Path):
    source = tmp_path / "AGENTS.md"
    out = tmp_path / "AGENTS.glp"
    report = tmp_path / "report.json"
    source.write_text("Never commit secrets. Always run tests before completion. Report what changed. `pytest`", encoding="utf-8")
    result = runner.invoke(app, ["compile", str(source), "-o", str(out), "--report", str(report), "--strict", "--min-operational-coverage", "50", "--max-unmapped", "2"])
    assert result.exit_code == 0, result.output
    assert out.exists()
    assert report.exists()


def test_cli_strict_accepts_structured_repository_policy(tmp_path: Path):
    source = tmp_path / "README.md"
    out = tmp_path / "README.glp"
    source.write_text("Route tenant reads through TenantResolver.", encoding="utf-8")
    result = runner.invoke(app, ["compile", str(source), "-o", str(out), "--strict", "--max-unmapped", "0"])
    assert result.exit_code == 0, result.output
    assert out.exists()


def test_cli_inspect_text_and_json(tmp_path: Path):
    source = tmp_path / "AGENTS.md"
    source.write_text("## Testing\nBefore opening a PR, make sure the suite is green. `pytest`", encoding="utf-8")
    text = runner.invoke(app, ["inspect", str(source), "--show-unmapped"])
    js = runner.invoke(app, ["inspect", str(source), "--format", "json"])
    assert text.exit_code == 0
    assert "Glyph inspect" in text.output
    assert js.exit_code == 0
    assert "run_tests_before_done" in js.output


def test_cli_rules_suggest_text_and_yaml(tmp_path: Path):
    source = tmp_path / "README.md"
    source.write_text("Route tenant reads through TenantResolver.", encoding="utf-8")
    text = runner.invoke(app, ["rules", "suggest", str(source)])
    yaml = runner.invoke(app, ["rules", "suggest", str(source), "--format", "yaml"])
    assert text.exit_code == 0
    assert "Potential custom rules" in text.output
    assert "rules:" in yaml.output


@pytest.mark.parametrize(
    "filename",
    ["AGENTS.md", "CLAUDE.md", "README.md", "CONTRIBUTING.md", ".github/copilot-instructions.md", ".cursor/rules/project.mdc"],
)
def test_realistic_file_family_compilation(tmp_path: Path, filename: str):
    path = tmp_path / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("Read relevant files before editing. Before opening a PR, make sure the suite is green. Never commit secrets. `pytest`", encoding="utf-8")
    manifest, report = analyze_files([path])
    assert "run_tests_before_done" in manifest.must
    assert report.operational_coverage >= 50


@pytest.mark.parametrize(
    "text",
    [
        "# Messy\nrandom\n- [x] before marking work done execute the test suite\n`pytest`",
        "Completion criteria:\n- tests pass\n- report verification",
        "Security notes: never include tokens in examples.",
        "Pull requests must stay focused and avoid broad rewrites.",
        "Local development uses `uvicorn app.main:app --reload`.",
    ],
)
def test_messy_markdown_robustness(text: str):
    manifest, report = analyze_text(text, "AGENTS.md")
    assert manifest.semantic_units() or manifest.commands or report.unmapped_operational_candidates


def test_short_file_overhead_behavior():
    manifest, report = analyze_text("Run tests. `pytest`", "AGENTS.md")
    assert report.markdown_tokens > 0
    assert report.glp_tokens > 0
    assert "test" in manifest.commands


def test_large_file_reduction_behavior():
    text = ("Always run tests before completion. Never commit secrets. Ask before destructive operations. Report what changed. `pytest`\n" * 80)
    _, report = analyze_text(text, "AGENTS.md")
    assert report.token_reduction > 0


def test_benchmark_supports_non_agents_filenames():
    from glyph.governance.benchmark import run_benchmark

    result = run_benchmark(Path("benchmarks"))
    cases = {case["case"] for case in result["cases"]}
    assert {"claude-code", "copilot-instructions", "cursor-rules", "readme-dev-section", "contributing-pr-workflow"} <= cases
    assert all("operational_coverage" in case for case in result["cases"])
