""" Test suite """

from ...main import Main


class TestMain:
    """Test class for main"""

    def test_setup(self):
        """Test that main has a setup method"""
        main = Main(None)
        main.setup()

    def test_execute(self):
        """Test that main has an execute method"""
        main = Main(None)
        main.execute()

    def test_shutdown(self):
        """Test that main has a shutdown method"""
        main = Main(None)
        main.shutdown()
