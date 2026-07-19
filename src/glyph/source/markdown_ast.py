from __future__ import annotations

import re

from .adapters import detect_adapter
from .document_ir import BlockIR, DocumentIR, SectionIR


def _current_section(stack: list[tuple[int, str]]) -> tuple[str | None, list[str]]:
    if not stack:
        return None, []
    return stack[-1][1], [title for _, title in stack]


def _document_role(text: str, adapter: str, source: str) -> tuple[str, str]:
    """Classify the document context before looking for reusable directives.

    This deliberately uses only filename/adapter and local heading language.  A
    README may contain an operational development section, so it remains mixed
    rather than being treated as agent guidance wholesale.
    """
    lowered = text.lower()
    if adapter in {"agents_md", "claude_md", "copilot_instructions", "cursor_rules"}:
        return "agent_instructions", "agent"
    normalized_source = source.lower().replace("\\", "/")
    if "/docs/plans/" in f"/{normalized_source.lstrip('/')}":
        return "implementation_spec", "developer"
    if adapter == "contributing":
        return "contributor_guide", "contributor"
    operational_headings = ("agent instructions", "instructions", "contributing", "development workflow", "working on", "pull request")
    product_headings = ("api reference", "architecture", "overview", "product", "concepts")
    has_operational = any(f"# {heading}" in lowered or f"## {heading}" in lowered for heading in operational_headings)
    has_product = any(f"# {heading}" in lowered or f"## {heading}" in lowered for heading in product_headings)
    if has_operational and not has_product:
        return "contributor_guide", "developer"
    if has_product and not has_operational:
        return "product_docs", "developer"
    return "mixed", "mixed"


def parse_markdown(text: str, source: str = "<memory>", adapter: str | None = None) -> DocumentIR:
    lines = text.splitlines()
    adapter_name = adapter or detect_adapter(source)
    role, audience = _document_role(text, adapter_name, source)
    doc = DocumentIR(source=source, adapter=adapter_name, role=role, audience=audience)
    stack: list[tuple[int, str]] = []
    i = 0
    while i < len(lines):
        raw = lines[i]
        line = raw.rstrip()
        stripped = line.strip()
        line_no = i + 1
        if not stripped:
            i += 1
            continue
        if i == 0 and stripped == "---":
            start = line_no
            i += 1
            while i < len(lines) and lines[i].strip() != "---":
                i += 1
            if i < len(lines):
                i += 1
            doc.blocks.append(BlockIR(type="horizontal_rule", text="frontmatter", line_start=start, line_end=i, source=source, section=None, parent_headings=[]))
            continue
        heading = re.match(r"^(#{1,6})\s+(.+?)\s*$", stripped)
        if heading:
            level = len(heading.group(1))
            title = heading.group(2).strip()
            stack = [(lvl, txt) for lvl, txt in stack if lvl < level]
            parents = [txt for _, txt in stack]
            stack.append((level, title))
            doc.sections.append(SectionIR(title=title, level=level, line_start=line_no, parent_titles=parents))
            doc.blocks.append(BlockIR(type="heading", text=title, line_start=line_no, line_end=line_no, source=source, section=title, heading_level=level, parent_headings=parents + [title]))
            i += 1
            continue
        section, parents = _current_section(stack)
        fence = re.match(r"^```(\w+)?\s*$", stripped)
        if fence:
            lang = fence.group(1)
            start = line_no
            body: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                body.append(lines[i])
                i += 1
            end = i + 1 if i < len(lines) else len(lines)
            doc.blocks.append(BlockIR(type="fenced_code_block", text="\n".join(body).strip(), line_start=start, line_end=end, source=source, section=section, code_language=lang, parent_headings=parents))
            i += 1
            continue
        if re.match(r"^(-{3,}|\*{3,}|_{3,})$", stripped):
            doc.blocks.append(BlockIR(type="horizontal_rule", text=stripped, line_start=line_no, line_end=line_no, source=source, section=section, parent_headings=parents))
            i += 1
            continue
        if stripped.startswith(">"):
            start = line_no
            body = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                body.append(lines[i].strip().lstrip(">").strip())
                i += 1
            doc.blocks.append(BlockIR(type="blockquote", text=" ".join(body), line_start=start, line_end=i, source=source, section=section, parent_headings=parents))
            continue
        if "|" in stripped and i + 1 < len(lines) and re.search(r"\|\s*:?-{3,}:?\s*\|", lines[i + 1]):
            start = line_no
            table_lines = [stripped, lines[i + 1].strip()]
            i += 2
            while i < len(lines) and "|" in lines[i].strip():
                table_lines.append(lines[i].strip())
                i += 1
            rows = [[cell.strip().strip("`") for cell in row.strip("|").split("|")] for row in table_lines if not re.search(r"^\|?\s*:?-{3,}", row)]
            doc.blocks.append(BlockIR(type="table", text="\n".join(table_lines), line_start=start, line_end=i, source=source, section=section, table_rows=rows, parent_headings=parents))
            continue
        list_match = re.match(r"^(\s*)([-*+]|\d+[.])\s+(.+)$", line)
        if list_match:
            start = line_no
            items: list[str] = []
            checklist = False
            numbered = bool(re.match(r"\d+[.]", list_match.group(2)))
            while i < len(lines):
                m = re.match(r"^(\s*)([-*+]|\d+[.])\s+(.+)$", lines[i])
                if not m:
                    break
                current_numbered = bool(re.match(r"\d+[.]", m.group(2)))
                item = m.group(3).strip()
                current_checklist = bool(re.match(r"^\[[ xX]\]\s+", item))
                if items and (current_numbered != numbered or current_checklist != checklist):
                    break
                if current_checklist:
                    checklist = True
                    item = re.sub(r"^\[[ xX]\]\s+", "", item)
                i += 1
                continuation: list[str] = []
                while i < len(lines):
                    continued = lines[i]
                    continued_stripped = continued.strip()
                    if not continued_stripped:
                        break
                    if re.match(r"^(\s*)([-*+]|\d+[.])\s+", continued):
                        break
                    if re.match(r"^(#{1,6})\s+|^```", continued_stripped) or continued_stripped.startswith(">"):
                        break
                    if continued_stripped.startswith("|"):
                        break
                    continuation.append(continued_stripped)
                    i += 1
                items.append(" ".join([item, *continuation]))
            block_type = "checklist" if checklist else "numbered_list" if numbered else "bullet_list"
            doc.blocks.append(BlockIR(type=block_type, text="\n".join(items), line_start=start, line_end=i, source=source, section=section, parent_headings=parents))
            continue
        start = line_no
        para = [stripped]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#{1,6})\s+", lines[i].strip()) and not re.match(r"^```", lines[i].strip()) and not re.match(r"^(\s*)([-*+]|\d+[.])\s+", lines[i]) and not lines[i].strip().startswith(">"):
            para.append(lines[i].strip())
            i += 1
        paragraph = " ".join(para)
        doc.blocks.append(BlockIR(type="paragraph", text=paragraph, line_start=start, line_end=i, source=source, section=section, parent_headings=parents))
        for match in re.finditer(r"`([^`\n]+)`", paragraph):
            doc.blocks.append(BlockIR(type="inline_code", text=match.group(1), line_start=start, line_end=i, source=source, section=section, parent_headings=parents))
    return doc
