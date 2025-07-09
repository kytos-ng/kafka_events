""" Test suite for the Producer class """

import json
from kafka_events.managers.kafka._producer import Producer
from kafka_events.settings import (
    ACKS,
    ENABLE_ITEMPOTENCE,
    TOPIC_NAME,
    BATCH_SIZE,
    LINGER_MS,
    MAX_REQUEST_SIZE,
)


class TestProducer:
    """
    Testing suite
    """

    async def test_should_connect_properly_given_valid_broker(self) -> None:
        """
        Given a valid broker to connect to, Producer should successfully complete its setup
        routine.
        """
        producer = Producer(
            bootstrap_servers="localhost:9092",
            acks=ACKS,
            enable_itempotence=ENABLE_ITEMPOTENCE,
            topic_name=TOPIC_NAME,
            max_batch_size=BATCH_SIZE,
            linger_ms=LINGER_MS,
            max_request_size=MAX_REQUEST_SIZE,
        )

        await producer.initialize_producer()
        assert producer.is_ready() is True

    async def test_should_send_messages_with_valid_data(self) -> None:
        """
        The producer should be able to valid messages to Kafka
        """
        message: bytes = json.dumps("Test").encode()

        producer = Producer(
            bootstrap_servers="localhost:9092",
            acks=ACKS,
            enable_itempotence=ENABLE_ITEMPOTENCE,
            topic_name=TOPIC_NAME,
            max_batch_size=BATCH_SIZE,
            linger_ms=LINGER_MS,
            max_request_size=MAX_REQUEST_SIZE,
        )

        await producer.initialize_producer()
        await producer.send_data(message)
