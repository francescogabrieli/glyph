# Glyph MCP Server

Glyph includes a local MCP server for MCP-compatible coding agents that need deterministic instruction analysis.

## What It Does

The server exposes Glyph as local tools for compiling, inspecting, checking, linting, scoring, and selecting `.glp` manifests. It reuses Glyph's Python service layer directly and does not shell out to the `glyph` CLI for each tool call.

## Installation

Base installs do not include MCP dependencies:

```bash
pip install "glyph-instructions @ git+https://github.com/francescogabrieli/glyph.git@v0.2.0"
```

Install MCP support with:

```bash
pip install "glyph-instructions[mcp] @ git+https://github.com/francescogabrieli/glyph.git@v0.2.0"
```

For development:

```bash
pip install -e ".[dev,mcp]"
```

If MCP support is missing, `glyph mcp` prints:

```txt
MCP support is not installed.
Install it with: pip install "glyph-instructions[mcp]"
```

## Run

```bash
glyph mcp
```

The server runs locally over MCP stdio.

## Tools

- `glyph_compile`: compile one or more Markdown instruction files into a `.glp` file.
- `glyph_inspect`: inspect mapped candidates, unmapped candidates, commands, conflicts, confidence, and signals.
- `glyph_stats`: compare token counts for Markdown and `.glp`.
- `glyph_select`: emit a deterministic task-relevant subset in `glp` or `markdown` format.
- `glyph_check`: validate coverage, reduction, unmapped count, conflicts, and stale output.
- `glyph_lint`: report instruction smells with severity and suggested fixes.
- `glyph_score`: score instruction quality dimensions.

## Example Tool Input

```json
{
  "sources": ["AGENTS.md", "README.md"],
  "output": "AGENTS.glp",
  "profile": "compact",
  "strict": true,
  "min_operational_coverage": 80,
  "max_unmapped": 5,
  "report": "glyph-report.json"
}
```

Example output:

```json
{
  "output_path": "AGENTS.glp",
  "profile": "compact",
  "semantic_coverage": 100.0,
  "operational_coverage": 95.0,
  "markdown_tokens": 1200,
  "glp_tokens": 280,
  "reduction": 0.766,
  "unmapped_count": 2,
  "conflict_count": 0,
  "warnings": []
}
```

## Claude Desktop Style Configuration

```json
{
  "mcpServers": {
    "glyph": {
      "command": "glyph",
      "args": ["mcp"]
    }
  }
}
```

## Security Model

Glyph MCP runs locally.

It reads and writes only paths provided by the user or client.

It does not call remote APIs.

It does not call LLMs.

It does not execute arbitrary shell commands as part of analysis.

`glyph_compile` may write `.glp` and report files. Other tools are read-only unless their behavior is explicitly changed in future documentation.

## Limitations

Glyph v0.1 does not include a hosted server, web app, VSCode plugin, LLM-based classifier, binary `.glp` format, or native Codex/Claude runtime integration. Those are future product surfaces, not part of the v0.1 release boundary.
