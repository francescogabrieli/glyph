from __future__ import annotations

import pytest

from glyph.pipeline.compiler import analyze_text


@pytest.mark.parametrize(
    "text",
    [
        "You don't need to run tests for documentation-only changes.",
        "Never skip tests unless the change is docs-only.",
        "This project uses pytest, but contributors are not required to run it locally.",
        "The examples below show what not to do.\n\n- Always run tests before saying done.",
        "> Always run tests before saying done.",
        "Glyph turns verbose instructions into compact semantic manifests.",
        "Historically, maintainers ran pytest manually before releases.",
        "The command `pytest` exists for maintainers who want to run it.",
        "Do not treat this README as coding-agent instructions.",
    ],
)
def test_adversarial_non_active_or_exception_language_does_not_flatten_to_test_rule(text: str):
    manifest, report = analyze_text(text, "README.md")
    assert "run_tests_before_done" not in manifest.must
    if "don't need" in text or "unless" in text:
        assert report.unmapped_operational_candidates


def test_conflicting_test_instructions_are_reported_not_silently_flattened():
    manifest, report = analyze_text("Always run tests before saying done. Do not run tests unless explicitly asked.", "AGENTS.md")
    assert "run_tests_before_done" in manifest.must
    assert any(candidate.text == "Do not run tests unless explicitly asked." for candidate in report.unmapped_operational_candidates)
    assert any(conflict.id == "testing_required_and_skipped" for conflict in report.conflicts)


def test_code_examples_do_not_become_active_rules():
    text = """## Examples

```markdown
Always run tests before saying done.
Never commit secrets.
```
"""
    manifest, report = analyze_text(text, "README.md")
    assert not manifest.semantic_units()
    assert not report.unmapped_operational_candidates


def test_active_instruction_after_bad_examples_still_maps():
    text = """The examples below show what not to do.

- Always run tests before saying done.

## Rules
Always run tests before completion.
"""
    manifest, _ = analyze_text(text, "AGENTS.md")
    assert "run_tests_before_done" in manifest.must
