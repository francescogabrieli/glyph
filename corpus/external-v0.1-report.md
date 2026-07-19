# Glyph v0.2 external corpus sweep

This is a metadata-only, reproducible static sweep. It does not redistribute third-party instruction files.

## Gate

| Criterion | Result |
| --- | --- |
| zero_crashes | PASS |
| zero_non_determinisms | PASS |
| retained_coverage_100 | PASS |
| safety_retention_100 | PASS |
| dropped_count_0 | PASS |
| high_risk_preserved_count_0 | PASS |
| structured_agent_instruction_coverage_gte_90 | PASS |
| structured_operational_coverage_gte_80 | PASS |

## Summary

- Repositories: 10
- Files compiled: 124
- Agent-specific files: 18
- Determinism failures: 0
- Files requiring review: 9
- Structured coverage: 78.7% average; 0.0% minimum
- Retained coverage: 100.0% average; 100.0% minimum
- Safety retention: 100.0% average; 100.0% minimum
- Preserved directives: 316
- High-risk preserved directives: 0
- Dropped candidates: 0
- Canonical candidate coverage: 10.9% average
- Agent-instruction coverage: 96.6% average; 88.4% minimum
- Structured operational coverage: 82.2% average; 0.0% minimum
- Token reduction: 55.8% average; -352.0% minimum; 12 negative files

## Repositories

