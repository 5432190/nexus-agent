"""Pytest configuration for Nexus Agent tests."""

from __future__ import annotations

import pytest
import respx

pytest_plugins = ["pytest_asyncio"]


@pytest.fixture(autouse=True)
def mock_httpx():
    with respx.mock(assert_all_mocked=False) as respx_mock:
        yield respx_mock
