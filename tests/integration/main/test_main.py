""" Test suite """

import asyncio

from main import Main


class TestMain:
    """Test class for main"""

    async def test_setup_and_shutdown(self):
        """Test that main's setup and shutdown function works correctly"""
        main = Main(None)
        main.setup()

        await asyncio.sleep(1)

        main.shutdown()

    async def test_execute(self):
        """Test that main has an execute method"""
        main = Main(None)

        await asyncio.sleep(1)

        main.execute()
        main.shutdown()
