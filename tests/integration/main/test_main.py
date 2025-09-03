""" Test suite """

import asyncio
from unittest.mock import patch, MagicMock, AsyncMock, Mock

from napps.kytos.kafka_events.main import Main
from napps.kytos.kafka_events.tests.helpers.mocked_functions import (
    simulate_successful_delay,
    setup_mock_instance,
)


class TestMain:
    """Test class for main"""

    @patch("napps.kytos.kafka_events.managers.kafka._producer.AIOKafkaProducer")
    async def test_setup(self, producer_mock: MagicMock):
        """Test that main's setup works correctly"""
        mock_instance: AsyncMock = setup_mock_instance(producer_mock)
        mock_instance.start = AsyncMock(side_effect=simulate_successful_delay)

        # Create main object

        Main(None)

        await asyncio.sleep(1)

        # Asserts

        producer_mock.assert_called_once()
        mock_instance.start.assert_called_once()

    @patch("napps.kytos.kafka_events.managers.kafka._producer.AIOKafkaProducer")
    async def test_execute(self, producer_mock: MagicMock):
        """Test that main has an execute method"""
        mock_instance: AsyncMock = setup_mock_instance(producer_mock)
        mock_instance.start = AsyncMock(side_effect=simulate_successful_delay)

        main = Main(None)

        await asyncio.sleep(1)

        main.execute()

        # Asserts

        producer_mock.assert_called_once()
        mock_instance.start.assert_called_once()

    @patch("napps.kytos.kafka_events.managers.kafka.handler.Producer")
    async def test_shutdown(self, producer_mock: MagicMock):
        """Test that main has a working shutdown method"""
        mock_instance: AsyncMock = setup_mock_instance(producer_mock)
        mock_instance.initialize_producer = AsyncMock(
            side_effect=simulate_successful_delay
        )
        mock_instance.sync_close = Mock(side_effect=lambda x, callback=None: None)

        main = Main(None)

        await asyncio.sleep(1)

        main.shutdown()

        # Asserts

        producer_mock.assert_called_once()
        mock_instance.initialize_producer.assert_called_once()
        mock_instance.sync_close.assert_called_once()
