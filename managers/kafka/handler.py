""" The implementation class for KafkaManager, the public interface used by main. """

import asyncio
from interface import KafkaManager
from _producer import Producer
from _serializer import JSONSerializer
from kafka_events.settings import (
    BOOTSTRAP_SERVERS,
    ACKS,
    ENABLE_ITEMPOTENCE,
    TOPIC_NAME,
    BATCH_SIZE,
    LINGER_MS,
    MAX_REQUEST_SIZE,
)


class KafkaDomainManager(KafkaManager):
    """Acts like an orchestrator for internal components."""

    def __init__(self):
        """
        Object-oriented, with separate classes for specific tasks
        """
        self._producer = Producer(
            bootstrap_servers=BOOTSTRAP_SERVERS,
            acks=ACKS,
            enable_itempotence=ENABLE_ITEMPOTENCE,
            topic_name=TOPIC_NAME,
            max_batch_size=BATCH_SIZE,
            linger_ms=LINGER_MS,
            max_request_size=MAX_REQUEST_SIZE,
        )
        self._serializer = JSONSerializer()

    async def send(self, event: str, message: any) -> None:
        """
        Send data to Kafka. Uses the following flow:

        - Checks that the producer was not closed
        - Checks that the producer is ready
        - Serializes the message into JSON
        - Awaits the producer to enqueue the message
        """
        if self._producer.is_closed():
            return
        if not self._producer.is_ready():
            await self._producer.initialize_producer()

        await self._producer.send_data(
            await self._serializer.serialize_and_encode(event, message)
        )

    async def setup(self) -> None:
        """
        Sets up the producer by awaiting its setup routine (Necessary for AIOKafka)
        """
        await self._producer.initialize_producer()

    def shutdown(self, loop: asyncio.AbstractEventLoop) -> None:
        """
        Expected functionality:
        - Shuts down the producer by awaiting its shutdown routine (Necessary for AIOKafka)

        Actual:
        - Due to Main's shutdown sequence being synchronous AND the event loop is shut down
        before this occurs, the producer's routine cannot be awaited. Thus, we need to cancel
        all messages manually
        """
        for task in asyncio.all_tasks(loop):
            task.cancel()
