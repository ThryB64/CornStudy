SHELL := /usr/bin/env bash
.SHELLFLAGS := -Eeuo pipefail -c
.DEFAULT_GOAL := help

PYTHON ?= python3
VENV ?= venv
ACTIVATE = source $(VENV)/bin/activate
PIP = $(VENV)/bin/pip
PY = $(VENV)/bin/python

# ----------------------------------------------------------------------
# Setup
# ----------------------------------------------------------------------

.PHONY: help
help:
	@echo "Mais project - unified pipeline"
	@echo ""
	@echo "  make venv             Create virtualenv and install package + collectors"
	@echo "  make install-dev      Install dev dependencies (tests, lint)"
	@echo "  make install-ml       Install ML dependencies (lgbm, xgb, catboost, ...)"
	@echo "  make install-ui       Install Streamlit UI dependencies"
	@echo ""
	@echo "  make collect          Phase 1: download all raw sources"
	@echo "  make clean-data       Phase 1: clean raw -> interim"
	@echo "  make features         Phase 1: build features.parquet from interim"
	@echo "  make targets          Phase 1: build targets.parquet (y_logret_h{5,10,20,30})"
	@echo "  make audit            Phase 1: anti-leakage audit (FAIL-FAST)"
	@echo "  make data             Phase 1: collect + clean + features + targets + audit"
	@echo ""
	@echo "  make train            Phase 3: smoke-train default model (ridge_reg)"
	@echo "  make train-all        Phase 3: train all registry models (long run)"
	@echo "  make stack            Phase 3: build meta-database + stacking"
	@echo "  make backtest         Phase 2: agronomic backtest (sell/store/wait)"
	@echo "  make factors          Phase 2: build economic factors"
	@echo "  make factor-analysis  Phase 2: regenerate factors + factor report"
	@echo "  make study            Phase 2: professional corn price study"
	@echo "  make ui               Launch Streamlit dashboard"
	@echo ""
	@echo "  make test             Run unit + integration tests"
	@echo "  make lint             ruff check + mypy"
	@echo "  make format           ruff format"
	@echo ""
	@echo "  make migrate-legacy   One-shot: convert old csv/corrige/* into data/interim/*.parquet"
	@echo "  make clean-cache      Remove __pycache__, .pytest_cache, .ruff_cache"

$(VENV)/bin/activate:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install -q --upgrade pip setuptools wheel
	$(PIP) install -q -e ".[collect]"

.PHONY: venv
venv: $(VENV)/bin/activate

.PHONY: install-dev install-ml install-ui install-all
install-dev: venv
	$(PIP) install -q -e ".[dev]"
install-ml: venv
	$(PIP) install -q -e ".[ml]"
install-ui: venv
	$(PIP) install -q -e ".[ui]"
install-all: venv
	$(PIP) install -q -e ".[collect,ml,ui,dev,api]"

# ----------------------------------------------------------------------
# Phase 1: Data pipeline
# ----------------------------------------------------------------------

.PHONY: collect clean-data features targets audit data

collect: venv
	$(PY) -m mais.cli collect all

clean-data: venv
	$(PY) -m mais.cli clean

features: venv
	$(PY) -m mais.cli features

targets: venv
	$(PY) -m mais.cli targets

audit: venv
	$(PY) -m mais.cli audit-leakage

data: collect clean-data features targets audit
	@echo "Data pipeline OK -> data/processed/{features,targets}.parquet"

migrate-legacy: venv
	$(PY) -m mais.cli migrate-legacy

# ----------------------------------------------------------------------
# Phase 3: Training & evaluation
# ----------------------------------------------------------------------

.PHONY: train train-all stack backtest factors factor-analysis study ui

train: venv
	$(PY) -m mais.cli train --model ridge_reg --target y_logret_h20 --trials 20

train-all: venv
	$(PY) -m mais.cli train --all

stack: venv
	$(PY) -m mais.cli stack

backtest: venv
	$(PY) -m mais.cli backtest

factors: venv
	$(PY) -m mais.cli factors

factor-analysis: venv
	$(PY) scripts/run_factor_analysis.py

study: venv
	$(PY) -m mais.cli study

ui: install-ui
	$(VENV)/bin/streamlit run src/mais/ui/app.py

# ----------------------------------------------------------------------
# Tests / quality
# ----------------------------------------------------------------------

.PHONY: test lint format clean-cache

test: install-dev
	$(VENV)/bin/pytest

lint: install-dev
	$(VENV)/bin/ruff check src tests
	-$(VENV)/bin/mypy src

format: install-dev
	$(VENV)/bin/ruff format src tests
	$(VENV)/bin/ruff check --fix src tests

clean-cache:
	find . -type d \( -name __pycache__ -o -name .pytest_cache -o -name .ruff_cache -o -name .mypy_cache \) -exec rm -rf {} + 2>/dev/null || true
