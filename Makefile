# Copyright 2023 ABSA Group Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

PYTHON ?= python3
PIP ?= $(PYTHON) -m pip
COV_MIN ?= 80

.DEFAULT_GOAL := help
.PHONY: help all install qa format format-check lint types test test-integration coverage coverage-html audit

help: ## Show available targets.
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  %-18s %s\n", $$1, $$2}'

all: install qa ## Install dependencies and run the full local quality gate.

install: ## Install runtime and development dependencies.
	$(PIP) install -r requirements-dev.txt

qa: coverage format-check lint types audit ## Run the full local quality gate.

format: ## Apply Ruff fixes and format Python code.
	ruff check --fix .
	ruff format .

format-check: ## Check Python formatting without modifying files.
	ruff format --check .

lint: ## Run Ruff lint, security, and complexity checks.
	ruff check .

types: ## Run the mypy type checker.
	mypy .

test: ## Run the unit test suite.
	pytest -v tests/unit

test-integration: ## Run the offline integration tests (no GitHub token needed).
	pytest -v tests/integration/ --ignore=tests/integration/live

coverage: ## Run unit tests with the coverage threshold.
	pytest --cov=. -v tests/unit --cov-fail-under=$(COV_MIN)

coverage-html: ## Run unit tests with coverage and generate an HTML report.
	pytest --cov=. -v tests/unit --cov-fail-under=$(COV_MIN) --cov-report=html

audit: ## Audit runtime and development dependencies for known vulnerabilities.
	pip-audit -r requirements-dev.txt
