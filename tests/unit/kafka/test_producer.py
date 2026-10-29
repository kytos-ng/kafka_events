"""Test class for unit testing Producer"""

import json
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from napps.kytos.kafka_events.tests.helpers.producer_helper import (
    create_and_initialize_producer,
)


async def simulate_long_timeout(*_: any) -> None:
    """Simulate an operation that exceeds the test timeout."""
    await asyncio.sleep(0.1)


async def simple_async_func() -> None:
    """A simple asynchronous function to await"""
    return None


class TestProducer:
    """
    Test suite
    """

    @patch("napps.kytos.kafka_events.managers.kafka._producer.KAFKA_TIMELIMIT", 0.01)
    @patch("napps.kytos.kafka_events.managers.kafka._producer.AIOKafkaProducer")
    async def test_producer_raises_exception_on_timeout_on_initialization(
        self, mock_producer: MagicMock
    ) -> None:
        """
        When initializing, the producer should raise a timeout exception if it takes too long
        """
        mock_producer_instance: MagicMock = mock_producer.return_value
        mock_producer_instance.start.side_effect = simulate_long_timeout

        with pytest.raises(asyncio.TimeoutError):
            await create_and_initialize_producer("localhost:9092")

    @patch("napps.kytos.kafka_events.managers.kafka._producer.monotonic")
    @patch("napps.kytos.kafka_events.managers.kafka._producer.AIOKafkaProducer")
    async def test_producer_retries_initialization_every_60_seconds(
        self, mock_producer: MagicMock, mock_monotonic: MagicMock
    ) -> None:
        """
        Message sends should not retry initialization until the configured
        error interval has elapsed.
        """
        mock_producer_instance: MagicMock = mock_producer.return_value
        mock_producer_instance.start.side_effect = [
            simple_async_func(),
            simple_async_func(),
            simple_async_func(),
        ]
        mock_producer_instance.send_and_wait = AsyncMock()
        mock_monotonic.side_effect = [0, 1, 61]

        producer = await create_and_initialize_producer("localhost:9092")
        producer._producer._closed = False  # pylint:disable=protected-access
        producer._initialized = False  # pylint:disable=protected-access

        await producer.send_data(json.dumps("Test").encode())
        assert mock_producer_instance.start.call_count == 1
        mock_producer_instance.send_and_wait.assert_not_called()

        await producer.send_data(json.dumps("Test").encode())
        assert mock_producer_instance.start.call_count == 2
        mock_producer_instance.send_and_wait.assert_awaited_once()

    @patch("napps.kytos.kafka_events.managers.kafka._producer.AIOKafkaProducer")
    async def test_producer_accurately_cancels_methods(
        self, mock_producer: MagicMock
    ) -> None:
        """
        When canceling coroutines from the event loop, the producer should only cancel
        coroutines found in aiokafka or the Producer class.
        """
        mock_producer_instance: MagicMock = mock_producer.return_value
        mock_producer_instance.start.side_effect = simple_async_func

        producer = await create_and_initialize_producer("localhost:9092")

        initialize: asyncio.Task = asyncio.create_task(producer.initialize_producer())
        send_data: asyncio.Task = asyncio.create_task(
            producer.send_data(json.dumps("test").encode())
        )

        producer.sync_close(loop=asyncio.get_running_loop(), callback=lambda: None)

        with pytest.raises(asyncio.CancelledError):
            await initialize

        with pytest.raises(asyncio.CancelledError):
            await send_data
