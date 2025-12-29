# Copilot Review Rules

Default review

- **Scope:** Single PR, normal risk.
- **Priorities (in order):** correctness → security → tests → maintainability → style.
- **Checks:**
  - Highlight logic bugs, missing edge cases, and regressions.
  - Flag security or data‑handling issues.
  - Check that tests exist and cover the changed logic.
  - Point out large complexity / duplication hotspots.
- **Response format:**
  - Use short bullet points.
  - Reference files + line ranges where possible.
  - Do NOT rewrite the whole PR or produce long reports.

Double-check review

- **Scope:** Higher‑risk PRs (security, infra, money flows, wide refactors).
- **Additional focus:**
  - Re‑validate that previous review comments were correctly addressed.
  - Re‑check high‑risk areas: auth, permissions, money transfers, persistence, external calls.
  - Look for hidden side effects and backward‑compatibility issues.
- **Response format:**
  - Only add comments where risk/impact is non‑trivial.
  - Avoid repeating minor style notes already covered by default review.
  