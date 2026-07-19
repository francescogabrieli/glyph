from __future__ import annotations

from pathlib import Path

ADAPTERS = {
    "agents_md",
    "claude_md",
    "copilot_instructions",
    "cursor_rules",
    "readme",
    "contributing",
    "generic_markdown",
}


def detect_adapter(path: str | Path) -> str:
    p = Path(path)
    name = p.name.lower()
    text = str(p).lower()
    if name == "agents.md":
        return "agents_md"
    if name == "claude.md":
        return "claude_md"
    if text.endswith(".github/copilot-instructions.md"):
        return "copilot_instructions"
    if name == ".cursorrules" or ".cursor/rules/" in text or name.endswith(".mdc"):
        return "cursor_rules"
    if name == "readme.md":
        return "readme"
    if name == "contributing.md":
        return "contributing"
    return "generic_markdown"


def validate_adapter(adapter: str | None) -> str | None:
    if adapter is None:
        return None
    if adapter not in ADAPTERS:
        raise ValueError(f"Unknown adapter '{adapter}'. Expected one of: {', '.join(sorted(ADAPTERS))}")
    return adapter
