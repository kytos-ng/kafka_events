""" Test suite """

import asyncio
from unittest.mock import patch, MagicMock, AsyncMock, Mock

from kytos.lib.helpers import get_test_client, get_controller_mock
from napps.kytos.kafka_events.main import Main
from napps.kytos.kafka_events.tests.helpers.mocked_functions import (
    setup_mock_instance,
)
from napps.kytos.kafka_events.settings import BLOCKED_PATTERNS


class TestMain:
    """Test class for main"""

    def setup_method(self):
        """Execute before each tests."""
        self.base_endpoint = "kytos/kafka_events/v1"

    async def get_client(self, producer_mock: MagicMock):
        """Get a test client with the producer mocked."""
        mock_instance: AsyncMock = setup_mock_instance(producer_mock)
        mock_instance.start = AsyncMock()

        controller = get_controller_mock()
        napp = Main(controller)
        api_client = get_test_client(controller, napp)
        napp.controller.loop = asyncio.get_running_loop()

        return api_client

    @patch("napps.kytos.kafka_events.managers.kafka._producer.AIOKafkaProducer")
    async def test_get_filters(self, producer_mock: MagicMock):
        """Test get_filters endpoint."""
        api_client = await self.get_client(producer_mock)
        endpoint = f"{self.base_endpoint}/filters"
        response = await api_client.get(endpoint)
        print(api_client.base_url)
        expected = {"filters": list(BLOCKED_PATTERNS)}
        assert response.json() == expected
        assert response.status_code == 200

    @patch("napps.kytos.kafka_events.managers.kafka._producer.AIOKafkaProducer")
    async def test_setup(self, producer_mock: MagicMock):
        """Test that main's setup works correctly"""
        mock_instance: AsyncMock = setup_mock_instance(producer_mock)
        mock_instance.start = AsyncMock()

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
        mock_instance.start = AsyncMock()

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
        mock_instance.initialize_producer = AsyncMock()
        mock_instance.sync_close = Mock(side_effect=lambda x, callback=None: None)

        main = Main(None)

        await asyncio.sleep(1)

        main.shutdown()

        # Asserts

        producer_mock.assert_called_once()
        mock_instance.initialize_producer.assert_called_once()
        mock_instance.sync_close.assert_called_once()
