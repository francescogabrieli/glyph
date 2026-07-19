from __future__ import annotations

import re
from pathlib import Path

from .conflicts import detect_conflicts
from ..core.models import CandidateResolution, GlyphManifest, SemanticRule, SourceHit
from ..formats.renderer import render_glp
from ..semantics.custom_rules import load_custom_policy_rules, load_custom_rules
from ..semantics.policies import classify_risk, is_operational, resolve_candidate
from ..semantics.rules import RULES
from ..semantics.classifier import classify_commands
from ..source.adapters import detect_adapter, validate_adapter
from ..source.candidates import extract_command_candidates, extract_instruction_candidates
from ..source.document_ir import ConflictFinding, ExtractionReport, InstructionCandidate, SemanticLedger, SemanticMatch
from ..source.markdown_ast import parse_markdown
from ..source.tokenizer import count_tokens


STACK_PATTERNS = {
    "python": r"\bpython\b|pyproject|pip install",
    "fastapi": r"\bfastapi\b|uvicorn",
    "django": r"\bdjango\b",
    "flask": r"\bflask\b",
    "postgres": r"\bpostgres(?:ql)?\b|psql",
    "sqlite": r"\bsqlite\b",
    "docker": r"\bdocker\b|docker compose",
    "pytest": r"\bpytest\b",
    "ruff": r"\bruff\b",
    "mypy": r"\bmypy\b",
    "node": r"\bnode\b|npm ",
    "react": r"\breact\b|vite|next\.js|nextjs",
    "typescript": r"\btypescript\b|\btsc\b|\.tsx\b",
    "eslint": r"\beslint\b",
    "playwright": r"\bplaywright\b",
    "pandas": r"\bpandas\b",
    "airflow": r"\bairflow\b",
    "dbt": r"\bdbt\b",
    "terraform": r"\bterraform\b",
}

FLOW_RULES = [
    ("read", "read_before_edit"),
    ("plan", "plan_before_edit"),
    ("minimal_change", "minimal_change"),
    ("lint", "lint_before_done"),
    ("typecheck", "typecheck_before_done"),
    ("test", "run_tests_before_done"),
    ("report", "report_changes"),
]
AGENT_INTENTS = {"agent_instruction", "testing_policy", "safety_policy"}
COMMAND_SEMANTICS = {
    "test": "run_tests_before_done",
    "lint": "lint_before_done",
    "typecheck": "typecheck_before_done",
    "build": "verify_build_before_done",
    "migrate": "validate_database_migrations",
}
CANONICAL_SIGNATURES = {
    "secrets_commit": ("commit", "secrets"),
    "prod_config_write": ("write", "production_config"),
    "deploy_without_approval": ("deploy", "approval"),
    "unsafe_migrations": ("run", "unsafe_migrations"),
    "schema_changes": ("change", "schema"),
    "destructive_ops": ("require", "destructive_operations"),
}


def _extract_scope(text: str) -> list[str]:
    values = set(re.findall(r"(?:^|[\s`])((?:src|tests|docs|app|packages|services|frontend|backend|infra|migrations)/)(?:[\s`]|$)", text, flags=re.M))
    return sorted(values)


def _extract_goal(text: str) -> list[str]:
    lowered = text.lower()
    goal: set[str] = set()
    if "maintain" in lowered or "improve" in lowered:
        goal.add("maintain_improve")
    if "backend" in lowered:
        goal.add("backend")
    if "frontend" in lowered:
        goal.add("frontend")
    if "data pipeline" in lowered:
        goal.add("data_pipeline")
    if "security" in lowered:
        goal.add("security")
    return sorted(goal)


def _extract_agent(text: str, adapter: str) -> str | None:
    lowered = text.lower()
    if adapter in {"readme", "contributing", "generic_markdown"}:
        return None
    if "backend" in lowered and "frontend" not in lowered:
        return "backend"
    if "frontend" in lowered and "backend" not in lowered:
        return "frontend"
    if "security" in lowered:
        return "security"
    if adapter in {"agents_md", "claude_md", "copilot_instructions", "cursor_rules"}:
        return "coding"
    return None


