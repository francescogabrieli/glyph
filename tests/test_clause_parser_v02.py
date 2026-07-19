from __future__ import annotations

import pytest

from glyph.pipeline.compiler import analyze_text
from glyph.semantics.clause_parser import ClauseContext, parse_policy_clause


CASES = [
    ("HRX-02", "Never include access tokens in sample output.", "include", "action"),
    ("HRX-12", "Never delete protected audit records.", "delete", "action"),
    ("HRX-15", "Credentials must not be returned to external callers.", "returned", "passive"),
    ("HRX-16", "Do not include private keys in fixtures.", "include", "action"),
    ("HRX-18", "Never include session tokens in diagnostic output.", "include", "action"),
    ("HRX-20", "Never accept unsigned deployment requests.", "accept", "action"),
    ("HRX-21", "Service credentials must belong to the workload identity.", "belong_to", "state"),
    ("HRX-23", "Operators must route privileged requests through the approval service.", "route", "action"),
    ("HRX-34", "Export jobs must not include access tokens.", "include", "action"),
    ("HRX-40", "Automation must not request production credentials.", "request", "action"),
]


@pytest.mark.parametrize(("shape", "text", "predicate", "kind"), CASES)
def test_unambiguous_hrx_shapes_have_one_structured_parse(shape: str, text: str, predicate: str, kind: str):
    parsed = parse_policy_clause(text, "must")
    assert parsed.status == "structured", (shape, parsed)
    assert parsed.predicate == predicate
    assert parsed.predicate_kind == kind
    assert "unique_parse" in parsed.evidence
    assert parsed.expression is not None
    policy = parsed.to_policy("must", "high", ["security"])
    assert policy and policy.id == policy.fingerprint()


@pytest.mark.parametrize(("shape", "text", "predicate", "kind"), CASES)
def test_hrx_shapes_integrate_without_safety_or_retention_loss(shape: str, text: str, predicate: str, kind: str):
    manifest, report = analyze_text(text, "AGENTS.md")
    assert report.retained_coverage == 100.0, shape
    assert report.safety_retention == 100.0, shape
    assert report.dropped_count == 0, shape
    assert report.structured_coverage == 100.0, shape
    if manifest.policies:
        policy = next(policy for policy in manifest.policies if policy.expression is not None)
        assert policy.expression and predicate in policy.expression.terms()


@pytest.mark.parametrize(("shape", "text", "predicate", "kind"), CASES)
def test_nearby_narrative_never_becomes_policy(shape: str, text: str, predicate: str, kind: str):
    parsed = parse_policy_clause(f"The guide says {text[0].lower()}{text[1:]}", "must")
    assert parsed.status == "unsupported", shape
    assert parsed.reason_code == "narrative_attribution"


@pytest.mark.parametrize(("shape", "text", "predicate", "kind"), CASES)
def test_ambiguous_attachment_remains_unstructured(shape: str, text: str, predicate: str, kind: str):
    parsed = parse_policy_clause(f"If relevant context applies, {text}", "must")
    assert parsed.status == "ambiguous", shape
    assert parsed.reason_code == "ambiguous_condition_attachment"


@pytest.mark.parametrize(
    "text",
    [
        "It must not include production credentials.",
        "Automation must not request relevant credentials.",
        "Never delete audit records and deployment logs.",
        "Credentials must be returned to callers or operators.",
        "Production identities must carefully correspond across protected boundaries.",
    ],
)
def test_pronouns_vague_objects_coordination_and_unknown_predicates_are_preserved(text: str):
    parsed = parse_policy_clause(text, "must")
    assert parsed.status in {"ambiguous", "unsupported"}
    manifest, report = analyze_text(text, "AGENTS.md")
    assert not any(policy.is_v2 for policy in manifest.policies)
    assert manifest.preserved
    assert report.retained_coverage == 100.0
    assert report.safety_retention == 100.0


@pytest.mark.parametrize(
    ("text", "predicate"),
    [
        ("Do not assume remote state is synchronized.", "assume"),
        ("Never import the application root from plugins.", "import"),
        ("Do not introduce machine-local requirements.", "introduce"),
        ("Do not duplicate shared guidance in child files.", "duplicate"),
        ("Do not rely on cached credentials.", "rely"),
        ("Do not invent product behavior.", "invent"),
        ("Do not narrate obvious implementation details.", "narrate"),
    ],
)
def test_general_negative_action_vocabulary_is_structured(text: str, predicate: str):
    parsed = parse_policy_clause(text, "deny")
    assert parsed.status == "structured"
    assert parsed.predicate == predicate
    assert parsed.predicate_kind == "action"
    assert parsed.negated

    narrative = parse_policy_clause(f"The guide says {text[0].lower()}{text[1:]}", "deny")
    assert narrative.status == "unsupported"
    assert narrative.reason_code == "narrative_attribution"


