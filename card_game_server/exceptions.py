#
# Room
#


class RoomFullError(Exception):
    """
    Raised when a room is full and a player tries to join.
    """


class RoomNotFoundError(Exception):
    """
    Raised when a room is not found.
    """


class PlayerNotInRoomError(Exception):
    """
    Raised when a player tries to leave a room that he is not in.
    """


#
# Player
#


class PlayerNotFoundError(Exception):
    """
    Raised when a player is not found.
    """


#
# UdpServer
#


class UdpServerFailedToSendError(Exception):
    """
    Raised when a message could not be sent.
    """
