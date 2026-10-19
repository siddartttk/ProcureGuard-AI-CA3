from copy import deepcopy
from pathlib import Path
import pytest
from procureguard.data_loader import load_dataset


@pytest.fixture
def dataset():
    return deepcopy(load_dataset(Path(__file__).resolve().parents[1] / 'data/synthetic'))
