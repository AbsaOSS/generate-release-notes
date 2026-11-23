# Generate Release Notes Action—for Developers

- [Get Started](#get-started)
- [Quality Gates](#quality-gates)
- [Running Unit Tests](#running-unit-tests)
- [Running Integration Tests](#running-integration-tests)
- [Code Coverage](#code-coverage)
- [Run Action Locally](#run-action-locally)
- [Branch Naming Convention (PID:H-1)](#branch-naming-convention-pidh-1)

## Get Started

Clone the repository and navigate to the project directory:

```shell
git clone https://github.com/AbsaOSS/generate-release-notes.git
cd generate-release-notes
```

Python versions:
- **Runtime:** this checkout supports Python 3.11 and newer; `action.yml` rejects older interpreters.
- **Local development and testing:** Python 3.14 matches the quality-gate job.
  CI also runs unit and offline integration tests on both 3.11 and 3.14.
- Ruff (`target-version`) and mypy (`python_version`) are configured for 3.11,
  which helps catch some version-specific incompatibilities even when run on 3.14. These tools do not guarantee
  runtime compatibility with every standard-library API; CI also runs tests on Python 3.11.

Set up the development environment:

```shell
python3 -m venv .venv
source .venv/bin/activate
make install
```

## Quality Gates

Ruff combines linting, import sorting, formatting, security checks, and complexity checks. The configuration is in
[pyproject.toml](pyproject.toml), and the [Makefile](Makefile) provides the same commands used by the
[pull-request workflow](.github/workflows/test.yml).

Run the complete local gate from the repository root:

```shell
make qa
```

`make qa` runs unit tests with the 80% coverage threshold, Ruff format and lint checks, mypy, and `pip-audit`.
The dependency audit queries the vulnerability database and therefore requires network access.

Use `make format` to apply Ruff's safe fixes and formatting. Individual targets include `make lint`,
`make format-check`, `make types`, `make test`, `make coverage`, and `make audit`.

## Running Unit Tests

Unit tests are written using pytest. To run the tests, use the following command:

```shell
make test
```

This will execute all tests located in the tests/unit directory.

## Running Integration Tests

The integration suite exercises the full pipeline from `main.run()` to final markdown output without reaching the GitHub API.

**Offline tests** (under `tests/integration/`) replace the GitHub API layer with mocks and run in CI on every PR — no token required, fully deterministic.
**Live tests** (under `tests/integration/live/`) call the real GitHub API against the `AbsaOSS/generate-release-notes` repository. Run these manually to verify network-dependent behaviour such as `BulkSubIssueCollector`, or to confirm that API changes have not broken the integration. They are skipped in CI on fork PRs where the token is unavailable.

### Design concept

Each test calls `main.run()` directly with `INPUT_*` environment variables. The GitHub API layer is replaced by mocks; `DataMiner.mine_data()` is patched to return a hand-crafted `MinedData`. All other pipeline components — `FilterByRelease`, `DefaultRecordFactory`, `ReleaseNotesBuilder`, `CustomChapters`, and `ServiceChapters` — execute as real code.

### Key components

| Component | Location | Role |
|---|---|---|
| Fixture factories | `conftest.py` | `make_issue`, `make_pr`, `make_commit`, `make_repo`, `make_release` — typed mocks with minimal required attributes |
| `build_mined_data()` | `helpers.py` | Assembles a `MinedData` from fixture objects for injection into the pipeline |
| `capture_run()` | `helpers.py` | Sets env vars, calls `main.run()`, parses the GitHub Actions output format back to a plain string |
| Golden snapshot | `fixtures/test_full_pipeline_snapshot.md` | Byte-for-byte reference output for `T-INT-01` |

### Run offline tests (no token needed)

Runs all integration tests except the live suite; safe to run locally and in CI.

```shell
pytest tests/integration/ --ignore=tests/integration/live -v
```

### Regenerate golden snapshot

Re-runs the full-pipeline snapshot test and overwrites `fixtures/test_full_pipeline_snapshot.md` with the current output. Use this after intentional output changes to update the baseline.

```shell
WRITE_SNAPSHOTS=1 pytest tests/integration/test_snapshot.py::test_full_pipeline_snapshot
```

### Live smoke test (requires `GITHUB_TOKEN`)

Queries the real GitHub API against `AbsaOSS/generate-release-notes` to verify `BulkSubIssueCollector`. Skipped in CI on fork PRs.

```shell
pytest tests/integration/live/ -v
```

## Code Coverage

Code coverage is collected using pytest-cov. Run the unit suite with the 80% coverage threshold:

```shell
make coverage
```

To generate an HTML coverage report:

```shell
make coverage-html
```

Open the report at:

```shell
open htmlcov/index.html
```

## Run Action Locally
Create run_locally.sh file and place it in the project root. Use Python 3.11 or newer.

```bash
#!/bin/bash

# Set environment variables based on the action inputs
export INPUT_TAG_NAME="v0.2.0"

export INPUT_CHAPTERS='[
{ title: No entry 🚫, label: duplicate },
{ title: Breaking Changes 💥, label: breaking-change },
{ title: New Features 🎉, label: enhancement },
{ title: New Features 🎉, label: feature },
{ title: Bugfixes 🛠, label: bug },
{ title: Infrastructure ⚙️, label: infrastructure },
{ title: Silent-live 🤫, label: silent-live },
{ title: Documentation 📜, label: documentation }
]'
export INPUT_WARNINGS="true"
export INPUT_PUBLISHED_AT="true"
export INPUT_SKIP_RELEASE_NOTES_LABELS="ignore-in-release"
export INPUT_PRINT_EMPTY_CHAPTERS="true"
export INPUT_VERBOSE="true"

# CI in-built variables
export GITHUB_REPOSITORY="< owner >/< repo-name >"
export INPUT_GITHUB_TOKEN=$(printenv <your-env-token-var>)

PROJECT_ROOT="$(pwd)"
export PYTHONPATH="${PYTHONPATH}:${PROJECT_ROOT}"

# Debugging statements
echo "PYTHONPATH: ${PYTHONPATH}"
echo "Current working directory: ${PROJECT_ROOT}"

# Run the Python script
python3 ./<path-to-action-project-root>/main.py
```

## Branch Naming Convention (PID:H-1)
All work branches MUST use an allowed prefix followed by a concise kebab-case descriptor (optional numeric ID):
Allowed prefixes:
- feature/ : new functionality & enhancements
- fix/     : bug fixes / defect resolutions
- docs/    : documentation-only updates
- chore/   : maintenance, CI, dependency bumps, non-behavioral refactors
Examples:
- feature/add-hierarchy-support
- fix/456-null-title-parsing
- docs/update-readme-quickstart
- chore/upgrade-pygithub
Rules:
- Prefix mandatory; rename non-compliant branches before PR (`git branch -m feature/<new-name>` etc.).
- Descriptor lowercase kebab-case; hyphens only; avoid vague terms (`update`, `changes`).
- Align scope: a docs-only PR MUST use docs/ prefix, not feature/.
Verification Tip:
```shell
git rev-parse --abbrev-ref HEAD | grep -E '^(feature|fix|docs|chore)/' || echo 'Branch naming violation (expected allowed prefix)'
```
Future possible prefixes (not enforced yet): `refactor/`, `perf/`.
