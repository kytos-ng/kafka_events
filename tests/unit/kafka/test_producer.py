"""Test class for unit testing Producer"""

import json
import asyncio
from unittest.mock import patch, MagicMock

import pytest

from napps.kytos.kafka_events.settings import KAFKA_TIMELIMIT
from napps.kytos.kafka_events.tests.helpers.producer_helper import (
    create_and_initialize_producer,
)
from aiokafka.errors import KafkaError
from tenacity import wait_none


async def simulate_long_timeout(*_: any) -> None:
    """
    Simulate a timeout. Goes just above the upper boundary to be as quick as
    possible, while still timing out
    """
    await asyncio.sleep(KAFKA_TIMELIMIT + 1)


async def simple_async_func() -> None:
    """A simple asynchronous function to await"""
    return None


class TestProducer:
    """
    Test suite
    """

    @patch("asyncio.wait_for")
    async def test_producer_raises_exception_on_timeout_on_initialization(
        self, asyn_mock
    ) -> None:
        """
        When initializing, the producer should raise a timeout exception if it takes too long
        """
        asyn_mock.side_effect = asyncio.TimeoutError
        # mock_producer_instance.start.side_effect = simulate_long_timeout

        with pytest.raises(asyncio.TimeoutError):
            await create_and_initialize_producer("localhost:9092")

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

    @patch("napps.kytos.kafka_events.managers.kafka._producer.AIOKafkaProducer")
    async def test_send_data_retries(self, mock_producer: MagicMock) -> None:
        """Test send_data with retries"""
        mock_producer_instance: MagicMock = mock_producer.return_value
        mock_producer_instance.start.side_effect = simple_async_func
        producer = await create_and_initialize_producer("localhost:9092")
        mock_producer_instance.send_and_wait.side_effect = KafkaError

        # Do not wait
        producer.send_data.retry.wait = wait_none()

        with pytest.raises(KafkaError):
            await producer.send_data(json.dumps("test").encode())

        assert mock_producer_instance.send_and_wait.call_count == 3
