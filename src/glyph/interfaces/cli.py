from __future__ import annotations

import json as json_module
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from ..core.models import CompressionProfile
from ..formats.parser import parse_glp
from ..formats.renderer import render_glp, render_markdown
from ..governance.benchmark import benchmark_real as benchmark_real_run
from ..governance.benchmark import run_benchmark
from ..governance.check import check_lock, check_pair
from ..governance.diff import load_any, semantic_diff
from ..governance.emit import TARGET_TITLES, emit_markdown
from ..governance.lint import lint_text, warning_lines
from ..governance.lock import write_lock
from ..governance.reports import report_to_json, write_report
from ..governance.score import badge as badge_line
from ..governance.score import score_path
from ..governance.select import select_output
from .config import GlyphConfig, default_config_text, load_config
from .diagnostics import PACKAGE_NAME, doctor_info, version_info
from ..pipeline.compiler import analyze_files, compile_files
from ..pipeline.verifier import verify
from ..semantics.custom_rules import load_custom_rules, suggest_rules
from ..source.adapters import validate_adapter
from ..source.tokenizer import count_tokens

app = typer.Typer(help="Glyph: compile agent instructions into compact .glp semantic manifests.")
rules_app = typer.Typer(help="Work with custom Glyph semantic rules.")
app.add_typer(rules_app, name="rules")
console = Console()


MINIMAL_AGENTS_GLP = """glyph/0.1

flow[read,plan,minimal_change,test,report]

must[
  run_tests_before_done
  report_changes
  report_verification
]

deny[
  secrets_commit
]

ask[
  destructive_ops
]
"""


def _fail(message: str) -> None:
    console.print(f"Error: {message}", markup=False)
    raise typer.Exit(1)


def _load_config_or_exit() -> GlyphConfig | None:
    try:
        return load_config()
    except ValueError as exc:
        _fail(f"{exc}\nFix .glyph/config.toml or remove it.")


def _config_rules(rules: Path | None, config: GlyphConfig | None) -> Path | None:
    if rules is not None:
        return rules
    if config and config.paths.rules:
        return Path(config.paths.rules)
    return None


def _ensure_inputs_exist(paths: list[Path]) -> None:
    for path in paths:
        if not path.exists():
            _fail(f"{path} does not exist.\nCheck the path or create the file before running Glyph.")
        if not path.is_file():
            _fail(f"{path} is not a file.\nPass a Markdown instruction file.")


def _ensure_parent_exists(path: Path) -> None:
    parent = path.parent
    if parent and not parent.exists():
        _fail(f"Output directory {parent} does not exist.\nCreate it first, or choose another output path with -o.")


def _read_text(path: Path, kind: str = "file") -> str:
    if not path.exists():
        _fail(f"{path} does not exist.\nCheck the {kind} path and try again.")
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        _fail(f"Could not read {path}: {exc}")


def _parse_manifest(path: Path):
    try:
        return parse_glp(_read_text(path, ".glp manifest"))
    except ValueError as exc:
        _fail(f"Invalid .glp syntax in {path}: {exc}\nRun `glyph compile ... -o {path}` to regenerate it.")


@app.command(help="Print Glyph version and local capability information.")
def version(json_output: bool = typer.Option(False, "--json", help="Output machine-readable JSON.")) -> None:
    info = version_info()
    if json_output:
        typer.echo(json_module.dumps(info, indent=2) + "\n", nl=False)
        return
    console.print(f"Glyph {info['glyph_version']}")
    console.print(f"Python: {info['python_version']}")
    console.print(f"Package: {info['package_name']}")
    console.print(f"MCP: {'available' if info['mcp_available'] else 'unavailable'}")
    console.print(f"Tokenizer: {info['tokenizer']}")


@app.command(help="Check whether the local Glyph environment is ready.")
def doctor(json_output: bool = typer.Option(False, "--json", help="Output machine-readable JSON.")) -> None:
    info = doctor_info()
    if json_output:
        typer.echo(json_module.dumps(info, indent=2) + "\n", nl=False)
    else:
        console.print("Glyph doctor\n")
        console.print(f"{'Version:':22} {info['glyph_version']}")
        console.print(f"{'Package:':22} {PACKAGE_NAME}")
        console.print(f"{'CLI:':22} glyph")
        console.print(f"{'Python:':22} {info['python_version']}")
        console.print(f"{'Install path:':22} {info['install_path']}", markup=False)
        console.print(f"{'Tokenizer:':22} {info['tokenizer']}")
        console.print(f"{'MCP support:':22} {'installed' if info['mcp_available'] else 'not installed'}")
        if not info["mcp_available"]:
            console.print(f"{'Install with:':22} pip install \"{PACKAGE_NAME}[mcp]\"", markup=False)
        console.print(f"{'Writable cwd:':22} {'yes' if info['writable_cwd'] else 'no'}")
        build = info["build_metadata"]
        console.print(f"{'Build metadata:':22} {build['name'] + ' ' + build['version'] if build else 'not installed as distribution'}")
        console.print("\nSanity checks:")
        for check in info["sanity_checks"]:
            marker = "✓" if check["ok"] else "✗"
            suffix = "" if check["ok"] else f" ({check['error']})"
            console.print(f"{marker} {check['name']}{suffix}", markup=False)
        console.print(f"\nStatus: {info['status']}")
    if info["status"] != "ok" or not info["writable_cwd"]:
        raise typer.Exit(1)