@pytest.mark.parametrize(
    ("text", "predicate"),
    [
        ("Do not hardcode sensitive sample values.", "hardcode"),
        ("Never invoke package installers directly.", "invoke"),
        ("Do not ignore API failures.", "ignore"),
        ("Do not pin a global runtime version.", "pin"),
        ("Never attribute changes to an automated assistant.", "attribute"),
        ("Do not access another tenant.", "access"),
    ],
)
def test_additional_general_negative_predicates_are_structured(text: str, predicate: str):
    parsed = parse_policy_clause(text, "deny")
    assert parsed.status == "structured"
    assert parsed.predicate == predicate
    assert parsed.negated


@pytest.mark.parametrize(
    ("text", "predicate", "objects"),
    [
        ("Generated artifacts are read-only.", "be", ("read-only",)),
        ("Every source file needs a license header.", "need", ("a_license_header",)),
        ("Build metadata required.", "required", ()),
    ],
)
def test_normative_bare_states_are_structured(text: str, predicate: str, objects: tuple[str, ...]):
    parsed = parse_policy_clause(text, "must")
    assert parsed.status == "structured"
    assert parsed.predicate == predicate
    assert parsed.predicate_kind == "state"
    assert parsed.objects == objects


def test_condition_subject_resolves_immediate_singular_pronoun():
    parsed = parse_policy_clause("If release channel is present, it is a lowercase string.", "must")
    assert parsed.status == "structured"
    assert parsed.condition
    assert parsed.subject == ("release_channel",)
    assert "coreference:condition_subject" in parsed.evidence


def test_positive_object_conjunction_uses_explicit_all_operator():
    conjunction = parse_policy_clause("Public functions must include type hints and return annotations.", "must")
    assert conjunction.status == "structured"
    assert conjunction.expression and conjunction.expression.op == "all"
    assert conjunction.objects == ("type_hints", "return_annotations")


def test_avoid_object_and_inline_command_denial_are_structured_without_guessing():
    avoided = parse_policy_clause("Avoid machine-local paths.", "deny")
    assert avoided.status == "structured"
    assert avoided.predicate == "avoid"
    assert avoided.objects == ("machine-local_paths",)

    command = parse_policy_clause("Never `package manager tidy`.", "deny")
    assert command.status == "structured"
    assert command.predicate == "run"
    assert command.negated


def test_deictic_current_document_and_immediate_plural_antecedent_are_structured():
    parsed = parse_policy_clause(
        "Runtime-specific instructions belong here only when they do not apply to other clients.",
        "must",
    )
    assert parsed.status == "structured"
    assert parsed.subject == ("runtime-specific_instructions",)
    assert parsed.predicate == "belong_to"
    assert parsed.objects == ("current_document",)
    assert parsed.condition and parsed.condition.expression.op == "not"
    assert "coreference:subject" in parsed.evidence


def test_deictic_belonging_with_vague_target_remains_ambiguous():
    parsed = parse_policy_clause(
        "Runtime-specific instructions belong here only when they do not apply to relevant clients.",
        "must",
    )
    assert parsed.status == "ambiguous"
    assert parsed.reason_code == "vague_reference"


@pytest.mark.parametrize("text", [
    "Do not combine a packaging change with a runtime migration.",
    "Do not require a tool migration before the architecture changes.",
    "Do not store raw credential metadata.",
    "Do not export provider bindings.",
    "Do not broaden managed permissions.",
])
def test_general_high_risk_negative_actions_are_structured(text: str):
    parsed = parse_policy_clause(text, "deny")
    assert parsed.status == "structured"
    assert parsed.negated


def test_simple_action_condition_and_positive_imperative_attach_to_policy():
    parsed = parse_policy_clause(
        "If you change schema behavior, update all affected layers.",
        "must",
    )
    assert parsed.status == "structured"
    assert parsed.condition and parsed.condition.expression.predicate == "change"
    assert parsed.subject == ("agent",)
    assert parsed.predicate == "update"


def test_negative_without_requirements_becomes_structured_exception_all():
    parsed = parse_policy_clause(
        "Do not add runtime dependencies without a clear need and an explicit tradeoff.",
        "deny",
    )
    assert parsed.status == "structured"
    assert parsed.exceptions and parsed.exceptions[0].expression.op == "all"
    assert parsed.negated


def test_temporal_ordering_is_not_flattened_into_positive_action_target():
    parsed = parse_policy_clause(
        "Provision runtime credentials before enabling remote execution.",
        "must",
    )
    assert parsed.status == "unsupported"
    assert parsed.reason_code == "temporal_sequence_required"


def test_scope_is_not_used_as_subject():
    parsed = parse_policy_clause("Release jobs must use managed credentials within deploy/.", "must")
    assert parsed.status == "structured"
    assert parsed.subject == ("release_jobs",)
    assert parsed.scope == ("deploy/",)
    assert parsed.objects == ("managed_credentials",)


