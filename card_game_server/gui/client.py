"""
A simple PyQt5 client for the card game server.

The layout consists in:
- A top text box that asks for the Room ID the user wants to join.
- Three buttons below it, one for joining the room, one for creating a new room,
    and one for leaving the room.
- Below that, we split the screen in two, one for the room's players and one for
    the room's chat.
- The room's players is a list of players, with their names.
- The room's chat is a list of messages and, at the bottom, a text box for
    sending messages.
- There's also a log of the game's events in the bottom of the screen.
"""

from random import randint
from threading import Thread

import pendulum
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QListWidget,
)

from card_game_server.client import Client


# Build the layout
class ClientGui(QWidget):
    """
    The main widget of the client.
    """

    def __init__(self):
        super().__init__()
        self._client: Client = None
        self.init_ui()
        Thread(target=self.connect_to_server, daemon=True).start()

    def init_ui(self):
        """
        Initialize the layout.
        """
        self.setWindowTitle('Card Game Client')
        self.setGeometry(300, 300, 800, 600)

        # Top text box
        self.room_id_text = QLineEdit(self)
        self.room_id_text.setPlaceholderText('Room ID')
        self.room_id_text.setFixedHeight(30)

        # Buttons
        self.join_button = QPushButton('Join', self)
        self.join_button.setFixedHeight(30)
        self.join_button.clicked.connect(self.join_room)

        self.create_button = QPushButton('Create', self)
        self.create_button.setFixedHeight(30)
        self.create_button.clicked.connect(self.create_room)

        self.leave_button = QPushButton('Leave', self)
        self.leave_button.setFixedHeight(30)
        self.leave_button.clicked.connect(self.leave_room)

        # Room's players and chat
        self.room_players_list = QListWidget(self)
        self.room_chat_list = QListWidget(self)

        # Room's chat text box
        self.room_chat_text = QLineEdit(self)
        self.room_chat_text.setPlaceholderText('Type a message...')
        self.room_chat_text.setFixedHeight(30)
        self.room_chat_text.returnPressed.connect(self.send_message)

        # Log of the game's events
        self.log_list = QListWidget(self)

        # Layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(self.room_id_text)

        self.buttons_layout = QHBoxLayout(self)
        self.buttons_layout.addWidget(self.join_button)
        self.buttons_layout.addWidget(self.create_button)
        self.buttons_layout.addWidget(self.leave_button)
        self.main_layout.addLayout(self.buttons_layout)

        self.room_layout = QHBoxLayout(self)
        self.room_layout.addWidget(self.room_players_list)
        self.room_layout.addWidget(self.room_chat_list)
        self.main_layout.addLayout(self.room_layout)

        self.room_chat_layout = QHBoxLayout(self)
        self.room_chat_layout.addWidget(self.room_chat_text)
        self.main_layout.addLayout(self.room_chat_layout)

        self.log_layout = QHBoxLayout(self)
        self.log_layout.addWidget(self.log_list)
        self.main_layout.addLayout(self.log_layout)

        self.show()

    def log(self, message: str):
        """
        Add a message to the log.
        """
        self.log_list.addItem(f"{pendulum.now().isoformat()}: {message}")

    def connect_to_server(self):
        """
        Connect to the server.
        """
        from time import sleep
        self.log("Connecting to the server...")
        try:
            self._client: Client = Client(
                server_host="localhost",
                server_port_tcp=1234,
                server_port_udp=1234,
                client_port_udp=randint(5000, 6000),
            )
            self.log(
                f"Successfully connected with ID {self._client.identifier}")
        except Exception as e:
            self.log(f"Failed to connect: {e}")

    def send_message(self):
        """
        Send a message to the server.
        """
        message = self.room_chat_text.text()
        self.log(f"Sending message: {message}")
        self._client.send_all(message)
        self.room_chat_list.addItem(
            f"{pendulum.now().isoformat()}: {message}")
        self.room_chat_text.setText('')

    def create_room(self):
        """
        Create a new room.
        """
        self.log("Creating a new room...")
        self._client.create_room()
        self.log(f"Successfully created room {self._client.room_id}")

    def join_room(self):
        """
        Join an existing room.
        """
        self.log("Joining a room...")
        room_id = self.room_id_text.text()
        self._client.join_room(room_id)
        self.log(f"Successfully joined room {room_id}")

    def leave_room(self):
        """
        Leave the current room.
        """
        self.log("Leaving the room...")
        self._client.leave_room()
        self.log("Successfully left the room")
