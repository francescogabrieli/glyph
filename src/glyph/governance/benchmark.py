from __future__ import annotations

import json
from pathlib import Path

from ..core.models import CompressionProfile
from ..formats.renderer import render_glp
from ..pipeline.compiler import analyze_files
from ..pipeline.verifier import verify, verify_expected
from ..source.tokenizer import count_tokens
from .lint import lint_text

CANDIDATE_PATTERNS = ["AGENTS.md", "CLAUDE.md", ".github/copilot-instructions.md", ".cursorrules", ".cursor/rules/*.mdc", "README.md", "CONTRIBUTING.md", "docs/**/*.md"]
CASE_SOURCE_PATTERNS = ["AGENTS.md", "CLAUDE.md", ".github/copilot-instructions.md", ".cursorrules", ".cursor/rules/*.mdc", "README.md", "CONTRIBUTING.md"]


def discover_case_source(case_dir: Path) -> Path | None:
    for pattern in CASE_SOURCE_PATTERNS:
        matches = sorted(path for path in case_dir.glob(pattern) if path.is_file())
        if matches:
            return matches[0]
    return None


def _candidate_category(text: str) -> str:
    lowered = text.lower()
    if any(term in lowered for term in ["test", "pytest", "suite", "verify", "lint", "typecheck", "build"]):
        return "testing and verification"
    if any(term in lowered for term in ["secret", "credential", "token", "api key", ".env", "auth", "security"]):
        return "security and secrets"
    if any(term in lowered for term in ["database", "migration", "schema", "tenant", "sql"]):
        return "database and migrations"
    if "generated" in lowered or "snapshot" in lowered:
        return "generated files"
    if "api" in lowered or "breaking" in lowered:
        return "public API changes"
    if "dependency" in lowered or "package" in lowered or "lockfile" in lowered:
        return "dependency changes"
    if "docs" in lowered or "documentation" in lowered:
        return "documentation requirements"
    if "accessibility" in lowered or "a11y" in lowered or "aria" in lowered:
        return "accessibility requirements"
    if "pr" in lowered or "pull request" in lowered or "review" in lowered:
        return "PR/review workflow"
    if "deploy" in lowered or "release" in lowered or "production" in lowered:
        return "deployment and release safety"
    if "workspace" in lowered or "monorepo" in lowered or "boundary" in lowered:
        return "monorepo package boundaries"
    if any(term in lowered for term in ["agent", "tool", "inspect", "rules suggest"]):
        return "agent behavior / tool usage"
    return "common repository conventions"


