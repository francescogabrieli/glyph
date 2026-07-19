from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from glyph.formats.renderer import render_glp, render_markdown
from glyph.governance.benchmark import run_benchmark
from glyph.governance.check import check_pair
from glyph.governance.emit import emit_markdown
from glyph.governance.score import score_path
from glyph.governance.select import select_manifest
from glyph.interfaces.cli import app
from glyph.pipeline.compiler import analyze_text, compile_files
from glyph.semantics.custom_rules import load_custom_rules
from glyph.source.candidates import extract_instruction_candidates
from glyph.source.markdown_ast import parse_markdown


runner = CliRunner()


def test_public_contribution_templates_are_present_and_route_security_privately():
    issue_template_root = Path(".github/ISSUE_TEMPLATE")
    expected_forms = {
        "extraction-bug.yml",
        "preserved-directive.yml",
        "adapter-request.yml",
        "custom-policy.yml",
    }

    assert expected_forms <= {path.name for path in issue_template_root.glob("*.yml")}
    config = (issue_template_root / "config.yml").read_text(encoding="utf-8")
    assert "blank_issues_enabled: false" in config
    assert "SECURITY.md" in config
    assert "do not include secrets" in config

    pull_request_template = Path(".github/pull_request_template.md").read_text(encoding="utf-8")
    assert "Semantic boundary" in pull_request_template
    assert "positive, negative, and ambiguity coverage" in pull_request_template
    assert "third-party source text" in pull_request_template
    assert "SECURITY.md" in pull_request_template


def test_release_smoke_uses_a_fresh_wheel_environment():
    script = Path("scripts/release-smoke.sh").read_text(encoding="utf-8")

    assert "mktemp -d" in script
    assert '[[ -x "$ROOT/.venv/bin/python" ]]' in script
    assert 'command -v python' in script
    assert 'PYTHON_BIN="python3"' in script
    assert '"$PYTHON_BIN" -m build --outdir "$BUILD_OUTPUT"' in script
    assert 'rm -rf "$BUILD_OUTPUT" "$SMOKE_VENV"' in script
    assert "trap cleanup EXIT" in script
    assert '"$PYTHON_BIN" -m venv "$SMOKE_VENV"' in script
    assert 'python -m pip install "$BUILD_OUTPUT"/*.whl' in script
    assert "pip install dist/*.whl" not in script
    assert "python -m venv /tmp/glyph-smoke-venv" not in script


@pytest.mark.parametrize(
    ("text", "unit"),
    [
        ("Use existing shared helpers before adding utilities.", "use_existing_helpers"),
        ("Prefer existing patterns for services.", "prefer_existing_patterns"),
        ("Do not edit generated files manually.", "avoid_generated_files"),
        ("Do not change lockfiles without a dependency reason.", "do_not_edit_lockfiles_unless_needed"),
        ("Update docs when behavior changes.", "update_docs_when_behavior_changes"),
        ("Preserve public APIs unless migration work is requested.", "preserve_public_api"),
        ("Avoid unrelated packages.", "avoid_unrelated_packages"),
        ("Keep the PR focused.", "keep_pr_focused"),
        ("Preserve accessibility behavior.", "preserve_accessibility"),
        ("Validate database migrations before completion.", "validate_database_migrations"),
        ("Use the shared database helper rather than opening raw connections.", "use_existing_helpers"),
        ("Do not open raw database connections.", "avoid_raw_database_connections"),
        ("Document breaking changes.", "document_breaking_changes"),
        ("Avoid dependency changes without a clear reason.", "avoid_dependency_changes_without_reason"),
        ("Do not modify CI configuration without a clear reason.", "do_not_modify_ci_without_reason"),
        ("Respect package boundaries and ask before crossing ownership boundaries.", "respect_package_boundaries"),
        ("Verify the build before completion.", "verify_build_before_done"),
        ("Avoid large dependency additions.", "avoid_large_dependency_additions"),
        ("Do not commit debug logs.", "do_not_commit_debug_logs"),
        ("Do not touch `.env` files or secret files unless explicitly requested.", "avoid_touching_secrets_or_env_files"),
        ("Report security impact for sensitive changes.", "report_security_impact"),
        ("Report the partition range, source dataset, target dataset, expected volume, and rollback approach.", "report_data_change_impact"),
        ("Ask before changing retention windows or warehouse permissions.", "data_retention_changes"),
        ("Keep service boundaries clear.", "preserve_service_boundaries"),
    ],
)
def test_launch_semantic_rules_map_realistic_wording(text: str, unit: str):
    manifest = analyze_text(f"## Workflow\n{text}", "AGENTS.md")[0]
    assert unit in manifest.semantic_units()


