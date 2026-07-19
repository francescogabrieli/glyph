from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from glyph.core.models import CompressionProfile, GlyphManifest, PolicyAtom, PreservedDirective
from glyph.formats.parser import parse_glp
from glyph.formats.renderer import render_glp, render_markdown
from glyph.governance.diff import semantic_diff
from glyph.governance.lock import create_lock
from glyph.governance.select import select_manifest
from glyph.interfaces.cli import app
from glyph.pipeline.compiler import analyze_files, analyze_text, compile_text
from glyph.pipeline.verifier import verify
from glyph.semantics.policies import classify_risk


runner = CliRunner()


@pytest.mark.parametrize(
    "text",
    [
        "Run the token-gate check before committing interface changes.",
        "Document required inputs, outputs, permissions, constraints, and artifacts.",
        "Use the appropriate schema file for the selected database engine.",
        "For production, use a hosted database provider.",
        "Run the tutorial against a development instance with a test token.",
        "Run integration checks when credentials are available.",
        "Use an explicit environment file only when credentials are needed.",
    ],
)
def test_incidental_safety_lexemes_do_not_raise_high_risk(text: str):
    assert classify_risk(text) != "high"


@pytest.mark.parametrize(
    "text",
    [
        "Never expose an access token.",
        "Ask permission before changing production configuration.",
        "Do not broaden managed permissions.",
        "Review schema changes before applying a migration.",
        "Never delete protected records.",
    ],
)
def test_contextual_safety_relations_remain_high_risk(text: str):
    assert classify_risk(text) == "high"


def test_policy_and_preserve_round_trip_in_every_profile():
    manifest = GlyphManifest(
        policies=[
            PolicyAtom(
                category="must",
                action="require",
                target="permission_check",
                scope=["page.tsx"],
                exceptions=["layout.tsx"],
                risk="high",
                tags=["security"],
            )
        ],
        preserved=[
            PreservedDirective(
                category="unknown",
                text="Keep the exact source-faithful operational clause.",
                risk="medium",
                tags=["repository"],
            )
        ],
    )
    for profile in CompressionProfile:
        parsed = parse_glp(render_glp(manifest, profile))
        assert parsed.policies == manifest.sorted_copy().policies
        assert parsed.preserved == manifest.sorted_copy().preserved


def test_content_identifiers_do_not_depend_on_source_paths_or_lines():
    text = "## Rules\nAlways route tenant reads through TenantResolver."
    one, _ = analyze_text(text, "/tmp/one/AGENTS.md")
    two, _ = analyze_text("\n\n" + text, "/another/path/README.md")
    assert one.policies[0].id == two.policies[0].id
    assert one.policies[0].id.startswith("p_")


def test_atomicization_inherited_mode_and_exceptions_are_preserved_together():
    manifest, report = analyze_text(
        "## Ask first\n"
        "- Delete stale artifacts unless the task only changes documentation.\n"
        "\n## Completion\n"
        "Always run tests and report what changed.",
        "AGENTS.md",
    )
    policy = next(policy for policy in manifest.policies if policy.expression and policy.expression.predicate == "delete")
    assert policy.category == "ask"
    assert policy.exception_expressions
    assert {"run_tests_before_done", "report_changes"} <= manifest.semantic_units()
    assert all(resolution.destination != "dropped" for resolution in report.ledger.resolutions)


def test_general_policy_shapes_are_structured_without_high_risk_preservation():
    text = Path("spec/fixtures/retention-policies.md").read_text(encoding="utf-8")
    manifest, report = analyze_text(text, "AGENTS.md")

    migration = next(policy for policy in manifest.policies if policy.expression and "apply" in policy.expression.terms())
    firewall = next(policy for policy in manifest.policies if policy.expression is not None)
    assert migration.category == "must"
    assert migration.expression.op == "not"
    assert "production_overrides" in migration.expression.terms()
    assert migration.exception_expressions[0].expression.predicate == "explicitly_approves"
    assert firewall.expression.subject == ["production_firewall_bypasses"]
    assert firewall.expression.predicate == "pass"
    assert firewall.expression.objects == ["reviewgate"]
    assert firewall.scope == []
    assert report.high_risk_preserved_count == 0
    assert report.structured_coverage == 100.0
    assert report.retained_coverage == 100.0


