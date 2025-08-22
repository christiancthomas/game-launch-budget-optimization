"""Config loading for budget optimization.

Loads YAML configs and does basic validation so the optimizer doesn't melt.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Any


def load_config(config_path: str):
    """Load config YAML and validate the important bits."""
    config_file = Path(config_path)

    if not config_file.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    with open(config_file) as f:
        try:
            config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Error parsing YAML file {config_path}: {e}")

    _validate_config(config)
    return config


def _validate_config(config: Dict[str, Any]):
    """Check that config has the stuff we need."""
    required = ["budget", "channels", "synth_data", "optimization", "output"]

    for section in required:
        if section not in config:
            raise ValueError(f"Missing '{section}' section in config")

    # Budget sanity check
    budget = config["budget"]["total"]
    if not isinstance(budget, (int, float)) or budget <= 0:
        raise ValueError("Budget must be > 0")

    # Channel validation
    channels = config["channels"]
    if not channels or not isinstance(channels, list):
        raise ValueError("Need at least one channel")

    for ch in channels:
        if not all(k in ch for k in ["name", "min_spend", "max_spend"]):
            raise ValueError(f"Channel {ch.get('name', '?')} missing required fields")

        if ch["min_spend"] < 0 or ch["max_spend"] <= ch["min_spend"]:
            raise ValueError(f"Invalid spend constraints for {ch['name']}")

    # Don't let min spends exceed budget (that would be awkward)
    total_min = sum(ch["min_spend"] for ch in channels)
    if total_min > budget:
        raise ValueError(f"Channel minimums ({total_min}) > budget ({budget})")


def get_channel_names(config: Dict[str, Any]) -> List[str]:
    """Channel names from config."""
    return [ch["name"] for ch in config["channels"]]


def get_channel_constraints(config: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
    """Min/max spend per channel."""
    return {
        ch["name"]: {"min_spend": ch["min_spend"], "max_spend": ch["max_spend"]}
        for ch in config["channels"]
    }


def get_total_budget(config: Dict[str, Any]) -> float:
    """Returns total budget as float."""
    return float(config["budget"]["total"])
