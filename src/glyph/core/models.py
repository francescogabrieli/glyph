from __future__ import annotations

import hashlib
import json
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, model_validator


RuleCategory = Literal["must", "deny", "ask", "allow"]
DirectiveCategory = Literal["must", "deny", "ask", "allow", "unknown"]
RiskLevel = Literal["low", "medium", "high"]
PredicateKind = Literal["action", "state", "passive"]
ExpressionOperator = Literal["atomic", "all", "any", "not"]


class CompressionProfile(str, Enum):
    readable = "readable"
    compact = "compact"
    ultra = "ultra"


class SemanticRule(BaseModel):
    id: str
    category: RuleCategory
    patterns: list[str]
    rendered: str
    positive_terms: list[str] = Field(default_factory=list)
    negative_terms: list[str] = Field(default_factory=list)
    required_context_terms: list[str] = Field(default_factory=list)
    section_hints: list[str] = Field(default_factory=list)
    modal_hints: list[str] = Field(default_factory=list)
    severity: str = "medium"
    safety_critical: bool = False
    always_select: bool = False


class SourceHit(BaseModel):
    source: str
    line: int = 0
    text: str


def _content_id(prefix: str, value: object) -> str:
    """Return a stable content identifier with no source-location inputs."""
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return f"{prefix}_{hashlib.sha256(encoded.encode('utf-8')).hexdigest()[:12]}"


class PolicyExpression(BaseModel):
    """Small deterministic predicate expression used by `.glp 0.2`."""

    op: ExpressionOperator
    kind: PredicateKind | None = None
    subject: list[str] = Field(default_factory=list)
    predicate: str | None = None
    objects: list[str] = Field(default_factory=list)
    operands: list["PolicyExpression"] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_shape(self) -> "PolicyExpression":
        if self.op == "atomic":
            if self.kind is None or not self.subject or not self.predicate or self.operands:
                raise ValueError("atomic expressions require kind, subject, and predicate, and cannot have operands")
        else:
            if self.kind is not None or self.subject or self.predicate is not None or self.objects:
                raise ValueError(f"{self.op} expressions only accept operands")
            required = 1 if self.op == "not" else 2
            if len(self.operands) < required or (self.op == "not" and len(self.operands) != 1):
                raise ValueError(f"{self.op} expression requires {'one' if self.op == 'not' else 'at least two'} operand(s)")
        return self

    def payload(self) -> dict[str, object]:
        if self.op == "atomic":
            return {
                "op": self.op,
                "kind": self.kind,
                "subject": sorted(dict.fromkeys(self.subject)),
                "predicate": self.predicate,
                "objects": list(dict.fromkeys(self.objects)),
            }
        operands = [operand.sorted_copy() for operand in self.operands]
        if self.op in {"all", "any"}:
            operands.sort(key=lambda operand: operand.fingerprint())
        return {"op": self.op, "operands": [operand.payload() for operand in operands]}

    def fingerprint(self) -> str:
        return _content_id("e", self.payload())

    def sorted_copy(self) -> "PolicyExpression":
        return PolicyExpression.model_validate(self.payload())

    def terms(self) -> list[str]:
        if self.op == "atomic":
            return [*self.subject, self.predicate or "", *self.objects]
        return [term for operand in self.operands for term in operand.terms()]

    def node_ids(self) -> set[str]:
        return {self.fingerprint(), *(node_id for operand in self.operands for node_id in operand.node_ids())}


class AttachedExpression(BaseModel):
    """A condition or exception plus the policy/expression node it modifies."""

    attachment: str = "policy"
    expression: PolicyExpression

    def payload(self) -> dict[str, object]:
        return {"attachment": self.attachment, "expression": self.expression.sorted_copy().payload()}

    def sorted_copy(self) -> "AttachedExpression":
        return AttachedExpression.model_validate(self.payload())


class PolicyLink(BaseModel):
    """Content-addressed linkage for clauses that cannot be atomized safely."""

    group: str
    relation: Literal["inseparable"] = "inseparable"
    order: int

    def payload(self) -> dict[str, object]:
        return {"group": self.group, "relation": self.relation, "order": self.order}


