from typing import Any


class Message:
    def __init__(self, data: dict):
        self._raw_data: dict = data
        self._identifier: str = data.get('identifier', None)
        self._room_id: str = data.get('room_id', None)
        self._payload: Any = data.get('payload', None)
        self._action: str = data.get('action', None)

    @property
    def identifier(self) -> str:
        return self._identifier

    @property
    def room_id(self) -> str:
        return self._room_id

    @property
    def payload(self) -> Any:
        return self._payload

    @property
    def action(self) -> str:
        return self._action
