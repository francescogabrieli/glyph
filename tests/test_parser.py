from glyph.formats.parser import parse_glp


def test_parse_readable_glp():
    manifest = parse_glp(
        """glyph/0.1

agent backend
stack[
  python
  pytest
]
cmd.test "pytest"
must[
  run_tests_before_done
]
deny[secrets_commit]
ask[destructive_ops]
"""
    )
    assert manifest.agent == "backend"
    assert manifest.stack == ["pytest", "python"]
    assert manifest.commands["test"] == "pytest"
    assert "run_tests_before_done" in manifest.must
