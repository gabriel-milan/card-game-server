from typing import (
    List,
    Tuple,
    Union,
)

from card_game_server.exceptions import (
    PlayerNotFoundError,
    PlayerNotInRoomError,
    RoomFullError,
    RoomNotFoundError,
)
from card_game_server.logger import log
from card_game_server.models.player import Player
from card_game_server.models.room import Room


class Rooms:

    def __init__(
        self,
        capacity: int = 2,
    ):
        """
        Collection of rooms.
        """
        self._players: List[Player] = []
        self._rooms: List[Room] = []
        self._capacity: int = capacity

    @property
    def rooms(self) -> List[Room]:
        """
        Get all rooms.
        """
        return self._rooms

    @property
    def room_ids(self) -> List[str]:
        """
        Get all room identifiers.
        """
        return [room.identifier for room in self._rooms]

    @property
    def players(self) -> List[Player]:
        """
        Get all players.
        """
        return self._players

    @property
    def capacity(self) -> int:
        """
        Get capacity of rooms.
        """
        return self._capacity

    def get_player(self, player_id: str) -> Player:
        """
        Get a player by its identifier.
        """
        for player in self._players:
            if player.identifier == player_id:
                return player
        return None

    def get_any_room(self, room_id: str = None) -> Room:
        """
        Get a room by its identifier.
        """
        # Try to match room ID
        for room in self._rooms:
            if room.identifier == room_id:
                return room

        # Try to find any not full room
        for room in self._rooms:
            if not room.is_full():
                return room

        # Create a new room
        room = Room(capacity=self._capacity)
        self._rooms.append(room)
        return room

    def get_room(self, room_id: str = None) -> Room:
        """
        Get a room by its identifier.
        """
        # Try to match room ID
        for room in self._rooms:
            if room.identifier == room_id:
                return room
        return None

    def register(
        self,
        address: Tuple[str, int],
        udp_port: Union[int, str],
    ) -> Player:
        """
        Register a player.
        """
        player = Player(
            address,
            udp_port,
        )
        found = False
        # for registered_player in self._players:
        #     if player.address == registered_player.address:
        #         player = registered_player
        #         found = True
        #         break

        if not found:
            self._players.append(player)

        return player

    def join(
        self,
        player_id: str,
        room_id: str = None,
    ) -> Room:
        """
        Join a room.
        """
        player = self.get_player(player_id)
        if player is None:
            raise PlayerNotFoundError()
        if room_id is not None:
            room = self.get_room(room_id)
            if room is None:
                raise RoomNotFoundError()
            if room.is_full():
                raise RoomFullError()
        else:
            room = self.get_any_room(room_id)
        room.join(player)
        return room

    def leave(
        self,
        player_id: str,
        room_id: str,
    ) -> Room:
        """
        Leave a room.
        """
        player = self.get_player(player_id)
        if player is None:
            raise PlayerNotFoundError()
        room = self.get_room(room_id)
        if room is None:
            raise RoomNotFoundError()
        if player not in room.players:
            raise PlayerNotInRoomError()
        room.leave(player)
        return room

    def create(self, room_name: str = None) -> Room:
        """
        Creates a new room.
        """
        room = Room(
            capacity=self._capacity,
            name=room_name,
        )
        self._rooms.append(room)
        return room

    def clear_empty_rooms(self) -> None:
        """
        Remove all empty rooms.
        """
        for room in self._rooms:
            if room.is_empty():
                self._rooms.remove(room)

    def send(
        self,
        player_id: str,
        room_id: str,
        message: str
    ):
        """
        Send a message to a room.
        """
        room = self.get_room(room_id)
        if room is None:
            raise RoomNotFoundError()
        self.sendto(player_id, room_id, room.players, message)

    def sendto(
        self,
        player_id: str,
        room_id: str,
        recipients: Union[List[Player], Player],
        message: str,
    ):
        """
        Send a message to a player.
        """
        room = self.get_room(room_id)
        if room is None:
            raise RoomNotFoundError()
        player = self.get_player(player_id)
        if player is None:
            raise PlayerNotFoundError()
        if player not in room.players:
            raise PlayerNotInRoomError()
        if isinstance(recipients, str):
            recipients: List[Player] = [recipients]
        recipient_ids = [recipient.identifier for recipient in recipients]
        for player in room.players:
            if player.identifier in recipient_ids:
                log(
                    f"Sending message to {player.udp_address}", "debug")
                player.send_udp(player_id, message)
