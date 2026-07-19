from __future__ import annotations

import json

from ..core.models import CompressionProfile, GlyphManifest, PolicyAtom, PolicyExpression, PreservedDirective, SemanticRule


def quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _block(name: str, values: list[str], profile: CompressionProfile) -> list[str]:
    if not values:
        return []
    if profile == CompressionProfile.readable:
        return [f"{name}["] + [f"  {value}" for value in values] + ["]", ""]
    return [f"{name}[{','.join(values)}]"]


def _policy_line(policy: PolicyAtom, ultra: bool = False) -> str:
    category = {"must": "m", "deny": "d", "ask": "a", "allow": "l"}[policy.category] if ultra else policy.category
    if policy.expression is not None:
        expression = json.dumps(policy.expression.sorted_copy().payload(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        fields: list[tuple[str, str]] = [("x" if ultra else "expression", expression)]
        if policy.condition_expression:
            condition = json.dumps(policy.condition_expression.sorted_copy().payload(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            fields.append(("w" if ultra else "when_expression", condition))
        for exception in policy.exception_expressions:
            value = json.dumps(exception.sorted_copy().payload(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            fields.append(("ex" if ultra else "except_expression", value))
        if policy.link:
            link = json.dumps(policy.link.payload(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            fields.append(("l" if ultra else "link", link))
    else:
        fields = [("a" if ultra else "action", policy.action), ("t" if ultra else "target", policy.target)]
    fields.extend(("s" if ultra else "scope", value) for value in policy.scope)
    if policy.expression is None:
        fields.extend(("c" if ultra else "condition", value) for value in policy.conditions)
        fields.extend(("e" if ultra else "except", value) for value in policy.exceptions)
    fields.append(("r" if ultra else "risk", policy.risk))
    fields.extend(("g" if ultra else "tag", value) for value in policy.tags)
    structured_keys = {"expression", "when_expression", "except_expression", "link", "x", "w", "ex", "l"}
    rendered_fields = [
        f"{key}={quote(value)}" if key in structured_keys or any(char.isspace() for char in value) else f"{key}={value}"
        for key, value in fields
    ]
    return " ".join([category, policy.id, *rendered_fields])


def _preserve_line(directive: PreservedDirective, ultra: bool = False) -> str:
    category = {"must": "m", "deny": "d", "ask": "a", "allow": "l", "unknown": "u"}[directive.category] if ultra else directive.category
    fields = [("r" if ultra else "risk", directive.risk), *[("g" if ultra else "tag", value) for value in directive.tags]]
    rendered_fields = [f"{key}={quote(value)}" if any(char.isspace() for char in value) else f"{key}={value}" for key, value in fields]
    return " ".join([category, directive.id, *rendered_fields, "--", quote(directive.text)])


def _structured_blocks(manifest: GlyphManifest, profile: CompressionProfile) -> list[str]:
    lines: list[str] = []
    if manifest.policies:
        name = "p" if profile == CompressionProfile.ultra else "policy"
        if profile == CompressionProfile.readable:
            lines += [f"{name}["] + [f"  {_policy_line(policy)}" for policy in manifest.policies] + ["]", ""]
        elif profile == CompressionProfile.ultra:
            lines += [f"{name}[{_policy_line(policy, ultra=True)}]" for policy in manifest.policies]
        else:
            lines += [f"{name}[{_policy_line(policy)}]" for policy in manifest.policies]
    if manifest.preserved:
        name = "x" if profile == CompressionProfile.ultra else "preserve"
        if profile == CompressionProfile.readable:
            lines += [f"{name}["] + [f"  {_preserve_line(directive)}" for directive in manifest.preserved] + ["]", ""]
        elif profile == CompressionProfile.ultra:
            lines += [f"{name}[{_preserve_line(directive, ultra=True)}]" for directive in manifest.preserved]
        else:
            lines += [f"{name}[{_preserve_line(directive)}]" for directive in manifest.preserved]
    return lines


def render_glp(manifest: GlyphManifest, profile: CompressionProfile = CompressionProfile.compact, version: str | None = None) -> str:
    m = manifest.sorted_copy()
    output_version = version or m.version
    if output_version not in {"0.1", "0.2"}:
        raise ValueError(".glp version must be 0.1 or 0.2")
    if output_version == "0.1" and any(policy.is_v2 for policy in m.policies):
        raise ValueError("Cannot render a structured glyph/0.2 policy as glyph/0.1 without semantic loss")
    if output_version == "0.1" and (m.allow or any(policy.category == "allow" for policy in m.policies) or any(item.category == "allow" for item in m.preserved)):
        raise ValueError("Cannot render glyph/0.2 allow semantics as glyph/0.1 without semantic loss")
    if profile == CompressionProfile.ultra:
        lines = [f"g/{output_version}"]
        aliases = [("s", m.stack), ("sc", m.scope), ("f", m.flow), ("m", m.must), ("d", m.deny), ("a", m.ask), ("l", m.allow)]
        for name, values in aliases:
            if values:
                lines.append(f"{name}[{','.join(values)}]")
        for label, command in m.commands.items():
            lines.append(f"cmd.{label} {quote(command)}")
        lines.extend(_structured_blocks(m, profile))
        return "\n".join(lines) + "\n"

    lines = [f"glyph/{output_version}"]
    if profile == CompressionProfile.readable:
        lines.append("")
    if m.agent:
        lines.append(f"agent {m.agent}")
    if m.goal:
        lines.append("goal " + " ".join(m.goal))
    for name, values in [("stack", m.stack), ("scope", m.scope), ("flow", m.flow)]:
        lines.extend(_block(name, values, profile))
    for label, command in m.commands.items():
        lines.append(f"cmd.{label} {quote(command)}")
    if profile == CompressionProfile.readable and m.commands:
        lines.append("")
    for name, values in [("must", m.must), ("deny", m.deny), ("ask", m.ask), ("allow", m.allow)]:
        lines.extend(_block(name, values, profile))
    lines.extend(_structured_blocks(m, profile))
    rendered = "\n".join(lines).rstrip() + "\n"
    return rendered


def render_markdown(manifest: GlyphManifest, title: str = "Agent Instructions", extra_rules: list[SemanticRule] | None = None) -> str:
    m = manifest.sorted_copy()
    lines = [f"# {title}", "", "Generated from a Glyph `.glp` manifest. This preserves encoded operational semantics, not original prose.", ""]
    if m.agent:
        lines += ["## Agent", "", f"- {m.agent}", ""]
    if m.stack:
        lines += ["## Stack", "", *[f"- `{item}`" for item in m.stack], ""]
    if m.flow:
        lines += ["## Workflow", "", *[f"{idx}. {item.replace('_', ' ')}" for idx, item in enumerate(m.flow, 1)], ""]
    if m.commands:
        lines += ["## Commands", ""]
        lines += [f"- `{label}`: `{command}`" for label, command in m.commands.items()]
        lines.append("")
    from ..semantics.rules import RULE_BY_ID
    registry = dict(RULE_BY_ID)
    for rule in extra_rules or []:
        registry[rule.id] = rule

    for heading, attr in [("Required", "must"), ("Forbidden", "deny"), ("Ask First", "ask"), ("Allowed", "allow")]:
        values = getattr(m, attr)
        if values:
            lines += [f"## {heading}", ""]
            lines += [f"- {registry[value].rendered if value in registry else value}" for value in values]
            lines.append("")
    if m.policies:
        lines += ["## Structured Policies", ""]
        def policy_wording(policy: PolicyAtom) -> str:
            mode = {"must": "Require", "deny": "Do not", "ask": "Ask for approval before", "allow": "Allow"}[policy.category]
            if policy.expression is not None:
                wording = f"{mode} {_expression_markdown(policy.expression)}"
            else:
                subject = policy.target.replace("_", " ")
                action = policy.action.replace("_", " ")
                wording = f"{mode} {action} {subject}" if policy.category != "ask" else f"{mode} {subject}"
            if policy.scope:
                wording += " in " + ", ".join(policy.scope)
            if policy.expression is not None and policy.condition_expression:
                wording += " when " + _expression_markdown(policy.condition_expression.expression)
            elif policy.conditions:
                wording += " when " + ", ".join(policy.conditions)
            if policy.expression is not None and policy.exception_expressions:
                wording += " except " + "; ".join(_expression_markdown(item.expression) for item in policy.exception_expressions)
            elif policy.exceptions:
                wording += " except " + ", ".join(policy.exceptions)
            return wording.rstrip(".") + "."

        linked_groups: dict[str, list[PolicyAtom]] = {}
        for policy in m.policies:
            if policy.link:
                linked_groups.setdefault(policy.link.group, []).append(policy)
            else:
                lines.append(f"- {policy_wording(policy)}")
        for group in sorted(linked_groups):
            lines.append("- Apply these policies together as one inseparable directive:")
            for policy in sorted(linked_groups[group], key=lambda item: item.link.order if item.link else 0):
                lines.append(f"  - {policy_wording(policy)}")
        lines.append("")
    if m.preserved:
        lines += ["## Preserved Operational Directives", "", "The following directives are retained verbatim because Glyph did not structurally interpret them.", ""]
        for directive in m.preserved:
            lines.append(f"- [{directive.category}] {directive.text}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _expression_markdown(expression: PolicyExpression) -> str:
    if expression.op == "atomic":
        subject = " and ".join(value.replace("_", " ") for value in expression.subject)
        predicate = (expression.predicate or "").replace("_", " ")
        objects = " ".join(value.replace("_", " ") for value in expression.objects)
        return " ".join(value for value in (subject, predicate, objects) if value)
    children = [_expression_markdown(child) for child in expression.operands]
    if expression.op == "not":
        return f"not ({children[0]})"
    joiner = " and " if expression.op == "all" else " or "
    return "(" + joiner.join(children) + ")"
