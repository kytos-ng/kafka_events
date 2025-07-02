""" An abstract base class used for abstracting the contents of the Kafka domain away from main """

from abc import ABC, abstractmethod


class KafkaManager(ABC):
    """The public interface to be used by main for the Kafka domain"""

    @abstractmethod
    async def send(self, event: str, message: any) -> None:
        """The public method to send data to kafka"""

    @abstractmethod
    async def setup(self) -> None:
        """The public method to setup the producer instance"""

    @abstractmethod
    def shutdown(self) -> None:
        """The public method to shutdown the producer instance"""
