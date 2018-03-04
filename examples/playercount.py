"""This example is a basic player count monitor. It periodically prints out the number of
players on the server.
"""
import logging
import re
import kagtcprlib
from kagtcprlib.utils import USERNAME_REGEX
from kagtcprlib.handlers import BaseHandler


class PlayerCountHandler(BaseHandler):
    """Keeps a count of the number of players on a server by looking for lines like:
        Joan of Arc (Eluded) is now spectating
        Joan of Arc (Eluded) has joined Red Team
        Player Eluded left the game (players left 0)
    """
    def __init__(self):
        self.playerCount = 0

    def handle(self, client_nickname, timestamp, content):
        print("GOT", content)
        change = False

        match = re.match(r"^{0} connected as".format(USERNAME_REGEX), content)
        if match:
            change = True
            self.playerCount += 1

        match = re.match(r"^Player (.*) left the game \(players left (\d+)\)", content)
        if match:
            change = True
            self.playerCount = int(match.group(2))

        if change:
            logging.info("Player count: {}".format(self.playerCount))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    client = kagtcprlib.Client(nickname="playercount", host="localhost", port=50301,
                               rcon_password="ilovetrenchrun")

    client.add_handler(PlayerCountHandler())
    client.connect_forever()
