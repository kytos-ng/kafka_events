"""Handler testing suite"""

import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

from kytos.core import KytosEvent
from napps.kytos.kafka_events.managers.kafka.handler import KafkaManager
from napps.kytos.kafka_events.tests.helpers.mocked_functions import (
    setup_mock_instance,
)


class TestHandler:
    """Testing suite"""

    @patch("napps.kytos.kafka_events.managers.kafka._producer.AIOKafkaProducer")
    async def test_setup_succeeds_with_valid_broker(
        self, producer_mock: MagicMock
    ) -> None:
        """
        Given an available broker, setup should succeed
        """
        mock_instance: AsyncMock = setup_mock_instance(producer_mock)
        mock_instance.start = AsyncMock()
        mock_instance.configure_mock(_closed=False)

        handler = KafkaManager()
        await handler.setup()

        assert handler._producer.is_ready()  # pylint:disable=protected-access

        # Assert mocks
        producer_mock.assert_called_once()
        mock_instance.start.assert_called_once()

    @patch("napps.kytos.kafka_events.managers.kafka._producer.AIOKafkaProducer")
    async def test_send_succeeds_with_valid_data(
        self, producer_mock: MagicMock
    ) -> None:
        """
        Given valid data, send_data should succeed
        """
        mock_instance: AsyncMock = setup_mock_instance(producer_mock)
        mock_instance.start = AsyncMock()
        mock_instance.send = AsyncMock()

        handler = KafkaManager()
        await handler.setup()

        event = KytosEvent(name="Test", content={"Data": "Test"})
        await handler.send(event)

        # Assert mocks

        producer_mock.assert_called_once()
        mock_instance.start.assert_called_once()
        mock_instance.send.assert_called_once()

    @patch("napps.kytos.kafka_events.managers.kafka._producer.AIOKafkaProducer")
    async def test_send_returns_when_producer_is_closed(
        self, producer_mock: MagicMock
    ) -> None:
        """
        If the producer has been closed, do not attempt to send data
        """
        mock_instance: AsyncMock = setup_mock_instance(producer_mock)
        mock_instance.start = AsyncMock()
        mock_instance.configure_mock(_closed=False)
        mock_instance.send = AsyncMock()
        mock_instance.stop = AsyncMock()

        handler = KafkaManager()

        await handler.setup()
        await handler._producer.shutdown()  # pylint:disable=protected-access

        event = KytosEvent(name="Test", content=None)

        # Should immediately return. If it tries to send, an exception would be thrown.
        await handler.send(event)

        # Assert mocks

        producer_mock.assert_called_once()
        mock_instance.start.assert_called_once()
        mock_instance.stop.assert_called_once()

    @patch("napps.kytos.kafka_events.managers.kafka._producer.AIOKafkaProducer")
    async def test_send_will_initialize_if_producer_is_not_ready(
        self, producer_mock: MagicMock
    ) -> None:
        """
        Because Main's setup function is synchronous, the application may try sending
        messages before the producer is ready. We avoid this by awaiting the initialization
        method before sending
        """
        mock_instance: AsyncMock = setup_mock_instance(producer_mock)
        mock_instance.start = AsyncMock()
        mock_instance.send = AsyncMock()

        handler = KafkaManager()
        await handler.setup()

        event = KytosEvent(name="Test", content={"Test": "Test"})

        await handler.send(event)

        # Assert mocks

        mock_instance.start.assert_called_once()
        mock_instance.send.assert_called_once()

    @patch("napps.kytos.kafka_events.managers.kafka._producer.AIOKafkaProducer")
    async def test_shutdown_only_cancels_valid_data(
        self, producer_mock: MagicMock
    ) -> None:
        """
        Given a loop with mixed Tasks, only cancel what is acceptable.
        """
        mock_instance: AsyncMock = setup_mock_instance(producer_mock)
        mock_instance.start = AsyncMock()

        async def send(*_: any) -> None:
            """SHOULD BE CANCELLED"""
            await asyncio.sleep(60)

        async def alt_send(*_: any) -> None:
            """SHOULD NOT BE CANCELLED"""
            await asyncio.sleep(60)

        async def initialize_producer(*_: any) -> None:
            """SHOULD BE CANCELLED"""
            await asyncio.sleep(60)

        async def sync_close(*_: any) -> None:
            """SHOULD BE CANCELLED"""
            await asyncio.sleep(60)

        async def find_something(*_: any) -> None:
            """SHOULD NOT BE CANCELLED"""
            await asyncio.sleep(60)

        handler = KafkaManager()
        await handler.setup()

        loop: asyncio.AbstractEventLoop = asyncio.get_running_loop()

        enqueued_tasks: list[asyncio.Task] = [
            asyncio.create_task(send()),
            asyncio.create_task(alt_send()),
            asyncio.create_task(initialize_producer()),
            asyncio.create_task(sync_close()),
            asyncio.create_task(find_something()),
        ]

        handler.shutdown(loop)

        assert enqueued_tasks[0].cancelling() == 1
        assert enqueued_tasks[1].cancelling() == 0
        assert enqueued_tasks[2].cancelling() == 1
        assert enqueued_tasks[3].cancelling() == 1
        assert enqueued_tasks[4].cancelling() == 0

        # Assert mocks

        mock_instance.start.assert_called_once()
