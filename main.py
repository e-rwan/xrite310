import sys
import os

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from PySide6.QtNetwork import QLocalSocket, QLocalServer
from PySide6.QtCore import Qt, QByteArray, QIODevice
from ui.main_window import MainWindow
from constants import UNIQUE_APP_ID, ICON_PATH

print(ICON_PATH)

def is_another_instance_running():
    socket = QLocalSocket()
    socket.connectToServer(UNIQUE_APP_ID)
    if socket.waitForConnected(100):
        # envoyer un signal quelconque (utile si on veut que la 1ère instance réagisse)
        socket.write(b"raise")
        socket.flush()
        socket.waitForBytesWritten(100)
        socket.disconnectFromServer()
        return True
    return False


def create_single_instance_server(main_window):
    server = QLocalServer()
    try:
        QLocalServer.removeServer(UNIQUE_APP_ID)
    except:
        pass

    if not server.listen(UNIQUE_APP_ID):
        print("Impossible d'écouter sur le socket.")
        return None

    def on_new_connection():
        socket = server.nextPendingConnection()
        if socket and socket.waitForReadyRead(100):
            message = bytes(socket.readAll().data()).decode()
            if message == "raise":
                main_window.show()
                main_window.raise_()
                main_window.activateWindow()
                main_window.setWindowState(
                    main_window.windowState() & ~Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive
                )
        socket.disconnectFromServer()

    server.newConnection.connect(on_new_connection)
    return server


def main():
    if is_another_instance_running():
        print("App is already running.")
        sys.exit(0)

    app = QApplication(sys.argv)

    app.setWindowIcon(QIcon(ICON_PATH))

    main_window = MainWindow()
    main_window.resize(1400, 800)
    main_window.show()

    create_single_instance_server(main_window)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
