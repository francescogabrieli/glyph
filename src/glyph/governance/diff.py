from __future__ import annotations

from pathlib import Path

from ..core.models import GlyphManifest
from ..formats.parser import parse_glp
from ..pipeline.compiler import compile_text


def load_any(path: Path, rules_path: Path | None = None) -> GlyphManifest:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".glp" or text.lstrip().startswith(("glyph/0.1", "g/0.1", "glyph/0.2", "g/0.2")):
        return parse_glp(text)
    return compile_text(text, str(path), rules_path=rules_path)


def semantic_diff(old: GlyphManifest, new: GlyphManifest) -> dict[str, object]:
    old_units = old.semantic_units()
    new_units = new.semantic_units()
    changed_commands = {k: (old.commands.get(k), new.commands.get(k)) for k in sorted(set(old.commands) | set(new.commands)) if old.commands.get(k) != new.commands.get(k)}
    risks: list[str] = []
    removed = old_units - new_units
    if "run_tests_before_done" in removed:
        risks.append("Removed required testing rule: run_tests_before_done")
    for rule in ["secrets_commit", "credentials_exposure", "api_key_exposure", "prod_config_write"]:
        if rule in removed:
            risks.append(f"High risk: removed safety deny rule: {rule}")
    old_policies = {policy.fingerprint(): policy for policy in old.policies}
    new_policies = {policy.fingerprint(): policy for policy in new.policies}
    old_preserved = {directive.fingerprint(): directive for directive in old.preserved}
    new_preserved = {directive.fingerprint(): directive for directive in new.preserved}
    removed_policy_fingerprints = sorted(set(old_policies) - set(new_policies))
    removed_preserve_fingerprints = sorted(set(old_preserved) - set(new_preserved))
    for fingerprint in removed_policy_fingerprints:
        policy = old_policies[fingerprint]
        if policy.risk == "high" or "security" in policy.tags:
            risks.append(f"High risk: removed safety-critical policy atom: {policy.id}")
    for fingerprint in removed_preserve_fingerprints:
        directive = old_preserved[fingerprint]
        if directive.risk == "high" or "security" in directive.tags:
            risks.append(f"High risk: removed safety-critical preserved directive: {directive.id}")
    # The IDs are content fingerprints.  Pair different fingerprints with the
    # same operation to make a field-level policy change explicit in reviews.
    changed_policies = []
    old_by_operation = {(policy.category, *policy.operation_key()): policy for policy in old.policies}
    new_by_operation = {(policy.category, *policy.operation_key()): policy for policy in new.policies}
    for operation in sorted(set(old_by_operation) & set(new_by_operation)):
        before, after = old_by_operation[operation], new_by_operation[operation]
        if before.fingerprint() != after.fingerprint():
            changed_policies.append({"before": before.fingerprint(), "after": after.fingerprint(), "operation": operation})
    return {
        "added": sorted(new_units - old_units),
        "removed": sorted(removed),
        "changed_commands": changed_commands,
        "changed_stack": (old.stack, new.stack) if old.stack != new.stack else None,
        "changed_flow": (old.flow, new.flow) if old.flow != new.flow else None,
        "changed_must": (old.must, new.must) if old.must != new.must else None,
        "changed_deny": (old.deny, new.deny) if old.deny != new.deny else None,
        "changed_ask": (old.ask, new.ask) if old.ask != new.ask else None,
        "changed_allow": (old.allow, new.allow) if old.allow != new.allow else None,
        "added_policies": sorted(set(new_policies) - set(old_policies)),
        "removed_policies": removed_policy_fingerprints,
        "changed_policies": changed_policies,
        "added_preserved": sorted(set(new_preserved) - set(old_preserved)),
        "removed_preserved": removed_preserve_fingerprints,
        "policy_fingerprints": {policy.id: policy.fingerprint() for policy in new.policies},
        "preserved_fingerprints": {directive.id: directive.fingerprint() for directive in new.preserved},
        "risks": risks,
    }
