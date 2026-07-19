from pathlib import Path

from glyph.governance.lock import create_lock, write_lock


def test_lockfile_generation(tmp_path: Path):
    md = tmp_path / "AGENTS.md"
    md.write_text("Always run tests before completion. `pytest`", encoding="utf-8")
    data = create_lock([md])
    assert "checksum" in data
    out = tmp_path / "glyph.lock.json"
    write_lock([md], out)
    assert out.exists()