def _confidence_distribution(values: list[float]) -> dict[str, int]:
    buckets = {"high": 0, "medium": 0, "low": 0}
    for value in values:
        buckets["high" if value >= 0.8 else "medium" if value >= 0.6 else "low"] += 1
    return buckets


def rules_with_custom(rules_path: Path | None = None) -> list[SemanticRule]:
    return RULES + load_custom_rules(rules_path)


def _append_provenance(manifest: GlyphManifest, identifier: str, candidate: InstructionCandidate) -> None:
    hit = SourceHit(source=candidate.source, line=candidate.line, text=candidate.text)
    existing = manifest.provenance.setdefault(identifier, [])
    if hit not in existing:
        existing.append(hit)


def _policy_conflicts(manifest: GlyphManifest) -> list[ConflictFinding]:
    """Find incompatible modal categories over the same structured operation."""
    signatures: dict[tuple[str, str], list[tuple[str, str]]] = {}
    for policy in manifest.policies:
        signatures.setdefault(policy.operation_key(), []).append((policy.category, policy.id))
    for category in ("must", "deny", "ask"):
        for rule_id in getattr(manifest, category):
            signature = CANONICAL_SIGNATURES.get(rule_id)
            if signature:
                signatures.setdefault(signature, []).append((category, rule_id))
    findings: list[ConflictFinding] = []
    for (action, target), values in sorted(signatures.items()):
        categories = {category for category, _ in values}
        if len(categories) <= 1:
            continue
        findings.append(
            ConflictFinding(
                id=f"incompatible_policy_{action}_{target}".replace("/", "_"),
                semantic_units=sorted(identifier for _, identifier in values),
                source_texts=[],
                source_files=[],
                line_numbers=[],
                severity="high",
                suggested_fix=f"Resolve incompatible categories for {action} {target}: {', '.join(sorted(categories))}.",
            )
        )
    return findings


def _adapter_for(candidate: InstructionCandidate, adapters: dict[str, str]) -> str:
    return adapters.get(candidate.source, detect_adapter(candidate.source))


def _operational_candidates(candidates: list[InstructionCandidate], adapters: dict[str, str]) -> list[InstructionCandidate]:
    return [candidate for candidate in candidates if is_operational(candidate, _adapter_for(candidate, adapters))]


def _metrics(candidates: list[InstructionCandidate], resolutions: list[CandidateResolution], adapters: dict[str, str]) -> dict[str, object]:
    operational = _operational_candidates(candidates, adapters)
    destinations: dict[tuple[str, str | None, int | None], set[str]] = {}
    for resolution in resolutions:
        destinations.setdefault((resolution.candidate_id, resolution.source, resolution.line), set()).add(resolution.destination)

    def has(candidate: InstructionCandidate, *kinds: str) -> bool:
        return bool(destinations.get((candidate.id, candidate.source, candidate.line), set()) & set(kinds))

    canonical = sum(1 for candidate in operational if has(candidate, "canonical"))
    structured = sum(1 for candidate in operational if has(candidate, "canonical", "policy"))
    retained = sum(1 for candidate in operational if has(candidate, "canonical", "policy", "preserve"))
    dropped = [candidate for candidate in operational if has(candidate, "dropped")]
    # Kept for API compatibility with the pre-ledger inspection endpoint.  CI
    # limits use ``dropped_count`` exclusively; these candidates may be safely
    # represented by a policy or preserved directive.
    noncanonical = [candidate for candidate in operational if not has(candidate, "canonical")]
    high_risk = [candidate for candidate in operational if candidate.risk == "high" or classify_risk(candidate.text) == "high"]
    retained_high_risk = sum(1 for candidate in high_risk if has(candidate, "canonical", "policy", "preserve"))
    preserved = [candidate for candidate in operational if has(candidate, "preserve")]
    agent = [
        candidate
        for candidate in operational
        if candidate.intent in AGENT_INTENTS
        and (candidate.operational_confidence >= 0.4 or has(candidate, "canonical", "policy"))
    ]
    return {
        "canonical_candidate_coverage": _coverage(canonical, len(operational)),
        "structured_coverage": _coverage(structured, len(operational)),
        "retained_coverage": _coverage(retained, len(operational)),
        "safety_retention": _coverage(retained_high_risk, len(high_risk)),
        "preserved_count": len(preserved),
        "high_risk_preserved_count": sum(1 for candidate in preserved if candidate.risk == "high" or classify_risk(candidate.text) == "high"),
        "dropped_count": len(dropped),
        "dropped": dropped,
        "noncanonical": noncanonical,
        "agent_instruction_coverage": _coverage(sum(1 for candidate in agent if has(candidate, "canonical", "policy")), len(agent)),
        "operational_coverage": _coverage(structured, len(operational)),
    }


