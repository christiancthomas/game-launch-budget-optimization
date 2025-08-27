# Game Launch Marketing Budget Optimization

![CI](https://github.com/christiancthomas/game-launch-budget-optimization/actions/workflows/pr-check.yml/badge.svg) ![Python](https://img.shields.io/badge/python-3.13%2B-blue)

## Problem Statement

Game launches often involve a flurry of marketing activity across multiple
channels: search, social, video, influencer, and more. Deciding how to allocate
limited marketing budgets among these channels will have a significant impact on
overall conversions and revenue. Without a structured approach, budget
allocation decisions may rely on intuition or historical habits, which can lead
to suboptimal results (unrealized ROI, lost revenue, poor ad spend, etc.).

This project uses quadratic programming to determine the optimal
allocation of marketing budgets across channels. By modeling diminishing
returns, budget constraints, and channel-specific caps, it aims to maximize
conversions (or revenue) while providing transparency into trade-offs and
sensitivity to changes.

## Business Context

In a competitive launch environment, every marketing dollar counts. Game
publishers and marketing teams need to:

1. Justify spend allocation with data-driven reasoning

2. Adapt budgets dynamically as performance data changes

3. Understand the marginal return of each channel at different spend levels

By providing a reproducible, optimization-based framework, this project gives
launch teams a defensible and flexible tool for maximizing impact while staying
within operational and financial limits.

### Business Impact

For marketing teams, this provides:

1. **Data-driven budget allocation** replacing gut instinct with mathematical optimization
2. **Sensitivity analysis** showing trade-offs between channels
3. **Scalable framework** adaptable to different budget levels and channel mixes

## Technical Approach

The solution combines several key concepts:

- **Mathematical Optimization**: Quadratic programming (QP) to handle non-linear diminishing returns
- **Synthetic Data Modeling**: Realistic channel performance simulation based on industry metrics
- **Statistical Curve Fitting**: Quadratic functions (`conversions = a·spend - b·spend²`) to model channel saturation effects
- **Constraint Programming**: Budget limits, minimum spend requirements, and channel capacity bounds

### ✅ Core Data Infrastructure

- **Configuration system** (`src/config/`) with YAML-based parameter management
- **Synthetic data generation** (`src/data/synth.py`) with realistic channel characteristics
- **Mathematical curve modeling** (`src/features/curves.py`) for diminishing returns

## Current status

This repository is in its initial setup phase. The core problem framing and
business context are defined, and the next steps will involve:

- Generating synthetic data to mimic realistic launch scenarios

- Fitting channel response curves with diminishing returns

- Building optimization models and running baseline allocation scenarios

### 🚧 In Development

- **Quadratic Programming Solver**: SciPy-based optimizer for budget allocation
- **End-to-end CLI**: `optimize` command for complete pipeline execution
- **Results Visualization**: Matplotlib charts showing optimal allocations

### Quick start: How to install dependencies and run baseline optimization

## Getting Started

This project uses a Makefile to make getting started and development as easy as
possible.

### Prerequisites

- Python 3.13+ installed on your system
- Git (for cloning the repository)

### Quick Start

1. **Clone the repository:**

   ```bash
   git clone https://github.com/christiancthomas/game-launch-budget-optimization.git
   cd game-launch-budget-optimization
   ```

2. **Set up the development environment:**

   ```bash
   make setup
   ```

   This single command will:
   - Create a virtual environment (`venv`)
   - Install all dependencies from `requirements.txt`
   - Install development tools (pytest, pre-commit, black, ruff)
   - Set up pre-commit hooks for code quality
   - Create the project directory structure

3. **Activate the virtual environment:**

   ```bash
   source venv/bin/activate
   ```

   This step is needed for development work (running scripts, interactive
   Python, installing additional packages). The Makefile commands (`make test`,
   `make lint`, etc.) will work without activation since they are designed to
   use the virtual environment automatically.

4. **Generate synthetic data:**

   ```bash
   # Create realistic marketing channel benchmarks
   make synth
   ```

5. **Running tests:**

   ```bash
   make test
   ```

### Other Useful Commands

- `make help` - See all available commands
- `make lint` - Check code quality using `ruff` and `black`
- `make format` - Auto-format code
- `make baseline` - Run optimization pipeline
- `make clean` - Clean up virtual environment and cache files

## Mathematical Framework

The optimization problem can be modeled as:

```text
Maximize: Σᵢ (aᵢ·xᵢ - bᵢ·xᵢ²)  [Total conversions across all channels]

Subject to:
- Σᵢ xᵢ = Budget                 [Budget constraint]
- min_spendᵢ ≤ xᵢ ≤ max_spendᵢ   [Channel capacity bounds]
- xᵢ ≥ 0                         [Non-negativity]
```

Where:

- `xᵢ` = spend allocated to channel i
- `aᵢ` = initial efficiency (conversions per dollar)
- `bᵢ` = diminishing returns coefficient

This quadratic formulation captures the economic reality that additional spend yields progressively fewer returns due to audience saturation and increased competition.

## Project Structure

```text
src/
├── config/          # YAML configuration and loading
├── data/            # Synthetic data generation
├── features/        # Mathematical curve modeling
├── opt/             # Optimization solvers (in development)
└── viz/             # Visualization (in development)

tests/               # Comprehensive test suite
data/raw/            # Generated synthetic datasets
experiments/         # Results and analysis outputs
```

## Future Enhancements

**V1 Completion Goals:**

- Complete quadratic programming solver implementation
- End-to-end optimization pipeline with CSV output
- Basic visualizations
- Comprehensive documentation and examples

**V2 Advanced Features:**

- More advanced response curves for more sophisticated modeling
- Sensitivity and seasonality analysis
- Integration with real marketing attribution data
- Interactive tools for scenario planning
