from __future__ import annotations

import re

from ..core.models import LintWarning
from ..pipeline.compiler import analyze_text
from ..source.tokenizer import count_tokens


def lint_text(text: str, source: str = "<memory>", rules_path=None) -> list[LintWarning]:
    manifest, report = analyze_text(text, source, rules_path=rules_path)
    warnings: list[LintWarning] = []
    tokens, _ = count_tokens(text)
    density = len(manifest.semantic_units()) / max(tokens, 1)
    if tokens > 900 and density < 0.02:
        warnings.append(LintWarning(id="context_bloat", severity="medium", source=source, explanation="The file is long relative to detected operational semantics.", suggested_fix="Move background prose out of agent instructions or compile to .glp."))
    seen: dict[str, int] = {}
    for key, hits in manifest.provenance.items():
        seen[key] = len(hits)
    for key, count in seen.items():
        if count > 1:
            warnings.append(LintWarning(id="duplicate_instruction", severity="low", source=source, explanation=f"`{key}` appears in multiple wordings.", suggested_fix="Keep one canonical instruction or rely on the .glp semantic unit."))
    if manifest.conflicts:
        warnings.append(LintWarning(id="conflicting_instruction", severity="high", source=source, explanation="Opposing operational rules were detected.", suggested_fix="Remove the weaker or outdated instruction."))
    if re.search(r"\b(be careful|best judgment|do the right thing|use common sense)\b", text, re.I):
        warnings.append(LintWarning(id="vague_instruction", severity="low", source=source, explanation="The file contains vague non-operational guidance.", suggested_fix="Replace vague wording with concrete semantic rules."))
    if "test" not in manifest.commands:
        warnings.append(LintWarning(id="missing_test_command", severity="medium", source=source, explanation="No test command was detected.", suggested_fix="Add a concrete test command such as `pytest` or `npm test`."))
    if not ({"secrets_commit", "credentials_exposure", "api_key_exposure"} & manifest.semantic_units()):
        warnings.append(LintWarning(id="missing_safety_rules", severity="high", source=source, explanation="No secret or credential safety rule was detected.", suggested_fix="Add a deny rule for secrets and credentials."))
    if not ({"report_changes", "report_verification"} <= manifest.semantic_units()):
        warnings.append(LintWarning(id="missing_reporting_rules", severity="medium", source=source, explanation="Reporting expectations are incomplete.", suggested_fix="Add instructions to report changes and verification."))
    if len(re.findall(r"\b(spaces|tabs|semicolons|quotes|line length|trailing comma)\b", text, re.I)) > 4:
        warnings.append(LintWarning(id="lint_leakage", severity="low", source=source, explanation="The file contains low-level formatting rules better enforced by linters.", suggested_fix="Move formatting details to formatter/linter config."))
    if re.search(r"\b(how to write|learn|tutorial|algorithm|data structure)\b", text, re.I):
        warnings.append(LintWarning(id="skill_leakage", severity="low", source=source, explanation="The file appears to teach generic programming skills.", suggested_fix="Keep repository-specific operating instructions only."))
    if tokens > 1300:
        warnings.append(LintWarning(id="excessive_prose", severity="medium", source=source, explanation="The file contains substantial prose that may not be operational.", suggested_fix="Shorten explanations or move them to documentation."))
    if len(manifest.unknown_operational) >= 3:
        warnings.append(LintWarning(id="non_operational_content", severity="low", source=source, explanation="Some operational-looking sentences could not be classified.", suggested_fix="Rewrite them as concrete rules or commands."))
    if re.search(r"\bpython2|node 12|npm audit fix --force\b", text, re.I):
        warnings.append(LintWarning(id="stale_command", severity="medium", source=source, explanation="A potentially stale command was detected.", suggested_fix="Update or remove the command."))
    if re.search(r"\balways\b.*\b(any|all|everything)\b|\bnever\b.*\bany\b", text, re.I):
        warnings.append(LintWarning(id="overbroad_rule", severity="low", source=source, explanation="An overbroad rule may be hard to enforce.", suggested_fix="Scope the rule to concrete files, commands, or task types."))
    if ("destructive_without_approval" in manifest.conflicts) or re.search(r"destructive operations are allowed without approval", text, re.I) or (re.search(r"\b(rm -rf|drop database|terraform apply)\b", text, re.I) and "destructive_ops" not in manifest.ask):
        warnings.append(LintWarning(id="dangerous_permission", severity="high", source=source, explanation="Destructive operations are allowed or described without explicit approval.", suggested_fix="Add an ask rule for destructive_ops."))
    for candidate in report.unmapped_operational_candidates:
        warnings.append(LintWarning(id="unmapped_operational_instruction", severity="medium", source=candidate.source, line=candidate.line, explanation=f"Operational-looking instruction was not mapped: {candidate.text}", suggested_fix="Add a custom Glyph rule or rewrite as a known semantic instruction."))
    if report.operational_coverage < 85:
        warnings.append(LintWarning(id="low_operational_coverage", severity="medium", source=source, explanation=f"Operational coverage is {report.operational_coverage:.1f}%.", suggested_fix="Inspect unmapped candidates and add custom rules where useful."))
    return warnings


def warning_lines(warnings: list[LintWarning]) -> list[str]:
    lines: list[str] = []
    for warning in warnings:
        location = f" {warning.source}:{warning.line}" if warning.source and warning.line else f" {warning.source}" if warning.source else ""
        lines.extend([f"[{warning.severity}] {warning.id}{location}", warning.explanation, f"Suggested fix: {warning.suggested_fix}", ""])
    return lines