def _coverage(numerator: int, denominator: int) -> float:
    return 100.0 if denominator == 0 else (numerator / denominator) * 100


def _build_ledger(
    candidates: list[InstructionCandidate],
    commands: list[object],
    semantics: list[str],
    conflicts: list[ConflictFinding],
    resolutions: list[CandidateResolution],
    dropped: list[InstructionCandidate],
    adapters: dict[str, str],
) -> SemanticLedger:
    resolved_destinations: dict[tuple[str, str | None, int | None], set[str]] = {}
    for resolution in resolutions:
        resolved_destinations.setdefault((resolution.candidate_id, resolution.source, resolution.line), set()).add(resolution.destination)
    high_risk_fallbacks = [
        candidate
        for candidate in candidates
        if is_operational(candidate, _adapter_for(candidate, adapters))
        and (candidate.risk == "high" or classify_risk(candidate.text) == "high")
        and "canonical" not in resolved_destinations.get((candidate.id, candidate.source, candidate.line), set())
    ]
    return SemanticLedger(
        compressed_semantics=sorted(set(semantics)),
        commands=list(commands),
        repo_specific_candidates=[candidate for candidate in candidates if candidate.intent == "repo_convention"],
        product_requirements=[candidate for candidate in candidates if candidate.intent == "product_requirement"],
        implementation_requirements=[candidate for candidate in candidates if candidate.intent == "implementation_requirement"],
        api_contracts=[candidate for candidate in candidates if candidate.intent == "api_contract"],
        conditional_instructions=[candidate for candidate in candidates if candidate.intent == "conditional_instruction"],
        examples_or_references=[candidate for candidate in candidates if candidate.intent in {"example_content", "reference_content"}],
        non_operational_context=[candidate for candidate in candidates if candidate.intent == "non_operational_context"],
        # Compatibility diagnostics retain high-risk fallbacks here. CI loss
        # gates use ``dropped_candidates`` and never treat a preserve fallback
        # as silently unmapped.
        high_risk_unmapped=high_risk_fallbacks,
        resolutions=resolutions,
        operational_candidates=_operational_candidates(candidates, adapters),
        dropped_candidates=dropped,
        conflicts=conflicts,
    )


