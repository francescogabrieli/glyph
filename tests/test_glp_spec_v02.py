from __future__ import annotations

from pathlib import Path

import pytest

from glyph.core.models import AttachedExpression, CompressionProfile, GlyphManifest, PolicyAtom, PolicyExpression, PolicyLink
from glyph.formats.parser import parse_glp
from glyph.formats.renderer import render_glp
from glyph.governance.diff import semantic_diff
from glyph.governance.emit import TARGET_TITLES, emit_markdown
from glyph.governance.lock import create_lock
from glyph.governance.select import select_manifest
from glyph.pipeline.compiler import analyze_text


def atom(kind: str, subject: str, predicate: str, *objects: str) -> PolicyExpression:
    return PolicyExpression(op="atomic", kind=kind, subject=[subject], predicate=predicate, objects=list(objects))  # type: ignore[arg-type]


def test_v01_rendering_is_byte_stable_and_has_lossless_semantic_upgrade_view():
    source = 'glyph/0.1\npolicy[must p_fixed action=route target=tenant_reads condition="tenant exists" risk=high tag=security]\n'
    parsed = parse_glp(source)
    assert render_glp(parsed) == source
    expression = parsed.policies[0].semantic_expression()
    assert expression == atom("action", "agent", "route", "tenant_reads")
    assert parsed.policies[0].conditions == ["tenant exists"]
    upgraded = parsed.upgraded_v2()
    assert upgraded.version == "0.2"
    assert parse_glp(render_glp(upgraded)) == upgraded
    assert upgraded.policies[0].conditions == ["tenant exists"]


@pytest.mark.parametrize("profile", list(CompressionProfile))
def test_v02_parse_render_parse_equality_and_deterministic_ids(profile: CompressionProfile):
    condition = PolicyExpression(op="all", operands=[atom("state", "environment", "is", "production"), atom("state", "request", "has", "approval")])
    policy = PolicyAtom(
        category="must",
        expression=PolicyExpression(op="not", operands=[atom("passive", "credentials", "stored", "artifact")]),
        scope=["services/auth/"],
        condition_expression=AttachedExpression(attachment="policy", expression=condition),
        exception_expressions=[AttachedExpression(attachment="policy", expression=atom("state", "mode", "is", "local"))],
        risk="high",
        tags=["security"],
    )
    manifest = GlyphManifest(version="0.2", policies=[policy])
    rendered = render_glp(manifest, profile)
    reparsed = parse_glp(rendered)
    assert reparsed == manifest.sorted_copy()
    assert render_glp(reparsed, profile) == rendered
    assert policy.id == PolicyAtom(**policy.payload()).id


def test_subject_is_distinct_from_repository_scope_and_predicate_parts():
    policy = PolicyAtom(
        category="must",
        expression=atom("action", "release_automation", "use", "managed_identity"),
        scope=["deploy/"],
    )
    parsed = parse_glp(render_glp(GlyphManifest(policies=[policy])))
    expression = parsed.policies[0].expression
    assert expression and expression.subject == ["release_automation"]
    assert expression.predicate == "use"
    assert expression.objects == ["managed_identity"]
    assert parsed.policies[0].scope == ["deploy/"]


@pytest.mark.parametrize("kind", ["action", "state", "passive"])
def test_atomic_predicate_kinds(kind: str):
    expression = atom(kind, "artifact", "validated", "review_service")
    assert parse_glp(render_glp(GlyphManifest(policies=[PolicyAtom(category="must", expression=expression)]))).policies[0].expression == expression


@pytest.mark.parametrize("op", ["all", "any"])
def test_condition_all_and_any_operators(op: str):
    expression = PolicyExpression(op=op, operands=[atom("state", "environment", "is", "production"), atom("state", "change", "has", "approval")])  # type: ignore[arg-type]
    policy = PolicyAtom(category="must", expression=atom("action", "agent", "deploy", "artifact"), condition_expression=AttachedExpression(expression=expression))
    assert parse_glp(render_glp(GlyphManifest(policies=[policy]))).policies[0].condition_expression.expression == expression.sorted_copy()  # type: ignore[union-attr]


