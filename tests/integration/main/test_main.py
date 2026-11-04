""" Test suite """

import asyncio
from unittest.mock import patch, MagicMock, AsyncMock, Mock
import re

import pytest
from kytos.core import KytosEvent
from kytos.core.rest_api import HTTPException
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

    async def test_set_allowed_topics_loads_all_topics(self):
        """Test loading multiple topics compiles every pattern."""
        await self.get_client()

        self.napp.set_allowed_topics(
            {
                "topic-a": ["event-a"],
                "topic-b": ["event-b"],
            }
        )

        assert set(self.napp._allowed) == {"topic-a", "topic-b"}
        assert self.napp._allowed["topic-a"][0].pattern == "event-a"
        assert self.napp._allowed["topic-b"][0].pattern == "event-b"

    async def test_set_allowed_topics_not_partial_update(self):
        """Test invalid patterns do not partially update allowed topics."""
        await self.get_client()
        self.napp._allowed = {"existing": [re.compile("existing")]}

        with pytest.raises(HTTPException):
            self.napp.set_allowed_topics(
                {
                    "valid": ["valid"],
                    "invalid": ["["],
                }
            )

        assert len(self.napp._allowed) == 1
        assert "existing" in self.napp._allowed

    async def test_add_topics_invalid_pattern(self):
        """Test invalid patterns are rejected before database persistence."""
        api_client = await self.get_client()
        payload = {"broken": ["["]}

        response = await api_client.post(f"{self.base_endpoint}/topics", json=payload)

        assert response.status_code == 400
        assert self.napp.topic_controller.insert_allowed_topics.call_count == 0
        assert "broken" not in self.napp._allowed

    async def test_set_allowed_topics_rejects_invalid_database_pattern(self):
        """Test invalid patterns loaded from the database fail explicitly."""
        await self.get_client()
        self.napp.topic_controller.get_allowed_topics_patterns.return_value = {
            "broken": ["["]
        }

        with pytest.raises(re.error):
            self.napp.set_allowed_topics()

        assert "broken" not in self.napp._allowed

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

    @patch("napps.kytos.kafka_events.main.Main.set_allowed_topics")
    async def test_add_topics_numeric_topic_error(self, set_topics_mock):
        """Test add_topics method with a purely numeric topic."""
        api_client = await self.get_client()
        payload = {
            "123": ["pattern1", "pattern2"],
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

    async def test_update_topic_keeps_non_identical_patterns(self):
        """Test update_topic keeps patterns that are not identical."""
        api_client = await self.get_client()

        self.napp._allowed = {"new_topic": [re.compile("event.*")]}
        endpoint = f"{self.base_endpoint}/topics/new_topic"
        response = await api_client.patch(endpoint, json=["event.other.*"])

        assert response.status_code == 200
        assert set(response.json()["new_topic"]) == {"event.*", "event.other.*"}
        assert len(self.napp._allowed["new_topic"]) == 2

    async def test_update_topic_keeps_regex_alternatives(self):
        """Test update_topic keeps a pattern that expands existing matches."""
        api_client = await self.get_client()

        self.napp._allowed = {"new_topic": [re.compile("foo")]}
        endpoint = f"{self.base_endpoint}/topics/new_topic"
        response = await api_client.patch(endpoint, json=["foo|bar"])

        assert response.status_code == 200
        assert set(response.json()["new_topic"]) == {"foo", "foo|bar"}
        assert len(self.napp._allowed["new_topic"]) == 2

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