def test_common_markdown_directive_wrappers_are_structured_safely():
    text = (
        "## Rules\n"
        "- Authentication**: Validate instance ownership before operations\n"
        "- If backend work is needed, ask permission first.\n"
        "- You may read the artifact but NEVER delete it.\n"
    )
    manifest, report = analyze_text(text, "AGENTS.md")

    assert report.high_risk_preserved_count == 1
    assert report.retained_coverage == 100.0
    assert any(policy.action == "validate" for policy in manifest.policies)
    assert any(policy.category == "ask" and policy.condition_expression is not None for policy in manifest.policies)
    assert any(directive.category == "deny" and "delete it" in directive.text for directive in manifest.preserved)
    assert any(resolution.reason_code == "pronoun_reference" for resolution in report.ledger.resolutions)


def test_local_antecedent_is_used_end_to_end_for_mixed_allow_deny_policy():
    manifest, report = analyze_text(
        "Database: Located at `var/state.db` (SQLite). You may read from it but NEVER delete it.",
        "AGENTS.md",
    )
    assert report.high_risk_preserved_count == 0
    assert {policy.category for policy in manifest.policies} == {"allow", "deny"}
    assert len({policy.link.group for policy in manifest.policies if policy.link}) == 1


def test_conservative_fallback_is_retained_and_strict_require_structured_rejects_it(tmp_path: Path):
    source = tmp_path / "AGENTS.md"
    output = tmp_path / "AGENTS.glp"
    source.write_text("## Rules\nAlways carefully respect the relevant architectural intent.", encoding="utf-8")
    manifest, report = analyze_files([source])
    assert len(manifest.preserved) == 1
    assert report.retained_coverage == 100.0
    assert report.structured_coverage == 0.0
    result = runner.invoke(app, ["compile", str(source), "-o", str(output), "--strict", "--require-structured"])
    assert result.exit_code == 1
    assert not output.exists()


def test_high_risk_preserved_directive_fails_default_strict_gate(tmp_path: Path):
    source = tmp_path / "AGENTS.md"
    output = tmp_path / "AGENTS.glp"
    source.write_text("Never under any circumstances use a workflow with production impact.", encoding="utf-8")
    manifest, report = analyze_files([source])
    assert manifest.preserved and manifest.preserved[0].risk == "high"
    assert report.safety_retention == 100.0
    result = runner.invoke(app, ["compile", str(source), "-o", str(output), "--strict"])
    assert result.exit_code == 1
    assert "high-risk preserved" in result.output
    assert not output.exists()


def test_verify_uses_candidate_to_atom_ledger_for_policy_and_preserve():
    source = "## Rules\nAlways route tenant reads through TenantResolver.\nAlways carefully respect the relevant architectural intent."
    manifest = compile_text(source, "AGENTS.md")
    report = verify(source, manifest)
    assert report.retained_coverage == 100.0
    assert report.structured_coverage == 50.0
    assert not report.missing_policy_ids
    assert not report.missing_preserve_ids


def test_verify_preserves_adapter_identity_for_end_to_end_ledger():
    source = "Use repository helpers for tenant-aware queries."
    manifest = compile_text(source, "AGENTS.md")
    report = verify(source, manifest, source="AGENTS.md")
    assert report.retained_coverage == 100.0


def test_generic_document_blockquote_is_excluded_from_operational_denominators():
    text = (
        "> Never expose production credentials.\n\n"
        "Never commit secrets.\n"
    )
    manifest, report = analyze_text(text, "README.md")

    quoted = next(candidate for candidate in report.candidates if candidate.block_type == "blockquote")
    assert quoted not in report.ledger.operational_candidates
    assert any(
        resolution.candidate_id == quoted.id and resolution.destination == "non_operational"
        for resolution in report.ledger.resolutions
    )
    assert report.retained_coverage == 100.0
    assert report.safety_retention == 100.0
    assert "secrets_commit" in manifest.deny


def test_instruction_blockquote_remains_operational_and_safety_retained():
    manifest, report = analyze_text("> Never commit secrets.\n", "AGENTS.md")

    quoted = next(candidate for candidate in report.candidates if candidate.block_type == "blockquote")
    assert quoted in report.ledger.operational_candidates
    assert report.retained_coverage == 100.0
    assert report.safety_retention == 100.0
    assert "secrets_commit" in manifest.deny


def test_source_code_fence_statements_do_not_inherit_policy_modality():
    text = """## Required Pattern

```typescript
import { widget } from 'library';
```

## Forbidden Pattern

```typescript
import { widget } from 'library';
```
"""

    manifest, report = analyze_text(text, "docs/synthetic-policy.md")

    assert not manifest.policies
    assert not report.conflicts
    assert not report.ledger.operational_candidates


def test_source_code_fence_keeps_explicit_comment_directive():
    text = """## Rules

```python
# Never commit secrets.
value = build_fixture()
```
"""

    manifest, report = analyze_text(text, "AGENTS.md")

    assert "secrets_commit" in manifest.deny
    assert report.safety_retention == 100.0