@app.command(help="Initialize Glyph config and an AGENTS.glp manifest.")
def init(
    from_path: Optional[Path] = typer.Option(None, "--from", help="Compile an existing Markdown instruction file."),
    force: bool = typer.Option(False, "--force", help="Overwrite existing Glyph files."),
) -> None:
    config_path = Path(".glyph/config.toml")
    manifest_path = Path("AGENTS.glp")
    lock_path = Path("glyph.lock.json")
    targets = [config_path, manifest_path]
    if from_path is not None:
        targets.append(lock_path)
        _ensure_inputs_exist([from_path])
    existing = [path for path in targets if path.exists()]
    if existing and not force:
        names = ", ".join(str(path) for path in existing)
        _fail(f"{names} already exist.\nUse --force to overwrite them, or move the existing files first.")
    config_path.parent.mkdir(parents=True, exist_ok=True)
    source_for_config = str(from_path) if from_path is not None else "AGENTS.md"
    config_path.write_text(default_config_text(source_for_config, str(manifest_path)), encoding="utf-8")
    if from_path is not None:
        manifest = compile_files([from_path])
        manifest_path.write_text(render_glp(manifest), encoding="utf-8")
        write_lock([from_path], lock_path)
    else:
        manifest_path.write_text(MINIMAL_AGENTS_GLP, encoding="utf-8")
    console.print(f"Wrote {config_path}")
    console.print(f"Wrote {manifest_path}")
    if from_path is not None:
        console.print(f"Wrote {lock_path}")
    console.print("\nNext commands:")
    console.print("glyph inspect AGENTS.md --show-unmapped")
    console.print("glyph stats AGENTS.md AGENTS.glp")
    console.print("glyph check AGENTS.md AGENTS.glp --min-coverage 95 --min-operational-coverage 80")


