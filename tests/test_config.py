from pathlib import Path
from brightsidebudget.config.config import Config


def test_get_journal(config_fixture_path: Path):
    if not config_fixture_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_fixture_path}")
    config = Config.from_user_config(config_fixture_path)
    config.get_journal()