import os
import subprocess
import sys
from pathlib import Path

import pytest


POSTGRES_TEST_URL = os.getenv("AGENTSEC_TEST_POSTGRES_URL")


@pytest.mark.skipif(not POSTGRES_TEST_URL, reason="AGENTSEC_TEST_POSTGRES_URL is not configured")
def test_full_api_flow_against_postgresql(tmp_path):
    """Run the API flow in a fresh interpreter so database settings cannot leak from SQLite tests."""
    backend = Path(__file__).resolve().parents[1]
    environment = os.environ.copy()
    environment["DATABASE_URL"] = POSTGRES_TEST_URL
    environment.pop("AGENTSEC_DATABASE_PATH", None)
    environment["PYTHONPATH"] = str(backend)
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(backend / "tests" / "test_api.py"), "-q"],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