@app.command(help="Compile one or more Markdown instruction files into a .glp manifest.")
def compile(
    inputs: Optional[list[Path]] = typer.Argument(None, help="Input instruction files."),
    output: Optional[Path] = typer.Option(None, "-o", "--output", help="Output .glp path."),
    adapter: Optional[str] = typer.Option(None, "--adapter", help="Override input adapter."),
    profile: Optional[CompressionProfile] = typer.Option(None, "--profile", help="Compression profile."),
    report: Optional[Path] = typer.Option(None, "--report", help="Write compile report as .json or .md."),
    strict: bool = typer.Option(False, "--strict", help="Fail before writing when retention, safety, or conflict gates fail."),
    min_operational_coverage: Optional[float] = typer.Option(None, "--min-operational-coverage", help="Alias for --min-structured-coverage."),
    min_structured_coverage: Optional[float] = typer.Option(None, "--min-structured-coverage", help="Strict-mode minimum canonical-or-policy coverage."),
    min_retained_coverage: Optional[float] = typer.Option(None, "--min-retained-coverage", help="Strict-mode minimum canonical, policy, or preserved retention."),
    min_agent_instruction_coverage: Optional[float] = typer.Option(None, "--min-agent-instruction-coverage", help="Strict-mode minimum coverage for general agent instructions only."),
    max_unmapped: Optional[int] = typer.Option(None, "--max-unmapped", help="Strict-mode maximum genuinely dropped operational candidates."),
    max_high_risk_unmapped: Optional[int] = typer.Option(None, "--max-high-risk-unmapped", help="Strict-mode maximum genuinely dropped high-risk candidates."),
    max_preserved: Optional[int] = typer.Option(None, "--max-preserved", help="Strict-mode maximum preserved directives."),
    max_high_risk_preserved: Optional[int] = typer.Option(None, "--max-high-risk-preserved", help="Strict-mode maximum high-risk preserved directives (default: 0)."),
    require_structured: bool = typer.Option(False, "--require-structured", help="Reject every preserved fallback directive."),
    rules: Optional[Path] = typer.Option(None, "--rules", help="Custom glyph.rules.yml file."),
) -> None:
    try:
        config = _load_config_or_exit()
        resolved_inputs = inputs or ([Path(config.paths.source)] if config and config.paths.source else None)
        resolved_output = output or (Path(config.paths.manifest) if config and config.paths.manifest else None)
        if not resolved_inputs:
            _fail("No input files provided.\nPass files explicitly, or set [paths].source in .glyph/config.toml.")
        if resolved_output is None:
            _fail("No output path provided.\nUse -o AGENTS.glp, or set [paths].manifest in .glyph/config.toml.")
        profile_value = profile or (config.profile() if config else None) or CompressionProfile.compact
        rules_path = _config_rules(rules, config)
        strict_min_structured = min_structured_coverage if min_structured_coverage is not None else min_operational_coverage
        if strict_min_structured is None and config and config.min_operational_coverage is not None:
            strict_min_structured = config.min_operational_coverage
        strict_min_retained = 100.0 if min_retained_coverage is None else min_retained_coverage
        strict_max_unmapped = max_unmapped
        if strict_max_unmapped is None and config and config.max_unmapped is not None:
            strict_max_unmapped = config.max_unmapped
        strict_max_high_risk = 0 if max_high_risk_unmapped is None else max_high_risk_unmapped
        strict_max_high_risk_preserved = 0 if max_high_risk_preserved is None else max_high_risk_preserved
        _ensure_inputs_exist(resolved_inputs)
        _ensure_parent_exists(resolved_output)
        if report:
            _ensure_parent_exists(report)
        validate_adapter(adapter)
        manifest, extraction = analyze_files(resolved_inputs, adapter, rules_path)
        if report:
            write_report(report, extraction)
        if strict:
            errors = []
            if strict_min_structured is not None and extraction.structured_coverage < strict_min_structured:
                errors.append(f"structured coverage {extraction.structured_coverage:.1f}% is below {strict_min_structured:.1f}%")
            if extraction.retained_coverage < strict_min_retained:
                errors.append(f"retained coverage {extraction.retained_coverage:.1f}% is below {strict_min_retained:.1f}%")
            if min_agent_instruction_coverage is not None and extraction.agent_instruction_coverage < min_agent_instruction_coverage:
                errors.append(f"agent instruction coverage {extraction.agent_instruction_coverage:.1f}% is below {min_agent_instruction_coverage:.1f}%")
            if strict_max_unmapped is not None and extraction.dropped_count > strict_max_unmapped:
                errors.append(f"dropped operational candidates {extraction.dropped_count} exceeds {strict_max_unmapped}")
            high_risk_dropped = sum(1 for candidate in extraction.ledger.dropped_candidates if candidate.risk == "high")
            if high_risk_dropped > strict_max_high_risk:
                errors.append(f"high-risk dropped candidates {high_risk_dropped} exceeds {strict_max_high_risk}")
            if max_preserved is not None and extraction.preserved_count > max_preserved:
                errors.append(f"preserved directives {extraction.preserved_count} exceeds {max_preserved}")
            if extraction.high_risk_preserved_count > strict_max_high_risk_preserved:
                errors.append(f"high-risk preserved directives {extraction.high_risk_preserved_count} exceeds {strict_max_high_risk_preserved} (legacy high-risk unmapped candidates are preserved, not dropped)")
            if require_structured and extraction.preserved_count:
                errors.append(f"structured output required but {extraction.preserved_count} directives were preserved")
            if extraction.conflicts:
                errors.append("conflicts detected: " + ", ".join(conflict.id for conflict in extraction.conflicts))
            if errors:
                for error in errors:
                    console.print(f"FAIL: {error}")
                console.print("Fix the source instructions, lower explicit thresholds, or review unmapped candidates with `glyph inspect --show-unmapped`.")
                raise typer.Exit(1)
        resolved_output.write_text(render_glp(manifest, profile_value), encoding="utf-8")
        console.print(f"Wrote {resolved_output}")
    except Exception as exc:
        if isinstance(exc, typer.Exit):
            raise
        _fail(str(exc))


@app.command(help="Render a .glp manifest back to Markdown for compatibility.")
def render(input: Path, output: Path = typer.Option(..., "-o", "--output", help="Output Markdown path."), rules: Optional[Path] = typer.Option(None, "--rules", help="Custom glyph.rules.yml file.")) -> None:
    config = _load_config_or_exit()
    rules_path = _config_rules(rules, config)
    _ensure_parent_exists(output)
    try:
        manifest = _parse_manifest(input)
        output.write_text(render_markdown(manifest, extra_rules=load_custom_rules(rules_path)), encoding="utf-8")
        console.print(f"Wrote {output}")
    except Exception as exc:
        if isinstance(exc, typer.Exit):
            raise
        _fail(str(exc))


@app.command(help="Compare token usage between Markdown and .glp files.")
def stats(markdown: Path, glp: Path) -> None:
    md_text = _read_text(markdown, "Markdown")
    glp_text = _read_text(glp, ".glp")
    md_tokens, tokenizer = count_tokens(md_text)
    glp_tokens, _ = count_tokens(glp_text)
    saved = md_tokens - glp_tokens
    reduction = 0 if md_tokens == 0 else (1 - glp_tokens / md_tokens) * 100
    console.print("Glyph token report\n")
    console.print(f"Input: {markdown}")
    console.print(f"Glyph: {glp}")
    console.print(f"Tokenizer: {tokenizer}\n")
    console.print(f"Markdown tokens: {md_tokens}")
    console.print(f"GLP tokens:      {glp_tokens}")
    console.print(f"Saved tokens:    {saved}")
    console.print(f"Reduction:       {reduction:.1f}%")


