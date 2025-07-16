""" Test suite for the Producer class """

import asyncio
import json

from aiokafka import AIOKafkaConsumer

from managers.kafka._producer import Producer
from tests.helpers.producer_helper import create_and_initialize_producer
from settings import TOPIC_NAME


class TestProducer:
    """
    Testing suite

    Note: In Main, the shutdown sequence is synchronous, thus it does not use the Producer
    class's correct shudown routine, favoring the synchronous method. The synchronous method
    cancels all pending tasks before closing the loop. While not desirable, it is the
    valid way to sufficently shutdown at the moment. In this testing suite, we opt
    to use the correct shutdown routine as to reduce warning messages in stdout.
    """

    async def test_should_connect_properly_given_valid_broker(self) -> None:
        """
        Given a valid broker to connect to, Producer should successfully complete its setup
        routine.
        """
        producer: Producer = await create_and_initialize_producer(
            bootstrap_servers="localhost:9092"
        )

        assert producer.is_ready() is True

        await producer.shutdown()

    async def test_should_send_messages_with_valid_data(self) -> None:
        """
        The producer should be able to valid messages to Kafka
        """
        # Create a consumer first.
        # We want to do this because we want it to consume the LATEST message, not previous
        # messages that have been sent from other integration tests.
        consumer = AIOKafkaConsumer(TOPIC_NAME, bootstrap_servers="localhost:9092")
        await consumer.start()

        # Create a test message
        message: bytes = json.dumps("Test").encode()

        producer = await create_and_initialize_producer(
            bootstrap_servers="localhost:9092"
        )

        await producer.send_data(message)

        # Wait for the message to propagate

        await asyncio.sleep(1)

        # Test that the message was received

        topics = await asyncio.create_task(
            asyncio.wait_for(consumer.getone(), timeout=5)
        )

        assert topics is not None

        # Close producer & consumer
        await producer.shutdown()
        await consumer.stop()
