""" Test suite """

import asyncio
from unittest.mock import patch, MagicMock, AsyncMock, Mock
import re

from kytos.core import KytosEvent
from kytos.lib.helpers import get_test_client, get_controller_mock
from napps.kytos.kafka_events.main import Main
from napps.kytos.kafka_events.tests.helpers.mocked_functions import (
    setup_mock_instance,
)
from napps.kytos.kafka_events.settings import BLOCKED_PATTERNS


# pylint: disable=no-member,no-value-for-parameter
class TestMain:
    """Test class for main"""

    def setup_method(self):
        """Execute before each tests."""
        Main.get_topic_controller = MagicMock()
        self.base_endpoint = "kytos/kafka_events/v1"
        self.napp = None

    @patch("napps.kytos.kafka_events.managers.kafka.handler.Producer")
    async def get_client(self, producer_mock: MagicMock):
        """Get a test client with the producer mocked."""
        mock_instance: AsyncMock = setup_mock_instance(producer_mock)
        mock_instance.start = AsyncMock()

        controller = get_controller_mock()
        self.napp = Main(controller)
        api_client = get_test_client(controller, self.napp)
        self.napp.controller.loop = asyncio.get_running_loop()

        return api_client

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

    async def test_handle_events_blocked_event(self):
        """Test that blocked events are not sent to Kafka."""
        await self.get_client()
        self.napp._blocked = [re.compile("blocked")]
        self.napp._kafka_handler.send = AsyncMock()

        event = KytosEvent(name="blocked.event")
        await self.napp.handle_events(event)

        self.napp._kafka_handler.send.assert_not_awaited()

    async def test_handle_events_matching_topic(self):
        """Test that matching events are sent to their configured topic."""
        await self.get_client()
        self.napp._allowed = {"topic-a": [re.compile("matching")]}
        self.napp._kafka_handler.send = AsyncMock()

        event = KytosEvent(name="matching.event")
        await self.napp.handle_events(event)

        self.napp._kafka_handler.send.assert_awaited_once_with(event, "topic-a")

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

    async def test_get_topics(self):
        """Test get_topics endpoint."""
        api_client = await self.get_client()
        endpoint = f"{self.base_endpoint}/topics"
        response = await api_client.get(endpoint)

        expected = {"blocked": list(BLOCKED_PATTERNS), "allowed": {}}
        assert response.json() == expected
        assert response.status_code == 200

        self.napp._allowed = {"mock_topic": [re.compile("new_pattern")]}
        expected["allowed"] = {"mock_topic": ["new_pattern"]}

        response = await api_client.get(endpoint)

        assert response.json() == expected
        assert response.status_code == 200

    @patch("napps.kytos.kafka_events.main.Main.set_allowed_topics")
    async def test_add_topics(self, set_topics_mock: Mock):
        """Test add_topics method."""
        api_client = await self.get_client()
        payload = {
            "new_topic": ["pattern1", "pattern2"],
            "mocked_topic": ["pattern3", "pattern4"],
        }
        endpoint = f"{self.base_endpoint}/topics"
        response = await api_client.post(endpoint, json=payload)
        data = response.json()

        assert response.status_code == 201
        assert data["topics"] == list(payload.keys())

        top_control = self.napp.topic_controller
        assert top_control.insert_allowed_topics.call_count == 1
        assert top_control.insert_allowed_topics.call_args[0][0] == payload
        assert set_topics_mock.call_count == 2
        assert set_topics_mock.call_args[0][0] == payload

    @patch("napps.kytos.kafka_events.main.Main.set_allowed_topics")
    async def test_add_topics_existing_topic_error(self, set_topics_mock):
        """Test add_topics method with an existing topic."""
        api_client = await self.get_client()
        self.napp._allowed = {"new_topic": ["some_pattern"]}
        payload = {
            "new_topic": ["pattern1", "pattern2"],
            "mocked_topic": ["pattern3", "pattern4"],
        }
        endpoint = f"{self.base_endpoint}/topics"
        response = await api_client.post(endpoint, json=payload)

        assert response.status_code == 400
        top_control = self.napp.topic_controller
        assert top_control.insert_allowed_topics.call_count == 0
        assert set_topics_mock.call_count == 1

    async def test_delete_topic(self):
        """Test delete_topic method."""
        api_client = await self.get_client()

        self.napp._allowed = {"new_topic": ["some_pattern"]}
        endpoint = f"{self.base_endpoint}/topics/new_topic"
        response = await api_client.delete(endpoint)

        assert response.status_code == 200
        top_control = self.napp.topic_controller
        assert not self.napp._allowed
        assert top_control.delete_allowed_topic.call_count == 1
        assert top_control.delete_allowed_topic.call_args[0][0] == "new_topic"

    async def test_delete_topic_not_found(self):
        """Test delete_topic method with a non-existing topic."""
        api_client = await self.get_client()
        endpoint = f"{self.base_endpoint}/topics/non_existing_topic"
        response = await api_client.delete(endpoint)
        assert response.status_code == 404

    async def test_update_topic(self):
        """Test update_topic method."""
        api_client = await self.get_client()

        self.napp._allowed = {"new_topic": [re.compile("some_pattern")]}
        payload = ["pattern1", "pattern2"]
        endpoint = f"{self.base_endpoint}/topics/new_topic"
        response = await api_client.patch(endpoint, json=payload)

        assert response.status_code == 200
        top_control = self.napp.topic_controller
        assert top_control.insert_allowed_topics.call_count == 1
        assert len(self.napp._allowed["new_topic"]) == 3

    async def test_update_topic_ignores_redundant(self):
        """Test update_topic ignores patterns covered by an existing pattern."""
        api_client = await self.get_client()

        self.napp._allowed = {"new_topic": [re.compile("event.*")]}
        endpoint = f"{self.base_endpoint}/topics/new_topic"
        response = await api_client.patch(endpoint, json=["event.other.*"])

        assert response.status_code == 200
        assert response.json() == {"new_topic": ["event.*"]}
        assert len(self.napp._allowed["new_topic"]) == 1

    async def test_update_topic_removes_duplicates(self):
        """Test update_topic removes duplicate patterns."""
        api_client = await self.get_client()

        self.napp._allowed = {"new_topic": []}
        endpoint = f"{self.base_endpoint}/topics/new_topic"
        response = await api_client.patch(
            endpoint,
            json=["event.*", "event.*"],
        )

        assert response.status_code == 200
        assert response.json() == {"new_topic": ["event.*"]}
        assert len(self.napp._allowed["new_topic"]) == 1
        top_control = self.napp.topic_controller
        assert top_control.insert_allowed_topics.call_args[0][0] == {
            "new_topic": ["event.*"]
        }

    async def test_update_topic_not_found(self):
        """Test update_topic method with a non-existing topic."""
        api_client = await self.get_client()

        payload = ["pattern1", "pattern2"]
        endpoint = f"{self.base_endpoint}/topics/new_topic"
        response = await api_client.patch(endpoint, json=payload)

        assert response.status_code == 404
        top_control = self.napp.topic_controller
        assert top_control.insert_allowed_topics.call_count == 0

    async def test_replace_pattern(self):
        """Test replace_pattern method."""
        api_client = await self.get_client()

        self.napp._allowed = {"new_topic": [re.compile("some_pattern")]}
        payload = ["pattern1", "pattern2"]
        endpoint = f"{self.base_endpoint}/topics/new_topic"
        response = await api_client.put(endpoint, json=payload)

        assert response.status_code == 200
        top_control = self.napp.topic_controller
        assert top_control.insert_allowed_topics.call_count == 1
        assert len(self.napp._allowed["new_topic"]) == 2

    async def test_replace_pattern_not_found(self):
        """Test replace_pattern method with a non-existing topic."""
        api_client = await self.get_client()

        payload = ["pattern1", "pattern2"]
        endpoint = f"{self.base_endpoint}/topics/new_topic"
        response = await api_client.put(endpoint, json=payload)

        assert response.status_code == 404
        top_control = self.napp.topic_controller
        assert top_control.insert_allowed_topics.call_count == 0