def verify_cmd(markdown: Path, glp: Path, rules: Optional[Path] = typer.Option(None, "--rules", help="Custom glyph.rules.yml file.")) -> None:
    config = _load_config_or_exit()
    rules_path = _config_rules(rules, config)
    manifest = _parse_manifest(glp)
    markdown_text = _read_text(markdown, "Markdown")
    report = verify(markdown_text, manifest, rules_path, source=str(markdown))
    console.print("Post-hardening coverage report\n")
    console.print(f"Detected semantic units: {len(report.detected_semantic_units)}")
    console.print(f"Encoded semantic units:  {len(report.encoded_semantic_units)}")
    console.print(f"Missing semantic units:  {len(report.missing_semantic_units)}")
    console.print(f"Semantic coverage (compatibility): {report.coverage:.1f}%")
    console.print(f"Structured coverage:     {report.structured_coverage:.1f}%")
    console.print(f"Retained coverage:       {report.retained_coverage:.1f}%")
    console.print(f"Safety retention:        {report.safety_retention:.1f}%")
    console.print(f"Preserved directives:    {report.preserved_count}")
    console.print(f"High-risk preserved:     {report.high_risk_preserved_count}")
    console.print(f"Dropped candidates:      {report.dropped_count}")
    console.print(f"Legacy high-risk unmapped: {report.high_risk_unmapped_count}")
    if report.missing_semantic_units:
        console.print("Missing: " + ", ".join(report.missing_semantic_units))


app.command("verify", help="Verify semantic coverage between Markdown and a .glp manifest.")(verify_cmd)


@app.command(help="Run benchmark cases and write benchmark-report.json and benchmark-report.md.")
def benchmark(root: Path) -> None:
    if not root.exists():
        _fail(f"{root} does not exist.\nPass a benchmark directory such as benchmarks/.")
    result = run_benchmark(root)
    table = Table(title="Glyph benchmark")
    for column in ["case", "source", "md", "readable", "compact", "ultra", "best reduction", "structured", "retained", "safety", "preserved", "high-risk preserved", "dropped", "conflicts", "semantic (diag)", "high-risk unmapped (diag)"]:
        table.add_column(column)
    for case in result["cases"]:  # type: ignore[index]
        table.add_row(case["case"], case["source"], str(case["markdown_tokens"]), str(case["readable_tokens"]), str(case["compact_tokens"]), str(case["ultra_tokens"]), f"{case['best_reduction'] * 100:.1f}%", f"{case['structured_coverage'] * 100:.1f}%", f"{case['retained_coverage'] * 100:.1f}%", f"{case['safety_retention'] * 100:.1f}%", str(case["preserved_count"]), str(case["high_risk_preserved_count"]), str(case["dropped_count"]), str(case["conflict_count"]), f"{case['semantic_coverage']:.1f}%", str(case.get("high_risk_unmapped_count", 0)))
    console.print(table)
    console.print(f"Average best reduction:      {result['average_best_reduction'] * 100:.1f}%")
    console.print(f"Average structured coverage:  {result.get('average_structured_coverage', 0) * 100:.1f}%")
    console.print(f"Average retained coverage:    {result.get('average_retained_coverage', 0) * 100:.1f}%")
    console.print(f"Average safety retention:     {result.get('average_safety_retention', 0) * 100:.1f}%")
    console.print(f"Preserved directives:         {result.get('preserved_count', 0)}")
    console.print(f"High-risk preserved:          {result.get('high_risk_preserved_count', 0)}")
    console.print(f"Dropped candidates:            {result.get('dropped_count', 0)}")
    console.print(f"Compatibility semantic coverage: {result['average_coverage'] * 100:.1f}%")
    console.print(f"Compatibility high-risk unmapped: {result.get('high_risk_unmapped_count', 0)}")


