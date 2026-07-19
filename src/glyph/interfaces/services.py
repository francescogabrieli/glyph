from __future__ import annotations

from pathlib import Path
from typing import Any

from ..core.models import CompressionProfile
from ..formats.parser import parse_glp
from ..formats.renderer import render_glp
from ..governance.check import check_pair
from ..governance.lint import lint_text
from ..governance.reports import write_report
from ..governance.score import score_path
from ..governance.select import select_manifest, select_output
from ..pipeline.compiler import analyze_files
from ..source.tokenizer import count_tokens


class GlyphServiceError(ValueError):
    """Readable service-layer failure for CLI and MCP callers."""


def _path(value: str) -> Path:
    if not value:
        raise GlyphServiceError("Path values must not be empty.")
    return Path(value)


def _optional_path(value: str | None) -> Path | None:
    return Path(value) if value else None


def _profile(value: str | CompressionProfile) -> CompressionProfile:
    try:
        return value if isinstance(value, CompressionProfile) else CompressionProfile(value)
    except ValueError as exc:
        allowed = ", ".join(profile.value for profile in CompressionProfile)
        raise GlyphServiceError(f"Invalid profile {value!r}; expected one of: {allowed}.") from exc


def _candidate_dict(candidate: Any) -> dict[str, Any]:
    return {
        "id": candidate.id,
        "text": candidate.text,
        "source": candidate.source,
        "line": candidate.line,
        "section": candidate.section,
        "block_type": candidate.block_type,
        "intent": candidate.intent,
        "intent_confidence": candidate.intent_confidence,
        "operational_confidence": candidate.operational_confidence,
        "semantic_unit": candidate.semantic_unit,
        "semantic_confidence": candidate.semantic_confidence,
        "signals": list(candidate.signals or candidate.reasons),
        "reasoning_summary": candidate.reasoning_summary,
        "inherited_category": candidate.inherited_category,
        "risk": candidate.risk,
    }


def _match_dict(match: Any) -> dict[str, Any]:
    return {
        "semantic_unit": match.semantic_unit,
        "category": match.category,
        "confidence": match.confidence,
        "signals": list(match.signals),
        "candidate": _candidate_dict(match.candidate),
    }


def _command_candidate_dict(candidate: Any) -> dict[str, Any]:
    return {
        "command": candidate.command,
        "source": candidate.source,
        "line": candidate.line,
        "section": candidate.section,
        "block_type": candidate.block_type,
        "label": candidate.label,
        "confidence": candidate.confidence,
        "signals": list(candidate.signals),
    }


def _conflict_dict(conflict: Any) -> dict[str, Any]:
    return {
        "id": conflict.id,
        "severity": conflict.severity,
        "semantic_units": list(conflict.semantic_units),
        "source_files": list(conflict.source_files),
        "line_numbers": list(conflict.line_numbers),
        "suggested_fix": conflict.suggested_fix,
    }


