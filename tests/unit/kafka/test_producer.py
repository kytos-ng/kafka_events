"""Test class for unit testing Producer"""

import json
import asyncio
from unittest.mock import patch, MagicMock

import pytest

from napps.kytos.kafka_events.settings import KAFKA_TIMELIMIT
from napps.kytos.kafka_events.tests.helpers.producer_helper import (
    create_and_initialize_producer,
)


async def simulate_long_timeout(*_: any) -> None:
    """
    Simulate a timeout. Goes just above the upper boundary to be as quick as
    possible, while still timing out
    """
    await asyncio.sleep(KAFKA_TIMELIMIT+1)


async def simple_async_func() -> None:
    """A simple asynchronous function to await"""
    return None


class TestProducer:
    """
    Test suite
    """

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

    @patch("napps.kytos.kafka_events.managers.kafka._producer.AIOKafkaProducer")
    async def test_producer_raises_exception_on_timeout_on_send(
        self, mock_producer: MagicMock
    ) -> None:
        """
        When sending data, the producer should raise a timeout exception if it takes too long
        """
        mock_producer_instance: MagicMock = mock_producer.return_value
        mock_producer_instance.start.side_effect = simple_async_func
        mock_producer_instance.send.side_effect = simulate_long_timeout

        producer = await create_and_initialize_producer("localhost:9092")

        with pytest.raises(asyncio.TimeoutError):
            await producer.send_data(json.dumps("Test").encode())

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
