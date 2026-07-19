from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _format_pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def summarize(results: dict) -> str:
    runs = results.get("runs", [])
    by_condition: dict[str, list[dict]] = defaultdict(list)
    baseline_tokens: dict[str, int] = {}
    baseline_rule_rates: dict[str, dict[str, float]] = defaultdict(dict)

    for run in runs:
        condition = run["condition"]
        by_condition[condition].append(run)
        if condition == "original_markdown":
            baseline_tokens[run["case_id"]] = int(run["instruction_tokens"])

    for run in by_condition.get("original_markdown", []):
        for rule_id, outcome in run.get("rule_results", {}).items():
            followed = outcome.get("followed")
            if followed is None:
                continue
            baseline_rule_rates[run["case_id"]][rule_id] = 1.0 if followed else 0.0

    lines = [
        "Glyph behavior evaluation summary",
        "",
        "Runs by condition",
    ]
    failures = results.get("failures", [])
    if failures:
        lines.append(f"- failures: {len(failures)}")
    for condition in sorted(by_condition):
        lines.append(f"- {condition}: {len(by_condition[condition])}")

    lines.extend(["", "Condition metrics"])
    for condition in sorted(by_condition):
        condition_runs = by_condition[condition]
        tokens = [float(run["instruction_tokens"]) for run in condition_runs]
        must = [float(run["must_adherence"]) for run in condition_runs]
        deny = [float(run["deny_violations"]) for run in condition_runs]
        ask = [float(run["ask_adherence"]) for run in condition_runs if run.get("ask_adherence") is not None]
        test = [float(run["test_compliance"]) for run in condition_runs]
        reporting = [float(run.get("reporting_compliance", 0.0)) for run in condition_runs]
        success = [float(run.get("task_success", 0.0)) for run in condition_runs]
        agent_success = [1.0 if int(run.get("agent_returncode", 0)) == 0 else 0.0 for run in condition_runs]
        token_reductions: list[float] = []
        for run in condition_runs:
            baseline = baseline_tokens.get(run["case_id"])
            if baseline:
                token_reductions.append(1 - float(run["instruction_tokens"]) / float(baseline))
        lines.append(f"- {condition}")
        lines.append(f"  average instruction tokens: {_mean(tokens):.1f}")
        lines.append(f"  token reduction vs original_markdown: {_format_pct(_mean(token_reductions))}")
        lines.append(f"  must adherence: {_format_pct(_mean(must))}")
        lines.append(f"  deny violations: {_mean(deny):.2f}")
        lines.append(f"  ask adherence: {_format_pct(_mean(ask)) if ask else 'not observed'}")
        lines.append(f"  test compliance: {_format_pct(_mean(test))}")
        lines.append(f"  reporting compliance: {_format_pct(_mean(reporting))}")
        lines.append(f"  task success: {_format_pct(_mean(success))}")
        lines.append(f"  agent command success: {_format_pct(_mean(agent_success))}")

    probe_runs = [run for run in runs if run.get("safety_probe")]
    if probe_runs:
        lines.extend(["", "Safety probes"])
        for run in probe_runs:
            probe = run["safety_probe"]
            lines.append(
                f"- {run['case_id']} {run['condition']}: {probe['target_rule']} "
                f"followed={probe['followed']} asked={probe['asked_for_confirmation']} "
                f"protected_state_preserved={probe['protected_state_preserved']}"
            )

    per_rule_by_condition: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for condition, condition_runs in by_condition.items():
        for run in condition_runs:
            for rule_id, outcome in run.get("rule_results", {}).items():
                followed = outcome.get("followed")
                if followed is None:
                    continue
                per_rule_by_condition[condition][rule_id].append(1.0 if followed else 0.0)

    lines.extend(["", "Per-rule deltas vs original_markdown"])
    for condition in sorted(condition for condition in by_condition if condition != "original_markdown"):
        lines.append(f"- {condition}")
        rule_ids = sorted(set(per_rule_by_condition[condition]) | set(per_rule_by_condition.get("original_markdown", {})))
        for rule_id in rule_ids:
            current = _mean(per_rule_by_condition[condition].get(rule_id, []))
            baseline_values = per_rule_by_condition.get("original_markdown", {}).get(rule_id, [])
            baseline = _mean(baseline_values)
            delta = current - baseline
            lines.append(f"  {rule_id}: {delta:+.2f}")

    if failures:
        lines.extend(["", "Failures"])
        for failure in failures:
            lines.append(f"- {failure.get('case_id')} {failure.get('condition')}: {failure.get('error')}")

    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: python evals/behavior/analyze.py <results.json>", file=sys.stderr)
        return 2
    path = Path(argv[1])
    print(summarize(_load(path)), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
