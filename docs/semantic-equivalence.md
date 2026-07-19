# Semantic Equivalence

Glyph preserves measured operational semantics, not arbitrary prose.

Different sentences can encode the same operational unit:

```txt
Always run tests before saying the task is complete.
Before marking work done, run the test suite.
Do not say the task is complete unless tests pass.
```

All map to:

```txt
run_tests_before_done
```

This means Glyph can verify that important operational instructions remain encoded. It does not prove the original literary style, background context, or stochastic LLM behavior is identical.

Glyph also reports unmapped operational candidates. These are instructions that appear operational but do not match the current semantic registry or custom rules. They are reported with source file, line number, section, operational confidence, and reasons.
