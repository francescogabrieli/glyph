from __future__ import annotations

import re


TOKENIZER_NAME = "fallback"
_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+|[^\w\s]", re.UNICODE)


def fallback_tokens(text: str) -> list[str]:
    return _TOKEN_RE.findall(text)


def count_tokens(text: str) -> tuple[int, str]:
    try:
        import tiktoken  # type: ignore

        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text)), "tiktoken:cl100k_base"
    except Exception:
        return len(fallback_tokens(text)), TOKENIZER_NAME
