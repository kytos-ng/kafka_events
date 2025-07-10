"""Handler testing suite"""

import asyncio

from aiokafka import AIOKafkaConsumer

from kytos.core import KytosEvent
from managers.kafka.handler import KafkaDomainManager
from settings import TOPIC_NAME, KAFKA_TIMELIMIT


class TestHandler:
    """Testing suite"""

    async def test_setup_succeeds_with_valid_broker(self) -> None:
        """
        Given an available broker, setup should succeed
        """
        handler = KafkaDomainManager()
        await handler.setup()

        assert handler._producer.is_ready()  # pylint:disable=protected-access

        await handler._producer.shutdown()  # pylint:disable=protected-access

    async def test_send_succeeds_with_valid_data(self) -> None:
        """
        Given valid data, send_data should succeed
        """
        # First create an AIOKafkaConsumer to test the data was propagated
        consumer = AIOKafkaConsumer(TOPIC_NAME, bootstrap_servers="localhost:9092")
        await consumer.start()

        handler = KafkaDomainManager()
        await handler.setup()

        event = KytosEvent(name="Test", content={"Data": "Test"})
        await handler.send(event.name, event.content)

        assert await asyncio.wait_for(consumer.getone(), KAFKA_TIMELIMIT) is not None
        await consumer.stop()

    async def test_send_returns_when_producer_is_closed(self) -> None:
        """
        If the producer has been closed, do not attempt to send data
        """
        handler = KafkaDomainManager()

        await handler.setup()
        await handler._producer.shutdown()  # pylint:disable=protected-access

        assert not handler._producer.is_closed()  # pylint:disable=protected-access

        # Should immediately return. If it tries to send, an exception would be thrown.
        handler.send("Test", None)

    async def test_send_will_initialize_if_producer_is_not_ready(self) -> None:
        """
        Because Main's setup function is synchronous, the application may try sending
        messages before the producer is ready. We avoid this by awaiting the initialization
        method before sending
        """
        # First create an AIOKafkaConsumer to test the data was propagated
        consumer = AIOKafkaConsumer(TOPIC_NAME, bootstrap_servers="localhost:9092")
        await consumer.start()

        handler = KafkaDomainManager()

        await handler.send("Test", {"Test": "Test"})

        assert consumer.getone() is not None
        await consumer.stop()

    async def test_shutdown_only_cancels_valid_data(self) -> None:
        """
        Given a loop with mixed Tasks, only cancel what is acceptable.
        """

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

        handler = KafkaDomainManager()
        loop: asyncio.AbstractEventLoop = asyncio.get_running_loop()

        enqueued_tasks: list[asyncio.Task] = [
            asyncio.create_task(send()),
            asyncio.create_task(alt_send()),
            asyncio.create_task(initialize_producer()),
            asyncio.create_task(sync_close()),
            asyncio.create_task(find_something()),
        ]

        handler.shutdown(loop)

        assert enqueued_tasks[0].cancelling == 1
        assert enqueued_tasks[1].cancelling == 0
        assert enqueued_tasks[2].cancelling == 1
        assert enqueued_tasks[3].cancelling == 1
        assert enqueued_tasks[4].cancelling == 0