def test_generic_product_and_api_narrative_is_not_operational_but_instruction_adapter_remains_active():
    narrative = "It should be possible to run the service with in-memory adapters."
    generic_manifest, generic_report = analyze_text(narrative, "docs/design.md")
    assert not generic_report.ledger.operational_candidates
    assert not generic_manifest.policies

    instruction_manifest, instruction_report = analyze_text(narrative, "AGENTS.md")
    assert instruction_report.ledger.operational_candidates
    assert instruction_manifest.preserved or instruction_manifest.policies


def test_generic_api_return_description_is_excluded_without_hiding_direct_safety_rule():
    text = "Returns a key that should be stored securely.\n\nNever expose production credentials."
    manifest, report = analyze_text(text, "docs/api.md")
    assert len(report.ledger.operational_candidates) == 1
    assert report.safety_retention == 100.0
    assert manifest.policies or manifest.semantic_units()


@pytest.mark.parametrize(
    "text",
    [
        "Selecting a recurring task should make it clear that the target is reusable.",
        "For this product, this should be treated as a hard cutover in direction.",
        "When the workforce is automated, you need more than a task list — you need a control plane.",
        "Each workspace has agents, goals, and budgets — everything a team needs, except the operating system is software.",
    ],
)
def test_generic_product_direction_prose_is_not_an_operational_candidate(text: str):
    _, report = analyze_text(text, "docs/design.md")
    assert not report.ledger.operational_candidates


def test_generic_conditional_config_fragment_is_not_promoted_by_read_only_or_before():
    text = "Local validation config using sandbox mode: read-only if login credentials are available."
    _, report = analyze_text(text, "docs/runtime.md")
    assert not report.ledger.operational_candidates


def test_implementation_plan_checklist_is_not_an_active_agent_policy():
    text = "## Draft messages\n- Check authentication and verify that the identifier exists."
    _, report = analyze_text(text, "docs/plans/change.md")
    assert not report.ledger.operational_candidates


@pytest.mark.parametrize(
    "text",
    [
        "Before opening a change request, run the verification suite.",
        "On a dependency upgrade, read the release notes and run integration tests.",
        "If protected configuration changes, ask for approval first.",
    ],
)
def test_prefixed_imperatives_remain_operational(text: str):
    _, report = analyze_text(text, "CONTRIBUTING.md")
    assert report.ledger.operational_candidates


def test_generic_command_example_label_and_passive_product_contract_are_not_policies():
    text = (
        "For a production build, run for example:\n\n"
        "Managed runtime homes are always seeded from the configured host home."
    )
    _, report = analyze_text(text, "docs/deployment.md")
    assert not report.ledger.operational_candidates


def test_collection_title_containing_rules_does_not_make_catalog_entries_normative():
    text = (
        "# Curated Build Rules\n\n"
        "## Rules\n\n"
        "### Deployment catalog\n\n"
        "- [Hosted Runtime](https://example.invalid/runtime) - Production deployment reference.\n"
    )
    manifest, report = analyze_text(text, "README.md")

    assert not report.ledger.operational_candidates
    assert not manifest.policies
    assert not manifest.preserved


def test_linked_entry_with_explicit_modal_remains_operational():
    text = (
        "# Curated Build Rules\n\n"
        "## Rules\n\n"
        "- [Release checklist](https://example.invalid/release) must be reviewed before deployment.\n"
    )
    manifest, report = analyze_text(text, "README.md")

    assert report.ledger.operational_candidates
    assert manifest.policies or manifest.preserved


def test_generic_component_contract_is_not_an_agent_instruction():
    text = "The response must not include authentication credentials."
    manifest, report = analyze_text(text, "docs/api-reference.md")

    assert not report.ledger.operational_candidates
    assert not manifest.policies
    assert report.ledger.api_contracts


def test_component_contract_remains_operational_in_instruction_adapter():
    text = "The response must not include authentication credentials."
    manifest, report = analyze_text(text, "AGENTS.md")

    assert report.ledger.operational_candidates
    assert manifest.policies or manifest.preserved


def test_generic_contributor_subject_remains_operational():
    text = "Contributors must not include authentication credentials in fixtures."
    manifest, report = analyze_text(text, "CONTRIBUTING.md")

    assert report.ledger.operational_candidates
    assert manifest.policies


def test_configuration_table_row_is_reference_not_policy():
    text = (
        "## Environment variables\n\n"
        "| Variable | Description | Required |\n"
        "| --- | --- | --- |\n"
        "| SERVICE_TOKEN | Authentication token | required |\n"
    )
    manifest, report = analyze_text(text, "README.md")

    assert not report.ledger.operational_candidates
    assert not manifest.policies
    assert report.ledger.api_contracts


