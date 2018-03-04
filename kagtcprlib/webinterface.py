"""Module webinterface provides a web interface to show the status of each
KAG server connected.
To run it, you must provide a config .toml file containing the details of
each server you wish to connect to.

Example:
    $ python -m kagtcprlib.webinterface example_config_file.toml

Now navigate to http://localhost:8000 and you should be able to see the interface.
"""
import argparse
import http.server
import json
import logging
import os
import threading
import time
import webbrowser
from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket

from .client import load_clients_from_config_file
from .handlers import BaseHandler, PlayerCountHandler

CLIENTS_LIST = []
CLIENTS_DESCRIPTION_HASH = None  # used to detect whether a re-sync needs to occur
WEBSOCKET_SERVER = None


class MyWebSocketServer(SimpleWebSocketServer):
    """Extension of SimpleWebSocketServer which allows for broadcasting a
    SocketMsg to all connected sockets.
    """

    def broadcast(self, msg):
        """Broadcasts a SocketMsg to all connected websockets.

        Args:
            msg (SocketMsg): The message to send
        """
        assert(isinstance(msg, SocketMsg))
        for (_, conn) in self.connections.items():
            conn.sendMessage(msg.json())


class KagClientInfoSocket(WebSocket):
    """Extension of WebSocket used to handle the connection to the browser.
    """

    def handleMessage(self):
        logging.info("Received message %s", self.data)
        try:
            data = json.loads(self.data)
        except json.decoder.JSONDecodeError:
            logging.error("Received a message which could not be parsed")
            return
        msg = SocketMsg(data["message"], data["data"])
        handle_incoming_message(msg)

    def handleConnected(self):
        logging.info(self.address, "websocket connected")
        self.send_clients_list()

    def handleClosed(self):
        logging.info(self.address, "websocket closed")

    def send_clients_list(self):
        msg = SocketMsg("clients_list", get_client_descriptions())
        self.sendMessage(msg.json())


class SocketMsg:
    """A message to be sent over the WebSocket to browsers.

    Args:
        type (str): The type of the message.
            This identifies what kind of message this is, and what the data will be.
        data (any): The message's data. This could be any type which is JSON serializable.
    """

    def __init__(self, type, data):
        assert(isinstance(type, str))
        self.type = type
        self.data = data

    def json(self):
        """Serializes the SocketMsg as a JSON string

        Returns:
            str: The serialized SocketMsg
        """
        msg = {"message": self.type, "data": self.data}
        return json.dumps(msg)


class WebSocketBroadcastHandler(BaseHandler):
    """This handler, whenever it receives a line, will broadcast it to all
    connected WebSockets.
    """
    def handle(self, client_nickname, timestamp, content):
        msg = SocketMsg("tcpr_line", {"nickname": client_nickname, "timestamp": timestamp,
                                      "content": content})
        WEBSOCKET_SERVER.broadcast(msg)


def get_client_description(client):
    """Returns useful info about the given Client.

    Args:
        client (Client): The client
    Returns:
        dict: The description
    """
    desc = {"nickname": client.nickname, "host": client.host, "port": client.port,
            "connected": client.is_connected()}
    pch = client.get_handler(PlayerCountHandler)
    if pch:
        desc["player_count"] = pch.player_count
    return desc


def get_client_descriptions():
    """Returns the descriptions of each Client in CLIENT_LIST.

    Returns:
        list(dict): The descriptions
    """
    return [get_client_description(client) for client in CLIENTS_LIST]


def get_client_by_name(nickname):
    """Returns the client identified by `nickname` from CLIENT_LIST.

    Args:
        nickname (str): The nickname of the client
    """
    for client in CLIENTS_LIST:
        if client.nickname == nickname:
            return client
    return None


def sync_clients():
    """Works out whether the description of any clients has changed, and if so
    broadcasts the change to all connected websockets.
    """
    global CLIENTS_DESCRIPTION_HASH
    descriptions = get_client_descriptions()
    descriptions_json = json.dumps(descriptions)
    desc_hash = hash(descriptions_json)

    # Hashing the descriptions allows us to know when we need to re-sync
    if desc_hash != CLIENTS_DESCRIPTION_HASH:
        logging.debug("Re-syncing")
        CLIENTS_DESCRIPTION_HASH = desc_hash
        msg = SocketMsg("clients_list", descriptions)
        WEBSOCKET_SERVER.broadcast(msg)


def sync_clients_worker():
    while True:
        time.sleep(1)
        sync_clients()


def handle_incoming_message(msg):
    """Handles an incoming SocketMsg from a client.
    This occurs for example, when a user types a line of text into the TCPR prompt
    in the browser.

    Args:
        msg (SocketMsg): The message received from the connection.
    """
    if msg.type == "tcpr_prompt_line":
        client_nickname = msg.data["nickname"]
        line = msg.data["line"]

        client = get_client_by_name(client_nickname)
        if not client:
            logging.error("Received a 'tcpr_prompt_line' msg with an unknown client nickname")
            return
        else:
            logging.info("Sending to client %s: %s", client_nickname, line)
            client.send(line)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("config_file", help="Path to the clients config file")
    parser.add_argument("--port", help="Which port to run on", default=8000)
    parser.add_argument("--dev", help="Whether to enable dev mode", action='store_true')
    parser.add_argument("--ws-port", help="Which port should the WebSocket server run on",
                        default=8001)
    args = parser.parse_args()

    log_level = logging.INFO
    if args.dev:
        log_level = logging.DEBUG
    logging.basicConfig(level=log_level)

    assert(os.path.isfile(args.config_file))
    CLIENTS_LIST = load_clients_from_config_file(args.config_file)

    bch = WebSocketBroadcastHandler()
    for client in CLIENTS_LIST:
        client.add_handler(PlayerCountHandler())
        client.add_handler(bch)
        client.connect_forever_in_thread()

    # Change directory to web/ to ensure the server only serves files from there
    web_dir = os.path.join(os.path.dirname(__file__), 'web')
    os.chdir(web_dir)

    # Setup WebSocket server
    logging.info("WebSocket server serving on {}".format(args.ws_port))
    WEBSOCKET_SERVER = MyWebSocketServer('', args.ws_port, KagClientInfoSocket)
    ws_thread = threading.Thread(name="websocketserver", target=WEBSOCKET_SERVER.serveforever)
    ws_thread.daemon = True
    ws_thread.start()

    # Setup syncer
    syncer_thread = threading.Thread(name="syncer", target=sync_clients_worker)
    syncer_thread.daemon = True
    syncer_thread.start()

    webbrowser.open("http://localhost:{}".format(args.port))

    # Setup main http server
    logging.info("HTTP serving on {}".format(args.port))
    server_address = ('', args.port)
    httpd = http.server.HTTPServer(server_address, http.server.SimpleHTTPRequestHandler)
    httpd.serve_forever()
