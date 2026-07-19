from glyph.source.adapters import detect_adapter


def test_adapter_detection():
    assert detect_adapter("AGENTS.md") == "agents_md"
    assert detect_adapter("CLAUDE.md") == "claude_md"
    assert detect_adapter(".github/copilot-instructions.md") == "copilot_instructions"
    assert detect_adapter(".cursor/rules/glyph.mdc") == "cursor_rules"
    assert detect_adapter("README.md") == "readme"
    assert detect_adapter("CONTRIBUTING.md") == "contributing"
