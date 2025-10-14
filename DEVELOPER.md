# Generate Release Notes Action—for Developers

- [Get Started](#get-started)
- [Run Static Code Analysis](#running-static-code-analysis)
- [Run Black Tool Locally](#run-black-tool-locally)
- [Run mypy Tool Locally](#run-mypy-tool-locally)
- [Run Unit Test](#running-unit-test)
- [Run Action Locally](#run-action-locally)

## Get Started

Clone the repository and navigate to the project directory:

```shell
git clone https://github.com/AbsaOSS/generate-release-notes.git
cd generate-release-notes
```

Install the dependencies:

```shell
pip install -r requirements.txt
export PYTHONPATH=<your path>/generate-release-notes/src
```

## Running Static Code Analysis

This project uses the Pylint tool for static code analysis. Pylint analyzes your code without actually running it. It checks for errors, enforces coding standards, looks for code smells, etc.

Pylint displays a global evaluation score for the code, rated out of a maximum score of 10.0. We aim to keep our code quality above 9.5.

### Set Up Python Environment
```shell
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

This command will also install a Pylint tool, since it is listed in the project requirements.

### Run Pylint
Run Pylint on all files currently tracked by Git in the project.
```shell
pylint $(git ls-files '*.py')
```

To run Pylint on a specific file, follow the pattern `pylint <path_to_file>/<name_of_file>.py`.

Example:
```shell
pylint release-notes-generator/generator.py
``` 

## Run Black Tool Locally
This project uses the [Black](https://github.com/psf/black) tool for code formatting.
Black aims for consistency, generality, readability, and reducing git diffs.
The coding style used can be viewed as a strict subset of PEP 8.

The project root file `pyproject.toml` defines the Black tool configuration.
In this project, we are accepting a line length of 120 characters.

Follow these steps to format your code with Black locally:

### Set Up Python Environment
From the terminal in the root of the project, run the following command:

```shell
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

This command will also install a Black tool, since it is listed in the project requirements.

### Run Black
Run Black on all files currently tracked by Git in the project.
```shell
black $(git ls-files '*.py')
```

To run Black on a specific file, follow the pattern `black <path_to_file>/<name_of_file>.py`.

Example:
```shell
black release_notes_generator/generator.py
``` 

### Expected Output
This is the console's expected output example after running the tool:
```
All done! ✨ 🍰 ✨
1 file reformatted.
```


## Run mypy Tool Locally

This project uses the [my[py]](https://mypy.readthedocs.io/en/stable/) tool, a static type checker for Python.

> Type checkers help ensure that you correctly use variables and functions in your code.
> With mypy, add type hints (PEP 484) to your Python programs,
> and mypy will warn you when you use those types incorrectly.
my[py] configuration is in `pyproject.toml` file.

Follow these steps to format your code with my[py] locally:

### Run my[py]

Run my[py] on all files in the project.
```shell
  mypy .
```

To run my[py] check on a specific file, follow the pattern `mypy <path_to_file>/<name_of_file>.py --check-untyped-defs`.

Example:
```shell
   mypy living_documentation_regime/living_documentation_generator.py
``` 


## Running Unit Test

Unit tests are written using pytest. To run the tests, use the following command:

```shell
pytest tests/unit
```

This will execute all tests located in the tests directory.

## Code Coverage

Code coverage is collected using the pytest-cov coverage tool. To run the tests and collect coverage information, use the following command:

```shell
pytest --cov=. -v tests/unit --cov-fail-under=80                      # Check coverage threshold
pytest --cov=. -v tests/unit --cov-fail-under=80 --cov-report=html    # Generate HTML report
```

This will execute all tests in the tests directory and generate a code coverage report.

See the coverage report on the path:

```shell
open htmlcov/index.html
```

## Run Action Locally
Create run_locally.sh file and place it in the project root.

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

# Run the Python script
python3 ./<path-to-action-project-root>/main.py
```

## Branch Naming Convention (Principle 13)
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
