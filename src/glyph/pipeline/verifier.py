from __future__ import annotations

import json
from pathlib import Path

from ..core.models import GlyphManifest, VerifyReport
from .compiler import analyze_text


def verify(markdown: str, manifest: GlyphManifest, rules_path: Path | None = None, source: str = "<memory>", adapter: str | None = None) -> VerifyReport:
    """Verify against the same source identity used at compile time.

    Adapter choice participates in deterministic confidence scoring, so callers
    with a real path must pass it rather than re-analyzing every document as an
    anonymous memory buffer.
    """
    detected_manifest, extraction = analyze_text(markdown, source=source, adapter=adapter, rules_path=rules_path)
    detected = detected_manifest.semantic_units()
    encoded = manifest.semantic_units()
    missing = sorted(detected - encoded)
    missing_commands = {k: v for k, v in detected_manifest.commands.items() if manifest.commands.get(k) != v}
    missing_stack = sorted(set(detected_manifest.stack) - set(manifest.stack))
    coverage = 100.0 if not detected else (len(detected & encoded) / len(detected)) * 100
    expected_policies = {policy.id for policy in detected_manifest.policies}
    expected_preserved = {directive.id for directive in detected_manifest.preserved}
    actual_policies = {policy.id for policy in manifest.policies}
    actual_preserved = {directive.id for directive in manifest.preserved}
    missing_policy_ids = sorted(expected_policies - actual_policies)
    missing_preserve_ids = sorted(expected_preserved - actual_preserved)

    operational = extraction.ledger.operational_candidates
    by_candidate: dict[tuple[str, str | None, int | None], list[object]] = {}
    for resolution in extraction.ledger.resolutions:
        by_candidate.setdefault((resolution.candidate_id, resolution.source, resolution.line), []).append(resolution)

    def retained(candidate: object, destinations: set[str]) -> bool:
        key = (getattr(candidate, "id"), getattr(candidate, "source"), getattr(candidate, "line"))
        for resolution in by_candidate.get(key, []):
            if resolution.destination == "canonical" and resolution.canonical_id in encoded and "canonical" in destinations:
                return True
            policy_ids = set(resolution.policy_ids or ([resolution.policy_id] if resolution.policy_id else []))
            if resolution.destination == "policy" and policy_ids and policy_ids <= actual_policies and "policy" in destinations:
                return True
            if resolution.destination == "preserve" and resolution.preserve_id in actual_preserved and "preserve" in destinations:
                return True
        return False

    def metric(items: list[object], destinations: set[str]) -> float:
        return 100.0 if not items else sum(1 for candidate in items if retained(candidate, destinations)) / len(items) * 100

    high_risk = [candidate for candidate in operational if candidate.risk == "high"]
    return VerifyReport(
        detected_semantic_units=sorted(detected),
        encoded_semantic_units=sorted(encoded),
        missing_semantic_units=missing,
        coverage=coverage,
        missing_commands=missing_commands,
        missing_stack=missing_stack,
        conflicts=detected_manifest.conflicts + manifest.conflicts,
        missing_policy_ids=missing_policy_ids,
        missing_preserve_ids=missing_preserve_ids,
        canonical_candidate_coverage=metric(operational, {"canonical"}),
        structured_coverage=metric(operational, {"canonical", "policy"}),
        retained_coverage=metric(operational, {"canonical", "policy", "preserve"}),
        safety_retention=metric(high_risk, {"canonical", "policy", "preserve"}),
        preserved_count=len(manifest.preserved),
        high_risk_preserved_count=sum(1 for directive in manifest.preserved if directive.risk == "high"),
        dropped_count=0,
    )


def operational_coverage(markdown: str, rules_path: Path | None = None, source: str = "<memory>", adapter: str | None = None) -> tuple[float, int]:
    _, report = analyze_text(markdown, source=source, adapter=adapter, rules_path=rules_path)
    return report.structured_coverage, report.dropped_count


def verify_expected(manifest: GlyphManifest, expected_path: Path) -> VerifyReport:
    expected = json.loads(expected_path.read_text(encoding="utf-8"))
    semantic = set(expected.get("semantic_units", []))
    encoded = manifest.semantic_units()
    missing = sorted(semantic - encoded)
    missing_commands = {k: v for k, v in expected.get("commands", {}).items() if manifest.commands.get(k) != v}
    missing_stack = sorted(set(expected.get("stack", [])) - set(manifest.stack))
    total = len(semantic) + len(expected.get("commands", {})) + len(expected.get("stack", []))
    missed = len(missing) + len(missing_commands) + len(missing_stack)
    coverage = 100.0 if total == 0 else ((total - missed) / total) * 100
    return VerifyReport(
        detected_semantic_units=sorted(semantic),
        encoded_semantic_units=sorted(encoded),
        missing_semantic_units=missing,
        coverage=coverage,
        missing_commands=missing_commands,
        missing_stack=missing_stack,
        conflicts=manifest.conflicts,
    )
