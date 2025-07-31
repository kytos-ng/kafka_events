""" Kytos/kafka_events """

import asyncio
from asyncio import AbstractEventLoop

from napps.kytos.kafka_events.managers.kafka.handler import KafkaManager
from kytos.core import KytosEvent, KytosNApp, log
from kytos.core.helpers import alisten_to


class Main(KytosNApp):
    """
    Main class of the Kytos/kafka_events NApp.
    """

    def setup(self):
        """
        Setup the kafka_events/Kytos NApp
        """
        log.info("SETUP Kytos/kafka_events")

        self._tasks: list[asyncio.Task] = []

        self._kafka_handler: KafkaManager = KafkaManager()
        self._async_loop: AbstractEventLoop = asyncio.get_running_loop()

        self._tasks.append(self._async_loop.create_task(self._kafka_handler.setup()))

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

    @alisten_to(".*")
    async def handle_events(self, event: KytosEvent):
        """
        Handle and process KytosEvents

        Accepts every propagated event (uses .* regex syntax)
        """
        await self._kafka_handler.send(event)
