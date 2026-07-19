from __future__ import annotations

import hashlib
import re

from .document_ir import CandidateIntent, CommandCandidate, DocumentIR, InstructionCandidate

STRONG_SECTIONS = {
    "agent instructions", "rules", "constraints", "workflow", "process", "development", "setup",
    "local development", "commands", "testing", "linting", "type checking", "build", "deploy",
    "deployment", "security", "safety", "contributing", "pull requests", "before opening a pr",
    "completion criteria", "repository conventions", "documentation",
}
MODALS = ["must", "should", "required", "always", "never", "do not", "don't", "avoid", "ask", "confirm"]
IMPERATIVE_VERBS = ("access", "add", "aim", "assume", "attribute", "change", "check", "classify", "close", "commit", "confirm", "create", "delete", "deploy", "document", "duplicate", "edit", "encourage", "ensure", "fix", "follow", "hardcode", "ignore", "import", "include", "inspect", "introduce", "invent", "invoke", "keep", "kill", "make", "mix", "narrate", "open", "pin", "prefer", "preserve", "read", "rely", "report", "reserve", "respect", "respond", "restore", "route", "run", "start", "state", "stop", "summarize", "target", "update", "use", "validate", "verify", "write")
SAFETY_TERMS = ["secret", "credential", "token", "api key", "production", "destructive", "delete", "drop", "security", "auth", "permission", "deploy"]
TEST_TERMS = ["test", "tests", "suite", "green", "pytest", "unit test", "unit tests", "e2e", "integration"]
COMMAND_PREFIXES = ("pip ", "uv ", "uvicorn", "python ", "pytest", "ruff ", "mypy", "npm ", "pnpm ", "yarn ", "docker ", "alembic", "dbt ", "terraform ", "kubectl ", "make ", "go ", "cargo ")
EXPLANATORY_STARTS = (
    "this project ", "the project ", "the repository ", "the system ", "the frontend ",
    "the backend ", "the api layer ", "the monorepo ", "the readme ", "this section ",
    "contributors use ", "most work ", "most implementation work ", "new screens usually ",
    "node tooling ", "python tooling ", "those notes ", "these notes ", "a reader may ",
    "a new contributor may ", "database changes affect ", "security changes affect ",
    "real monorepo guidance ", "a good pr identifies ", "before a release, reviewers care ",
    "for pull requests, ", "if local setup fails, ", "some contributors use ",
    "infrastructure changes should be especially narrow",
)
EXPLANATORY_PHRASES = (
    "was created to", "is a modern", "is organized around", "explains how",
    "explains local setup", "useful context", "domain context", "architecture context",
    "human orientation", "being retired", "contains backend services",
    "should remain unmapped", "should be reported as unmapped",
    "should only compact", "not required commands",
    "operational parts below",
)
META_SUBJECTS = ("glyph should", "the extraction engine should", "the structural parser should", "generic coding agents should")
PRODUCT_SIGNALS = (
    "must expose", "must implement", "should support", "add a command", "the command should",
    "the cli should", "the mcp server should", "the report should include", "the parser should",
    "the report should", "a useful report should", "the compiler should", "the benchmark should", "the benchmark must", "benchmark must", "create a file", "add support for", "required repository structure",
    "required semantic units", "final response", "glyph must", "glyph should", "compiler must",
    "benchmark suite must", "testing rule is removed", "safety rules such as", "documentation must cover",
    "commands must", "errors must", "ci-related commands must", "all commands must",
)
API_CONTRACT_SIGNALS = (
    "command should", "cli should", "flag", "flags", "json", "schema", "tool names", "entrypoint",
    "entrypoints", "mcp", "api", "function", "class", "module", "file path", "output should",
)
IMPLEMENTATION_SIGNALS = (
    "create module", "add function", "extend class", "update pyproject", "add tests", "write report",
    "generate file", "generate report", "generate a markdown report", "validate schema", "expose service function", "implement", "add deterministic",
    "update tests", "create benchmark", "add benchmark",
)
EXAMPLE_SIGNALS = (
    "example", "for example", "example output", "usage", "expected output", "sample",
    "examples below", "bad example", "good example",
)
NON_OPERATIONAL_SECTIONS = ("overview", "background", "motivation", "what glyph is", "what glyph is not", "purpose")
REFERENCE_TABLE_SECTIONS = ("configuration", "environment", "error code", "field", "option", "parameter", "reference", "variable")
CONDITIONAL_SIGNALS = ("unless", "except", "only if", "if and only if", "when possible", "docs-only", "documentation-only", "not required to run")
RELEASE_SIGNALS = ("release", "publish", "version", "changelog", "tag", "wheel", "smoke")
REPO_SPECIFIC_SIGNALS = (
    "resolver", "router", "presenter", "coordinator", "classifier", "service", "bridge",
    "repository helper", "shared tenant", "tenant-aware", "tenant resolver", "tenant", "route ", "through ",
)
PROSE_FENCE_LANGUAGES = {"", "md", "markdown", "text", "txt"}
ATOMIC_DIRECTIVE_STARTS = (
    "always", "never", "do not", "don't", "avoid", "ask", "confirm", "request",
    "run", "use", "route", "prefer", "preserve", "keep", "check", "verify", "make",
    "create", "report", "summarize", "follow", "update", "document", "validate", "import",
    "include", "introduce", "invent", "duplicate", "narrate", "rely", "assume", "access",
    "aim", "attribute", "classify", "close", "encourage", "fix", "hardcode", "ignore",
    "invoke", "kill", "mix", "open", "pin", "reserve", "respect", "respond", "restore", "start", "stop", "target",
)