def test_simple_and_not_conditions_and_exception_attachment():
    simple = atom("state", "environment", "is", "production")
    negated = PolicyExpression(op="not", operands=[simple])
    policy = PolicyAtom(
        category="must",
        expression=atom("action", "agent", "write", "configuration"),
        condition_expression=AttachedExpression(attachment="policy", expression=simple),
        exception_expressions=[AttachedExpression(attachment="policy", expression=negated)],
    )
    parsed = parse_glp(render_glp(GlyphManifest(policies=[policy]))).policies[0]
    assert parsed.condition_expression and parsed.condition_expression.attachment == "policy"
    assert parsed.exception_expressions[0].expression.op == "not"


def test_all_expression_preserves_inseparable_compound_policy_linkage():
    compound = PolicyExpression(op="all", operands=[atom("action", "agent", "sign", "artifact"), atom("action", "agent", "publish", "artifact")])
    manifest = GlyphManifest(policies=[PolicyAtom(category="must", expression=compound)])
    assert len(manifest.sorted_copy().policies) == 1
    assert manifest.sorted_copy().policies[0].expression.op == "all"  # type: ignore[union-attr]


@pytest.mark.parametrize("profile", list(CompressionProfile))
def test_allow_and_cross_modality_link_round_trip_atomically(profile: CompressionProfile):
    group = "g_synthetic"
    policies = [
        PolicyAtom(category="allow", expression=atom("action", "agent", "read", "artifact"), link=PolicyLink(group=group, order=0), risk="high"),
        PolicyAtom(category="deny", expression=atom("action", "agent", "delete", "artifact"), link=PolicyLink(group=group, order=1), risk="high"),
    ]
    manifest = GlyphManifest(version="0.2", policies=policies)
    rendered = render_glp(manifest, profile)
    parsed = parse_glp(rendered)
    assert parsed == manifest.sorted_copy()
    selected = select_manifest(parsed, "read artifact", max_tokens=None)
    assert {policy.category for policy in selected.policies} == {"allow", "deny"}
    markdown = emit_markdown(parsed, "agents-md")
    assert "one inseparable directive" in markdown
    assert "Allow agent read artifact" in markdown
    assert "Do not agent delete artifact" in markdown
    with pytest.raises(ValueError, match="semantic loss"):
        render_glp(manifest, version="0.1")


def test_v02_downgrade_with_semantic_loss_is_rejected():
    manifest = GlyphManifest(policies=[PolicyAtom(category="must", expression=atom("state", "artifact", "be", "immutable"))])
    with pytest.raises(ValueError, match="semantic loss"):
        render_glp(manifest, version="0.1")


def test_supported_relation_extraction_and_conservative_narrative_non_match():
    manifest, report = analyze_text("Service accounts must use managed credentials.", "AGENTS.md")
    policy = manifest.policies[0]
    assert manifest.version == "0.2"
    assert policy.expression == atom("action", "service_accounts", "use", "managed_credentials")
    narrative, _ = analyze_text("The guide says service accounts must use managed credentials.", "README.md")
    assert not any(policy.is_v2 for policy in narrative.policies)
    assert report.retained_coverage == 100.0


def test_ambiguous_high_risk_relation_is_preserved():
    manifest, report = analyze_text("Production identities must carefully correspond across protected boundaries.", "AGENTS.md")
    assert manifest.preserved and manifest.preserved[0].risk == "high"
    assert report.high_risk_preserved_count == 1


def test_semantic_diff_selection_lock_and_emitters_support_v02(tmp_path: Path):
    old_policy = PolicyAtom(category="must", expression=atom("action", "release_agent", "use", "managed_identity"), risk="high", tags=["security"])
    new_policy = PolicyAtom(category="must", expression=atom("action", "release_agent", "use", "ephemeral_identity"), risk="high", tags=["security"])
    result = semantic_diff(GlyphManifest(policies=[old_policy]), GlyphManifest(policies=[new_policy]))
    assert result["removed_policies"] and any("High risk" in risk for risk in result["risks"])
    selected = select_manifest(GlyphManifest(policies=[new_policy]), "update documentation")
    assert selected.policies == [new_policy]
    for target in TARGET_TITLES:
        emitted = emit_markdown(GlyphManifest(policies=[new_policy]), target)
        assert "release agent use ephemeral identity" in emitted

    source = tmp_path / "AGENTS.md"
    source.write_text("Release agents must use managed identities.", encoding="utf-8")
    first = create_lock([source])
    second = create_lock([source])
    assert first == second
    assert first["manifest_version"] == "0.2"
