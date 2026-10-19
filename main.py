""" Kytos/kafka_events """

import pathlib
import re
import asyncio
from asyncio import AbstractEventLoop
from collections import defaultdict
from napps.kytos.kafka_events.settings import BLOCKED_PATTERNS
from napps.kytos.kafka_events.managers.kafka.handler import KafkaManager
from kytos.core import KytosEvent, KytosNApp, log, rest
from kytos.core.helpers import alisten_to, load_spec, avalidate_openapi
from kytos.core.rest_api import JSONResponse, Request, aget_json_or_400, HTTPException
from .controllers import TopicController


class Main(KytosNApp):
    """
    Main class of the Kytos/kafka_events NApp.
    """

    spec = load_spec(pathlib.Path(__file__).parent / "openapi.yml")

    def setup(self):
        """
        Setup the kafka_events/Kytos NApp
        """
        log.info("SETUP Kytos/kafka_events")
        self.topic_controller = self.get_topic_controller()

        self._tasks: list[asyncio.Task] = []
        self._kafka_handler: KafkaManager = KafkaManager()
        self._async_loop: AbstractEventLoop = asyncio.get_running_loop()
        self._blocked: list[re.Pattern] = [
            re.compile(pattern) for pattern in BLOCKED_PATTERNS
        ]
        self._allowed: dict[str, list[re.Pattern]] = defaultdict(list)
        self.set_allowed_topics()

        self._tasks.append(self._async_loop.create_task(self._kafka_handler.setup()))
        self.aldo = None

    def execute(self):
        """
        Setup the kafka_events/Kytos NApp
        """
        log.info("EXECUTE Kytos/kafka_events")

    def shutdown(self):
        """
        Execute when your napp is unloaded.
        """
        log.info("SHUTDOWN kafka_events/Kytos")
        self._kafka_handler.shutdown(self._async_loop)

    @staticmethod
    def get_topic_controller() -> TopicController:
        """
        Initialize and return the TopicController instance.
        """
        return TopicController()

    def set_allowed_topics(self, allowed_topics: dict[str, list[str]] = None) -> None:
        """
        Set the allowed topics and their patterns.
        """
        if allowed_topics is None:
            allowed_topics = self.topic_controller.get_allowed_topics_patterns()

        for topic, patterns in allowed_topics.items():
            self._allowed[topic] = []
            for pattern in patterns:
                self._allowed[topic].append(re.compile(pattern))

    @alisten_to(".*")
    async def handle_events(self, event: KytosEvent):
        """
        Handle and process KytosEvents

        Accepts every propagated event (uses .* regex syntax)
        """
        for pattern in self._blocked:
            if pattern.search(event.name):
                return

        chosen_topic = None
        for topic, patterns in self._allowed.items():
            for pattern in patterns:
                if pattern.search(event.name):
                    chosen_topic = topic
                    break

        await self._kafka_handler.send(event, chosen_topic)

    @rest("v1/topics", methods=["GET"])
    @avalidate_openapi(spec)
    async def get_topics(self, _request: Request) -> JSONResponse:
        """
        Get the list of topics.
        """
        allowed = {}
        for topic, patterns in self._allowed.items():
            allowed[topic] = [p.pattern for p in patterns]
        content = {
            "allowed": allowed,
            "blocked": [p.pattern for p in self._blocked],
        }
        return JSONResponse(content=content)

    @rest("v1/topics", methods=["POST"])
    @avalidate_openapi(spec)
    async def add_topics(self, request: Request) -> JSONResponse:
        """
        Add the topics from the request
        """
        data = await aget_json_or_400(request)
        for topic in data.keys():
            if topic in self._allowed:
                msg = (
                    f"Topic {topic} is already added, "
                    f"Did you mean to replace or append?."
                )
                raise HTTPException(400, detail=msg)
            # patterns arrays are checked with the openapi spec

        # Add to database first
        self.topic_controller.insert_allowed_topics(data)
        self.set_allowed_topics(data)

        return JSONResponse(content={"topics": list(data.keys())}, status_code=201)

    @rest("v1/topics/{topic}", methods=["DELETE"])
    @avalidate_openapi(spec)
    async def delete_topic(self, request: Request) -> JSONResponse:
        """
        Delete the topics from the request
        """
        topic = request.path_params["topic"]
        if topic not in self._allowed:
            msg = f"Topic {topic} is not present in the allowed list."
            raise HTTPException(404, detail=msg)
        self._allowed.pop(topic)
        self.topic_controller.delete_allowed_topic(topic)
        msg = {"response": f"Topic {topic} has been removed from the allowed list."}
        return JSONResponse(msg, status_code=200)

    @rest("v1/topics/{topic}", methods=["PATCH"])
    @avalidate_openapi(spec)
    async def update_topic(self, request: Request) -> JSONResponse:
        """
        Update (add) new topics from the request to the selected topic.
        Duplicates are removed.
        """
        topic = request.path_params["topic"]

        if topic not in self._allowed:
            raise HTTPException(
                404, detail=f"Topic {topic} is not present in the allowed list."
            )

        topics = await aget_json_or_400(request)

        old_topic = set(pat.pattern for pat in self._allowed[topic])
        new_topic = set(topics)

        adding_topics = new_topic | old_topic
        mod_topic = {topic: list(adding_topics)}
        self.set_allowed_topics(mod_topic)
        self.topic_controller.insert_allowed_topics(mod_topic)

        return JSONResponse(content=mod_topic, status_code=200)

    @rest("v1/topics/{topic}", methods=["PUT"])
    @avalidate_openapi(spec)
    async def replace_pattern(self, request: Request) -> JSONResponse:
        """
        Replace the patterns from the request to the selected topic.
        """
        topic = request.path_params["topic"]

        if topic not in self._allowed:
            raise HTTPException(
                404, detail=f"Topic {topic} is not present in the allowed list."
            )

        patterns = await aget_json_or_400(request)
        self.set_allowed_topics({topic: patterns})
        self.topic_controller.insert_allowed_topics({topic: patterns})

        return JSONResponse(content={topic: patterns}, status_code=200)