def split_sentences(text: str) -> list[str]:
    parts: list[str] = []
    for line in text.splitlines():
        clean = re.sub(r"^[\s>*#\-\d.\[\]xX]+", "", line).strip()
        clean = clean.replace("**", "")
        if not clean:
            continue
        parts.extend(part.strip() for part in re.split(r"(?<=[.!?])\s+", clean) if part.strip())
    return parts


def split_atomic_directives(text: str) -> list[str]:
    """Split only clauses that have their own explicit directive predicate.

    In particular, ``run tests and lint`` stays together: ``lint`` has no
    independent predicate.  ``run tests and report verification`` becomes two
    atomic directives because the second clause starts a new imperative.
    """
    atomic: list[str] = []
    for sentence in split_sentences(text):
        clauses = [part.strip() for part in re.split(r"\s*;\s*", sentence) if part.strip()]
        for clause in clauses:
            match = re.search(
                r"\s+(?:and|then|also)\s+(?=(?:" + "|".join(re.escape(item) for item in ATOMIC_DIRECTIVE_STARTS) + r")\b)",
                clause,
                flags=re.IGNORECASE,
            )
            if match:
                atomic.extend([clause[:match.start()].strip(), clause[match.end():].strip()])
            else:
                atomic.append(clause)
    return [item for item in atomic if item]


def _candidate_id(text: str, section: str | None, block_type: str) -> str:
    value = "\0".join([" ".join(text.split()), (section or "").lower(), block_type])
    return "c_" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def _inherited_category(section: str | None, parents: list[str]) -> str | None:
    """Infer deontic mode only from headings that are themselves directives.

    Product and collection titles frequently contain words such as ``rules``
    or ``workflow``.  Treating any ancestor containing those tokens as a
    normative heading turns every descendant catalog entry into a policy.
    Evaluate headings independently and require an explicit directive phrase
    or a complete normative heading instead.
    """
    headings = [" ".join(value.lower().split()) for value in [*parents, section or ""] if value.strip()]
    if any(re.search(r"\b(ask first|ask before|confirmation required|required approval|approval required)\b", heading) for heading in headings):
        return "ask"
    if any(
        re.fullmatch(r"(?:what )?(?:never|do not|don't|forbidden|prohibited|avoid)(?:\s+.+)?", heading)
        or re.fullmatch(r"(?:things|actions|changes) to avoid", heading)
        for heading in headings
    ):
        return "deny"
    normative_headings = {
        "agent instructions",
        "completion criteria",
        "constraints",
        "development rules",
        "guidelines",
        "instructions",
        "requirements",
        "rules",
        "workflow",
    }
    if any(
        heading in normative_headings
        or re.fullmatch(r"(?:always|must|required)(?:\s+.+)?", heading)
        or re.fullmatch(r"(?:rules|requirements|instructions|guidelines) (?:for|when|while) .+", heading)
        for heading in headings
    ):
        return "must"
    return None


def looks_like_command(value: str) -> bool:
    stripped = value.strip().strip("$ ").strip("`")
    return stripped.startswith(COMMAND_PREFIXES) or bool(re.match(r"^[A-Z_]+=.+\s+\w+", stripped))


def _has_directive_language(lowered: str) -> bool:
    if any(re.search(r"(?<![a-z])" + re.escape(modal) + r"(?![a-z])", lowered) for modal in MODALS):
        return True
    verb_pattern = "|".join(re.escape(verb) for verb in IMPERATIVE_VERBS)
    predicate = r"(?:please\s+)?(?:" + verb_pattern + r")(?![a-z_-])"
    return bool(
        re.match(r"^" + predicate, lowered)
        or re.match(r"^(?:if|when|before|after|on|for)\b.{1,240}?,\s*" + predicate, lowered)
        or re.match(r"^[a-z][a-z0-9 _./-]{0,80}:\s*" + predicate, lowered)
    )