class PolicyAtom(BaseModel):
    """A legacy v0.1 atom or a v0.2 policy expression statement."""

    id: str = ""
    category: RuleCategory
    action: str = ""
    target: str = ""
    scope: list[str] = Field(default_factory=list)
    conditions: list[str] = Field(default_factory=list)
    exceptions: list[str] = Field(default_factory=list)
    risk: RiskLevel = "medium"
    tags: list[str] = Field(default_factory=list)
    expression: PolicyExpression | None = None
    condition_expression: AttachedExpression | None = None
    exception_expressions: list[AttachedExpression] = Field(default_factory=list)
    link: PolicyLink | None = None

    @model_validator(mode="after")
    def validate_policy_shape(self) -> "PolicyAtom":
        if self.expression is None and (not self.action or not self.target):
            raise ValueError("v0.1 policies require action and target")
        if self.expression is not None and (self.action or self.target or self.conditions or self.exceptions):
            raise ValueError("v0.2 expression policies cannot mix legacy action/target/condition fields")
        if self.expression is not None:
            valid_attachments = {"policy", *self.expression.node_ids()}
            attached = ([self.condition_expression] if self.condition_expression else []) + self.exception_expressions
            if any(item.attachment not in valid_attachments for item in attached):
                raise ValueError("condition/exception attachment must name policy or an expression node id")
        if self.link is not None and self.expression is None:
            raise ValueError("linked policies require a structured expression")
        return self

    @property
    def is_v2(self) -> bool:
        return self.expression is not None

    def semantic_expression(self) -> PolicyExpression:
        """Losslessly expose a v0.1 action/target atom through the v0.2 view."""
        if self.expression is not None:
            return self.expression.sorted_copy()
        return PolicyExpression(op="atomic", kind="action", subject=["agent"], predicate=self.action, objects=[self.target])

    def operation_key(self) -> tuple[str, str]:
        expression = self.semantic_expression()
        if not self.is_v2:
            return self.action, self.target
        return "expression", expression.fingerprint()

    def terms(self) -> list[str]:
        values = self.semantic_expression().terms()
        if not self.is_v2:
            values.extend([*self.conditions, *self.exceptions])
        elif self.condition_expression:
            values.extend(self.condition_expression.expression.terms())
        for exception in self.exception_expressions:
            values.extend(exception.expression.terms())
        return [*values, *self.scope, *self.tags]

    def payload(self) -> dict[str, object]:
        if self.expression is not None:
            payload: dict[str, object] = {
                "category": self.category,
                "expression": self.expression.sorted_copy().payload(),
                "scope": sorted(dict.fromkeys(self.scope)),
                "condition_expression": self.condition_expression.sorted_copy().payload() if self.condition_expression else None,
                "exception_expressions": [item.sorted_copy().payload() for item in sorted(self.exception_expressions, key=lambda item: json.dumps(item.payload(), sort_keys=True))],
                "risk": self.risk,
                "tags": sorted(dict.fromkeys(self.tags)),
            }
            if self.link:
                payload["link"] = self.link.payload()
            return payload
        return {
            "category": self.category,
            "action": self.action,
            "target": self.target,
            "scope": sorted(dict.fromkeys(self.scope)),
            "conditions": sorted(dict.fromkeys(self.conditions)),
            "exceptions": sorted(dict.fromkeys(self.exceptions)),
            "risk": self.risk,
            "tags": sorted(dict.fromkeys(self.tags)),
        }

    def fingerprint(self) -> str:
        return _content_id("p", self.payload())

    def model_post_init(self, __context: object) -> None:
        if not self.id:
            self.id = self.fingerprint()

    def sorted_copy(self) -> "PolicyAtom":
        values = self.payload()
        values["id"] = self.id or self.fingerprint()
        return PolicyAtom(**values)


class CustomPolicyRule(BaseModel):
    """Repository-authored exact mapping from source wording to a 0.2 policy."""

    id: str
    match: Literal["exact"] = "exact"
    patterns: list[str]
    policy: PolicyAtom


class PreservedDirective(BaseModel):
    """An operational clause retained verbatim when structured parsing is unsafe."""

    id: str = ""
    category: DirectiveCategory = "unknown"
    text: str
    risk: RiskLevel = "medium"
    tags: list[str] = Field(default_factory=list)

    def payload(self) -> dict[str, object]:
        return {
            "category": self.category,
            "text": self.text,
            "risk": self.risk,
            "tags": sorted(dict.fromkeys(self.tags)),
        }

    def fingerprint(self) -> str:
        return _content_id("x", self.payload())

    def model_post_init(self, __context: object) -> None:
        if not self.id:
            self.id = self.fingerprint()

    def sorted_copy(self) -> "PreservedDirective":
        values = self.payload()
        values["id"] = self.id or self.fingerprint()
        return PreservedDirective(**values)


