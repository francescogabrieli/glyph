from __future__ import annotations

from ..source.document_ir import ConflictFinding, SemanticMatch

CONFLICT_PATTERNS = [
    ("testing_required_and_skipped", "run_tests_before_done", ["do not run tests", "skip tests"], "Remove either the required testing rule or the skip-tests instruction."),
    ("prod_config_conflict", "prod_config_write", ["may update production configuration directly", "update production configuration directly"], "Require approval for production configuration writes."),
    ("destructive_without_approval", "destructive_ops", ["do not ask for confirmation before deleting", "destructive operations are allowed without approval"], "Require approval for destructive operations."),
    ("large_refactor_conflict", "no_large_refactors", ["refactor broadly", "rewrite broadly", "whenever you see an opportunity"], "Keep refactor scope explicit and requested."),
]


def detect_conflicts(matches: list[SemanticMatch]) -> list[ConflictFinding]:
    findings: list[ConflictFinding] = []
    unit_matches = {match.semantic_unit: match for match in matches}
    all_text = " ".join(match.candidate.text.lower() for match in matches)
    for conflict_id, unit, phrases, fix in CONFLICT_PATTERNS:
        if unit in unit_matches and any(phrase in all_text for phrase in phrases):
            related = [match for match in matches if match.semantic_unit == unit or any(phrase in match.candidate.text.lower() for phrase in phrases)]
            findings.append(ConflictFinding(
                id=conflict_id,
                semantic_units=[unit],
                source_texts=[m.candidate.text for m in related],
                source_files=sorted({m.candidate.source for m in related}),
                line_numbers=sorted({m.candidate.line for m in related}),
                severity="high",
                suggested_fix=fix,
            ))
    return findings