def _source_code_comment_directives(text: str) -> list[str]:
    """Extract policies only from explicit comments in source-code fences."""
    directives: list[str] = []
    for line in text.splitlines():
        match = re.match(r"^(?:#|//|--|/\*+|\*|<!--)\s*(.*?)\s*(?:\*/|-->)?$", line.strip())
        if not match:
            continue
        comment = match.group(1).strip()
        if comment and _has_directive_language(comment.lower()):
            directives.extend(split_atomic_directives(comment))
    return directives


def _looks_explanatory(lowered: str, section: str | None) -> bool:
    section_lower = (section or "").lower()
    if any(lowered.startswith(subject) for subject in META_SUBJECTS):
        return True
    if any(phrase in lowered for phrase in EXPLANATORY_PHRASES):
        return True
    if any(lowered.startswith(prefix) for prefix in EXPLANATORY_STARTS) and not lowered.startswith(("the agent must", "the agent should", "the assistant must", "the assistant should")):
        if not re.search(r"\b(must|always|never|do not|don't|avoid|ask|confirm|run|verify|report|update|preserve|keep|prefer|follow)\b", lowered):
            return True
        if any(word in section_lower for word in ["context", "overview", "notes"]) and not re.search(r"\b(must|always|never|do not|don't|avoid|ask|confirm)\b", lowered):
            return True
    if any(word in section_lower for word in ["context", "overview", "notes"]):
        if lowered.startswith(("it should ", "they should ", "those ", "these ")) or " should " in lowered and "coding agent" not in lowered:
            return True
        if not _has_directive_language(lowered) and not lowered.startswith(("use ", "run ", "keep ", "avoid ", "never ", "do not ", "update ", "preserve ")):
            return True
    return False


def _row_is_command_reference(text: str, section: str | None, block_type: str) -> bool:
    if block_type != "table":
        return False
    cells = [cell.strip().strip("`") for cell in text.split("|")]
    if any(looks_like_command(cell) for cell in cells):
        return True
    lowered = text.lower()
    return bool(section and section.lower() == "commands" and re.search(r"\b(test|tests|build|install|dev|lint|typecheck|deploy|migrate)\b", lowered))


def _looks_like_catalog_reference(text: str, block_type: str) -> bool:
    """Recognize linked catalog entries without suppressing real directives."""
    return (
        block_type in {"bullet_list", "numbered_list"}
        and bool(re.search(r"\]\(https?://[^)]+\)", text))
        and not _has_directive_language(text.lower())
    )


def _looks_like_path_catalog_reference(text: str, block_type: str) -> bool:
    return (
        block_type in {"bullet_list", "numbered_list"}
        and bool(re.match(r"^`?[-\w./]+/?`?\s+(?:-|–|—)\s+", text))
        and not _has_directive_language(text.lower())
    )


def _looks_like_reference_label(text: str, document_role: str) -> bool:
    if document_role == "agent_instructions":
        return False
    lowered = text.lower().strip().replace("**", "")
    if re.match(r"^(?:always|never|do not|don't|avoid|use|run|keep|read|write|check|verify)\b", lowered):
        return False
    if re.fullmatch(r"required\s+[a-z][a-z0-9 _/-]{1,80}", lowered):
        return True
    label = re.fullmatch(r"(`?[-a-z0-9_. ]+`?)\s*:\s*(.+)", lowered)
    if not label:
        return False
    key, value = label.group(1), label.group(2)
    if key.startswith("`"):
        return True
    if key == "authentication" and re.match(r"^(?:login|no login|authentication|auth)\b.*\b(?:required|optional|enabled|disabled)\b|^login required\b", value):
        return True
    if _has_directive_language(value):
        return False
    return bool(
        key == "hook point"
        or re.match(r"^(?:required|optional|login required|no login required|target/config-path declarations)\b", value)
        or "required/optional" in value
    )


def _looks_like_reference_table(text: str, section: str | None, block_type: str) -> bool:
    if block_type != "table":
        return False
    section_lower = (section or "").lower()
    cells = [cell.strip() for cell in text.split("|")]
    first = cells[0] if cells else ""
    token_key = bool(re.fullmatch(r"`?[A-Z][A-Z0-9_]+`?", first))
    code_or_status_key = bool(re.fullmatch(r"`?(?:\d{3}|--?[a-z0-9-]+|[a-z][a-z0-9_.-]*)`?", first, flags=re.IGNORECASE))
    return any(term in section_lower for term in REFERENCE_TABLE_SECTIONS) and (token_key or code_or_status_key)


