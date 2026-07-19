from __future__ import annotations

import re
import shlex
import json

from ..core.models import AttachedExpression, GlyphManifest, PolicyAtom, PolicyExpression, PolicyLink, PreservedDirective


SECTION_MAP = {"m": "must", "d": "deny", "a": "ask", "l": "allow", "s": "stack", "f": "flow", "sc": "scope"}
ALLOWED_SECTIONS = {"agent", "goal", "stack", "scope", "flow", "must", "deny", "ask", "allow"}
ALLOWED_SECTION_KEYS = ALLOWED_SECTIONS | set(SECTION_MAP)
POLICY_NAMES = {"policy", "p"}
PRESERVE_NAMES = {"preserve", "x"}
CATEGORY_ALIASES = {"m": "must", "d": "deny", "a": "ask", "l": "allow", "u": "unknown"}
POLICY_FIELD_ALIASES = {
    "a": "action", "t": "target", "s": "scope", "c": "condition", "e": "except", "r": "risk", "g": "tag",
    "x": "expression", "w": "when_expression", "ex": "except_expression", "l": "link",
}


def _strip_comments(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not line.strip().startswith("#"))


def _parse_values(raw: str) -> list[str]:
    raw = raw.strip()
    if not raw:
        return []
    return [part.strip().strip(",") for part in re.split(r"[\n,]+", raw) if part.strip().strip(",")]


def _tokens(raw: str, line: int) -> list[str]:
    try:
        return shlex.split(raw, posix=True)
    except ValueError as exc:
        raise ValueError(f"Invalid quoted value on line {line}: {exc}") from exc


def _category(value: str, line: int, preserve: bool = False) -> str:
    category = CATEGORY_ALIASES.get(value, value)
    allowed = {"must", "deny", "ask", "allow", "unknown"} if preserve else {"must", "deny", "ask", "allow"}
    if category not in allowed:
        expected = ", ".join(sorted(allowed))
        raise ValueError(f"Invalid directive category on line {line}: {value}; expected {expected}")
    return category


def _parse_fields(parts: list[str], line: int, aliases: dict[str, str]) -> dict[str, list[str]]:
    values: dict[str, list[str]] = {}
    for part in parts:
        if "=" not in part:
            raise ValueError(f"Invalid field on line {line}: {part}; expected key=value")
        key, value = part.split("=", 1)
        key = aliases.get(key, key)
        if key not in {"action", "target", "scope", "condition", "except", "risk", "tag", "expression", "when_expression", "except_expression", "link"}:
            raise ValueError(f"Unknown policy field on line {line}: {key}")
        values.setdefault(key, []).append(value)
    return values


def _json_model(value: str, line: int, model: type[PolicyExpression] | type[AttachedExpression] | type[PolicyLink]):
    try:
        return model.model_validate(json.loads(value))
    except (json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"Invalid structured policy expression on line {line}: {exc}") from exc


def _parse_policy(raw: str, line: int, version: str) -> PolicyAtom:
    parts = _tokens(raw, line)
    if len(parts) < 3:
        raise ValueError(f"Invalid policy syntax on line {line}; expected category id and policy fields")
    category = _category(parts[0], line)
    identifier = parts[1]
    fields = _parse_fields(parts[2:], line, POLICY_FIELD_ALIASES)
    structured = fields.get("expression", [])
    if structured and version != "0.2":
        raise ValueError(f"Structured policy expressions require glyph/0.2 (line {line})")
    if structured:
        if len(structured) != 1 or fields.get("action") or fields.get("target") or fields.get("condition") or fields.get("except"):
            raise ValueError(f"Structured policy on line {line} requires one expression and cannot mix v0.1 fields")
    elif len(fields.get("action", [])) != 1 or len(fields.get("target", [])) != 1:
        raise ValueError(f"Policy on line {line} requires exactly one action and target")
    risk = fields.get("risk", ["medium"])
    if len(risk) != 1 or risk[0] not in {"low", "medium", "high"}:
        raise ValueError(f"Invalid policy risk on line {line}")
    common = {"id": identifier, "category": category, "scope": fields.get("scope", []), "risk": risk[0], "tags": fields.get("tag", [])}
    if structured:
        when = fields.get("when_expression", [])
        exceptions = fields.get("except_expression", [])
        if len(when) > 1:
            raise ValueError(f"Policy on line {line} accepts at most one attached condition")
        policy = PolicyAtom(
            **common,  # type: ignore[arg-type]
            expression=_json_model(structured[0], line, PolicyExpression),
            condition_expression=_json_model(when[0], line, AttachedExpression) if when else None,
            exception_expressions=[_json_model(value, line, AttachedExpression) for value in exceptions],
            link=_json_model(fields["link"][0], line, PolicyLink) if fields.get("link") else None,
        )
        if identifier != policy.fingerprint():
            raise ValueError(f"Structured policy id on line {line} is not its content-derived id; expected {policy.fingerprint()}")
        return policy
    return PolicyAtom(**common, action=fields["action"][0], target=fields["target"][0], conditions=fields.get("condition", []), exceptions=fields.get("except", []))  # type: ignore[arg-type]


