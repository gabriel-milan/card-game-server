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
        self._identifier: str = uuid4()
        self._address: str = address[0]
        self._udp_address: Tuple[str, int] = (address, int(udp_port))

    def __eq__(self, other: 'Player'):
        return self._identifier == other._identifier

    @property
    def identifier(self):
        return self._identifier

    @property
    def address(self):
        return self._address

    @property
    def udp_address(self):
        return self._udp_address

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
