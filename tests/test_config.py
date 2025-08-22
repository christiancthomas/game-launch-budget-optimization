"""
Basic checks so we don't ship broken config loading.
"""

import pytest
import tempfile
import yaml
from pathlib import Path

from src.config.load import (
    load_config,
    get_channel_names,
    get_channel_constraints,
    get_total_budget,
)


@pytest.fixture
def sample_config():
    """Minimal config for testing."""
    return {
        "budget": {"total": 50000.0, "currency": "USD"},
        "channels": [
            {"name": "Google", "min_spend": 5000.0, "max_spend": 20000.0},
            {"name": "Meta", "min_spend": 3000.0, "max_spend": 15000.0},
        ],
        "synth_data": {"random_seed": 42, "cpc_range": [0.5, 3.0]},
        "optimization": {"solver": "scipy_minimize"},
        "output": {"results_dir": "experiments/results"},
    }


def test_config_loads_correctly(sample_config):
    """Test that basic config loading works."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(sample_config, f)
        f.flush()

        config = load_config(f.name)
        assert config["budget"]["total"] == 50000.0
        assert len(config["channels"]) == 2

        Path(f.name).unlink()


def test_missing_file_fails():
    """Should fail if config doesn't exist."""
    with pytest.raises(FileNotFoundError):
        load_config("nonsense.yaml")


def test_helper_functions(sample_config):
    """Helper functions extract the right stuff."""
    names = get_channel_names(sample_config)
    assert names == ["Google", "Meta"]

    constraints = get_channel_constraints(sample_config)
    assert "Google" in constraints
    assert constraints["Google"]["max_spend"] == 20000.0

    budget = get_total_budget(sample_config)
    assert budget == 50000.0


def test_real_default_config_works():
    """Our actual config should load fine."""
    config = load_config("src/config/default.yaml")

    # basic sanity
    assert config["budget"]["total"] > 0
    assert len(config["channels"]) > 0

    # helpers work too
    names = get_channel_names(config)
    budget = get_total_budget(config)
    assert len(names) > 0
    assert budget > 0
