Copilot instructions for generate-release-notes

Purpose
This repo contains a Python GitHub Action that generates release notes from GitHub issues, PRs, and commits.

Context
- Composite action defined in action.yml
- Entry script is main.py
- Core code is in release_notes_generator/ (inputs, mining, chapter building, rendering)
- Inputs are read from GitHub Actions env vars (via ActionInputs)

Coding guidelines
- Keep changes small and focused
- Prefer clear, explicit code over clever tricks
- Keep behaviour of action inputs and output formats stable unless the contract is intentionally updated

Output discipline (reduce review time)
- Default to concise responses (aim ≤ 10 lines in the final recap)
- Do not restate large file contents, configs, or checklists; link to files and summarize deltas
- Prefer actionable bullets over prose; avoid repeating unchanged plan sections
- When making code changes, end with: What changed / Why / How to verify (commands/tests)
- Only include deep rationale, alternatives, or long examples when explicitly requested

Python and style
- Target Python 3.11 or later
- Follow the current patterns in release_notes_generator
- Add type hints for new public functions and classes
- Use logging, not print, and keep logging wired through release_notes_generator.utils.logging_config
- All Python imports must be placed at the top of the file, not inside methods or functions

Docstrings and comments
- Keep docstrings consistent with existing modules: a short summary line, then optional `Parameters:` / `Returns:` sections
- Avoid long prose, tutorials, or doctest-style examples inside docstrings; keep them focused on behavior and contracts
- Prefer self-explanatory code over comments; add comments only when they explain non-obvious intent or edge cases (the “why”)
- Avoid multi-line comment blocks that restate what the code already expresses

Copyright headers
- Ensure the standard copyright/license header is present in every code file, including `__init__.py` modules
- Use the repository/project's first-copyright year (the year of the first file that introduced this standard header), not the individual file creation year

Testing
- Use pytest with tests located in tests/
- Test behaviour: return values, raised errors, log messages, exit codes
- Prefer unit tests under tests/unit/; keep integration tests optional and isolated
- Mock GitHub API interactions and environment variables; do not call the real GitHub API in unit tests

Tooling
- Format with Black using pyproject.toml
- Run Pylint on tracked Python files, excluding tests/, and aim for score 9.5 or higher
- Run mypy and prefer fixing types instead of ignoring errors
- Use pytest-cov and keep coverage at or above 80 percent

Pre-commit Quality Gates:
Before submitting any PR or claiming work is complete, ALWAYS run these checks locally:

1. Testing
- Run unit tests: `pytest tests/unit/` (or relevant test directory)
- Run integration/verification tests if they exist
- Ensure exit code 0 for all tests
- Fix any test failures before proceeding

2. Code Quality
- Format with Black: `black $(git ls-files '*.py')`
- Run Pylint: `pylint $(git ls-files '*.py')`
  - Target score: ≥ 9.5/10
  - Fix warnings before submitting
- Run mypy: `mypy .` or `mypy <changed_files>`
  - Resolve type errors or use appropriate type ignore comments
  - Document why type ignores are necessary

3. Verification Workflow
3.1. **After writing code**: Run tests immediately
3.2. **After tests pass**: Run linters (Black, Pylint, mypy)
3.3. **After linters pass**: Commit changes
3.4. **Before pushing**: Run full quality gate again

4. Early Detection
- Run quality checks EARLY in development, not at the end
- Fix issues incrementally as they appear
- Don't accumulate technical debt

Common Pitfalls to Avoid:

Dependencies
- Check library compatibility with target Python version BEFORE using
- Test imports locally before committing
- For untyped libraries: add `# type: ignore[import-untyped]` comments

Logging
- Always use lazy % formatting: `logger.info("msg %s", var)`
- NEVER use f-strings in logging: ~~`logger.info(f"msg {var}")`~~
- Reason: avoids string interpolation when logging is disabled

Variable Cleanup
- Remove unused variables promptly
- Run linters to catch them early
- Don't leave dead code

Checklist Template
Use this for every PR:
- All tests pass locally (pytest)
- Black formatting applied
- Pylint score ≥ 9.5
- Mypy passes (or documented type ignores)
- No unused imports/variables
- Logging uses lazy % formatting
- Dependencies tested locally
- Documentation updated

Architecture notes
 - Action must work on a GitHub Actions runner with only requirements.txt dependencies
 - Keep pure logic free of environment access where practical; prefer routing env/input behaviour through ActionInputs
 - Avoid adding network calls to unit tests

File overview
- main.py: sets up logging and runs the action
- action.yml: composite action definition
- release_notes_generator/action_inputs.py: action input handling
- release_notes_generator/generator.py: orchestration
- release_notes_generator/builder/: release notes builder
- release_notes_generator/chapters/: chapter implementations
- release_notes_generator/data/: mining/filtering
- release_notes_generator/model/: data models and records
- release_notes_generator/utils/: helpers including gh_action and logging_config

Common commands
- Create and activate venv, install deps:
  - python3 -m venv .venv
  -	source .venv/bin/activate
  - pip install -r requirements.txt
- Run tests:
  - pytest tests/
- Run coverage:
  - pytest --ignore=tests/integration --cov=. tests/ --cov-fail-under=80 --cov-report=html
- Format and lint:
  - black
  - pylint --ignore=tests $(git ls-files "*.py")
  - mypy .

Learned rules
- Keep externally-visible output stable; tests assert on exact strings in several places
- Do not change exit codes for existing failure scenarios
