from __future__ import annotations

import json
from pathlib import Path
import re
import unicodedata

from ..core.models import AttachedExpression, CustomPolicyRule, PolicyAtom, PolicyExpression, SemanticRule


def find_default_rules_file(root: Path | None = None) -> Path | None:
    base = root or Path.cwd()
    for candidate in [base / "glyph.rules.yml", base / ".glyph" / "rules.yml"]:
        if candidate.exists():
            return candidate
    return None


LIST_KEYS = {"patterns", "positive_terms", "negative_terms", "required_context_terms", "section_hints", "modal_hints"}
BOOL_KEYS = {"always_select", "safety_critical"}
POLICY_LIST_KEYS = {"scope", "tags", "exception_expressions"}


def _parse_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "yes", "1", "on"}


def _string_list(value: object) -> list[str]:
    return [str(item) for item in value] if isinstance(value, list) else []


def _parse_list(lines: list[str], start: int, parent_indent: int) -> tuple[list[str], int]:
    values: list[str] = []
    i = start
    while i < len(lines) and re.match(r"\s+-\s+", lines[i]) and len(lines[i]) - len(lines[i].lstrip()) > parent_indent:
        values.append(re.sub(r"^\s+-\s+", "", lines[i]).strip().strip('"').strip("'"))
        i += 1
    return values, i


def _scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"\"", "'"}:
        return value[1:-1]
    return value


def _load_raw_rules(path: Path | None) -> list[dict[str, object]]:
    if path is None:
        default = find_default_rules_file()
        if default is None:
            return []
        path = default
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ValueError(f"Could not read rules file {path}: {exc}") from exc
    rules: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    policy: dict[str, object] | None = None
    policy_indent = -1
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())
        if stripped.startswith("- id:"):
            if current:
                rules.append(current)
            current = {"id": _scalar(stripped.split(":", 1)[1])}
            policy = None
            policy_indent = -1
        elif stripped.startswith("- ") and current is None:
            raise ValueError(f"Malformed custom rule in {path}: rule entries must start with '- id:'")
        elif current is not None and ":" in stripped:
            key, value = stripped.split(":", 1)
            key = key.strip()
            value = _scalar(value)
            if key == "policy" and not value:
                policy = {}
                current["policy"] = policy
                policy_indent = indent
            elif policy is not None and indent > policy_indent:
                if key in POLICY_LIST_KEYS:
                    values, new_i = _parse_list(lines, i + 1, indent)
                    policy[key] = values
                    i = new_i - 1
                else:
                    policy[key] = value
            elif key in LIST_KEYS:
                policy = None
                values, new_i = _parse_list(lines, i + 1, indent)
                current[key] = values
                i = new_i - 1
            elif key in BOOL_KEYS:
                policy = None
                current[key] = _parse_bool(value)
            else:
                policy = None
                current[key] = value
        i += 1
    if current:
        rules.append(current)
    return rules


def load_custom_rules(path: Path | None) -> list[SemanticRule]:
    rules = _load_raw_rules(path)
    out: list[SemanticRule] = []
    for raw in rules:
        if raw.get("policy") is not None:
            continue
        if "id" not in raw:
            raise ValueError(f"Malformed custom rule in {path}: missing id")
        if not raw.get("patterns"):
            raise ValueError(f"Malformed custom rule in {path}: rule {raw['id']} has no patterns")
        try:
            out.append(SemanticRule(
                id=str(raw["id"]),
                category=str(raw.get("category", "must")),  # type: ignore[arg-type]
                patterns=_string_list(raw.get("patterns", [])),
                positive_terms=_string_list(raw.get("positive_terms", [])),
                negative_terms=_string_list(raw.get("negative_terms", [])),
                required_context_terms=_string_list(raw.get("required_context_terms", [])),
                section_hints=_string_list(raw.get("section_hints", [])),
                modal_hints=_string_list(raw.get("modal_hints", [])),
                rendered=str(raw.get("rendered", str(raw["id"]).replace("_", " ").capitalize() + ".")),
                severity=str(raw.get("severity", "medium")),
                safety_critical=_parse_bool(raw.get("safety_critical", False)),
                always_select=_parse_bool(raw.get("always_select", False)),
            ))
        except Exception as exc:
            raise ValueError(f"Malformed custom rule in {path}: {raw}") from exc
    return out


