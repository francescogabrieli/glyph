from glyph.governance.diff import semantic_diff
from glyph.pipeline.compiler import compile_text


def test_semantic_diff_risk_on_removed_testing():
    old = compile_text("Always run tests before completion. Never commit secrets.")
    new = compile_text("Never commit secrets.")
    result = semantic_diff(old, new)
    assert "run_tests_before_done" in result["removed"]
    assert result["risks"]
