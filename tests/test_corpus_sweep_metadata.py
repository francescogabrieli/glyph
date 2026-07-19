from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

SPEC = importlib.util.spec_from_file_location("glyph_corpus_sweep", Path(__file__).parents[1] / "evals" / "corpus_sweep.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
_sanitized_derivation = MODULE._sanitized_derivation
_taxonomy_summary = MODULE._taxonomy_summary
markdown_report = MODULE.markdown_report


def test_sanitized_derivation_contains_structure_but_no_source_text():
    resolution = SimpleNamespace(
        policy_shape="negative_action",
        subject_available=True,
        predicate_kind="action",
        object_cardinality=1,
        operators=["not", "atomic"],
        attachment="policy",
        ambiguous=False,
        reason_code="unique_negative_action",
        destination="policy",
        reason="third-party wording must never be copied",
    )
    result = _sanitized_derivation(resolution)
    assert result == {
        "shape": "negative_action",
        "subject_available": True,
        "predicate_kind": "action",
        "object_cardinality": 1,
        "operators": ["atomic", "not"],
        "attachment": "policy",
        "ambiguous": False,
        "reason_code": "unique_negative_action",
        "outcome": "policy",
    }
    assert "wording" not in str(result)


def test_taxonomy_aggregates_equal_sanitized_shapes_deterministically():
    derivation = {"shape": "unresolved", "predicate_kind": None, "object_cardinality": 0, "operators": [], "attachment": None, "ambiguous": True, "reason_code": "pronoun_reference", "outcome": "preserve", "subject_available": False}
    first = _taxonomy_summary([{"derivation": derivation}, {"derivation": derivation}])
    second = _taxonomy_summary(list(reversed([{"derivation": derivation}, {"derivation": derivation}])))
    assert first == second
    assert first[0]["count"] == 2


def test_markdown_report_labels_v02_and_includes_only_aggregate_taxonomy():
    report = {
        "gate": {"zero_crashes": True},
        "repositories": [],
        "summary": {
            "repositories": 0, "files": 0, "agent_specific_files": 0, "determinism_failures": 0, "review_required": 0,
            "average_structured_coverage": 100.0, "minimum_structured_coverage": 100.0,
            "average_retained_coverage": 100.0, "minimum_retained_coverage": 100.0,
            "average_safety_retention": 100.0, "minimum_safety_retention": 100.0,
            "preserved_count": 0, "high_risk_preserved_count": 0, "dropped_count": 0,
            "average_canonical_candidate_coverage": 100.0, "average_agent_instruction_coverage": 100.0,
            "minimum_agent_instruction_coverage": 100.0, "average_operational_coverage": 100.0,
            "minimum_operational_coverage": 100.0, "average_token_reduction": 0.5, "minimum_token_reduction": 0.5,
            "negative_reduction_files": 0, "triage_counts": {}, "high_risk_candidate_count": 2,
            "high_risk_taxonomy": [{"shape": "unresolved", "predicate_kind": None, "object_cardinality": 0, "operators": [], "attachment": None, "ambiguous": True, "reason_code": "pronoun_reference", "outcome": "preserve", "count": 2}],
        },
    }
    rendered = markdown_report(report)
    assert rendered.startswith("# Glyph v0.2 external corpus sweep")
    assert "High-risk operational candidates: 2" in rendered
    assert "third-party wording" not in rendered.lower()
