from __future__ import annotations

from typing import Literal

from .services import (
    glyph_check_service,
    glyph_compile_service,
    glyph_inspect_service,
    glyph_lint_service,
    glyph_score_service,
    glyph_select_service,
    glyph_stats_service,
)

MCP_INSTALL_MESSAGE = 'MCP support is not installed.\nInstall it with: pip install "glyph-instructions[mcp]"'


def create_mcp_server():
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise RuntimeError(MCP_INSTALL_MESSAGE) from exc

    server = FastMCP("glyph")

    @server.tool()
    def glyph_compile(
        sources: list[str],
        output: str,
        profile: Literal["readable", "compact", "ultra"] = "compact",
        rules_file: str | None = None,
        strict: bool = False,
        min_operational_coverage: float | None = None,
        max_unmapped: int | None = None,
        report: str | None = None,
        min_structured_coverage: float | None = None,
        min_retained_coverage: float | None = None,
        max_preserved: int | None = None,
        max_high_risk_preserved: int | None = None,
        require_structured: bool = False,
    ) -> dict:
        """Compile Markdown instruction files into a .glp manifest."""
        return glyph_compile_service(sources, output, profile, rules_file, strict, min_operational_coverage, max_unmapped, report, min_structured_coverage, min_retained_coverage, max_preserved, max_high_risk_preserved, require_structured)

    @server.tool()
    def glyph_inspect(source: str, rules_file: str | None = None, show_unmapped: bool = False) -> dict:
        """Inspect mapped and unmapped operational instructions."""
        return glyph_inspect_service(source, rules_file, show_unmapped)

    @server.tool()
    def glyph_stats(markdown_path: str, glp_path: str) -> dict:
        """Compare token counts for Markdown and .glp files."""
        return glyph_stats_service(markdown_path, glp_path)

    @server.tool()
    def glyph_select(
        glp_path: str,
        task: str,
        format: Literal["glp", "markdown"] = "glp",
        max_tokens: int | None = None,
    ) -> dict:
        """Select a deterministic task-relevant subset of a .glp manifest."""
        return glyph_select_service(glp_path, task, format, max_tokens)

    @server.tool()
    def glyph_check(
        markdown_path: str,
        glp_path: str,
        min_coverage: float | None = None,
        min_operational_coverage: float | None = None,
        min_reduction: float | None = None,
        max_unmapped: int | None = None,
        max_high_risk_unmapped: int | None = None,
        fail_on_conflicts: bool = False,
        min_structured_coverage: float | None = None,
        min_retained_coverage: float | None = None,
        max_preserved: int | None = None,
        max_high_risk_preserved: int | None = None,
        require_structured: bool = False,
    ) -> dict:
        """Validate coverage, reduction, freshness, unmapped count, and conflicts."""
        return glyph_check_service(
            markdown_path,
            glp_path,
            min_coverage=min_coverage,
            min_operational_coverage=min_operational_coverage,
            min_reduction=min_reduction,
            max_unmapped=max_unmapped,
            max_high_risk_unmapped=max_high_risk_unmapped,
            fail_on_conflicts=fail_on_conflicts,
            min_structured_coverage=min_structured_coverage,
            min_retained_coverage=min_retained_coverage,
            max_preserved=max_preserved,
            max_high_risk_preserved=max_high_risk_preserved,
            require_structured=require_structured,
        )

    @server.tool()
    def glyph_lint(source: str, rules_file: str | None = None) -> dict:
        """Lint a Markdown instruction file for instruction smells."""
        return glyph_lint_service(source, rules_file)

    @server.tool()
    def glyph_score(source: str, rules_file: str | None = None) -> dict:
        """Score instruction quality with deterministic dimensions."""
        return glyph_score_service(source, rules_file)

    return server


def run_mcp_server() -> None:
    create_mcp_server().run()
