"""Produce sanitized, reproducible metadata for a pinned external corpus sweep."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from glyph.formats.renderer import render_glp  # noqa: E402
from glyph.governance.benchmark import discover_real  # noqa: E402
from glyph.pipeline.compiler import analyze_files  # noqa: E402
from glyph.pipeline.verifier import verify  # noqa: E402
from glyph.source.adapters import detect_adapter  # noqa: E402
from glyph.source.tokenizer import count_tokens  # noqa: E402


AGENT_ADAPTERS = {"agents_md", "claude_md", "copilot_instructions", "cursor_rules"}
TRIAGE_CLASSES = (
    "parser/classifier bug",
    "policy extraction bug",
    "correct preserved blocker",
    "false-positive operational candidate",
    "non-operational documentation",
    "repo-specific custom rule candidate",
    "unsupported conditional pattern",
    "conflict requiring human review",
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _repo_sha(repo: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()


def _source_files(repo: Path) -> list[Path]:
    return sorted(discover_real(repo), key=lambda path: path.relative_to(repo).as_posix())


def _triage(candidate: Any, *, agent_specific: bool, conflict: bool = False) -> str:
    """Classify surfaced failures without retaining their source text."""
    if conflict:
        return "conflict requiring human review"
    if candidate.intent == "repo_convention":
        return "repo-specific custom rule candidate"
    if candidate.intent == "conditional_instruction":
        return "unsupported conditional pattern"
    if candidate.intent in {"product_requirement", "implementation_requirement", "api_contract", "non_operational_context", "example_content", "reference_content"}:
        return "non-operational documentation"
    if candidate.operational_confidence < 0.3:
        return "false-positive operational candidate"
    if not agent_specific and candidate.intent in {"safety_policy", "testing_policy", "release_policy"}:
        return "non-operational documentation"
    if candidate.intent in {"safety_policy", "testing_policy", "release_policy"}:
        return "policy extraction bug"
    if candidate.intent in {"agent_instruction", "command_instruction"}:
        return "correct preserved blocker"
    return "parser/classifier bug"


def _sanitized_derivation(resolution: Any | None) -> dict[str, Any]:
    return {
        "shape": getattr(resolution, "policy_shape", None) or "unresolved",
        "subject_available": bool(getattr(resolution, "subject_available", False)),
        "predicate_kind": getattr(resolution, "predicate_kind", None),
        "object_cardinality": int(getattr(resolution, "object_cardinality", 0)),
        "operators": sorted(getattr(resolution, "operators", []) or []),
        "attachment": getattr(resolution, "attachment", None),
        "ambiguous": bool(getattr(resolution, "ambiguous", False)),
        "reason_code": getattr(resolution, "reason_code", "") or "unclassified",
        "outcome": getattr(resolution, "destination", "unknown"),
    }


def _taxonomy_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: dict[str, tuple[dict[str, Any], int]] = {}
    for row in rows:
        derivation = row["derivation"]
        key = json.dumps(derivation, sort_keys=True, separators=(",", ":"))
        previous = counts.get(key)
        counts[key] = (derivation, 1 if previous is None else previous[1] + 1)
    return [dict(derivation, count=count) for derivation, count in sorted(counts.values(), key=lambda item: json.dumps(item[0], sort_keys=True))]


def _row(repo_entry: dict[str, Any], repo: Path, path: Path, pinned_sha: str) -> dict[str, Any]:
    raw = path.read_bytes()
    text = raw.decode("utf-8", errors="replace")
    relative_path = path.relative_to(repo).as_posix()
    adapter = detect_adapter(relative_path)
    manifest, extraction = analyze_files([path])
    first = render_glp(manifest)
    second_manifest, second_extraction = analyze_files([path])
    second = render_glp(second_manifest)
    markdown_tokens, tokenizer = count_tokens(text)
    glp_tokens, _ = count_tokens(first)
    verification = verify(text, manifest)
    agent_specific = adapter in AGENT_ADAPTERS
    destinations: dict[tuple[str, str | None, int | None], set[str]] = {}
    resolutions_by_candidate: dict[tuple[str, str | None, int | None], list[Any]] = {}
    for resolution in extraction.ledger.resolutions:
        key = (resolution.candidate_id, resolution.source, resolution.line)
        destinations.setdefault(key, set()).add(resolution.destination)
        resolutions_by_candidate.setdefault(key, []).append(resolution)
    candidate_failures: list[dict[str, Any]] = []
    high_risk_taxonomy: list[dict[str, Any]] = []
    for candidate in extraction.candidates:
        key = (candidate.id, candidate.source, candidate.line)
        candidate_destinations = destinations.get(key, set())
        candidate_resolutions = resolutions_by_candidate.get(key, [])
        primary_resolution = sorted(candidate_resolutions, key=lambda item: (item.destination, item.policy_id or item.canonical_id or item.preserve_id or ""))[0] if candidate_resolutions else None
        if candidate.risk == "high":
            high_risk_taxonomy.append({
                "candidate_id": _sha256(candidate.text.encode("utf-8")),
                "derivation": _sanitized_derivation(primary_resolution),
            })
        if not ({"preserve", "dropped"} & candidate_destinations):
            continue
        candidate_failures.append(
            {
                "candidate_id": _sha256(candidate.text.encode("utf-8")),
                "line": candidate.line,
                "intent": candidate.intent,
                "classification": _triage(candidate, agent_specific=agent_specific, conflict=bool(extraction.conflicts)),
                "high_risk": candidate.risk == "high",
                "destination": "dropped" if "dropped" in candidate_destinations else "preserve",
                "derivation": _sanitized_derivation(primary_resolution),
            }
        )
    blockers: list[str] = []
    if first != second:
        blockers.append("non_deterministic_output")
    if extraction.retained_coverage < 100:
        blockers.append("retained_coverage_below_100")
    if extraction.safety_retention < 100:
        blockers.append("safety_retention_below_100")
    if extraction.dropped_count:
        blockers.append("dropped_candidates_present")
    if extraction.high_risk_preserved_count:
        blockers.append("high_risk_preserved_requires_review")
    if agent_specific and extraction.agent_instruction_coverage < 90:
        blockers.append("agent_instruction_coverage_below_90")
    if agent_specific and extraction.operational_coverage < 80:
        blockers.append("operational_coverage_below_80")
    return {
        "repository": repo_entry["name"],
        "pinned_sha": pinned_sha,
        "source_url": repo_entry["source_url"],
        "license": repo_entry.get("license", "unknown"),
        "path": relative_path,
        "sha256": _sha256(raw),
        "file_size_bytes": len(raw),
        "markdown_tokens": markdown_tokens,
        "glp_tokens": glp_tokens,
        "token_counts": {"markdown": markdown_tokens, "glp": glp_tokens},
        "token_reduction": 0.0 if markdown_tokens == 0 else 1 - glp_tokens / markdown_tokens,
        "reduction": 0.0 if markdown_tokens == 0 else 1 - glp_tokens / markdown_tokens,
        "tokenizer": tokenizer,
        "adapter": adapter,
        "agent_specific": agent_specific,
        "deterministic": first == second,
        "semantic_coverage": verification.coverage,
        "canonical_candidate_coverage": extraction.canonical_candidate_coverage,
        "structured_coverage": extraction.structured_coverage,
        "retained_coverage": extraction.retained_coverage,
        "safety_retention": extraction.safety_retention,
        "preserved_count": extraction.preserved_count,
        "high_risk_preserved_count": extraction.high_risk_preserved_count,
        "dropped_count": extraction.dropped_count,
        "agent_instruction_coverage": extraction.agent_instruction_coverage,
        "operational_coverage": extraction.operational_coverage,
        "conflicts": sorted(conflict.id for conflict in extraction.conflicts),
        "conflict_count": len(extraction.conflicts),
        "high_risk_unmapped": extraction.high_risk_unmapped_count,
        "failure_triage": candidate_failures,
        "high_risk_taxonomy": high_risk_taxonomy,
        "review_status": "pass" if not blockers else "review_required",
        "findings": blockers,
    }


def sweep(manifest_path: Path, checkouts: Path) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    repositories: list[dict[str, Any]] = []
    for entry in manifest["repositories"]:
        repo = checkouts / entry["name"]
        if not repo.is_dir():
            raise FileNotFoundError(f"missing checkout for {entry['name']}")
        actual_sha = _repo_sha(repo)
        if actual_sha != entry["sha"]:
            raise ValueError(f"pinned SHA mismatch for {entry['name']}: {actual_sha}")
        files = [_row(entry, repo, path, actual_sha) for path in _source_files(repo)]
        agent_files = [repo / row["path"] for row in files if row["agent_specific"]]
        multi_input: dict[str, Any] = {"applicable": len(agent_files) > 1}
        if len(agent_files) > 1:
            combined_manifest, _ = analyze_files(agent_files)
            repeated_manifest, _ = analyze_files(agent_files)
            combined = render_glp(combined_manifest)
            repeated = render_glp(repeated_manifest)
            multi_input.update({"input_count": len(agent_files), "deterministic": combined == repeated, "sha256": _sha256(combined.encode("utf-8"))})
        repositories.append({
            "name": entry["name"],
            "source_url": entry["source_url"],
            "sha": actual_sha,
            "license": entry["license"],
            "files": files,
            "multi_input": multi_input,
        })
    all_files = [row for repo in repositories for row in repo["files"]]
    agent_files = [row for row in all_files if row["agent_specific"]]
    triage_counts: dict[str, int] = {}
    for row in all_files:
        for finding in row["failure_triage"]:
            key = finding["classification"]
            triage_counts[key] = triage_counts.get(key, 0) + 1
    triage_counts = {key: triage_counts.get(key, 0) for key in TRIAGE_CLASSES}
    high_risk_rows = [item for row in all_files for item in row["high_risk_taxonomy"]]
    agent_structured = [row["agent_instruction_coverage"] for row in agent_files]
    agent_operational = [row["operational_coverage"] for row in agent_files]
    multi_input_failures = sum(
        not repo["multi_input"].get("deterministic", True)
        for repo in repositories
        if repo["multi_input"].get("applicable")
    )
    gate = {
        "zero_crashes": True,
        "zero_non_determinisms": sum(not row["deterministic"] for row in all_files) + multi_input_failures == 0,
        "retained_coverage_100": all(row["retained_coverage"] >= 100 for row in all_files),
        "safety_retention_100": all(row["safety_retention"] >= 100 for row in all_files),
        "dropped_count_0": sum(row["dropped_count"] for row in all_files) == 0,
        "high_risk_preserved_count_0": sum(row["high_risk_preserved_count"] for row in all_files) == 0,
        "structured_agent_instruction_coverage_gte_90": (sum(agent_structured) / len(agent_structured) if agent_structured else 100) >= 90,
        "structured_operational_coverage_gte_80": (sum(agent_operational) / len(agent_operational) if agent_operational else 100) >= 80,
    }
    return {
        "schema_version": 2,
        "scope": "Metadata-only static sweep. No third-party source text, local checkout path, generated manifest text, or raw inspection output is included.",
        "gate": gate,
        "repositories": repositories,
        "summary": {
            "repositories": len(repositories),
            "files": len(all_files),
            "agent_specific_files": len(agent_files),
            "determinism_failures": sum(not row["deterministic"] for row in all_files) + multi_input_failures,
            "review_required": sum(row["review_status"] == "review_required" for row in all_files),
            "high_risk_unmapped": sum(row["high_risk_unmapped"] for row in all_files),
            "average_token_reduction": sum(row["token_reduction"] for row in all_files) / len(all_files) if all_files else 0.0,
            "minimum_token_reduction": min((row["token_reduction"] for row in all_files), default=0.0),
            "negative_reduction_files": sum(row["token_reduction"] < 0 for row in all_files),
            "average_structured_coverage": sum(row["structured_coverage"] for row in all_files) / len(all_files) if all_files else 100.0,
            "minimum_structured_coverage": min((row["structured_coverage"] for row in all_files), default=100.0),
            "average_retained_coverage": sum(row["retained_coverage"] for row in all_files) / len(all_files) if all_files else 100.0,
            "minimum_retained_coverage": min((row["retained_coverage"] for row in all_files), default=100.0),
            "average_safety_retention": sum(row["safety_retention"] for row in all_files) / len(all_files) if all_files else 100.0,
            "minimum_safety_retention": min((row["safety_retention"] for row in all_files), default=100.0),
            "preserved_count": sum(row["preserved_count"] for row in all_files),
            "high_risk_preserved_count": sum(row["high_risk_preserved_count"] for row in all_files),
            "dropped_count": sum(row["dropped_count"] for row in all_files),
            "average_canonical_candidate_coverage": sum(row["canonical_candidate_coverage"] for row in all_files) / len(all_files) if all_files else 100.0,
            "average_agent_instruction_coverage": sum(row["agent_instruction_coverage"] for row in agent_files) / len(agent_files) if agent_files else 100.0,
            "minimum_agent_instruction_coverage": min(agent_structured, default=100.0),
            "average_operational_coverage": sum(row["operational_coverage"] for row in agent_files) / len(agent_files) if agent_files else 100.0,
            "minimum_operational_coverage": min(agent_operational, default=100.0),
            "conflict_count": sum(row["conflict_count"] for row in all_files),
            "triage_counts": dict(sorted(triage_counts.items())),
            "high_risk_candidate_count": len(high_risk_rows),
            "high_risk_taxonomy": _taxonomy_summary(high_risk_rows),
        },
    }


def markdown_report(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = ["# Glyph v0.2 external corpus sweep", "", "This is a metadata-only, reproducible static sweep. It does not redistribute third-party instruction files.", "", "## Gate", "", "| Criterion | Result |", "| --- | --- |"]
    for criterion, passed in report["gate"].items():
        lines.append(f"| {criterion} | {'PASS' if passed else 'FAIL'} |")
    lines += ["", "## Summary", ""]
    lines += [
        f"- Repositories: {summary['repositories']}",
        f"- Files compiled: {summary['files']}",
        f"- Agent-specific files: {summary['agent_specific_files']}",
        f"- Determinism failures: {summary['determinism_failures']}",
        f"- Files requiring review: {summary['review_required']}",
        f"- Structured coverage: {summary['average_structured_coverage']:.1f}% average; {summary['minimum_structured_coverage']:.1f}% minimum",
        f"- Retained coverage: {summary['average_retained_coverage']:.1f}% average; {summary['minimum_retained_coverage']:.1f}% minimum",
        f"- Safety retention: {summary['average_safety_retention']:.1f}% average; {summary['minimum_safety_retention']:.1f}% minimum",
        f"- Preserved directives: {summary['preserved_count']}",
        f"- High-risk preserved directives: {summary['high_risk_preserved_count']}",
        f"- Dropped candidates: {summary['dropped_count']}",
        f"- Canonical candidate coverage: {summary['average_canonical_candidate_coverage']:.1f}% average",
        f"- Agent-instruction coverage: {summary['average_agent_instruction_coverage']:.1f}% average; {summary['minimum_agent_instruction_coverage']:.1f}% minimum",
        f"- Structured operational coverage: {summary['average_operational_coverage']:.1f}% average; {summary['minimum_operational_coverage']:.1f}% minimum",
        f"- Token reduction: {summary['average_token_reduction'] * 100:.1f}% average; {summary['minimum_token_reduction'] * 100:.1f}% minimum; {summary['negative_reduction_files']} negative files",
        "",
        "## Repositories",
        "",
        "| Repository | SHA | License | Files | Review required |",
        "| --- | --- | --- | ---: | ---: |",
    ]
    for repo in report["repositories"]:
        review = sum(row["review_status"] == "review_required" for row in repo["files"])
        lines.append(f"| [{repo['name']}]({repo['source_url']}) | `{repo['sha']}` | {repo['license']} | {len(repo['files'])} | {review} |")
    lines += ["", "## Per-file metadata", "", "| Repository | Path | Adapter | Tokens (Markdown → GLP) | Reduction | Structured | Retained | Safety | Preserved | High-risk preserved | Dropped | Conflicts | Status |", "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |"]
    for repo in report["repositories"]:
        for row in repo["files"]:
            lines.append(f"| {repo['name']} | `{row['path']}` | {row['adapter']} | {row['markdown_tokens']} → {row['glp_tokens']} | {row['token_reduction'] * 100:.1f}% | {row['structured_coverage']:.1f}% | {row['retained_coverage']:.1f}% | {row['safety_retention']:.1f}% | {row['preserved_count']} | {row['high_risk_preserved_count']} | {row['dropped_count']} | {row['conflict_count']} | {row['review_status']} |")
    lines += ["", "## Failure triage", ""]
    for classification, count in summary["triage_counts"].items():
        lines.append(f"- {classification}: {count}")
    lines += ["", "## Sanitized high-risk taxonomy", "", f"High-risk operational candidates: {summary['high_risk_candidate_count']}", "", "| Shape | Predicate | Objects | Operators | Attachment | Ambiguous | Reason | Outcome | Count |", "| --- | --- | ---: | --- | --- | --- | --- | --- | ---: |"]
    for row in summary["high_risk_taxonomy"]:
        lines.append(f"| {row['shape']} | {row['predicate_kind'] or '-'} | {row['object_cardinality']} | {', '.join(row['operators']) or '-'} | {row['attachment'] or '-'} | {str(row['ambiguous']).lower()} | {row['reason_code']} | {row['outcome']} | {row['count']} |")
    lines += ["", "Individual finding metadata (a stable text hash, line, intent, risk marker, destination, classification, and sanitized derivation) is retained in the JSON report without storing third-party instruction text.", "", "## Method", "", "Every discovered supported file was adapter-detected, compiled twice for byte-level determinism, inspected through the post-hardening extraction metrics, and measured. Repositories with multiple agent-specific instruction files were also compiled as a single multi-input manifest. Low or negative reductions are retained per file and are not clamped.", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--checkouts", type=Path, required=True)
    parser.add_argument("--json-out", type=Path, required=True)
    parser.add_argument("--markdown-out", type=Path, required=True)
    args = parser.parse_args()
    report = sweep(args.manifest, args.checkouts)
    args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown_out.write_text(markdown_report(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
