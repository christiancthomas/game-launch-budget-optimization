# Game Launch Marketing Budget Optimization

![CI](https://github.com/christiancthomas/game-launch-budget-optimization/actions/workflows/pr-check.yml/badge.svg) ![Python](https://img.shields.io/badge/python-3.13%2B-blue)

## Problem Statement

Game launches often involve a flurry of marketing activity across multiple
channels: search, social, video, influencer, and more. Deciding how to allocate
limited marketing budgets among these channels will have a significant impact on
overall conversions and revenue. Without a structured approach, budget
allocation decisions may rely on intuition or historical habits, which can lead
to suboptimal results (unrealized ROI, lost revenue, poor ad spend, etc.).

I used quadratic programming methods here to determine the optimal
allocation of marketing budgets across channels. By modeling diminishing
returns, budget constraints, and channel-specific caps, you can theoretically
maximize conversions (or revenue).

This project is still in a prototype stage. If you're using this for real budget
decisions, you should definitely validate the response curves against your
historical data first. The default parameters are based on what I've seen in gaming but YMMV.

🎮

## Business Context

In the gaming industry, budgets are limited. So every dollar counts. Game
publishers and marketing teams need to:

1. Justify spend allocation with data-driven reasoning

2. Adapt budgets dynamically as performance data changes

3. Understand the marginal return of each channel at different spend levels

By providing a reproducible, optimization-based framework, this project gives
launch teams a defensible and flexible tool for maximizing impact while staying
within operational and financial limits.

**For marketing teams, this tool provides:**

1. **Data-driven budget allocation** replacing gut instinct with mathematical optimization
2. (TODO) **Sensitivity analysis** showing trade-offs between channels
3. **Scalable framework** adaptable to different budget levels and channel mixes

### Quick Start

I used a Makefile as a wrapper for commonly bundled commands because this is simpler for me (and users, I assume). I've provided instructions based on that usage below. You can always run the python commands directly if preferred.

1. **Clone the repository:**

   ```bash
   git clone https://github.com/christiancthomas/game-launch-budget-optimization.git
   cd game-launch-budget-optimization
   ```

2. **Set up the development environment:**

   ```bash
   make setup
   ```

   This will:
   - Create a virtual environment (`venv`)
   - Install all dependencies from `requirements.txt`
   - Install development tools (pytest, pre-commit, black, ruff)
   - Set up pre-commit hooks for code quality
   - Create the project directory structure

3. **Run the complete optimization pipeline:**

   ```bash
   # Generate synthetic data and run optimization
   make baseline
   ```

   **Example output:**

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

4. **Run tests to validate everything works:**

   ```bash
   make test
   ```

5. **(for development work only) Activate the virtual environment:**

   ```bash
   source venv/bin/activate
   ```

   This step is only needed for development work (running scripts directly, installing additional packages, etc.). The Makefile commands (`make test`,
   `make lint`, etc.) will work without activation since they are designed to
   use the virtual environment automatically.

### Prerequisites

- Python 3.13+ installed on your system
- Git (for cloning the repository)

## Current Status: V1 Complete! 🎉

Officially hit all the **V1 milestone goals**!

- **End-to-end optimization pipeline** from synthetic data to optimal budget allocation
- **Production-ready CLI tools** for data generation and optimization
- **Comprehensive test coverage** full integration test suite
- **Mathematical validation** of budget conservation, constraint satisfaction, and business logic
- **Quality controls** with pre-commit hooks, linting, and enforcement of a consistent style

Future updates will focus on adding more advanced features to handle more complex scenarios.

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

### Other Useful Commands

- `make help` - see all available commands
- `make test` - runs test suite
- `make synth` - generates synthetic channel data
- `make baseline` - generates sample data and runs optimization
- `make lint` - checks code quality using `ruff` and `black` (for developers)
- `make format` - auto-formats code (for developers)
- `make clean` - cleans up virtual environment and cache files

## Methodology

The solution combines a few key mathematical concepts:

- **Mathematical Optimization**: Quadratic programming (QP) to handle non-linear diminishing returns
- **Synthetic Data Modeling**: Realistic channel performance simulation based on industry metrics
- **Statistical Curve Fitting**: Quadratic functions (`conversions = a*spend - b*spend²`) to model channel saturation effects
- **Constraint Handling**: Budget limits, minimum spend requirements, and channel capacity bounds

### Mathematical Framework

The optimization problem can be modeled as:

```text
Maximize: Σᵢ (aᵢ*xᵢ - bᵢ*xᵢ²)  [Total conversions across all channels]

Subject to:
- Σᵢ xᵢ = Budget                 [Budget constraint]
- min_spendᵢ ≤ xᵢ ≤ max_spendᵢ   [Channel capacity bounds]
- xᵢ ≥ 0                         [Can't spend negative budget]
```

Where:

- `xᵢ` = spend allocated to channel i
- `aᵢ` = initial efficiency (conversions per dollar)
- `bᵢ` = diminishing returns coefficient

This quadratic formulation captures the economic reality that additional spend yields progressively fewer returns due to audience saturation and increased competition. Linear programming methods strictly won't work here because it doesn't capture the diminishing returns effect at higher spends.

## Project Structure

```tree
src/                 # Main code
├── config/          # YAML configuration and loading
├── data/            # Sample data & outputs
├── features/        # Mathematical curve modeling
├── opt/             # Quadratic programming solver
├── viz/             # Generated visualizations
└── cli.py           # Command line interface

tests/
data/                # Generated datasets and results
experiments/         # jupyter notebooks
```

## Limitations and Next Steps

This version is a first pass meant to set up the framework. There are some notable simplifications that I relied on and are areas I’d like to expand on in future versions:

- **Data realism** – The current dataset uses synthetic values. That makes it easy to test and develop on, but limits how realistic the outputs are compared to actual campaign performance. I'm working on a future version that will use historical spend/conversion data (with sufficient anonymization/jitter) to validate the model.
- **Solver choice** – I used SciPy’s SLSQP solver because it's easily accessible and handles both bounds and constraints directly, which maps well to this version of the problem. It’s quick to run in a small python script and works fine with a nonlinear objective. The tradeoff is that SLSQP is a local solver, so results depend on scaling and starting values. Future work might test alternatives like CVXPy or mixed-integer approaches if the problem expands significantly in scale.
- **Modeling depth** – The optimization logic makes some straightforward assumptions. Future iterations could test alternative approaches like nonlinear constraints, geo-based consideration, Bayesian methods, or ML-based forecasting.
- **Granularity** – Right now the scope is at the channel level. Adding geo-level or sub-channel (Meta-FB / Meta-IG, Google-search / Google-YT, etc.) optimization would make the outputs more actionable.
- **Usability** – Everything runs through a the console at this stage. A lightweight dashboard, notebooke, or simple interface would make it easier for others to tweak inputs and run scenarios.

The goal for v1 was to build something clear and working, not final. These notes are here to mark where the project can grow.

### Next Steps (V1.1?)

- **Visualizations**: Graphical representations showing allocation breakdowns and potentially sensitivity analysis (likely via notebook usage)
- **Results Analysis**: Enhanced CLI output with deeper reporting such as efficiency ranking and detailed ROI metrics
- **Real Data Integration**: Leverage realistic data for more useful analysis

### Potential V2 Ideas

- **Advanced Response Curves**: More advanced response curves for more sophisticated modeling should theoretically be more realistic, but need to test this beyond synthetic data
- **Sensitivity Analysis**: A more robust sensitivity analysis could better inform decision making and support "what-if" analyses
- **Seasonality Modeling**: How does time of year, week, or day impact the results? Gaming is incredibly seasonal and it's expected that this could impact real-world results
- **Interactive Scenario Planning**: Interactive features for exploratory analysis
