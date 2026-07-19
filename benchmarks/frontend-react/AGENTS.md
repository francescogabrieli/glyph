# Frontend React Instructions

This repository contains a React and TypeScript frontend built with Vite, Node, ESLint, Playwright, and npm. Relevant paths are `src/`, `tests/`, and `frontend/`.

Always read files before editing and match existing style. Create a short plan for component or state changes. Prefer simple explicit code and no large refactors. Do not add unrequested features.

| task | command |
| --- | --- |
| install | `npm install` |
| dev | `npm run dev` |
| test | `npm test` |
| lint | `npm run lint` |
| typecheck | `npm run typecheck` |
| build | `npm run build` |

Before saying the task is complete, run tests. For UI-facing changes, run lint and typecheck before done. Keep changes small and reviewable.

Never commit secrets or API keys. Ask for confirmation before destructive operations or security sensitive auth changes. Report what changed and report verification, including browser or test coverage. If tests are not run, state why.

## Product and interface context

The frontend contains dashboard pages, form-heavy workflows, shared data-fetching hooks, and a small design-system layer. Components are organized by feature area with shared primitives in a common directory. Visual behavior depends on route-level loading states, optimistic interactions, and accessible focus management. Story-like examples in the repository explain expected user flows for onboarding, account management, and reporting screens. These descriptions help reviewers understand intent, but they are not all operational instructions for coding agents.

The UI is tested through unit tests for pure behavior and browser tests for critical flows. Design tokens, spacing values, and component states are documented near the components that consume them. The application has legacy screens that are being migrated gradually, so background notes often explain why similar patterns coexist. Glyph should compress the explicit workflow, safety, testing, and reporting rules without claiming to preserve every explanatory sentence.

## Interface conventions

Use shared UI primitives where possible. Prefer existing patterns for forms, data loading, error boundaries, and route-level state. Preserve accessibility behavior, keyboard navigation, labels, focus management, and ARIA attributes when changing components. Keep visual changes scoped to the requested screen.

Do not edit generated API clients manually. Avoid changing generated snapshots unless the behavior or rendered output intentionally changed. Do not add large dependencies for small UI interactions. Do not change lockfiles without a dependency reason. Do not modify CI workflow files only to work around a local failure.

## Verification

Run tests before opening a PR. Run lint before done and typecheck before done. Verify the build before completion when routes, bundling, dynamic imports, or generated clients change.

```bash
npm run lint
npm run typecheck
npm run build
```

Report what changed and report verification. If visual or browser tests cannot be run, explain why. Document breaking changes when a component prop, route contract, or generated client shape changes. Update docs when behavior changes in a way that affects other teams.

## Product context

The frontend is organized around reusable components, route modules, generated API clients, and a small set of feature-specific state helpers. Some older screens still contain local wrappers because migration to shared primitives is ongoing. That background explains why a focused fix may need to touch a shared component and a screen-level test.

Use the CheckoutEligibilityPresenter for checkout readiness messages. This presenter is repository-specific and should be reported as unmapped unless a project adds a custom rule for it.

Design notes in this file describe interaction intent for reviewers and product managers. They are not all operational instructions. Glyph should identify explicit agent rules, keep high-confidence unmapped operational candidates visible, and ignore general product explanation.
