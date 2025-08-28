"""Helper class for simulation functions"""

import asyncio


async def simulate_successful_delay(*_) -> None:
    """Simulate a delay for aiokafkaproducer.start()"""
    await asyncio.sleep(0.2)
    return
