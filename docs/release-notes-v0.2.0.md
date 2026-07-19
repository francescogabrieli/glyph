# Glyph 0.2.0 Release Notes

Date: 2026-07-19
Status: GitHub release; PyPI distribution planned

Glyph 0.2.0 is the first public-alpha candidate for a deterministic
Instructions-as-Code toolchain. It compiles operational guidance from Markdown
into a versioned semantic manifest, keeps uncertain meaning visible, and gives
CI concrete retention, safety, diff, selection, and lockfile checks.

## Highlights

- Explicit `glyph/0.2` manifests add structured policies without turning
  relations or conditions into opaque strings.
- The expression language stays deliberately small: atomic, all, any, and not.
- Governed subject, action/state/passive predicate, object, repository scope,
  condition, exception, and attachment remain distinct.
- Inseparable mixed-modality policies retain an explicit content-derived link
  across verification, diff, selection, locks, and Markdown emission.
- Deterministic clause extraction only structures a directive when one valid
  interpretation exists. Ambiguous or repository-specific input remains a
  preserved directive unless an exact custom policy resolves it.
- The package is organized by architectural responsibility and ships typing
  information, a local CLI, compatibility emitters, and an optional MCP extra.

## Compatibility

Glyph continues to parse and render `glyph/0.1` deterministically. Existing
0.1 policies upgrade losslessly into the internal 0.2 semantic view. Rendering
a 0.2 policy as 0.1 is rejected when doing so would lose meaning. Strict mode,
canonical ordering, and content-derived identity are unchanged in strength.

The Python module layout changed before the public alpha: legacy flat imports
such as `glyph.compiler` are removed. Integrations should import from the owning
package, for example `glyph.pipeline.compiler`, `glyph.formats.parser`, or
`glyph.governance.diff`.

## Validation evidence

The pinned ten-repository static corpus passes its fixed thresholds with 100%
retained coverage, 100% safety retention, zero dropped candidates, zero
high-risk preserved directives, and zero nondeterminism. Agent-instruction
coverage is 96.63% and structured operational coverage is 82.18%. Across all
124 supported files, 316 lower-risk directives remain preserved because they
are ambiguous or repository-specific. These numbers describe that exact pinned
input set; they are not a universal accuracy or behavioral-equivalence claim.

The synthetic benchmark reports 96.6% structured coverage, 100% retained and
safety coverage, zero high-risk preserved directives, and zero drops. Package
validation includes Python 3.10 through 3.14, Ruff, mypy, source and wheel
builds, a fresh-wheel smoke environment, CLI gates, and optional MCP startup.

## Known limits

- Glyph preserves measurable operational semantics, not arbitrary prose or
  guaranteed model behavior.
- Conservative preservation can make small files larger; negative per-file
  reductions are reported rather than hidden.
- Repository-specific ambiguity requires an exact custom policy instead of a
  broader heuristic.
- No LLM, hosted service, remote classifier, native agent runtime integration,
  or binary manifest format is included.
- The separately governed behavior matrix has not been run, so this candidate
  makes no behavioral-equivalence claim.

## Publication boundary

Version 0.2.0 is distributed through the tagged GitHub Release with its wheel
and source distribution attached. PyPI distribution is planned separately; no
package-registry account or publishing credential is required for this release.
