from pathlib import Path
import shutil
import pytest


@pytest.fixture
def journal_fixture_path() -> Path:
    """Path to the journal.xlsx fixture file."""
    return Path("tests/fixtures/journal.xlsx")

@pytest.fixture(scope="session")
def output_dir() -> Path:
    """
    Retourne le chemin vers le dossier de sortie pour les tests.
    """
    return Path(__file__).parent / "output"

@pytest.fixture(scope="session", autouse=True)
def clear_output_folder(output_dir: Path):
    """
    Avant la session pytest : supprime puis recrée tests/output
    pour que le dossier soit toujours vide au début.
    """
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)