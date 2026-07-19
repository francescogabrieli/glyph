from __future__ import annotations

from ..core.models import SemanticRule
from ..source.document_ir import CommandCandidate, InstructionCandidate, SemanticMatch
from .confidence import score_rule

COMMAND_LABEL_PATTERNS = {
    "install": ["install", "pip install", "npm install", "pnpm install", "uv sync"],
    "dev": ["local development", "start", "dev", "uvicorn", "npm run dev", "pnpm dev", "vite", "next dev"],
    "test": ["test", "tests", "suite", "pytest", "npm test", "pnpm test", "vitest", "go test"],
    "lint": ["lint", "ruff check", "eslint", "npm run lint", "pnpm lint"],
    "typecheck": ["type", "typecheck", "type check", "mypy", "pyright", "tsc"],
    "format": ["format", "ruff format", "black", "prettier"],
    "build": ["build", "npm run build", "pnpm build", "docker build"],
    "migrate": ["migration", "migrate", "alembic", "prisma migrate", "dbt run"],
    "seed": ["seed"],
    "deploy": ["deploy", "deployment", "terraform apply", "kubectl apply"],
}
MAPPABLE_INTENTS = {
    "agent_instruction",
    "repo_convention",
    "testing_policy",
    "safety_policy",
    "release_policy",
    "command_instruction",
    "conditional_instruction",
    "unknown_operational",
    "high_risk_unmapped",
}


def classify_instructions(candidates: list[InstructionCandidate], rules: list[SemanticRule], adapter: str) -> list[SemanticMatch]:
    matches: list[SemanticMatch] = []
    for candidate in candidates:
        if candidate.intent not in MAPPABLE_INTENTS:
            continue
        if candidate.block_type == "blockquote" and adapter not in {"agents_md", "claude_md", "copilot_instructions", "cursor_rules"}:
            continue
        for rule in rules:
            confidence, signals = score_rule(rule, candidate, adapter)
            if confidence >= 0.52:
                matches.append(SemanticMatch(semantic_unit=rule.id, category=rule.category, confidence=confidence, signals=signals, candidate=candidate))
    return matches


def classify_command(candidate: CommandCandidate) -> CommandCandidate:
    command_text = candidate.command.lower()
    haystack = f"{candidate.section or ''} {candidate.context} {candidate.command}".lower()
    best_label = None
    best_score = 0.0
    signals: list[str] = []
    for label, patterns in COMMAND_LABEL_PATTERNS.items():
        score = 0.0
        matched = []
        for pattern in patterns:
            if pattern in command_text:
                score += 1.0
                matched.append(pattern)
            elif pattern in haystack:
                score += 0.3
                matched.append(pattern)
        if label in (candidate.section or "").lower():
            score += 0.25
        if score > best_score:
            best_label = label
            best_score = score
            signals = [f"label_pattern:{p.replace(' ', '_')}" for p in matched]
    candidate.label = best_label if best_score >= 0.3 else "other"
    candidate.confidence = min(best_score, 1.0)
    candidate.signals = signals or ["command_like"]
    return candidate


def classify_commands(candidates: list[CommandCandidate]) -> list[CommandCandidate]:
    return [classify_command(candidate) for candidate in candidates]