def _looks_like_product_contract(text: str, section: str | None, document_role: str) -> bool:
    """Separate component behavior from instructions addressed to a worker."""
    if document_role == "agent_instructions":
        return False
    lowered = re.sub(r"[*_`]", "", text.lower()).strip()
    if re.match(r"^(?:always|never|do not|don't|avoid|ask|confirm|run|use|keep|read|write|check|verify|update|preserve|deploy|commit)\b", lowered):
        return False
    if re.match(r"^(?:if|when)\s+(?:you|we|contributors?|developers?|maintainers?|reviewers?|agents?)\b", lowered):
        return False
    governed_subject = r"(?:agents?|assistants?|contributors?|developers?|maintainers?|reviewers?|users?|you|we|code|changes?|files?|tests?|pull requests?|prs?|commits?|implementations?)"
    if re.match(rf"^(?:the\s+)?{governed_subject}\b.{{0,80}}\b(?:must|should|never|do not|don't|required)\b", lowered):
        return False
    product_subject = (
        r"(?:api|ui|server|service|system|runtime|adapter|provider|endpoint|response|request|command|warning|output|view|views|role|home|"
        r"config(?:uration)?|field|schema|application|app|vault|dialog|workflow|integration|"
        r"secret(?:s| values?| refs?)?|user-secret refs?|credentials?|tokens?|paths?|values?|merges?|normalization|imported references?|exported data|"
        r"environment variables?|database|deployment|deployments|home|homes|record|package|feature)"
    )
    qualified_product_subject = rf"(?:[a-z0-9_/-]+\s+){{0,4}}{product_subject}"
    subject_contract = re.match(
        rf"^(?:the\s+|an?\s+|existing\s+|required\s+|missing\s+|local\s+|board/admin\s+|prompt-level\s+)?{qualified_product_subject}\b.{{0,160}}\b(?:must|should|never|may|can|do not|does not|needs?|requires?|fails?|uses?|stores?|accepts?|returns?|displays?|includes?|exports?|resolves?|preselects?|copies?|updates?|drops?)\b",
        lowered,
    )
    causal_contract = re.match(r"^(?:because|this keeps?|this allows?|imported|existing)\b", lowered) and re.search(product_subject, lowered)
    passive_data_contract = re.search(r"\bmust not be (?:exported|stored|returned|logged|printed|included)\b", lowered) and re.search(r"\b(?:paths?|values?|credentials?|tokens?|data|refs?)\b", lowered)
    relative_contract = re.match(r"^[a-z][^.!?]{0,100}\bthat must be\b", lowered)
    section_lower = (section or "").lower()
    contract_section = any(term in section_lower for term in ("api", "authentication", "behavior", "configuration", "declaration", "deployment", "health", "import", "provider", "response", "runtime", "secret", "semantics", "vault", "warning"))
    pronoun_contract = contract_section and re.match(r"^(?:it|they)\s+(?:must|should|never|do not|don't|can|may)\b", lowered)
    nested_component_contract = re.match(r"^(?:an?|the)\s+.+?\s+(?:is|are)\s+.+?,\s+(?:so|and)\s+the\s+(?:adapter|provider|runtime|service|api)\s+must\b", lowered)
    conditional_component_contract = re.match(
        r"^(?:if|when)\s+.+?,\s+(?:the\s+)?(?:adapter|provider|runtime|service|api|ui|response|operation|wrapper|deployment|deployments)\s+(?:must|should|can|may|runs?|retries|reconnects?|falls?|defaults?|uses?|includes?|deletes?)\b",
        lowered,
    )
    for_component_contract = re.match(r"^for\s+.+?,\s+(?:the\s+)?(?:adapter|provider|runtime|service|api|ui|response|operation|wrapper|role)\s+(?:must|should|can|may|needs?|requires?)\b", lowered)
    option_contract = re.match(r"^`?--?[a-z0-9-]+(?:\s+[a-z0-9_-]+)?`?\s+(?:updates?|uses?|sets?|selects?|controls?)\b", lowered)
    passive_component_contract = re.match(
        rf"^(?:the\s+|an?\s+|managed\s+|authenticated\s+)?{qualified_product_subject}\b.{{0,160}}\b(?:is|are)\s+(?:always\s+|never\s+)?[a-z][a-z_-]*ed\b",
        lowered,
    )
    cross_reference = re.match(r"^for\s+.+?,\s+see\s+.+", lowered) and bool(re.search(r"`[^`]+\.(?:md|mdc)`|\[[^]]+\]\([^)]+\)", text))
    return bool(subject_contract or causal_contract or passive_data_contract or relative_contract or pronoun_contract or nested_component_contract or conditional_component_contract or for_component_contract or option_contract or passive_component_contract or cross_reference)