def glyph_compile_service(
    sources: list[str],
    output: str,
    profile: str = "compact",
    rules_file: str | None = None,
    strict: bool = False,
    min_operational_coverage: float | None = None,
    max_unmapped: int | None = None,
    report: str | None = None,
    min_structured_coverage: float | None = None,
    min_retained_coverage: float | None = None,
    max_preserved: int | None = None,
    max_high_risk_preserved: int | None = None,
    require_structured: bool = False,
) -> dict[str, Any]:
    if not sources:
        raise GlyphServiceError("At least one source file is required.")
    profile_value = _profile(profile)
    paths = [_path(source) for source in sources]
    manifest, extraction = analyze_files(paths, rules_path=_optional_path(rules_file))
    warnings: list[str] = []
    if strict:
        structured_threshold = min_structured_coverage if min_structured_coverage is not None else min_operational_coverage
        if structured_threshold is not None and extraction.structured_coverage < structured_threshold:
            warnings.append(f"structured coverage {extraction.structured_coverage:.1f}% is below {structured_threshold:.1f}%")
        retained_threshold = 100.0 if min_retained_coverage is None else min_retained_coverage
        if extraction.retained_coverage < retained_threshold:
            warnings.append(f"retained coverage {extraction.retained_coverage:.1f}% is below {retained_threshold:.1f}%")
        high_risk_dropped = sum(1 for candidate in extraction.ledger.dropped_candidates if candidate.risk == "high")
        if high_risk_dropped > 0:
            warnings.append(f"high-risk dropped candidates {high_risk_dropped} exceeds 0")
        if max_unmapped is not None and extraction.dropped_count > max_unmapped:
            warnings.append(f"dropped operational candidates {extraction.dropped_count} exceeds {max_unmapped}")
        if max_preserved is not None and extraction.preserved_count > max_preserved:
            warnings.append(f"preserved directives {extraction.preserved_count} exceeds {max_preserved}")
        high_preserved_limit = 0 if max_high_risk_preserved is None else max_high_risk_preserved
        if extraction.high_risk_preserved_count > high_preserved_limit:
            warnings.append(f"high-risk preserved directives {extraction.high_risk_preserved_count} exceeds {high_preserved_limit}")
        if require_structured and extraction.preserved_count:
            warnings.append(f"structured output required but {extraction.preserved_count} directives were preserved")
        if extraction.conflicts:
            warnings.append("conflicts detected: " + ", ".join(conflict.id for conflict in extraction.conflicts))
        if warnings:
            if report:
                write_report(_path(report), extraction)
            raise GlyphServiceError("; ".join(warnings))
    output_path = _path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_glp(manifest, profile_value), encoding="utf-8")
    if report:
        write_report(_path(report), extraction)
    return {
        "output_path": str(output_path),
        "profile": profile_value.value,
        "semantic_coverage": extraction.semantic_coverage,
        "canonical_candidate_coverage": extraction.canonical_candidate_coverage,
        "structured_coverage": extraction.structured_coverage,
        "retained_coverage": extraction.retained_coverage,
        "safety_retention": extraction.safety_retention,
        "preserved_count": extraction.preserved_count,
        "high_risk_preserved_count": extraction.high_risk_preserved_count,
        "dropped_count": extraction.dropped_count,
        "agent_instruction_coverage": extraction.agent_instruction_coverage,
        "repo_specific_coverage": extraction.repo_specific_coverage,
        "spec_classification_rate": extraction.spec_classification_rate,
        "operational_coverage": extraction.operational_coverage,
        "high_risk_unmapped_count": extraction.high_risk_unmapped_count,
        "markdown_tokens": extraction.markdown_tokens,
        "glp_tokens": extraction.glp_tokens,
        "reduction": extraction.token_reduction,
        "unmapped_count": extraction.dropped_count,
        "conflict_count": len(extraction.conflicts),
        "warnings": warnings,
    }


def glyph_inspect_service(source: str, rules_file: str | None = None, show_unmapped: bool = False) -> dict[str, Any]:
    path = _path(source)
    _, extraction = analyze_files([path], rules_path=_optional_path(rules_file))
    return {
        "source": source,
        "adapter": extraction.adapters.get(str(path), "generic_markdown"),
        "semantic_coverage": extraction.semantic_coverage,
        "canonical_candidate_coverage": extraction.canonical_candidate_coverage,
        "structured_coverage": extraction.structured_coverage,
        "retained_coverage": extraction.retained_coverage,
        "safety_retention": extraction.safety_retention,
        "preserved_count": extraction.preserved_count,
        "high_risk_preserved_count": extraction.high_risk_preserved_count,
        "dropped_count": extraction.dropped_count,
        "agent_instruction_coverage": extraction.agent_instruction_coverage,
        "repo_specific_coverage": extraction.repo_specific_coverage,
        "spec_classification_rate": extraction.spec_classification_rate,
        "operational_coverage": extraction.operational_coverage,
        "high_risk_unmapped_count": extraction.high_risk_unmapped_count,
        "mapped_candidates": [_match_dict(match) for match in extraction.matches],
        "unmapped_candidates": [_candidate_dict(candidate) for candidate in extraction.unmapped_operational_candidates] if show_unmapped else [],
        "ledger": extraction.ledger.model_dump(),
        "commands": [_command_candidate_dict(candidate) for candidate in extraction.command_candidates],
        "conflicts": [_conflict_dict(conflict) for conflict in extraction.conflicts],
    }


