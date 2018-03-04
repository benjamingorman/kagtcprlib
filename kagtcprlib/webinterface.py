"""Module webinterface provides a web interface to show the status of each
KAG server connected.
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
        assert(isinstance(msg, SocketMsg))
        for (_, conn) in self.connections.items():
            conn.sendMessage(msg.json())


class KagClientInfoSocket(WebSocket):

    def handleMessage(self):
        # echo
        self.sendMessage(self.data)

    def handleConnected(self):
        print(self.address, "websocket connected")
        self.send_clients_list()

    def handleClosed(self):
        print(self.address, "websocket closed")

    def send_clients_list(self):
        msg = SocketMsg("clients_list", get_client_descriptions())
        self.sendMessage(msg.json())


class SocketMsg:
    """A message to be sent over the WebSocket to browsers.
    """
    def __init__(self, type, data):
        assert(isinstance(type, str))
        self.type = type
        self.data = data

    def json(self):
        msg = {"message": self.type, "data": self.data}
        return json.dumps(msg)


class WebSocketBroadcastHandler(BaseHandler):
    """Handler which, whenever it receives a line, will broadcast it to all
    connected WebSockets.
    """
    def handle(self, client_nickname, timestamp, content):
        msg = SocketMsg("tcpr_line", {"nickname": client_nickname, "timestamp": timestamp,
                                      "content": content})
        WEBSOCKET_SERVER.broadcast(msg)


def get_client_description(client):
    desc = {"nickname": client.nickname, "host": client.host, "port": client.port,
            "connected": client.is_connected()}
    pch = client.get_handler(PlayerCountHandler)
    if pch:
        desc["player_count"] = pch.player_count
    return desc


def get_client_descriptions():
    return [get_client_description(client) for client in CLIENTS_LIST]


def sync_clients():
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
    print("WebSocket server serving on {}".format(args.ws_port))
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
    print("Serving on {}".format(args.port))
    server_address = ('', args.port)
    httpd = http.server.HTTPServer(server_address, http.server.SimpleHTTPRequestHandler)
    httpd.serve_forever()
