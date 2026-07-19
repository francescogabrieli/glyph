from __future__ import annotations

from pathlib import Path

import pytest

from glyph.formats.parser import parse_glp
from glyph.formats.renderer import render_markdown


FIXTURES = Path("spec/fixtures")
EXPECTED = FIXTURES / "expected"


@pytest.mark.parametrize(
    "name",
    ["minimal", "safety", "testing", "fullstack", "custom-rules"],
)
def test_valid_glp_fixtures_parse(name: str):
    manifest = parse_glp((FIXTURES / f"{name}.glp").read_text(encoding="utf-8"))
    assert manifest.version == "0.1"


@pytest.mark.parametrize(
    "name",
    ["invalid-unknown-section", "invalid-syntax"],
)
def test_invalid_glp_fixtures_fail(name: str):
    with pytest.raises(ValueError):
        parse_glp((FIXTURES / f"{name}.glp").read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "name",
    ["minimal", "safety", "testing", "fullstack", "custom-rules"],
)
def test_valid_glp_fixtures_render_deterministically(name: str):
    manifest = parse_glp((FIXTURES / f"{name}.glp").read_text(encoding="utf-8"))
    rendered = render_markdown(manifest)
    expected = (EXPECTED / f"{name}.md").read_text(encoding="utf-8")
    assert rendered == expected
