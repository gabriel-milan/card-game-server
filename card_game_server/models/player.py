import json
import socket
from typing import Tuple, Union
from uuid import uuid4


class Player:

    def __init__(
        self,
        address: Tuple[str, int],
        udp_port: Union[str, int]
    ):
        """
        Identification of a remote player.
        """
        self._identifier: str = str(uuid4())
        self._address: str = address
        self._udp_address: Tuple[str, int] = (address[0], int(udp_port))

    def __eq__(self, other: 'Player'):
        return self._identifier == other._identifier

    def __str__(self) -> str:
        return f"<Player {self._identifier} (udp_port={self.udp_address[1]})>"

    def __repr__(self) -> str:
        return self.__str__()

    @property
    def identifier(self):
        return self._identifier

    @property
    def address(self):
        return self._address

    @property
    def udp_address(self):
        return self._udp_address

    # pylint: disable=no-self-use
    def send_tcp(
        self,
        success: bool,
        data: str,
        sock: socket.socket
    ):
        """
        Send a TCP message to the player.
        """
        message = json.dumps({
            'success': success,
            'message': data,
        })
        sock.send(message.encode())

    def send_udp(
        self,
        player_identifier: str,
        message: str,
    ):
        """
        Send a UDP message to the player.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(
            json.dumps({player_identifier: message}).encode(),
            self._udp_address,
        )
        sock.close()
