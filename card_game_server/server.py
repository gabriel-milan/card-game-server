import json
import socket
from threading import Thread, Lock
from time import time
from typing import Union

from card_game_server.exceptions import (
    RoomNotFoundError,
    UdpServerFailedToSendError,
)
from card_game_server.logger import log
from card_game_server.models.rooms import Rooms
from card_game_server.models.message import Message

# TODO: Schedule cleaning empty rooms every once in a while


class UdpServer(Thread):
    def __init__(
        self,
        udp_port: Union[str, int],
        rooms: Rooms,
        lock: Lock
    ):
        """
        UDP server.
        """
        super().__init__()
        self._udp_port: int = int(udp_port)
        self._rooms: Rooms = rooms
        self._lock: Lock = lock
        self._listening: bool = True
        self._sock: socket.socket = None

    def handle(self, message: Message):
        """
        Implements message handling
        """
        if message.room_id not in self._rooms.rooms:
            raise RoomNotFoundError()
        self._lock.acquire()
        try:
            if message.action == "send":
                try:
                    self._rooms.send(
                        message.identifier,
                        message.room_id,
                        message.payload["message"]
                    )
                except Exception as e:
                    raise UdpServerFailedToSendError() from e
            elif message.action == "sendto":
                try:
                    self._rooms.sendto(
                        message.identifier,
                        message.room_id,
                        message.payload["recipients"],
                        message.payload["message"]
                    )
                except Exception as e:
                    raise UdpServerFailedToSendError() from e
        finally:
            self._lock.release()

    def run(self):
        """
        Thread run method.
        """
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.bind(('0.0.0.0', self._udp_port))
        self._sock.setblocking(0)
        self._sock.settimeout(5)
        while self._listening:
            try:
                data, address = self._sock.recvfrom(1024)
                data = json.loads(data.decode('utf-8'))
                log(f"Received message from {address}: {data}", "debug")
            except socket.timeout:
                continue

            message: Message = Message(data)
            try:
                self.handle(message)
            except RoomNotFoundError:
                log("Room with id {} not found".format(
                    message.room_id), "error")
        self.stop()

    def stop(self):
        """
        Stop the server.
        """
        self._listening = False
        self._sock.close()


class TcpServer(Thread):
    def __init__(
        self,
        tcp_port: Union[str, int],
        rooms: Rooms,
        lock: Lock
    ):
        """
        TCP server.
        """
        super().__init__()
        self._tcp_port: int = int(tcp_port)
        self._rooms: Rooms = rooms
        self._lock: Lock = lock
        self._listening: bool = True
        self._message: dict = {
            'success': None,
            'message': None,
        }
        self._sock: socket.socket = None

    def handle(
        self,
        conn: socket.socket,
        address,
        message: Message,
    ):
        """
        Implements message handling
        """
        # TODO.

    def run(self):
        """
        Thread run method.
        """
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.bind(('0.0.0.0', self._tcp_port))
        self._sock.setblocking(0)
        self._sock.settimeout(5)
        self._sock.listen(1)

        while self._listening:
            try:
                conn, address = self._sock.accept()
            except socket.timeout:
                continue
            data = conn.recv(1024)
            data = json.loads(data.decode('utf-8'))
            log(f"Received message from {address}: {data}", "debug")

            message: Message = Message(data)
            self._lock.acquire()
            try:
                self.handle(
                    conn,
                    address,
                    message,
                )
            finally:
                self._lock.release()
            conn.close()
        self.stop()

    def stop(self):
        """
        Stop the server.
        """
        self._listening = False
        self._sock.close()