| Repository | SHA | License | Files | Review required |
| --- | --- | --- | ---: | ---: |
| [promptfoo](https://github.com/promptfoo/promptfoo) | `bafcbf23f77c34aead99f43cf06c65cedc384517` | MIT | 19 | 2 |
| [cal.com](https://github.com/calcom/cal.com) | `f00434927386c9ecdcbd7e6c5f82d22044a245bc` | MIT | 4 | 2 |
| [deepagents](https://github.com/langchain-ai/deepagents) | `e9c61304460baab2058a667198600cadef516954` | MIT | 2 | 1 |
| [paperclip](https://github.com/paperclipai/paperclip) | `e4e12bfb890a0fdf4c7de092362472c50a584533` | MIT | 73 | 2 |
| [space-agent](https://github.com/agent0ai/space-agent) | `10f4ffdaf50a8136cf8450d17c11286178fd58e6` | MIT | 2 | 1 |
| [claudian](https://github.com/YishenTu/claudian) | `7d7cc84c60a77431aaccda7ff49a2f1f4ae1c2ab` | MIT | 3 | 0 |
| [evolution-api](https://github.com/evolution-foundation/evolution-api) | `fa09d37892cdbb1d65a250155d293d92230c5b30` | Apache-2.0 with additional conditions | 6 | 1 |
| [awesome-copilot](https://github.com/github/awesome-copilot) | `30472ecf0fe34cc561df958c08501ecc5ca80ea4` | MIT | 10 | 0 |
| [awesome-cursorrules](https://github.com/PatrickJS/awesome-cursorrules) | `b044f956f021b6e8877f16781bcfc466a6a120e9` | CC0-1.0 | 2 | 0 |
| [kubernetes](https://github.com/kubernetes/kubernetes) | `843726939e910e30714ae425d083cd91be4b2437` | Apache-2.0 | 3 | 0 |

## Per-file metadata

| Repository | Path | Adapter | Tokens (Markdown → GLP) | Reduction | Structured | Retained | Safety | Preserved | High-risk preserved | Dropped | Conflicts | Status |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| promptfoo | `AGENTS.md` | agents_md | 5029 → 5402 | -7.4% | 73.1% | 100.0% | 100.0% | 25 | 0 | 0 | 0 | review_required |
| promptfoo | `CLAUDE.md` | claude_md | 5 → 9 | -80.0% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |
| promptfoo | `CONTRIBUTING.md` | contributing | 132 → 46 | 65.2% | 0.0% | 100.0% | 100.0% | 1 | 0 | 0 | 0 | pass |
| promptfoo | `README.md` | readme | 1305 → 258 | 80.2% | 80.0% | 100.0% | 100.0% | 1 | 0 | 0 | 0 | pass |
| promptfoo | `docs/agents/AGENTS.md` | agents_md | 226 → 545 | -141.2% | 80.0% | 100.0% | 100.0% | 2 | 0 | 0 | 0 | review_required |
| promptfoo | `docs/agents/codex-app-server-provider-notes.md` | generic_markdown | 5640 → 865 | 84.7% | 80.0% | 100.0% | 100.0% | 3 | 0 | 0 | 0 | pass |
| promptfoo | `docs/agents/coding-agent-provider-taxonomy.md` | generic_markdown | 4472 → 1059 | 76.3% | 45.8% | 100.0% | 100.0% | 13 | 0 | 0 | 0 | pass |
| promptfoo | `docs/agents/database-security.md` | generic_markdown | 838 → 230 | 72.6% | 40.0% | 100.0% | 100.0% | 3 | 0 | 0 | 0 | pass |
| promptfoo | `docs/agents/dependency-management.md` | generic_markdown | 733 → 611 | 16.6% | 70.0% | 100.0% | 100.0% | 3 | 0 | 0 | 0 | pass |
| promptfoo | `docs/agents/git-workflow.md` | generic_markdown | 438 → 459 | -4.8% | 60.0% | 100.0% | 100.0% | 4 | 0 | 0 | 0 | pass |
| promptfoo | `docs/agents/logging.md` | generic_markdown | 485 → 66 | 86.4% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |
| promptfoo | `docs/agents/pr-conventions.md` | generic_markdown | 1925 → 960 | 50.1% | 78.6% | 100.0% | 100.0% | 3 | 0 | 0 | 0 | pass |
| promptfoo | `docs/agents/python.md` | generic_markdown | 336 → 458 | -36.3% | 87.5% | 100.0% | 100.0% | 1 | 0 | 0 | 0 | pass |
| promptfoo | `docs/architecture/packages.md` | generic_markdown | 1310 → 340 | 74.0% | 60.0% | 100.0% | 100.0% | 2 | 0 | 0 | 0 | pass |
| promptfoo | `docs/plans/2026-01-08-plugins-state-management-refactor.md` | generic_markdown | 4033 → 88 | 97.8% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |
| promptfoo | `docs/plans/2026-05-02-multi-package-system-proposal.md` | generic_markdown | 4745 → 93 | 98.0% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |
| promptfoo | `docs/plans/eng-1770.md` | generic_markdown | 1515 → 69 | 95.4% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |
| promptfoo | `docs/plans/smoke-tests.md` | generic_markdown | 13028 → 39 | 99.7% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |
| promptfoo | `docs/scheduler-architecture.md` | generic_markdown | 2041 → 182 | 91.1% | 20.0% | 100.0% | 100.0% | 4 | 0 | 0 | 0 | pass |
| cal.com | `AGENTS.md` | agents_md | 2199 → 2267 | -3.1% | 88.0% | 100.0% | 100.0% | 6 | 0 | 0 | 0 | review_required |
| cal.com | `CLAUDE.md` | claude_md | 2199 → 2267 | -3.1% | 88.0% | 100.0% | 100.0% | 6 | 0 | 0 | 0 | review_required |
| cal.com | `CONTRIBUTING.md` | contributing | 2099 → 983 | 53.2% | 55.0% | 100.0% | 100.0% | 9 | 0 | 0 | 0 | pass |
| cal.com | `README.md` | readme | 9505 → 3415 | 64.1% | 80.3% | 100.0% | 100.0% | 13 | 0 | 0 | 0 | pass |
| deepagents | `AGENTS.md` | agents_md | 5241 → 1968 | 62.4% | 77.1% | 100.0% | 100.0% | 8 | 0 | 0 | 0 | review_required |
| deepagents | `README.md` | readme | 1685 → 275 | 83.7% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |
| paperclip | `AGENTS.md` | agents_md | 2308 → 1961 | 15.0% | 64.1% | 100.0% | 100.0% | 14 | 0 | 0 | 0 | review_required |
| paperclip | `CONTRIBUTING.md` | contributing | 2508 → 1518 | 39.5% | 84.4% | 100.0% | 100.0% | 5 | 0 | 0 | 0 | pass |
| paperclip | `README.md` | readme | 5135 → 488 | 90.5% | 83.3% | 100.0% | 100.0% | 1 | 0 | 0 | 0 | pass |
| paperclip | `docs/adapters/adapter-ui-parser.md` | generic_markdown | 2617 → 825 | 68.5% | 28.6% | 100.0% | 100.0% | 15 | 0 | 0 | 0 | pass |
| paperclip | `docs/adapters/claude-local.md` | generic_markdown | 1510 → 288 | 80.9% | 60.0% | 100.0% | 100.0% | 2 | 0 | 0 | 0 | pass |
| paperclip | `docs/adapters/codex-local.md` | generic_markdown | 2150 → 417 | 80.6% | 62.5% | 100.0% | 100.0% | 3 | 0 | 0 | 0 | pass |
| paperclip | `docs/adapters/creating-an-adapter.md` | generic_markdown | 2768 → 556 | 79.9% | 50.0% | 100.0% | 100.0% | 6 | 0 | 0 | 0 | pass |
| paperclip | `docs/adapters/external-adapters.md` | generic_markdown | 2780 → 242 | 91.3% | 50.0% | 100.0% | 100.0% | 2 | 0 | 0 | 0 | pass |
| paperclip | `docs/adapters/gemini-local.md` | generic_markdown | 470 → 65 | 86.2% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |
| paperclip | `docs/adapters/http.md` | generic_markdown | 337 → 6 | 98.2% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |
| paperclip | `docs/adapters/overview.md` | generic_markdown | 2047 → 519 | 74.6% | 87.5% | 100.0% | 100.0% | 1 | 0 | 0 | 0 | pass |
| paperclip | `docs/adapters/process.md` | generic_markdown | 336 → 49 | 85.4% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |
| paperclip | `docs/agents-runtime.md` | generic_markdown | 1655 → 700 | 57.7% | 92.9% | 100.0% | 100.0% | 1 | 0 | 0 | 0 | pass |
| paperclip | `docs/api/activity.md` | generic_markdown | 258 → 6 | 97.7% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |
| paperclip | `docs/api/agents.md` | agents_md | 796 → 46 | 94.2% | 0.0% | 100.0% | 100.0% | 1 | 0 | 0 | 0 | review_required |
| paperclip | `docs/api/approvals.md` | generic_markdown | 481 → 6 | 98.8% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |
| paperclip | `docs/api/authentication.md` | generic_markdown | 307 → 54 | 82.4% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |
| paperclip | `docs/api/companies.md` | generic_markdown | 470 → 6 | 98.7% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |
| paperclip | `docs/api/costs.md` | generic_markdown | 340 → 35 | 89.7% | 0.0% | 100.0% | 100.0% | 1 | 0 | 0 | 0 | pass |
| paperclip | `docs/api/dashboard.md` | generic_markdown | 165 → 91 | 44.8% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |
| paperclip | `docs/api/goals-and-projects.md` | generic_markdown | 599 → 61 | 89.8% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |
| paperclip | `docs/api/issues.md` | generic_markdown | 1676 → 205 | 87.8% | 25.0% | 100.0% | 100.0% | 3 | 0 | 0 | 0 | pass |
| paperclip | `docs/api/overview.md` | generic_markdown | 434 → 68 | 84.3% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |
| paperclip | `docs/api/routines.md` | generic_markdown | 1475 → 272 | 81.6% | 66.7% | 100.0% | 100.0% | 2 | 0 | 0 | 0 | pass |
| paperclip | `docs/api/secrets-remote-import.md` | generic_markdown | 1072 → 64 | 94.0% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |
| paperclip | `docs/api/secrets.md` | generic_markdown | 3380 → 575 | 83.0% | 70.0% | 100.0% | 100.0% | 3 | 0 | 0 | 0 | pass |
| paperclip | `docs/built-in-agents.md` | generic_markdown | 1550 → 570 | 63.2% | 66.7% | 100.0% | 100.0% | 3 | 0 | 0 | 0 | pass |
| paperclip | `docs/cli/control-plane-commands.md` | generic_markdown | 1082 → 781 | 27.8% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |
| paperclip | `docs/cli/overview.md` | generic_markdown | 524 → 318 | 39.3% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |
| paperclip | `docs/cli/setup-commands.md` | generic_markdown | 744 → 182 | 75.5% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |
| paperclip | `docs/companies/companies-spec.md` | generic_markdown | 4074 → 1971 | 51.6% | 45.2% | 100.0% | 100.0% | 23 | 0 | 0 | 0 | pass |
| paperclip | `docs/deploy/aws-ecs.md` | generic_markdown | 4818 → 895 | 81.4% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |
| paperclip | `docs/deploy/database.md` | generic_markdown | 499 → 336 | 32.7% | 75.0% | 100.0% | 100.0% | 1 | 0 | 0 | 0 | pass |
| paperclip | `docs/deploy/deployment-modes.md` | generic_markdown | 488 → 244 | 50.0% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |
| paperclip | `docs/deploy/dev-plane-restart-hygiene.md` | generic_markdown | 768 → 262 | 65.9% | 66.7% | 100.0% | 100.0% | 2 | 0 | 0 | 0 | pass |
| paperclip | `docs/deploy/docker.md` | generic_markdown | 769 → 213 | 72.3% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |
| paperclip | `docs/deploy/environment-variables.md` | generic_markdown | 712 → 10 | 98.6% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |
| paperclip | `docs/deploy/local-development.md` | generic_markdown | 522 → 132 | 74.7% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |
| paperclip | `docs/deploy/overview.md` | generic_markdown | 340 → 318 | 6.5% | 71.4% | 100.0% | 100.0% | 2 | 0 | 0 | 0 | pass |
| paperclip | `docs/deploy/secrets.md` | generic_markdown | 5000 → 2464 | 50.7% | 84.6% | 100.0% | 100.0% | 6 | 0 | 0 | 0 | pass |
| paperclip | `docs/deploy/storage.md` | generic_markdown | 189 → 67 | 64.6% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |
| paperclip | `docs/deploy/tailscale-private-access.md` | generic_markdown | 490 → 68 | 86.1% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |
| paperclip | `docs/feedback-voting.md` | generic_markdown | 1891 → 233 | 87.7% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |
| paperclip | `docs/guides/agent-developer/comments-and-communication.md` | generic_markdown | 631 → 299 | 52.6% | 42.9% | 100.0% | 100.0% | 4 | 0 | 0 | 0 | pass |
| paperclip | `docs/guides/agent-developer/cost-reporting.md` | generic_markdown | 383 → 92 | 76.0% | 50.0% | 100.0% | 100.0% | 1 | 0 | 0 | 0 | pass |
| paperclip | `docs/guides/agent-developer/handling-approvals.md` | generic_markdown | 616 → 412 | 33.1% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |
| paperclip | `docs/guides/agent-developer/heartbeat-protocol.md` | generic_markdown | 1290 → 1061 | 17.8% | 50.0% | 100.0% | 100.0% | 12 | 0 | 0 | 0 | pass |
| paperclip | `docs/guides/agent-developer/how-agents-work.md` | generic_markdown | 543 → 135 | 75.1% | 50.0% | 100.0% | 100.0% | 1 | 0 | 0 | 0 | pass |
| paperclip | `docs/guides/agent-developer/skills-store.md` | generic_markdown | 3252 → 429 | 86.8% | 55.6% | 100.0% | 100.0% | 4 | 0 | 0 | 0 | pass |
| paperclip | `docs/guides/agent-developer/task-workflow.md` | generic_markdown | 1116 → 458 | 59.0% | 63.6% | 100.0% | 100.0% | 4 | 0 | 0 | 0 | pass |
| paperclip | `docs/guides/agent-developer/writing-a-skill.md` | generic_markdown | 482 → 341 | 29.3% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |
| paperclip | `docs/guides/board-operator/activity-log.md` | generic_markdown | 350 → 99 | 71.7% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |
| paperclip | `docs/guides/board-operator/approvals.md` | generic_markdown | 355 → 151 | 57.5% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |
| paperclip | `docs/guides/board-operator/costs-and-budgets.md` | generic_markdown | 438 → 62 | 85.8% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |
| paperclip | `docs/guides/board-operator/creating-a-company.md` | generic_markdown | 447 → 93 | 79.2% | 50.0% | 100.0% | 100.0% | 1 | 0 | 0 | 0 | pass |
| paperclip | `docs/guides/board-operator/dashboard.md` | generic_markdown | 304 → 138 | 54.6% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |
| paperclip | `docs/guides/board-operator/delegation.md` | generic_markdown | 1365 → 357 | 73.8% | 71.4% | 100.0% | 100.0% | 2 | 0 | 0 | 0 | pass |
| paperclip | `docs/guides/board-operator/execution-workspaces-and-runtime-services.md` | generic_markdown | 882 → 113 | 87.2% | 50.0% | 100.0% | 100.0% | 1 | 0 | 0 | 0 | pass |
| paperclip | `docs/guides/board-operator/experimental-features.md` | generic_markdown | 397 → 230 | 42.1% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |
| paperclip | `docs/guides/board-operator/importing-and-exporting.md` | generic_markdown | 1844 → 400 | 78.3% | 57.1% | 100.0% | 100.0% | 3 | 0 | 0 | 0 | pass |
| paperclip | `docs/guides/board-operator/managing-agents.md` | generic_markdown | 639 → 129 | 79.8% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |
| paperclip | `docs/guides/board-operator/managing-tasks.md` | generic_markdown | 422 → 242 | 42.7% | 75.0% | 100.0% | 100.0% | 1 | 0 | 0 | 0 | pass |
| paperclip | `docs/guides/board-operator/org-structure.md` | generic_markdown | 332 → 158 | 52.4% | 66.7% | 100.0% | 100.0% | 1 | 0 | 0 | 0 | pass |
| paperclip | `docs/guides/execution-policy.md` | generic_markdown | 2490 → 802 | 67.8% | 20.8% | 100.0% | 100.0% | 19 | 0 | 0 | 0 | pass |
| paperclip | `docs/guides/openclaw-docker-setup.md` | generic_markdown | 3056 → 803 | 73.7% | 83.3% | 100.0% | 100.0% | 1 | 0 | 0 | 0 | pass |
| paperclip | `docs/pipelines-tutorial.md` | generic_markdown | 5545 → 437 | 92.1% | 87.5% | 100.0% | 100.0% | 1 | 0 | 0 | 0 | pass |
| paperclip | `docs/plans/2026-03-13-issue-documents-plan.md` | generic_markdown | 3204 → 64 | 98.0% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |
| paperclip | `docs/specs/agent-config-ui.md` | generic_markdown | 2854 → 557 | 80.5% | 90.0% | 100.0% | 100.0% | 1 | 0 | 0 | 0 | pass |
| paperclip | `docs/specs/cliphub-plan.md` | generic_markdown | 4187 → 95 | 97.7% | 50.0% | 100.0% | 100.0% | 1 | 0 | 0 | 0 | pass |
| paperclip | `docs/start/architecture.md` | generic_markdown | 955 → 181 | 81.0% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |
| paperclip | `docs/start/core-concepts.md` | generic_markdown | 793 → 103 | 87.0% | 0.0% | 100.0% | 100.0% | 3 | 0 | 0 | 0 | pass |
| paperclip | `docs/start/quickstart.md` | generic_markdown | 405 → 221 | 45.4% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |
| paperclip | `docs/start/what-is-paperclip.md` | generic_markdown | 428 → 55 | 87.1% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |
| space-agent | `AGENTS.md` | agents_md | 1049 → 2365 | -125.5% | 77.8% | 100.0% | 100.0% | 8 | 0 | 0 | 0 | review_required |
| space-agent | `README.md` | readme | 1754 → 488 | 72.2% | 57.1% | 100.0% | 100.0% | 3 | 0 | 0 | 0 | pass |
| claudian | `AGENTS.md` | agents_md | 1240 → 1817 | -46.5% | 80.0% | 100.0% | 100.0% | 5 | 0 | 0 | 0 | pass |
| claudian | `CLAUDE.md` | claude_md | 25 → 113 | -352.0% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |
| claudian | `README.md` | readme | 2291 → 236 | 89.7% | 60.0% | 100.0% | 100.0% | 2 | 0 | 0 | 0 | pass |
| evolution-api | `.cursor/rules/core-development.mdc` | cursor_rules | 1585 → 1550 | 2.2% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |
| evolution-api | `.cursor/rules/project-context.mdc` | cursor_rules | 1674 → 1176 | 29.7% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |
| evolution-api | `AGENTS.md` | agents_md | 2600 → 878 | 66.2% | 78.9% | 100.0% | 100.0% | 4 | 0 | 0 | 0 | review_required |
| evolution-api | `CLAUDE.md` | claude_md | 1914 → 441 | 77.0% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |
| evolution-api | `CONTRIBUTING.md` | contributing | 608 → 342 | 43.8% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |
| evolution-api | `README.md` | readme | 2065 → 305 | 85.2% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |
| awesome-copilot | `.github/copilot-instructions.md` | copilot_instructions | 834 → 415 | 50.2% | 85.7% | 100.0% | 100.0% | 1 | 0 | 0 | 0 | pass |
| awesome-copilot | `AGENTS.md` | agents_md | 3833 → 4540 | -18.4% | 86.4% | 100.0% | 100.0% | 12 | 0 | 0 | 0 | pass |
| awesome-copilot | `CONTRIBUTING.md` | contributing | 5680 → 3556 | 37.4% | 85.5% | 100.0% | 100.0% | 8 | 0 | 0 | 0 | pass |
| awesome-copilot | `README.md` | readme | 29014 → 372 | 98.7% | 75.0% | 100.0% | 100.0% | 1 | 0 | 0 | 0 | pass |
| awesome-copilot | `docs/README.agents.md` | generic_markdown | 74940 → 177 | 99.8% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |
| awesome-copilot | `docs/README.hooks.md` | generic_markdown | 753 → 121 | 83.9% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |
| awesome-copilot | `docs/README.instructions.md` | generic_markdown | 54783 → 112 | 99.8% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |
| awesome-copilot | `docs/README.plugins.md` | generic_markdown | 5448 → 175 | 96.8% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |
| awesome-copilot | `docs/README.skills.md` | generic_markdown | 43713 → 80 | 99.8% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |
| awesome-copilot | `docs/README.workflows.md` | generic_markdown | 733 → 302 | 58.8% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |
| awesome-cursorrules | `CONTRIBUTING.md` | contributing | 734 → 489 | 33.4% | 85.7% | 100.0% | 100.0% | 1 | 0 | 0 | 0 | pass |
| awesome-cursorrules | `README.md` | readme | 12777 → 824 | 93.6% | 68.8% | 100.0% | 100.0% | 5 | 0 | 0 | 0 | pass |
| kubernetes | `AGENTS.md` | agents_md | 331 → 1025 | -209.7% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |
| kubernetes | `CONTRIBUTING.md` | contributing | 122 → 59 | 51.6% | 0.0% | 100.0% | 100.0% | 1 | 0 | 0 | 0 | pass |
| kubernetes | `README.md` | readme | 954 → 201 | 78.9% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | pass |

## Failure triage

- conflict requiring human review: 0
- correct preserved blocker: 172
- false-positive operational candidate: 77
- non-operational documentation: 11
- parser/classifier bug: 0
- policy extraction bug: 4
- repo-specific custom rule candidate: 6
- unsupported conditional pattern: 46

## Sanitized high-risk taxonomy

High-risk operational candidates: 59

| Shape | Predicate | Objects | Operators | Attachment | Ambiguous | Reason | Outcome | Count |
| --- | --- | ---: | --- | --- | --- | --- | --- | ---: |
| durable_authorization | - | 1 | all, any, atomic | policy | false | unique_durable_authorization | policy | 1 |
| approval_statement_compound | - | 1 | all, atomic, not | policy | false | unique_approval_statement_compound | policy | 1 |
| positive_action | action | 1 | any, atomic | policy | false | unique_positive_action | policy | 1 |
| action_predicate | action | 1 | atomic | policy | false | unique_action_predicate | policy | 1 |
| avoid_action | action | 1 | atomic | policy | false | unique_avoid_action | policy | 1 |
| positive_action | action | 1 | atomic | policy | false | unique_positive_action | policy | 2 |
| positive_action | - | 2 | all, any, atomic | policy | false | unique_positive_action | policy | 1 |
| required_state | state | 0 | atomic | - | false | unique_required_state | policy | 1 |
| unresolved | - | 0 | - | - | false | unclassified | canonical | 12 |
| unresolved | - | 0 | - | - | false | temporal_sequence_required | policy | 1 |
| negative_action | action | 1 | atomic, not | - | false | unique_negative_action | policy | 3 |
| positive_action | action | 1 | atomic | - | false | unique_positive_action | policy | 18 |
| state_predicate | state | 1 | atomic | - | false | unique_state_predicate | policy | 1 |
| action_predicate | - | 2 | all, atomic, not | - | false | unique_action_predicate | policy | 1 |
| negative_action | - | 2 | all, atomic, not | - | false | unique_negative_action | policy | 5 |
| positive_action | - | 2 | all, atomic | - | false | unique_positive_action | policy | 7 |
| mixed_modal_compound | - | 2 | atomic | - | false | unique_mixed_modal_compound | policy | 1 |
| positive_action | - | 3 | all, atomic | - | false | unique_positive_action | policy | 1 |

Individual finding metadata (a stable text hash, line, intent, risk marker, destination, classification, and sanitized derivation) is retained in the JSON report without storing third-party instruction text.

## Method

Every discovered supported file was adapter-detected, compiled twice for byte-level determinism, inspected through the post-hardening extraction metrics, and measured. Repositories with multiple agent-specific instruction files were also compiled as a single multi-input manifest. Low or negative reductions are retained per file and are not clamped.
