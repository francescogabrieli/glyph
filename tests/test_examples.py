from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from glyph.formats.parser import parse_glp
from glyph.interfaces.cli import app
from glyph.semantics.custom_rules import load_custom_rules


runner = CliRunner()


def test_examples_parse():
    root = Path("examples")
    assert root.exists()
    for glp in root.glob("**/*.glp"):
        manifest = parse_glp(glp.read_text(encoding="utf-8"))
        assert manifest.semantic_units()

    rules = load_custom_rules(root / "custom-rules/glyph.rules.yml")
    assert rules[0].id == "route_tenant_reads"

    json.loads((root / "mcp/claude-desktop-config.example.json").read_text(encoding="utf-8"))


def test_custom_rules_example_check_passes():
    result = runner.invoke(
        app,
        [
            "check",
            "examples/custom-rules/AGENTS.md",
            "examples/custom-rules/AGENTS.glp",
            "--rules",
            "examples/custom-rules/glyph.rules.yml",
            "--min-coverage",
            "80",
            "--min-operational-coverage",
            "80",
            "--min-reduction",
            "-999",
        ],
    )
    assert result.exit_code == 0, result.output
