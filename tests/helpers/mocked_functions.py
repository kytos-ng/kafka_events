"""Helper class for simulation functions"""

from unittest.mock import MagicMock, AsyncMock


async def simulate_successful_delay(*_) -> None:
    """Simulate a delay for aiokafkaproducer.start()"""
    return


def setup_mock_instance(mock: MagicMock) -> MagicMock:
    """Return the mock instance from a mock"""
    mock_instance = AsyncMock()
    mock.return_value = mock_instance
    return mock_instance
