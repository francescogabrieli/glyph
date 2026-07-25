from __future__ import annotations

import json
from pathlib import Path


def test_glyph_skill_has_required_frontmatter_and_references() -> None:
    root = Path("skills/glyph")
    skill = (root / "SKILL.md").read_text(encoding="utf-8")

    assert skill.startswith("---\n")
    assert "\nname: glyph\n" in skill
    assert "\ndescription:" in skill
    assert "glyph inspect" in skill
    assert "glyph verify" in skill
    assert "Never rewrite" in skill

    assert (root / "LICENSE.txt").exists()
    assert (root / "references/commands.md").exists()
    assert (root / "references/trust-model.md").exists()


def test_agent_plugin_manifests_reference_glyph_skill() -> None:
    codex = json.loads(Path(".codex-plugin/plugin.json").read_text(encoding="utf-8"))
    claude = json.loads(Path(".claude-plugin/marketplace.json").read_text(encoding="utf-8"))

    assert codex["name"] == "glyph"
    assert codex["skills"] == "./skills/"

    plugins = claude["plugins"]
    assert len(plugins) == 1
    assert plugins[0]["name"] == "glyph"
    assert plugins[0]["skills"] == ["./skills/glyph"]
