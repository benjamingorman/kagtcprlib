"""Module handlers contains some example handlers which might be added to `Client` instances.
"""
from abc import ABC, abstractmethod
import os
import logging


class BaseHandler(ABC):
    """Abstract base class for handlers. Handlers are added to `Client`s and respond to lines
    of text received from KAG. The handler will only be called if the line matches it's regex.
    By default all lines are matched.

    Args:
        regex (str): A regular expression used to match lines from KAG
            (not including the timestamp). The line will only be handled if it matches the regex.
    """

    regex = ".*"

    @abstractmethod
    def handle(self, timestamp, line):
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

    def handle(self, timestamp, line):
        self._log.debug("%s %s", timestamp, line)
