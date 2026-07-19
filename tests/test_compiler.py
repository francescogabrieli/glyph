from glyph.pipeline.compiler import compile_text


def test_compile_markdown_to_semantics_and_commands():
    text = """
# AGENTS
Always read relevant files before editing. Create a short plan before editing.
Never commit secrets, tokens, API keys, or credentials.
Ask for confirmation before destructive operations.
Run tests before completion.
```bash
pytest
ruff check .
```
Report what changed and report what was verified.
"""
    manifest = compile_text(text, "AGENTS.md")
    assert "read_before_edit" in manifest.must
    assert "run_tests_before_done" in manifest.must
    assert "secrets_commit" in manifest.deny
    assert "destructive_ops" in manifest.ask
    assert manifest.commands["test"] == "pytest"
    assert manifest.commands["lint"] == "ruff check ."


def test_messy_markdown_degrades_gracefully():
    text = """
random intro
- [x] before marking work done execute the test suite
| thing | value |
| --- | --- |
| tests | `npm test` |
Some vague operational sentence should use best judgment.
"""
    manifest = compile_text(text, ".cursor/rules/app.mdc")
    assert "run_tests_before_done" in manifest.must
    assert manifest.commands["test"] == "npm test"
    assert manifest.unknown_operational
