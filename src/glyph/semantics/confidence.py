from __future__ import annotations

from ..core.models import SemanticRule
from ..source.document_ir import InstructionCandidate


def score_rule(rule: SemanticRule, candidate: InstructionCandidate, adapter: str = "generic_markdown") -> tuple[float, list[str]]:
    text = candidate.text.lower()
    section = (candidate.section or "").lower()
    signals: list[str] = []
    score = 0.0
    for pattern in rule.patterns:
        if pattern.lower() in text:
            signals.append(f"pattern:{pattern.replace(' ', '_')}")
            score += 0.65
            break
    for term in rule.positive_terms:
        if term.lower() in text:
            signals.append(f"term:{term.replace(' ', '_')}")
            score += 0.12
    for term in rule.required_context_terms:
        if term.lower() in text or term.lower() in section:
            signals.append(f"context:{term.replace(' ', '_')}")
            score += 0.12
    for hint in rule.section_hints:
        if hint.lower() in section:
            signals.append(f"section:{hint.replace(' ', '_')}")
            score += 0.14
            break
    for modal in rule.modal_hints:
        if modal.lower() in text:
            signals.append(f"modal:{modal.replace(' ', '_')}")
            score += 0.10
            break
    if rule.negative_terms and any(term.lower() in text for term in rule.negative_terms):
        signals.append("negative_term")
        score -= 0.25
    if candidate.block_type in {"checklist", "numbered_list"}:
        signals.append(f"block:{candidate.block_type}")
        score += 0.05
    if adapter in {"agents_md", "claude_md", "copilot_instructions", "cursor_rules"}:
        signals.append(f"adapter:{adapter}")
        score += 0.04
    return max(0.0, min(score, 1.0)), signals
