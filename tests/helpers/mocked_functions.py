"""Helper class for simulation functions"""

from unittest.mock import MagicMock, AsyncMock


def setup_mock_instance(mock: MagicMock) -> MagicMock:
    """Return the mock instance from a mock"""
    mock_instance = AsyncMock()
    mock.return_value = mock_instance
    return mock_instance
