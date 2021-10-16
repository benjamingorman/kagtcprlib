# kagtcprlib &middot; ![AUR](https://img.shields.io/aur/license/yaourt.svg) [![Build Status](https://travis-ci.org/benjamingorman/kagtcprlib.svg?branch=master)](https://travis-ci.org/benjamingorman/kagtcprlib)


A TCPR library for King Arthur's Gold, aiming to provide a simple solution for writing interesting TCPR mods.

* Supports async connections to multiple KAG servers.

`kagtcprlib` is available from PyPi. To install: `pip install kagtcprlib`

The basic design of the library is that the user creates a `Client` instance:

```python
client = Client(nickname="playercount", host="localhost", port=50301, rcon_password="ilovetrenchrun")
```

Then adds some handlers to it:

```python
client.add_handler(PingHandler())
```

Then calls the client's `connect` method:

```python
client.connect()
```

Whenever the client receives a line of text from KAG, all matching handlers will be run. If any handler returns some text, it will be sent back to KAG as an RCON command.

What each handler does is totally up to the user. This could involve creating entries in a database, posting to a web API, or just logging to a file.

## Example

```python
import logging
import kagtcprlib
from kagtcprlib.handlers import BaseHandler

class PingHandler(BaseHandler):
    """Respond to 'ping' from KAG with code to print 'pong' in chat.
    """
    def handle(self, client_nickname, timestamp, content):
        if content == "ping":
            logging.info("Got ping from %s, sending pong.", client_nickname)
            return "getNet().server_SendMsg('pong');"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    client = kagtcprlib.Client(nickname="playercount", host="localhost", port=50301,
                               rcon_password="ilovetrenchrun")

    client.add_handler(PingHandler())
    client.connect_forever()
```

For more examples see the `examples/` folder.

## Contributing

You are welcome to contribute to this project.

Please ensure your feature branch is based on the `master` branch and is named like `feature-foo-bar`.

You must run `pylint` over your code and ensure it receives at least a score of 9.

## Docs

<https://benjamingorman.github.io/kagtcprlib/>
