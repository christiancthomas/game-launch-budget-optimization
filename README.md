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
- **Quadratic Programming Solver** (`src/opt/solve.py`) using SciPy SLSQP optimization
- **Complete CLI interface** (`src/cli.py`) with `synth` and `optimize` commands
- **Comprehensive test suite** (30 tests) including end-to-end integration validation

## Current Status: V1 Complete! 🎉

This repository has achieved its **V1 milestone goals**:

✅ **End-to-end optimization pipeline** from synthetic data to optimal budget allocation
✅ **Production-ready CLI tools** for data generation and optimization
✅ **Comprehensive test coverage** full integration test suite
✅ **Mathematical validation** of budget conservation, constraint satisfaction, and business logic
✅ **Quality controls** with pre-commit hooks, linting, and enforcement of a consistent style

Future updates will focus on adding more advanced features.

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

3. **Activate the virtual environment (for development work only):**

   ```bash
   source venv/bin/activate
   ```

   This step is needed for development work (running scripts, interactive
   Python, installing additional packages). The Makefile commands (`make test`,
   `make lint`, etc.) will work without activation since they are designed to
   use the virtual environment automatically.

4. **Run the complete optimization pipeline:**

   ```bash
   # Generate synthetic data and run optimization
   make baseline
   ```

5. **Run tests to validate everything works:**

   ```bash
   make test
   ```

### CLI Commands Reference

**Basic Commands:**

```bash
# Generate synthetic data
python -m src.cli synth [--config CONFIG_FILE] [--out OUTPUT_CSV]

# Run optimization
python -m src.cli optimize [--benchmarks CSV_FILE] [--budget AMOUNT] [--output RESULTS_CSV]

# Or use Makefile shortcuts
make synth      # Generate data only
make baseline   # Generate data + run optimization
```

**What You'll See:**

```text
🚀 Running budget optimization...
💰 Total budget: $100000.0
📊 Optimizing 5 channels...

✅ OPTIMIZATION COMPLETE!
OPTIMAL ALLOCATION:
Channel         | Spend    | Conversions  | CPA
------------------------------------------------------------
google          | $   6537 |     157 conv | $   42 CPA
meta            | $  35000 |    1408 conv | $   25 CPA
tiktok          | $  20005 |     545 conv | $   37 CPA
reddit          | $  25000 |    1091 conv | $   23 CPA
x               | $  13458 |     600 conv | $   22 CPA
------------------------------------------------------------
TOTAL           | $ 100000 |    3801 conv | $   26 CPA

Budget utilization: 100.0%
```

### Other Useful Commands

- `make help` - See all available commands
- `make test` - Run test suite
- `make synth` - Generate synthetic channel data
- `make baseline` - Run complete synth → optimize pipeline
- `make lint` - Check code quality using `ruff` and `black`
- `make format` - Auto-format code
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

**This quadratic formulation captures the economic reality that additional spend yields progressively fewer returns due to audience saturation and increased competition.**

## Project Structure

```text
src/
├── config/          # YAML configuration and loading
├── data/            # Synthetic data generation
├── features/        # Mathematical curve modeling
├── opt/             # Quadratic programming solver
├── viz/             # Visualization (future)
└── cli.py           # Command-line interface

tests/               # comprehensive testing to ensure stability
data/                # Generated datasets and results
experiments/         # Analysis outputs
```

## Limitations and Next Steps  

This version is a first pass meant to set up the framework. There are some notable simplifications / limitations I relied on and could be areas I’d like to expand on in future versions:  

- **Data realism** – The current dataset uses simplified or synthetic values. That makes it easy to test and share, but limits how realistic the outputs are compared to actual campaign performance. A future version could pull in historical spend/outcome data (with anonymization) to validate the model.  
- **Solver choice** – I used SciPy’s SLSQP solver because it handles both bounds and constraints directly, which maps well to this version of the problem. It’s quick to run in a small python script and works fine with a nonlinear objective. The tradeoff is that SLSQP is a local solver, so results depend on scaling and starting values. Future work might test alternatives like CVXPy or mixed-integer approaches if the problem expands.
- **Modeling depth** – The optimization logic makes some straightforward assumptions. Future iterations could test alternative approaches like nonlinear constraints, geo-based consideration, Bayesian methods, or ML-based forecasting.  
- **Granularity** – Right now the scope is at the channel level. Adding geo-level or sub-channel (Meta-FB / Meta-IG, Google-search / Google-YT, etc.) optimization would make the outputs more actionable.  
- **Usability** – Everything runs through a the console at this stage. A lightweight dashboard, notebooke, or simple interface would make it easier for others to tweak inputs and run scenarios.  

The goal for v1 was to build something clear and working, not final. These notes are here to mark where the project can grow.  

**V1.1 Next Steps:**

- **Visualizations**: Graphical representations showing allocation breakdowns and potentially sensitivity analysis (likely via notebook usage)
- **Results Analysis**: Enhanced CLI output with channel efficiency rankings and ROI insights
- **Real Data Integration**: Leverage realistic data for more useful analysis

**V2 Advanced Features:**

- **Advanced Response Curves**: Hill/logistic curves for more sophisticated modeling -- theoretically more realistic
- **Multi-Objective Optimization**: Optimize for multiple KPIs (conversions, DLC purchases, reactivations, etc.)
- **Sensitivity Analysis**: Budget sweep analysis and constraint shadow pricing
- **Seasonality Modeling**: Time-based demand curves and budget allocation over campaign periods
- **Interactive Scenario Planning**: Interactive features for marketing teams to explore "what-if" scenarios
