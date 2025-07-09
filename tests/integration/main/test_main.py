""" Test suite """

from kafka_events.main import Main


class TestMain:
    """Test class for main"""

    async def test_setup(self):
        """Test that main's setup function works correctly"""
        main = Main(None)
        main.setup()

    async def test_execute(self):
        """Test that main has an execute method"""
        main = Main(None)
        main.execute()

    async def test_shutdown(self):
        """Test that main has a shutdown method"""
        main = Main(None)
        main.shutdown()
