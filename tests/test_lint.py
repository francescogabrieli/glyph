from glyph.governance.lint import lint_text


def test_lint_detects_smells():
    warnings = lint_text("Use best judgment. Destructive operations are allowed without approval. Run `rm -rf tmp`.")
    ids = {warning.id for warning in warnings}
    assert "vague_instruction" in ids
    assert "dangerous_permission" in ids
    assert "missing_test_command" in ids