class CandidateResolution(BaseModel):
    """Auditable destination for one extracted source candidate."""

    candidate_id: str
    source: str | None = None
    line: int | None = None
    destination: Literal["canonical", "policy", "preserve", "non_operational", "dropped"]
    canonical_id: str | None = None
    policy_id: str | None = None
    policy_ids: list[str] = Field(default_factory=list)
    preserve_id: str | None = None
    reason: str = ""
    reason_code: str = ""
    evidence: list[str] = Field(default_factory=list)
    policy_shape: str | None = None
    subject_available: bool = False
    predicate_kind: PredicateKind | None = None
    object_cardinality: int = 0
    operators: list[str] = Field(default_factory=list)
    attachment: str | None = None
    ambiguous: bool = False
    risk: RiskLevel = "low"


class GlyphManifest(BaseModel):
    version: str = "0.1"
    agent: str | None = None
    goal: list[str] = Field(default_factory=list)
    stack: list[str] = Field(default_factory=list)
    scope: list[str] = Field(default_factory=list)
    flow: list[str] = Field(default_factory=list)
    commands: dict[str, str] = Field(default_factory=dict)
    must: list[str] = Field(default_factory=list)
    deny: list[str] = Field(default_factory=list)
    ask: list[str] = Field(default_factory=list)
    allow: list[str] = Field(default_factory=list)
    policies: list[PolicyAtom] = Field(default_factory=list)
    preserved: list[PreservedDirective] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)
    provenance: dict[str, list[SourceHit]] = Field(default_factory=dict)
    unknown_operational: list[str] = Field(default_factory=list)

    def semantic_units(self) -> set[str]:
        return set(self.must) | set(self.deny) | set(self.ask) | set(self.allow)

    def structured_ids(self) -> set[str]:
        return self.semantic_units() | {policy.id for policy in self.policies}

    def retained_ids(self) -> set[str]:
        return self.structured_ids() | {directive.id for directive in self.preserved}

    def upgraded_v2(self) -> "GlyphManifest":
        """Select the 0.2 container without rewriting lossless v0.1 atoms."""
        return self.model_copy(update={"version": "0.2"}).sorted_copy()

    def sorted_copy(self) -> "GlyphManifest":
        preferred_flow = ["read", "plan", "minimal_change", "lint", "typecheck", "test", "build", "report"]
        flow = [item for item in preferred_flow if item in self.flow]
        flow.extend(sorted(item for item in self.flow if item not in flow))
        version = "0.2" if self.allow or any(policy.is_v2 or policy.category == "allow" for policy in self.policies) or any(directive.category == "allow" for directive in self.preserved) else self.version
        return self.model_copy(
            update={
                "version": version,
                "goal": sorted(dict.fromkeys(self.goal)),
                "stack": sorted(dict.fromkeys(self.stack)),
                "scope": sorted(dict.fromkeys(self.scope)),
                "flow": flow,
                "commands": dict(sorted(self.commands.items())),
                "must": sorted(dict.fromkeys(self.must)),
                "deny": sorted(dict.fromkeys(self.deny)),
                "ask": sorted(dict.fromkeys(self.ask)),
                "allow": sorted(dict.fromkeys(self.allow)),
                "policies": sorted(
                    {policy.id or policy.fingerprint(): policy.sorted_copy() for policy in self.policies}.values(),
                    key=lambda policy: policy.id,
                ),
                "preserved": sorted(
                    {directive.id or directive.fingerprint(): directive.sorted_copy() for directive in self.preserved}.values(),
                    key=lambda directive: directive.id,
                ),
                "conflicts": sorted(dict.fromkeys(self.conflicts)),
            }
        )


class LintWarning(BaseModel):
    id: str
    severity: str
    source: str | None = None
    line: int | None = None
    explanation: str
    suggested_fix: str


class VerifyReport(BaseModel):
    detected_semantic_units: list[str]
    encoded_semantic_units: list[str]
    missing_semantic_units: list[str]
    coverage: float
    missing_commands: dict[str, str] = Field(default_factory=dict)
    missing_stack: list[str] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)
    missing_policy_ids: list[str] = Field(default_factory=list)
    missing_preserve_ids: list[str] = Field(default_factory=list)
    canonical_candidate_coverage: float = 100.0
    structured_coverage: float = 100.0
    retained_coverage: float = 100.0
    safety_retention: float = 100.0
    preserved_count: int = 0
    high_risk_preserved_count: int = 0
    dropped_count: int = 0