def _json_model(value: object, model: type[PolicyExpression] | type[AttachedExpression], rule_id: object):
    try:
        return model.model_validate(json.loads(str(value)))
    except (json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"Malformed custom policy rule {rule_id}: invalid {model.__name__}: {exc}") from exc


def load_custom_policy_rules(path: Path | None) -> list[CustomPolicyRule]:
    out: list[CustomPolicyRule] = []
    for raw in _load_raw_rules(path):
        policy_raw = raw.get("policy")
        if policy_raw is None:
            continue
        if not isinstance(policy_raw, dict):
            raise ValueError(f"Malformed custom policy rule {raw.get('id')}: policy must be a mapping")
        if raw.get("match") != "exact":
            raise ValueError(f"Malformed custom policy rule {raw.get('id')}: policy rules require match: exact")
        patterns = _string_list(raw.get("patterns", []))
        if not patterns:
            raise ValueError(f"Malformed custom policy rule {raw.get('id')}: patterns are required")
        if not policy_raw.get("expression"):
            raise ValueError(f"Malformed custom policy rule {raw.get('id')}: policy.expression is required")
        condition = policy_raw.get("condition_expression")
        exception_values = _string_list(policy_raw.get("exception_expressions", []))
        try:
            policy = PolicyAtom(
                category=str(policy_raw.get("category", raw.get("category", "must"))),  # type: ignore[arg-type]
                expression=_json_model(policy_raw["expression"], PolicyExpression, raw.get("id")),
                scope=_string_list(policy_raw.get("scope", [])),
                condition_expression=_json_model(condition, AttachedExpression, raw.get("id")) if condition else None,
                exception_expressions=[_json_model(value, AttachedExpression, raw.get("id")) for value in exception_values],
                risk=str(policy_raw.get("risk", "medium")),  # type: ignore[arg-type]
                tags=_string_list(policy_raw.get("tags", [])),
            )
            out.append(CustomPolicyRule(id=str(raw.get("id", "")), match="exact", patterns=patterns, policy=policy))
        except Exception as exc:
            if isinstance(exc, ValueError) and str(exc).startswith("Malformed custom policy"):
                raise
            raise ValueError(f"Malformed custom policy rule {raw.get('id')}: {exc}") from exc
    return out


def normalise_exact_policy_text(value: str) -> str:
    """Normalize layout only; preserve case and punctuation for exact rules."""
    return " ".join(unicodedata.normalize("NFC", value).strip().split())


def matching_custom_policy_rules(text: str, rules: list[CustomPolicyRule]) -> list[CustomPolicyRule]:
    candidate = normalise_exact_policy_text(text)
    return [rule for rule in rules if any(candidate == normalise_exact_policy_text(pattern) for pattern in rule.patterns)]


def suggest_rules(unmapped: list[object]) -> list[dict[str, object]]:
    suggestions = []
    seen = set()
    ordered = sorted(unmapped, key=lambda c: getattr(c, "operational_confidence", 0.0), reverse=True)
    for candidate in ordered:
        text = getattr(candidate, "text", "")
        words = re.findall(r"[a-zA-Z][a-zA-Z0-9]+", text.lower())
        if not words:
            continue
        key_words = [w for w in words if w not in {"the", "and", "for", "before", "rather", "than", "with", "without", "should", "must", "always"}][:5]
        rule_id = "_".join(key_words[:4]) or "custom_instruction"
        if rule_id in seen:
            continue
        seen.add(rule_id)
        category = "deny" if any(w in words for w in ["avoid", "never", "not", "do"]) else "must"
        section = getattr(candidate, "section", None)
        safety = any(w in words for w in ["secret", "secrets", "credential", "credentials", "auth", "security", "token", "production"])
        suggestions.append({
            "id": rule_id,
            "category": category,
            "patterns": [text],
            "positive_terms": key_words[:3],
            "section_hints": [section.lower()] if isinstance(section, str) and section else [],
            "modal_hints": [word for word in ["must", "should", "always", "never", "avoid", "use", "run", "keep", "update"] if word in words][:2],
            "rendered": text.rstrip(".") + ".",
            "severity": "high" if safety else "medium",
            "safety_critical": safety,
            "always_select": safety,
        })
    return suggestions
