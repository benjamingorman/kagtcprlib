"""Module client contains the `Client` class, used to create a TCPR connection to KAG.
It also contains several useful utility functions for working with clients and config files.
"""
import logging
import re
import socket
import threading
import time
import toml

from . import constants
from . import exceptions
from . import handlers

class Client:
    """Encapsulates a TCPR connection to a specific KAG server.
    The way to use a Client is to create one, add some handlers to it, and then call the client's `connect()` method.
    Handlers are instances of `kagtcprlib.handlers.BaseHandler`.

    Args:
        nickname (str): A unique nickname for the client
        host (str): The IP address of the server
        port (int): The server's RCON port
        rcon_password (str): The RCON password for the server
    """

    def __init__(self, nickname="client", host="localhost", port=50301, rcon_password="example"):
        assert(isinstance(nickname, str))
        assert(isinstance(host, str))
        assert(isinstance(port, int))
        assert(isinstance(rcon_password, str))

        self.nickname = nickname
        self.host = host
        self.port = port
        self.rcon_password = rcon_password
        self._log = logging.getLogger(name=self.nickname)
        self._sock = None
        self._handlers = []

    def connect(self):
        """Connects to KAG and handles all TCPR lines received. Blocks until the server closes the connection.
        """
        self._log.debug("Connecting...")

        with socket.socket() as sock:
            self._sock = sock
            try:
                sock.connect((self.host, self.port))
            except ConnectionError:
                self._log.warning("Couldn't connect to KAG. Is the server running?")
                return

            self._log.debug("Connected.")

            # The first line we send has to be the rcon password
            self.send(self.rcon_password)
            # TODO: Detect if the password was wrong and raise an exception
            self._log.debug("Authenticated.")

            self._log.info("Listening...")
            # This will loop endlessly as long as the socket is open
            for line in sock.makefile('r', encoding='utf-8'):
                self._log.debug("Received: %s", line)
                # Detect server shutdown
                if re.match("^\d\d:\d\d:\d\dTCPR: server shutting down", line):
                    break
                else:
                    # If any handlers return text then send it over the connection
                    msgs_to_send = self._handle_line(line)
                    for msg in msgs_to_send:
                        if len(msg) > constants.MAX_LINE_LENGTH:
                            self._log.error("Message exceeds maximum line length, not sending it.")
                        else:
                            self.send(msg)

        # Null the socket reference to indicate the client is not connected
        self._sock = None

    def send(self, text):
        """Sends a line of text (probably angelscript code) to KAG.
        If the client is not connected a `NotConnectedException` will be raised.

        Args:
            text (str): The text to send. Note that excess whitespace is stripped and newlines are added automatically.
        """
        # TODO: improve this to query the socket object if it exists to see if it's
        # actually connected.
        if not self._sock:
            raise exceptions.NotConnectedException()

        text = text.strip() # remove whitespace
        self._sock.send("{0}\n".format(text).encode("utf-8"))

    def add_handler(self, handler):
        """Adds a new handler to the client.
        Handlers may be functions or instances of a `Handler` class.

        Args:
            handler (Handler): The handler to add
        """
        assert(isinstance(handler, handlers.BaseHandler))
        self._handlers.append(handler)

    def connect_forever(self):
        """Forever calls the client's connect method.
        """
        while True:
            try:
                self.connect() # should only return if there's an error or the server shuts down
            except KeyboardInterrupt:
                # Handle ctrl-c gracefully
                return
            except Exception as e:
                self._log.error(e, exc_info=True)
            time.sleep(1)

    def connect_forever_in_thread(self):
        """Creates a daemon thread which runs the client, forever calling it's connect method

        Returns:
            threading.Thread: the thread created
        """
        thread = threading.Thread(name=self.nickname, target=self.connect_forever)
        thread.daemon = True
        thread.start()
        return thread

    def _split_line(self, line):
        """Splits the line into timestamp and content.

        Args:
            line (str): Line received from KAG

        Returns:
            (str, str): timestamp, content
        """
        match = re.match("^(\[\d\d:\d\d:\d\d\])(.*)$", line)
        if not match:
            self._log.warning("Strangely formatted line: %s", line)
            (timestamp, content) = (None, line)
        else:
            (timestamp, content) = (match.group(1), match.group(2).strip())
        return (timestamp, content)

    def _handle_line(self, line):
        """Handles an incoming line from the TCPR connection, running any matching handlers.

        Args:
            line(str): The line received

        Returns:
            list(str): A list of messages to send back to KAG
        """
        timestamp, content = self._split_line(line)
        msgs_to_send = []
        for handler in self._handlers:
            if re.match(handler.regex, content):
                msg = handler.handle(timestamp, content)
                if msg:
                    msgs_to_send.append(msg)
        return msgs_to_send

def load_clients_from_config_file(config_file_path):
    """Loads a config toml file from the given path.
    Returns a list of clients created using the parameters in the config file.

    Args:
        config_file_path (str): Path to the config .toml file

    Returns:
        list(Client): List of Client instances
    """
    config = toml.load(config_file_path)

    clients = []
    for (client_nickname, server_config) in config.items():
        client = Client(nickname=client_nickname, host=server_config["host"], port=server_config["port"],
                        rcon_password=server_config["rcon_password"])
        clients.append(client)

    return clients

def run_clients(clients):
    """Utility function to run all the given clients.

    Args:
        clients (list(Client)): The list of clients to run
    """
    threads = [client.connect_forever_in_thread() for client in clients]

    while True:
        if not any(thread.is_alive() for thread in threads):
            break
        time.sleep(1)
