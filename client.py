# card_game_server.gui.client.Client is our QWidget.
# This script intends to launch the client.

from PyQt5.QtWidgets import QApplication

from card_game_server.gui.client import ClientGui


if __name__ == '__main__':
    app = QApplication([])
    client = ClientGui()
    client.show()
    app.exec_()
