Copilot instructions

Purpose
- Must define a consistent style for .github/copilot-instructions.md.
- Must keep externally-visible behavior stable unless intentionally changing the contract.

Structure
- Must keep sections in the same order across repos.
- Prefer bullet lists over paragraphs.
- Must use constraint words: Must / Must not / Prefer / Avoid.
- Must keep one blank line at end of file.

Context
- Must support a GitHub Action / CI automation context.
- Must treat environment and GitHub I/O as boundary concerns.

Coding guidelines
- Must keep changes small and focused.
- Prefer clear, explicit code over clever tricks.
- Must keep pure logic free of environment access where practical.
- Prefer routing env/I/O through a single boundary module.
- Must keep externally-visible strings, formats, and exit codes stable unless intentional.

Output discipline (reduce review time)
- Must default to concise responses (aim ≤ 10 lines in the final recap).
- Must not paste large file contents/configs/checklists; link and summarize deltas.
- Prefer actionable bullets over prose.
- When making code changes, must end with:
  - What changed
  - Why
  - How to verify (commands/tests)
- Avoid deep rationale unless explicitly requested.

PR Body Management
- Must treat PR description as a changelog.
- Must not rewrite or replace the entire PR body.
- Must append updates chronologically under a new heading.
- Prefer headings: "## Update [YYYY-MM-DD]" or "## Changes Added".
- Must reference the commit hash that introduced the change.

Inputs
- Must read inputs via environment variables when running in CI.
- Must centralize parsing and validation in one input layer.
- Must not duplicate validation across modules.
- Prefer documenting required vs optional inputs with defaults.

Language and style
- Must target Python 3.14+.
- Must add type hints for new public functions and classes.
- Must use logging, not print.
- Must use lazy % formatting for logs.
- Must keep imports at top of file.
- Must include the standard copyright/license header in every code file, including __init__.py.
- Must use the project first-copyright year.

String formatting
- Prefer t-strings for non-logging templates.
- Avoid f-strings for user-facing text unless needed for clarity.
- Must not use f-strings or t-strings in logging calls.

Docstrings and comments
- Docstrings:
  - Must start with a short summary line.
  - Prefer structured sections (Parameters: / Returns: / Raises:).
  - Avoid tutorials, long prose, and doctest examples.
- Comments:
  - Prefer self-explanatory code.
  - Prefer comments for intent/edge cases (the “why”).
  - Avoid blocks that restate the code.

Patterns
- Errors:
  - Prefer raising exceptions in leaf modules.
  - Prefer translating failures to action failure output / exit codes at the entry point.
- Testability:
  - Must keep boundaries mockable.
  - Must not call real external APIs in unit tests.

Testing
- Must use pytest under tests/.
- Must test return values, exceptions, log messages, and exit codes.
- Prefer unit tests under tests/unit/.
- Must mock GitHub API interactions and environment variables in unit tests.

Tooling
- Must format with Black (pyproject.toml).
- Must lint with Pylint (ignore tests/).
- Must type-check with mypy.
- Must keep coverage ≥ 80% when running pytest-cov.

Quality gates
- Must run tests first, then format/lint/type-check.
- Tests:
  - pytest tests/unit/
  - pytest tests/
- Coverage:
  - pytest --ignore=tests/integration --cov=. tests/ --cov-fail-under=80 --cov-report=html
- Format:
  - black $(git ls-files '*.py')
- Lint:
  - pylint --ignore=tests $(git ls-files '*.py')
- Types:
  - mypy .

Common pitfalls to avoid
- Dependencies: must verify compatibility with target runtime.
- Untyped deps: avoid type: ignore unless required; document why.
- Logging: must keep lazy % formatting.
- Cleanup: must remove unused imports/variables.
- Stability: avoid changing externally-visible strings/outputs.

Learned rules
- Must not change exit codes for existing failure scenarios.
- Must not change externally-visible output strings without updating the contract.

Repo additions
- Project name: generate-release-notes
- Entry points: action.yml, main.py
- Core package: release_notes_generator/
- Input layer: ActionInputs (INPUT_* env vars)
- Logging wiring: release_notes_generator.utils.logging_config
- Contract-sensitive outputs: release notes text; action failure strings; exit codes
- Commands:
  - python3 -m venv .venv
  - source .venv/bin/activate
  - pip install -r requirements.txt
