from __future__ import annotations

import json
from pathlib import Path

from ..core.models import CompressionProfile
from ..formats.parser import parse_glp
from ..formats.renderer import render_glp
from ..pipeline.compiler import analyze_files
from ..pipeline.verifier import verify
from ..semantics.rules import RULE_BY_ID
from ..source.tokenizer import count_tokens
from .lock import create_lock


def _detect_profile(glp_text: str) -> CompressionProfile:
    first = glp_text.lstrip().splitlines()[0] if glp_text.strip() else ""
    if first in {"g/0.1", "g/0.2"}:
        return CompressionProfile.ultra
    if any(line.startswith("  ") for line in glp_text.splitlines()):
        return CompressionProfile.readable
    return CompressionProfile.compact


def check_pair(
    markdown_path: Path,
    glp_path: Path,
    min_coverage: float = 95.0,
    min_reduction: float = 30.0,
    fail_on_conflicts: bool = False,
    min_operational_coverage: float | None = None,
    max_unmapped: int | None = None,
    max_high_risk_unmapped: int | None = None,
    rules_path: Path | None = None,
    min_retained_coverage: float | None = None,
    min_structured_coverage: float | None = None,
    max_preserved: int | None = None,
    max_high_risk_preserved: int | None = None,
    require_structured: bool = False,
) -> tuple[bool, list[str]]:
    markdown = markdown_path.read_text(encoding="utf-8")
    glp_text = glp_path.read_text(encoding="utf-8")
    manifest = parse_glp(glp_text)
    compiled, extraction = analyze_files([markdown_path], rules_path=rules_path)
    report = verify(markdown, manifest, rules_path=rules_path, source=str(markdown_path))
    md_tokens, tokenizer = count_tokens(markdown)
    profile = _detect_profile(glp_text)
    glp_tokens, _ = count_tokens(glp_text)
    reduction = 0.0 if md_tokens == 0 else (1 - glp_tokens / md_tokens) * 100
    errors: list[str] = []
    if report.coverage < min_coverage:
        errors.append(f"semantic coverage {report.coverage:.1f}% is below {min_coverage:.1f}%")
    if reduction < min_reduction:
        errors.append(f"token reduction {reduction:.1f}% is below {min_reduction:.1f}% using {tokenizer}")
    structured_threshold = min_structured_coverage if min_structured_coverage is not None else min_operational_coverage
    if structured_threshold is not None and report.structured_coverage < structured_threshold:
        errors.append(f"structured coverage {report.structured_coverage:.1f}% is below {structured_threshold:.1f}%")
    if min_retained_coverage is not None and report.retained_coverage < min_retained_coverage:
        errors.append(f"retained coverage {report.retained_coverage:.1f}% is below {min_retained_coverage:.1f}%")
    if max_unmapped is not None and report.dropped_count > max_unmapped:
        errors.append(f"dropped operational candidates {report.dropped_count} exceeds {max_unmapped}")
    high_risk_dropped = sum(1 for candidate in extraction.ledger.dropped_candidates if candidate.risk == "high")
    if max_high_risk_unmapped is not None and high_risk_dropped > max_high_risk_unmapped:
        errors.append(f"high-risk dropped candidates {high_risk_dropped} exceeds {max_high_risk_unmapped}")
    if max_preserved is not None and report.preserved_count > max_preserved:
        errors.append(f"preserved directives {report.preserved_count} exceeds {max_preserved}")
    if max_high_risk_preserved is not None and report.high_risk_preserved_count > max_high_risk_preserved:
        errors.append(f"high-risk preserved directives {report.high_risk_preserved_count} exceeds {max_high_risk_preserved}")
    if require_structured and report.preserved_count:
        errors.append(f"structured output required but {report.preserved_count} directives were preserved")
    if render_glp(compiled, profile).strip() != render_glp(manifest, profile).strip():
        errors.append(".glp is stale; re-run glyph compile")
    if fail_on_conflicts and extraction.conflicts:
        errors.append("conflicts detected: " + ", ".join(conflict.id for conflict in extraction.conflicts))
    dangerous = {rule_id for rule_id in compiled.semantic_units() if RULE_BY_ID.get(rule_id) and RULE_BY_ID[rule_id].safety_critical}
    removed = sorted(dangerous - manifest.semantic_units())
    if removed:
        errors.append("dangerous safety rules missing from .glp: " + ", ".join(removed))
    return not errors, errors


def check_lock(lock_path: Path) -> tuple[bool, list[str]]:
    expected = json.loads(lock_path.read_text(encoding="utf-8"))
    if expected.get("schema") != "glyph-lock/v3":
        return False, ["lockfile schema is obsolete; re-run glyph lock to generate glyph-lock/v3"]
    paths = [Path(path) for path in expected["inputs"]]
    rules_value = expected.get("rules", {})
    rules_path = Path(rules_value["path"]) if isinstance(rules_value, dict) and rules_value.get("path") else None
    current = create_lock(paths, rules_path)
    if current["checksum"] != expected.get("checksum"):
        return False, ["lockfile is stale; re-run glyph lock"]
    return True, []
