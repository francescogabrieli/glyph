"""Contract tests for the modular package layout."""

from glyph.core.models import GlyphManifest
from glyph.formats.parser import parse_glp
from glyph.formats.renderer import render_glp
from glyph.pipeline.compiler import analyze_text
from glyph.semantics.rules import RULE_BY_ID
from glyph.source.markdown_ast import parse_markdown


def test_canonical_packages_are_importable() -> None:
    assert GlyphManifest.__module__ == "glyph.core.models"
    assert callable(analyze_text)
    assert callable(parse_markdown)
    assert callable(parse_glp)
    assert callable(render_glp)
    assert "run_tests_before_done" in RULE_BY_ID