@pytest.mark.parametrize(
    "text",
    [
        "This project was created to simplify local development.",
        "FastAPI is a modern web framework for building APIs.",
        "The frontend is organized around reusable components.",
        "This section explains how the pipeline works.",
        "Thanks for contributing.",
        "A reader may learn how tenants fit together before finding commands.",
        "If local setup fails, check that Docker is running.",
        "Those sections are valuable for humans, but Glyph should only compact operational instructions.",
    ],
)
def test_false_positive_filtering_ignores_contextual_prose(text: str):
    doc = parse_markdown(f"## Context\n{text}", "README.md")
    assert extract_instruction_candidates(doc) == []


@pytest.mark.parametrize(
    "text",
    [
        "Run pytest before opening a PR.",
        "Do not commit API keys.",
        "Use the shared database helper.",
        "Keep changes focused and avoid broad refactors.",
        "Update docs when behavior changes.",
    ],
)
def test_operational_examples_still_count(text: str):
    doc = parse_markdown(f"## Rules\n{text}", "AGENTS.md")
    assert extract_instruction_candidates(doc)


def test_command_table_rows_are_commands_not_unmapped_candidates():
    _, report = analyze_text(
        """
## Commands

| label | command |
| --- | --- |
| tests | `pytest` |
| build | `npm run build` |
""",
        "README.md",
    )
    assert report.commands_detected["test"] == "pytest"
    assert report.commands_detected["build"] == "npm run build"
    assert not report.unmapped_operational_candidates


def test_custom_rule_full_metadata_render_emit_inspect_and_coverage(tmp_path: Path):
    source = tmp_path / "README.md"
    source.write_text("## Database\nRoute tenant reads through TenantResolver.", encoding="utf-8")
    plain_manifest, plain_report = analyze_text(source.read_text(), str(source))
    assert "route_tenant_reads" not in plain_manifest.semantic_units()
    assert plain_report.unmapped_operational_candidates

    rules = tmp_path / "glyph.rules.yml"
    rules.write_text(
        """rules:
  - id: route_tenant_reads
    category: must
    patterns:
      - "route tenant reads through tenantresolver"
    positive_terms:
      - "tenant"
    section_hints:
      - "database"
    modal_hints:
      - "route"
    rendered: "Route tenant reads through TenantResolver."
    severity: high
    safety_critical: true
    always_select: true
""",
        encoding="utf-8",
    )
    custom_rules = load_custom_rules(rules)
    manifest, report = analyze_text(source.read_text(), str(source), rules_path=rules)
    assert "route_tenant_reads" in manifest.must
    assert not report.unmapped_operational_candidates
    assert report.operational_coverage == 100.0

    glp = tmp_path / "README.glp"
    glp.write_text(render_glp(manifest), encoding="utf-8")
    assert "route_tenant_reads" in glp.read_text(encoding="utf-8")
    assert "Route tenant reads through TenantResolver." in render_markdown(manifest, extra_rules=custom_rules)
    assert "Route tenant reads through TenantResolver." in emit_markdown(manifest, "agents-md", custom_rules)
    selected = select_manifest(manifest, "fix tenant bug")
    assert "route_tenant_reads" in selected.must

    result = runner.invoke(app, ["inspect", str(source), "--rules", str(rules)])
    assert result.exit_code == 0, result.output
    assert "route_tenant_reads" in result.output


def test_rules_suggest_outputs_extended_metadata(tmp_path: Path):
    source = tmp_path / "README.md"
    source.write_text("## Database\nRoute tenant reads through TenantResolver.", encoding="utf-8")
    result = runner.invoke(app, ["rules", "suggest", str(source), "--format", "yaml"])
    assert result.exit_code == 0, result.output
    assert "positive_terms:" in result.output
    assert "section_hints:" in result.output
    assert "always_select:" in result.output
    assert "policy:" not in result.output


def test_inspect_text_summary_and_json_shape(tmp_path: Path):
    source = tmp_path / "AGENTS.md"
    source.write_text("## Testing\nBefore opening a PR, make sure the suite is green. `pytest`", encoding="utf-8")
    text = runner.invoke(app, ["inspect", str(source), "--show-unmapped"])
    assert text.exit_code == 0, text.output
    assert "Summary" in text.output
    assert "Operational coverage" in text.output
    assert "signals:" in text.output

    js = runner.invoke(app, ["inspect", str(source), "--format", "json"])
    payload = json.loads(js.output)
    assert payload["operational_coverage"] == 100.0
    assert payload["matches"][0]["semantic_unit"]


