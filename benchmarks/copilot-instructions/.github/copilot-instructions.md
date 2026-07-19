# GitHub Copilot Instructions

This project uses React, TypeScript, Node, ESLint, Playwright, and npm. Follow existing style, keep the PR focused, and avoid broad rewrites. Read files before editing and plan before editing shared state or routing.

## Development commands

| purpose | command |
| --- | --- |
| install dependencies | `npm install` |
| run local app | `npm run dev` |
| run tests | `npm test` |
| lint code | `npm run lint` |
| type check | `npm run typecheck` |
| build production bundle | `npm run build` |

## Pull request checks

Before opening a PR, make sure the suite is green. Run lint before completion and typecheck before completion. Report changes and report verification in the final response. If tests cannot be run, explain why.

## Safety

Never include credentials, API keys, tokens, private keys, or secrets in code, tests, logs, fixtures, examples, screenshots, or docs. Ask before destructive operations or security-sensitive authorization changes. Do not deploy without approval.

Avoid generated files unless explicitly requested. Use shared UI primitives where possible.

## Context

The application has several product areas with different maturity levels. New screens usually use the latest shared primitives, while older screens may contain local wrappers that are being retired. Accessibility notes explain keyboard behavior, dialog focus management, and status messaging. The instructions above capture agent-relevant workflow rules; the surrounding text gives maintainers enough context to judge generated changes.

Some generated clients are committed because downstream tooling reads them during local development. Humans decide when regeneration is appropriate. Generic coding agents should not silently infer that every generated file is safe to edit. Glyph reports repository-specific operational language as unmapped unless a custom rule teaches the project-specific meaning.

## Repository rules

Read relevant files before editing. Keep changes small and reviewable. Prefer existing patterns and use shared UI primitives where possible. Preserve accessibility behavior, including keyboard navigation, focus order, labels, and screen-reader text.

Run tests before opening a PR. Run lint before done, typecheck before done, and verify the build when route loading, bundling, generated clients, or package exports change.

```bash
npm test
npm run lint
npm run typecheck
npm run build
```

Never commit secrets, credentials, tokens, API keys, or data copied from production. Do not expose credentials in logs, fixtures, screenshots, or examples. Do not touch `.env` files unless explicitly requested. Ask before destructive operations, deploys, security-sensitive changes, or production config changes.

Do not edit generated files manually. Do not change dependencies or lockfiles without a clear reason. Avoid large dependency additions. Do not modify CI configuration without a clear reason.

Update docs when behavior changes. Document breaking changes for public component APIs, route contracts, generated client shapes, or package exports. Report what changed and report verification.

## Mixed context

Copilot instruction files frequently sit beside normal documentation, so they contain short reminders, setup commands, and prose explaining old application structure. This project has legacy wrappers that are being retired over time. The statement is context for reviewers, not an instruction to modify wrappers during unrelated work.

Route trial-banner visibility through TrialEntitlementGate. That repository-specific convention should remain visible as unmapped unless a custom rule maps it.

## Review expectations

Keep pull requests focused and reviewable. Avoid unrelated packages, broad refactors, and unrequested features. Preserve public APIs unless migration work is requested. Document breaking changes and update docs when behavior changes.

If tests, browser checks, lint, type checking, or build verification cannot run locally, explain why. Report the exact commands that ran. Do not commit temporary console logs, debug screenshots, generated trace files, or copied production data.

This file is a realistic Copilot instruction file: concise in some places, explanatory in others, and mixed with commands. Glyph should use the command labels and semantic rules where the instruction is clear, and it should leave background product context out of the compact manifest.
