"""Deterministic, evidence-producing parser for `.glp 0.2` policy clauses."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Literal

from ..core.models import AttachedExpression, PolicyAtom, PolicyExpression, PolicyLink, RiskLevel, RuleCategory


ParseStatus = Literal["structured", "ambiguous", "unsupported"]

ACTION_PREDICATES = {
    "accept", "access", "add", "aim", "apply", "ask", "assume", "attribute", "broaden", "call", "change", "check", "classify", "close", "combine", "commit", "contain",
    "create", "delete", "deploy", "document", "edit", "ensure", "expose",
    "cite", "defer", "drop", "duplicate", "encourage", "export", "fix", "follow", "generate", "hand_edit", "hardcode", "ignore", "import", "include", "inspect", "introduce", "invoke", "link",
    "invent", "keep", "kill", "make", "mix", "modify", "narrate", "open", "pass", "pin", "prefer", "preserve",
    "normalize", "print", "provide", "provision", "push", "put", "read", "rely", "remove", "report", "request", "require", "reserve", "respond", "respect", "restore", "route", "run", "scope", "split", "start", "state", "stop", "store", "summarize", "target", "update", "warn",
    "use", "validate", "verify", "write",
}
VAGUE_TERMS = {"appropriate", "judgment", "relevant", "unknown", "undocumented", "unspecified"}
PRONOUNS = {"he", "her", "him", "it", "she", "that", "their", "them", "these", "they", "this", "those"}
NARRATIVE_TERMS = {"documentation", "example", "explains", "explain", "guide", "says", "say"}


def normalise_term(value: str) -> str:
    value = value.strip(" .;:")
    value = re.sub(r"['’]s\b", "", value)
    value = re.sub(r"[`'\"]", "", value)
    value = re.sub(r"\s+", "_", value.lower())
    return re.sub(r"[^a-z0-9._/:-]+", "_", value).strip("_")


@dataclass(frozen=True)
class ClauseContext:
    antecedent: str | None = None


@dataclass(frozen=True)
class LinkedStatement:
    category: RuleCategory
    expression: PolicyExpression


@dataclass(frozen=True)
class ClauseParseResult:
    status: ParseStatus
    reason_code: str
    expression: PolicyExpression | None = None
    category: RuleCategory | None = None
    scope: tuple[str, ...] = ()
    condition: AttachedExpression | None = None
    exceptions: tuple[AttachedExpression, ...] = ()
    subject: tuple[str, ...] = ()
    predicate: str | None = None
    objects: tuple[str, ...] = ()
    modality: str | None = None
    negated: bool = False
    evidence: tuple[str, ...] = ()
    alternatives: tuple[str, ...] = ()
    linked_statements: tuple[LinkedStatement, ...] = ()

    @property
    def predicate_kind(self) -> str | None:
        expression = self.expression
        while expression is not None and expression.op == "not":
            expression = expression.operands[0]
        return expression.kind if expression and expression.op == "atomic" else None

    @property
    def operators(self) -> list[str]:
        values: list[str] = []

        def visit(expression: PolicyExpression | None) -> None:
            if expression is None:
                return
            values.append(expression.op)
            for operand in expression.operands:
                visit(operand)

        visit(self.expression)
        for statement in self.linked_statements:
            visit(statement.expression)
        if self.condition:
            visit(self.condition.expression)
        for exception in self.exceptions:
            visit(exception.expression)
        return sorted(dict.fromkeys(values))

    def to_policy(self, fallback_category: RuleCategory, risk: RiskLevel, tags: list[str]) -> PolicyAtom | None:
        policies = self.to_policies(fallback_category, risk, tags)
        if len(policies) != 1:
            return None
        return policies[0]

    def to_policies(self, fallback_category: RuleCategory, risk: RiskLevel, tags: list[str]) -> list[PolicyAtom]:
        if self.status != "structured":
            return []
        if self.expression is not None:
            return [PolicyAtom(
                category=self.category or fallback_category,
                expression=self.expression,
                scope=list(self.scope),
                condition_expression=self.condition,
                exception_expressions=list(self.exceptions),
                risk=risk,
                tags=tags,
            )]
        if len(self.linked_statements) < 2:
            return []
        components = sorted(
            self.linked_statements,
            key=lambda item: json.dumps({"category": item.category, "expression": item.expression.payload()}, sort_keys=True, separators=(",", ":")),
        )
        group_payload = {
            "relation": "inseparable",
            "components": [{"category": item.category, "expression": item.expression.payload()} for item in components],
            "scope": list(self.scope),
            "condition": self.condition.payload() if self.condition else None,
            "exceptions": [item.payload() for item in self.exceptions],
            "risk": risk,
            "tags": sorted(tags),
        }
        encoded = json.dumps(group_payload, sort_keys=True, separators=(",", ":"))
        group_id = "g_" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:12]
        return [
            PolicyAtom(
                category=statement.category,
                expression=statement.expression,
                scope=list(self.scope),
                condition_expression=self.condition,
                exception_expressions=list(self.exceptions),
                risk=risk,
                tags=tags,
                link=PolicyLink(group=group_id, relation="inseparable", order=index),
            )
            for index, statement in enumerate(components)
        ]


def _reject(reason: str, *, ambiguous: bool = False, evidence: list[str] | None = None, alternatives: list[str] | None = None) -> ClauseParseResult:
    return ClauseParseResult(
        status="ambiguous" if ambiguous else "unsupported",
        reason_code=reason,
        evidence=tuple(evidence or []),
        alternatives=tuple(alternatives or []),
    )


def _contains_vague_or_pronoun(value: str) -> str | None:
    words = set(re.findall(r"[a-z]+", value.lower()))
    if words & VAGUE_TERMS:
        return "vague_reference"
    if words & PRONOUNS:
        return "pronoun_reference"
    return None


def _condition_expression(text: str) -> PolicyExpression | None:
    text = " ".join(text.strip(" .;:").split())
    if re.fullmatch(r"intentionally required", text, flags=re.IGNORECASE):
        return _atomic("state", "policy_action", "be", ["intentionally_required"])
    requested_work = re.fullmatch(
        r"(?:the\s+)?user\s+has\s+asked\s+you\s+to\s+(.+?)\s+work\s+on\s+(.+)",
        text,
        flags=re.IGNORECASE,
    )
    if requested_work:
        actions = [normalise_term(value) for value in re.split(r"\s*(?:,|\bor\b)\s*", requested_work.group(1), flags=re.IGNORECASE) if value.strip()]
        target = normalise_term(requested_work.group(2))
        if actions and target and all(action in {"fix", "improve", "land"} for action in actions):
            atoms = [_atomic("action", "user", f"ask_agent_to_{action}", [target]) for action in actions]
            return atoms[0] if len(atoms) == 1 else PolicyExpression(op="any", operands=atoms)
    needed_unrequested = re.fullmatch(
        r"(.+?)\s+is\s+needed\s+and\s+(?:the\s+)?user\s+did\s+not\s+explicitly\s+ask\s+for\s+it",
        text,
        flags=re.IGNORECASE,
    )
    if needed_unrequested and not _contains_vague_or_pronoun(needed_unrequested.group(1)):
        target = normalise_term(needed_unrequested.group(1))
        return PolicyExpression(op="all", operands=[
            _atomic("state", target, "be", ["needed"]),
            PolicyExpression(op="not", operands=[_atomic("action", "user", "explicitly_ask_for", [target])]),
        ])
    relies = re.fullmatch(r"(.+?)\s+(?:already\s+)?relies\s+on\s+(.+)", text, flags=re.IGNORECASE)
    if relies and not _contains_vague_or_pronoun(relies.group(1)):
        subject = normalise_term(relies.group(1))
        objects = [normalise_term(value) for value in re.split(r"\s*(?:,|\band\b)\s*", relies.group(2), flags=re.IGNORECASE) if value.strip()]
        if subject and objects and all(objects):
            return _atomic("state", subject, "rely_on", objects)
    for separator, operator in ((" or ", "any"), (" and ", "all")):
        parts = [part.strip() for part in text.split(separator)]
        if len(parts) > 1:
            operands = [_condition_expression(part) for part in parts]
            if all(operands):
                return PolicyExpression(op=operator, operands=operands)  # type: ignore[arg-type]
            return None
    if text.lower().startswith("not "):
        operand = _condition_expression(text[4:])
        return PolicyExpression(op="not", operands=[operand]) if operand else None
    exists = re.fullmatch(r"(.+?)\s+exists", text, flags=re.IGNORECASE)
    if exists and not _contains_vague_or_pronoun(exists.group(1)):
        subject = normalise_term(exists.group(1))
        return _atomic("state", subject, "exist", []) if subject else None
    match = re.fullmatch(r"(.+?)\s+(is|are|has|needs|uses|equals|contains)\s+(.+)", text, flags=re.IGNORECASE)
    if match:
        if _contains_vague_or_pronoun(match.group(1)) or _contains_vague_or_pronoun(match.group(3)):
            return None
        subject = normalise_term(match.group(1))
        object_value = normalise_term(match.group(3))
        if not subject or not object_value:
            return None
        predicate = "need" if match.group(2).lower() == "needs" else match.group(2).lower()
        return PolicyExpression(op="atomic", kind="state", subject=[subject], predicate=predicate, objects=[object_value])
    action_condition = _simple_action_condition(text)
    if action_condition is not None:
        return action_condition
    relation = re.fullmatch(r"(.+?)\s+(only\s+|explicitly\s+)?(changes|approves)(?:\s+(.+))?", text, flags=re.IGNORECASE)
    if not relation or _contains_vague_or_pronoun(relation.group(1)) or (relation.group(4) and _contains_vague_or_pronoun(relation.group(4))):
        return None
    subject = normalise_term(relation.group(1))
    modifier = (relation.group(2) or "").strip().lower()
    predicate = "_".join(value for value in (modifier, relation.group(3).lower()) if value)
    objects = [normalise_term(relation.group(4))] if relation.group(4) else []
    if not subject or any(not value for value in objects):
        return None
    return PolicyExpression(op="atomic", kind="state", subject=[subject], predicate=predicate, objects=objects)


def _simple_action_condition(text: str) -> PolicyExpression | None:
    match = re.fullmatch(r"(.+?)\s+([a-z][a-z_-]*)\s+(.+)", text.strip(), flags=re.IGNORECASE)
    if not match:
        return None
    raw_subject, predicate, raw_object = match.group(1), match.group(2).lower().replace("-", "_"), match.group(3)
    if predicate not in ACTION_PREDICATES or _contains_vague_or_pronoun(raw_subject) or _contains_vague_or_pronoun(raw_object):
        return None
    subject = "agent" if raw_subject.lower() == "you" else normalise_term(raw_subject)
    object_value = normalise_term(raw_object)
    return _atomic("action", subject, predicate, [object_value]) if subject and object_value else None


def _requirement_expression(text: str) -> PolicyExpression | None:
    values = [re.sub(r"^(?:an?|the)\s+", "", part.strip(), flags=re.IGNORECASE) for part in re.split(r"\s+and\s+", text, flags=re.IGNORECASE)]
    if not values or any(_contains_vague_or_pronoun(value) for value in values):
        return None
    objects = [normalise_term(value) for value in values]
    if any(not value for value in objects):
        return None
    atoms = [_atomic("state", "policy_context", "has", [value]) for value in objects]
    return atoms[0] if len(atoms) == 1 else PolicyExpression(op="all", operands=atoms)


def _split_route_object(value: str) -> list[str] | None:
    parts = re.fullmatch(r"(.+?)\s+through\s+(.+)", value, flags=re.IGNORECASE)
    if not parts:
        return [normalise_term(value)]
    direct, mediator = normalise_term(parts.group(1)), normalise_term(parts.group(2))
    return [direct, mediator] if direct and mediator else None


def _atomic(kind: str, subject: str, predicate: str, objects: list[str]) -> PolicyExpression:
    return PolicyExpression(op="atomic", kind=kind, subject=[subject], predicate=predicate, objects=objects)  # type: ignore[arg-type]


def _negative_atoms(kind: str, subjects: list[str], predicate: str, objects: list[str]) -> PolicyExpression:
    operands = [PolicyExpression(op="not", operands=[_atomic(kind, subject, predicate, [object_value] if object_value else [])]) for subject in subjects for object_value in (objects or [""])]
    return operands[0] if len(operands) == 1 else PolicyExpression(op="all", operands=operands)


def _or_objects(value: str) -> list[str] | None:
    if re.search(r"\band\b", value, flags=re.IGNORECASE):
        return None
    parts = [normalise_term(part) for part in re.split(r"\s+or\s+", value, flags=re.IGNORECASE)]
    return parts if all(parts) else None


def _and_objects(value: str) -> list[str] | None:
    parts = [part.strip() for part in re.split(r"\s+and\s+", value, flags=re.IGNORECASE)]
    if len(parts) < 2:
        return [normalise_term(value)]
    if any(re.match(r"^[a-z][a-z_-]*\s+", part, flags=re.IGNORECASE) and part.split()[0].lower().replace("-", "_") in ACTION_PREDICATES for part in parts[1:]):
        return None
    normalized = [normalise_term(part) for part in parts]
    return normalized if all(normalized) else None


def _condition_subject(expression: PolicyExpression | None) -> str | None:
    if expression is None or expression.op != "atomic" or len(expression.subject) != 1:
        return None
    return expression.subject[0]


def _for_context_expression(text: str) -> PolicyExpression | None:
    """Convert a bounded ``For <context>`` prefix into a policy condition."""
    raw = " ".join(text.strip(" .;:").split())
    typed = re.fullmatch(r"(.+?)\s+(builds?|deployments?|environments?|operations?|runs?)", raw, flags=re.IGNORECASE)
    if typed:
        values_text, context_noun = typed.group(1), typed.group(2).lower()
        context_subject = {
            "build": "build_environment", "builds": "build_environment",
            "deployment": "deployment_environment", "deployments": "deployment_environment",
            "environment": "environment", "environments": "environment",
            "operation": "operation_mode", "operations": "operation_mode",
            "run": "runtime_mode", "runs": "runtime_mode",
        }[context_noun]
    else:
        values_text, context_subject = raw, "environment"
    values = [
        normalise_term(re.sub(r"^(?:a|an|the)\s+", "", value.strip(), flags=re.IGNORECASE))
        for value in re.split(r"\s+(?:and|or)\s+", values_text, flags=re.IGNORECASE)
    ]
    if not values or any(not value or _contains_vague_or_pronoun(value) for value in values):
        return None
    atoms = [_atomic("state", context_subject, "be", [value]) for value in values]
    return atoms[0] if len(atoms) == 1 else PolicyExpression(op="any", operands=atoms)


def _local_referent(context: ClauseContext | None) -> tuple[str, tuple[str, ...]] | None:
    if context is None or not context.antecedent:
        return None
    antecedent = context.antecedent.replace("**", "").strip()
    located = re.fullmatch(r"([A-Za-z][A-Za-z0-9 _/-]{0,60}):\s+Located\s+at\s+`([^`]+)`(?:\s+\(.+\))?\.?", antecedent, flags=re.IGNORECASE)
    if located:
        return normalise_term(located.group(1)), (located.group(2),)
    label = re.match(r"^`([^`]+)`\s*:\s*.+", antecedent)
    if label:
        return normalise_term(label.group(1)), ()
    subject = re.match(r"^(.{1,120}?)\s+(?:is|are)\s+.+", antecedent, flags=re.IGNORECASE)
    if subject and not _contains_vague_or_pronoun(subject.group(1)):
        value = normalise_term(subject.group(1))
        if value:
            return value, ()
    return None


def _leading_condition_split(text: str) -> tuple[PolicyExpression, str] | None:
    prefix = re.match(r"^(?:if|when)\s+", text, flags=re.IGNORECASE)
    if not prefix:
        return None
    verb_pattern = "|".join(sorted(ACTION_PREDICATES))
    policy_start = re.compile(
        r"^(?:(?:always|never|please|do not|don't|avoid|ask|confirm)\b|"
        r"(?:" + verb_pattern + r")\b|"
        r"[^,]{1,120}\s+(?:must|should|may|never|is|are|has|have|needs|is required to|are required to|has durable authorization to|have durable authorization to)\b)",
        flags=re.IGNORECASE,
    )
    interpretations: list[tuple[PolicyExpression, str]] = []
    for boundary in re.finditer(r",\s+", text[prefix.end():]):
        absolute = prefix.end() + boundary.start()
        condition_text = text[prefix.end():absolute]
        remainder = text[prefix.end() + boundary.end():]
        expression = _condition_expression(condition_text)
        if expression is not None and policy_start.match(remainder):
            interpretations.append((expression, remainder))
    if len(interpretations) == 1:
        return interpretations[0]
    requested_work = [
        item
        for item in interpretations
        if item[0].op == "any" and all(
            operand.op == "atomic" and (operand.predicate or "").startswith("ask_agent_to_")
            for operand in item[0].operands
        )
    ]
    return requested_work[0] if len(requested_work) == 1 else None


def parse_policy_clause(text: str, fallback_category: RuleCategory, context: ClauseContext | None = None) -> ClauseParseResult:
    """Return one unique structured interpretation or an auditable rejection."""
    core = " ".join(text.strip().split())
    evidence: list[str] = []
    condition: AttachedExpression | None = None
    exceptions: tuple[AttachedExpression, ...] = ()

    if re.search(r"\b(?:it|this|those resources)\b", core, flags=re.IGNORECASE):
        referent = _local_referent(context)
        if referent:
            referent_value, referent_scope = referent
            core = re.sub(r"\bthose resources\b|\bit\b|\bthis\b", referent_value.replace("_", " "), core, flags=re.IGNORECASE)
            evidence.append("coreference:local_antecedent")
        else:
            referent_scope = ()
    else:
        referent_scope = ()

    for_prefix = re.match(r"^for\s+(.+?),\s+(.+)$", core, flags=re.IGNORECASE)
    if for_prefix:
        parsed_context = _for_context_expression(for_prefix.group(1))
        if parsed_context is None:
            return _reject("ambiguous_condition_attachment", ambiguous=True, evidence=["leading_for_context"])
        condition = AttachedExpression(attachment="policy", expression=parsed_context)
        core = for_prefix.group(2)
        evidence.append("condition:policy")

    has_leading_condition = bool(re.match(r"^(?:if|when)\s+", core, flags=re.IGNORECASE))
    leading = _leading_condition_split(core)
    if has_leading_condition:
        if leading is None:
            return _reject("ambiguous_condition_attachment", ambiguous=True, evidence=["leading_condition"])
        condition = AttachedExpression(attachment="policy", expression=leading[0])
        core = leading[1]
        evidence.append("condition:policy")

    if condition and re.search(r"\bthat branch(?:'s)?\b", core, flags=re.IGNORECASE):
        condition_objects = {
            value
            for value in condition.expression.terms()
            if value.endswith("branch") or value.endswith("_branch")
        }
        if len(condition_objects) == 1:
            core = re.sub(r"\bthat branch(?:'s)?\b", "requested branch's", core, flags=re.IGNORECASE)
            evidence.append("coreference:condition_object")

    rationale_match = re.search(r"\s+because\s+.+$", core, flags=re.IGNORECASE)
    if rationale_match:
        core = core[: rationale_match.start()]
        evidence.append("rationale:non_operational")

    example_suffix = re.search(r":\s+.+(?:,|\bor\b).+$", core, flags=re.IGNORECASE)
    if example_suffix and re.match(r"^(?:always\s+|please\s+)?(?:" + "|".join(sorted(ACTION_PREDICATES)) + r")\b", core, flags=re.IGNORECASE):
        core = core[: example_suffix.start()]
        evidence.append("examples:non_normative")

    trailing_when = re.search(r"\s+(?:only\s+)?when\s+(.+)$", core, flags=re.IGNORECASE)
    if trailing_when and not re.search(r"\bbelong\s+here\s+only\s+when\b", core, flags=re.IGNORECASE):
        if condition is not None:
            return _reject("ambiguous_condition_attachment", ambiguous=True, evidence=[*evidence, "trailing_condition"])
        parsed_condition = _condition_expression(trailing_when.group(1))
        if parsed_condition is None:
            return _reject("ambiguous_condition_attachment", ambiguous=True, evidence=[*evidence, "trailing_condition"])
        condition = AttachedExpression(attachment="policy", expression=parsed_condition)
        core = core[: trailing_when.start()]
        evidence.append("condition:policy")

    exception_match = re.search(r"\s+unless\s+(.+)$", core, flags=re.IGNORECASE)
    if exception_match:
        parsed_exception = _condition_expression(exception_match.group(1))
        if parsed_exception is None:
            return _reject("ambiguous_exception_attachment", ambiguous=True, evidence=[*evidence, "trailing_exception"])
        exceptions = (AttachedExpression(attachment="policy", expression=parsed_exception),)
        core = core[: exception_match.start()]
        evidence.append("exception:policy")

    without_match = re.search(r"\s+without\s+(.+)$", core, flags=re.IGNORECASE)
    if without_match and re.match(r"^(?:never|do not|don't)\b", core, flags=re.IGNORECASE):
        parsed_exception = _requirement_expression(without_match.group(1))
        if parsed_exception is None:
            return _reject("ambiguous_exception_attachment", ambiguous=True, evidence=[*evidence, "trailing_without"])
        exceptions = (AttachedExpression(attachment="policy", expression=parsed_exception),)
        core = core[: without_match.start()]
        evidence.append("exception:policy")

    lowered = core.lower().strip(" .")
    if set(re.findall(r"[a-z]+", lowered)) & NARRATIVE_TERMS:
        return _reject("narrative_attribution", evidence=evidence)

    condition_subject = _condition_subject(condition.expression) if condition else None
    if condition_subject and re.match(r"^it\s+(?:is|has|needs)\b", core, flags=re.IGNORECASE):
        core = re.sub(r"^it\b", condition_subject.replace("_", " "), core, count=1, flags=re.IGNORECASE)
        evidence.append("coreference:condition_subject")

    deictic_belonging = re.fullmatch(
        r"(.+?)\s+belong\s+here\s+only\s+when\s+they\s+do\s+not\s+apply\s+to\s+(.+?)\.?",
        core,
        flags=re.IGNORECASE,
    )
    if deictic_belonging:
        raw_subject, raw_object = deictic_belonging.group(1), deictic_belonging.group(2)
        rejection = _contains_vague_or_pronoun(raw_subject) or _contains_vague_or_pronoun(raw_object)
        if rejection or len(raw_subject.split()) > 8:
            return _reject(rejection or "subject_too_broad", ambiguous=True, evidence=[*evidence, "deictic:current_document"])
        subject, object_value = normalise_term(raw_subject), normalise_term(raw_object)
        expression = _atomic("state", subject, "belong_to", ["current_document"])
        condition_expression = PolicyExpression(
            op="not",
            operands=[_atomic("state", subject, "apply_to", [object_value])],
        )
        return ClauseParseResult(
            status="structured", reason_code="unique_deictic_belonging", expression=expression, category=fallback_category,
            condition=AttachedExpression(attachment="policy", expression=condition_expression),
            subject=(subject,), predicate="belong_to", objects=("current_document",),
            evidence=tuple([*evidence, "deictic:current_document", "coreference:subject", "condition:policy", "unique_parse"]),
        )

    avoided = re.fullmatch(r"avoid\s+(.+?)\.?", core, flags=re.IGNORECASE)
    if avoided:
        raw_object = avoided.group(1)
        rejection = _contains_vague_or_pronoun(raw_object)
        if rejection:
            return _reject(rejection, ambiguous=True, evidence=[*evidence, "predicate:avoid"])
        if re.search(r"\band\b|\bor\b", raw_object, flags=re.IGNORECASE):
            return _reject("ambiguous_coordination", ambiguous=True, evidence=[*evidence, "predicate:avoid"])
        object_value = normalise_term(raw_object)
        expression = _atomic("action", "agent", "avoid", [object_value])
        return ClauseParseResult(
            status="structured", reason_code="unique_avoid_action", expression=expression, category="must",
            condition=condition, exceptions=exceptions,
            subject=("agent",), predicate="avoid", objects=(object_value,), modality="avoid",
            evidence=tuple([*evidence, "subject:implicit_agent", "predicate:action", "unique_parse"]),
        )

    denied_command = re.fullmatch(r"never\s+`([^`]+)`\.?", core, flags=re.IGNORECASE)
    if denied_command:
        object_value = normalise_term(denied_command.group(1))
        expression = PolicyExpression(op="not", operands=[_atomic("action", "agent", "run", [object_value])])
        return ClauseParseResult(
            status="structured", reason_code="unique_command_denial", expression=expression, category="must",
            subject=("agent",), predicate="run", objects=(object_value,), modality="never", negated=True,
            evidence=tuple([*evidence, "subject:implicit_agent", "predicate:action", "unique_parse"]),
        )

    contrasted = re.fullmatch(r".+?,\s+but\s+(?:the\s+)?(.+?)\s+still\s+requires?\s+(.+?)\.?", core, flags=re.IGNORECASE)
    if contrasted and not _contains_vague_or_pronoun(contrasted.group(1)) and not _contains_vague_or_pronoun(contrasted.group(2)):
        subject = normalise_term(contrasted.group(1))
        relation_object = re.fullmatch(r"(?:the\s+same\s+)?(`?[\w:]+`?\s+permission)(?:\s+as\s+(.+))?", contrasted.group(2), flags=re.IGNORECASE)
        if not relation_object:
            return _reject("ambiguous_relation_object", ambiguous=True, evidence=[*evidence, "contrast:but"])
        contrast_objects = [normalise_term(relation_object.group(1))]
        if relation_object.group(2):
            contrast_objects.append(normalise_term(relation_object.group(2)))
        expression = _atomic("state", subject, "require", contrast_objects)
        return ClauseParseResult(
            status="structured", reason_code="unique_contrastive_relation", expression=expression, category=fallback_category,
            subject=(subject,), predicate="require", objects=tuple(contrast_objects), modality="still_requires", negated=False,
            evidence=tuple([*evidence, "contrast:but", "predicate:state", "unique_parse"]),
        )
    mixed_modal = re.fullmatch(
        r"(.+?)\s+may\s+([a-z][a-z_-]*)\s+(?:from\s+)?(.+?)\s+but\s+never\s+([a-z][a-z_-]*)\s+(.+?)\.?",
        core,
        flags=re.IGNORECASE,
    )
    if mixed_modal:
        raw_subject, allow_predicate, allow_object, deny_predicate, deny_object = mixed_modal.groups()
        if any(_contains_vague_or_pronoun(value) for value in (raw_subject, allow_object, deny_object)):
            return _reject("pronoun_reference", ambiguous=True, evidence=evidence)
        allow_predicate = allow_predicate.lower().replace("-", "_")
        deny_predicate = deny_predicate.lower().replace("-", "_")
        if allow_predicate not in ACTION_PREDICATES or deny_predicate not in ACTION_PREDICATES:
            return _reject("unsupported_action_predicate", evidence=evidence)
        subject = "agent" if raw_subject.lower() == "you" else normalise_term(raw_subject)
        statements = (
            LinkedStatement("allow", _atomic("action", subject, allow_predicate, [normalise_term(allow_object)])),
            LinkedStatement("deny", _atomic("action", subject, deny_predicate, [normalise_term(deny_object)])),
        )
        return ClauseParseResult(
            status="structured", reason_code="unique_mixed_modal_compound", linked_statements=statements,
            scope=referent_scope, subject=(subject,), predicate="mixed_modal", objects=(normalise_term(allow_object), normalise_term(deny_object)),
            evidence=tuple([*evidence, "link:inseparable", "unique_parse"]),
        )

    durable_authorization = re.fullmatch(
        r"you\s+have\s+durable\s+authorization\s+to\s+`?(?:[a-z][a-z_-]*\s+)?([a-z][a-z_-]*)`?\s+and\s+`?(?:[a-z][a-z_-]*\s+)?([a-z][a-z_-]*)`?\s+to\s+(.+?)\s+without\s+per-step\s+confirmation\.?",
        core,
        flags=re.IGNORECASE,
    )
    if durable_authorization:
        first, second, raw_object = durable_authorization.groups()
        if re.search(r"\bthat branch(?:'s)?\b", raw_object, flags=re.IGNORECASE) and condition is not None:
            raw_object = re.sub(r"\bthat branch(?:'s)?\b", "requested branch's", raw_object, flags=re.IGNORECASE)
            evidence.append("coreference:condition_object")
        if first.lower() not in ACTION_PREDICATES or second.lower() not in ACTION_PREDICATES or _contains_vague_or_pronoun(raw_object):
            return _reject("unsupported_predicate", evidence=evidence)
        object_value = normalise_term(raw_object)
        expression = PolicyExpression(op="all", operands=[
            _atomic("action", "agent", first.lower(), [object_value]),
            _atomic("action", "agent", second.lower(), [object_value]),
        ])
        return ClauseParseResult(
            status="structured", reason_code="unique_durable_authorization", expression=expression, category="allow",
            condition=condition, subject=("agent",), predicate="durable_authorization", objects=(object_value,), modality="authorization",
            evidence=tuple([*evidence, "category:allow", "approval:waived", "unique_parse"]),
        )

    approval_and_statement = re.fullmatch(
        r"ask\s+permission\s+first\s+and\s+state\s+(?:the\s+)?(.+?)\s+required\.?",
        core,
        flags=re.IGNORECASE,
    )
    if approval_and_statement:
        change = normalise_term(approval_and_statement.group(1))
        if not change or _contains_vague_or_pronoun(change):
            return _reject("vague_reference", ambiguous=True, evidence=evidence)
        statements = (
            LinkedStatement("ask", _atomic("action", "agent", "make", [change])),
            LinkedStatement("must", _atomic("action", "agent", "state", [f"{change}_required"])),
        )
        return ClauseParseResult(
            status="structured", reason_code="unique_approval_statement_compound", linked_statements=statements,
            condition=condition, subject=("agent",), predicate="approval_statement", objects=(change,),
            evidence=tuple([*evidence, "link:inseparable", "unique_parse"]),
        )
    negative_imperative = re.fullmatch(r"(never|do not|don't|avoid)\s+([a-z][a-z_-]*)\s+(.+?)\.?", core, flags=re.IGNORECASE)
    if negative_imperative:
        modality, negative_predicate, raw_object = negative_imperative.group(1).lower(), negative_imperative.group(2).lower().replace("-", "_"), negative_imperative.group(3)
        rejection = _contains_vague_or_pronoun(raw_object)
        if rejection:
            return _reject(rejection, ambiguous=True, evidence=[*evidence, f"modal:{modality}"])
        if negative_predicate not in ACTION_PREDICATES:
            return _reject("unsupported_action_predicate", evidence=[*evidence, f"modal:{modality}"])
        if re.search(r"\band\b", raw_object, flags=re.IGNORECASE):
            return _reject("ambiguous_coordination", ambiguous=True, evidence=evidence, alternatives=["compound_policy", "compound_argument"])
        negative_objects = _split_route_object(raw_object) if negative_predicate == "route" else _or_objects(raw_object)
        if not negative_objects or not all(negative_objects):
            return _reject("missing_object", evidence=evidence)
        expression = _negative_atoms("action", ["agent"], negative_predicate, negative_objects)
        return ClauseParseResult(
            status="structured", reason_code="unique_negative_action", expression=expression, category="must",
            condition=condition, exceptions=exceptions, subject=("agent",), predicate=negative_predicate, objects=tuple(negative_objects),
            modality=modality, negated=True, evidence=tuple([*evidence, f"modal:{modality}", "subject:implicit_agent", "unique_parse"]),
        )

    passive_never = re.fullmatch(r"(.+?)\s+(?:is|are)\s+never\s+([a-z][a-z_-]*ed)(?:\s+(?:by|to|from)\s+(.+))?\.?", core, flags=re.IGNORECASE)
    if passive_never:
        raw_subjects = [part.strip() for part in re.split(r"\s+and\s+", passive_never.group(1), flags=re.IGNORECASE)]
        if any(_contains_vague_or_pronoun(part) for part in raw_subjects):
            return _reject("pronoun_reference", ambiguous=True, evidence=evidence)
        subjects = [normalise_term(part) for part in raw_subjects]
        passive_objects = [normalise_term(passive_never.group(3))] if passive_never.group(3) else []
        expression = _negative_atoms("passive", subjects, passive_never.group(2).lower(), passive_objects)
        return ClauseParseResult(
            status="structured", reason_code="unique_negative_passive", expression=expression, category="must",
            subject=tuple(subjects), predicate=passive_never.group(2).lower(), objects=tuple(passive_objects), modality="never", negated=True,
            evidence=tuple([*evidence, "modal:never", "predicate:passive", "unique_parse"]),
        )

    subject_never = re.fullmatch(r"(.+?)\s+never\s+([a-z][a-z_-]*)\s+(.+?)\.?", core, flags=re.IGNORECASE)
    if subject_never and subject_never.group(2).lower() in ACTION_PREDICATES:
        if _contains_vague_or_pronoun(subject_never.group(1)):
            return _reject("pronoun_reference", ambiguous=True, evidence=evidence)
        subject_never_objects = _or_objects(subject_never.group(3))
        if subject_never_objects is None:
            return _reject("ambiguous_coordination", ambiguous=True, evidence=evidence, alternatives=["compound_policy", "compound_argument"])
        subject_never_subject = normalise_term(subject_never.group(1))
        subject_never_predicate = subject_never.group(2).lower()
        expression = _negative_atoms("action", [subject_never_subject], subject_never_predicate, subject_never_objects)
        return ClauseParseResult(
            status="structured", reason_code="unique_negative_action", expression=expression, category="must",
            subject=(subject_never_subject,), predicate=subject_never_predicate, objects=tuple(subject_never_objects), modality="never", negated=True,
            evidence=tuple([*evidence, "modal:never", "predicate:action", "unique_parse"]),
        )

    bare_state = re.fullmatch(r"(.+?)\s+(is|are|has|needs)\s+(.+?)\.?", core, flags=re.IGNORECASE)
    if bare_state:
        raw_subject, relation, raw_object = bare_state.group(1), bare_state.group(2).lower(), bare_state.group(3)
        rejection = _contains_vague_or_pronoun(raw_subject) or _contains_vague_or_pronoun(raw_object)
        if rejection:
            return _reject(rejection, ambiguous=True, evidence=evidence)
        if len(raw_subject.split()) > 8:
            return _reject("subject_too_broad", ambiguous=True, evidence=evidence)
        negated_state = raw_object.lower().startswith("not ")
        if negated_state:
            raw_object = raw_object[4:]
        objects = _and_objects(raw_object)
        if objects is None:
            return _reject("ambiguous_coordination", ambiguous=True, evidence=evidence)
        subject = normalise_term(raw_subject)
        predicate = {"is": "be", "are": "be", "has": "have", "needs": "need"}[relation]
        operands = [_atomic("state", subject, predicate, [object_value]) for object_value in objects]
        state_expression = operands[0] if len(operands) == 1 else PolicyExpression(op="all", operands=operands)
        expression = PolicyExpression(op="not", operands=[state_expression]) if negated_state else state_expression
        return ClauseParseResult(
            status="structured", reason_code="unique_bare_state", expression=expression, category=fallback_category,
            condition=condition, exceptions=exceptions, subject=(subject,), predicate=predicate, objects=tuple(objects), negated=negated_state,
            evidence=tuple([*evidence, "predicate:state", "unique_parse"]),
        )

    required_state = re.fullmatch(r"(.+?)\s+required\.?", core, flags=re.IGNORECASE)
    if required_state and not _contains_vague_or_pronoun(required_state.group(1)) and len(required_state.group(1).split()) <= 8:
        subject = normalise_term(required_state.group(1))
        expression = _atomic("state", subject, "required", [])
        return ClauseParseResult(
            status="structured", reason_code="unique_required_state", expression=expression, category=fallback_category,
            condition=condition, exceptions=exceptions, subject=(subject,), predicate="required",
            evidence=tuple([*evidence, "predicate:state", "unique_parse"]),
        )

    positive_imperative = re.fullmatch(r"(?:(always|please)\s+)?([a-z][a-z_-]*)\s+(.+?)\.?", core, flags=re.IGNORECASE)
    if positive_imperative:
        modality = (positive_imperative.group(1) or "imperative").lower()
        predicate = positive_imperative.group(2).lower().replace("-", "_")
        raw_object = positive_imperative.group(3)
        if predicate in ACTION_PREDICATES and not re.search(r"\b(?:must|should|is required to|are required to)\b", raw_object, flags=re.IGNORECASE):
            rejection = _contains_vague_or_pronoun(raw_object)
            if rejection:
                return _reject(rejection, ambiguous=True, evidence=[*evidence, f"modal:{modality}"])
            if re.search(r"\b(?:before|after)\b", raw_object, flags=re.IGNORECASE):
                return _reject("temporal_sequence_required", evidence=[*evidence, f"modal:{modality}"])
            alternative_objects = bool(re.search(r"\bor\b", raw_object, flags=re.IGNORECASE))
            objects = _split_route_object(raw_object) if predicate == "route" else (_or_objects(raw_object) if alternative_objects else _and_objects(raw_object))
            if objects is None:
                return _reject("ambiguous_coordination", ambiguous=True, evidence=[*evidence, f"modal:{modality}"])
            atoms = [_atomic("action", "agent", predicate, [object_value]) for object_value in objects]
            expression = _atomic("action", "agent", predicate, objects) if predicate == "route" else (atoms[0] if len(atoms) == 1 else PolicyExpression(op="any" if alternative_objects else "all", operands=atoms))
            return ClauseParseResult(
                status="structured", reason_code="unique_positive_action", expression=expression, category=fallback_category,
                condition=condition, exceptions=exceptions, subject=("agent",), predicate=predicate, objects=tuple(objects), modality=modality,
                evidence=tuple([*evidence, f"modal:{modality}", "subject:implicit_agent", "predicate:action", "unique_parse"]),
            )

    modal = re.fullmatch(r"(.{1,120}?)\s+(must|should|is required to|are required to)\s+(not\s+)?(.+?)\.?", core, flags=re.IGNORECASE)
    if not modal:
        return _reject("unsupported_clause_shape", evidence=evidence)
    raw_subject, modality, negated, body = modal.group(1), modal.group(2).lower(), bool(modal.group(3)), modal.group(4).strip(" .")
    if len(raw_subject.split()) > 8:
        return _reject("subject_too_broad", ambiguous=True, evidence=[*evidence, f"modal:{modality}"])
    if re.search(r"\btheir\b", body, flags=re.IGNORECASE) and re.search(r"(?:s|agents|callers)\s*$", raw_subject, flags=re.IGNORECASE):
        body = re.sub(r"\btheir\b", "own", body, flags=re.IGNORECASE)
        evidence.append("possessive:reflexive")
    rejection = _contains_vague_or_pronoun(raw_subject) or _contains_vague_or_pronoun(body)
    if rejection:
        return _reject(rejection, ambiguous=True, evidence=[*evidence, f"modal:{modality}"])
    compound_state = re.fullmatch(r"belong\s+to\s+(.+?),\s+use\s+(.+?),\s+and\s+have\s+(.+?)\s*\((.+?)\s+or\s+(.+?)\)", body, flags=re.IGNORECASE)
    if compound_state:
        subject = normalise_term(raw_subject)
        belong_object = normalise_term(compound_state.group(1))
        use_object = normalise_term(compound_state.group(2))
        status_name = normalise_term(re.sub(r"\s*status\s*$", "", compound_state.group(3), flags=re.IGNORECASE) + " status")
        status_options = [normalise_term(compound_state.group(4)), normalise_term(compound_state.group(5))]
        status_any = PolicyExpression(op="any", operands=[_atomic("state", subject, f"have_{status_name}", [option]) for option in status_options])
        expression = PolicyExpression(op="all", operands=[
            _atomic("state", subject, "belong_to", [belong_object]),
            _atomic("action", subject, "use", [use_object]),
            status_any,
        ])
        return ClauseParseResult(
            status="structured", reason_code="unique_compound_state", expression=expression, category=fallback_category,
            subject=(subject,), predicate="compound_state", objects=(belong_object, use_object, *status_options), modality=modality,
            evidence=tuple([*evidence, f"modal:{modality}", "operator:all", "operator:any", "unique_parse"]),
        )
    scope: list[str] = []
    scoped = re.search(r"\s+(?:in|within)\s+(`?[-\w./]+/`?)$", body, flags=re.IGNORECASE)
    if scoped:
        scope.append(scoped.group(1).strip("`"))
        body = body[: scoped.start()]
        evidence.append("scope:repository_area")

    subject = normalise_term(raw_subject)
    modal_predicate: str
    modal_objects: list[str]
    kind: str
    passive = re.fullmatch(r"be\s+([a-z][a-z_-]*ed)(?:\s+(?:by|to|from)\s+(.+))?", body, flags=re.IGNORECASE)
    belongs = re.fullmatch(r"belong\s+to\s+(.+)", body, flags=re.IGNORECASE)
    state_relation = re.fullmatch(r"(have|need|reflect|come\s+from)\s+(.+)", body, flags=re.IGNORECASE)
    state = re.fullmatch(r"be\s+(.+)", body, flags=re.IGNORECASE)
    action = re.fullmatch(r"([a-z][a-z_-]*)\s+(.+)", body, flags=re.IGNORECASE)
    if passive:
        if passive.group(2) and re.search(r"\bor\b", passive.group(2), flags=re.IGNORECASE) and not negated:
            return _reject("ambiguous_coordination", ambiguous=True, evidence=[*evidence, f"modal:{modality}"], alternatives=["alternative_object", "compound_argument"])
        kind, modal_predicate = "passive", passive.group(1).lower()
        passive_value = passive.group(2)
        modal_objects = [normalise_term(passive_value)] if passive_value else []
    elif belongs:
        kind, modal_predicate, modal_objects = "state", "belong_to", [normalise_term(belongs.group(1))]
    elif state_relation:
        kind, modal_predicate = "state", state_relation.group(1).lower().replace(" ", "_")
        relation_objects = _and_objects(state_relation.group(2))
        if relation_objects is None:
            return _reject("ambiguous_coordination", ambiguous=True, evidence=[*evidence, f"modal:{modality}"])
        modal_objects = relation_objects
    elif state:
        kind, modal_predicate, modal_objects = "state", "be", [normalise_term(state.group(1))]
    elif action and action.group(1).lower().replace("-", "_") in ACTION_PREDICATES:
        kind, modal_predicate = "action", action.group(1).lower().replace("-", "_")
        action_objects = _split_route_object(action.group(2)) if modal_predicate == "route" else (_or_objects(action.group(2)) if negated else _and_objects(action.group(2)))
        if action_objects is None:
            return _reject("ambiguous_coordination", ambiguous=True, evidence=[*evidence, f"modal:{modality}"], alternatives=["compound_policy", "compound_argument"])
        modal_objects = action_objects
    else:
        return _reject("unsupported_predicate", evidence=[*evidence, f"modal:{modality}"])
    if any(not item for item in modal_objects):
        return _reject("missing_object", evidence=evidence)

    atomic = _atomic(kind, subject, modal_predicate, modal_objects)
    if not negated and len(modal_objects) > 1 and (kind == "state" or (kind == "action" and modal_predicate != "route")):
        expression = PolicyExpression(op="all", operands=[_atomic(kind, subject, modal_predicate, [object_value]) for object_value in modal_objects])
    else:
        expression = _negative_atoms(kind, [subject], modal_predicate, modal_objects) if negated else atomic
    return ClauseParseResult(
        status="structured", reason_code=f"unique_{kind}_predicate", expression=expression,
        category="must" if negated else fallback_category, scope=tuple(scope), condition=condition, exceptions=exceptions,
        subject=(subject,), predicate=modal_predicate, objects=tuple(modal_objects), modality=modality, negated=negated,
        evidence=tuple([*evidence, f"modal:{modality}", f"predicate:{kind}", "unique_parse"]),
    )