@app.command("benchmark-real", help="Benchmark arbitrary repositories without modifying files unless --write is passed.")
def benchmark_real(root: Path, patterns: Optional[str] = typer.Option(None, "--patterns", help="Comma-separated glob patterns."), write: bool = typer.Option(False, "--write", help="Write .glp files next to sources.")) -> None:
    if not root.exists():
        _fail(f"{root} does not exist.\nPass an existing repository path.")
    parsed = [p.strip() for p in patterns.split(",")] if patterns else None
    result = benchmark_real_run(root, parsed, write)
    console.print(f"Files discovered: {result['files_discovered']}")
    console.print(f"Files compiled:   {result['files_compiled']}")
    console.print(f"Average reduction:             {result['average_reduction'] * 100:.1f}%")
    console.print(f"Average structured coverage:   {result.get('average_structured_coverage', 0) * 100:.1f}%")
    console.print(f"Average retained coverage:     {result.get('average_retained_coverage', 0) * 100:.1f}%")
    console.print(f"Average safety retention:      {result.get('average_safety_retention', 0) * 100:.1f}%")
    console.print(f"Preserved directives:          {result.get('preserved_count', 0)}")
    console.print(f"High-risk preserved:           {result.get('high_risk_preserved_count', 0)}")
    console.print(f"Dropped candidates:            {result.get('dropped_count', 0)}")
    console.print(f"Compatibility semantic coverage: {result['average_coverage'] * 100:.1f}%")
    console.print(f"Compatibility high-risk unmapped: {result.get('high_risk_unmapped_count', 0)}")
    if result["files"]:  # type: ignore[index]
        table = Table(title="Real-world benchmark")
        for column in ["file", "md tokens", "glp tokens", "reduction", "structured", "retained", "safety", "preserved", "high-risk preserved", "dropped", "semantic (diag)", "high-risk unmapped (diag)"]:
            table.add_column(column)
        for row in result["files"]:  # type: ignore[index]
            table.add_row(row["file"], str(row["markdown_tokens"]), str(row["glp_tokens"]), f"{row['reduction'] * 100:.1f}%", f"{row['structured_coverage'] * 100:.1f}%", f"{row['retained_coverage'] * 100:.1f}%", f"{row['safety_retention'] * 100:.1f}%", str(row["preserved_count"]), str(row["high_risk_preserved_count"]), str(row["dropped_count"]), f"{row['coverage'] * 100:.1f}%", str(row["high_risk_unmapped_count"]))
        console.print(table)
    poor = [row for row in result["files"] if row["structured_coverage"] < 0.8 or row["high_risk_preserved_count"] > 0 or row["dropped_count"] > 0]  # type: ignore[index]
    if poor:
        console.print("Files needing review:")
        for row in poor:
            console.print(f"- {row['file']}: structured={row['structured_coverage'] * 100:.1f}% retained={row['retained_coverage'] * 100:.1f}% safety={row['safety_retention'] * 100:.1f}% preserved={row['preserved_count']} high-risk-preserved={row['high_risk_preserved_count']} dropped={row['dropped_count']}")


@app.command(help="Lint a Markdown instruction file for instruction smells.")
def lint(input: Path, rules: Optional[Path] = typer.Option(None, "--rules", help="Custom glyph.rules.yml file.")) -> None:
    config = _load_config_or_exit()
    rules_path = _config_rules(rules, config)
    try:
        warnings = lint_text(_read_text(input, "Markdown"), str(input), rules_path)
    except Exception as exc:
        if isinstance(exc, typer.Exit):
            raise
        _fail(str(exc))
    if not warnings:
        console.print("No instruction smells detected.")
        return
    console.print("\n".join(warning_lines(warnings)).rstrip(), markup=False)


@app.command(help="Compare operational meaning between instruction files or .glp manifests.")
def diff(old: Path, new: Path, rules: Optional[Path] = typer.Option(None, "--rules", help="Custom glyph.rules.yml file.")) -> None:
    config = _load_config_or_exit()
    rules_path = _config_rules(rules, config)
    try:
        result = semantic_diff(load_any(old, rules_path), load_any(new, rules_path))
    except Exception as exc:
        _fail(str(exc))
    console.print("Glyph semantic diff\n")
    if result["added"]:
        console.print("Added:")
        for item in result["added"]:
            console.print(f"+ {item}")
    if result["removed"]:
        console.print("\nRemoved:")
        for item in result["removed"]:
            console.print(f"- {item}")
    if result["changed_commands"]:
        console.print("\nChanged commands:")
        for key, values in result["changed_commands"].items():
            console.print(f"~ {key}: {values[0]!r} -> {values[1]!r}")
    for label, key in [("Added policies", "added_policies"), ("Removed policies", "removed_policies"), ("Added preserved directives", "added_preserved"), ("Removed preserved directives", "removed_preserved")]:
        if result.get(key):
            console.print(f"\n{label}:")
            for item in result[key]:
                console.print(f"~ {item}")
    if result["risks"]:
        console.print("\nRisk:")
        for risk in result["risks"]:
            console.print(f"! {risk}")


@app.command(help="Create a semantic lockfile for instruction files.")
def lock(
    inputs: list[Path],
    output: Path = typer.Option(..., "-o", "--output", help="Output lockfile path."),
    rules: Optional[Path] = typer.Option(None, "--rules", help="Custom glyph.rules.yml file, including exact 0.2 policies."),
) -> None:
    _ensure_inputs_exist(inputs)
    _ensure_parent_exists(output)
    write_lock(inputs, output, rules)
    console.print(f"Wrote {output}")


