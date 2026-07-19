from __future__ import annotations

from pathlib import Path


def test_readme_references_new_adoption_docs():
    readme = Path("README.md").read_text(encoding="utf-8")
    for relative_path in [
        "docs/native-agent-support.md",
        "docs/agent-maintainer-proposal.md",
        "docs/behavior-evaluation.md",
        "spec/glp-0.1.md",
    ]:
        assert relative_path in readme
        assert Path(relative_path).exists()