def operational_score(text: str, section: str | None, block_type: str) -> tuple[float, list[str]]:
    lowered = text.lower()
    if _row_is_command_reference(text, section, block_type):
        return 0.0, ["command_reference"]
    if looks_like_command(text):
        return 0.0, ["command_reference"]
    if lowered.startswith(("thanks ", "thank you ")):
        return 0.0, ["courtesy"]
    if any(phrase in lowered for phrase in ["this context", "background prose", "benchmark", "orientation", "documentation context", "not operational", "human orientation", "operational parts matter"]):
        return 0.0, ["context_prose"]
    if _looks_explanatory(lowered, section):
        return 0.0, ["explanatory_prose"]
    if "work mainly in" in lowered or "relevant paths" in lowered:
        return 0.0, ["scope_context"]
    if section and section.lower() == "commands" and lowered.rstrip().endswith(":"):
        return 0.0, ["command_label"]
    if lowered.rstrip().endswith(":") and not re.search(r"\b(must|always|never|do not|don't|avoid|ask|confirm)\b", lowered):
        return 0.0, ["command_label"]
    # Mere mentions of tests, security, or APIs are documentation, not agent
    # guidance.  A directive needs modal language or an imperative predicate.
    if not _has_directive_language(lowered):
        return 0.0, ["no_directive_predicate"]
    reasons: list[str] = []
    score = 0.0
    verb_pattern = "|".join(re.escape(verb) for verb in IMPERATIVE_VERBS)
    imperative_match = re.match(
        r"^(?:(?:if|when|before|after|on|for)\b.{1,240}?,\s*|[a-z][a-z0-9 _./-]{0,80}:\s*)?(?:please\s+)?("
        + verb_pattern
        + r")(?![a-z_-])",
        lowered,
    )
    if imperative_match:
        reasons.extend(["imperative", f"modal:{imperative_match.group(1)}"])
        score += 0.18
    for modal in MODALS:
        pattern = r"(?<![a-z])" + re.escape(modal) + r"(?![a-z])"
        if re.search(pattern, lowered):
            reasons.append(f"modal:{modal.replace(' ', '_')}")
            score += 0.18
            break
    if any(term in lowered for term in SAFETY_TERMS):
        reasons.append("safety_term")
        score += 0.22
    if any(term in lowered for term in TEST_TERMS):
        reasons.append("testing_term")
        score += 0.18
    if section and section.lower() in STRONG_SECTIONS:
        reasons.append(f"section:{section.lower().replace(' ', '_')}")
        score += 0.24
    if block_type in {"bullet_list", "numbered_list", "checklist", "table"}:
        reasons.append(f"block:{block_type}")
        score += 0.12
    if re.search(r"\b(src|tests|docs|backend|frontend|database|helper|generated|package|packages|pr|files|editing|changes|credentials|secrets)\b", lowered):
        reasons.append("repository_specific_instruction")
        score += 0.12
    if looks_like_command(text):
        reasons.append("command_like")
        score += 0.18
    if reasons == ["safety_term"] or reasons == ["testing_term"] or (len(reasons) == 1 and reasons[0].startswith("section:")):
        return 0.1, reasons
    return min(score, 1.0), reasons


def _contains_any(lowered: str, values: tuple[str, ...] | list[str]) -> bool:
    return any(value in lowered for value in values)


def _looks_like_path_or_symbol(text: str) -> bool:
    return bool(re.search(r"(`[^`]+`|[\w./-]+\.(?:py|md|json|toml|yml|yaml|mdc|glp)|\b[a-zA-Z_][\w]*\(|--[a-z0-9-]+|\bglyph [a-z-]+)", text))