@app.command(help="Validate .glp coverage, reduction, freshness, or a lockfile for CI.")
def check(
    markdown: Optional[Path] = typer.Argument(None, help="Markdown instruction file."),
    glp: Optional[Path] = typer.Argument(None, help=".glp manifest file."),
    min_coverage: Optional[float] = typer.Option(None, "--min-coverage"),
    min_operational_coverage: Optional[float] = typer.Option(None, "--min-operational-coverage", help="Alias for --min-structured-coverage."),
    min_structured_coverage: Optional[float] = typer.Option(None, "--min-structured-coverage"),
    min_retained_coverage: Optional[float] = typer.Option(None, "--min-retained-coverage"),
    min_reduction: Optional[float] = typer.Option(None, "--min-reduction"),
    max_unmapped: Optional[int] = typer.Option(None, "--max-unmapped"),
    max_high_risk_unmapped: Optional[int] = typer.Option(None, "--max-high-risk-unmapped"),
    max_preserved: Optional[int] = typer.Option(None, "--max-preserved"),
    max_high_risk_preserved: Optional[int] = typer.Option(None, "--max-high-risk-preserved"),
    require_structured: bool = typer.Option(False, "--require-structured"),
    fail_on_conflicts: bool = typer.Option(False, "--fail-on-conflicts"),
    lock_file: Optional[Path] = typer.Option(None, "--lock"),
    rules: Optional[Path] = typer.Option(None, "--rules", help="Custom glyph.rules.yml file."),
) -> None:
    config = _load_config_or_exit()
    rules_path = _config_rules(rules, config)
    resolved_markdown = markdown or (Path(config.paths.source) if config and config.paths.source else None)
    resolved_glp = glp or (Path(config.paths.manifest) if config and config.paths.manifest else None)
    resolved_min_coverage = min_coverage if min_coverage is not None else (config.min_semantic_coverage if config and config.min_semantic_coverage is not None else 95.0)
    resolved_min_operational = min_structured_coverage if min_structured_coverage is not None else (min_operational_coverage if min_operational_coverage is not None else (config.min_operational_coverage if config else None))
    resolved_min_reduction = min_reduction if min_reduction is not None else (config.min_reduction if config and config.min_reduction is not None else 30.0)
    resolved_max_unmapped = max_unmapped if max_unmapped is not None else (config.max_unmapped if config else None)
    try:
        if lock_file:
            if not lock_file.exists():
                _fail(f"{lock_file} does not exist.\nCreate it with `glyph lock ... -o {lock_file}`.")
            ok, errors = check_lock(lock_file)
        elif resolved_markdown and resolved_glp:
            _ensure_inputs_exist([resolved_markdown, resolved_glp])
            ok, errors = check_pair(
                resolved_markdown,
                resolved_glp,
                min_coverage=resolved_min_coverage,
                min_reduction=resolved_min_reduction,
                fail_on_conflicts=fail_on_conflicts,
                min_operational_coverage=resolved_min_operational,
                max_unmapped=resolved_max_unmapped,
                max_high_risk_unmapped=max_high_risk_unmapped,
                rules_path=rules_path,
                min_retained_coverage=min_retained_coverage,
                min_structured_coverage=resolved_min_operational,
                max_preserved=max_preserved,
                max_high_risk_preserved=max_high_risk_preserved,
                require_structured=require_structured,
            )
        else:
            _fail("Provide MARKDOWN GLP or --lock glyph.lock.json.\nAlternatively set [paths].source and [paths].manifest in .glyph/config.toml.")
    except Exception as exc:
        if isinstance(exc, typer.Exit):
            raise
        _fail(str(exc))
    if not ok:
        for error in errors:
            console.print(f"FAIL: {error}")
        console.print("Fix the manifest with `glyph compile`, or adjust explicit thresholds if they are intentionally stricter than this project.")
        raise typer.Exit(1)
    console.print("Glyph check passed.")


@app.command(help="Emit Markdown fallback files for existing agent tools.")
def emit(input: Path, target: str = typer.Option(..., "--target", help=f"One of: {', '.join(TARGET_TITLES)}"), output: Path = typer.Option(..., "-o", "--output"), rules: Optional[Path] = typer.Option(None, "--rules", help="Custom glyph.rules.yml file.")) -> None:
    config = _load_config_or_exit()
    rules_path = _config_rules(rules, config)
    _ensure_parent_exists(output)
    try:
        manifest = _parse_manifest(input)
        output.write_text(emit_markdown(manifest, target, load_custom_rules(rules_path)), encoding="utf-8")
        console.print(f"Wrote {output}")
    except ValueError as exc:
        _fail(f"{exc}\nUse --target with one of: {', '.join(sorted(TARGET_TITLES))}.")
    except Exception as exc:
        if isinstance(exc, typer.Exit):
            raise
        _fail(str(exc))


@app.command(help="Select a deterministic task-relevant subset of instructions.")
def select(input: Path, task: str = typer.Option(..., "--task"), format: str = typer.Option("glp", "--format"), max_tokens: Optional[int] = typer.Option(None, "--max-tokens")) -> None:
    manifest = _parse_manifest(input)
    try:
        console.print(select_output(manifest, task, format, max_tokens), markup=False)
    except ValueError as exc:
        _fail(str(exc))