def test_path_catalog_entry_is_reference_but_parenthetical_prohibition_is_not_hidden():
    reference = "## Layout\n- `plugins/` – Extension implementations\n"
    manifest, report = analyze_text(reference, "AGENTS.md")
    assert not report.ledger.operational_candidates
    assert not manifest.policies

    directive = "## Layout\n- `build/` – Generated output (do not edit directly)\n"
    _, directive_report = analyze_text(directive, "AGENTS.md")
    assert directive_report.ledger.operational_candidates


def test_frontmatter_and_generic_reference_labels_are_not_operational():
    text = (
        "---\n"
        "title: Hosted deployment\n"
        "summary: Deploy the service to production\n"
        "---\n\n"
        "## Authentication\n"
        "- `auth_mode`: login required\n"
    )
    manifest, report = analyze_text(text, "docs/deployment.md")
    assert not report.ledger.operational_candidates
    assert not manifest.policies


def test_generic_product_pronoun_contract_is_contextual_but_contributor_rule_remains_active():
    product = "## Secret import behavior\nThey must not store plaintext credential values.\n"
    product_manifest, product_report = analyze_text(product, "docs/api.md")
    assert not product_report.ledger.operational_candidates
    assert not product_manifest.policies

    contributor = "## Rules\nThey must not store plaintext credential values.\n"
    _, contributor_report = analyze_text(contributor, "CONTRIBUTING.md")
    assert contributor_report.ledger.operational_candidates


def test_generic_conditional_component_contract_and_option_description_are_reference_context():
    text = (
        "## Runtime behavior\n"
        "If the connection drops, the UI reconnects automatically.\n\n"
        "## Configuration\n"
        "`--section credentials` updates the deployment-level provider.\n"
    )
    manifest, report = analyze_text(text, "docs/runtime.md")
    assert not report.ledger.operational_candidates
    assert not manifest.policies


def test_conditional_instruction_addressed_to_contributor_is_not_hidden():
    text = "If you change the schema, update all affected layers."
    _, report = analyze_text(text, "CONTRIBUTING.md")
    assert report.ledger.operational_candidates


def test_explicit_rules_heading_still_provides_normative_inheritance():
    text = "# Project Guide\n\n## Rules\n\n- Keep generated files synchronized.\n"
    manifest, report = analyze_text(text, "README.md")

    assert report.ledger.operational_candidates
    assert manifest.policies or manifest.preserved


def test_selection_keeps_preserved_and_safety_policy_and_reports_minimum_budget():
    manifest = GlyphManifest(
        stack=["python", "react"],
        policies=[PolicyAtom(category="deny", action="write", target="production_config", risk="high", tags=["security"])],
        preserved=[PreservedDirective(category="unknown", text="Keep the legacy coordination clause exactly.")],
    )
    selected = select_manifest(manifest, "update React component")
    assert selected.policies == manifest.policies
    assert selected.preserved == manifest.preserved
    try:
        select_manifest(manifest, "update React component", max_tokens=1)
    except ValueError as exc:
        assert "mandatory instruction budget" in str(exc)
    else:
        raise AssertionError("expected an impossible budget to fail")


def test_multi_input_deduplicates_policy_and_merges_provenance(tmp_path: Path):
    one = tmp_path / "AGENTS.md"
    two = tmp_path / "CONTRIBUTING.md"
    text = "Always route tenant reads through TenantResolver."
    one.write_text(text, encoding="utf-8")
    two.write_text(text, encoding="utf-8")
    manifest, _ = analyze_files([one, two])
    assert len(manifest.policies) == 1
    assert len(manifest.provenance[manifest.policies[0].id]) == 2


def test_diff_and_lock_include_structured_and_preserved_fingerprints(tmp_path: Path):
    old = compile_text("Always route tenant reads through TenantResolver.", "AGENTS.md")
    new = compile_text("Always route tenant reads through AlternateResolver.", "AGENTS.md")
    result = semantic_diff(old, new)
    assert result["removed_policies"]
    source = tmp_path / "AGENTS.md"
    source.write_text("Always route tenant reads through TenantResolver.", encoding="utf-8")
    lock = create_lock([source])
    assert lock["schema"] == "glyph-lock/v3"
    assert lock["policy_fingerprints"]


def test_markdown_renderer_labels_preserved_wording_without_claiming_interpretation():
    rendered = render_markdown(GlyphManifest(preserved=[PreservedDirective(category="unknown", text="Keep this exact operational clause.")]))
    assert "did not structurally interpret" in rendered
    assert "Keep this exact operational clause." in rendered