def glyph_stats_service(markdown_path: str, glp_path: str) -> dict[str, Any]:
    markdown = _path(markdown_path).read_text(encoding="utf-8")
    glp = _path(glp_path).read_text(encoding="utf-8")
    markdown_tokens, tokenizer = count_tokens(markdown)
    glp_tokens, _ = count_tokens(glp)
    return {
        "markdown_tokens": markdown_tokens,
        "glp_tokens": glp_tokens,
        "saved_tokens": markdown_tokens - glp_tokens,
        "reduction": 0.0 if markdown_tokens == 0 else 1 - glp_tokens / markdown_tokens,
        "tokenizer": tokenizer,
    }


def glyph_select_service(glp_path: str, task: str, format: str = "glp", max_tokens: int | None = None) -> dict[str, Any]:
    manifest = parse_glp(_path(glp_path).read_text(encoding="utf-8"))
    selected = select_manifest(manifest, task, max_tokens)
    selected_text = select_output(manifest, task, format, max_tokens)
    estimated_tokens, _ = count_tokens(selected_text)
    return {
        "selected_text": selected_text,
        "format": format,
        "estimated_tokens": estimated_tokens,
        "included_semantic_units": sorted(selected.semantic_units()),
        "included_commands": dict(selected.commands),
    }


def glyph_check_service(
    markdown_path: str,
    glp_path: str,
    min_coverage: float | None = None,
    min_operational_coverage: float | None = None,
    min_reduction: float | None = None,
    max_unmapped: int | None = None,
    max_high_risk_unmapped: int | None = None,
    fail_on_conflicts: bool = False,
    min_structured_coverage: float | None = None,
    min_retained_coverage: float | None = None,
    max_preserved: int | None = None,
    max_high_risk_preserved: int | None = None,
    require_structured: bool = False,
) -> dict[str, Any]:
    markdown = _path(markdown_path)
    glp = _path(glp_path)
    ok, reasons = check_pair(
        markdown,
        glp,
        min_coverage=95.0 if min_coverage is None else min_coverage,
        min_reduction=30.0 if min_reduction is None else min_reduction,
        fail_on_conflicts=fail_on_conflicts,
        min_operational_coverage=min_operational_coverage,
        max_unmapped=max_unmapped,
        max_high_risk_unmapped=max_high_risk_unmapped,
        min_structured_coverage=min_structured_coverage,
        min_retained_coverage=min_retained_coverage,
        max_preserved=max_preserved,
        max_high_risk_preserved=max_high_risk_preserved,
        require_structured=require_structured,
    )
    _, extraction = analyze_files([markdown])
    stats = glyph_stats_service(markdown_path, glp_path)
    return {
        "passed": ok,
        "reasons": reasons,
        "semantic_coverage": 100.0,
        "canonical_candidate_coverage": extraction.canonical_candidate_coverage,
        "structured_coverage": extraction.structured_coverage,
        "retained_coverage": extraction.retained_coverage,
        "safety_retention": extraction.safety_retention,
        "preserved_count": extraction.preserved_count,
        "high_risk_preserved_count": extraction.high_risk_preserved_count,
        "dropped_count": extraction.dropped_count,
        "agent_instruction_coverage": extraction.agent_instruction_coverage,
        "repo_specific_coverage": extraction.repo_specific_coverage,
        "spec_classification_rate": extraction.spec_classification_rate,
        "operational_coverage": extraction.operational_coverage,
        "high_risk_unmapped_count": extraction.high_risk_unmapped_count,
        "reduction": stats["reduction"] * 100,
        "unmapped_count": extraction.dropped_count,
        "conflict_count": len(extraction.conflicts),
    }


def glyph_lint_service(source: str, rules_file: str | None = None) -> dict[str, Any]:
    warnings = lint_text(_path(source).read_text(encoding="utf-8"), source, _optional_path(rules_file))
    rows = [
        {
            "id": warning.id,
            "severity": warning.severity,
            "message": warning.explanation,
            "source": warning.source,
            "line": warning.line,
            "suggested_fix": warning.suggested_fix,
        }
        for warning in warnings
    ]
    return {
        "warnings": rows,
        "summary": {
            "count": len(rows),
            "high": sum(1 for row in rows if row["severity"] == "high"),
            "medium": sum(1 for row in rows if row["severity"] == "medium"),
            "low": sum(1 for row in rows if row["severity"] == "low"),
        },
    }


def glyph_score_service(source: str, rules_file: str | None = None) -> dict[str, Any]:
    return score_path(_path(source), _optional_path(rules_file))
