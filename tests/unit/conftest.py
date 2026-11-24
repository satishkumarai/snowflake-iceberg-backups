import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def _cwd_repo_root():
    prev = os.getcwd()
    os.chdir(ROOT)
    yield
    os.chdir(prev)
