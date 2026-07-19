from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from glyph.formats.parser import parse_glp
from glyph.interfaces.cli import app
from glyph.interfaces.config import load_config


runner = CliRunner()


def test_version_text_and_json():
    text = runner.invoke(app, ["version"])
    assert text.exit_code == 0, text.output
    assert "Glyph 0.2.0" in text.output
    assert "Package: glyph-instructions" in text.output
    assert "Tokenizer:" in text.output

    js = runner.invoke(app, ["version", "--json"])
    assert js.exit_code == 0, js.output
    payload = json.loads(js.output)
    assert payload["glyph_version"] == "0.2.0"
    assert payload["package_name"] == "glyph-instructions"
    assert payload["cli"] == "glyph"
    assert payload["tokenizer"] in {"tiktoken", "fallback"}


def test_doctor_text_and_json(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    text = runner.invoke(app, ["doctor"])
    assert text.exit_code == 0, text.output
    assert "Glyph doctor" in text.output
    assert "parse .glp" in text.output
    assert "Status: ok" in text.output

    js = runner.invoke(app, ["doctor", "--json"])
    assert js.exit_code == 0, js.output
    payload = json.loads(js.output)
    assert payload["status"] == "ok"
    assert payload["writable_cwd"] is True
    assert {check["name"] for check in payload["sanity_checks"]} >= {"parse .glp", "render .glp", "count tokens"}


def test_init_creates_config_and_template(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0, result.output
    assert (tmp_path / ".glyph/config.toml").exists()
    manifest = tmp_path / "AGENTS.glp"
    assert manifest.exists()
    parsed = parse_glp(manifest.read_text(encoding="utf-8"))
    assert "run_tests_before_done" in parsed.must
    assert "glyph inspect AGENTS.md --show-unmapped" in result.output


def test_init_from_compiles_source_and_writes_lock(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "README.md"
    source.write_text("Always run tests before completion. Never commit secrets. `pytest`", encoding="utf-8")
    result = runner.invoke(app, ["init", "--from", str(source)])
    assert result.exit_code == 0, result.output
    assert "Wrote AGENTS.glp" in result.output
    assert (tmp_path / "glyph.lock.json").exists()
    parsed = parse_glp((tmp_path / "AGENTS.glp").read_text(encoding="utf-8"))
    assert "run_tests_before_done" in parsed.must
    assert "secrets_commit" in parsed.deny


def test_init_refuses_overwrite_and_force_overwrites(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "AGENTS.glp").write_text("old", encoding="utf-8")
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 1
    assert "already exist" in result.output
    assert "Use --force" in result.output

    forced = runner.invoke(app, ["init", "--force"])
    assert forced.exit_code == 0, forced.output
    assert (tmp_path / "AGENTS.glp").read_text(encoding="utf-8").startswith("glyph/0.1")


def test_config_loading_and_compile_cli_override_precedence(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "AGENTS.md"
    source.write_text("Always run tests before completion. Never commit secrets. `pytest`", encoding="utf-8")
    (tmp_path / ".glyph").mkdir()
    (tmp_path / ".glyph/config.toml").write_text(
        'version = "0.1"\n'
        'default_profile = "ultra"\n'
        "min_reduction = 100\n"
        "\n"
        "[paths]\n"
        'source = "AGENTS.md"\n'
        'manifest = "AGENTS.glp"\n',
        encoding="utf-8",
    )

    config = load_config(tmp_path / ".glyph/config.toml")
    assert config is not None
    assert config.profile().value == "ultra"

    result = runner.invoke(app, ["compile"])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "AGENTS.glp").read_text(encoding="utf-8").startswith("g/0.1")

    override = runner.invoke(app, ["compile", "--profile", "readable", "-o", "readable.glp"])
    assert override.exit_code == 0, override.output
    readable = (tmp_path / "readable.glp").read_text(encoding="utf-8")
    assert readable.startswith("glyph/0.1")
    assert "must[\n" in readable

    failing_check = runner.invoke(app, ["check"])
    assert failing_check.exit_code == 1
    assert "token reduction" in failing_check.output

    passing_check = runner.invoke(app, ["check", "--min-reduction", "-999"])
    assert passing_check.exit_code == 0, passing_check.output


def test_config_parse_error_is_human_readable(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".glyph").mkdir()
    (tmp_path / ".glyph/config.toml").write_text('default_profile = "compact\n', encoding="utf-8")
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    compile_result = runner.invoke(app, ["compile"])
    assert compile_result.exit_code == 1
    assert "Could not parse config" in compile_result.output
    assert "Fix .glyph/config.toml" in compile_result.output


def test_common_cli_errors_are_human_readable(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "AGENTS.md"
    source.write_text("Always run tests before completion.", encoding="utf-8")

    missing_source = runner.invoke(app, ["compile", "NOPE.md", "-o", "AGENTS.glp"])
    assert missing_source.exit_code == 1
    assert "NOPE.md does not exist" in missing_source.output

    missing_output_dir = runner.invoke(app, ["compile", str(source), "-o", "missing/AGENTS.glp"])
    assert missing_output_dir.exit_code == 1
    assert "Output directory missing does not exist" in missing_output_dir.output

    bad_glp = tmp_path / "bad.glp"
    bad_glp.write_text("not glp", encoding="utf-8")
    render_result = runner.invoke(app, ["render", str(bad_glp), "-o", "out.md"])
    assert render_result.exit_code == 1
    assert "Invalid .glp syntax" in render_result.output

    valid_glp = tmp_path / "AGENTS.glp"
    valid_glp.write_text("glyph/0.1\nmust[run_tests_before_done]\n", encoding="utf-8")
    bad_target = runner.invoke(app, ["emit", str(valid_glp), "--target", "bad", "-o", "out.md"])
    assert bad_target.exit_code == 1
    assert "Use --target with one of" in bad_target.output
