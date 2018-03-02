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

    def test_looks_like_chat_msg(self):
        self.assertTrue(utils.looks_like_chat_msg("<Joan of Arc> Hey"))
        self.assertFalse(utils.looks_like_chat_msg("example"))
