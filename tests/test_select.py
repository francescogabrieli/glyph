from glyph.core.models import GlyphManifest
from glyph.governance.select import select_manifest, select_output
from glyph.semantics.rules import RULE_BY_ID


def test_task_selection_keeps_safety_and_test_rules():
    manifest = GlyphManifest(stack=["python", "react"], commands={"test": "pytest"}, flow=["read", "test", "report"], must=["run_tests_before_done", "report_changes", "report_verification"], deny=["secrets_commit"], ask=["destructive_ops"])
    selected = select_manifest(manifest, "fix failing tests")
    assert selected.commands["test"] == "pytest"
    assert "secrets_commit" in selected.deny
    assert "must[" in select_output(manifest, "fix failing tests")


def test_task_selection_preserves_safety_critical_rules_for_unrelated_task():
    manifest = GlyphManifest(
        stack=["python", "react"],
        commands={"test": "pytest", "build": "npm run build"},
        flow=["read", "plan", "test", "build", "report"],
        must=["run_tests_before_done", "report_changes", "report_verification"],
        deny=["secrets_commit", "credentials_exposure", "api_key_exposure", "prod_config_write", "deploy_without_approval"],
        ask=["destructive_ops", "schema_changes", "security_sensitive_changes"],
    )
    selected = select_manifest(manifest, "update React component", max_tokens=300)
    assert {"secrets_commit", "credentials_exposure", "api_key_exposure", "prod_config_write", "deploy_without_approval"} <= set(selected.deny)
    assert {"destructive_ops", "schema_changes", "security_sensitive_changes"} <= set(selected.ask)

    markdown = select_output(manifest, "update React component", "markdown", 300)
    assert "Never commit secrets" in markdown
    assert "Ask for confirmation before destructive operations" in markdown


def test_cache_permission_rule_is_safety_critical_and_always_selected():
    rule = RULE_BY_ID["cache_clear_permission"]
    assert rule.safety_critical is True
    assert rule.always_select is True

    manifest = GlyphManifest(ask=["cache_clear_permission"])
    selected = select_manifest(manifest, "update a React component")
    assert selected.ask == ["cache_clear_permission"]
    assert "use `--no-cache` instead" in select_output(manifest, "update a React component", "markdown")
