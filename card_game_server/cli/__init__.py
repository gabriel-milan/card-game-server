from threading import Lock

from typer import Typer

from card_game_server.models.rooms import Rooms
from card_game_server.server import TcpServer, UdpServer

app = Typer()

# app.add_typer(
#     client.app,
#     name="client",
#     help="Handles client implementation for the game server.",
# )


@app.command()
def start(capacity: int = 2, tcp_port: int = 1234, udp_port: int = 1234):
    """
    Starts the server.
    """
    lock = Lock()
    rooms = Rooms(capacity)
    udp_server = UdpServer(udp_port, rooms, lock)
    tcp_server = TcpServer(tcp_port, rooms, lock)
    udp_server.start()
    tcp_server.start()
    is_running = True

    print("Simple Game Server.")
    print("--------------------------------------")
    print("list : list rooms")
    print("room #room_id : print room information")
    print("user #user_id : print user information")
    print("quit : quit server")
    print("--------------------------------------")

    while is_running:
        cmd = input("cmd >")
        if cmd == "list":
            if len(rooms.rooms) == 0:
                print("No rooms.")
            else:
                print("Rooms :")
                for room in rooms.rooms:
                    print("%s - %s (%d/%d)" % (room.identifier,
                                               room.name,
                                               len(room.players),
                                               room.capacity))
            if len(rooms.players) == 0:
                print("No players.")
            else:
                print("Players :")
                for player in rooms.players:
                    print("%s - %s" % (player.identifier, player.address))
        elif cmd.startswith("room "):
            try:
                id = cmd[5:]
                room = rooms.get_room(id)
                print("%s - %s (%d/%d)" % (room.identifier,
                                           room.name,
                                           len(room.players),
                                           room.capacity))
                print("Players :")
                for player in room.players:
                    print(player.identifier)
            except:
                print("Error while getting room informations")
        elif cmd.startswith("user "):
            try:
                player = rooms.get_player(cmd[5:])
                print("%s : %s:%d" % (player.identifier,
                                      player.address))
            except:
                print("Error while getting user informations")
        elif cmd == "quit":
            print("Shutting down  server...")
            udp_server.stop()
            tcp_server.stop()
            is_running = False

    udp_server.join()
    tcp_server.join()
