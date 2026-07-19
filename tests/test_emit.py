from glyph.core.models import GlyphManifest
from glyph.governance.emit import emit_markdown


def test_emit_targets():
    manifest = GlyphManifest(must=["run_tests_before_done"], deny=["secrets_commit"])
    assert "Claude Instructions" in emit_markdown(manifest, "claude-md")
    assert "alwaysApply" in emit_markdown(manifest, "cursor")