def run_benchmark(root: Path, write_reports: bool = True) -> dict[str, object]:
    cases = []
    for case_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        md = discover_case_source(case_dir)
        expected = case_dir / "expected.json"
        if md is None or not expected.exists():
            continue
        manifest, extraction = analyze_files([md])
        glp = render_glp(manifest)
        (case_dir / "AGENTS.glp").write_text(glp, encoding="utf-8")
        md_tokens, tokenizer = count_tokens(md.read_text(encoding="utf-8"))
        glp_tokens, _ = count_tokens(glp)
        report = verify_expected(manifest, expected)
        readable_tokens, _ = count_tokens(render_glp(manifest, profile=CompressionProfile.readable))
        ultra_tokens, _ = count_tokens(render_glp(manifest, profile=CompressionProfile.ultra))
        profiles = {
            "readable": {"tokens": readable_tokens, "reduction": 0.0 if md_tokens == 0 else (1 - readable_tokens / md_tokens) * 100},
            "compact": {"tokens": glp_tokens, "reduction": 0.0 if md_tokens == 0 else (1 - glp_tokens / md_tokens) * 100},
            "ultra": {"tokens": ultra_tokens, "reduction": 0.0 if md_tokens == 0 else (1 - ultra_tokens / md_tokens) * 100},
        }
        best = min(profile["tokens"] for profile in profiles.values())
        dropped_categories: dict[str, int] = {}
        for candidate in extraction.ledger.dropped_candidates:
            category = _candidate_category(candidate.text)
            dropped_categories[category] = dropped_categories.get(category, 0) + 1
        cases.append({
            "name": case_dir.name,
            "case": case_dir.name,
            "source": str(md.relative_to(case_dir)),
            "input": str(md),
            "markdown_tokens": md_tokens,
            "glp_tokens": glp_tokens,
            "readable_tokens": readable_tokens,
            "compact_tokens": glp_tokens,
            "ultra_tokens": ultra_tokens,
            "profiles": profiles,
            "reduction": 0.0 if md_tokens == 0 else 1 - glp_tokens / md_tokens,
            "best_reduction": 0.0 if md_tokens == 0 else 1 - best / md_tokens,
            "coverage": report.coverage / 100,
            "semantic_coverage": report.coverage,
            "agent_instruction_coverage": extraction.agent_instruction_coverage / 100,
            "repo_specific_coverage": extraction.repo_specific_coverage / 100,
            "spec_classification_rate": extraction.spec_classification_rate / 100,
            "operational_coverage": extraction.operational_coverage / 100,
            "canonical_candidate_coverage": extraction.canonical_candidate_coverage / 100,
            "structured_coverage": extraction.structured_coverage / 100,
            "retained_coverage": extraction.retained_coverage / 100,
            "safety_retention": extraction.safety_retention / 100,
            "preserved_count": extraction.preserved_count,
            "high_risk_preserved_count": extraction.high_risk_preserved_count,
            "dropped_count": extraction.dropped_count,
            "high_risk_unmapped_count": extraction.high_risk_unmapped_count,
            "unmapped_count": extraction.dropped_count,
            "dropped_categories": dropped_categories,
            # Compatibility alias; release review uses dropped_count.
            "unmapped_categories": dropped_categories,
            "conflict_count": len(extraction.conflicts),
            "tokenizer": tokenizer,
            "missing_semantic_units": report.missing_semantic_units,
            "missing_commands": report.missing_commands,
            "missing_stack": report.missing_stack,
        })
    avg_reduction = sum(c["reduction"] for c in cases) / len(cases) if cases else 0
    avg_best_reduction = sum(c["best_reduction"] for c in cases) / len(cases) if cases else 0
    avg_coverage = sum(c["coverage"] for c in cases) / len(cases) if cases else 0
    avg_agent = sum(c["agent_instruction_coverage"] for c in cases) / len(cases) if cases else 0
    avg_repo = sum(c["repo_specific_coverage"] for c in cases) / len(cases) if cases else 0
    avg_spec = sum(c["spec_classification_rate"] for c in cases) / len(cases) if cases else 0
    avg_operational = sum(c["operational_coverage"] for c in cases) / len(cases) if cases else 0
    avg_structured = sum(c["structured_coverage"] for c in cases) / len(cases) if cases else 0
    avg_retained = sum(c["retained_coverage"] for c in cases) / len(cases) if cases else 0
    avg_safety_retention = sum(c["safety_retention"] for c in cases) / len(cases) if cases else 0
    tokenizer = cases[0]["tokenizer"] if cases else "fallback"
    profile_averages = {
        profile: sum(c["profiles"][profile]["reduction"] for c in cases) / len(cases) if cases else 0
        for profile in ["readable", "compact", "ultra"]
    }
    top_categories: dict[str, int] = {}
    for case in cases:
        for category, count in case["dropped_categories"].items():
            top_categories[category] = top_categories.get(category, 0) + count
    result = {
        "summary": {
            "cases": len(cases),
            "average_semantic_coverage": avg_coverage * 100,
            "average_agent_instruction_coverage": avg_agent * 100,
            "average_repo_specific_coverage": avg_repo * 100,
            "average_spec_classification_rate": avg_spec * 100,
            "average_operational_coverage": avg_operational * 100,
            "average_structured_coverage": avg_structured * 100,
            "average_retained_coverage": avg_retained * 100,
            "average_safety_retention": avg_safety_retention * 100,
            "average_best_reduction": avg_best_reduction * 100,
            "average_reduction_by_profile": profile_averages,
            "preserved_count": sum(c["preserved_count"] for c in cases),
            "high_risk_preserved_count": sum(c["high_risk_preserved_count"] for c in cases),
            "dropped_count": sum(c["dropped_count"] for c in cases),
            "average_preserved_count": sum(c["preserved_count"] for c in cases) / len(cases) if cases else 0,
            "average_high_risk_preserved_count": sum(c["high_risk_preserved_count"] for c in cases) / len(cases) if cases else 0,
            "average_dropped_count": sum(c["dropped_count"] for c in cases) / len(cases) if cases else 0,
            # Compatibility diagnostics; these are not release gates.
            "high_risk_unmapped_count": sum(c["high_risk_unmapped_count"] for c in cases),
            "unmapped_count": sum(c["dropped_count"] for c in cases),
            "conflict_count": sum(c["conflict_count"] for c in cases),
            "top_dropped_categories": dict(sorted(top_categories.items(), key=lambda item: (-item[1], item[0]))[:8]),
            "top_unmapped_categories": dict(sorted(top_categories.items(), key=lambda item: (-item[1], item[0]))[:8]),
            "tokenizer": tokenizer,
        },
        "cases": cases,
        "average_reduction": avg_reduction,
        "average_best_reduction": avg_best_reduction,
        "average_coverage": avg_coverage,
        "average_agent_instruction_coverage": avg_agent,
        "average_repo_specific_coverage": avg_repo,
        "average_spec_classification_rate": avg_spec,
        "average_operational_coverage": avg_operational,
        "average_structured_coverage": avg_structured,
        "average_retained_coverage": avg_retained,
        "average_safety_retention": avg_safety_retention,
        "preserved_count": sum(c["preserved_count"] for c in cases),
        "high_risk_preserved_count": sum(c["high_risk_preserved_count"] for c in cases),
        "dropped_count": sum(c["dropped_count"] for c in cases),
        "high_risk_unmapped_count": sum(c["high_risk_unmapped_count"] for c in cases),
    }
    if write_reports:
        (root / "benchmark-report.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (root / "benchmark-report.md").write_text(markdown_report(result), encoding="utf-8")
    return result


def markdown_report(result: dict[str, object]) -> str:
    cases = result["cases"]
    summary = result.get("summary", {})
    lines = ["# Glyph benchmark", ""]
    if isinstance(summary, dict):
        lines += [
            "## Summary",
            "",
            f"- Cases: {summary.get('cases', len(cases))}",
            f"- Tokenizer: {summary.get('tokenizer', 'fallback')}",
            f"- Average best-profile reduction: {summary.get('average_best_reduction', 0):.1f}%",
            "### Post-hardening metrics",
            "",
            f"- Average structured coverage: {summary.get('average_structured_coverage', 0):.1f}%",
            f"- Average retained coverage: {summary.get('average_retained_coverage', 0):.1f}%",
            f"- Average safety retention: {summary.get('average_safety_retention', 0):.1f}%",
            f"- Preserved directives: {summary.get('preserved_count', 0)}",
            f"- High-risk preserved directives: {summary.get('high_risk_preserved_count', 0)}",
            f"- Dropped candidates: {summary.get('dropped_count', 0)}",
            "",
            "### Compatibility diagnostics",
            "",
            f"- Legacy semantic coverage: {summary.get('average_semantic_coverage', 0):.1f}%",
            f"- Legacy high-risk unmapped count: {summary.get('high_risk_unmapped_count', 0)}",
            f"- Average agent instruction coverage: {summary.get('average_agent_instruction_coverage', 0):.1f}%",
            f"- Average repo-specific coverage: {summary.get('average_repo_specific_coverage', 0):.1f}%",
            f"- Average spec classification rate: {summary.get('average_spec_classification_rate', 0):.1f}%",
            f"- Average operational coverage: {summary.get('average_operational_coverage', 0):.1f}%",
            f"- Legacy unmapped count: {summary.get('unmapped_count', 0)}",
            f"- Conflicts: {summary.get('conflict_count', 0)}",
            "",
            "## Average Reduction By Profile",
            "",
        ]
        for profile, value in summary.get("average_reduction_by_profile", {}).items():
            lines.append(f"- {profile}: {value:.1f}%")
        lines += ["", "## Top Dropped Candidate Categories (compatibility alias: Top Unmapped Categories)", ""]
        if summary.get("top_dropped_categories"):
            for category, count in summary["top_dropped_categories"].items():
                lines.append(f"- {category}: {count}")
        else:
            lines.append("- None (no candidates were dropped).")
        lines.append("")
    lines += ["## Cases", "", "| case | source | md tokens | readable | compact | ultra | best reduction | structured | retained | safety | preserved | high-risk preserved | dropped | conflicts | semantic (diag) | high-risk unmapped (diag) |", "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for case in cases:  # type: ignore[assignment]
        lines.append(f"| {case['case']} | {case['source']} | {case['markdown_tokens']} | {case['readable_tokens']} | {case['compact_tokens']} | {case['ultra_tokens']} | {case['best_reduction'] * 100:.1f}% | {case['structured_coverage'] * 100:.1f}% | {case['retained_coverage'] * 100:.1f}% | {case['safety_retention'] * 100:.1f}% | {case['preserved_count']} | {case['high_risk_preserved_count']} | {case['dropped_count']} | {case['conflict_count']} | {case.get('semantic_coverage', case['coverage'] * 100):.1f}% | {case.get('high_risk_unmapped_count', 0)} |")
    lines += ["", "## Per-case Notes", ""]
    for case in cases:  # type: ignore[assignment]
        note = "No conflicts"
        if case["dropped_count"]:
            categories = ", ".join(f"{key} ({value})" for key, value in case.get("dropped_categories", {}).items())
            note = f"{case['dropped_count']} dropped candidates: {categories}"
        elif case["preserved_count"]:
            note = f"{case['preserved_count']} preserved directives"
        if case["conflict_count"]:
            note += f"; {case['conflict_count']} conflicts"
        lines.append(f"- {case['case']}: {note}.")
    return "\n".join(lines) + "\n"


def discover_real(root: Path, patterns: list[str] | None = None) -> list[Path]:
    found: list[Path] = []
    for pattern in patterns or CANDIDATE_PATTERNS:
        found.extend(path for path in root.glob(pattern) if path.is_file() and ".venv" not in path.parts and ".git" not in path.parts)
    return sorted(set(found))


def benchmark_real(root: Path, patterns: list[str] | None = None, write: bool = False) -> dict[str, object]:
    files = discover_real(root, patterns)
    rows = []
    for path in files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        manifest, extraction = analyze_files([path])
        glp = render_glp(manifest)
        if write:
            path.with_suffix(path.suffix + ".glp").write_text(glp, encoding="utf-8")
        md_tokens, tokenizer = count_tokens(text)
        glp_tokens, _ = count_tokens(glp)
        verification = verify(text, manifest, source=str(path))
        warnings = lint_text(text, str(path))
        rows.append({
            "file": str(path),
            "markdown_tokens": md_tokens,
            "glp_tokens": glp_tokens,
            "reduction": 0 if md_tokens == 0 else 1 - glp_tokens / md_tokens,
            "coverage": verification.coverage / 100,
            "agent_instruction_coverage": extraction.agent_instruction_coverage / 100,
            "repo_specific_coverage": extraction.repo_specific_coverage / 100,
            "spec_classification_rate": extraction.spec_classification_rate / 100,
            "operational_coverage": extraction.operational_coverage / 100,
            "canonical_candidate_coverage": extraction.canonical_candidate_coverage / 100,
            "structured_coverage": extraction.structured_coverage / 100,
            "retained_coverage": extraction.retained_coverage / 100,
            "safety_retention": extraction.safety_retention / 100,
            "preserved_count": extraction.preserved_count,
            "high_risk_preserved_count": extraction.high_risk_preserved_count,
            "dropped_count": extraction.dropped_count,
            "high_risk_unmapped_count": extraction.high_risk_unmapped_count,
            "unmapped_count": extraction.dropped_count,
            "candidate_breakdown": {
                "mapped_agent_instructions": len({(m.candidate.source, m.candidate.line, m.candidate.text) for m in extraction.matches}),
                "repo_specific": len(extraction.ledger.repo_specific_candidates),
                "product_requirements": len(extraction.ledger.product_requirements),
                "implementation_requirements": len(extraction.ledger.implementation_requirements),
                "api_contracts": len(extraction.ledger.api_contracts),
                "conditional_instructions": len(extraction.ledger.conditional_instructions),
                "examples_or_references": len(extraction.ledger.examples_or_references),
                "non_operational_context": len(extraction.ledger.non_operational_context),
                "high_risk_unmapped": len(extraction.ledger.high_risk_unmapped),
            },
            "lint_smells": [w.id for w in warnings],
            "tokenizer": tokenizer,
        })
    return {
        "files_discovered": len(files),
        "files_compiled": len(rows),
        "files": rows,
        "average_reduction": sum(r["reduction"] for r in rows) / len(rows) if rows else 0,
        "average_coverage": sum(r["coverage"] for r in rows) / len(rows) if rows else 0,
        "average_agent_instruction_coverage": sum(r["agent_instruction_coverage"] for r in rows) / len(rows) if rows else 0,
        "average_repo_specific_coverage": sum(r["repo_specific_coverage"] for r in rows) / len(rows) if rows else 0,
        "average_spec_classification_rate": sum(r["spec_classification_rate"] for r in rows) / len(rows) if rows else 0,
        "average_operational_coverage": sum(r["operational_coverage"] for r in rows) / len(rows) if rows else 0,
        "average_structured_coverage": sum(r["structured_coverage"] for r in rows) / len(rows) if rows else 0,
        "average_retained_coverage": sum(r["retained_coverage"] for r in rows) / len(rows) if rows else 0,
        "average_safety_retention": sum(r["safety_retention"] for r in rows) / len(rows) if rows else 0,
        "preserved_count": sum(r["preserved_count"] for r in rows),
        "high_risk_preserved_count": sum(r["high_risk_preserved_count"] for r in rows),
        "dropped_count": sum(r["dropped_count"] for r in rows),
        "average_preserved_count": sum(r["preserved_count"] for r in rows) / len(rows) if rows else 0,
        "average_high_risk_preserved_count": sum(r["high_risk_preserved_count"] for r in rows) / len(rows) if rows else 0,
        "average_dropped_count": sum(r["dropped_count"] for r in rows) / len(rows) if rows else 0,
        # Compatibility diagnostic; release review uses the post-hardening counts.
        "high_risk_unmapped_count": sum(r["high_risk_unmapped_count"] for r in rows),
    }
