import atexit
import json
import socket
from threading import Thread, Lock
from typing import Tuple, Union

from card_game_server.exceptions import (
    PlayerNotInRoomError,
    RoomFullError,
    RoomNotFoundError,
    UdpServerFailedToSendError,
)
from card_game_server.logger import log
from card_game_server.models.rooms import Rooms
from card_game_server.models.message import Message


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
        atexit.register(self.stop)

    def handle(self, message: Message):
        """
        Implements message handling
        """
        if message.room_id not in self._rooms.room_ids:
            log(f"Room with id {message.room_id} not found when handling message "
                f"from player {message.identifier}", "error")
            raise RoomNotFoundError()
        self._lock.acquire()
        try:
            if message.action == "send":
                log(f"Sending message {message.payload} to {message.room_id}", "debug")
                try:
                    self._rooms.send(
                        message.identifier,
                        message.room_id,
                        message.payload["message"]
                    )
                    log(
                        f"Message successfully sent to {message.room_id}", "debug")
                except Exception as exc:
                    log(
                        f"Failed to send message to {message.room_id}: {exc}", "error")
                    raise UdpServerFailedToSendError() from exc
            elif message.action == "sendto":
                log(
                    f'Sending message {message.payload} to {message.payload["recipients"]}', "debug"
                )
                try:
                    self._rooms.sendto(
                        message.identifier,
                        message.room_id,
                        message.payload["recipients"],
                        message.payload["message"]
                    )
                    log(
                        f"Message successfully sent to {message.payload['recipients']}", "debug")
                except Exception as exc:
                    log(
                        f"Failed to send message to {message.payload['recipients']}: {exc}", "error"
                    )
                    raise UdpServerFailedToSendError() from exc
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
                log(f"Room with id {message.room_id} not found", "error")
        self._sock.close()

    def stop(self):
        """
        Stop the server.
        """
        self._listening = False


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

    def handle(  # pylint: disable=too-many-statements
        self,
        sock: socket.socket,
        address: Tuple[str, int],
        message: Message,
    ) -> None:
        """
        Implements message handling
        """
        # If we want to register a player, just do it and return
        if message.action == "register":
            log(f"Registering player with UDP port {message.payload}", "debug")
            client = self._rooms.register(address, int(message.payload))
            log(f"Registered player {client}", "debug")
            client.send_tcp(True, client.identifier, sock)
            log(f"Sent registration confirmation to {client}", "debug")
            return

        # If we have a Player ID
        if message.identifier is not None:

            # Check if it is registered, if it's not, send a failure message
            if not self._rooms.get_player(message.identifier):
                log(f"Unknown Player ID {message.identifier} for {address}", "error")
                message = self._message.copy()
                message['success'] = False
                message['message'] = "Unknown Player ID"
                sock.send(json.dumps(message).encode())
                return

            # If it is, get the player object
            client = self._rooms.get_player(message.identifier)

            # If the action asks to join a room
            if message.action == "join":
                # Tries to find a room and join it
                try:
                    if not self._rooms.get_room(message.payload):
                        log(f"Player {client} tried to join room {message.payload} "
                            "but it doesn't exist", "error")
                        raise RoomNotFoundError()
                    log(f"Player {client} is joining room {message.payload}", "debug")
                    self._rooms.join(message.identifier, message.payload)
                    log(f"Player {client} joined room {message.payload}", "debug")
                    client.send_tcp(True, message.payload, sock)
                    log(f"Sent join confirmation to {client}", "debug")
                except RoomNotFoundError:
                    client.send_tcp(False, message.payload, sock)
                    log(
                        f"Sent join failure (RoomNotFound) to {client}", "debug")
                except RoomFullError:
                    client.send_tcp(False, message.payload, sock)
                    log(f"Sent join failure (RoomFull) to {client}", "debug")

            # If the action asks to join ANY room
            elif message.action == "autojoin":
                log(f"Player {client} is trying to autojoin ANY room", "debug")
                room_id = self._rooms.join(message.identifier)
                log(f"Player {client} joined room {room_id}", "debug")
                client.send_tcp(True, room_id, sock)
                log(f"Sent autojoin confirmation to {client}", "debug")

            # If the action asks to list rooms
            elif message.action == "get_rooms":
                log(f"Player {client} is trying to list rooms", "debug")
                rooms = []
                for room in self._rooms.rooms:
                    rooms.append({
                        "id": room.identifier,
                        "name": room.name,
                        "n_players": len(room.players),
                        "capacity": room.capacity,
                    })
                client.send_tcp(True, rooms, sock)
                log(f"Sent rooms list to {client}", "debug")

            # If the action asks to create a room
            elif message.action == "create":
                log(f"Player {client} is trying to create a room", "debug")
                room_id = self._rooms.create(message.payload).identifier
                log(f"Player {client} created room {room_id}", "debug")
                self._rooms.join(client.identifier, room_id)
                log(f"Player {client} joined room {room_id}", "debug")
                client.send_tcp(True, room_id, sock)
                log(f"Sent create confirmation to {client}", "debug")

            # If the action asks to leave a room
            elif message.action == "leave":
                log(f"Player {client} is trying to leave a room", "debug")
                try:
                    if not self._rooms.get_room(message.room_id):
                        log(f"Player {client} tried to leave room {message.room_id} but "
                            "it doesn't exist", "error")
                        raise RoomNotFoundError()
                    self._rooms.leave(message.identifier, message.room_id)
                    log(f"Player {client} left room {message.room_id}", "debug")
                    client.send_tcp(True, message.room_id, sock)
                    log(f"Sent leave confirmation to {client}", "debug")
                except RoomNotFoundError:
                    client.send_tcp(False, message.room_id, sock)
                    log(
                        f"Sent leave failure (RoomNotFound) to {client}", "debug")
                except PlayerNotInRoomError:
                    client.send_tcp(False, message.room_id, sock)
                    log(
                        f"Sent leave failure (PlayerNotInRoom) to {client}", "debug")

            # Otherwise, user must register
            else:
                log(f"Player {client} sent an unknown action {message.action}", "error")
                message = self._message.copy()
                message['success'] = False
                message['message'] = "You must register"
                sock.send(json.dumps(message).encode())
                log(f"Sent failure to {client}", "debug")

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
        self._sock.close()

    def stop(self):
        """
        Stop the server.
        """
        self._listening = False