def classify_candidate_intent(
    text: str,
    section: str | None,
    block_type: str,
    previous_text: str = "",
    inherited_category: str | None = None,
    document_role: str = "mixed",
) -> tuple[CandidateIntent, float, list[str], str, float, list[str]]:
    lowered = text.lower()
    section_lower = (section or "").lower()
    previous_lower = previous_text.lower()
    signals: list[str] = []
    operational_confidence, reasons = operational_score(text, section, block_type)

    if document_role == "implementation_spec":
        signals.append("implementation_spec_context")
        return "implementation_requirement", 0.94, signals, "Implementation-plan content is not an active reusable agent directive.", 0.0, ["implementation_spec_context"]

    # A collection can legitimately use a heading such as "Rules" for a list
    # of linked artifacts.  Reference syntax is stronger evidence than the
    # inherited heading mode unless the entry itself contains a directive.
    if _looks_like_catalog_reference(text, block_type):
        signals.append("catalog_reference")
        return "reference_content", 0.92, signals, "Linked catalog entry is reference material, not an active instruction.", 0.0, ["catalog_reference"]

    if _looks_like_path_catalog_reference(text, block_type):
        signals.append("path_catalog_reference")
        return "reference_content", 0.92, signals, "Path catalog entry is reference material, not an active instruction.", 0.0, ["path_catalog_reference"]

    if _looks_like_reference_label(text, document_role):
        signals.append("reference_label")
        return "reference_content", 0.92, signals, "Configuration label is reference material, not an active instruction.", 0.0, ["reference_label"]

    if _looks_like_reference_table(text, section, block_type):
        signals.append("reference_table")
        return "api_contract", 0.92, signals, "Configuration or status table row is reference data, not an active instruction.", 0.0, ["reference_table"]

    if _looks_like_product_contract(text, section, document_role):
        signals.append("product_contract_subject")
        return "api_contract", 0.9, signals, "Component behavior is classified as a product/API contract rather than an instruction to an agent.", 0.0, ["product_contract_subject"]

    if document_role != "agent_instructions" and "command_label" in reasons:
        signals.append("command_example_label")
        return "reference_content", 0.92, signals, "A command-example label introduces code but is not itself an operational policy.", 0.0, ["command_example_label"]

    if document_role != "agent_instructions" and re.match(r"^run\s+this\b", lowered) and looks_like_command(previous_text):
        signals.append("preceding_command_reference")
        return "reference_content", 0.92, signals, "A deictic run instruction refers to the preceding extracted command.", 0.0, ["preceding_command_reference"]

    # A terse list under a modal heading is still an instruction.  This is
    # intentionally evaluated before generic narrative/API heuristics.
    if inherited_category and text.strip() and not looks_like_command(text) and (
        block_type in {"bullet_list", "numbered_list", "checklist", "table"}
        or operational_confidence >= 0.18
    ):
        signals.append(f"inherited:{inherited_category}")
        return (
            "agent_instruction",
            0.9,
            signals,
            f"Directive mode is inherited from the enclosing {inherited_category} section.",
            max(operational_confidence, 0.8),
            reasons + signals,
        )

    if _row_is_command_reference(text, section, block_type) or looks_like_command(text):
        signals.append("command_reference")
        return "reference_content", 0.88, signals, "Command snippets are extracted as commands, not active unmapped instructions.", 0.0, ["command_reference"]

    explicit_example_starts = ("example", "for example", "sample", "expected output")
    if lowered.startswith(explicit_example_starts) or _contains_any(section_lower, EXAMPLE_SIGNALS) or _contains_any(previous_lower, EXAMPLE_SIGNALS):
        signals.append("example_context")
        return "example_content", 0.92, signals, "Example or sample content is classified but not treated as an active rule.", 0.0, ["example_context"]

    if block_type == "table" and ("contract" in section_lower or "cli" in section_lower or "api" in section_lower):
        signals.append("contract_table")
        return "api_contract", 0.82, signals, "Contract table row is classified as API or CLI reference.", 0.0, ["contract_table"]

    if block_type == "table" and _looks_like_path_or_symbol(text):
        signals.append("contract_table")
        return "api_contract", 0.82, signals, "Table row contains command, path, schema, or symbol contract details.", 0.0, ["contract_table"]

    has_conditional = _contains_any(lowered, CONDITIONAL_SIGNALS) or bool(re.match(r"^(?:if|when)\b", lowered))
    if has_conditional and document_role != "agent_instructions" and not _has_directive_language(lowered):
        signals.append("non_operational_conditional_description")
        return "api_contract", 0.88, signals, "Conditional product or configuration description has no agent-directed predicate.", 0.0, reasons + signals
    if has_conditional and any(word in section_lower for word in ("context", "overview", "notes")) and not any(term in lowered for term in TEST_TERMS + SAFETY_TERMS):
        signals.append("non_operational_context")
        return "non_operational_context", 0.8, signals, "Conditional setup prose in a context section is not an active agent directive.", 0.0, reasons + signals
    if has_conditional and not ("requested" in lowered and not any(term in lowered for term in TEST_TERMS)):
        signals.append("conditional_language")
        if any(term in lowered for term in TEST_TERMS + SAFETY_TERMS):
            return "conditional_instruction", 0.9, signals, "Conditional policy may require exception semantics not available in .glp v0.1.", max(operational_confidence, 0.62), reasons + signals
        return "conditional_instruction", 0.78, signals, "Conditional wording is reported because .glp v0.1 does not encode exceptions.", max(operational_confidence, 0.24), reasons + signals

    if _contains_any(lowered, PRODUCT_SIGNALS):
        signals.append("product_requirement_language")
        if _contains_any(lowered, API_CONTRACT_SIGNALS) or _looks_like_path_or_symbol(text):
            signals.append("api_contract_signal")
            return "api_contract", 0.9, signals, "Product requirement defines CLI, MCP, API, path, or schema contract.", 0.0, reasons + signals
        return "product_requirement", 0.88, signals, "Product/spec requirement is classified for reports but not compressed as an agent rule.", 0.0, reasons + signals

    if "token reduction" in lowered or "token usage" in lowered or "token cost" in lowered or "token count" in lowered or "token savings" in lowered:
        signals.append("non_operational_context")
        return "non_operational_context", 0.8, signals, "Token-savings context is not treated as credential/token safety policy.", 0.0, reasons + signals

    if _contains_any(lowered, IMPLEMENTATION_SIGNALS):
        signals.append("implementation_requirement_language")
        return "implementation_requirement", 0.86, signals, "Implementation requirement is classified separately from reusable agent semantics.", 0.0, reasons + signals

    if re.search(r"\b(use|run)\s+`?(pytest|ruff|mypy|npm|pnpm|yarn|python -m build)", lowered):
        signals.append("command_instruction")
        return "command_instruction", 0.86, signals, "Tooling instruction is classified with commands instead of high-risk unmapped policy.", max(operational_confidence, 0.42), reasons + signals

    if _contains_any(lowered, RELEASE_SIGNALS) and _has_directive_language(lowered):
        signals.append("release_policy")
        return "release_policy", 0.84, signals, "Release policy is operational but may be repo-specific unless mapped.", max(operational_confidence, 0.44), reasons + signals

    if any(term in lowered for term in TEST_TERMS) and _has_directive_language(lowered):
        signals.append("testing_policy")
        return "testing_policy", 0.9, signals, "Testing policy is eligible for semantic mapping when a registered rule matches.", max(operational_confidence, 0.6), reasons + signals

    if any(term in lowered for term in SAFETY_TERMS) and _has_directive_language(lowered):
        signals.append("safety_policy")
        return "safety_policy", 0.9, signals, "Safety policy is eligible for semantic mapping when a registered rule matches.", max(operational_confidence, 0.6), reasons + signals

    if _contains_any(lowered, API_CONTRACT_SIGNALS) and _looks_like_path_or_symbol(text):
        signals.append("api_contract_signal")
        return "api_contract", 0.84, signals, "Candidate contains API, CLI, schema, tool, module, or path contract details.", 0.0, reasons + signals

    if looks_like_command(text) or (section_lower == "commands" and _has_directive_language(lowered)):
        signals.append("command_instruction")
        return "command_instruction", 0.86, signals, "Command instruction is tracked and command extraction handles executable commands.", max(operational_confidence, 0.42), reasons + signals

    if operational_confidence >= 0.18 and (_contains_any(lowered, REPO_SPECIFIC_SIGNALS) or re.search(r"\b[A-Z][A-Za-z0-9]+(?:Resolver|Router|Presenter|Coordinator|Classifier|Service|Bridge|Policy|Helper|Gate|Builder|Parser)\b", text)):
        signals.append("repo_specific_candidate")
        return "repo_convention", 0.84, signals, "Repository-specific directive should be mapped by a custom rule if important.", operational_confidence, reasons + signals

    if operational_confidence >= 0.18:
        signals.append("agent_instruction")
        return "agent_instruction", min(0.86, 0.55 + operational_confidence / 2), signals, "General operational agent instruction is eligible for semantic mapping.", operational_confidence, reasons + signals

    if _looks_explanatory(lowered, section) or any(term in section_lower for term in NON_OPERATIONAL_SECTIONS):
        signals.append("non_operational_context")
        return "non_operational_context", 0.78, signals, "Context or background prose is classified as non-operational.", 0.0, reasons + signals

    if _has_directive_language(lowered):
        signals.append("weak_directive_language")
        return "unknown_operational", 0.5, signals, "Directive-like wording could not be safely classified or mapped.", max(operational_confidence, 0.24), reasons + signals

    signals.append("reference_content")
    return "reference_content", 0.7, signals, "Reference content is retained in reports but not compressed.", 0.0, reasons + signals


