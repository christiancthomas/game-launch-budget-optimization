# Game Launch Budget Optimization - Makefile
# A handy build automation tool to make setup, running, and testing easier!
# Activates venv and defines setup, baseline, test targets

.PHONY: help setup test baseline clean lint format check-venv

# Default target
help:
	@echo "Available targets:"
	@echo "  setup     - Creates venv, installs dependencies, and sets up pre-commit hooks"
	@echo "  test      - Runs all tests"
	@echo "  baseline  - Generates synthetic data and runs optimization pipeline"
	@echo "  lint      - Runs linting checks"
	@echo "  format    - Formats code with black and ruff"
	@echo "  clean     - Removes virtual environment and cache files"

# Check if virtual environment exists and is activated
check-venv:
	@if [ ! -d "venv" ]; then \
		echo "Virtual environment not found. Run 'make setup' first."; \
		exit 1; \
	fi

# Setup target: this creates venv, installs deps, and sets up pre-commit
setup:
	@echo "🛠️ Setting up development environment..."
	python3 -m venv venv
	@echo "📦 Installing dependencies..."
	venv/bin/pip install --upgrade pip
	venv/bin/pip install -r requirements.txt
	venv/bin/pip install pytest pre-commit black ruff
	@echo "🪝 Installing pre-commit hooks..."
	venv/bin/pre-commit install
	@echo "✅ Setup complete! Virtual environment ready at venv/"
	@echo "💡 For developers, activate the virtual environment with:"
	@echo "   source venv/bin/activate"

# Test target: Run pytest
test: check-venv
	@echo "🧪 Running tests..."
	venv/bin/python -m pytest tests/ -v

# Baseline target: Run synth -> optimize pipeline
baseline: check-venv
	@echo "🎯 Running baseline optimization pipeline..."
	@echo "📊 Step 1: Generating synthetic channel data..."
	venv/bin/python -m src.cli synth
	@echo "🚀 Step 2: Running budget optimization..."
	venv/bin/python -m src.cli optimize --output data/processed/optimization_results.csv
	@echo "✅ Baseline pipeline complete!"
	@echo "📄 Results saved to data/processed/optimization_results.csv"

# Linting target
lint: check-venv
	@echo "🔍 Running linting checks..."
	venv/bin/ruff check src/ tests/
	venv/bin/black --check src/ tests/
	@echo "✅ Linting complete!"

# Format target
format: check-venv
	@echo "✨ Formatting code..."
	venv/bin/black src/ tests/
	venv/bin/ruff check --fix src/ tests/
	@echo "✅ Code formatted successfully!"

# Clean target: Remove venv and cache
clean:
	@echo "🧹 Cleaning up..."
	rm -rf venv
	rm -rf __pycache__
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -name "*.pyc" -delete
	@echo "✅ Cleanup complete!"
