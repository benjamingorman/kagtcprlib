import kagtcprlib

def ping_handler(req):
    """Responds to a "ping" request with a "pong"
    """
    return "pong"

if __name__ == "__main__":
    clients = kagtcprlib.load_clients_from_config_file("basic_config.toml")

    for client in clients:
        client.add_handler("ping", ping_handler)

    kagtcprlib.run_clients(clients)
