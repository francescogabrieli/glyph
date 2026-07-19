from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .. import __version__
from ..formats.renderer import render_glp
from ..pipeline.compiler import analyze_files
from ..source.tokenizer import count_tokens


def create_lock(paths: list[Path], rules_path: Path | None = None) -> dict[str, object]:
    manifest, report = analyze_files(paths, rules_path=rules_path)
    source_text = "\n".join(path.read_text(encoding="utf-8") for path in paths)
    rules_text = rules_path.read_text(encoding="utf-8") if rules_path else ""
    glp = render_glp(manifest)
    md_tokens, tokenizer = count_tokens(source_text)
    glp_tokens, _ = count_tokens(glp)
    checksum = hashlib.sha256((source_text + "\n---rules---\n" + rules_text + "\n---glp---\n" + glp).encode("utf-8")).hexdigest()
    return {
        "schema": "glyph-lock/v3",
        "version": __version__,
        "manifest_version": manifest.version,
        "inputs": [str(path) for path in paths],
        "rules": {
            "path": str(rules_path) if rules_path else None,
            "sha256": hashlib.sha256(rules_text.encode("utf-8")).hexdigest() if rules_path else None,
        },
        "semantic_units": sorted(manifest.semantic_units()),
        "allow": manifest.allow,
        "commands": manifest.commands,
        "stack": manifest.stack,
        "policies": [policy.model_dump() for policy in manifest.policies],
        "policy_fingerprints": {policy.id: policy.fingerprint() for policy in manifest.policies},
        "preserved_directives": [directive.model_dump() for directive in manifest.preserved],
        "preserved_fingerprints": {directive.id: directive.fingerprint() for directive in manifest.preserved},
        "provenance": {key: [hit.model_dump() for hit in hits] for key, hits in sorted(manifest.provenance.items())},
        "candidate_resolutions": [resolution.model_dump() for resolution in report.ledger.resolutions],
        "retention": {
            "structured_coverage": report.structured_coverage,
            "retained_coverage": report.retained_coverage,
            "safety_retention": report.safety_retention,
            "preserved_count": report.preserved_count,
            "high_risk_preserved_count": report.high_risk_preserved_count,
            "dropped_count": report.dropped_count,
        },
        "checksum": checksum,
        "tokenizer": tokenizer,
        "token_counts": {"markdown": md_tokens, "glp": glp_tokens},
    }


def write_lock(paths: list[Path], output: Path, rules_path: Path | None = None) -> dict[str, object]:
    data = create_lock(paths, rules_path)
    output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return data