def test_benchmark_report_json_shape_and_markdown_content():
    result = run_benchmark(Path("benchmarks"))
    assert result["summary"]["cases"] >= 10
    assert result["summary"]["average_operational_coverage"] >= 80
    assert "average_reduction_by_profile" in result["summary"]
    assert {"preserved_count", "high_risk_preserved_count", "dropped_count"} <= set(result["summary"])
    first = result["cases"][0]
    assert {"structured_coverage", "retained_coverage", "safety_retention", "preserved_count", "high_risk_preserved_count", "dropped_count"} <= set(first)
    assert "source" in first
    assert set(first["profiles"]) == {"readable", "compact", "ultra"}
    markdown = Path("benchmarks/benchmark-report.md").read_text(encoding="utf-8")
    assert "Average Reduction By Profile" in markdown
    assert "Top Unmapped Categories" in markdown
    assert "Per-case Notes" in markdown


def test_benchmark_non_agents_sources_are_displayed():
    result = run_benchmark(Path("benchmarks"))
    sources = {case["name"]: case["source"] for case in result["cases"]}
    assert sources["claude-code"] == "CLAUDE.md"
    assert sources["copilot-instructions"] == ".github/copilot-instructions.md"
    assert sources["cursor-rules"] == ".cursor/rules/project.mdc"
    assert sources["readme-dev-section"] == "README.md"
    assert sources["contributing-pr-workflow"] == "CONTRIBUTING.md"


def test_check_pair_operational_coverage_and_max_unmapped(tmp_path: Path):
    md = tmp_path / "AGENTS.md"
    md.write_text("Always run tests before completion. Never commit secrets. `pytest`", encoding="utf-8")
    glp = tmp_path / "AGENTS.glp"
    glp.write_text(render_glp(compile_files([md])), encoding="utf-8")
    ok, errors = check_pair(md, glp, min_coverage=90, min_reduction=-999, min_operational_coverage=90, max_unmapped=0)
    assert ok, errors

    md.write_text("Always run tests before completion. Route tenant reads through TenantResolver. `pytest`", encoding="utf-8")
    glp.write_text(render_glp(compile_files([md])), encoding="utf-8")
    ok, errors = check_pair(md, glp, min_coverage=0, min_reduction=-999, min_operational_coverage=100, max_unmapped=0)
    # Repository-specific directives now compile to structured policy atoms;
    # --min-operational-coverage is retained as the structured-coverage alias.
    assert ok, errors


def test_check_pair_detects_dangerous_removed_rules(tmp_path: Path):
    md = tmp_path / "AGENTS.md"
    md.write_text("Never commit secrets. Ask before destructive operations. `pytest`", encoding="utf-8")
    glp = tmp_path / "AGENTS.glp"
    glp.write_text("glyph/0.1\nmust[run_tests_before_done]\n", encoding="utf-8")
    ok, errors = check_pair(md, glp, min_coverage=0, min_reduction=-100)
    assert not ok
    assert any("dangerous safety rules" in error for error in errors)


def test_cli_check_supports_operational_thresholds(tmp_path: Path):
    md = tmp_path / "AGENTS.md"
    md.write_text("Always run tests before completion. Never commit secrets. `pytest`", encoding="utf-8")
    glp = tmp_path / "AGENTS.glp"
    glp.write_text(render_glp(compile_files([md])), encoding="utf-8")
    result = runner.invoke(
        app,
        [
            "check",
            str(md),
            str(glp),
            "--min-coverage",
            "90",
            "--min-operational-coverage",
            "90",
            "--min-reduction",
            "-999",
            "--max-unmapped",
            "0",
            "--fail-on-conflicts",
        ],
    )
    assert result.exit_code == 0, result.output


def test_score_penalizes_low_operational_coverage(tmp_path: Path):
    weak = tmp_path / "README.md"
    weak.write_text("Route tenant reads through TenantResolver. Route invoices through InvoiceResolver.", encoding="utf-8")
    strong = tmp_path / "AGENTS.md"
    strong.write_text(
        "Always run tests before completion. Never commit secrets. Ask before destructive operations. Report what changed and report what was verified. `pytest`",
        encoding="utf-8",
    )
    assert score_path(strong)["overall"] > score_path(weak)["overall"]


def test_score_rewards_command_coverage(tmp_path: Path):
    with_command = tmp_path / "with.md"
    without_command = tmp_path / "without.md"
    with_command.write_text("Always run tests before completion. Never commit secrets. `pytest`", encoding="utf-8")
    without_command.write_text("Always run tests before completion. Never commit secrets.", encoding="utf-8")
    assert score_path(with_command)["testing_coverage"] > score_path(without_command)["testing_coverage"]


def test_short_file_overhead_warning_from_lint():
    manifest, report = analyze_text("Run tests. `pytest`", "AGENTS.md")
    assert report.markdown_tokens <= report.glp_tokens
    assert "test" in manifest.commands


def test_large_file_reduction_sanity():
    text = (
        "Read relevant files before editing. Always run tests before completion. Never commit secrets. "
        "Ask before destructive operations. Report what changed and report what was verified. `pytest`\n"
        * 100
    )
    _, report = analyze_text(text, "AGENTS.md")
    assert report.token_reduction > 0.5
