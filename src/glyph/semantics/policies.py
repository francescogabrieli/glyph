"""Deterministic resolution of operational candidates beyond the rule registry.

This module is deliberately conservative.  If a clause cannot be represented
with stable fields at the required confidence, the compiler emits a
``PreservedDirective`` with its original wording instead of guessing.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field

from ..core.models import CandidateResolution, CustomPolicyRule, PolicyAtom, PreservedDirective, RiskLevel, RuleCategory, SemanticRule
from ..source.document_ir import ConflictFinding, InstructionCandidate, SemanticMatch
from .classifier import MAPPABLE_INTENTS
from .clause_parser import ClauseContext, ClauseParseResult, parse_policy_clause
from .confidence import score_rule
from .custom_rules import matching_custom_policy_rules


SAFETY_TERMS = (
    "secret", "credential", "token", "api key", "production", "destructive", "delete",
    "drop", "security", "auth", "permission", "deploy", "migration", "schema", "privacy",
)
TAG_TERMS = {
    "security": ("security", "auth", "permission", "credential", "secret", "token", "api key"),
    "testing": ("test", "pytest", "suite", "lint", "typecheck"),
    "database": ("database", "schema", "migration", "postgres", "sql"),
    "deployment": ("deploy", "release", "production"),
    "repository": ("repository", "code", "file", "path", "resolver", "service"),
}
DIRECTIVE_VERBS = (
    "access", "aim", "ask", "assume", "attribute", "broaden", "classify", "close", "combine", "confirm", "request", "require", "run", "use", "route", "prefer", "preserve", "keep",
    "check", "verify", "make", "create", "report", "summarize", "follow", "update",
    "document", "validate", "avoid", "remove", "delete", "edit", "modify", "write",
    "deploy", "commit", "expose", "add", "apply", "change", "keep", "ensure", "read", "inspect", "pass",
    "put", "generate", "import", "include", "introduce", "invent", "duplicate", "narrate", "rely", "state", "respect", "contain",
    "drop", "encourage", "export", "fix", "hardcode", "ignore", "invoke", "kill", "mix", "open", "pin", "reserve", "respond", "restore", "start", "stop", "store", "target",
)


@dataclass
class ResolutionResult:
    matches: list[SemanticMatch] = field(default_factory=list)
    policy: PolicyAtom | None = None
    policies: list[PolicyAtom] = field(default_factory=list)
    preserved: PreservedDirective | None = None
    resolutions: list[CandidateResolution] = field(default_factory=list)
    conflicts: list[ConflictFinding] = field(default_factory=list)


INSTRUCTION_ADAPTERS = {"agents_md", "claude_md", "copilot_instructions", "cursor_rules"}
GENERIC_DOCUMENT_ADAPTERS = {"readme", "contributing", "generic_markdown"}


def is_operational(candidate: InstructionCandidate, adapter: str) -> bool:
    """Return the authoritative post-context operational status.

    Candidate intent and confidence identify directive-like text, while the
    adapter/block context decides whether that text is active instructions.
    Generic-document blockquotes are quotations, not operational policy.
    """
    if candidate.block_type == "blockquote" and adapter not in INSTRUCTION_ADAPTERS:
        return False
    if re.search(r"\b(?:is|are) required to be able to\b.*\bdue to\b", candidate.text, flags=re.IGNORECASE):
        return False
    if adapter in GENERIC_DOCUMENT_ADAPTERS and re.match(
        r"^\s*(?:\(?this is why\b|(?:it|this|you) should be (?:possible|built|able)\b|returns?\s+.+\bthat should\b|selecting\s+.+\s+should make it clear\b|for\s+.+?,\s+this should be treated as\b|when\s+.+?,\s+you need more than\b|each\s+.+?—\s+everything\s+.+?,\s+except\b)",
        candidate.text,
        flags=re.IGNORECASE,
    ):
        return False
    return candidate.intent in MAPPABLE_INTENTS and candidate.operational_confidence >= 0.18


def _security_sensitive_text(text: str) -> bool:
    """Recognize security meaning without promoting incidental lexemes.

    Terms such as ``token`` and ``schema`` occur in test names and file
    catalogs.  A high-risk decision therefore requires either an intrinsically
    sensitive object or a security-relevant relation around the ambiguous
    noun.  This function is shared by risk and tag derivation so the compiler
    has one contextual interpretation of those terms.
    """
    lowered = " ".join(text.lower().split())
    if re.search(r"\b(?:secrets?|api[ _-]?keys?|private keys?)\b", lowered):
        return True
    if re.search(r"\b(?:authentication|authorization)\b", lowered):
        return True
    if re.search(r"\b(?:destructive|delete|drop|deploy(?:ment)?|migrations?)\b", lowered):
        return True
    if re.search(r"\bproduction\b", lowered) and re.search(
        r"\b(?:access|alter|bypass\w*|change|changing|config(?:uration)?|credentials?|emergency|firewall|identit\w*|impact|migrate|modify|operations?|override|secrets?|unsafe|update|write)\b",
        lowered,
    ):
        return True

    credential_context = re.sub(r"\btoken[-_ ]gates?\b|\b(?:design|syntax|parser) tokens?\b", "", lowered)
    credential_context = re.sub(
        r"\bcredentials?\s+(?:are\s+|is\s+)?(?:available|needed)\b",
        "",
        credential_context,
    )
    if re.search(r"\b(?:credentials?|tokens?)\b", credential_context) and re.search(
        r"\b(?:access|accept|belong|commit|contain|delete|deny|expose|export|hardcode|include|log|print|read|rely|request|return|route|share|store|use|write)\w*\b|\b(?:must not|never|do not|don't)\b",
        credential_context,
    ):
        return True

    if re.search(r"\bpermissions?\b", lowered) and re.search(
        r"\b(?:access|allow|approval|ask|broaden|deny|grant|iam|policy|require|revoke|scope)\b",
        lowered,
    ):
        return True
    if re.search(r"\bschema\b", lowered) and re.search(
        r"\b(?:alter|apply|change|delete|drop|migrate|migration|modify|production|unsafe|update|write)\b",
        lowered,
    ):
        return True
    return False


def classify_risk(text: str) -> RiskLevel:
    lowered = text.lower()
    if _security_sensitive_text(text):
        return "high"
    if any(term in lowered for term in ("test", "lint", "typecheck", "build", "release", "dependency")):
        return "medium"
    return "low"


def tags_for(text: str) -> list[str]:
    lowered = text.lower()
    return sorted(tag for tag, terms in TAG_TERMS.items() if any(term in lowered for term in terms))


def category_for(candidate: InstructionCandidate) -> RuleCategory:
    lowered = candidate.text.lower().strip()
    if re.search(r"\b(ask|confirm|request)\b.*\b(approval|confirmation|permission)\b|\bask permission\b", lowered):
        return "ask"
    if re.search(r"\b(never|do not|don't|avoid|forbidden|prohibited)\b", lowered):
        return "deny"
    if re.search(r"\b(?:may|allowed to|authorized to|authorisation to|authorization to|have durable authorization)\b", lowered):
        return "allow"
    if candidate.inherited_category:
        return candidate.inherited_category
    return "must"


def _strip_label_prefix(text: str) -> str:
    """Remove a Markdown label when the remainder is an explicit directive."""
    match = re.match(
        r"^\s*(?:[*_`~]+)?[A-Za-z][A-Za-z0-9 _./-]{0,80}(?:[*_`~]+)?\s*:\s+(.+)$",
        text,
    )
    if not match:
        return text.strip()
    body = match.group(1).strip()
    starts = r"(?:always|never|do not|don't|avoid|ask|confirm|request|if|when|" + "|".join(DIRECTIVE_VERBS) + r")\b"
    return body if re.match(starts, body, flags=re.IGNORECASE) else text.strip()


def _normalise_policy_text(text: str) -> str:
    """Expose the active directive in common labeled/compound Markdown forms."""
    text = text.replace("**", "")
    normalised = _strip_label_prefix(text)
    if re.search(r"\bmay\b.+\bbut\s+(?:never|do not|don't|avoid)\b", normalised, flags=re.IGNORECASE):
        return normalised
    compound = re.search(r"\b(?:but|and)\s+(never|do not|don't|avoid)\s+(.+)$", normalised, flags=re.IGNORECASE)
    if compound and not re.match(r"^(?:never|do not|don't|avoid)\b", normalised, flags=re.IGNORECASE):
        return f"{compound.group(1)} {compound.group(2)}"
    return normalised


def _phrase_values(text: str) -> tuple[list[str], list[str]]:
    conditions: list[str] = []
    exceptions: list[str] = []
    leading = re.match(r"^\s*(?:if|when)\s+(.+?),\s+(.+)$", text, flags=re.IGNORECASE)
    searchable = text
    if leading:
        condition = " ".join(leading.group(1).strip(" .;:").split())
        if condition:
            conditions.append(condition)
        searchable = leading.group(2)
    for marker, target in (("unless", exceptions), ("except", exceptions), ("only if", conditions), ("if", conditions), ("when", conditions), ("before", conditions), ("after", conditions)):
        for match in re.finditer(r"\b" + re.escape(marker) + r"\s+(.+?)(?=(?:\s+\b(?:unless|except|only if|if|when|before|after)\b)|$)", searchable, flags=re.IGNORECASE):
            phrase = " ".join(match.group(1).strip(" .;:").split())
            if phrase and phrase not in target:
                target.append(phrase)
    return conditions, exceptions


def _strip_clauses(text: str) -> str:
    leading = re.match(r"^\s*(?:if|when)\s+.+?,\s+(.+)$", text, flags=re.IGNORECASE)
    core = leading.group(1) if leading else text
    return re.split(r"\s+\b(?:unless|except|only if|if|when|before|after)\b\s+", core, maxsplit=1, flags=re.IGNORECASE)[0].strip(" .;:")


def _normalise_target(value: str) -> str:
    value = value.strip(" .;:")
    value = re.sub(r"[`'\"]", "", value)
    value = re.sub(r"\s+", "_", value.lower())
    value = re.sub(r"[^a-z0-9._/:-]+", "_", value).strip("_")
    return value


def _derive_policy(candidate: InstructionCandidate) -> tuple[list[PolicyAtom], float, ClauseParseResult]:
    text = candidate.text.strip()
    text = _normalise_policy_text(text)
    category = category_for(candidate)
    analysis = parse_policy_clause(text, category, ClauseContext(antecedent=candidate.local_antecedent))
    v2_policies = analysis.to_policies(category, classify_risk(text), tags_for(text))
    if v2_policies:
        return v2_policies, 0.96, analysis
    protected_ambiguity = analysis.reason_code in {"pronoun_reference", "vague_reference", "ambiguous_condition_attachment", "ambiguous_exception_attachment"}
    protected_ambiguity = protected_ambiguity or (
        analysis.reason_code == "ambiguous_coordination"
        and bool(re.search(r"^(?:never|do not|don't|avoid)\b|\bmust not\b", text, flags=re.IGNORECASE))
    )
    if classify_risk(text) == "high" and (protected_ambiguity or analysis.reason_code == "narrative_attribution"):
        return [], 0.0, analysis
    conditions, exceptions = _phrase_values(text)
    core = _strip_clauses(text)
    lowered = core.lower()
    risk = classify_risk(text)
    core = re.sub(r"^(?:always|must|should|required|please)\s+", "", core, flags=re.IGNORECASE)
    core = re.sub(r"^(?:never|do not|don't|avoid)\s+", "", core, flags=re.IGNORECASE)
    subject_scope: str | None = None
    match = re.match(r"([A-Za-z][A-Za-z_-]*)\s+(.+)$", core)
    if match:
        verb = match.group(1).lower().replace("-", "_")
        object_text = match.group(2).strip()
    else:
        verb = ""
        object_text = ""

    if category == "ask":
        ask_match = re.match(r"(?:ask|confirm|request)\s+(?:for\s+)?(.+)$", core, flags=re.IGNORECASE)
        if ask_match:
            verb = "ask"
            object_text = ask_match.group(1).strip()
    if verb not in DIRECTIVE_VERBS:
        # Policies commonly use a subject followed by a modal, rather than an
        # imperative at the start of the sentence (for example, "firewall
        # bypasses must pass ReviewGate").  The existing PolicyAtom fields can
        # represent this without preserving the whole clause as opaque text:
        # the subject becomes scope, and the predicate becomes action/target.
        modal = re.match(
            r"(.+?)\s+(?:must|should|required)(?:\s+to)?\s+([A-Za-z][A-Za-z_-]*)\s+(.+)$",
            core,
            flags=re.IGNORECASE,
        )
        if not modal or risk != "high":
            return [], 0.0, analysis
        subject_scope = _normalise_target(modal.group(1))
        verb = modal.group(2).lower().replace("-", "_")
        object_text = modal.group(3).strip()
    if verb not in DIRECTIVE_VERBS or not object_text:
        return [], 0.0, analysis
    action = "require" if category == "ask" else verb
    target = _normalise_target(object_text)
    if not target:
        return [], 0.0, analysis
    scope: list[str] = []
    if subject_scope:
        scope.append(subject_scope)
    scope_match = re.search(r"\b(?:in|within|under|on)\s+(`?[-\w./]+`?)", object_text, flags=re.IGNORECASE)
    if scope_match:
        scope.append(scope_match.group(1).strip("`"))
    policy = PolicyAtom(
        category=category,
        action=action,
        target=target,
        scope=scope,
        conditions=conditions,
        exceptions=exceptions,
        risk=risk,
        tags=tags_for(text),
    )
    confidence = 0.5
    if subject_scope or re.match(r"(?:always|must|should|required|never|do not|don't|avoid|ask|confirm|request|" + "|".join(DIRECTIVE_VERBS) + r")\b", lowered):
        # An explicit imperative at clause start is materially safer to
        # structure than a directive inferred from topical keywords alone.
        confidence += 0.30
    if candidate.inherited_category:
        confidence += 0.18
    if len(target) >= 3:
        confidence += 0.12
    if conditions or exceptions:
        confidence += 0.06
    if candidate.operational_confidence >= 0.6:
        confidence += 0.04
    return [policy], min(confidence, 1.0), analysis


def _analysis_metadata(analysis: ClauseParseResult) -> dict[str, object]:
    return {
        "reason_code": analysis.reason_code,
        "evidence": list(analysis.evidence),
        "policy_shape": analysis.reason_code.removeprefix("unique_") if analysis.status == "structured" else None,
        "subject_available": bool(analysis.subject),
        "predicate_kind": analysis.predicate_kind,
        "object_cardinality": len(analysis.objects),
        "operators": analysis.operators,
        "attachment": "policy" if analysis.condition or analysis.exceptions else None,
        "ambiguous": analysis.status == "ambiguous",
    }


def _risk_floor(policy: PolicyAtom, source_risk: str) -> PolicyAtom:
    levels = {"low": 0, "medium": 1, "high": 2}
    effective = source_risk if levels[source_risk] > levels[policy.risk] else policy.risk
    values = policy.payload()
    values["risk"] = effective
    return PolicyAtom(**values)


def _custom_policy_result(candidate: InstructionCandidate, rules: list[CustomPolicyRule], risk: str) -> ResolutionResult | None:
    matches = matching_custom_policy_rules(candidate.text, rules)
    if not matches:
        return None
    policies = {_risk_floor(rule.policy, risk).fingerprint(): _risk_floor(rule.policy, risk) for rule in matches}
    location = {"source": candidate.source, "line": candidate.line}
    if len(policies) == 1:
        policy = next(iter(policies.values()))
        return ResolutionResult(
            policy=policy,
            resolutions=[CandidateResolution(
                candidate_id=candidate.id,
                destination="policy",
                policy_id=policy.id,
                reason="matched exact custom policy rule",
                reason_code="custom_policy_exact",
                evidence=[f"custom_rule:{rule.id}" for rule in sorted(matches, key=lambda item: item.id)],
                policy_shape="custom_policy",
                subject_available=bool(policy.semantic_expression().terms()),
                predicate_kind=policy.semantic_expression().kind if policy.semantic_expression().op == "atomic" else None,
                object_cardinality=len(policy.semantic_expression().objects) if policy.semantic_expression().op == "atomic" else 0,
                operators=[policy.semantic_expression().op],
                attachment="policy" if policy.condition_expression or policy.exception_expressions else None,
                risk=policy.risk,
                **location,
            )],
        )
    rule_ids = sorted(rule.id for rule in matches)
    conflict_id = "custom_policy_conflict_" + hashlib.sha256("\0".join(rule_ids).encode("utf-8")).hexdigest()[:12]
    preserved = PreservedDirective(category=category_for(candidate), text=candidate.text, risk=risk, tags=tags_for(candidate.text))
    return ResolutionResult(
        preserved=preserved,
        resolutions=[CandidateResolution(
            candidate_id=candidate.id,
            destination="preserve",
            preserve_id=preserved.id,
            reason="incompatible exact custom policy rules matched",
            reason_code="custom_policy_conflict",
            evidence=[f"custom_rule:{rule_id}" for rule_id in rule_ids],
            ambiguous=True,
            risk=risk,
            **location,
        )],
        conflicts=[ConflictFinding(
            id=conflict_id,
            semantic_units=[policy.id for policy in policies.values()],
            source_files=[candidate.source],
            line_numbers=[candidate.line],
            severity="high",
            suggested_fix="Remove or reconcile incompatible exact custom policy rules: " + ", ".join(rule_ids),
        )],
    )


def _best_matches(candidate: InstructionCandidate, custom_rules: list[SemanticRule], registry_rules: list[SemanticRule], adapter: str) -> list[SemanticMatch]:
    """Custom rules take precedence; registry ties remain explicit ledger rows."""
    for rules in (custom_rules, registry_rules):
        matches: list[tuple[SemanticRule, float, list[str]]] = []
        for rule in rules:
            confidence, signals = score_rule(rule, candidate, adapter)
            if confidence >= 0.52:
                matches.append((rule, confidence, signals))
        if matches:
            # Keep distinct matching registry semantics (for example credentials
            # and API keys) but never fall through to the registry after a custom
            # rule has claimed the candidate.
            return [
                SemanticMatch(semantic_unit=rule.id, category=rule.category, confidence=confidence, signals=signals, candidate=candidate)
                for rule, confidence, signals in sorted(matches, key=lambda item: (-item[1], item[0].id))
            ]
    return []


def resolve_candidate(
    candidate: InstructionCandidate,
    custom_policy_rules: list[CustomPolicyRule],
    custom_rules: list[SemanticRule],
    registry_rules: list[SemanticRule],
    adapter: str,
) -> ResolutionResult:
    location = {"source": candidate.source, "line": candidate.line}
    if not is_operational(candidate, adapter):
        reason = (
            "blockquote outside an instruction adapter"
            if candidate.block_type == "blockquote" and adapter not in INSTRUCTION_ADAPTERS
            else candidate.reasoning_summary or candidate.intent
        )
        return ResolutionResult(
            resolutions=[CandidateResolution(candidate_id=candidate.id, destination="non_operational", reason=reason, risk=classify_risk(candidate.text), **location)]
        )
    risk = classify_risk(candidate.text)
    candidate.risk = risk
    custom_policy = _custom_policy_result(candidate, custom_policy_rules, risk)
    if custom_policy is not None:
        return custom_policy
    matches = _best_matches(candidate, custom_rules, registry_rules, adapter)
    if matches:
        candidate.semantic_unit = matches[0].semantic_unit
        candidate.semantic_confidence = matches[0].confidence
        return ResolutionResult(
            matches=matches,
            resolutions=[
                CandidateResolution(candidate_id=candidate.id, destination="canonical", canonical_id=match.semantic_unit, reason="matched semantic registry", risk=risk, **location)
                for match in matches
            ],
        )
    policies, confidence, analysis = _derive_policy(candidate)
    threshold = 0.90 if risk == "high" else 0.80
    if policies and confidence >= threshold:
        policy_ids = [policy.id for policy in policies]
        return ResolutionResult(
            policy=policies[0] if len(policies) == 1 else None,
            policies=policies if len(policies) > 1 else [],
            resolutions=[CandidateResolution(candidate_id=candidate.id, destination="policy", policy_id=policy_ids[0], policy_ids=policy_ids, reason=f"structured policy confidence {confidence:.2f}", risk=risk, **location, **_analysis_metadata(analysis))],
        )
    category = category_for(candidate)
    preserved = PreservedDirective(category=category, text=candidate.text, risk=risk, tags=tags_for(candidate.text))
    return ResolutionResult(
        preserved=preserved,
        resolutions=[CandidateResolution(candidate_id=candidate.id, destination="preserve", preserve_id=preserved.id, reason=f"policy confidence {confidence:.2f} below {threshold:.2f}", risk=risk, **location, **_analysis_metadata(analysis))],
    )
