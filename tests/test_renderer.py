from glyph.core.models import CompressionProfile, GlyphManifest
from glyph.formats.parser import parse_glp
from glyph.formats.renderer import render_glp, render_markdown


def test_render_deterministic_and_parseable():
    manifest = GlyphManifest(stack=["pytest", "python"], commands={"test": "pytest"}, must=["run_tests_before_done"])
    rendered = render_glp(manifest)
    assert rendered == render_glp(manifest)
    assert parse_glp(rendered).commands["test"] == "pytest"
    assert render_glp(manifest, CompressionProfile.ultra).startswith("g/0.1")
    assert "Run the test suite" in render_markdown(manifest)
