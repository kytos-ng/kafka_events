""" The implementation class for KafkaManager, the public interface used by main. """

import asyncio

from aiokafka.errors import KafkaError

from kytos.core import log, KytosEvent
from napps.kytos.kafka_events.managers.kafka._producer import Producer
from napps.kytos.kafka_events.managers.kafka._serializer import JSONSerializer
from napps.kytos.kafka_events.settings import (
    ACKS,
    BATCH_SIZE,
    BOOTSTRAP_SERVERS,
    ENABLE_ITEMPOTENCE,
    LINGER_MS,
    MAX_REQUEST_SIZE,
    TOPIC_NAME,
)


class KafkaManager:
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

    async def send(self, event: KytosEvent) -> None:
        """
        Send data to Kafka. Uses the following flow:

        - Checks that the producer was not closed
        - Checks that the producer is ready
        - Serializes the message into JSON
        - Awaits the producer to enqueue the message
        """
        event_name: str = event.name
        event_message: str = event.content

        try:
            await self._producer.send_data(
                self._serializer.serialize_and_encode(event_name, event_message)
            )
        except asyncio.TimeoutError as e:
            log.error(
                f"Producer tried publishing {event_name} [id: {event.id}, \
                      timestamp: {event.timestamp}] but timed out: {e}"
            )
        except KafkaError as e:
            log.error(f"Publishing to Kafka failed: {e}")

    async def setup(self) -> None:
        """
        Sets up the producer by awaiting its setup routine (Necessary for AIOKafka)
        """
        try:
            await self._producer.initialize_producer()
        except asyncio.TimeoutError:
            log.error("Producer initialization sequence timed out.")
        except KafkaError as e:
            log.error(f"Kafka producer initialization sequence failed: {e}")

    def shutdown(self, loop: asyncio.AbstractEventLoop) -> None:
        """
        Expected functionality:
        - Shuts down the producer by awaiting its shutdown routine (Necessary for AIOKafka)

        Actual:
        - Due to Main's shutdown sequence being synchronous AND the event loop is shut down
        before this occurs, the producer's routine cannot be awaited. Thus, we need to cancel
        all messages manually
        """

        def log_cancelled_exception(task: asyncio.Task) -> None:
            """
            If a cancelled exception occurs, log a warning, not an exception.
            """
            try:
                task.result()
            except asyncio.CancelledError:
                log.warning(
                    f"Task {task.get_coro().__name__} was cancelled during shutdown."
                )
            except Exception as e:  # pylint: disable=broad-exception-caught
                log.error(
                    f"Task {task.get_coro().__name__} raised an unexpected exception: {e}"
                )

        self._producer.sync_close(loop, callback=log_cancelled_exception)
