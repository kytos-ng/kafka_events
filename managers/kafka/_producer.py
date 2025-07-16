""" The producer suite. A package-private class that handles enqueueing data to be sent to Kafka """

import asyncio
from typing import Callable

from aiokafka import AIOKafkaClient, AIOKafkaProducer
from aiokafka.conn import AIOKafkaConnection
from aiokafka.producer.sender import Sender

from napps.kytos.kafka_events.settings import KAFKA_TIMELIMIT


class Producer:
    """The producer class. Uses AIOKafkaProducer to handle Kafka tasks"""

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        bootstrap_servers,
        acks,
        enable_itempotence,
        topic_name,
        max_batch_size,
        linger_ms,
        max_request_size,
    ):
        """
        Constructor for the producer class.

        Accepts arguments from the orchestrator handler class
        """
        self._producer = AIOKafkaProducer(
            bootstrap_servers=bootstrap_servers,
            acks=acks,
            enable_idempotence=enable_itempotence,
            linger_ms=linger_ms,
            max_batch_size=max_batch_size,
            max_request_size=max_request_size,
        )
        self._topic: str = topic_name

    async def initialize_producer(self) -> None:
        """
        Initialize the producer using AIOKafkaProducer's built in setup method
        """
        await asyncio.wait_for(self._producer.start(), KAFKA_TIMELIMIT)

    async def send_data(self, encoded_data: bytes) -> None:
        """
        Send data to AIOKafkaProducer's batch, which is then sent to Kafka after a short delay.

        The incoming data must already have been serialized and encoded.
        """
        await asyncio.wait_for(
            self._producer.send(self._topic, encoded_data), KAFKA_TIMELIMIT
        )

    async def shutdown(self) -> None:
        """
        NOT CURRENTLY IN USE. USE sync_close IN MAIN

        Calls the producer's stop() method.
        """
        await asyncio.wait_for(self._producer.stop(), KAFKA_TIMELIMIT)

    def sync_close(
        self, loop: asyncio.AbstractEventLoop, callback: Callable[[asyncio.Task], None]
    ) -> None:
        """
        Expected functionality:
        - Should call and await the stop method.

        Actual:
        - Due to Main's shutdown sequence being synchronous AND the event loop is shut down
        before this occurs, the producer's routine cannot be awaited. Thus, we need to cancel
        all messages manually
        """
        for task in asyncio.all_tasks(loop):
            if task.get_coro().__name__ in CANCELABLE_METHODS:
                task.cancel()
                task.add_done_callback(callback)

    def is_ready(self) -> bool:
        """
        Checks if the producer is ready by using its _closed component
        """
        return getattr(self._producer, "_closed", None) is False

    def is_closed(self) -> bool:
        """
        Checks if the producer was closed
        """
        return getattr(self._producer, "_closed", None) is True


# A constant used exclusively in sync_close. Finds all the acceptable methods to cancel
CANCELABLE_METHODS = {
    method_name
    for instance in (
        Producer,
        AIOKafkaProducer,
        AIOKafkaClient,
        AIOKafkaConnection,
        Sender,
    )
    for method_name in dir(instance)
    if callable(getattr(instance, method_name, None))
    and not method_name.startswith("__")
}
