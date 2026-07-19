from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from glyph.formats.renderer import render_glp
from glyph.interfaces.cli import app
from glyph.interfaces.mcp_server import MCP_INSTALL_MESSAGE
from glyph.interfaces.services import (
    glyph_check_service,
    glyph_compile_service,
    glyph_inspect_service,
    glyph_lint_service,
    glyph_score_service,
    glyph_select_service,
    glyph_stats_service,
)


runner = CliRunner()


def _source(tmp_path: Path) -> Path:
    source = tmp_path / "AGENTS.md"
    source.write_text(
        "# Agent Instructions\n"
        "This project contains detailed background for humans about architecture, onboarding, "
        "domain language, ownership, local development tradeoffs, and release context. "
        "Those notes are useful context, but the operational parts below are the instructions "
        "Glyph should preserve as compact semantic units.\n\n"
        "## Testing\nBefore opening a PR, make sure the suite is green. `pytest`\n\n"
        "## Security\nNever include credentials, API keys, or tokens in code, tests, logs, fixtures, or examples.\n"
        "Ask for confirmation before destructive operations.\n"
        "Report what changed and report what was verified.",
        encoding="utf-8",
    )
    return source


def test_glyph_compile_service_output_shape(tmp_path: Path):
    source = _source(tmp_path)
    output = tmp_path / "AGENTS.glp"
    result = glyph_compile_service([str(source)], str(output), strict=True, min_operational_coverage=80)
    assert output.exists()
    assert result["output_path"] == str(output)
    assert result["profile"] == "compact"
    assert result["semantic_coverage"] == 100.0
    assert result["operational_coverage"] >= 80
    assert result["markdown_tokens"] > result["glp_tokens"]
    assert result["unmapped_count"] == 0
    assert result["conflict_count"] == 0
    assert result["warnings"] == []


def test_glyph_inspect_service_output_shape(tmp_path: Path):
    source = _source(tmp_path)
    result = glyph_inspect_service(str(source), show_unmapped=True)
    assert result["source"] == str(source)
    assert result["adapter"] == "agents_md"
    assert result["mapped_candidates"]
    assert "semantic_unit" in result["mapped_candidates"][0]
    assert result["commands"]
    assert result["conflicts"] == []


def test_glyph_stats_service_output_shape(tmp_path: Path):
    source = _source(tmp_path)
    output = tmp_path / "AGENTS.glp"
    glyph_compile_service([str(source)], str(output))
    result = glyph_stats_service(str(source), str(output))
    assert result["markdown_tokens"] > 0
    assert result["glp_tokens"] > 0
    assert result["saved_tokens"] == result["markdown_tokens"] - result["glp_tokens"]
    assert 0 <= result["reduction"] <= 1
    assert result["tokenizer"]


def test_glyph_select_service_output_shape(tmp_path: Path):
    source = _source(tmp_path)
    output = tmp_path / "AGENTS.glp"
    glyph_compile_service([str(source)], str(output))
    result = glyph_select_service(str(output), "fix failing tests", "markdown")
    assert result["format"] == "markdown"
    assert result["selected_text"].startswith("# Selected Instructions")
    assert result["estimated_tokens"] > 0
    assert "run_tests_before_done" in result["included_semantic_units"]
    assert "test" in result["included_commands"]


def test_glyph_check_service_pass_and_fail_cases(tmp_path: Path):
    source = _source(tmp_path)
    output = tmp_path / "AGENTS.glp"
    glyph_compile_service([str(source)], str(output))
    passed = glyph_check_service(str(source), str(output), min_coverage=90, min_operational_coverage=80, min_reduction=10)
    assert passed["passed"] is True
    assert passed["reasons"] == []

    output.write_text(render_glp(passed_manifest_without_safety()), encoding="utf-8")
    failed = glyph_check_service(str(source), str(output), min_coverage=90, min_operational_coverage=80, min_reduction=10)
    assert failed["passed"] is False
    assert failed["reasons"]


def passed_manifest_without_safety():
    from glyph.core.models import GlyphManifest

    return GlyphManifest(must=["run_tests_before_done"], commands={"test": "pytest"})


def test_glyph_lint_service_warning_shape(tmp_path: Path):
    source = tmp_path / "README.md"
    source.write_text("Route tenant reads through TenantResolver.", encoding="utf-8")
    result = glyph_lint_service(str(source))
    assert result["summary"]["count"] >= 1
    assert {"id", "severity", "message", "source", "line", "suggested_fix"} <= set(result["warnings"][0])


def test_glyph_score_service_output_shape(tmp_path: Path):
    source = _source(tmp_path)
    result = glyph_score_service(str(source))
    for key in [
        "overall",
        "token_cost",
        "compression_potential",
        "semantic_clarity",
        "testing_coverage",
        "safety_coverage",
        "reporting_coverage",
        "conflict_risk",
        "context_bloat",
        "operational_coverage",
    ]:
        assert key in result


def test_missing_optional_mcp_dependency_error_message(monkeypatch):
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "mcp.server.fastmcp":
            raise ImportError("missing mcp")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    result = runner.invoke(app, ["mcp"])
    assert result.exit_code == 1
    assert MCP_INSTALL_MESSAGE in result.output


def test_mcp_help_does_not_require_optional_dependency():
    result = runner.invoke(app, ["mcp", "--help"])
    assert result.exit_code == 0
    assert "local Glyph MCP server" in result.output
