from __future__ import annotations

import json
from pathlib import Path

from glyph.formats.renderer import render_glp
from glyph.governance.select import select_manifest
from glyph.pipeline.compiler import analyze_text


def test_golden_cases_semantics_commands_unmapped_and_conflicts():
    cases = json.loads(Path("tests/golden/cases.json").read_text(encoding="utf-8"))
    for case in cases:
        manifest, report = analyze_text(case["source"], f"{case['name']}.md")
        units = manifest.semantic_units()
        for expected in case["semantic_units"]:
            assert expected in units, case["name"]
        for label, command in case["commands"].items():
            assert manifest.commands.get(label) == command, case["name"]
        unmapped = [candidate.text for candidate in report.unmapped_operational_candidates]
        for expected in case["unmapped_contains"]:
            assert expected in unmapped, case["name"]
        conflict_ids = [conflict.id for conflict in report.conflicts]
        for expected in case["conflicts"]:
            assert expected in conflict_ids, case["name"]


def test_golden_custom_rule_maps_repository_specific_instruction(tmp_path: Path):
    source = tmp_path / "AGENTS.md"
    source.write_text("## Database\nUse the shared tenant resolver instead of querying tenants manually.", encoding="utf-8")
    rules = tmp_path / "glyph.rules.yml"
    rules.write_text(
        """rules:
  - id: use_tenant_resolver
    category: must
    patterns:
      - "use the shared tenant resolver"
    positive_terms:
      - "tenant resolver"
    section_hints:
      - "database"
    modal_hints:
      - "use"
    rendered: "Use the shared tenant resolver."
    always_select: true
""",
        encoding="utf-8",
    )
    manifest, report = analyze_text(source.read_text(encoding="utf-8"), str(source), rules_path=rules)
    assert "use_tenant_resolver" in manifest.must
    assert not report.unmapped_operational_candidates


def test_golden_task_selection_keeps_safety_rules_for_unrelated_task(tmp_path: Path):
    manifest = analyze_text(
        "Always run tests before completion. Never commit secrets. Do not expose credentials. "
        "Do not expose API keys or tokens. Ask before destructive operations. Do not deploy without approval. "
        "Do not write production configuration without approval. `pytest`",
        "AGENTS.md",
    )[0]
    selected = select_manifest(manifest, "update React component", max_tokens=300)
    assert {"secrets_commit", "credentials_exposure", "api_key_exposure", "prod_config_write", "deploy_without_approval"} <= set(selected.deny)
    assert "destructive_ops" in selected.ask
    assert len(render_glp(selected)) < len(render_glp(manifest)) or selected.semantic_units() == manifest.semantic_units()
