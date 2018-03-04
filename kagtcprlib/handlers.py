"""Module handlers contains some example handlers which might be added to `Client` instances.
"""
from abc import ABC, abstractmethod
import os
import logging
import re

from . import utils


class BaseHandler(ABC):
    """Abstract base class for handlers. Handlers are added to `Client`s and respond to lines
    of text received from KAG.
    """

    @abstractmethod
    def handle(self, client_nickname, timestamp, line):
        """Handles a line of text received from KAG.
        If the handler returns a string it will be sent over the connection.

        Args:
            timestamp (str): The timestamp of the line
            line (str): The line received from kag
        """
        pass


class RotatingFileLoggingHandler(BaseHandler):
    """A handler which logs all the lines received to a file.
    Uses `RotatingFileHandler` internally.

    Args:
        log_directory (str): Path to the directory to place log files in
        file_name (str): The name of the log file
    """

    def __init__(self, log_directory, file_name):
        assert(os.path.isdir(log_directory))
        assert(isinstance(file_name, str) and len(file_name) > 0)
        log = logging.getLogger(file_name)
        log.setLevel(logging.DEBUG)
        log_file = os.path.join(log_directory, file_name)

        rfh = logging.handlers.RotatingFileHandler(log_file, maxBytes=100*1000000, backupCount=5)
        rfh.setLevel(logging.DEBUG)
        rfh.setFormatter(logging.Formatter("%(message)s"))
        log.addHandler(rfh)

        self._log = log

    def handle(self, client_nickname, timestamp, line):
        self._log.debug("%s %s", timestamp, line)


class PlayerCountHandler(BaseHandler):
    """Keeps a count of the number of players on a server by looking for lines like:
        Joan of Arc (Eluded) is now spectating
        Joan of Arc (Eluded) has joined Red Team
        Player Eluded left the game (players left 0)
    """
    def __init__(self):
        self.player_count = 0

    def handle(self, client_nickname, timestamp, content):
        match = re.match(r"^{0} connected as".format(utils.USERNAME_REGEX), content)
        old_player_count = self.player_count
        if match:
            self.player_count += 1

        match = re.match(r"^Player (.*) left the game \(players left (\d+)\)", content)
        if match:
            self.player_count = int(match.group(2))

        if old_player_count != self.player_count:
            logging.debug("PlayerCountHandler player count changed: %d", self.player_count)
