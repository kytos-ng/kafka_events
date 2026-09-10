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
    KAFKA_TIMELIMIT
)
from aiokafka.errors import KafkaError
from kytos.core.retry import before_sleep
from tenacity import retry, stop_after_attempt, wait_random, retry_if_exception_type
from random import randint

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

        self.eve_err = 0
        self.eve_retry = 0
        self.list_eve_sent = [0]

    #@retry(
    #    stop=stop_after_attempt(3),
    #    before_sleep=before_sleep,
    #    wait=wait_random(min=10, max=12),
    #    retry=retry_if_exception_type(KafkaError),
    #    reraise=True,
    #)
    async def send(self, event: KytosEvent, tries=0) -> None:
        """
        Send data to Kafka. Uses the following flow:

        - Checks that the producer was not closed
        - Checks that the producer is ready
        - Serializes the message into JSON
        - Awaits the producer to enqueue the message
        """
        event_name: str = event.name
        event_message = event.content
        topic_name = event_message.pop("kafka_topic", None)

        try:
            await self._producer.send_data(
                self._serializer.serialize_and_encode(event_name, event_message),
                event_name,
                topic_name,
            )
        except asyncio.TimeoutError as e:
            log.error(
                f"Producer tried publishing {event_name} [id: {event.id}, \
                      timestamp: {event.timestamp}] but timed out: {e}"
            )
            self.eve_err += 1
        except KafkaError as e:
            #log.error(f"Publishing to Kafka failed: {e}.")
            log.error(f"Publishing to Kafka failed: {e}. Try {tries + 1}/3")
            #self.eve_err += 1
            self.eve_retry += 1
            if tries < 3:
                tries += 1
                #await asyncio.sleep(randint(30, 36))
                await asyncio.sleep(10)
                await self.send(event, tries=tries)
            else:
                raise e
            #raise e

    async def setup(self) -> None:
        """
        Sets up the producer by awaiting its setup routine (Necessary for AIOKafka)
        """
        log.info("Initializing producer...")

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
