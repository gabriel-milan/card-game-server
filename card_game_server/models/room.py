from typing import List
from uuid import uuid4

from card_game_server.exceptions import (
    PlayerNotInRoomError,
    RoomFullError,
)
from card_game_server.models.player import Player


class Room:

    def __init__(
        self,
        capacity: int = 2,
        name: str = None,
    ):
        """
        A room for playing a game.
        """
        self._identifier: str = str(uuid4())
        self._capacity: int = capacity
        self._players: List[Player] = []
        self._name: str = name if name else self._identifier

    def __eq__(self, other: 'Room'):
        return self._identifier == other._identifier

    @property
    def identifier(self):
        return self._identifier

    @property
    def name(self):
        return self._name

    @property
    def capacity(self):
        return self._capacity

    @property
    def players(self):
        return self._players

    def is_full(self):
        """
        Check if the room is full.
        """
        return len(self._players) >= self._capacity

    def is_empty(self):
        """
        Check if the room is empty.
        """
        return len(self._players) == 0

    def is_in_room(self, player: Player):
        """
        Check if a player is in the room.
        """
        return player in self._players

    def join(self, player: Player):
        """
        Add a player to the room.
        """
        if self.is_full():
            raise RoomFullError()
        self._players.append(player)

    def leave(self, player: Player):
        """
        Remove a player from the room.
        """
        if player not in self._players:
            raise PlayerNotInRoomError()
        self._players.remove(player)