def extract_instruction_candidates(doc: DocumentIR, include_classified: bool = False) -> list[InstructionCandidate]:
    candidates: list[InstructionCandidate] = []
    previous_text = ""
    for block in doc.blocks:
        if block.type in {"heading", "horizontal_rule", "inline_code"}:
            previous_text = block.text
            continue
        if block.type == "fenced_code_block":
            inherited = _inherited_category(block.section, block.parent_headings)
            if (block.code_language or "").lower() not in PROSE_FENCE_LANGUAGES:
                comment_directives = _source_code_comment_directives(block.text) if doc.role == "agent_instructions" else []
                for line in comment_directives:
                    line_intent, line_confidence, line_signals, line_summary, line_score, line_reasons = classify_candidate_intent(line, block.section, block.type, previous_text, inherited, doc.role)
                    if line_score >= 0.18 or include_classified:
                        candidates.append(InstructionCandidate(id=_candidate_id(line, block.section, block.type), text=line, source=block.source, line=block.line_start, section=block.section, block_type=block.type, intent=line_intent, intent_confidence=line_confidence, operational_confidence=line_score, reasons=line_reasons, signals=line_signals, reasoning_summary=line_summary, inherited_category=inherited))
                previous_text = block.text
                continue
            intent, intent_confidence, signals, summary, score, reasons = classify_candidate_intent(block.text, block.section, block.type, previous_text, inherited, doc.role)
            if intent in {"example_content", "api_contract", "reference_content"}:
                if include_classified or score >= 0.18:
                    candidates.append(InstructionCandidate(id=_candidate_id(block.text, block.section, block.type), text=block.text, source=block.source, line=block.line_start, section=block.section, block_type=block.type, intent=intent, intent_confidence=intent_confidence, operational_confidence=score, reasons=reasons, signals=signals, reasoning_summary=summary, inherited_category=inherited))
            elif inherited and any(_has_directive_language(line.lower()) for line in block.text.splitlines()):
                for line in split_atomic_directives(block.text):
                    line_intent, line_confidence, line_signals, line_summary, line_score, line_reasons = classify_candidate_intent(line, block.section, block.type, previous_text, inherited, doc.role)
                    candidates.append(InstructionCandidate(id=_candidate_id(line, block.section, block.type), text=line, source=block.source, line=block.line_start, section=block.section, block_type=block.type, intent=line_intent, intent_confidence=line_confidence, operational_confidence=line_score, reasons=line_reasons, signals=line_signals, reasoning_summary=line_summary, inherited_category=inherited))
            previous_text = block.text
            continue
        previous_lower = previous_text.lower()
        if block.type in {"bullet_list", "numbered_list", "checklist"} and (
            "what not to do" in previous_lower or "examples below show" in previous_lower or "bad examples" in previous_lower
        ):
            for text in [item.strip() for item in block.text.splitlines() if item.strip()]:
                if include_classified:
                    candidates.append(InstructionCandidate(id=_candidate_id(text, block.section, block.type), text=text, source=block.source, line=block.line_start, section=block.section, block_type=block.type, intent="example_content", intent_confidence=0.9, operational_confidence=0.0, reasons=["example_context"], signals=["example_context"], reasoning_summary="Example or anti-example list item is not treated as an active rule."))
            previous_text = block.text
            continue
        texts = []
        if block.type in {"bullet_list", "numbered_list", "checklist"}:
            texts = [item.strip() for item in block.text.splitlines() if item.strip()]
        elif block.type == "table":
            for row in block.table_rows[1:]:
                texts.append(" | ".join(row))
        else:
            texts = split_sentences(block.text)
        inherited = _inherited_category(block.section, block.parent_headings)
        paragraph_antecedent: str | None = None
        for raw_text in texts:
            atomic_texts = split_atomic_directives(raw_text) if block.type not in {"table"} else [raw_text]
            for atomic_index, text in enumerate(atomic_texts):
                intent, intent_confidence, signals, summary, score, reasons = classify_candidate_intent(text, block.section, block.type, previous_text, inherited, doc.role)
                if score >= 0.18 or (include_classified and intent not in {"reference_content"}):
                    local_antecedent = atomic_texts[atomic_index - 1] if atomic_index else (paragraph_antecedent if block.type == "paragraph" else None)
                    candidates.append(InstructionCandidate(id=_candidate_id(text, block.section, block.type), text=text, source=block.source, line=block.line_start, section=block.section, block_type=block.type, intent=intent, intent_confidence=intent_confidence, operational_confidence=score, reasons=reasons, signals=signals, reasoning_summary=summary, inherited_category=inherited, local_antecedent=local_antecedent))
            if block.type == "paragraph" and atomic_texts:
                paragraph_antecedent = atomic_texts[-1]
        previous_text = block.text
    return candidates


