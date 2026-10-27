"""Load project settings and resolve paths relative to the repository root."""

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "project_config.json"


def load_config():
    """Read the editable JSON settings file."""
    with CONFIG_PATH.open(encoding="utf-8") as config_file:
        return json.load(config_file)


def project_path(config_key):
    """Return a configured project path as an absolute Path."""
    relative_path = load_config()["paths"][config_key]
    return PROJECT_ROOT / relative_path


def ensure_project_directories():
    """Create configured output folders when they are missing."""
    config = load_config()
    project_path("figures_directory").mkdir(parents=True, exist_ok=True)
    for key in (
        "clean_transactions",
        "data_quality_summary",
        "customer_rfm",
        "segment_summary",
        "category_performance",
        "category_priority",
        "report",
    ):
        project_path(key).parent.mkdir(parents=True, exist_ok=True)
