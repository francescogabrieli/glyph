from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from ..core.models import CandidateResolution


BlockType = Literal[
    "heading",
    "paragraph",
    "bullet_list",
    "numbered_list",
    "checklist",
    "fenced_code_block",
    "inline_code",
    "table",
    "blockquote",
    "horizontal_rule",
]

CandidateIntent = Literal[
    "agent_instruction",
    "repo_convention",
    "testing_policy",
    "safety_policy",
    "release_policy",
    "command_instruction",
    "product_requirement",
    "implementation_requirement",
    "api_contract",
    "example_content",
    "reference_content",
    "non_operational_context",
    "conditional_instruction",
    "unknown_operational",
    "high_risk_unmapped",
]
DocumentRole = Literal["agent_instructions", "contributor_guide", "implementation_spec", "product_docs", "mixed"]
DocumentAudience = Literal["agent", "contributor", "developer", "mixed"]


class BlockIR(BaseModel):
    type: BlockType
    text: str
    line_start: int
    line_end: int
    source: str
    section: str | None = None
    heading_level: int | None = None
    code_language: str | None = None
    table_rows: list[list[str]] = Field(default_factory=list)
    parent_headings: list[str] = Field(default_factory=list)


class SectionIR(BaseModel):
    title: str
    level: int
    line_start: int
    parent_titles: list[str] = Field(default_factory=list)


class DocumentIR(BaseModel):
    source: str
    adapter: str
    role: DocumentRole = "mixed"
    audience: DocumentAudience = "mixed"
    blocks: list[BlockIR] = Field(default_factory=list)
    sections: list[SectionIR] = Field(default_factory=list)


class CommandCandidate(BaseModel):
    command: str
    source: str
    line: int
    section: str | None = None
    block_type: str
    context: str = ""
    label: str | None = None
    confidence: float = 0.0
    signals: list[str] = Field(default_factory=list)


class InstructionCandidate(BaseModel):
    id: str = ""
    text: str
    source: str
    line: int
    section: str | None = None
    block_type: str
    intent: CandidateIntent = "unknown_operational"
    intent_confidence: float = 0.0
    operational_confidence: float = 0.0
    reasons: list[str] = Field(default_factory=list)
    signals: list[str] = Field(default_factory=list)
    reasoning_summary: str = ""
    semantic_unit: str | None = None
    semantic_confidence: float | None = None
    nearby_commands: list[str] = Field(default_factory=list)
    inherited_category: Literal["must", "deny", "ask", "allow"] | None = None
    local_antecedent: str | None = None
    conditions: list[str] = Field(default_factory=list)
    exceptions: list[str] = Field(default_factory=list)
    risk: Literal["low", "medium", "high"] = "low"


class SemanticMatch(BaseModel):
    semantic_unit: str
    category: str
    confidence: float
    signals: list[str] = Field(default_factory=list)
    candidate: InstructionCandidate


class ConflictFinding(BaseModel):
    id: str
    semantic_units: list[str] = Field(default_factory=list)
    source_texts: list[str] = Field(default_factory=list)
    source_files: list[str] = Field(default_factory=list)
    line_numbers: list[int] = Field(default_factory=list)
    severity: str = "high"
    suggested_fix: str


class SemanticLedger(BaseModel):
    compressed_semantics: list[str] = Field(default_factory=list)
    commands: list[CommandCandidate] = Field(default_factory=list)
    repo_specific_candidates: list[InstructionCandidate] = Field(default_factory=list)
    product_requirements: list[InstructionCandidate] = Field(default_factory=list)
    implementation_requirements: list[InstructionCandidate] = Field(default_factory=list)
    api_contracts: list[InstructionCandidate] = Field(default_factory=list)
    conditional_instructions: list[InstructionCandidate] = Field(default_factory=list)
    examples_or_references: list[InstructionCandidate] = Field(default_factory=list)
    non_operational_context: list[InstructionCandidate] = Field(default_factory=list)
    high_risk_unmapped: list[InstructionCandidate] = Field(default_factory=list)
    resolutions: list[CandidateResolution] = Field(default_factory=list)
    operational_candidates: list[InstructionCandidate] = Field(default_factory=list)
    dropped_candidates: list[InstructionCandidate] = Field(default_factory=list)
    conflicts: list[ConflictFinding] = Field(default_factory=list)


class ExtractionReport(BaseModel):
    input_files: list[str] = Field(default_factory=list)
    adapters: dict[str, str] = Field(default_factory=dict)
    markdown_tokens: int = 0
    glp_tokens: int = 0
    tokenizer: str = "fallback"
    semantic_units_detected: list[str] = Field(default_factory=list)
    semantic_units_emitted: list[str] = Field(default_factory=list)
    commands_detected: dict[str, str] = Field(default_factory=dict)
    semantic_coverage: float = 100.0
    agent_instruction_coverage: float = 100.0
    repo_specific_coverage: float = 100.0
    spec_classification_rate: float = 100.0
    operational_coverage: float = 100.0
    high_risk_unmapped_count: int = 0
    unmapped_operational_candidates: list[InstructionCandidate] = Field(default_factory=list)
    conflicts: list[ConflictFinding] = Field(default_factory=list)
    confidence_distribution: dict[str, int] = Field(default_factory=dict)
    token_reduction: float = 0.0
    matches: list[SemanticMatch] = Field(default_factory=list)
    command_candidates: list[CommandCandidate] = Field(default_factory=list)
    documents: list[DocumentIR] = Field(default_factory=list)
    candidates: list[InstructionCandidate] = Field(default_factory=list)
    ledger: SemanticLedger = Field(default_factory=SemanticLedger)
    canonical_candidate_coverage: float = 100.0
    structured_coverage: float = 100.0
    retained_coverage: float = 100.0
    safety_retention: float = 100.0
    preserved_count: int = 0
    high_risk_preserved_count: int = 0
    dropped_count: int = 0
