from __future__ import annotations

import re

from ..core.models import GlyphManifest, PolicyAtom
from ..formats.renderer import render_glp, render_markdown
from ..semantics.rules import RULE_BY_ID
from ..source.tokenizer import count_tokens


def _task_tokens(task: str) -> set[str]:
    return set(re.findall(r"[a-z0-9_/-]+", task.lower()))


def _policy_relevant(policy: PolicyAtom, tokens: set[str]) -> bool:
    text = " ".join(policy.terms()).replace("_", " ").lower()
    return any(token in text for token in tokens)


def _is_mandatory_policy(policy: PolicyAtom) -> bool:
    return policy.link is not None or policy.risk == "high" or "security" in policy.tags


def _trim_to_budget(selected: GlyphManifest, max_tokens: int | None) -> GlyphManifest:
    if max_tokens is None:
        return selected.sorted_copy()
    selected = selected.sorted_copy()
    optional_policy_ids = {policy.id for policy in selected.policies if not _is_mandatory_policy(policy)}
    optional_must = {
        rule_id
        for rule_id in selected.must
        if not (RULE_BY_ID.get(rule_id) and RULE_BY_ID[rule_id].always_select)
    }
    while count_tokens(render_glp(selected))[0] > max_tokens and selected.stack:
        selected.stack.pop()
    while count_tokens(render_glp(selected))[0] > max_tokens and selected.flow:
        selected.flow.pop()
    while count_tokens(render_glp(selected))[0] > max_tokens and selected.commands:
        selected.commands.pop(sorted(selected.commands)[-1])
    while count_tokens(render_glp(selected))[0] > max_tokens and optional_policy_ids:
        policy_id = sorted(optional_policy_ids)[-1]
        selected.policies = [policy for policy in selected.policies if policy.id != policy_id]
        optional_policy_ids.remove(policy_id)
    while count_tokens(render_glp(selected))[0] > max_tokens and optional_must:
        rule_id = sorted(optional_must)[-1]
        selected.must.remove(rule_id)
        optional_must.remove(rule_id)
    rendered_tokens = count_tokens(render_glp(selected))[0]
    if rendered_tokens > max_tokens:
        raise ValueError(f"--max-tokens {max_tokens} is below the mandatory instruction budget of {rendered_tokens} tokens")
    return selected.sorted_copy()


def select_manifest(manifest: GlyphManifest, task: str, max_tokens: int | None = None) -> GlyphManifest:
    tokens = _task_tokens(task)
    selected = GlyphManifest(version=manifest.version, agent=manifest.agent)
    selected.stack = [item for item in manifest.stack if item.lower() in tokens]
    if not selected.stack:
        selected.stack = manifest.stack[:3]
    command_keys: set[str] = set()
    if {"test", "tests", "failing", "bug"} & tokens:
        command_keys.add("test")
    if {"lint", "style"} & tokens:
        command_keys.add("lint")
    if {"type", "typescript", "mypy", "typecheck"} & tokens:
        command_keys.add("typecheck")
    if {"build", "release"} & tokens:
        command_keys.add("build")
    if {"migration", "database", "schema"} & tokens:
        command_keys.update({"migrate", "test"})
    selected.commands = {key: manifest.commands[key] for key in sorted(command_keys) if key in manifest.commands}
    selected.flow = [item for item in manifest.flow if item in {"read", "plan", "minimal_change", "test", "lint", "typecheck", "report"}]

    # All explicit denials and approval requirements are mandatory for every
    # selected manifest, independent of textual task relevance.
    selected.deny = list(manifest.deny)
    selected.ask = list(manifest.ask)
    selected.allow = list(manifest.allow)
    for rule_id in manifest.must:
        rule = RULE_BY_ID.get(rule_id)
        relevant = bool(rule and rule.always_select)
        relevant = relevant or rule_id in {"run_tests_before_done", "report_changes", "report_verification", "read_before_edit", "plan_before_edit", "minimal_change"}
        relevant = relevant or any(part in tokens for part in rule_id.split("_"))
        if relevant:
            selected.must.append(rule_id)
    selected.policies = [policy for policy in manifest.policies if _is_mandatory_policy(policy) or _policy_relevant(policy, tokens)]
    selected_groups = {policy.link.group for policy in selected.policies if policy.link}
    if selected_groups:
        selected_ids = {policy.id for policy in selected.policies}
        selected.policies.extend(
            policy
            for policy in manifest.policies
            if policy.link and policy.link.group in selected_groups and policy.id not in selected_ids
        )
    # Preserved directives are deliberately never hidden: a shortened task
    # context must not imply that Glyph understood or discarded their wording.
    selected.preserved = list(manifest.preserved)
    return _trim_to_budget(selected, max_tokens)


def select_output(manifest: GlyphManifest, task: str, fmt: str = "glp", max_tokens: int | None = None) -> str:
    selected = select_manifest(manifest, task, max_tokens)
    if fmt == "markdown":
        return render_markdown(selected, "Selected Instructions")
    if fmt != "glp":
        raise ValueError("--format must be glp or markdown")
    return render_glp(selected)
