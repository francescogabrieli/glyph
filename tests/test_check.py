from pathlib import Path

from glyph.formats.renderer import render_glp
from glyph.governance.check import check_pair
from glyph.pipeline.compiler import compile_files


def test_check_pair_passes_and_fails_thresholds(tmp_path: Path):
    md = tmp_path / "AGENTS.md"
    md.write_text("Always run tests before completion. Never commit secrets. Ask for confirmation before destructive operations. `pytest`", encoding="utf-8")
    glp = tmp_path / "AGENTS.glp"
    glp.write_text(render_glp(compile_files([md])), encoding="utf-8")
    ok, errors = check_pair(md, glp, min_coverage=90, min_reduction=-100)
    assert ok, errors
    ok, errors = check_pair(md, glp, min_coverage=101, min_reduction=0)
    assert not ok