@app.command(help="Score an instruction file and explain quality dimensions.")
def score(input: Path, badge: bool = typer.Option(False, "--badge", help="Output a Markdown badge only."), rules: Optional[Path] = typer.Option(None, "--rules", help="Custom glyph.rules.yml file.")) -> None:
    config = _load_config_or_exit()
    rules_path = _config_rules(rules, config)
    try:
        result = score_path(input, rules_path)
    except Exception as exc:
        _fail(str(exc))
    if badge:
        console.print(badge_line(int(result["overall"])), markup=False)
        return
    console.print("Glyph score\n")
    console.print(f"File: {input}\n")
    labels = [
        ("Token cost", "token_cost"),
        ("Compression potential", "compression_potential"),
        ("Semantic clarity", "semantic_clarity"),
        ("Testing coverage", "testing_coverage"),
        ("Safety coverage", "safety_coverage"),
        ("Reporting coverage", "reporting_coverage"),
        ("Conflict risk", "conflict_risk"),
        ("Context bloat", "context_bloat"),
        ("Overall", "overall"),
    ]
    for label, key in labels:
        value = result[key]
        suffix = "/100" if isinstance(value, int) and key not in {"token_cost"} else ""
        console.print(f"{label + ':':24} {value}{suffix}")


@app.command(help="Start the local Glyph MCP server over stdio.")
def mcp() -> None:
    try:
        from .mcp_server import run_mcp_server

        run_mcp_server()
    except RuntimeError as exc:
        console.print(str(exc), markup=False)
        raise typer.Exit(1) from exc


@app.command(help="Inspect structured extraction, candidates, matches, commands, unmapped candidates, and conflicts.")
def inspect(input: Path, show_unmapped: bool = typer.Option(False, "--show-unmapped"), format: str = typer.Option("text", "--format"), rules: Optional[Path] = typer.Option(None, "--rules")) -> None:
    config = _load_config_or_exit()
    rules_path = _config_rules(rules, config)
    _ensure_inputs_exist([input])
    try:
        _, extraction = analyze_files([input], rules_path=rules_path)
    except Exception as exc:
        _fail(str(exc))
    if format == "json":
        typer.echo(report_to_json(extraction), nl=False)
        return
    console.print("Glyph inspect\n")
    console.print(f"Source: {input}", markup=False)
    console.print(f"Adapter: {extraction.adapters.get(str(input), 'generic_markdown')}\n", markup=False)
    console.print("Summary")
    console.print(f"Semantic coverage:             {extraction.semantic_coverage:.1f}%")
    console.print(f"Canonical candidate coverage:  {extraction.canonical_candidate_coverage:.1f}%")
    console.print(f"Structured coverage:           {extraction.structured_coverage:.1f}%")
    console.print(f"Retained coverage:             {extraction.retained_coverage:.1f}%")
    console.print(f"Safety retention:              {extraction.safety_retention:.1f}%")
    console.print(f"Agent instruction coverage:    {extraction.agent_instruction_coverage:.1f}%")
    console.print(f"Repo-specific coverage:        {extraction.repo_specific_coverage:.1f}%")
    console.print(f"Spec classification rate:      {extraction.spec_classification_rate:.1f}%")
    console.print(f"Operational coverage:          {extraction.operational_coverage:.1f}%")
    console.print(f"Preserved directives:          {extraction.preserved_count}")
    console.print(f"High-risk preserved:           {extraction.high_risk_preserved_count}")
    console.print(f"Dropped directives:            {extraction.dropped_count}")
    console.print(f"Conflicts:                     {len(extraction.conflicts)}")
    console.print("\nCandidate breakdown")
    console.print(f"Mapped agent instructions:     {len({(m.candidate.source, m.candidate.line, m.candidate.text) for m in extraction.matches})}")
    console.print(f"Repo-specific instructions:    {len(extraction.ledger.repo_specific_candidates)}")
    console.print(f"Product/spec requirements:     {len(extraction.ledger.product_requirements)}")
    console.print(f"Implementation requirements:   {len(extraction.ledger.implementation_requirements)}")
    console.print(f"API/CLI contracts:             {len(extraction.ledger.api_contracts)}")
    console.print(f"Conditional instructions:      {len(extraction.ledger.conditional_instructions)}")
    console.print(f"Example/reference blocks:      {len(extraction.ledger.examples_or_references)}")
    console.print(f"Non-operational context:       {len(extraction.ledger.non_operational_context)}")
    console.print(f"High-risk unmapped:            {len(extraction.ledger.high_risk_unmapped)}")
    for doc in extraction.documents:
        console.print("\nSections detected:")
        for section in doc.sections:
            console.print(f"- {'  ' * (section.level - 1)}{section.title} (line {section.line_start})", markup=False)
    if extraction.commands_detected:
        console.print("\nCommands detected:")
        for label, command in extraction.commands_detected.items():
            console.print(f"- cmd.{label}: {command}", markup=False)
        for command in extraction.command_candidates:
            console.print(f"  source: {command.source}:{command.line} confidence={command.confidence:.2f} signals={', '.join(command.signals)}", markup=False)
    if extraction.matches:
        console.print("\nSemantic matches:")
        for match in extraction.matches:
            console.print(f"[{match.candidate.section or 'root'}] {match.candidate.source}:{match.candidate.line}", markup=False)
            console.print(f'✓ "{match.candidate.text}"', markup=False)
            console.print(f"  → {match.semantic_unit}")
            console.print(f"  confidence: {match.confidence:.2f}")
            console.print(f"  intent: {match.candidate.intent} confidence={match.candidate.intent_confidence:.2f}")
            console.print(f"  signals: {', '.join(match.signals)}", markup=False)
    classified_groups = [
        ("Classified product/spec/API requirements", "◇", extraction.ledger.product_requirements + extraction.ledger.implementation_requirements + extraction.ledger.api_contracts),
        ("Repository-specific/custom-rule candidates", "?", extraction.ledger.repo_specific_candidates),
        ("Conditional/needs-attention instructions", "△", extraction.ledger.conditional_instructions),
        ("High-risk unmapped", "!", extraction.ledger.high_risk_unmapped),
    ]
    for title, marker, candidates in classified_groups:
        if candidates:
            console.print(f"\n{title}:")
            for candidate in candidates[:20]:
                console.print(f"[{candidate.section or 'root'}] {candidate.source}:{candidate.line}", markup=False)
                console.print(f'{marker} "{candidate.text}"', markup=False)
                if candidate.semantic_unit:
                    console.print(f"  → {candidate.semantic_unit}")
                else:
                    console.print(f"  → {candidate.intent}")
                console.print(f"  confidence: {candidate.intent_confidence:.2f}")
                if candidate.reasoning_summary:
                    console.print(f"  note: {candidate.reasoning_summary}", markup=False)
    if show_unmapped and extraction.unmapped_operational_candidates:
        console.print("\nUnmapped operational candidates:")
        for candidate in extraction.unmapped_operational_candidates:
            console.print(f"[{candidate.section or 'root'}] {candidate.source}:{candidate.line}", markup=False)
            marker = "!" if candidate.intent == "high_risk_unmapped" else "△" if candidate.intent == "conditional_instruction" else "?"
            console.print(f'{marker} "{candidate.text}"', markup=False)
            console.print(f"  intent: {candidate.intent} confidence={candidate.intent_confidence:.2f}")
            console.print(f"  operational confidence: {candidate.operational_confidence:.2f}")
            console.print(f"  signals: {', '.join(candidate.signals or candidate.reasons)}", markup=False)
    if extraction.conflicts:
        console.print("\nConflicts:")
        for conflict in extraction.conflicts:
            console.print(f"- {conflict.id}: {conflict.suggested_fix}")


