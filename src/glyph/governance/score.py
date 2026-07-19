from __future__ import annotations

from pathlib import Path

from ..formats.parser import parse_glp
from ..formats.renderer import render_glp
from ..pipeline.compiler import analyze_text
from ..source.tokenizer import count_tokens
from .lint import lint_text


def score_path(path: Path, rules_path: Path | None = None) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".glp" or text.lstrip().startswith(("glyph/0.1", "g/0.1", "glyph/0.2", "g/0.2")):
        manifest = parse_glp(text)
        markdown_tokens = count_tokens(text)[0]
        glp_tokens = markdown_tokens
        warnings = []
    else:
        manifest, extraction = analyze_text(text, str(path), rules_path=rules_path)
        markdown_tokens = count_tokens(text)[0]
        glp_tokens = count_tokens(render_glp(manifest))[0]
        warnings = lint_text(text, str(path))
    units = manifest.semantic_units()
    safety = 100 if {"secrets_commit", "destructive_ops"} <= units else 70 if units & {"secrets_commit", "credentials_exposure"} else 35
    testing = 100 if "run_tests_before_done" in units and "test" in manifest.commands else 75 if "run_tests_before_done" in units else 40
    reporting = 100 if {"report_changes", "report_verification"} <= units else 50
    conflict = 100 if not manifest.conflicts else 35
    clarity = min(100, 45 + len(units) * 5 + len(manifest.commands) * 4)
    bloat_penalty = 20 if markdown_tokens > 1500 else 10 if markdown_tokens > 900 else 0
    warning_weights = {
        "conflicting_instruction": 18,
        "dangerous_permission": 18,
        "missing_safety_rules": 16,
        "missing_test_command": 12,
        "low_operational_coverage": 12,
        "unmapped_operational_instruction": 4,
        "context_bloat": 10,
        "excessive_prose": 8,
    }
    lint_penalty = min(35, sum(warning_weights.get(warning.id, 3) for warning in warnings))
    if path.suffix != ".glp":
        lint_penalty += min(20, len(extraction.unmapped_operational_candidates) * 4)
    # Quality scoring rewards portable registry semantics more strongly than a
    # repository-specific policy fallback.  CI's operational/structured gate
    # remains available separately through ``glyph check``.
    op_cov = 100 if path.suffix == ".glp" else extraction.canonical_candidate_coverage
    overall = round((safety + testing + reporting + conflict + clarity + op_cov) / 6 - bloat_penalty - lint_penalty)
    reduction = 0 if markdown_tokens == 0 else (1 - glp_tokens / markdown_tokens) * 100
    return {
        "token_cost": markdown_tokens,
        "compression_potential": "high" if reduction >= 40 else "medium" if reduction >= 20 else "low",
        "semantic_clarity": clarity,
        "testing_coverage": testing,
        "safety_coverage": safety,
        "reporting_coverage": reporting,
        "conflict_risk": "low" if not manifest.conflicts else "high",
        "context_bloat": "high" if markdown_tokens > 1500 else "medium" if markdown_tokens > 900 else "low",
        "overall": max(0, min(100, overall)),
        "operational_coverage": round(op_cov),
    }


def badge(score: int) -> str:
    color = "brightgreen" if score >= 85 else "yellow" if score >= 70 else "orange" if score >= 50 else "red"
    return f"![Glyph score](https://img.shields.io/badge/glyph-{score}%2F100-{color})"
