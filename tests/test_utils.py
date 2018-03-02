import unittest
import re

from .context import kagtcprlib
import kagtcprlib.utils as utils

class TestUtils(unittest.TestCase):
    def test_username_regex(self):
        example_username = "Eluded_1-2-3"
        self.assertTrue(re.match(utils.USERNAME_REGEX, example_username))
        self.assertFalse(re.match(utils.USERNAME_REGEX, "bob#"))
        self.assertFalse(re.match(utils.USERNAME_REGEX, ""))
        self.assertTrue(re.match(utils.USERNAME_REGEX, "averyverylongusernamethatistoolong"))

    def test_handle_line(self):
        example_line = "[00:00:00] test123"
        handler = CountingHandler()
        self.client.add_handler(handler)
        msgs = self.client._handle_line(example_line)
        self.assertEqual(handler.linesHandled, 1)
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0], "foo")

        # It shouldn't handle if the regex doesn't match
        handler.regex = "x"
        self.client._handle_line(example_line)
        self.assertEqual(handler.linesHandled, 1)
