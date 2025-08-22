# Game Launch Marketing Budget Optimization

## Problem summary

Game launches often involve a flurry of marketing activity across multiple
channels: search, social, video, influencer, and more. Deciding how to allocate
limited marketing budgets among these channels can have a significant impact on
overall conversions and revenue. Without a structured approach, budget
allocation decisions may rely on intuition or historical habits, which can lead
to suboptimal results.

This project uses linear and quadratic programming to determine the optimal
allocation of marketing budgets across channels. By modeling diminishing
returns, budget constraints, and channel-specific caps, it aims to maximize
conversions (or revenue) while providing transparency into trade-offs and
sensitivity to changes.

## Business context

In a competitive launch environment, every marketing dollar counts. Game
publishers and marketing teams need to:

1. Justify spend allocation with data-driven reasoning

2. Adapt budgets dynamically as performance data changes

3. Understand the marginal return of each channel at different spend levels

By providing a reproducible, optimization-based framework, this project gives
launch teams a defensible and flexible tool for maximizing impact while staying
within operational and financial limits.

## Current status

This repository is in its initial setup phase. The core problem framing and
business context are defined, and the next steps will involve:

- Generating synthetic data to mimic realistic launch scenarios

- Fitting channel response curves with diminishing returns

- Building optimization models and running baseline allocation scenarios

## Placeholders for future sections

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

4. **Verify the setup:**

   ```bash
   make test
   ```

### Other Useful Commands

- `make help` - See all available commands
- `make lint` - Check code quality
- `make format` - Auto-format code
- `make baseline` - Run optimization pipeline (coming in future milestones)
- `make clean` - Clean up virtual environment and cache files

### Data dictionary: Explanation of dataset fields

### Methods: Detailed description of LP vs QP approach

### Results: Visualizations and sensitivity analysis findings

### Why it matters: Key takeaways for marketing decision-makers