def _report(
    *,
    input_files: list[str],
    adapters: dict[str, str],
    source_text: str,
    manifest: GlyphManifest,
    candidates: list[InstructionCandidate],
    matches: list[SemanticMatch],
    commands: list[object],
    documents: list[object],
    conflicts: list[ConflictFinding],
    resolutions: list[CandidateResolution],
) -> ExtractionReport:
    metrics = _metrics(candidates, resolutions, adapters)
    markdown_tokens, tokenizer = count_tokens(source_text)
    glp_tokens, _ = count_tokens(render_glp(manifest))
    emitted = manifest.semantic_units()
    detected = {match.semantic_unit for match in matches}
    semantic_coverage = _coverage(len(detected & emitted), len(detected))
    dropped = list(metrics["dropped"])
    ledger = _build_ledger(candidates, commands, list(emitted), conflicts, resolutions, dropped, adapters)
    return ExtractionReport(
        input_files=input_files,
        adapters=adapters,
        markdown_tokens=markdown_tokens,
        glp_tokens=glp_tokens,
        tokenizer=tokenizer,
        semantic_units_detected=sorted(detected),
        semantic_units_emitted=sorted(emitted),
        commands_detected=manifest.commands,
        semantic_coverage=semantic_coverage,
        agent_instruction_coverage=float(metrics["agent_instruction_coverage"]),
        repo_specific_coverage=100.0,
        spec_classification_rate=100.0,
        operational_coverage=float(metrics["operational_coverage"]),
        # Compatibility field for diagnostics: unlike CI thresholds, it also
        # surfaces high-risk fallback clauses so older integrations can prompt
        # a review. ``dropped_count`` remains the authoritative loss metric.
        high_risk_unmapped_count=sum(1 for candidate in metrics["noncanonical"] if candidate.risk == "high" or classify_risk(candidate.text) == "high"),
        unmapped_operational_candidates=list(metrics["noncanonical"]),
        conflicts=conflicts,
        confidence_distribution=_confidence_distribution([match.confidence for match in matches]),
        token_reduction=0.0 if markdown_tokens == 0 else 1 - glp_tokens / markdown_tokens,
        matches=matches,
        command_candidates=commands,  # type: ignore[arg-type]
        documents=documents,  # type: ignore[arg-type]
        candidates=candidates,
        ledger=ledger,
        canonical_candidate_coverage=float(metrics["canonical_candidate_coverage"]),
        structured_coverage=float(metrics["structured_coverage"]),
        retained_coverage=float(metrics["retained_coverage"]),
        safety_retention=float(metrics["safety_retention"]),
        preserved_count=int(metrics["preserved_count"]),
        high_risk_preserved_count=int(metrics["high_risk_preserved_count"]),
        dropped_count=int(metrics["dropped_count"]),
    )


def analyze_text(text: str, source: str = "<memory>", adapter: str | None = None, rules_path: Path | None = None) -> tuple[GlyphManifest, ExtractionReport]:
    adapter_name = validate_adapter(adapter) or detect_adapter(source)
    doc = parse_markdown(text, source, adapter_name)
    custom_rules = load_custom_rules(rules_path)
    custom_policy_rules = load_custom_policy_rules(rules_path)
    candidates = extract_instruction_candidates(doc, include_classified=True)
    command_candidates = classify_commands(extract_command_candidates(doc))
    manifest = GlyphManifest(agent=_extract_agent(text, adapter_name), goal=_extract_goal(text))
    lowered = text.lower()
    manifest.stack = sorted(name for name, pattern in STACK_PATTERNS.items() if re.search(pattern, lowered))
    manifest.scope = _extract_scope(text)
    matches: list[SemanticMatch] = []
    resolutions: list[CandidateResolution] = []
    resolution_conflicts: list[ConflictFinding] = []

    for candidate in candidates:
        result = resolve_candidate(candidate, custom_policy_rules, custom_rules, RULES, adapter_name)
        matches.extend(result.matches)
        resolutions.extend(result.resolutions)
        resolution_conflicts.extend(result.conflicts)
        for match in result.matches:
            target = getattr(manifest, match.category)
            if match.semantic_unit not in target:
                target.append(match.semantic_unit)
            _append_provenance(manifest, match.semantic_unit, candidate)
        emitted_policies = [*([result.policy] if result.policy else []), *result.policies]
        for policy in emitted_policies:
            manifest.policies.append(policy)
            _append_provenance(manifest, policy.id, candidate)
        if result.preserved:
            manifest.preserved.append(result.preserved)
            _append_provenance(manifest, result.preserved.id, candidate)

    for command in command_candidates:
        label = command.label or "other"
        key = label
        if label == "other":
            key = "other" if "other" not in manifest.commands else f"other{len([item for item in manifest.commands if item.startswith('other')]) + 1}"
        if key not in manifest.commands:
            manifest.commands[key] = command.command
        if label in COMMAND_SEMANTICS:
            rule_id = COMMAND_SEMANTICS[label]
            if rule_id not in manifest.must:
                manifest.must.append(rule_id)
            hit = SourceHit(source=command.source, line=command.line, text=f"Detected cmd.{label} {command.command!r}")
            if hit not in manifest.provenance.setdefault(rule_id, []):
                manifest.provenance[rule_id].append(hit)

    for flow, rule_id in FLOW_RULES:
        if rule_id in manifest.semantic_units() and flow not in manifest.flow:
            manifest.flow.append(flow)
    for command_flow in ("test", "lint", "typecheck", "build"):
        if command_flow in manifest.commands and command_flow not in manifest.flow:
            manifest.flow.append(command_flow)
    conflicts = resolution_conflicts + detect_conflicts(matches) + _policy_conflicts(manifest)
    raw_lowered = text.lower()
    if "run tests" in raw_lowered and ("do not run tests" in raw_lowered or "skip tests" in raw_lowered):
        conflicts.append(ConflictFinding(id="testing_required_and_skipped", semantic_units=["run_tests_before_done"], source_texts=[text], source_files=[source], line_numbers=[1], severity="high", suggested_fix="Remove either the required testing rule or the skip-tests instruction."))
    manifest.conflicts = [conflict.id for conflict in conflicts]
    canonical_candidates = {
        (resolution.candidate_id, resolution.source, resolution.line)
        for resolution in resolutions
        if resolution.destination == "canonical"
    }
    manifest.unknown_operational = [
        candidate.text
        for candidate in candidates
        if is_operational(candidate, adapter_name) and (candidate.id, candidate.source, candidate.line) not in canonical_candidates
    ]
    manifest = manifest.sorted_copy()
    report = _report(
        input_files=[source],
        adapters={source: adapter_name},
        source_text=text,
        manifest=manifest,
        candidates=candidates,
        matches=matches,
        commands=command_candidates,
        documents=[doc],
        conflicts=conflicts,
        resolutions=resolutions,
    )
    return manifest, report