def extract_command_candidates(doc: DocumentIR) -> list[CommandCandidate]:
    out: list[CommandCandidate] = []
    previous_text = ""
    for block in doc.blocks:
        values: list[tuple[str, str]] = []
        if block.type == "fenced_code_block":
            values = [(line.strip().strip("$ "), previous_text) for line in block.text.splitlines() if line.strip() and not line.strip().startswith("#")]
        elif block.type == "inline_code":
            values = [(block.text.strip().strip("$ "), previous_text)]
        elif block.type == "table":
            for row in block.table_rows[1:]:
                for cell in row:
                    values.append((cell.strip().strip("$ "), " ".join(row)))
        elif block.type in {"bullet_list", "numbered_list", "checklist", "paragraph"}:
            values = [(m.strip().strip("$ "), block.text) for m in re.findall(r"`([^`\n]+)`", block.text)]
        for command, context in values:
            normalized = command.strip().strip("$ ").strip("`")
            context_lower = context.lower()
            if any(phrase in context_lower for phrase in ["not required", "exists for maintainers", "who want to run", "want to run it"]):
                continue
            if looks_like_command(normalized):
                out.append(CommandCandidate(command=normalized, source=block.source, line=block.line_start, section=block.section, block_type=block.type, context=context))
        if block.type not in {"fenced_code_block", "inline_code", "horizontal_rule"}:
            previous_text = block.text
    return out
