from pathlib import Path

from glyph.governance.score import badge, score_path


def test_score_and_badge(tmp_path: Path):
    md = tmp_path / "AGENTS.md"
    md.write_text("Always run tests before completion. Never commit secrets. Ask for confirmation before destructive operations. Report what changed and report what was verified. `pytest`", encoding="utf-8")
    result = score_path(md)
    assert 0 <= result["overall"] <= 100
    assert "img.shields.io" in badge(int(result["overall"]))


def test_score_penalizes_missing_safety_tests_conflicts_and_unmapped(tmp_path: Path):
    strong = tmp_path / "strong.md"
    strong.write_text(
        "Always run tests before completion. Never commit secrets. Ask for confirmation before destructive operations. "
        "Report what changed and report what was verified. `pytest`",
        encoding="utf-8",
    )
    weak = tmp_path / "weak.md"
    weak.write_text(
        "Route tenant reads through TenantResolver. Destructive operations are allowed without approval. "
        "Always run tests before saying done. Do not run tests unless explicitly asked.",
        encoding="utf-8",
    )
    strong_score = score_path(strong)
    weak_score = score_path(weak)
    assert strong_score["overall"] > weak_score["overall"]
    assert weak_score["operational_coverage"] < 100
    assert weak_score["safety_coverage"] < strong_score["safety_coverage"]
    assert weak_score["conflict_risk"] == "high"