def _parse_preserve(raw: str, line: int) -> PreservedDirective:
    parts = _tokens(raw, line)
    if "--" not in parts:
        raise ValueError(f"Invalid preserve syntax on line {line}; expected -- followed by quoted text")
    divider = parts.index("--")
    header, wording = parts[:divider], parts[divider + 1 :]
    if len(header) < 2 or not wording:
        raise ValueError(f"Invalid preserve syntax on line {line}")
    category = _category(header[0], line, preserve=True)
    identifier = header[1]
    fields = _parse_fields(header[2:], line, POLICY_FIELD_ALIASES)
    unsupported = set(fields) - {"risk", "tag"}
    if unsupported:
        raise ValueError(f"Preserve on line {line} only accepts risk and tag fields")
    risk = fields.get("risk", ["medium"])
    if len(risk) != 1 or risk[0] not in {"low", "medium", "high"}:
        raise ValueError(f"Invalid preserve risk on line {line}")
    return PreservedDirective(
        id=identifier,
        category=category,  # type: ignore[arg-type]
        text=" ".join(wording),
        risk=risk[0],  # type: ignore[arg-type]
        tags=fields.get("tag", []),
    )


def _block(lines: list[str], start: int) -> tuple[str, str, int]:
    """Return section name, content, and the closing-line index."""
    line = lines[start].strip()
    match = re.match(r"([A-Za-z]+)\[(.*)$", line)
    if not match:
        raise ValueError(f"Invalid .glp syntax on line {start + 1}: {line}")
    name, rest = match.group(1), match.group(2)
    if rest.endswith("]"):
        return name, rest[:-1], start
    content: list[str] = [rest] if rest else []
    index = start + 1
    while index < len(lines) and lines[index].strip() != "]":
        content.append(lines[index].strip())
        index += 1
    if index >= len(lines):
        raise ValueError(f"Unclosed .glp section starting on line {start + 1}: {name}[")
    return name, "\n".join(content), index


def parse_glp(text: str) -> GlyphManifest:
    lines = [line.rstrip() for line in _strip_comments(text).splitlines() if line.strip()]
    headers = {"glyph/0.1": "0.1", "g/0.1": "0.1", "glyph/0.2": "0.2", "g/0.2": "0.2"}
    if not lines or lines[0].strip() not in headers:
        raise ValueError("Invalid .glp header; expected glyph/0.1, g/0.1, glyph/0.2, or g/0.2")
    version = headers[lines[0].strip()]
    manifest = GlyphManifest(version=version)
    index = 1
    while index < len(lines):
        line = lines[index].strip()
        if line.startswith("agent "):
            manifest.agent = line.split(None, 1)[1]
        elif line.startswith("goal "):
            manifest.goal = _parse_values(line.split(None, 1)[1].replace(" ", ","))
        elif line.startswith("cmd."):
            try:
                label, raw = line[4:].split(None, 1)
            except ValueError as exc:
                raise ValueError(f"Invalid command syntax on line {index + 1}: {line}") from exc
            parsed = _tokens(raw, index + 1)
            manifest.commands[label] = " ".join(parsed) if raw[:1] in {"\"", "'"} else raw.strip("\"")
        elif re.match(r"[A-Za-z]+\[", line):
            name, raw, end = _block(lines, index)
            if name in POLICY_NAMES:
                entries = [entry.strip().rstrip(",") for entry in raw.splitlines() if entry.strip()]
                if not entries and raw.strip():
                    entries = [raw.strip()]
                if len(entries) == 1 and "\n" not in raw and entries[0]:
                    entries = [entries[0]]
                for entry in entries:
                    manifest.policies.append(_parse_policy(entry, index + 1, version))
            elif name in PRESERVE_NAMES:
                entries = [entry.strip().rstrip(",") for entry in raw.splitlines() if entry.strip()]
                if not entries and raw.strip():
                    entries = [raw.strip()]
                if len(entries) == 1 and "\n" not in raw and entries[0]:
                    entries = [entries[0]]
                for entry in entries:
                    manifest.preserved.append(_parse_preserve(entry, index + 1))
            else:
                key = SECTION_MAP.get(name, name)
                if name not in ALLOWED_SECTION_KEYS:
                    raise ValueError(f"Unknown .glp section on line {index + 1}: {name}")
                if key == "allow" and version != "0.2":
                    raise ValueError(f"Allow rules require glyph/0.2 (line {index + 1})")
                setattr(manifest, key, _parse_values(raw))
            index = end
        else:
            raise ValueError(f"Invalid .glp syntax on line {index + 1}: {line}")
        index += 1
    return manifest.sorted_copy()
