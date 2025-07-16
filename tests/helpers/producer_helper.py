"""Helper methods when doing tests"""

from managers.kafka._producer import Producer
from settings import (
    ACKS,
    ENABLE_ITEMPOTENCE,
    TOPIC_NAME,
    BATCH_SIZE,
    LINGER_MS,
    MAX_REQUEST_SIZE,
)


# pylint: disable=too-many-arguments
async def create_and_initialize_producer(
    bootstrap_servers: str,
    acks: str = ACKS,
    enable_itempotence: str = ENABLE_ITEMPOTENCE,
    topic_name: str = TOPIC_NAME,
    max_batch_size: int = BATCH_SIZE,
    linger_ms: int = LINGER_MS,
    max_request_size: int = MAX_REQUEST_SIZE,
) -> Producer:
    """
    Create and initialize a AIOKafkaProducer instance
    """
    producer = Producer(
        bootstrap_servers=bootstrap_servers,
        acks=acks,
        enable_itempotence=enable_itempotence,
        topic_name=topic_name,
        max_batch_size=max_batch_size,
        linger_ms=linger_ms,
        max_request_size=max_request_size,
    )

    await producer.initialize_producer()

    return producer
