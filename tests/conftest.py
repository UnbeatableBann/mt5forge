"""Shared pytest fixtures."""

from __future__ import annotations

import pytest

from tests.mocks.mock_data import sample_candles
from tests.mocks.mock_mt5 import MockMT5


@pytest.fixture
def candles():
    return sample_candles()


@pytest.fixture
def mock_mt5():
    mt5 = MockMT5()
    mt5.initialize()
    mt5.login(123456, password="secret", server="Demo")
    return mt5