@rules_app.command("suggest", help="Suggest custom rules from unmapped operational candidates.")
def rules_suggest(input: Path, format: str = typer.Option("text", "--format")) -> None:
    _, extraction = analyze_files([input])
    suggestions = suggest_rules(extraction.unmapped_operational_candidates)
    if format == "yaml":
        lines = ["rules:"]
        for suggestion in suggestions:
            lines += [f"  - id: {suggestion['id']}", f"    category: {suggestion['category']}", "    patterns:"]
            lines += [f"      - \"{pattern}\"" for pattern in suggestion["patterns"]]
            if suggestion.get("positive_terms"):
                lines.append("    positive_terms:")
                lines += [f"      - \"{term}\"" for term in suggestion["positive_terms"]]
            if suggestion.get("section_hints"):
                lines.append("    section_hints:")
                lines += [f"      - \"{hint}\"" for hint in suggestion["section_hints"]]
            if suggestion.get("modal_hints"):
                lines.append("    modal_hints:")
                lines += [f"      - \"{hint}\"" for hint in suggestion["modal_hints"]]
            lines.append(f"    rendered: \"{suggestion['rendered']}\"")
            lines.append(f"    severity: {suggestion.get('severity', 'medium')}")
            lines.append(f"    safety_critical: {str(suggestion.get('safety_critical', False)).lower()}")
            lines.append(f"    always_select: {str(suggestion.get('always_select', False)).lower()}")
        console.print("\n".join(lines), markup=False)
        return
    console.print("Potential custom rules\n")
    for idx, suggestion in enumerate(suggestions, 1):
        console.print(f"{idx}. {suggestion['id']}")
        console.print(f"   category: {suggestion['category']}")
        console.print("   matched phrases:")
        for pattern in suggestion["patterns"]:
            console.print(f"   - {pattern}")


if __name__ == "__main__":
    app()
