# kagtcprlib

A TCPR library for King Arthur's Gold, aiming to provide a simple solution for writing interesting TCPR mods.

* Supports async connections to multiple KAG servers.

## Example

```python
import logging
import re
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
```

## Contributing

You are welcome to contribute to this project.

Please ensure your feature branch is based on the `dev` branch and is named like `feature-foo-bar`.

You must run `pylint` over your code and ensure it receives at least a score of 9.

## Docs
