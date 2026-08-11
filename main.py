""" Kytos/kafka_events """

import pathlib
import re
import asyncio
from asyncio import AbstractEventLoop

import plotly.graph_objects as go
import psutil

from napps.kytos.kafka_events.settings import BLOCKED_PATTERNS
from napps.kytos.kafka_events.managers.kafka.handler import KafkaManager
from kytos.core import KytosEvent, KytosNApp, log, rest
from kytos.core.helpers import alisten_to, load_spec
from kytos.core.rest_api import JSONResponse, Request

from random import choice, randint
from string import ascii_uppercase

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

        self._tasks: list[asyncio.Task] = []
        self._kafka_handler: KafkaManager = KafkaManager()
        self._async_loop: AbstractEventLoop = asyncio.get_running_loop()
        self._blocked: list[re.Pattern] = [
            re.compile(pattern) for pattern in BLOCKED_PATTERNS
        ]
        self._process = psutil.Process()
        self._process.cpu_percent()
        self.cpu_count = psutil.cpu_count()

        self._tasks.append(self._async_loop.create_task(self._kafka_handler.setup()))
        self._tasks.append(self._async_loop.create_task(self.set_stats()))

        self.events_received = 0
        self.events_sent = 0
        self.events_dropped = 0

        self.list_received = []
        self.list_sent = []
        self.list_dropped = []
        self.list_cpu = []
        self.list_ram = []
        self.last_event = None
        self.counter = 0
        self.stop_it = False

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

    def reset_stats(self):
        """
        Reset the statistics of the NApp.
        """
        self.list_received = []
        self.list_sent = []
        self.list_dropped = []
        self.list_cpu = []
        self.list_ram = []
        self._kafka_handler.list_eve_sent = []

    def final_stats(self):
        self._kafka_handler.list_eve_sent.append(self._kafka_handler.eve_err)
        self.list_received.append(self.events_received)
        self.list_sent.append(self.events_sent)
        self.list_dropped.append(self.events_dropped)
        self.list_cpu.append(self._process.cpu_percent()/self.cpu_count)
        self.list_ram.append(self._process.memory_info().rss)
        self.events_received = 0
        self._kafka_handler.eve_err = 0
        self.events_sent = 0
        self.events_dropped = 0

    async def set_stats(self):
        while True and not self.stop_it:
            self._kafka_handler.list_eve_sent.append(self._kafka_handler.eve_err)
            self.list_received.append(self.events_received)
            self.list_sent.append(self.events_sent)
            self.list_dropped.append(self.events_dropped)
            self.list_cpu.append(self._process.cpu_percent()/self.cpu_count)
            self.list_ram.append(self._process.memory_info().rss)
            self.events_received = 0
            self._kafka_handler.eve_err = 0
            self.events_sent = 0
            self.events_dropped = 0
            await asyncio.sleep(1)

    def close_it(self):
        self.stop_it = True
        self.final_stats()
        self.create_graphs()

    def create_graphs(
        self,
        include_dropped: bool = False,
        output_dir: pathlib.Path | str | None = None,
    ) -> dict[str, pathlib.Path]:
        output_path = (
            pathlib.Path(output_dir)
            if output_dir
            else pathlib.Path(__file__).parent / "images"
        )
        output_path.mkdir(parents=True, exist_ok=True)
        samples = list(range(len(self.list_sent)))

        events_figure = go.Figure()
        events_figure.add_trace(
            go.Scatter(x=samples, y=self.list_sent, mode="lines", name="Sent")
        )
        events_figure.add_trace(
            go.Scatter(
                x=samples,
                y=self._kafka_handler.list_eve_sent,
                mode="lines",
                name="Errors",
            )
        )
        if include_dropped:
            events_figure.add_trace(
                go.Scatter(
                    x=samples,
                    y=self.list_dropped,
                    mode="lines",
                    name="Dropped",
                )
            )
        events_figure.update_layout(
            title="Kafka Events",
            xaxis_title="Seconds",
            yaxis_title="Events per second",
        )
        # Total displayed
        total_events = sum(self.list_sent)
        total_errors = sum(self._kafka_handler.list_eve_sent)
        events_figure.add_annotation(
            x=0.01,
            y=0.99,
            xref="paper",
            yref="paper",
            xanchor="left",
            yanchor="top",
            align="left",
            showarrow=False,
            text=(
                f"Total Events: {total_events:,}<br>"
                f"Total Errors: {total_errors:,}"
            ),
            bordercolor="black",
            borderwidth=1,
            borderpad=6,
            bgcolor="rgba(255,255,255,0.85)",
        )

        cpu_figure = go.Figure(
            data=[
                go.Scatter(
                    x=list(range(len(self.list_cpu))),
                    y=self.list_cpu,
                    mode="lines",
                    name="CPU",
                )
            ]
        )
        cpu_figure.update_layout(
            title="CPU Percentage",
            xaxis_title="Seconds",
            yaxis_title="CPU (%)",
        )
        cpu_figure.add_annotation(
            x=0.01,
            y=0.99,
            xref="paper",
            yref="paper",
            xanchor="left",
            yanchor="top",
            align="left",
            showarrow=False,
            text=(
                f"CPU Count: {self.cpu_count}<br>"
                f"Max CPU Usage: {max(self.list_cpu):.2f}%<br>"
            ),
            bordercolor="black",
            borderwidth=1,
            borderpad=6,
            bgcolor="rgba(255,255,255,0.85)",
        )

        ram_figure = go.Figure(
            data=[
                go.Scatter(
                    x=list(range(len(self.list_ram))),
                    y=[value / (1024 * 1024) for value in self.list_ram],
                    mode="lines",
                    name="RAM",
                )
            ]
        )
        ram_figure.update_layout(
            title="Memory Usage",
            xaxis_title="Seconds",
            yaxis_title="RAM (MiB)",
        )

        events_path = output_path / "events.html"
        cpu_path = output_path / "cpu.html"
        ram_path = output_path / "ram.html"

        events_figure.write_html(events_path)
        cpu_figure.write_html(cpu_path)
        ram_figure.write_html(ram_path)

        return {
            "events": events_path,
            "cpu": cpu_path,
            "ram": ram_path,
        }

    @alisten_to(".*")
    async def handle_events(self, event: KytosEvent):
        """
        Handle and process KytosEvents

        Accepts every propagated event (uses .* regex syntax)
        """
        if self.stop_it:
            return
        self.events_received += 1
        for pattern in self._blocked:
            if pattern.search(event.name):
                self.events_dropped += 1
                return
        self.last_event = event
        self.counter += 1
        event.content["counter"] = self.counter
        await self._kafka_handler.send(event)
        self.events_sent += 1

    @rest("v1/ended", methods=["POST"])
    async def end_test(self, _request: Request) -> JSONResponse:
        self.create_graphs()
        return JSONResponse(content={"message": "OKA."}, status_code=200)

    @rest("v1/filters", methods=["GET"])
    async def get_filters(self, _request: Request) -> JSONResponse:
        """
        Get the list of filters.
        """
        return JSONResponse(content={"filters": list(BLOCKED_PATTERNS)})

    def start_test(self, seconds=120, messages_per_second=5000, ) -> JSONResponse:
        async def run_test(seconds, messages_per_second, test):
            log.info(f"START TEST: {seconds} seconds, {messages_per_second} messages per second")
            for i in range(seconds):
                for _ in range(messages_per_second):
                    length = randint(800, 1500)  # Random length between 800 and 1500
                    my_string = ''.join(choice(ascii_uppercase) for i in range(length))
                    await self.controller.buffers.app.aput(
                        KytosEvent(f"kytos/kafka.test{test}", content={"value": my_string})
                    )
                await asyncio.sleep(1)
                log.info(f"TEST {i + 1}/{seconds} HAVE PASSED.")
            log.info("END TEST")
        messages_per_second = messages_per_second//4
        self._async_loop.create_task(run_test(seconds, messages_per_second, 1))
        self._async_loop.create_task(run_test(seconds, messages_per_second, 2))
        self._async_loop.create_task(run_test(seconds, messages_per_second, 3))
        self._async_loop.create_task(run_test(seconds, messages_per_second, 4))
