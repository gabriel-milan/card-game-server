import json
import socket
from threading import Lock, Thread
from typing import Any, List, Set, Tuple

from card_game_server.logger import log


class SocketThread(Thread):
    def __init__(
        self,
        address: Tuple[str, int],
        client: 'Client',
        lock: Lock,
    ):
        """
        Implements a socket within a thread.
        """
        super().__init__()
        self._client = client
        self._lock = lock
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.bind(address)

    def run(self):
        """
        Get responses from server.
        """
        while True:
            data, _ = self._sock.recvfrom(1024)
            self._lock.acquire()
            try:
                self._client.add_server_message(data)
            finally:
                self._lock.release()

    def stop(self):
        """
        Stops this thread.
        """
        self._sock.close()


class Client:  # pylint: disable=too-many-instance-attributes
    def __init__(
        self,
        server_host: str,
        server_port_tcp: int = 1234,
        server_port_udp: int = 1234,
        client_port_udp: int = 1235,
    ):
        """
        Client for communicating with the game server.
        """
        self._identifier: str = None
        self._server_messages: List[str] = []
        self._room_id = None
        self._client_udp: Tuple[str, int] = ("0.0.0.0", client_port_udp)
        self._lock = Lock()
        self._server_listener = SocketThread(
            self._client_udp,
            self,
            self._lock,
        )
        self._server_listener.start()
        self._server_udp: Tuple[str, int] = (server_host, server_port_udp)
        self._server_tcp: Tuple[str, int] = (server_host, server_port_tcp)
        self._sock_tcp: socket.socket = None

        self.register()

    def __str__(self) -> str:
        return f"<Client {self._identifier} (udp_port={self._client_udp[1]})>"

    def __repr__(self) -> str:
        return self.__str__()

    @property
    def identifier(self):
        """
        Returns the identifier of this client.
        """
        return self._identifier

    @property
    def room_id(self):
        """
        Returns the room id of this client.
        """
        return self._room_id

    def add_server_message(self, message: str):
        """
        Adds a server message to this object.
        """
        self._server_messages.append(message)

    def parse_data(self, data: str) -> Any:  # pylint: disable=no-self-use
        """
        Parses payload from server.
        """
        try:
            data = json.loads(data)
            if data["success"]:
                return data["message"]
            raise Exception(data["message"])
        except ValueError:
            log(data)
        return None

    def get_messages(self) -> Set[str]:
        """
        Returns messages received from server
        """
        messages = self._server_messages
        self._server_messages = []
        return set(messages)

    def send_tcp_message(self, message: str) -> Any:
        """
        Sends a TCP message, parses the response and returns it.
        """
        self._sock_tcp = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM)
        self._sock_tcp.connect(self._server_tcp)
        self._sock_tcp.send(message.encode())
        data = self._sock_tcp.recv(1024)
        self._sock_tcp.close()
        response = self.parse_data(data)
        return response

    def send_udp_message(self, message: str) -> None:
        """
        Sends an UDP message.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(message.encode(), self._server_udp)

    def send_all(self, message: str):
        """
        Sends a message to all players in the room.
        """
        message = json.dumps({
            "action": "send",
            "payload": {"message": message},
            "room_id": self._room_id,
            "identifier": self._identifier,
        })
        self.send_udp_message(message)

    def send_to(self, recipients: List[str], message: str):
        """
        Sends a message to a list of players.
        """
        message = json.dumps({
            "action": "sendto",
            "payload": {"message": message, "recipients": recipients},
            "room_id": self._room_id,
            "identifier": self._identifier,
        })
        self.send_udp_message(message)

    def create_room(self, room_name: str = None):
        """
        Creates a new room in the server.
        """
        message = json.dumps({
            "action": "create",
            "payload": room_name,
            "identifier": self._identifier,
        })
        response = self.send_tcp_message(message)
        self._room_id = response

    def join_room(self, room_id):
        """
        Joins an existing room in the server.
        """
        message = json.dumps({
            "action": "join",
            "payload": room_id,
            "identifier": self._identifier,
        })
        response = self.send_tcp_message(message)
        self._room_id = response

    def autojoin(self):
        """
        Join any valid room.
        """
        message = json.dumps({
            "action": "autojoin",
            "identifier": self._identifier,
        })
        response = self.send_tcp_message(message)
        self._room_id = response

    def leave_room(self):
        """
        Leave the current room.
        """
        message = json.dumps({
            "action": "leave",
            "room_id": self._room_id,
            "identifier": self._identifier,
        })
        self.send_tcp_message(message)

    def get_rooms(self) -> List[dict]:
        """
        Gets the list of existing rooms in the server.
        """
        message = json.dumps({
            "action": "get_rooms",
            "identifier": self._identifier,
        })
        response = self.send_tcp_message(message)
        return response

    def register(self):
        """
        Register the client to server and get unique identifier.
        """
        message = json.dumps({
            "action": "register",
            "payload": self._client_udp[1]
        })
        response = self.send_tcp_message(message)
        self._identifier = response
