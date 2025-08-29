""" Test suite for the Producer class """

from unittest.mock import patch, MagicMock, Mock

from napps.kytos.kafka_events.managers.kafka._producer import Producer
from napps.kytos.kafka_events.tests.helpers.producer_helper import (
    create_and_initialize_producer,
)
from napps.kytos.kafka_events.tests.helpers.mocked_functions import (
    simulate_successful_delay,
    setup_mock_instance,
)


class TestProducer:
    """
    Mocked testing suite
    """

    @patch("napps.kytos.kafka_events.managers.kafka._producer.AIOKafkaProducer")
    async def test_should_connect_properly_given_valid_broker(
        self, producer_mock: MagicMock
    ) -> None:
        """
        Given a valid broker to connect to, Producer should successfully complete its setup
        routine.
        """
        mock_instance: MagicMock = setup_mock_instance(producer_mock)
        mock_instance.start = Mock(side_effect=simulate_successful_delay)
        mock_instance.configure_mock(_closed=False)

        producer: Producer = await create_and_initialize_producer(
            bootstrap_servers="localhost:9092"
        )

        assert producer.is_ready() is True

        # Assert mocks

        producer_mock.assert_called_once()
        mock_instance.start.assert_called_once()

    @patch("napps.kytos.kafka_events.managers.kafka._producer.AIOKafkaProducer")
    async def test_should_be_initialized_on_setup(
        self, producer_mock: MagicMock
    ) -> None:
        """
        On setup, the Producer object should sent initialized to true.
        """
        mock_instance: MagicMock = setup_mock_instance(producer_mock)
        mock_instance.start = Mock(side_effect=simulate_successful_delay)

        producer: Producer = await create_and_initialize_producer(
            bootstrap_servers="localhost:9092"
        )

        assert producer._initialized is True

        # Assert mocks

        producer_mock.assert_called_once()
        mock_instance.start.assert_called_once()