def test_condition_and_exception_attachment_evidence_is_explicit():
    parsed = parse_policy_clause(
        "If environment is production, release jobs must use managed credentials unless mode is local.",
        "must",
    )
    assert parsed.status == "structured"
    assert parsed.condition and parsed.condition.attachment == "policy"
    assert parsed.exceptions and parsed.exceptions[0].attachment == "policy"
    assert {"condition:policy", "exception:policy"} <= set(parsed.evidence)


def test_for_context_causal_rationale_and_example_suffix_are_structured_without_opaque_targets():
    contextual = parse_policy_clause(
        "For self-hosted and local runs, use the default identity chain: workload identity, instance role, or local profile.",
        "must",
    )
    assert contextual.status == "structured"
    assert contextual.condition and contextual.condition.expression.op == "any"
    assert contextual.objects == ("the_default_identity_chain",)
    assert "examples:non_normative" in contextual.evidence

    rationale = parse_policy_clause(
        "Use the managed command because it records an audit event and updates bindings.",
        "must",
    )
    assert rationale.status == "structured"
    assert rationale.objects == ("the_managed_command",)
    assert "rationale:non_operational" in rationale.evidence


def test_short_intentional_requirement_is_a_structured_exception():
    parsed = parse_policy_clause(
        "Avoid exposing secrets in reusable prompts unless intentionally required.",
        "deny",
    )
    assert parsed.status == "structured"
    assert parsed.exceptions
    assert parsed.exceptions[0].expression.objects == ["intentionally_required"]


def test_local_coreference_mixed_modal_clause_becomes_inseparable_allow_deny_policies():
    parsed = parse_policy_clause(
        "You may read from it but NEVER delete it.",
        "must",
        ClauseContext(antecedent="Database: Located at `var/state.db` (SQLite)."),
    )
    policies = parsed.to_policies("must", "high", ["security"])
    assert parsed.status == "structured"
    assert {policy.category for policy in policies} == {"allow", "deny"}
    assert len({policy.link.group for policy in policies if policy.link}) == 1
    assert all(policy.link and policy.link.relation == "inseparable" for policy in policies)
    assert all(policy.scope == ["var/state.db"] for policy in policies)


def test_durable_authorization_and_conditional_approval_compound_are_structured():
    authorization = parse_policy_clause(
        "When the user has asked you to fix, improve, or land work on a non-main branch, you have durable authorization to commit and push to that branch's tracking remote without per-step confirmation.",
        "allow",
    )
    assert authorization.status == "structured"
    assert authorization.category == "allow"
    assert authorization.expression and authorization.expression.op == "all"
    assert authorization.condition

    approval = parse_policy_clause(
        "If backend work is needed and the user did not explicitly ask for it, ask permission first and state the narrow backend change required.",
        "ask",
    )
    policies = approval.to_policies("ask", "high", ["security"])
    assert approval.status == "structured"
    assert {policy.category for policy in policies} == {"ask", "must"}
    assert all(policy.condition_expression for policy in policies)


def test_only_when_all_condition_with_alternative_objects_is_structured():
    parsed = parse_policy_clause(
        "Add an explicit environment file or a generated environment file only when the evaluation needs local secrets and the file exists.",
        "must",
    )
    assert parsed.status == "structured"
    assert parsed.expression and parsed.expression.op == "any"
    assert parsed.condition and parsed.condition.expression.op == "all"
    assert {operand.predicate for operand in parsed.condition.expression.operands} == {"need", "exist"}


def test_compound_belong_use_and_status_relation_stays_one_policy():
    parsed = parse_policy_clause(
        "The selected vault must belong to the account, use external_storage, and have a selectable status (ready or warning).",
        "must",
    )
    assert parsed.status == "structured"
    assert parsed.reason_code == "unique_compound_state"
    assert parsed.expression and parsed.expression.op == "all"
    assert {operand.op for operand in parsed.expression.operands} == {"atomic", "any"}


def test_contrastive_permission_relation_separates_permission_and_comparator():
    parsed = parse_policy_clause(
        "Operators can provision records directly, but the route still requires the same records:create permission as normal creation.",
        "must",
    )
    assert parsed.status == "structured"
    assert parsed.reason_code == "unique_contrastive_relation"
    assert parsed.subject == ("route",)
    assert parsed.objects == ("records:create_permission", "normal_creation")


@pytest.mark.parametrize(
    ("text", "subject", "object_value"),
    [
        ("Agents should check their budget.", "agents", "own_budget"),
        ("IC agents should ask their manager.", "ic_agents", "own_manager"),
    ],
)
def test_explicit_plural_subject_resolves_reflexive_possessive(text: str, subject: str, object_value: str):
    parsed = parse_policy_clause(text, "must")
    assert parsed.status == "structured"
    assert parsed.subject == (subject,)
    assert parsed.objects == (object_value,)
    assert "possessive:reflexive" in parsed.evidence
