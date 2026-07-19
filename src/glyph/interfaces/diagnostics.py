from __future__ import annotations

import importlib.metadata
import importlib.util
import sys
from pathlib import Path
from typing import Any

from .. import __version__
from ..core.models import GlyphManifest
from ..formats.parser import parse_glp
from ..formats.renderer import render_glp
from ..pipeline.compiler import analyze_text
from ..source.tokenizer import count_tokens

PACKAGE_NAME = "glyph-instructions"
CLI_NAME = "glyph"


def installed_version() -> str:
    try:
        return importlib.metadata.version(PACKAGE_NAME)
    except importlib.metadata.PackageNotFoundError:
        return __version__


def tokenizer_status() -> str:
    _, name = count_tokens("Glyph")
    return "tiktoken" if name.startswith("tiktoken") else "fallback"


def mcp_available() -> bool:
    try:
        return importlib.util.find_spec("mcp.server.fastmcp") is not None
    except ModuleNotFoundError:
        return False


def package_install_path() -> str:
    import glyph

    return str(Path(glyph.__file__).resolve().parent)


def version_info() -> dict[str, Any]:
    return {
        "glyph_version": installed_version(),
        "python_version": sys.version.split()[0],
        "package_name": PACKAGE_NAME,
        "cli": CLI_NAME,
        "mcp_available": mcp_available(),
        "tokenizer": tokenizer_status(),
    }


def doctor_info(cwd: Path | None = None) -> dict[str, Any]:
    root = cwd or Path.cwd()
    checks: list[dict[str, Any]] = []

    def run_check(name: str, fn) -> None:
        try:
            fn()
            checks.append({"name": name, "ok": True, "error": None})
        except Exception as exc:
            checks.append({"name": name, "ok": False, "error": str(exc)})

    run_check("parse .glp", lambda: parse_glp("glyph/0.1\nmust[run_tests_before_done]\n"))
    run_check("render .glp", lambda: render_glp(GlyphManifest(must=["run_tests_before_done"])))
    run_check("count tokens", lambda: count_tokens("Run tests."))
    run_check("classify instruction", lambda: _assert_classifies())
    run_check("service layer", lambda: GlyphManifest(must=["run_tests_before_done"]).semantic_units())

    core_ok = all(check["ok"] for check in checks)
    try:
        dist = importlib.metadata.distribution(PACKAGE_NAME)
        metadata = {"name": dist.metadata.get("Name"), "version": dist.version}
    except importlib.metadata.PackageNotFoundError:
        metadata = None

    return {
        **version_info(),
        "install_path": package_install_path(),
        "writable_cwd": _writable(root),
        "optional_extras": {"mcp": mcp_available()},
        "build_metadata": metadata,
        "sanity_checks": checks,
        "status": "ok" if core_ok else "broken",
    }


def _assert_classifies() -> None:
    manifest, _ = analyze_text("Always run tests before completion.", "AGENTS.md")
    if "run_tests_before_done" not in manifest.semantic_units():
        raise AssertionError("run_tests_before_done was not detected")


def _writable(path: Path) -> bool:
    try:
        probe = path / ".glyph-doctor-write-test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        return True
    except OSError:
        return False
