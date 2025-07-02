""" The producer suite. A package-private class that handles enqueueing data to be sent to Kafka """

import asyncio
from aiokafka import AIOKafkaProducer
from kafka_events.settings import KAFKA_TIMELIMIT


class Producer:
    """The producer class. Uses AIOKafkaProducer to handle Kafka tasks"""

    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
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

    async def send_data(self, serialized_data: str) -> None:
        """
        Send data to AIOKafkaProducer's batch, which is then sent to Kafka after a short delay.

        The incoming data must already have been serialized.
        """
        await asyncio.wait_for(
            self._producer.send(self._topic, serialized_data), KAFKA_TIMELIMIT
        )

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
