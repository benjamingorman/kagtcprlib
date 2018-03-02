"""Module xmlrequesthandler contains a handler class for working with the xml-style requests
that KAGLadder uses.
"""
import re
import logging
import types
import xml.parsers.expat
import xmltodict

from ... import handlers

# These constants should be kept the same as those in the KAGLadder AngelScript TCPR library
REQ_UNUSED = 0
REQ_SENT = 1
REQ_HANDLED = 2
REQ_FAILED = 3

MULTILINE_MAX_LINES = 100


class Request:
    """Represents a request received from KAG.

    Args:
        client_name (str): The nickname of the `Client` that received the request
        timestamp (str): The timestamp of the request
        req_id (str): The id of the request
        method (str): The method of the request. This identifies what type of request it is
            and how it should be handled. e.g. "getplayercoins"
        params (dict): Additional information about the request. e.g. {"username": "Eluded"}
    """
    def __init__(self, client_name, timestamp, req_id, method, params):
        # pylint: disable=too-many-arguments
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
    def from_xml(client_name, timestamp, req_xml):
        """Creates a new `Request` from the given XML string

        Args:
            client_name (str): The nickname of the `Client` that received the request
            timestamp (str): The timestamp of the request
            req_xml (str): The xml string which is the serialized request
        """
        parsed = xmltodict.parse(req_xml)
        req_dict = parsed["request"]
        req = Request(client_name, timestamp, req_dict["id"], req_dict["method"],
                      req_dict["params"] or {})
        return req


class XMLRequestHandler(handlers.BaseHandler):
    """Deals with the XML-style requests which KAGLadder uses.
    Supports requests which exceed the 16k line limit via use of <multiline> tags.
    Use this handler by adding 'method handlers' for every different request method.
    The correct method handler will be delegated to based on the `method` parameter in the request.

    Example:
        >>> handler = XMLRequestHandler()
        >>> handler.add_method_handler("ping", lambda req: "pong")
        >>> # Now incoming requests with a method of "ping" will be responded to with "pong"
        >>> handler.handle("[00:00:00]",
                "<request><method>ping</method><id>1</id><params></params></request>")
        "pong"
    """

    def __init__(self):
        super(handlers.BaseHandler, self).__init__()
        self._method_handlers = []
        self._in_multiline = False
        self._multiline_timestamp = None
        self._multiline_content = []
        self._log = logging.getLogger(name="XMLRequestHandler")

    def handle(self, timestamp, content):
        """Handle incoming lines, dealing with <multiline> tags.
        """
        # When we see an opening <multiline> tag, start recording all lines seen
        # when the closing </multiline> comes, handle the line which is the concatenation
        # of all recorded lines.
        if re.match("^<multiline>$", content):
            self._log.debug("Entered multiline")
            self._in_multiline = True
            self._multiline_timestamp = timestamp
            self._multiline_content = []
        elif re.match("^</multiline>$", content):
            if not self._in_multiline:
                self._log.error("Got closing multiline tag whilst not in a multiline block!")
                return None
            self._log.debug("Exited multiline")
            self._in_multiline = False
            timestamp = self._multiline_timestamp
            content = "".join(self._multiline_content)
            return self._handle_line(timestamp, content)
        elif self._in_multiline:
            if len(self._multiline_content) > MULTILINE_MAX_LINES:
                # Avoid potential memory leak due to KAG sending invalid pairs of <multiline> tags
                self._log.warning(
                    "Excess multiline lines received. Did KAG send invalid pairs of tags?")
                self._in_multiline = False
            else:
                self._multiline_content.append(content)
        elif re.match("^<request>.*</request>$", content):
            return self._handle_line(timestamp, content)
        return None

    def add_method_handler(self, method_name, method_handler):
        """Adds a handler function which responds to requests of the matching method.

        Args:
            method_name (str): The name of the method e.g. "ping"
            method_handler (types.FunctionType): A function to run on the request
                The function should return a single string as the response e.g. "pong"
        """
        assert(isinstance(method_name, str))
        assert(isinstance(method_handler, types.FunctionType))
        self._method_handlers.append((method_name, method_handler))

    def _handle_line(self, timestamp, content):
        """Handles a received line (could be from a multi-line block)

        Args:
            timestamp (str): The timestamp of the line
            content (str): The content of the line
        """
        req = self._parse_request(timestamp, content)
        if req:
            self._log.debug("parsed request")
            response = self._handle_request(req)
            status = REQ_HANDLED

            if not response:
                response = ""
                status = REQ_FAILED

            # Escape any characters in the response which could cause problems
            response = response.replace("'", "").replace("\n", " ")
            self._log.info("Response: %s", response)

            return format_angelscript_response(req.req_id, response, status)
        return None

    def _parse_request(self, timestamp, content):
        """Attempts to parse a serialized request sent from KAG.

        Args:
            content (str): The content of the request

        Returns:
            Request: The parsed request
        """
        try:
            # TODO: client nickname is not passed as a parameter to `handle` yet
            # How can we get it here?
            req = Request.from_xml("TODO", timestamp, content)
            return req
        except (ValueError, xml.parsers.expat.ExpatError):
            self._log.error("Invalid request xml %s", content)
            return None

    def _handle_request(self, req):
        """Handles a received request
        """
        self._log.info("Request: %s, %s, %s", req.req_id, req.method, req.params)
        for (method, handler) in self._method_handlers:
            if method == req.method:
                self._log.debug("Using handler %s", handler.__name__)
                return handler(req)
        return None


def format_angelscript_response(req_id, response, status):
    """Returns an angelscript string to send back to the mod.
    """
    lines = ["getRules().set_string('TCPR_RES{0}', '{1}');".format(req_id, response),
             "getRules().set_u8('TCPR_REQ{0}', {2});".format(req_id, status)]
    return " ".join(lines)
