"""TODO: Module docs here"""
import logging
import os
import re
import socket
import threading
import time
import toml
import types
import xmltodict

from . import constants

class Client:
    """Encapsulates a TCPR connection to a specific KAG server.

    Args:
        name (str): A unique name for the client
        host (str): The IP address of the server
        port (int): The server's RCON port 
        rcon_password (str): The RCON password for the server
    """

    def __init__(self, name="client", host="localhost", port=50301, rcon_password="example",
                 log_directory=None):
        assert(isinstance(name, str))
        assert(isinstance(host, str))
        assert(isinstance(port, int))
        assert(isinstance(rcon_password, str))

        if log_directory != None:
            assert(isinstance(log_directory, str))

        self.name = name
        self.host = host
        self.port = port
        self.rcon_password = rcon_password
        self.log = None
        self._handlers = []
        self._in_multiline = False
        self._multiline_timestamp = None
        self._multiline_content = []

        self._setup_logging(log_directory)
        self.log.debug("Created client %s, %s:%s", name, host, port)

    def _setup_logging(self, log_directory):
        """Sets up a logging.Logger instance for the client, setting self.log.

        If `log_directory` is not provided then the client will log all messages to stdout.
        If `log_directory` is provided then the client will log to a file in the directory
        with a level of DEBUG, and to stdout with a level of INFO.

        Args:
            log_directory (str): The directory where log files will be saved
        """
        log = logging.getLogger(self.name)
        log.setLevel(logging.DEBUG)

        if log_directory:
            log_file = os.path.join(log_directory, "{}_log.txt".format(self.name))
            fh = logging.FileHandler(log_file)
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(logging.Formatter("[%(asctime)s]%(levelname)s: %(message)s"))
            log.addHandler(fh)

        sh = logging.StreamHandler()
        sh.setLevel(logging.INFO if log_directory else logging.DEBUG)
        sh.setFormatter(logging.Formatter("[%(asctime)s]%(name)s:%(levelname)s: %(message)s"))
        log.addHandler(sh)

        self.log = log

        if log_directory:
            self.log.info("%s logging to file %s", self.name, log_file)

    def add_handler(self, method_name, handler):
        """Adds a request handler to the client.

        Args:
            method_name (str): The name of the request method being handled
            handler (function): The handler function
        """
        assert(isinstance(method_name, str))
        assert(isinstance(handler, types.FunctionType))
        self.log.debug("Added handler (%s, %s)", method_name, handler.__name__)
        self._handlers.append((method_name, handler))

    def connect(self):
        """Connects to KAG and handles all TCPR lines received. Blocks until the server closes the connection.
        """
        self.log.debug("Connecting...")
        with socket.socket() as sock:
            try:
                sock.connect((self.host, self.port))
            except ConnectionError:
                self.log.warning("Couldn't connect to KAG. Is the server running?")
                return

            self.log.debug("Connected.")

            # The first line we send has to be the rcon password followed by a newline
            sock.send((self.rcon_password + "\n").encode())
            self.log.debug("Authenticated.")

            self.log.info("Listening...")
            # This will loop endlessly as long as the socket is open
            for line in sock.makefile('r'):
                # Detect server shutdown
                if re.match("^\d\d:\d\d:\d\dTCPR: server shutting down", line):
                    break
                else:
                    angelscript_code = self._handle_line(line)
                    if angelscript_code:
                        self.log.debug("Sending code \"%s\"", angelscript_code.rstrip())
                        sock.send(angelscript_code.encode())
        self.log.info("Disconnected.")

    def connect_forever(self):
        """Forever calls the client's connect method.
        """
        while True:
            try:
                self.connect() # should only return if there's an error or the server shuts down
            except Exception as e:
                self.log.error(e, exc_info=True)
            time.sleep(1)

    def connect_forever_in_thread(self):
        """Creates a daemon thread which runs the client, forever calling it's connect method

        Returns:
            threading.Thread: the thread created
        """
        thread = threading.Thread(name=self.name, target=self.connect_forever)
        thread.daemon = True
        thread.start()
        return thread

    def _handle_line(self, line):
        match = re.match("^\[(\d\d:\d\d:\d\d)\](.*)$", line)
        if not match:
            self.log.warning("Strangely formatted line: %s", line)
            return

        timestamp = match.group(1)
        content = match.group(2).strip()
        self.log.debug("Received (%s, \"%s\")", timestamp, content)

        if re.match("^<multiline>$", content):
            self.log.debug("Entered multiline")
            self._in_multiline = True
            self._multiline_timestamp = timestamp
            self._multiline_content = []
        elif re.match("^</multiline>$", content):
            if not self._in_multiline:
                self.log.error("Got closing multiline tag whilst not in a multiline block!")
            self.log.debug("Exited multiline")
            self._in_multiline = False
            timestamp = self._multiline_timestamp
            content = "".join(self._multiline_content)
            return self._handle_line("[{}] {}".format(timestamp, content))
        elif self._in_multiline:
            self._multiline_content.append(content)
        elif re.match("^<request>.*</request>$", content):
            req = self._parse_request(timestamp, content)
            if req:
                self.log.debug("parsed request")
                response = self._handle_request(req)
                status = constants.REQ_HANDLED

                if response == None:
                    response = ""
                    status = constants.REQ_FAILED

                # Escape any characters in the response which could cause problems
                response = response.replace("'", "").replace("\n", " ")
                self.log.info("Response: %s", response)

                code = "getRules().set_string('TCPR_RES{0}', '{1}'); getRules().set_u8('TCPR_REQ{0}', {2});\n".format(
                            req.req_id, response, status)
                if len(code) > constants.MAX_LINE_LENGTH:
                    self.log.error("Response code is too long (%d chars)", len(code))
                else:
                    return code

    def _parse_request(self, timestamp, content):
        """Attempts to parse a serialized request sent from KAG.

        Args:
            content (str): The content of the request

        Returns:
            Request: The parsed request
        """
        try:
            req = Request.from_xml(self.name, timestamp, content)
        except:
            self.log.error("Invalid request xml %s", content)
            return 
        return req

    def _handle_request(self, req):
        """Handles a request received from the TCPR connection
        """
        self.log.info("Request: %s, %s, %s", req.req_id, req.method, req.params)
        for (method, handler) in self._handlers:
            if method == req.method:
                self.log.debug("Using handler %s", handler.__name__)
                return handler(req)

class Request:
    """Represents a request received from KAG.
    """

    def __init__(self, client_name, timestamp, req_id, method, params):
        assert(isinstance(client_name, str))
        assert(isinstance(timestamp, str))
        assert(isinstance(req_id, str))
        assert(isinstance(method, str))
        assert(isinstance(params, dict))

        self.client_name = client_name
        self.timestamp = timestamp
        self.req_id = req_id
        self.method = method
        self.params = params

    @staticmethod
    def from_xml(client_name, timestamp, xml):
        parsed = xmltodict.parse(xml)
        req_dict = parsed["request"]
        req = Request(client_name, timestamp, req_dict["id"], req_dict["method"], req_dict["params"])
        return req

def load_clients_from_config_file(config_file_path, log_directory=None):
    config = toml.load(config_file_path)

    clients = []
    for (client_name, server_config) in config.items():
        client = Client(name=client_name, host=server_config["host"], port=server_config["port"],
                        rcon_password=server_config["rcon_password"], log_directory=log_directory)
        clients.append(client)

    return clients

def run_clients(clients):
    threads = [client.connect_forever_in_thread() for client in clients]

    while True:
        if not any(thread.is_alive() for thread in threads):
            break

        time.sleep(1)
