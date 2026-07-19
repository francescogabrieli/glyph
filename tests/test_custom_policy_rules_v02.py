from __future__ import annotations

import json
from pathlib import Path

import pytest

from glyph.governance.diff import semantic_diff
from glyph.governance.emit import emit_markdown
from glyph.governance.lock import create_lock
from glyph.governance.select import select_manifest
from glyph.pipeline.compiler import analyze_text
from glyph.semantics.custom_rules import load_custom_policy_rules, load_custom_rules


EXPRESSION = json.dumps({
    "op": "atomic",
    "kind": "passive",
    "subject": ["production_credentials"],
    "predicate": "encrypted",
    "objects": ["key_broker"],
}, separators=(",", ":"))


def write_policy_rules(path: Path, *, duplicate: bool = False) -> None:
    second = ""
    if duplicate:
        other = json.dumps({
            "op": "atomic", "kind": "state", "subject": ["production_credentials"],
            "predicate": "be", "objects": ["unavailable"],
        }, separators=(",", ":"))
        second = f'''  - id: conflicting_policy
    match: exact
    patterns:
      - "Production credentials must be encrypted by KeyBroker."
    policy:
      category: must
      expression: '{other}'
      risk: high
      tags:
        - security
'''
    path.write_text(
        f'''rules:
  - id: exact_credential_policy
    match: exact
    patterns:
      - "Production credentials must be encrypted by KeyBroker."
    policy:
      category: must
      expression: '{EXPRESSION}'
      scope:
        - deploy/
      risk: low
      tags:
        - security
{second}''',
        encoding="utf-8",
    )


def test_existing_custom_rule_schema_remains_unchanged(tmp_path: Path):
    path = tmp_path / "glyph.rules.yml"
    path.write_text('''rules:
  - id: use_helper
    category: must
    patterns:
      - "Use the project helper."
    rendered: "Use the project helper."
''', encoding="utf-8")
    assert [rule.id for rule in load_custom_rules(path)] == ["use_helper"]
    assert load_custom_policy_rules(path) == []


def test_exact_custom_policy_precedes_grammar_and_applies_risk_floor(tmp_path: Path):
    rules = tmp_path / "glyph.rules.yml"
    write_policy_rules(rules)
    source = "Production credentials must be encrypted by KeyBroker."
    manifest, report = analyze_text(source, "AGENTS.md", rules_path=rules)
    assert not manifest.preserved
    policy = manifest.policies[0]
    assert policy.risk == "high"
    assert policy.scope == ["deploy/"]
    assert policy.id in manifest.provenance
    resolution = next(item for item in report.ledger.resolutions if item.destination == "policy")
    assert resolution.reason_code == "custom_policy_exact"
    assert resolution.policy_id == policy.fingerprint()

    mismatched, mismatch_report = analyze_text(source.lower(), "AGENTS.md", rules_path=rules)
    assert not any(item.reason_code == "custom_policy_exact" for item in mismatch_report.ledger.resolutions)
    assert mismatched.policies != manifest.policies


def test_incompatible_exact_custom_policies_preserve_and_report_conflict(tmp_path: Path):
    rules = tmp_path / "glyph.rules.yml"
    write_policy_rules(rules, duplicate=True)
    manifest, report = analyze_text("Production credentials must be encrypted by KeyBroker.", "AGENTS.md", rules_path=rules)
    assert manifest.preserved and not manifest.policies
    assert any(conflict.id.startswith("custom_policy_conflict_") for conflict in report.conflicts)
    resolution = next(item for item in report.ledger.resolutions if item.destination == "preserve")
    assert resolution.reason_code == "custom_policy_conflict"
    assert resolution.ambiguous is True


def test_policy_rules_require_exact_match(tmp_path: Path):
    rules = tmp_path / "glyph.rules.yml"
    write_policy_rules(rules)
    rules.write_text(rules.read_text().replace("    match: exact\n", "", 1), encoding="utf-8")
    with pytest.raises(ValueError, match="require match: exact"):
        load_custom_policy_rules(rules)


def test_custom_policy_flows_through_diff_select_lock_and_markdown(tmp_path: Path):
    rules = tmp_path / "glyph.rules.yml"
    write_policy_rules(rules)
    source = tmp_path / "AGENTS.md"
    source.write_text("Production credentials must be encrypted by KeyBroker.", encoding="utf-8")
    manifest, _ = analyze_text(source.read_text(), str(source), rules_path=rules)
    selected = select_manifest(manifest, "update documentation")
    assert selected.policies == manifest.policies
    assert "production credentials encrypted key broker" in emit_markdown(manifest, "agents-md")
    assert semantic_diff(manifest, manifest)["risks"] == []
    lock = create_lock([source], rules_path=rules)
    assert lock["policy_fingerprints"]
    assert lock["rules"]["sha256"]
