# Instruction Smells

`glyph lint` detects these smells:

- `context_bloat`: long files with low operational density.
- `duplicate_instruction`: equivalent semantic units repeated in different wording.
- `conflicting_instruction`: opposing operational rules.
- `vague_instruction`: wording such as "be careful" or "use best judgment".
- `missing_test_command`: no concrete test command detected.
- `missing_safety_rules`: no secret or credential safety rule detected.
- `missing_reporting_rules`: missing change or verification reporting.
- `lint_leakage`: low-level formatting rules better enforced by linters.
- `skill_leakage`: generic programming lessons rather than repository instructions.
- `excessive_prose`: long non-operational explanations.
- `non_operational_content`: operational-looking sentences Glyph cannot classify.
- `stale_command`: commands that appear outdated or risky.
- `overbroad_rule`: rules that are too broad to enforce well.
- `dangerous_permission`: destructive operations without explicit approval.
- `unmapped_operational_instruction`: an operational-looking instruction did not map to a known or custom semantic unit.
- `low_operational_coverage`: too many operational candidates were unmapped.

Warnings include severity, explanation, and a suggested fix.
