import unittest

from .context import kagtcprlib
import kagtcprlib.client
import kagtcprlib.handlers as handlers


class CountingHandler(handlers.BaseHandler):
    def __init__(self):
        self.linesHandled = 0

    def handle(self, client_nickname, timestamp, content):
        self.linesHandled += 1
        return "foo"


class TestClient(unittest.TestCase):
    def setUp(self):
        self.client = kagtcprlib.client.Client()

    def test_split_line(self):
        example_line = "[12:56:40] hello"
        (timestamp, content) = self.client._split_line(example_line)
        self.assertEqual(timestamp, "[12:56:40]")
        self.assertEqual(content, "hello")

    def test_handle_line(self):
        example_line = "[00:00:00] test123"
        handler = CountingHandler()
        self.client.add_handler(handler)
        msgs = self.client._handle_line(example_line)
        self.assertEqual(handler.linesHandled, 1)
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0], "foo")
