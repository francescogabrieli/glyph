# FAQ

## Does Glyph preserve every word in a Markdown file?

No. It preserves measured operational semantics when it can do so safely, and
it preserves unresolved operational directives verbatim for review.

## Does Glyph guarantee identical agent behavior?

No. It measures and compares deterministic instruction semantics. Agent runtime
behavior is affected by model, prompt, tools, repository state, and many other
variables.

## Does Glyph send my instructions to an AI service?

No. The library and benchmark are local and deterministic; they do not make
network or LLM calls.

## Is Glyph available on PyPI?

Not yet. Version 0.2.0 is distributed through its tagged GitHub Release, and
PyPI distribution is planned. The README and getting-started guide contain the
version-pinned installation command.

## Can I use Glyph with Claude Code, Codex, Copilot, or Cursor?

Yes, through Markdown compatibility emitters and existing instruction files.
Glyph does not claim native runtime support from those products.

## Why did Glyph preserve a directive instead of compiling it?

Because it could not establish one faithful deterministic interpretation. This
is safer than inventing a predicate, subject, scope, condition, or exception.

## Can I remove `preserve[]` to make CI green?

Only if you deliberately use `--require-structured`; otherwise preserved text is
the safe fallback. Do not remove it to inflate coverage. Clarify the source or
add a reviewed custom mapping.

## What is the difference between a custom rule and an exact custom policy?

A custom rule maps stable wording to a canonical semantic identifier. An exact
custom policy maps one normalized source sentence to a structured 0.2 policy
with explicit semantics.

## Why can a `.glp` file be larger than the original?

Small input files sometimes cost fewer tokens than format headers and semantic
metadata. Glyph reports negative reduction honestly; use it as evidence, not as
a failure of semantic retention.
