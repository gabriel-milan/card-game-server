from functools import partial
import json
from threading import Thread

from typer import Typer

from card_game_server.client import Client
from card_game_server.logger import log

app = Typer()


def echo_messages(client: Client) -> None:
    """
    Echoes messages from server
    """
    while True:
        try:
            messages = client.get_messages()
            if len(messages) != 0:
                for message in messages:
                    message = json.loads(message)
                    log(message)
        except Exception as exc:
            log(f"Got exception when fetching messages: {exc}", "error")


@app.command()
def start(
    server_host: str,
    server_port_tcp: int = 1234,
    server_port_udp: int = 1234,
    client_port_udp: int = 1235,
):
    """
    Starts a client for the game server
    """
    client = Client(
        server_host=server_host,
        server_port_tcp=server_port_tcp,
        server_port_udp=server_port_udp,
        client_port_udp=client_port_udp,
    )
    thread_echo = Thread(target=partial(echo_messages, client), daemon=True)
    thread_echo.start()
    # TODO: implement interactive CLI
