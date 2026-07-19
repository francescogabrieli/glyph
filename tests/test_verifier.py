from glyph.pipeline.compiler import compile_text
from glyph.pipeline.verifier import verify


def test_verify_coverage():
    markdown = "Always run tests before completion. Never commit secrets. `pytest`"
    manifest = compile_text(markdown)
    report = verify(markdown, manifest)
    assert report.coverage == 100.0
    assert not report.missing_semantic_units
