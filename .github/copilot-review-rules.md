# Copilot Review Rules

Purpose

- Define consistent review behavior and response formatting for Copilot code reviews.
- Keep reviews concise and action-oriented.

Writing style

- Use short headings and bullet lists.
- Prefer do/avoid constraints over prose.
- Make checks verifiable (point to code and impact).
- Keep responses concise; avoid long audit reports unless requested.

Review modes

- Default review: standard PR risk.
- Double-check review: elevated risk PRs.

Mode: Default review

- Scope
  - Single PR, normal risk.
- Priorities (in order)
  - correctness → security → tests → maintainability → style
- Checks
  - Correctness
    - Do highlight logic bugs, missing edge cases, regressions, and contract changes.
  - Security & data handling
    - Do flag unsafe input handling, secrets exposure, auth/authz issues, and insecure defaults.
  - Tests
    - Do check that tests exist for changed logic and cover success + failure paths.
  - Maintainability
    - Do point out unnecessary complexity, duplication, and unclear naming/structure.
  - Style
    - Avoid style notes unless they reduce readability or break repo conventions.
- Response format
  - Use short bullet points.
  - Reference files + line ranges where possible.
  - Group comments by severity: Blocker (must fix), Important (should fix), Nit (optional).
  - Do provide minimal, actionable suggestions (what to change), not rewrites.
  - Avoid rewriting the whole PR or producing long reports.

Mode: Double-check review

- Scope
  - Higher-risk PRs (security, infra/CI, wide refactors, data migrations, auth changes).
- Additional focus
  - Do confirm previous review comments were addressed (when applicable).
  - Do re-check high-risk areas: auth, permissions, secrets, persistence, external calls, concurrency.
  - Do look for hidden side effects: backward compatibility, upgrade/rollout path, failure modes, retries/timeouts, idempotency.
  - Do validate safe defaults: least privilege, secure logging, safe error messages, predictable behavior on missing inputs.
- Response format
  - Only add comments where risk/impact is non-trivial.
  - Avoid repeating minor style notes already covered by default review.
  - If leaving something as-is, call out risk acceptance explicitly:
    - what risk
    - why acceptable
    - mitigation (tests/monitoring/feature flag)

Commenting rules (all modes)

- Always include:
  - What is the issue (1 line)
  - Why it matters (impact/risk)
  - How to fix (minimal actionable suggestion)
- Prefer linking to existing patterns in the repo over introducing new ones.
- If uncertain (missing context), ask a targeted question instead of assuming.

Non-goals

- Avoid requesting refactors unrelated to the PR’s intent.
- Avoid bikeshedding formatting if formatter/linter handles it.
- Avoid architectural rewrites unless explicitly requested.

Repo additions

- Domain-specific high-risk areas
  - GitHub API usage: pagination, rate limits, and error handling.
  - Secrets handling: avoid leaking tokens/headers in logs.
  - Contract-sensitive outputs: release notes text and action failure strings.
  - Exit codes: do not change existing failure exit codes unintentionally.
- Required tests
  - Prefer unit tests under tests/unit/.
  - Avoid real GitHub API calls in unit tests.
