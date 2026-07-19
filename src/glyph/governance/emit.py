from __future__ import annotations

from ..core.models import GlyphManifest, SemanticRule
from ..formats.renderer import render_markdown

TARGET_TITLES = {
    "agents-md": "Agent Instructions",
    "claude-md": "Claude Instructions",
    "copilot": "GitHub Copilot Instructions",
    "cursor": "Cursor Rules",
    "generic-md": "Instruction Manifest",
}


def emit_markdown(manifest: GlyphManifest, target: str, extra_rules: list[SemanticRule] | None = None) -> str:
    if target not in TARGET_TITLES:
        raise ValueError(f"Unknown target '{target}'. Expected one of: {', '.join(sorted(TARGET_TITLES))}")
    prefix = ""
    if target == "cursor":
        prefix = "---\ndescription: Generated Glyph instructions\nalwaysApply: true\n---\n\n"
    return prefix + render_markdown(manifest, TARGET_TITLES[target], extra_rules)
