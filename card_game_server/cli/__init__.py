from typer import Typer

from card_game_server.cli import client

app = Typer()

app.add_typer(
    client.app,
    name="client",
    help="Handles client implementation for the game server.",
)
