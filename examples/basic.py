"""This example looks for lines that looks like "ping".
When it receives one it sends code back to KAG to make it print "pong" in chat.
"""
import logging
import kagtcprlib
from kagtcprlib.handlers import BaseHandler

class PingHandler(BaseHandler):
    """Respond to 'ping' from KAG with code to print 'pong' in chat.
    """
    def handle(self, timestamp, content):
        if content == "ping":
            logging.info("Got ping, sending pong.")
            return "getNet().server_SendMsg('pong');"

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    client = kagtcprlib.Client(nickname="playercount", host="localhost", port=50301, rcon_password="ilovetrenchrun")

    client.add_handler(PingHandler())
    client.connect_forever()
