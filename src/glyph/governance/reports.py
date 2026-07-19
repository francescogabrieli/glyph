from __future__ import annotations

import json
from pathlib import Path

from ..source.document_ir import ExtractionReport


def report_to_json(report: ExtractionReport) -> str:
    payload = report.model_dump()
    payload["metrics"] = {
        "structured_coverage": report.structured_coverage,
        "retained_coverage": report.retained_coverage,
        "safety_retention": report.safety_retention,
        "preserved_count": report.preserved_count,
        "high_risk_preserved_count": report.high_risk_preserved_count,
        "dropped_count": report.dropped_count,
    }
    payload["compatibility_diagnostics"] = {
        "semantic_coverage": report.semantic_coverage,
        "canonical_candidate_coverage": report.canonical_candidate_coverage,
        "high_risk_unmapped_count": report.high_risk_unmapped_count,
        "operational_coverage": report.operational_coverage,
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def report_to_markdown(report: ExtractionReport) -> str:
    lines = ["# Glyph compile report", ""]
    lines += [
        f"- Inputs: {', '.join(report.input_files)}",
        f"- Tokenizer: {report.tokenizer}",
        f"- Markdown tokens: {report.markdown_tokens}",
        f"- GLP tokens: {report.glp_tokens}",
        f"- Token reduction: {report.token_reduction * 100:.1f}%",
        "## Post-hardening metrics",
        "",
        f"- Structured coverage: {report.structured_coverage:.1f}%",
        f"- Retained coverage: {report.retained_coverage:.1f}%",
        f"- Safety retention: {report.safety_retention:.1f}%",
        f"- Preserved directives: {report.preserved_count}",
        f"- High-risk preserved directives: {report.high_risk_preserved_count}",
        f"- Dropped candidates: {report.dropped_count}",
        "",
        "## Compatibility diagnostics",
        "",
        f"- Legacy semantic coverage: {report.semantic_coverage:.1f}%",
        f"- Legacy canonical candidate coverage: {report.canonical_candidate_coverage:.1f}%",
        f"- Legacy high-risk unmapped count: {report.high_risk_unmapped_count}",
        f"- Agent instruction coverage: {report.agent_instruction_coverage:.1f}%",
        f"- Repo-specific coverage: {report.repo_specific_coverage:.1f}%",
        f"- Spec classification rate: {report.spec_classification_rate:.1f}%",
        f"- Operational coverage: {report.operational_coverage:.1f}%",
        f"- Conflicts: {len(report.conflicts)}",
        "",
    ]
    if report.semantic_units_emitted:
        lines += ["## Semantic Units", "", *[f"- `{unit}`" for unit in report.semantic_units_emitted], ""]
    if report.commands_detected:
        lines += ["## Commands", "", *[f"- `{label}`: `{command}`" for label, command in report.commands_detected.items()], ""]
    if report.ledger.resolutions:
        lines += ["## Candidate Resolution Ledger", ""]
        for resolution in report.ledger.resolutions:
            destination_id = resolution.canonical_id or resolution.policy_id or resolution.preserve_id or "-"
            lines.append(f"- `{resolution.candidate_id}` {resolution.source}:{resolution.line} → {resolution.destination}:{destination_id}")
        lines.append("")
    ledger_groups = [
        ("Repo-Specific Custom-Rule Candidates", report.ledger.repo_specific_candidates),
        ("Product Requirements", report.ledger.product_requirements),
        ("Implementation Requirements", report.ledger.implementation_requirements),
        ("API Contracts", report.ledger.api_contracts),
        ("Conditional Instructions", report.ledger.conditional_instructions),
        ("Examples Or References", report.ledger.examples_or_references),
        ("Non-Operational Context", report.ledger.non_operational_context[:10]),
        ("High-Risk Unmapped", report.ledger.high_risk_unmapped),
    ]
    for title, candidates in ledger_groups:
        if candidates:
            lines += [f"## {title}", ""]
            for candidate in candidates:
                lines.append(f"- {candidate.source}:{candidate.line} [{candidate.section or 'root'}] {candidate.text}")
            lines.append("")
    if report.unmapped_operational_candidates:
        lines += ["## Non-Canonical Operational Candidates", ""]
        for candidate in report.unmapped_operational_candidates:
            lines.append(f"- {candidate.source}:{candidate.line} [{candidate.intent}] {candidate.text}")
        lines.append("")
    if report.conflicts:
        lines += ["## Conflicts", ""]
        for conflict in report.conflicts:
            lines.append(f"- `{conflict.id}` ({conflict.severity}): {conflict.suggested_fix}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_report(path: Path, report: ExtractionReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == ".json":
        path.write_text(report_to_json(report), encoding="utf-8")
    elif path.suffix.lower() in {".md", ".markdown"}:
        path.write_text(report_to_markdown(report), encoding="utf-8")
    else:
        raise ValueError("Report path must end in .json or .md")
