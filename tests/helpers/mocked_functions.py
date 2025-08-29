"""Helper class for simulation functions"""

import asyncio
from unittest.mock import MagicMock


async def simulate_successful_delay(*_) -> None:
    """Simulate a delay for aiokafkaproducer.start()"""
    await asyncio.sleep(0.2)
    return


def setup_mock_instance(mock: MagicMock) -> MagicMock:
    """Return the mock instance from a mock"""
    mock_instance = MagicMock()
    mock.return_value = mock_instance
    return mock_instance