def analyze_files(paths: list[Path], adapter: str | None = None, rules_path: Path | None = None) -> tuple[GlyphManifest, ExtractionReport]:
    merged = GlyphManifest()
    reports: list[ExtractionReport] = []
    source_texts: list[str] = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        source_texts.append(text)
        current, report = analyze_text(text, str(path), adapter, rules_path)
        reports.append(report)
        merged.agent = merged.agent or current.agent
        for attr in ("goal", "stack", "scope", "flow", "must", "deny", "ask", "allow", "conflicts", "unknown_operational"):
            setattr(merged, attr, getattr(merged, attr) + getattr(current, attr))
        merged.policies.extend(current.policies)
        merged.preserved.extend(current.preserved)
        for key, value in current.commands.items():
            if key not in merged.commands:
                merged.commands[key] = value
        for key, hits in current.provenance.items():
            merged.provenance.setdefault(key, []).extend(hit for hit in hits if hit not in merged.provenance.get(key, []))
    merged = merged.sorted_copy()
    all_candidates = [candidate for report in reports for candidate in report.candidates]
    all_matches = [match for report in reports for match in report.matches]
    all_commands = [command for report in reports for command in report.command_candidates]
    all_docs = [document for report in reports for document in report.documents]
    all_resolutions = [resolution for report in reports for resolution in report.ledger.resolutions]
    conflicts = [conflict for report in reports for conflict in report.conflicts]
    combined = _report(
        input_files=[str(path) for path in paths],
        adapters={key: value for report in reports for key, value in report.adapters.items()},
        source_text="\n".join(source_texts),
        manifest=merged,
        candidates=all_candidates,
        matches=all_matches,
        commands=all_commands,
        documents=all_docs,
        conflicts=conflicts,
        resolutions=all_resolutions,
    )
    return merged, combined


def compile_text(text: str, source: str = "<memory>", adapter: str | None = None, rules_path: Path | None = None) -> GlyphManifest:
    return analyze_text(text, source, adapter, rules_path)[0]


def compile_files(paths: list[Path], adapter: str | None = None, rules_path: Path | None = None) -> GlyphManifest:
    return analyze_files(paths, adapter, rules_path)[0]


def extract_commands(text: str) -> dict[str, str]:
    return analyze_text(text)[0].commands


def expected_from_manifest(manifest: GlyphManifest) -> dict[str, object]:
    return {
        "semantic_units": sorted(manifest.semantic_units()),
        "commands": manifest.commands,
        "stack": manifest.stack,
        "policies": [policy.id for policy in manifest.policies],
        "preserved": [directive.id for directive in manifest.preserved],
    }
